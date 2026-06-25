<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usersApi } from '@/services/api'
const officers = ref<any[]>([]); const search = ref(''); const loading = ref(true)
onMounted(async () => { try { const { data } = await usersApi.list({ page_size:50, role:'engineer' }); officers.value = data.items } finally { loading.value = false } })
const filtered = () => officers.value.filter(o => !search.value || o.full_name.toLowerCase().includes(search.value.toLowerCase()) || o.email.toLowerCase().includes(search.value.toLowerCase()))
</script>
<template>
  <div class="space-y-5">
    <div class="page-header flex items-center justify-between">
      <div><h1 class="page-title">Officer Directory</h1><p class="page-subtitle">Municipal engineering and coordination staff</p></div>
    </div>
    <div class="card card-body"><input v-model="search" class="input max-w-xs" placeholder="Search officers…" /></div>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="o in filtered()" :key="o.id" class="card card-body hover:shadow-md transition-shadow">
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 bg-primary-100 dark:bg-primary-900/40 rounded-full flex items-center justify-center text-primary-700 dark:text-primary-300 font-bold">{{ o.full_name?.charAt(0) }}</div>
          <div>
            <div class="font-semibold text-sm text-slate-900 dark:text-white">{{ o.full_name }}</div>
            <div class="text-xs text-slate-400 capitalize">{{ o.role }}</div>
          </div>
        </div>
        <div class="space-y-1 text-xs text-slate-500 dark:text-slate-400">
          <div>{{ o.email }}</div>
          <div v-if="o.designation">{{ o.designation }}</div>
          <div v-if="o.employee_id" class="font-mono">{{ o.employee_id }}</div>
        </div>
        <div class="mt-2"><span :class="[o.is_active?'text-green-600 bg-green-50 dark:bg-green-900/20':'text-red-500 bg-red-50 dark:bg-red-900/20','badge text-xs']">{{ o.is_active?'Active':'Inactive' }}</span></div>
      </div>
    </div>
  </div>
</template>
