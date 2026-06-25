<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { complaintsApi, analyticsApi } from '@/services/api'
import StatCard from '@/components/common/StatCard.vue'
import { ArrowRight, CheckCircle2, Clock3, SearchCheck, Wrench } from 'lucide-vue-next'
const complaints = ref<any[]>([]); const stats = ref<any[]>([])
const getCount = (s: string) => stats.value.find((x:any)=>x.status===s)?.count??0
onMounted(async () => {
  const [c, s] = await Promise.all([complaintsApi.list({ page_size:8, status:'pending' }), analyticsApi.complaintsByStatus()])
  complaints.value = c.data.items; stats.value = s.data
})
</script>
<template>
  <div class="space-y-6">
    <div class="page-header"><div class="muted-kicker">Operations coordination</div><h1 class="page-title">Coordinator Dashboard</h1><p class="page-subtitle">Review the incoming queue, validate triage quality, and keep execution moving across wards and departments.</p></div>
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard title="Pending Review" :value="String(getCount('pending'))" :icon="Clock3" color="amber" />
      <StatCard title="Under Review" :value="String(getCount('under_review'))" :icon="SearchCheck" color="blue" />
      <StatCard title="In Progress" :value="String(getCount('in_progress'))" :icon="Wrench" color="purple" />
      <StatCard title="Resolved" :value="String(getCount('resolved'))" :icon="CheckCircle2" color="green" />
    </div>
    <div class="table-wrap">
      <div class="card-header flex items-center justify-between"><h3 class="panel-title">Pending Triage</h3><RouterLink to="/complaints" class="btn-secondary btn-sm">View All <ArrowRight class="h-4 w-4" /></RouterLink></div>
      <table class="table">
        <thead><tr><th>ID</th><th>Title</th><th>Category</th><th>Ward</th><th>Submitted</th><th></th></tr></thead>
        <tbody>
          <tr v-for="c in complaints" :key="c.id">
            <td class="font-mono text-xs">{{ c.complaint_number }}</td>
            <td class="max-w-xs"><div class="truncate text-sm">{{ c.title }}</div></td>
            <td><span class="capitalize text-xs">{{ c.category?.replace('_',' ') }}</span></td>
            <td class="text-xs text-slate-400">{{ c.ward_number }}</td>
            <td class="text-xs text-slate-400">{{ new Date(c.created_at).toLocaleDateString('en-IN') }}</td>
            <td><RouterLink :to="`/complaints/${c.id}`" class="btn-primary btn-sm">Review</RouterLink></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
