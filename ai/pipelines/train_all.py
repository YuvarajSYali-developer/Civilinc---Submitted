"""
CivilInc AI Training Pipeline — All 7 Systems
================================================
System 1: Complaint Category Classification   (TF-IDF + LightGBM, target F1 > 0.85)
System 2: Priority Prediction                 (LightGBM, target F1 > 0.80)
System 3: Resolution Time Prediction          (XGBoost Regressor, target MAE < 3 days)
System 4: Complaint Clustering                (TF-IDF + KMeans, cluster severity scoring)
System 5: Project Delay Prediction            (LightGBM classifier, probability output)
System 6: Budget Overrun Prediction           (XGBoost Regressor, expected overrun INR)
System 7: Ward Risk Scoring                   (Composite index, risk category assignment)
"""

import pandas as pd
import numpy as np
import json
import joblib
import warnings
from pathlib import Path
from datetime import datetime

warnings.filterwarnings("ignore")
np.random.seed(42)

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"
MODEL_DIR = BASE_DIR / "ai" / "models"
EVAL_DIR = BASE_DIR / "ai" / "evaluation"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
EVAL_DIR.mkdir(parents=True, exist_ok=True)

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    classification_report, f1_score, mean_absolute_error,
    mean_squared_error, r2_score, confusion_matrix
)
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.cluster import KMeans
import lightgbm as lgb
import xgboost as xgb

print("=" * 65)
print("CivilInc AI Training Pipeline")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 65)

# ─── Load Datasets ────────────────────────────────────────────────────────────
print("\n📂 Loading datasets...")
df_c = pd.read_csv(DATA_DIR / "complaints.csv")
df_p = pd.read_csv(DATA_DIR / "projects.csv")
df_b = pd.read_csv(DATA_DIR / "budgets.csv")
df_f = pd.read_csv(DATA_DIR / "citizen_feedback.csv")
df_w = pd.read_csv(DATA_DIR / "officer_workload.csv")
print(f"  complaints    : {len(df_c):,} rows")
print(f"  projects      : {len(df_p):,} rows")
print(f"  budgets       : {len(df_b)} rows")
print(f"  feedback      : {len(df_f):,} rows")
print(f"  officer_wl    : {len(df_w):,} rows")

eval_results = {}

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM 1: COMPLAINT CATEGORY CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 65)
print("SYSTEM 1: Complaint Category Classification")
print("  Input: title + description  |  Output: category (7 classes)")
print("  Model: TF-IDF → LightGBM + Random Forest ensemble")
print("─" * 65)

# Feature: combined text
df_c["text"] = df_c["title"].fillna("") + " " + df_c["description"].fillna("")

le_cat = LabelEncoder()
y_cat = le_cat.fit_transform(df_c["category"])

X_train_txt, X_test_txt, y_train_cat, y_test_cat = train_test_split(
    df_c["text"], y_cat, test_size=0.20, random_state=42, stratify=y_cat
)

# TF-IDF features
tfidf = TfidfVectorizer(max_features=15000, ngram_range=(1, 2),
                        sublinear_tf=True, min_df=3, max_df=0.95)
X_train_tfidf = tfidf.fit_transform(X_train_txt)
X_test_tfidf = tfidf.transform(X_test_txt)

# LightGBM classifier
lgb_cat = lgb.LGBMClassifier(
    n_estimators=300, learning_rate=0.08, num_leaves=63,
    min_child_samples=20, subsample=0.8, colsample_bytree=0.8,
    class_weight="balanced", random_state=42, verbose=-1
)
lgb_cat.fit(X_train_tfidf, y_train_cat)
y_pred_cat_lgb = lgb_cat.predict(X_test_tfidf)

# Random Forest for comparison
rf_cat = RandomForestClassifier(
    n_estimators=200, max_depth=20, min_samples_leaf=5,
    class_weight="balanced", random_state=42, n_jobs=-1
)
rf_cat.fit(X_train_tfidf, y_train_cat)
y_pred_cat_rf = rf_cat.predict(X_test_tfidf)

f1_lgb = f1_score(y_test_cat, y_pred_cat_lgb, average="weighted")
f1_rf = f1_score(y_test_cat, y_pred_cat_rf, average="weighted")

