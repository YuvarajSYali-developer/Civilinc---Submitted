<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { projectsApi } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import type { Project } from '@/types'
import { AlertTriangle, ArrowLeft, ArrowRight, Plus, Search } from 'lucide-vue-next'

const auth = useAuthStore()
const projects = ref<Project[]>([])
const total = ref(0); const page = ref(1); const loading = ref(false)
const search = ref(''); const statusFilter = ref(''); const atRisk = ref(false)

const STATUSES = ['planning','tendering','in_progress','on_hold','completed','cancelled']
const STATUS_BADGE: Record<string,string> = {
  planning:'badge-pending', tendering:'badge-pending',
  in_progress:'badge-in-progress', on_hold:'badge-medium',
  completed:'badge-resolved', cancelled:'badge-pending'
}
const RISK_COLOR: Record<string,string> = { critical:'text-red-500', high:'text-orange-500', medium:'text-yellow-500', low:'text-green-500' }

async function fetch() {
  loading.value = true
  try {
    const { data } = await projectsApi.list({
      page: page.value, page_size: 20,
      status: statusFilter.value || undefined,
      at_risk: atRisk.value || undefined,
      search: search.value || undefined,
    })
    projects.value = data.items; total.value = data.total
  } finally { loading.value = false }
}

onMounted(fetch)
watch([statusFilter, atRisk], () => { page.value = 1; fetch() })
let t: any; watch(search, () => { clearTimeout(t); t = setTimeout(() => { page.value=1; fetch() }, 400) })
</script>
<template>
  <div class="space-y-5">
    <div class="page-header flex flex-wrap items-center justify-between gap-3">
      <div><div class="muted-kicker">Project delivery</div><h1 class="page-title">Projects</h1><p class="page-subtitle">{{ total.toLocaleString() }} infrastructure projects under planning, delivery, and review.</p></div>
      <RouterLink v-if="auth.isStaff" to="/projects/new" class="btn-primary"><Plus class="h-4 w-4" />New Project</RouterLink>
    </div>

    <div class="card card-body flex flex-wrap gap-3">
      <div class="relative">
        <Search class="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input v-model="search" class="input max-w-xs pl-11" placeholder="Search projects…" />
      </div>
      <select v-model="statusFilter" class="select w-40">
        <option value="">All Status</option>
        <option v-for="s in STATUSES" :key="s" :value="s">{{ s.replace('_',' ') }}</option>
      </select>
      <label class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300 cursor-pointer select-none">
        <input type="checkbox" v-model="atRisk" class="rounded" />
        <span class="inline-flex items-center gap-2"><AlertTriangle class="h-4 w-4 text-amber-500" />At Risk Only</span>
      </label>
    </div>

    <div class="table-wrap">
      <div v-if="loading" class="p-8 text-center text-slate-400">Loading…</div>
      <table v-else class="table">
        <thead><tr><th>ID</th><th>Title</th><th>Category</th><th>Status</th><th>Progress</th><th>Delay Risk</th><th>Budget</th><th>Ward</th><th></th></tr></thead>
        <tbody>
          <tr v-for="p in projects" :key="p.id">
            <td class="font-mono text-xs">{{ p.project_number }}</td>
            <td class="max-w-xs"><div class="font-medium text-sm truncate">{{ p.title }}</div></td>
            <td><span class="text-xs capitalize">{{ p.category?.replace('_',' ') }}</span></td>
            <td><span :class="[STATUS_BADGE[p.status]||'badge-pending','badge']">{{ p.status?.replace('_',' ') }}</span></td>
            <td class="w-28">
              <div class="flex items-center gap-2">
                <div class="flex-1 h-1.5 bg-surface-100 dark:bg-surface-800 rounded-full">
                  <div class="h-full bg-blue-500 rounded-full" :style="`width:${p.completion_percentage}%`"></div>
                </div>
                <span class="text-xs text-slate-400 w-8">{{ p.completion_percentage }}%</span>
              </div>
            </td>
            <td>
              <span v-if="p.delay_probability" :class="[RISK_COLOR[p.risk_category||'low'],'text-sm font-bold']">
                {{ Math.round(p.delay_probability*100) }}%
              </span>
              <span v-else class="text-slate-300 text-xs">—</span>
            </td>
            <td class="text-sm">{{ p.approved_budget ? `₹${(p.approved_budget/100).toFixed(1)}Cr` : '—' }}</td>
            <td class="text-xs text-slate-400">{{ p.ward_number ?? '—' }}</td>
            <td><RouterLink :to="`/projects/${p.id}`" class="btn-secondary btn-sm">View</RouterLink></td>
          </tr>
          <tr v-if="projects.length===0"><td colspan="9" class="text-center text-slate-400 py-8">No projects found</td></tr>
        </tbody>
      </table>
      <div class="flex items-center justify-between px-4 py-3 border-t">
        <span class="text-sm text-slate-400">Page {{ page }} · {{ total }} total</span>
        <div class="flex gap-2">
          <button :disabled="page<=1" @click="page--;fetch()" class="btn-secondary btn-sm"><ArrowLeft class="h-4 w-4" />Prev</button>
          <button :disabled="page*20>=total" @click="page++;fetch()" class="btn-secondary btn-sm">Next<ArrowRight class="h-4 w-4" /></button>
        </div>
      </div>
    </div>
  </div>
</template>
