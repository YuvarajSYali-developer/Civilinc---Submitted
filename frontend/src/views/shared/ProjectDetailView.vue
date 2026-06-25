<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { projectsApi, aiApi } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import type { Project } from '@/types'
import { ArrowLeft, Bot, Save, Sparkles } from 'lucide-vue-next'

const route = useRoute(); const auth = useAuthStore(); const ui = useUIStore()
const project = ref<Project|null>(null); const loading = ref(true); const updating = ref(false)
const aiRisk = ref<any>(null)
const updateForm = ref({ completion_percentage: 0, actual_cost: 0, status: '', actual_start_date: '', actual_end_date: '' })

const RISK_COLOR: Record<string,string> = { critical:'text-red-500 bg-red-50 dark:bg-red-900/20', high:'text-orange-500 bg-orange-50 dark:bg-orange-900/20', medium:'text-yellow-500 bg-yellow-50 dark:bg-yellow-900/20', low:'text-green-500 bg-green-50 dark:bg-green-900/20' }

onMounted(async () => {
  try {
    const { data } = await projectsApi.get(route.params.id as string)
    project.value = data
    updateForm.value.completion_percentage = data.completion_percentage
    updateForm.value.actual_cost = data.actual_cost
    updateForm.value.status = data.status
    // Fetch AI risk
    if (data.completion_percentage > 0 && data.approved_budget) {
      const planned_dur = data.planned_start_date && data.planned_end_date
        ? Math.round((new Date(data.planned_end_date).getTime()-new Date(data.planned_start_date).getTime())/86400000) : 365
      const elapsed_pct = data.actual_start_date
        ? Math.min(100, Math.round((Date.now()-new Date(data.actual_start_date).getTime())/86400000/planned_dur*100)) : 0
      const r = await aiApi.projectRisk({
        category: data.category, department: data.department_id,
        completion_pct: data.completion_percentage,
        budget_utilization_pct: data.budget_utilized_pct,
        elapsed_pct, planned_duration_days: planned_dur,
        approved_budget_lakhs: (data.approved_budget||0)/100000,
        actual_cost_lakhs: data.actual_cost/100000,
      })
      aiRisk.value = r.data
    }
  } finally { loading.value = false }
})