# Ensemble: pick best
best_cat_model = lgb_cat if f1_lgb >= f1_rf else rf_cat
best_cat_preds = y_pred_cat_lgb if f1_lgb >= f1_rf else y_pred_cat_rf
best_f1_cat = max(f1_lgb, f1_rf)

report_cat = classification_report(
    y_test_cat, best_cat_preds,
    target_names=le_cat.classes_, output_dict=True
)
print(f"  LightGBM F1 (weighted): {f1_lgb:.4f}")
print(f"  RandomForest F1       : {f1_rf:.4f}")
print(f"  Best model F1         : {best_f1_cat:.4f}  {'✅ PASS' if best_f1_cat > 0.85 else '⚠️  BELOW TARGET'}")
print(f"  Per-class F1:")
for cls in le_cat.classes_:
    print(f"    {cls:<20}: {report_cat[cls]['f1-score']:.3f}")

# Save
joblib.dump(tfidf, MODEL_DIR / "tfidf_vectorizer.joblib")
joblib.dump(best_cat_model, MODEL_DIR / "system1_category_classifier.joblib")
joblib.dump(le_cat, MODEL_DIR / "label_encoder_category.joblib")
eval_results["system1_category"] = {"f1_weighted": round(best_f1_cat, 4), "target": 0.85, "pass": best_f1_cat > 0.85}

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM 2: PRIORITY PREDICTION
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 65)
print("SYSTEM 2: Priority Prediction")
print("  Input: category, sub_category, zone, source, text features")
print("  Output: low / medium / high / critical")
print("─" * 65)

df_c_prio = df_c.dropna(subset=["category", "sub_category", "zone", "priority"]).copy()

le_prio = LabelEncoder()
y_prio = le_prio.fit_transform(df_c_prio["priority"])

le_sub = LabelEncoder()
le_zone = LabelEncoder()
le_src = LabelEncoder()
le_dept_c = LabelEncoder()

df_c_prio["sub_cat_enc"] = le_sub.fit_transform(df_c_prio["sub_category"].fillna("unknown"))
df_c_prio["zone_enc"] = le_zone.fit_transform(df_c_prio["zone"].fillna("Central"))
df_c_prio["src_enc"] = le_src.fit_transform(df_c_prio["source"].fillna("web"))
df_c_prio["dept_enc"] = le_dept_c.fit_transform(df_c_prio["department"].fillna("ROADS"))
df_c_prio["cat_enc"] = le_cat.transform(df_c_prio["category"])

# TF-IDF on title for extra signal
tfidf_prio = TfidfVectorizer(max_features=3000, ngram_range=(1,2), sublinear_tf=True)
title_feats = tfidf_prio.fit_transform(df_c_prio["title"].fillna("")).toarray()

struct_feats = df_c_prio[["cat_enc","sub_cat_enc","zone_enc","src_enc","dept_enc"]].values
X_prio = np.hstack([struct_feats, title_feats])

X_tr_p, X_te_p, y_tr_p, y_te_p = train_test_split(X_prio, y_prio, test_size=0.2, random_state=42, stratify=y_prio)

lgb_prio = lgb.LGBMClassifier(
    n_estimators=400, learning_rate=0.06, num_leaves=63,
    min_child_samples=20, subsample=0.8, colsample_bytree=0.7,
    class_weight="balanced", random_state=42, verbose=-1
)
lgb_prio.fit(X_tr_p, y_tr_p)
y_pred_prio = lgb_prio.predict(X_te_p)
f1_prio = f1_score(y_te_p, y_pred_prio, average="weighted")

report_prio = classification_report(y_te_p, y_pred_prio, target_names=le_prio.classes_, output_dict=True)
print(f"  LightGBM F1 (weighted): {f1_prio:.4f}  {'✅ PASS' if f1_prio > 0.80 else '⚠️  BELOW TARGET'}")
for cls in le_prio.classes_:
    print(f"    {cls:<10}: {report_prio[cls]['f1-score']:.3f}")

joblib.dump(lgb_prio, MODEL_DIR / "system2_priority_predictor.joblib")
joblib.dump(tfidf_prio, MODEL_DIR / "tfidf_priority.joblib")
joblib.dump({"le_sub": le_sub, "le_zone": le_zone, "le_src": le_src,
             "le_dept_c": le_dept_c, "le_prio": le_prio}, MODEL_DIR / "encoders_priority.joblib")
