<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { complaintsApi } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import type { Complaint } from '@/types'
import { AlertTriangle, ArrowLeft, ArrowRight, FilePenLine, RotateCcw, Search } from 'lucide-vue-next'

const auth = useAuthStore()
const complaints = ref<Complaint[]>([])
const total = ref(0); const page = ref(1); const loading = ref(false)
const search = ref(''); const statusFilter = ref(''); const priorityFilter = ref(''); const categoryFilter = ref('')

const CATEGORIES = ['roads','water_supply','drainage','electricity','parks','buildings','sanitation']
const STATUSES = ['pending','under_review','assigned','in_progress','resolved','closed','escalated']
const PRIORITIES = ['critical','high','medium','low']
const BADGE: Record<string,string> = { pending:'badge-pending', under_review:'badge-pending', assigned:'badge-in-progress', in_progress:'badge-in-progress', resolved:'badge-resolved', closed:'badge-resolved', escalated:'badge-critical', rejected:'badge-pending' }
const PRI_BADGE: Record<string,string> = { critical:'badge-critical', high:'badge-high', medium:'badge-medium', low:'badge-low' }

async function fetch() {
  loading.value = true
  try {
    const { data } = await complaintsApi.list({
      page: page.value, page_size: 20, search: search.value || undefined,
      status: statusFilter.value || undefined, priority: priorityFilter.value || undefined,
      category: categoryFilter.value || undefined
    })
    complaints.value = data.items; total.value = data.total
  } finally { loading.value = false }
}

onMounted(fetch)
watch([statusFilter, priorityFilter, categoryFilter], () => { page.value = 1; fetch() })
let timer: any
watch(search, () => { clearTimeout(timer); timer = setTimeout(() => { page.value = 1; fetch() }, 400) })

function resetFilters() { statusFilter.value=''; priorityFilter.value=''; categoryFilter.value=''; search.value='' }
</script>
<template>
  <div class="space-y-5">
    <div class="page-header flex flex-wrap items-center justify-between gap-3">
      <div><div class="muted-kicker">Complaint operations</div><h1 class="page-title">Complaints</h1><p class="page-subtitle">{{ total.toLocaleString() }} total complaints across the platform.</p></div>
      <div class="flex gap-2">
        <RouterLink v-if="auth.isCitizen" to="/complaints/new" class="btn-primary"><FilePenLine class="h-4 w-4" />Report Issue</RouterLink>
      </div>
    </div>

    <!-- Filters -->
    <div class="card card-body flex flex-wrap gap-3">
      <div class="relative">
        <Search class="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input v-model="search" class="input max-w-xs pl-11" placeholder="Search complaints…" />
      </div>
      <select v-model="statusFilter" class="select w-36">
        <option value="">All Status</option>
        <option v-for="s in STATUSES" :key="s" :value="s">{{ s.replace('_',' ') }}</option>
      </select>
      <select v-model="priorityFilter" class="select w-36">
        <option value="">All Priority</option>
        <option v-for="p in PRIORITIES" :key="p" :value="p">{{ p }}</option>
      </select>
      <select v-model="categoryFilter" class="select w-40">
        <option value="">All Categories</option>
        <option v-for="c in CATEGORIES" :key="c" :value="c">{{ c.replace('_',' ') }}</option>
      </select>
      <button v-if="statusFilter||priorityFilter||categoryFilter||search" @click="resetFilters" class="btn-ghost btn-sm"><RotateCcw class="h-4 w-4" />Clear</button>
    </div>

    <!-- Table -->
    <div class="table-wrap">
      <div v-if="loading" class="p-8 text-center text-slate-400">Loading…</div>
      <table v-else class="table">
        <thead><tr><th>ID</th><th>Title</th><th>Category</th><th>Priority</th><th>Status</th><th>Ward</th><th>Filed</th><th></th></tr></thead>
        <tbody>
          <tr v-for="c in complaints" :key="c.id">
            <td class="font-mono text-xs whitespace-nowrap">{{ c.complaint_number }}</td>
            <td class="max-w-xs">
              <div class="font-medium text-sm truncate">{{ c.title }}</div>
              <div v-if="c.sla_breached" class="mt-1 inline-flex items-center gap-1 text-xs font-medium text-red-500"><AlertTriangle class="h-3.5 w-3.5" />SLA Breached</div>
            </td>
            <td><span class="text-xs capitalize">{{ c.category?.replace('_',' ') }}</span></td>
            <td><span :class="[PRI_BADGE[c.priority],'badge']">{{ c.priority }}</span></td>
            <td><span :class="[BADGE[c.status]||'badge-pending','badge']">{{ c.status?.replace('_',' ') }}</span></td>
            <td class="text-xs text-slate-400">{{ c.ward_number ?? '—' }}</td>
            <td class="text-xs text-slate-400 whitespace-nowrap">{{ new Date(c.created_at).toLocaleDateString('en-IN') }}</td>
            <td><RouterLink :to="`/complaints/${c.id}`" class="btn-secondary btn-sm">View</RouterLink></td>
          </tr>
          <tr v-if="complaints.length===0"><td colspan="8" class="text-center text-slate-400 py-8">No complaints found</td></tr>
        </tbody>
      </table>
      <!-- Pagination -->
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
