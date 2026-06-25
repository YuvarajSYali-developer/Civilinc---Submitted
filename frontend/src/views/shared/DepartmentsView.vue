<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { departmentsApi } from '@/services/api'
const depts = ref<any[]>([]); const loading = ref(true)
onMounted(async () => { try { const { data } = await departmentsApi.list(); depts.value = data.items } finally { loading.value = false } })
</script>
<template>
  <div class="space-y-5">
    <div class="page-header"><h1 class="page-title">Departments</h1><p class="page-subtitle">BBMP municipal department configuration</p></div>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="d in depts" :key="d.id" class="card card-body">
        <div class="flex items-start justify-between mb-3">
          <div>
            <div class="font-bold text-slate-900 dark:text-white">{{ d.name }}</div>
            <div class="text-xs font-mono text-primary-600 dark:text-primary-400 mt-0.5">{{ d.code }}</div>
          </div>
          <span :class="[d.status==='active'?'badge-resolved':'badge-pending','badge']">{{ d.status }}</span>
        </div>
        <div class="grid grid-cols-2 gap-2 text-sm">
          <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded text-center">
            <div class="font-bold text-slate-900 dark:text-white">{{ d.total_complaints?.toLocaleString() ?? 0 }}</div>
            <div class="text-xs text-slate-400">Complaints</div>
          </div>
          <div class="p-2 bg-surface-50 dark:bg-surface-800 rounded text-center">
            <div class="font-bold text-slate-900 dark:text-white">{{ d.active_projects }}</div>
            <div class="text-xs text-slate-400">Projects</div>
          </div>
        </div>
        <div class="mt-3 text-xs text-slate-400">SLA: {{ d.sla_hours }}h · Budget: {{ d.annual_budget ? `₹${(d.annual_budget/10000000).toFixed(1)}Cr` : 'N/A' }}</div>
      </div>
    </div>
  </div>
</template>
