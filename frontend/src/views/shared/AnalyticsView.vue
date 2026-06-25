<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { analyticsApi, aiApi } from '@/services/api'
import StatCard from '@/components/common/StatCard.vue'
import {
  AlertTriangle,
  Building2,
  CheckCircle2,
  CircleDollarSign,
  ClipboardList,
  Droplets,
  Landmark,
  Lightbulb,
  MapPinned,
  Recycle,
  TrafficCone,
  Trees,
} from 'lucide-vue-next'

const overview = ref<any>(null)
const byCategory = ref<any[]>([])
const byWard = ref<any[]>([])
const deptPerf = ref<any[]>([])
const wardRisk = ref<any[]>([])
const projByStatus = ref<any[]>([])

onMounted(async () => {
  const [ov, cat, ward, dept, risk, proj] = await Promise.all([
    analyticsApi.overview(), analyticsApi.complaintsByCategory(),
    analyticsApi.complaintsByWard(15), analyticsApi.departmentPerformance(),
    aiApi.wardRisk(), analyticsApi.projectsByStatus(),
  ])
  overview.value = ov.data; byCategory.value = cat.data
  byWard.value = ward.data; deptPerf.value = dept.data
  wardRisk.value = (risk.data as any[]).filter(w => w.risk_category !== 'low').slice(0,15)
  projByStatus.value = proj.data
})

const RISK_BADGE: Record<string,string> = { critical:'badge-critical', high:'badge-high', medium:'badge-medium', low:'badge-low' }
const CAT_ICONS = { roads: TrafficCone, water_supply: Droplets, drainage: MapPinned, electricity: Lightbulb, parks: Trees, buildings: Building2, sanitation: Recycle }
</script>
<template>
  <div class="space-y-6">
    <div class="page-header"><div class="muted-kicker">City intelligence</div><h1 class="page-title">Analytics</h1><p class="page-subtitle">Citywide performance metrics for complaints, delivery efficiency, ward stress, and project utilization.</p></div>

    <div v-if="overview" class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard title="Total Complaints" :value="overview.complaints.total.toLocaleString()" :icon="ClipboardList" color="blue" />
      <StatCard title="Resolution Rate" :value="`${overview.complaints.resolution_rate}%`" :icon="CheckCircle2" color="green" />
      <StatCard title="SLA Breached" :value="overview.complaints.sla_breached.toLocaleString()" :icon="AlertTriangle" color="red" />
      <StatCard title="Budget Utilization" :value="`${overview.projects.budget_utilization_pct}%`" :icon="CircleDollarSign" color="amber" />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- By Category -->
      <div class="card card-body">
        <h3 class="panel-title mb-4">Complaints by Category</h3>
        <div class="space-y-3">
          <div v-for="item in byCategory.slice(0,7)" :key="item.category" class="flex items-center gap-3">
            <span class="icon-chip h-9 w-9">
              <component :is="CAT_ICONS[item.category] ?? Landmark" class="h-4 w-4" />
            </span>
            <div class="text-sm text-slate-600 dark:text-slate-300 w-32 truncate capitalize">{{ item.category.replace('_',' ') }}</div>
            <div class="flex-1 h-2 bg-surface-100 dark:bg-surface-800 rounded-full overflow-hidden">
              <div class="h-full bg-primary-500 rounded-full" :style="`width:${(item.count/(byCategory[0]?.count||1))*100}%`"></div>
            </div>
            <div class="text-sm font-medium w-16 text-right">{{ item.count.toLocaleString() }}</div>
          </div>
        </div>
      </div>

      <!-- Projects by Status -->
      <div class="card card-body">
        <h3 class="panel-title mb-4">Projects by Status</h3>
        <div class="space-y-3">
          <div v-for="item in projByStatus" :key="item.status" class="flex items-center gap-3">
            <div class="text-sm text-slate-600 dark:text-slate-300 w-28 truncate capitalize">{{ item.status.replace('_',' ') }}</div>
            <div class="flex-1 h-2 bg-surface-100 dark:bg-surface-800 rounded-full overflow-hidden">
              <div class="h-full bg-teal-500 rounded-full" :style="`width:${(item.count/(projByStatus.reduce((a:number,b:any)=>a+b.count,0)||1))*100}%`"></div>
            </div>
            <div class="text-sm font-medium w-12 text-right">{{ item.count }}</div>
          </div>
        </div>
      </div>

      <!-- Top Complaint Wards -->
      <div class="card card-body">
        <h3 class="panel-title mb-4">Top Complaint Wards</h3>
        <div class="space-y-2">
          <div v-for="(w,i) in byWard.slice(0,10)" :key="w.ward" class="flex items-center gap-3">
            <div class="w-6 h-6 rounded-full bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 text-xs font-bold flex items-center justify-center shrink-0">{{ i+1 }}</div>
            <div class="text-sm text-slate-700 dark:text-slate-200 flex-1">{{ w.ward }}</div>
            <div class="text-sm font-medium text-slate-600 dark:text-slate-300">{{ w.count.toLocaleString() }}</div>
          </div>
        </div>
      </div>

      <!-- Ward Risk -->
      <div class="card card-body">
        <div class="mb-4 flex items-center justify-between">
          <h3 class="panel-title">High Risk Wards (AI)</h3>
          <AlertTriangle class="h-4 w-4 text-amber-500" />
        </div>
        <div class="space-y-2 max-h-64 overflow-y-auto scrollbar-thin">
          <div v-for="w in wardRisk" :key="w.ward_number" class="flex items-center justify-between py-1.5 border-b border-surface-100 dark:border-surface-800 last:border-0">
            <div>
              <div class="text-sm font-medium text-slate-800 dark:text-slate-200">{{ w.ward_number }}</div>
              <div class="text-xs text-slate-400">score: {{ (w.risk_score*100).toFixed(0) }} · {{ w.total_complaints }} complaints</div>
            </div>
            <span :class="['badge', RISK_BADGE[w.risk_category]]">{{ w.risk_category }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Department Performance Table -->
    <div class="table-wrap">
      <div class="card-header"><h3 class="panel-title">Department Performance</h3></div>
      <table class="table">
        <thead><tr><th>Department</th><th>Total Complaints</th><th>Resolved</th><th>Resolution Rate</th><th>Active Projects</th></tr></thead>
        <tbody>
          <tr v-for="d in deptPerf" :key="d.id">
            <td class="font-medium">{{ d.name }}<br><span class="text-xs text-slate-400">{{ d.code }}</span></td>
            <td>{{ d.total_complaints?.toLocaleString() ?? 0 }}</td>
            <td>{{ d.resolved_complaints?.toLocaleString() ?? 0 }}</td>
            <td>
              <div class="flex items-center gap-2">
                <div class="w-20 h-1.5 bg-surface-100 dark:bg-surface-800 rounded-full overflow-hidden">
                  <div class="h-full bg-green-500 rounded-full" :style="`width:${d.resolution_rate}%`"></div>
                </div>
                <span class="text-xs">{{ d.resolution_rate }}%</span>
              </div>
            </td>
            <td>{{ d.active_projects }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
