<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { complaintsApi } from '@/services/api'
import { ArrowRight, ClipboardList, FilePenLine, MapPinned, Wrench } from 'lucide-vue-next'
const auth = useAuthStore(); const myComplaints = ref<any[]>([])
const BADGE: Record<string,string> = { pending:'badge-pending', resolved:'badge-resolved', in_progress:'badge-in-progress', assigned:'badge-in-progress', escalated:'badge-critical', closed:'badge-resolved', under_review:'badge-pending' }
const quickActions = [
  { to: '/complaints/new', label: 'Report Issue', meta: 'Create a new complaint with location and details.', icon: FilePenLine },
  { to: '/complaints', label: 'My Complaints', meta: 'Track status updates and response timelines.', icon: ClipboardList },
  { to: '/map', label: 'View Map', meta: 'See nearby issues and civic activity spatially.', icon: MapPinned },
  { to: '/projects', label: 'Projects', meta: 'Follow ward-level infrastructure work.', icon: Wrench },
]
onMounted(async () => { const { data } = await complaintsApi.list({ page_size:5 }); myComplaints.value = data.items })
</script>
<template>
  <div class="space-y-6">
    <div class="page-header flex items-center justify-between">
      <div>
        <div class="muted-kicker">Citizen workspace</div>
        <h1 class="page-title">My Dashboard</h1>
        <p class="page-subtitle">Welcome, {{ auth.user?.full_name }}. Stay on top of ward updates, responses, and project activity in {{ auth.user?.ward_number }}.</p>
      </div>
      <RouterLink to="/complaints/new" class="btn-primary">
        <FilePenLine class="h-4 w-4" />
        Report Issue
      </RouterLink>
    </div>
    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <RouterLink v-for="action in quickActions" :key="action.to" :to="action.to" class="card p-5 transition-all hover:-translate-y-1 hover:border-primary-200 cursor-pointer">
        <div class="flex items-start justify-between gap-4">
          <span class="icon-chip">
            <component :is="action.icon" class="h-5 w-5" />
          </span>
          <ArrowRight class="h-4 w-4 text-slate-300" />
        </div>
        <div class="mt-5 text-base font-semibold text-slate-800 dark:text-slate-100">{{ action.label }}</div>
        <div class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ action.meta }}</div>
      </RouterLink>
    </div>
    <div class="table-wrap">
      <div class="card-header flex items-center justify-between"><h3 class="panel-title">My Recent Complaints</h3><RouterLink to="/complaints" class="inline-flex items-center gap-2 text-sm font-semibold text-primary-600 dark:text-primary-400 hover:underline">View all <ArrowRight class="h-4 w-4" /></RouterLink></div>
      <div v-if="myComplaints.length===0" class="p-8 text-center"><p class="text-slate-400 text-sm">No complaints filed yet.</p><RouterLink to="/complaints/new" class="btn-primary btn-sm mt-3 inline-flex">Report your first issue</RouterLink></div>
      <table v-else class="table"><thead><tr><th>ID</th><th>Title</th><th>Category</th><th>Status</th><th>Filed On</th></tr></thead>
        <tbody>
          <tr v-for="c in myComplaints" :key="c.id">
            <td><RouterLink :to="`/complaints/${c.id}`" class="text-primary-600 dark:text-primary-400 font-mono text-xs hover:underline">{{ c.complaint_number }}</RouterLink></td>
            <td class="max-w-xs"><div class="truncate text-sm">{{ c.title }}</div></td>
            <td><span class="text-xs capitalize">{{ c.category?.replace('_',' ') }}</span></td>
            <td><span :class="[BADGE[c.status]||'badge-pending','badge']">{{ c.status?.replace('_',' ') }}</span></td>
            <td class="text-xs text-slate-400">{{ new Date(c.created_at).toLocaleDateString('en-IN') }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