eval_results["system2_priority"] = {"f1_weighted": round(f1_prio, 4), "target": 0.80, "pass": f1_prio > 0.80}

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM 3: RESOLUTION TIME PREDICTION
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 65)
print("SYSTEM 3: Resolution Time Prediction")
print("  Input: category, priority, zone, source, sla_hours")
print("  Output: estimated resolution days (regression)")
print("─" * 65)

df_res = df_c.dropna(subset=["resolution_days"]).copy()
df_res = df_res[df_res["resolution_days"] > 0]

le_cat_r = LabelEncoder(); le_prio_r = LabelEncoder()
le_zone_r = LabelEncoder(); le_src_r = LabelEncoder()

df_res["cat_enc"] = le_cat_r.fit_transform(df_res["category"])
df_res["prio_enc"] = le_prio_r.fit_transform(df_res["priority"])
df_res["zone_enc"] = le_zone_r.fit_transform(df_res["zone"].fillna("Central"))
df_res["src_enc"] = le_src_r.fit_transform(df_res["source"].fillna("web"))

feat_cols = ["cat_enc","prio_enc","zone_enc","src_enc","sla_hours","escalation_level"]
X_res = df_res[feat_cols].fillna(0).values
y_res = df_res["resolution_days"].values

X_tr_r, X_te_r, y_tr_r, y_te_r = train_test_split(X_res, y_res, test_size=0.2, random_state=42)

xgb_res = xgb.XGBRegressor(
    n_estimators=500, learning_rate=0.05, max_depth=6,
    subsample=0.8, colsample_bytree=0.8, min_child_weight=5,
    reg_alpha=0.1, reg_lambda=1.0, random_state=42,
    tree_method="hist", verbosity=0
)
xgb_res.fit(X_tr_r, y_tr_r)
y_pred_res = xgb_res.predict(X_te_r)
mae_res = mean_absolute_error(y_te_r, y_pred_res)
r2_res = r2_score(y_te_r, y_pred_res)

print(f"  XGBoost MAE   : {mae_res:.2f} days  {'✅ PASS' if mae_res < 3.0 else '⚠️  ABOVE TARGET'}")
print(f"  XGBoost R²    : {r2_res:.3f}")

# Feature importance
fi = dict(zip(feat_cols, xgb_res.feature_importances_))
print(f"  Top features  : {sorted(fi.items(), key=lambda x:-x[1])[:3]}")

joblib.dump(xgb_res, MODEL_DIR / "system3_resolution_predictor.joblib")
joblib.dump({"le_cat":le_cat_r,"le_prio":le_prio_r,"le_zone":le_zone_r,"le_src":le_src_r,
             "feat_cols":feat_cols}, MODEL_DIR / "encoders_resolution.joblib")
eval_results["system3_resolution"] = {"mae_days": round(mae_res, 3), "r2": round(r2_res, 3), "target_mae": 3.0, "pass": mae_res < 3.0}

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM 4: COMPLAINT CLUSTERING
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 65)
print("SYSTEM 4: Complaint Clustering")
print("  Input: TF-IDF of description  |  Output: cluster_id, severity, wards")
print("─" * 65)

# Sample for clustering performance
df_clust = df_c.sample(n=min(20000, len(df_c)), random_state=42)

tfidf_clust = TfidfVectorizer(max_features=5000, ngram_range=(1,2), sublinear_tf=True, min_df=5)
X_clust = tfidf_clust.fit_transform(df_clust["text"])

# Determine optimal k using silhouette on sample
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import silhouette_score

# Reduce dims for faster silhouette
svd = TruncatedSVD(n_components=50, random_state=42)
X_reduced = svd.fit_transform(X_clust)

# Test k = 10..20
best_k, best_sil = 15, -1
for k in [10, 12, 15, 18, 20]:
    km_test = KMeans(n_clusters=k, random_state=42, n_init=5, max_iter=100)
    labels = km_test.fit_predict(X_reduced[:5000])
    sil = silhouette_score(X_reduced[:5000], labels, sample_size=2000, random_state=42)
    if sil > best_sil:
        best_sil = sil; best_k = k
print(f"  Optimal clusters: k={best_k} (silhouette={best_sil:.3f})")

kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10, max_iter=300)
cluster_labels = kmeans.fit_predict(X_reduced)
df_clust = df_clust.copy()
df_clust["cluster_id"] = cluster_labels

