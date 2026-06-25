<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api, aiApi } from '@/services/api'
const health = ref<any>(null); const aiHealth = ref<any>(null)
onMounted(async () => {
  try { const r = await api.get('http://localhost:8000/health'); health.value = r.data } catch(e) { health.value = { status:'error' } }
  try { aiHealth.value = (await aiApi.health()).data } catch {}
})
</script>
<template>
  <div class="max-w-xl mx-auto space-y-4">
    <div class="page-header"><h1 class="page-title">System Health</h1></div>
    <div v-if="health" class="card card-body">
      <div class="flex items-center gap-2 mb-2"><div :class="['w-3 h-3 rounded-full', health.status==='healthy'?'bg-green-500':'bg-red-500']"></div><span class="font-semibold">Backend API</span></div>
      <div class="text-sm text-slate-500">{{ health.app }} v{{ health.version }} · {{ health.environment }}</div>
    </div>
    <div v-if="aiHealth" class="card card-body">
      <div class="flex items-center gap-2 mb-2"><div :class="['w-3 h-3 rounded-full', aiHealth.models_loaded?'bg-green-500':'bg-yellow-500']"></div><span class="font-semibold">AI Services</span></div>
      <div class="text-sm text-slate-500">{{ aiHealth.model_count }} models loaded</div>
      <div class="flex flex-wrap gap-2 mt-2">
        <span v-for="s in aiHealth.systems" :key="s" class="text-xs px-2 py-0.5 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded">{{ s }}</span>
      </div>
    </div>
  </div>
</template>
