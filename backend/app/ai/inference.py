"""
CivilInc AI Inference Service
Loads trained models and exposes prediction methods.
Called by FastAPI endpoints — no model training here.
"""
import joblib
import numpy as np
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger("civilinc.ai")

MODEL_DIR = Path(__file__).parents[3] / "ai" / "models"

_models: dict = {}

def _load():
    """Lazy-load all models on first use."""
    global _models
    if _models:
        return
    try:
        _models = {
            "tfidf":        joblib.load(MODEL_DIR / "tfidf_vectorizer.joblib"),
            "cat_clf":      joblib.load(MODEL_DIR / "system1_category_classifier.joblib"),
            "enc_cat":      joblib.load(MODEL_DIR / "encoders_category.joblib"),
            "le_cat":       joblib.load(MODEL_DIR / "label_encoder_category.joblib"),
            "prio_clf":     joblib.load(MODEL_DIR / "system2_priority_predictor.joblib"),
            "enc_prio":     joblib.load(MODEL_DIR / "encoders_priority.joblib"),
            "res_reg":      joblib.load(MODEL_DIR / "system3_resolution_predictor.joblib"),
            "enc_res":      joblib.load(MODEL_DIR / "encoders_resolution.joblib"),
            "tfidf_clust":  joblib.load(MODEL_DIR / "tfidf_cluster.joblib"),
            "svd_clust":    joblib.load(MODEL_DIR / "svd_cluster.joblib"),
            "kmeans":       joblib.load(MODEL_DIR / "system4_kmeans.joblib"),
            "delay_clf":    joblib.load(MODEL_DIR / "system5_delay_predictor.joblib"),
            "enc_delay":    joblib.load(MODEL_DIR / "encoders_delay.joblib"),
            "overrun_reg":  joblib.load(MODEL_DIR / "system6_overrun_predictor.joblib"),
            "enc_overrun":  joblib.load(MODEL_DIR / "encoders_overrun.joblib"),
        }
        logger.info("AI models loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load AI models: {e}")
        _models = {}


def predict_complaint(title: str, description: str, zone: str = "Central", source: str = "web") -> dict:
    """
    System 1 + 2 + 3 + 4: Full complaint triage.
    Returns category, priority, resolution_days, cluster_id, confidence.
    """
    _load()
    if not _models:
        return {"error": "Models not loaded"}

    try:
        # System 1: Category
        enc_cat = _models["enc_cat"]
        le_zone = enc_cat["le_zone"]; le_src = enc_cat["le_src"]
        zone_enc = le_zone.transform([zone])[0] if zone in le_zone.classes_ else 0
        src_enc  = le_src.transform([source])[0] if source in le_src.classes_ else 0
        title_feat = _models["tfidf"].transform([title]).toarray()
        X_cat = np.hstack([title_feat, [[zone_enc, src_enc]]])
        cat_encoded = _models["cat_clf"].predict(X_cat)[0]
        cat_proba = _models["cat_clf"].predict_proba(X_cat)[0]
        category = _models["le_cat"].inverse_transform([cat_encoded])[0]
        confidence = float(np.max(cat_proba))

        # Department mapping
        DEPT_MAP = {"roads":"ROADS","water_supply":"WATER","drainage":"WATER",
                    "electricity":"ELEC","parks":"PARKS","buildings":"BLDG","sanitation":"SWM"}
        SLA_MAP  = {"ROADS":48,"WATER":24,"ELEC":12,"PARKS":72,"BLDG":96,"SWM":24}
        dept = DEPT_MAP.get(category, "ROADS")
        sla_hours = SLA_MAP.get(dept, 48)

        # System 2: Priority
        enc_p = _models["enc_prio"]
        le_sub = enc_p["le_sub"]; le_zone_p = enc_p["le_zone"]
        le_src_p = enc_p["le_src"]; le_dept_p = enc_p["le_dept"]
        le_cat_p = enc_p["le_cat"]; le_prio = enc_p["le_prio"]

        crit_kws = ["burst","collapse","fallen","exposed","overflow","danger","accident","emergency"]
        has_crit = int(any(k in title.lower() for k in crit_kws))
        sub_enc  = 0  # unknown sub_category at this stage
        zone_enc2 = le_zone_p.transform([zone])[0] if zone in le_zone_p.classes_ else 0
        src_enc2  = le_src_p.transform([source])[0] if source in le_src_p.classes_ else 0
        dept_enc  = le_dept_p.transform([dept])[0] if dept in le_dept_p.classes_ else 0
        cat_enc_p = le_cat_p.transform([category])[0] if category in le_cat_p.classes_ else 0
        X_prio = np.array([[cat_enc_p, sub_enc, zone_enc2, src_enc2, dept_enc,
                            sla_hours, 0, 300, has_crit, 0]])  # defaults
        prio_encoded = _models["prio_clf"].predict(X_prio)[0]
        priority = le_prio.inverse_transform([prio_encoded])[0]

        # System 3: Resolution time
        enc_r = _models["enc_res"]
        le_cat_r = enc_r["le_cat"]; le_prio_r = enc_r["le_prio"]
        le_zone_r = enc_r["le_zone"]; le_src_r = enc_r["le_src"]
        cat_enc_r  = le_cat_r.transform([category])[0] if category in le_cat_r.classes_ else 0
        prio_enc_r = le_prio_r.transform([priority])[0] if priority in le_prio_r.classes_ else 0
        zone_enc_r = le_zone_r.transform([zone])[0] if zone in le_zone_r.classes_ else 0
        src_enc_r  = le_src_r.transform([source])[0] if source in le_src_r.classes_ else 0
        X_res = np.array([[cat_enc_r, prio_enc_r, zone_enc_r, src_enc_r, sla_hours, 0]])
        resolution_days = max(1, round(float(_models["res_reg"].predict(X_res)[0])))

        # System 4: Cluster
        text = title + " " + description
        X_clust = _models["tfidf_clust"].transform([text])
        X_svd   = _models["svd_clust"].transform(X_clust)
        cluster_id = int(_models["kmeans"].predict(X_svd)[0])

        return {
            "category": category,
            "department": dept,
            "priority": priority,
            "resolution_days": resolution_days,
            "cluster_id": cluster_id,
            "confidence": round(confidence, 3),
            "sla_hours": sla_hours,
        }
    except Exception as e:
        logger.error(f"Complaint prediction error: {e}")
        return {"error": str(e)}