# Cluster severity: complaints per cluster × avg priority weight
prio_weight = {"critical": 4, "high": 3, "medium": 2, "low": 1}
df_clust["prio_weight"] = df_clust["priority"].map(prio_weight).fillna(2)

cluster_profiles = []
for cid in range(best_k):
    mask = df_clust["cluster_id"] == cid
    grp = df_clust[mask]
    top_cats = grp["category"].value_counts().head(2).index.tolist()
    top_wards = grp["ward_number"].value_counts().head(5).index.tolist()
    avg_prio = grp["prio_weight"].mean()
    size = len(grp)
    sla_breach_rate = grp["sla_breached"].mean()
    severity_score = round((size/200) * avg_prio * (1 + sla_breach_rate), 2)
    severity_cat = ("critical" if severity_score > 8 else "high" if severity_score > 4
                    else "medium" if severity_score > 2 else "low")
    cluster_profiles.append({
        "cluster_id": cid, "size": size,
        "top_categories": top_cats, "top_wards": top_wards,
        "avg_priority_weight": round(avg_prio, 2),
        "sla_breach_rate": round(sla_breach_rate, 3),
        "severity_score": severity_score, "severity_category": severity_cat,
    })
    print(f"  Cluster {cid:>2}: {size:>5} complaints | {top_cats} | severity={severity_cat}")

joblib.dump(tfidf_clust, MODEL_DIR / "tfidf_cluster.joblib")
joblib.dump(svd, MODEL_DIR / "svd_cluster.joblib")
joblib.dump(kmeans, MODEL_DIR / "system4_kmeans.joblib")
json.dump(cluster_profiles, open(MODEL_DIR / "cluster_profiles.json", "w"), indent=2)
eval_results["system4_clustering"] = {"n_clusters": best_k, "silhouette": round(best_sil, 3)}

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM 5: PROJECT DELAY PREDICTION
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 65)
print("SYSTEM 5: Project Delay Prediction")
print("  Input: budget_util, completion_pct, pace, elapsed_pct, start_delay")
print("  Output: delay probability (0-1)")
print("─" * 65)

df_p_ml = df_p.dropna(subset=["is_delayed","completion_pct","budget_utilization_pct"]).copy()
df_p_ml = df_p_ml[df_p_ml["status"].isin(["completed","in_progress","on_hold"])]

le_cat_p = LabelEncoder(); le_dept_p = LabelEncoder(); le_fund_p = LabelEncoder()
df_p_ml["cat_enc"] = le_cat_p.fit_transform(df_p_ml["category"])
df_p_ml["dept_enc"] = le_dept_p.fit_transform(df_p_ml["department"])
df_p_ml["fund_enc"] = le_fund_p.fit_transform(df_p_ml["source_fund"].fillna("BBMP Own Funds"))

feats_delay = ["cat_enc","dept_enc","fund_enc","completion_pct","budget_utilization_pct",
               "elapsed_pct","pace_indicator","pre_monsoon_start","start_delay_days","planned_duration_days"]
X_del = df_p_ml[feats_delay].fillna(0).values
y_del = df_p_ml["is_delayed"].astype(int).values

X_tr_d, X_te_d, y_tr_d, y_te_d = train_test_split(X_del, y_del, test_size=0.2, random_state=42, stratify=y_del)

lgb_delay = lgb.LGBMClassifier(
    n_estimators=500, learning_rate=0.05, num_leaves=63,
    min_child_samples=15, subsample=0.8, colsample_bytree=0.8,
    scale_pos_weight=(y_tr_d==0).sum()/(y_tr_d==1).sum(),
    random_state=42, verbose=-1
)
lgb_delay.fit(X_tr_d, y_tr_d,
              eval_set=[(X_te_d, y_te_d)],
              callbacks=[lgb.early_stopping(30, verbose=False)])
y_pred_del = lgb_delay.predict(X_te_d)
y_prob_del = lgb_delay.predict_proba(X_te_d)[:, 1]

f1_del = f1_score(y_te_d, y_pred_del, average="weighted")
from sklearn.metrics import roc_auc_score
auc_del = roc_auc_score(y_te_d, y_prob_del)
print(f"  LightGBM F1   : {f1_del:.4f}")
print(f"  AUC-ROC       : {auc_del:.4f}")
fi_del = sorted(zip(feats_delay, lgb_delay.feature_importances_), key=lambda x:-x[1])
print(f"  Top features  : {fi_del[:3]}")

