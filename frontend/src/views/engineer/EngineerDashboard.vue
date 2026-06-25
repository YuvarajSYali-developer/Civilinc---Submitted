<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { complaintsApi, projectsApi, analyticsApi } from '@/services/api'
import StatCard from '@/components/common/StatCard.vue'
import { AlertTriangle, CheckCircle2, ClipboardList, Hammer, Wrench } from 'lucide-vue-next'
const auth = useAuthStore()
const myComplaints = ref<any[]>([]); const atRiskProjects = ref<any[]>([]); const stats = ref<any[]>([])
const getCount = (s: string) => stats.value.find((x:any)=>x.status===s)?.count??0
const STATUS_BADGE: Record<string,string> = { pending:'badge-pending', assigned:'badge-in-progress', in_progress:'badge-in-progress', resolved:'badge-resolved', escalated:'badge-critical' }
onMounted(async () => {
  const [c, r, s] = await Promise.all([complaintsApi.list({ page_size:5, status:'assigned' }), projectsApi.atRisk(0.6), analyticsApi.complaintsByStatus()])
  myComplaints.value = c.data.items; atRiskProjects.value = r.data.slice(0,5); stats.value = s.data
})
</script>
<template>
  <div class="space-y-6">
    <div class="page-header"><div class="muted-kicker">Execution desk</div><h1 class="page-title">Engineer Dashboard</h1><p class="page-subtitle">Welcome back, {{ auth.user?.full_name }}. Review assigned complaints and watch delay signals before projects slip further.</p></div>
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard title="Assigned" :value="String(getCount('assigned'))" :icon="ClipboardList" color="blue" />
      <StatCard title="In Progress" :value="String(getCount('in_progress'))" :icon="Wrench" color="amber" />
      <StatCard title="Resolved" :value="String(getCount('resolved'))" :icon="CheckCircle2" color="green" />
      <StatCard title="At-Risk Projects" :value="String(atRiskProjects.length)" :icon="AlertTriangle" color="red" />
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="table-wrap">
        <div class="card-header"><h3 class="panel-title">Assigned Complaints</h3></div>
        <table class="table">
          <thead><tr><th>ID</th><th>Title</th><th>Priority</th><th>Status</th></tr></thead>
          <tbody>
            <tr v-for="c in myComplaints" :key="c.id">
              <td><RouterLink :to="`/complaints/${c.id}`" class="text-primary-600 dark:text-primary-400 font-mono text-xs hover:underline">{{ c.complaint_number }}</RouterLink></td>
              <td class="max-w-xs"><div class="text-sm truncate">{{ c.title }}</div></td>
              <td><span :class="`badge-${c.priority} badge`">{{ c.priority }}</span></td>
              <td><span :class="[STATUS_BADGE[c.status]||'badge-pending','badge']">{{ c.status?.replace('_',' ') }}</span></td>
            </tr>
            <tr v-if="myComplaints.length===0"><td colspan="4" class="text-center text-slate-400 py-6">None assigned</td></tr>
          </tbody>
        </table>
      </div>
      <div class="card card-body">
        <div class="mb-4 flex items-center justify-between">
          <h3 class="panel-title">At-Risk Projects</h3>
          <Hammer class="h-4 w-4 text-slate-400" />
        </div>
        <div class="space-y-3">
          <div v-for="p in atRiskProjects" :key="p.id" class="p-3 bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/30 rounded-lg">
            <div class="flex items-start justify-between gap-2">
              <div><div class="text-sm font-medium text-slate-800 dark:text-slate-200 line-clamp-1">{{ p.title }}</div><div class="text-xs text-slate-400 mt-0.5">{{ p.project_number }} · {{ p.ward_number }}</div></div>
              <div class="text-right shrink-0"><div class="text-sm font-bold text-red-600">{{ Math.round((p.delay_probability||0)*100) }}%</div><div class="text-xs text-slate-400">delay risk</div></div>
            </div>
            <div class="mt-2 h-1.5 bg-surface-200 dark:bg-surface-700 rounded-full"><div class="h-full bg-blue-500 rounded-full" :style="`width:${p.completion_percentage}%`"></div></div>
            <div class="text-xs text-slate-400 mt-1">{{ p.completion_percentage }}% complete</div>
          </div>
          <div v-if="atRiskProjects.length===0" class="text-center text-slate-400 py-4">No at-risk projects</div>
        </div>
      </div>
    </div>
  </div>
</template>
