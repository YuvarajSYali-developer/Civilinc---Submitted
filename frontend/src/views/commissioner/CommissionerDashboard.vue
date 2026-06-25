<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { analyticsApi, aiApi } from '@/services/api'
import StatCard from '@/components/common/StatCard.vue'
import { AlertTriangle, ArrowUpRight, BriefcaseBusiness, CheckCircle2, ClipboardList } from 'lucide-vue-next'
const overview = ref<any>(null); const byCategory = ref<any[]>([]); const deptPerf = ref<any[]>([]); const wardRisks = ref<any[]>([])
const RISK_BADGE: Record<string,string> = { critical:'badge-critical', high:'badge-high', medium:'badge-medium', low:'badge-low' }
onMounted(async () => {
  const [ov, cat, dept, wr] = await Promise.all([analyticsApi.overview(), analyticsApi.complaintsByCategory(), analyticsApi.departmentPerformance(), aiApi.wardRisk()])
  overview.value = ov.data; byCategory.value = cat.data; deptPerf.value = dept.data
  wardRisks.value = (wr.data as any[]).sort((a,b)=>b.risk_score-a.risk_score).slice(0,10)
})
</script>
<template>
  <div class="space-y-6">
    <div class="page-header flex items-center justify-between">
      <div><div class="muted-kicker">Executive oversight</div><h1 class="page-title">Commissioner Dashboard</h1><p class="page-subtitle">A live operating view of complaints, departmental throughput, and emerging ward-level infrastructure risk.</p></div>
      <div class="text-sm text-slate-500 dark:text-slate-400">{{ new Date().toLocaleDateString('en-IN',{weekday:'long',year:'numeric',month:'long',day:'numeric'}) }}</div>
    </div>
    <div v-if="overview" class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard title="Total Complaints" :value="overview.complaints.total.toLocaleString()" :icon="ClipboardList" :sub="`${overview.complaints.pending} pending`" color="blue" />
      <StatCard title="Resolution Rate" :value="`${overview.complaints.resolution_rate}%`" :icon="CheckCircle2" :sub="`${overview.complaints.resolved.toLocaleString()} resolved`" color="green" />
      <StatCard title="Critical Issues" :value="overview.complaints.critical.toString()" :icon="AlertTriangle" :sub="`${overview.complaints.sla_breached} SLA breached`" color="red" />
      <StatCard title="Active Projects" :value="overview.projects.active.toString()" :icon="BriefcaseBusiness" :sub="`${overview.projects.at_risk} at risk`" color="amber" />
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="card card-body lg:col-span-2">
        <div class="mb-4 flex items-center justify-between">
          <h3 class="panel-title">Complaints by Category</h3>
          <span class="muted-kicker">Top categories</span>
        </div>
        <div class="space-y-3">
          <div v-for="item in byCategory.slice(0,7)" :key="item.category" class="flex items-center gap-3">
            <div class="text-sm text-slate-600 dark:text-slate-300 w-28 truncate capitalize">{{ item.category.replace('_',' ') }}</div>
            <div class="flex-1 h-2 bg-surface-100 dark:bg-surface-800 rounded-full overflow-hidden">
              <div class="h-full bg-primary-500 rounded-full" :style="`width:${(item.count/(byCategory[0]?.count||1))*100}%`"></div>
            </div>
            <div class="text-sm font-medium w-14 text-right">{{ item.count.toLocaleString() }}</div>
          </div>
        </div>
      </div>
      <div class="card card-body">
        <div class="mb-4 flex items-center justify-between">
          <h3 class="panel-title">High Risk Wards</h3>
          <AlertTriangle class="h-4 w-4 text-amber-500" />
        </div>
        <div class="space-y-2">
          <div v-for="w in wardRisks.slice(0,8)" :key="w.ward_number" class="flex items-center justify-between py-1.5 border-b border-surface-100 dark:border-surface-800 last:border-0">
            <div><div class="text-sm font-medium text-slate-800 dark:text-slate-200">{{ w.ward_number }}</div><div class="text-xs text-slate-400">{{ w.total_complaints }} complaints</div></div>
            <span :class="['badge', RISK_BADGE[w.risk_category]]">{{ w.risk_category }}</span>
          </div>
        </div>
      </div>
    </div>
    <div class="table-wrap">
      <div class="card-header flex items-center justify-between"><h3 class="panel-title">Department Performance</h3><span class="inline-flex items-center gap-2 text-xs font-semibold text-slate-400">Operational throughput <ArrowUpRight class="h-3.5 w-3.5" /></span></div>
      <table class="table">
        <thead><tr><th>Department</th><th>Complaints</th><th>Resolved</th><th>Resolution Rate</th><th>Projects</th></tr></thead>
        <tbody>
          <tr v-for="d in deptPerf" :key="d.id">
            <td><span class="font-medium">{{ d.name }}</span><br><span class="text-xs text-slate-400">{{ d.code }}</span></td>
            <td>{{ d.total_complaints?.toLocaleString() ?? 0 }}</td>
            <td>{{ d.resolved_complaints?.toLocaleString() ?? 0 }}</td>
            <td><div class="flex items-center gap-2"><div class="w-16 h-1.5 bg-surface-100 dark:bg-surface-800 rounded-full"><div class="h-full bg-green-500 rounded-full" :style="`width:${d.resolution_rate}%`"></div></div><span class="text-xs">{{ d.resolution_rate }}%</span></div></td>
            <td>{{ d.active_projects }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