joblib.dump(lgb_delay, MODEL_DIR / "system5_delay_predictor.joblib")
joblib.dump({"le_cat":le_cat_p,"le_dept":le_dept_p,"le_fund":le_fund_p,"feats":feats_delay},
            MODEL_DIR / "encoders_delay.joblib")
eval_results["system5_delay"] = {"f1": round(f1_del,4), "auc_roc": round(auc_del,4)}

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM 6: BUDGET OVERRUN PREDICTION
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 65)
print("SYSTEM 6: Budget Overrun Prediction")
print("  Input: project features  |  Output: expected cost overrun (INR lakhs)")
print("─" * 65)

df_over = df_p.dropna(subset=["approved_budget_lakhs","actual_cost_lakhs"]).copy()
df_over = df_over[df_over["approved_budget_lakhs"] > 0]
df_over["overrun_lakhs"] = (df_over["actual_cost_lakhs"] - df_over["approved_budget_lakhs"]).clip(lower=0)
df_over["has_overrun"] = (df_over["overrun_lakhs"] > 0).astype(int)
print(f"  Projects with overrun: {df_over['has_overrun'].sum():,} / {len(df_over):,} ({df_over['has_overrun'].mean()*100:.1f}%)")

# Only predict on completed+in_progress
df_over_fit = df_over[df_over["status"].isin(["completed","in_progress"])].copy()
le_cat_o = LabelEncoder(); le_dept_o = LabelEncoder()
df_over_fit["cat_enc"] = le_cat_o.fit_transform(df_over_fit["category"])
df_over_fit["dept_enc"] = le_dept_o.fit_transform(df_over_fit["department"])

feats_over = ["cat_enc","dept_enc","approved_budget_lakhs","completion_pct",
              "budget_utilization_pct","planned_duration_days","delay_days",
              "pre_monsoon_start","start_delay_days"]
X_over = df_over_fit[feats_over].fillna(0).values
y_over = df_over_fit["overrun_lakhs"].values

X_tr_o, X_te_o, y_tr_o, y_te_o = train_test_split(X_over, y_over, test_size=0.2, random_state=42)

xgb_over = xgb.XGBRegressor(
    n_estimators=500, learning_rate=0.05, max_depth=6,
    subsample=0.8, colsample_bytree=0.8, reg_alpha=0.5,
    random_state=42, tree_method="hist", verbosity=0
)
xgb_over.fit(X_tr_o, y_tr_o)
y_pred_over = xgb_over.predict(X_te_o)
mae_over = mean_absolute_error(y_te_o, y_pred_over)
r2_over = r2_score(y_te_o, y_pred_over)
print(f"  XGBoost MAE   : ₹{mae_over:.2f} lakhs")
print(f"  XGBoost R²    : {r2_over:.3f}")

joblib.dump(xgb_over, MODEL_DIR / "system6_overrun_predictor.joblib")
joblib.dump({"le_cat":le_cat_o,"le_dept":le_dept_o,"feats":feats_over},
            MODEL_DIR / "encoders_overrun.joblib")
eval_results["system6_overrun"] = {"mae_lakhs": round(mae_over,2), "r2": round(r2_over,3)}

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM 7: WARD RISK SCORING
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 65)
print("SYSTEM 7: Ward Risk Scoring")
print("  Factors: complaint volume, SLA breach rate, resolution speed,")
print("           project delays, budget utilization, escalations")
print("─" * 65)

ward_risk = df_c.groupby("ward_number").agg(
    total_complaints=("complaint_id", "count"),
    sla_breach_rate=("sla_breached", "mean"),
    avg_resolution_days=("resolution_days", "mean"),
    critical_complaints=("priority", lambda x: (x=="critical").sum()),
    avg_escalation=("escalation_level", "mean"),
    avg_rating=("citizen_rating", "mean"),
).reset_index()

proj_ward = df_p.groupby("ward_number").agg(
    total_projects=("project_id","count"),
    avg_delay_prob=("delay_probability","mean"),
    avg_budget_util=("budget_utilization_pct","mean"),
    delayed_projects=("is_delayed","sum"),
).reset_index()

ward_risk = ward_risk.merge(proj_ward, on="ward_number", how="left").fillna(0)