async function save() {
  if (!project.value) return
  updating.value = true
  try {
    const { data } = await projectsApi.update(project.value.id, updateForm.value)
    project.value = data; ui.toast('Project updated', 'success')
  } catch(e:any) { ui.toast(e?.response?.data?.detail||'Error','error') }
  finally { updating.value = false }
}
</script>
<template>
  <div class="max-w-4xl mx-auto space-y-5">
    <div class="flex items-center gap-3">
      <RouterLink to="/projects" class="btn-ghost btn-sm"><ArrowLeft class="h-4 w-4" />Projects</RouterLink>
      <div v-if="project" class="font-mono text-sm text-slate-500">{{ project.project_number }}</div>
    </div>
    <div v-if="loading" class="text-center py-12 text-slate-400">Loading…</div>
    <div v-else-if="project" class="grid grid-cols-1 lg:grid-cols-3 gap-5">
      <div class="lg:col-span-2 space-y-5">
        <div class="card card-body">
          <h2 class="text-xl font-bold text-slate-900 dark:text-white mb-2">{{ project.title }}</h2>
          <p v-if="project.description" class="text-sm text-slate-500 dark:text-slate-400 mb-4">{{ project.description }}</p>
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div><span class="text-slate-400">Category:</span> <span class="capitalize font-medium">{{ project.category?.replace('_',' ') }}</span></div>
            <div><span class="text-slate-400">Status:</span> <span class="capitalize font-medium">{{ project.status?.replace('_',' ') }}</span></div>
            <div><span class="text-slate-400">Ward:</span> <span class="font-medium">{{ project.ward_number ?? '—' }}</span></div>
            <div><span class="text-slate-400">Zone:</span> <span class="font-medium">{{ project.zone ?? '—' }}</span></div>
            <div><span class="text-slate-400">Planned Start:</span> <span class="font-medium">{{ project.planned_start_date ?? '—' }}</span></div>
            <div><span class="text-slate-400">Planned End:</span> <span class="font-medium">{{ project.planned_end_date ?? '—' }}</span></div>
            <div><span class="text-slate-400">Contractor:</span> <span class="font-medium">{{ project.contractor_name ?? '—' }}</span></div>
            <div><span class="text-slate-400">Source Fund:</span> <span class="font-medium">—</span></div>
          </div>
          <!-- Progress bar -->
          <div class="mt-5">
            <div class="flex justify-between text-sm mb-1">
              <span class="text-slate-500">Completion</span>
              <span class="font-bold">{{ project.completion_percentage }}%</span>
            </div>
            <div class="h-3 bg-surface-100 dark:bg-surface-800 rounded-full overflow-hidden">
              <div class="h-full bg-blue-500 rounded-full transition-all" :style="`width:${project.completion_percentage}%`"></div>
            </div>
          </div>
          <!-- Budget -->
          <div class="mt-4 grid grid-cols-3 gap-3">
            <div class="p-3 bg-surface-50 dark:bg-surface-800 rounded-lg text-center">
              <div class="text-xs text-slate-400">Estimated</div>
              <div class="text-sm font-bold text-slate-800 dark:text-slate-200">₹{{ (project.estimated_cost/10000000).toFixed(2) }}Cr</div>
            </div>
            <div class="p-3 bg-surface-50 dark:bg-surface-800 rounded-lg text-center">
              <div class="text-xs text-slate-400">Approved</div>
              <div class="text-sm font-bold text-slate-800 dark:text-slate-200">{{ project.approved_budget ? `₹${(project.approved_budget/10000000).toFixed(2)}Cr` : '—' }}</div>
            </div>
            <div class="p-3 bg-surface-50 dark:bg-surface-800 rounded-lg text-center">
              <div class="text-xs text-slate-400">Spent</div>
              <div class="text-sm font-bold text-slate-800 dark:text-slate-200">₹{{ (project.actual_cost/10000000).toFixed(2) }}Cr</div>
            </div>
          </div>
        </div>

        <!-- AI Risk -->
        <div v-if="aiRisk" class="card card-body" :class="aiRisk.risk_category ? RISK_COLOR[aiRisk.risk_category] : ''">
          <div class="mb-3 flex items-center gap-2">
            <Sparkles class="h-4 w-4" />
            <h3 class="font-semibold text-sm">AI Risk Assessment</h3>
          </div>
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div><span class="opacity-70">Delay Probability:</span><br><span class="font-bold text-lg">{{ Math.round((aiRisk.delay_probability||0)*100) }}%</span></div>
            <div><span class="opacity-70">Risk Category:</span><br><span class="font-bold capitalize text-lg">{{ aiRisk.risk_category }}</span></div>
            <div><span class="opacity-70">Expected Overrun:</span><br><span class="font-bold">₹{{ (aiRisk.expected_overrun_lakhs||0).toFixed(1) }}L</span></div>
            <div><span class="opacity-70">Risk Score:</span><br><span class="font-bold">{{ ((aiRisk.risk_score||0)*100).toFixed(0) }}/100</span></div>
          </div>
        </div>
      </div>

      <!-- Sidebar: Update -->
      <div class="space-y-5">
        <div v-if="auth.isStaff" class="card card-body">
          <h3 class="font-semibold text-slate-900 dark:text-white mb-4">Update Progress</h3>
          <div class="space-y-3">
            <div>
              <label class="label">Status</label>
              <select v-model="updateForm.status" class="select">
                <option v-for="s in ['planning','tendering','in_progress','on_hold','completed','cancelled']" :key="s" :value="s">{{ s.replace('_',' ') }}</option>
              </select>
            </div>
            <div>
              <label class="label">Completion % ({{ updateForm.completion_percentage }})</label>
              <input v-model.number="updateForm.completion_percentage" type="range" min="0" max="100" class="w-full" />
            </div>
            <div>
              <label class="label">Actual Cost (₹)</label>
              <input v-model.number="updateForm.actual_cost" type="number" class="input" />
            </div>
            <button @click="save" :disabled="updating" class="btn-primary w-full justify-center">
              <span v-if="updating">Saving…</span>
              <span v-else class="inline-flex items-center gap-2"><Save class="h-4 w-4" />Save Update</span>
            </button>
          </div>
        </div>
        <div class="card card-body text-sm space-y-2">
          <div class="flex justify-between"><span class="text-slate-400">Budget Used</span><span class="font-medium">{{ project.budget_utilized_pct }}%</span></div>
          <div class="flex justify-between"><span class="text-slate-400">Delay Prob.</span><span class="font-medium">{{ project.delay_probability ? Math.round(project.delay_probability*100)+'%' : '—' }}</span></div>
          <div class="flex justify-between"><span class="text-slate-400">Risk Score</span><span class="font-medium">{{ project.risk_score ? (project.risk_score*100).toFixed(0) : '—' }}</span></div>
        </div>
      </div>
    </div>
  </div>
</template>