def predict_project_risk(
    category: str, department: str, completion_pct: float,
    budget_utilization_pct: float, elapsed_pct: float,
    planned_duration_days: int, pre_monsoon_start: int = 0,
    start_delay_days: int = 0, source_fund: str = "BBMP Own Funds",
    approved_budget_lakhs: float = 0.0, actual_cost_lakhs: float = 0.0,
    delay_days: float = 0.0,
) -> dict:
    """System 5 + 6: Project delay probability + budget overrun."""
    _load()
    if not _models:
        return {"error": "Models not loaded"}

    try:
        enc_d = _models["enc_delay"]
        le_cat_d = enc_d["le_cat"]; le_dept_d = enc_d["le_dept"]; le_fund_d = enc_d["le_fund"]
        cat_enc  = le_cat_d.transform([category])[0] if category in le_cat_d.classes_ else 0
        dept_enc = le_dept_d.transform([department])[0] if department in le_dept_d.classes_ else 0
        fund_enc = le_fund_d.transform([source_fund])[0] if source_fund in le_fund_d.classes_ else 0
        pace = (completion_pct / elapsed_pct) if elapsed_pct > 0 else 1.0
        X_del = np.array([[cat_enc, dept_enc, fund_enc, completion_pct, budget_utilization_pct,
                           elapsed_pct, pace, pre_monsoon_start, start_delay_days, planned_duration_days]])
        delay_prob = float(_models["delay_clf"].predict_proba(X_del)[0][1])

        enc_o = _models["enc_overrun"]
        le_cat_o = enc_o["le_cat"]; le_dept_o = enc_o["le_dept"]
        cat_enc_o  = le_cat_o.transform([category])[0] if category in le_cat_o.classes_ else 0
        dept_enc_o = le_dept_o.transform([department])[0] if department in le_dept_o.classes_ else 0
        X_over = np.array([[cat_enc_o, dept_enc_o, approved_budget_lakhs, completion_pct,
                            budget_utilization_pct, planned_duration_days, delay_days,
                            pre_monsoon_start, start_delay_days]])
        expected_overrun = max(0.0, float(_models["overrun_reg"].predict(X_over)[0]))

        risk_score = round(delay_prob * 0.6 + min(1, budget_utilization_pct/100) * 0.4, 3)
        risk_cat = ("critical" if risk_score>0.75 else "high" if risk_score>0.50
                    else "medium" if risk_score>0.25 else "low")

        return {
            "delay_probability": round(delay_prob, 3),
            "expected_overrun_lakhs": round(expected_overrun, 2),
            "risk_score": risk_score,
            "risk_category": risk_cat,
        }
    except Exception as e:
        logger.error(f"Project risk prediction error: {e}")
        return {"error": str(e)}