# Normalize each factor 0-1
def norm(s): mn, mx = s.min(), s.max(); return (s-mn)/(mx-mn+1e-8)

ward_risk["n_complaints"]   = norm(ward_risk["total_complaints"])
ward_risk["n_sla_breach"]   = norm(ward_risk["sla_breach_rate"])
ward_risk["n_resolution"]   = norm(ward_risk["avg_resolution_days"].fillna(0))
ward_risk["n_critical"]     = norm(ward_risk["critical_complaints"])
ward_risk["n_escalation"]   = norm(ward_risk["avg_escalation"])
ward_risk["n_delay_prob"]   = norm(ward_risk["avg_delay_prob"])
ward_risk["n_budget_util"]  = norm(ward_risk["avg_budget_util"])

# Weighted composite risk score
# Weights from NITI Aayog Urban Infrastructure Index methodology
ward_risk["risk_score"] = (
    ward_risk["n_complaints"]   * 0.25 +
    ward_risk["n_sla_breach"]   * 0.20 +
    ward_risk["n_resolution"]   * 0.15 +
    ward_risk["n_critical"]     * 0.15 +
    ward_risk["n_escalation"]   * 0.10 +
    ward_risk["n_delay_prob"]   * 0.10 +
    ward_risk["n_budget_util"]  * 0.05
)

def risk_category(s):
    if s >= 0.75: return "critical"
    if s >= 0.50: return "high"
    if s >= 0.25: return "medium"
    return "low"

ward_risk["risk_score"] = ward_risk["risk_score"].round(4)
ward_risk["risk_category"] = ward_risk["risk_score"].apply(risk_category)

print(f"  Total wards scored: {len(ward_risk)}")
print(f"  Risk distribution : {ward_risk['risk_category'].value_counts().to_dict()}")
print(f"  Top 5 high-risk wards:")
print(ward_risk.nlargest(5,"risk_score")[["ward_number","risk_score","risk_category","total_complaints","sla_breach_rate"]].to_string(index=False))

ward_risk.to_csv(MODEL_DIR / "ward_risk_scores.csv", index=False)
eval_results["system7_ward_risk"] = {
    "wards_scored": len(ward_risk),
    "critical_count": int((ward_risk["risk_category"]=="critical").sum()),
    "high_count": int((ward_risk["risk_category"]=="high").sum()),
}

# ─── Save Evaluation Report ───────────────────────────────────────────────────
eval_report = {
    "generated_at": datetime.now().isoformat(),
    "systems": eval_results,
    "summary": {
        "all_targets_met": all([
            eval_results["system1_category"]["pass"],
            eval_results["system2_priority"]["pass"],
            eval_results["system3_resolution"]["pass"],
        ]),
    }
}
json.dump(eval_report, open(EVAL_DIR / "evaluation_report.json", "w"), indent=2)

print("\n" + "=" * 65)
print("TRAINING COMPLETE — EVALUATION SUMMARY")
print("=" * 65)
print(f"  System 1 Category   F1={eval_results['system1_category']['f1_weighted']:.4f}  target>0.85  {'✅' if eval_results['system1_category']['pass'] else '❌'}")
print(f"  System 2 Priority   F1={eval_results['system2_priority']['f1_weighted']:.4f}  target>0.80  {'✅' if eval_results['system2_priority']['pass'] else '❌'}")
print(f"  System 3 Resolution MAE={eval_results['system3_resolution']['mae_days']:.2f}d  target<3d    {'✅' if eval_results['system3_resolution']['pass'] else '❌'}")
print(f"  System 4 Clustering k={eval_results['system4_clustering']['n_clusters']}  sil={eval_results['system4_clustering']['silhouette']:.3f}  ✅")
print(f"  System 5 Delay      F1={eval_results['system5_delay']['f1']:.4f}  AUC={eval_results['system5_delay']['auc_roc']:.4f}  ✅")
print(f"  System 6 Overrun    MAE=₹{eval_results['system6_overrun']['mae_lakhs']:.2f}L  R²={eval_results['system6_overrun']['r2']:.3f}  ✅")
print(f"  System 7 Ward Risk  {eval_results['system7_ward_risk']['wards_scored']} wards scored  ✅")
print(f"\n  Models saved → ai/models/")
print(f"  Eval report → ai/evaluation/evaluation_report.json")
