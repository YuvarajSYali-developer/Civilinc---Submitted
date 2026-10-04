<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { complaintsApi } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import type { Complaint, ComplaintHistory } from '@/types'
import { AlertTriangle, ArrowLeft, Bot, MapPin, Save, Sparkles } from 'lucide-vue-next'

const route = useRoute()
const auth = useAuthStore()
const ui = useUIStore()
const complaint = ref<Complaint|null>(null)
const history = ref<ComplaintHistory[]>([])
const loading = ref(true)
const updating = ref(false)
const updateForm = ref({ status:'', priority:'', comment:'' })
const feedbackForm = ref({ rating: 5, feedback:'' })
const showFeedback = ref(false)

const STATUSES = ['pending','under_review','assigned','in_progress','resolved','closed','rejected']
const PRIORITIES = ['critical','high','medium','low']
const PRI_BADGE: Record<string,string> = { critical:'badge-critical', high:'badge-high', medium:'badge-medium', low:'badge-low' }
const STA_BADGE: Record<string,string> = { pending:'badge-pending', under_review:'badge-pending', assigned:'badge-in-progress', in_progress:'badge-in-progress', resolved:'badge-resolved', closed:'badge-resolved', escalated:'badge-critical' }

onMounted(async () => {
  try {
    const [c, h] = await Promise.all([
      complaintsApi.get(route.params.id as string),
      complaintsApi.history(route.params.id as string)
    ])
    complaint.value = c.data; history.value = h.data
    updateForm.value.status = c.data.status
    updateForm.value.priority = c.data.priority
  } finally { loading.value = false }
})

async function saveUpdate() {
  if (!complaint.value) return
  updating.value = true
  try {
    const { data } = await complaintsApi.update(complaint.value.id, updateForm.value)
    complaint.value = data
    const h = await complaintsApi.history(data.id)
    history.value = h.data
    updateForm.value.comment = ''
    ui.toast('Complaint updated', 'success')
  } catch(e:any) { ui.toast(e?.response?.data?.detail || 'Update failed', 'error') }
  finally { updating.value = false }
}

async function submitFeedback() {
  if (!complaint.value) return
  try {
    await complaintsApi.feedback(complaint.value.id, feedbackForm.value)
    ui.toast('Feedback submitted!', 'success'); showFeedback.value = false
    const { data } = await complaintsApi.get(complaint.value.id)
    complaint.value = data
  } catch(e:any) { ui.toast(e?.response?.data?.detail || 'Failed', 'error') }
}

async function escalate() {
  if (!complaint.value) return
  try {
    await complaintsApi.escalate(complaint.value.id)
    ui.toast('Complaint escalated', 'warning')
    const { data } = await complaintsApi.get(complaint.value.id); complaint.value = data
  } catch(e:any) { ui.toast(e?.response?.data?.detail || 'Failed', 'error') }
}
</script>
<template>
  <div class="max-w-4xl mx-auto space-y-5">
    <div class="flex items-center gap-3">
      <RouterLink to="/complaints" class="btn-ghost btn-sm"><ArrowLeft class="h-4 w-4" />Complaints</RouterLink>
      <div v-if="complaint" class="font-mono text-sm text-slate-500">{{ complaint.complaint_number }}</div>
    </div>

    <div v-if="loading" class="text-center py-12 text-slate-400">Loading…</div>
    <div v-else-if="complaint" class="grid grid-cols-1 lg:grid-cols-3 gap-5">
      <!-- Main -->
      <div class="lg:col-span-2 space-y-5">
        <div class="card card-body">
          <div class="flex flex-wrap items-start justify-between gap-3 mb-4">
            <h2 class="text-lg font-bold text-slate-900 dark:text-white leading-tight">{{ complaint.title }}</h2>
            <div class="flex gap-2">
              <span :class="[PRI_BADGE[complaint.priority],'badge']">{{ complaint.priority }}</span>
              <span :class="[STA_BADGE[complaint.status]||'badge-pending','badge']">{{ complaint.status?.replace('_',' ') }}</span>
            </div>
          </div>
          <p class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">{{ complaint.description }}</p>
          <div class="mt-4 grid grid-cols-2 gap-3 text-sm">
            <div><span class="text-slate-400">Category:</span> <span class="capitalize font-medium">{{ complaint.category?.replace('_',' ') }}</span></div>
            <div><span class="text-slate-400">Ward:</span> <span class="font-medium">{{ complaint.ward_number ?? '—' }}</span></div>
            <div><span class="text-slate-400">Zone:</span> <span class="font-medium">{{ complaint.zone ?? '—' }}</span></div>
            <div><span class="text-slate-400">Source:</span> <span class="font-medium capitalize">{{ complaint.source }}</span></div>
            <div><span class="text-slate-400">Filed:</span> <span class="font-medium">{{ new Date(complaint.created_at).toLocaleString('en-IN') }}</span></div>
            <div><span class="text-slate-400">SLA Breach:</span> <span :class="complaint.sla_breached?'text-red-500 font-bold':'text-green-600'">{{ complaint.sla_breached?'Yes':'No' }}</span></div>
          </div>
          <div v-if="complaint.address" class="mt-3 flex items-center gap-2 rounded-xl bg-surface-50 p-3 text-sm text-slate-600 dark:bg-surface-800 dark:text-slate-300">
            <MapPin class="h-4 w-4 text-slate-400" />
            {{ complaint.address }}
          </div>
        </div>

        <!-- AI Predictions -->
        <div v-if="complaint.ai_processed" class="card card-body bg-blue-50 dark:bg-blue-900/10 border-blue-200 dark:border-blue-800">
          <div class="mb-3 flex items-center gap-2 text-blue-800 dark:text-blue-300">
            <Sparkles class="h-4 w-4" />
            <h3 class="font-semibold text-sm">AI Triage Results</h3>
          </div>
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div><span class="text-slate-500">Predicted Category:</span><br><span class="font-medium capitalize">{{ complaint.ai_predicted_category?.replace('_',' ') ?? '—' }}</span></div>
            <div><span class="text-slate-500">Predicted Priority:</span><br><span class="font-medium capitalize">{{ complaint.ai_predicted_priority ?? '—' }}</span></div>
            <div><span class="text-slate-500">Est. Resolution:</span><br><span class="font-medium">{{ complaint.ai_predicted_resolution_days ?? '—' }} days</span></div>
            <div><span class="text-slate-500">Confidence:</span><br><span class="font-medium">{{ complaint.ai_confidence_score ? Math.round(complaint.ai_confidence_score*100)+'%' : '—' }}</span></div>
          </div>
        </div>

        <!-- History -->
        <div class="card card-body">
          <h3 class="font-semibold text-slate-900 dark:text-white mb-4">Activity History</h3>
          <div class="space-y-3">
            <div v-for="h in history" :key="h.id" class="flex gap-3">
              <div class="w-2 h-2 mt-2 rounded-full bg-primary-400 shrink-0"></div>
              <div class="flex-1 pb-3 border-b border-surface-100 dark:border-surface-800 last:border-0">
                <div class="flex items-center justify-between">
                  <span class="text-sm font-medium text-slate-700 dark:text-slate-200 capitalize">{{ h.action?.replace('_',' ') }}</span>
                  <span class="text-xs text-slate-400">{{ new Date(h.created_at).toLocaleString('en-IN') }}</span>
                </div>
                <div v-if="h.previous_status !== h.new_status" class="text-xs text-slate-400 mt-0.5">
                  Status: {{ h.previous_status }} to {{ h.new_status }}
                </div>
                <div v-if="h.comment" class="text-sm text-slate-500 dark:text-slate-400 mt-1 italic">"{{ h.comment }}"</div>
              </div>
            </div>
            <div v-if="history.length===0" class="text-sm text-slate-400">No history yet</div>
          </div>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="space-y-5">
        <!-- Update panel (staff only) -->
        <div v-if="auth.isStaff" class="card card-body">
          <h3 class="font-semibold text-slate-900 dark:text-white mb-4">Update Complaint</h3>
          <div class="space-y-3">
            <div>
              <label class="label">Status</label>
              <select v-model="updateForm.status" class="select">
                <option v-for="s in STATUSES" :key="s" :value="s">{{ s.replace('_',' ') }}</option>
              </select>
            </div>
            <div>
              <label class="label">Priority</label>
              <select v-model="updateForm.priority" class="select">
                <option v-for="p in PRIORITIES" :key="p" :value="p">{{ p }}</option>
              </select>
            </div>
            <div>
              <label class="label">Comment</label>
              <textarea v-model="updateForm.comment" class="input min-h-20 resize-none" placeholder="Add update note…"></textarea>
            </div>
            <button @click="saveUpdate" :disabled="updating" class="btn-primary w-full justify-center">
              <span v-if="updating">Saving…</span>
              <span v-else class="inline-flex items-center gap-2"><Save class="h-4 w-4" />Save Update</span>
            </button>
            <button v-if="auth.isCommissioner||auth.isEngineer" @click="escalate" class="btn-danger w-full justify-center btn-sm"><AlertTriangle class="h-4 w-4" />Escalate</button>
          </div>
        </div>

        <!-- Feedback (citizen, resolved only) -->
        <div v-if="auth.isCitizen && ['resolved','closed'].includes(complaint.status)" class="card card-body">
          <h3 class="font-semibold text-slate-900 dark:text-white mb-3">Rate Resolution</h3>
          <div v-if="complaint.citizen_rating" class="text-sm text-slate-500">
            You rated: {{ '★'.repeat(complaint.citizen_rating) }}{{ '☆'.repeat(5-complaint.citizen_rating) }}
          </div>
          <div v-else>
            <button @click="showFeedback=!showFeedback" class="btn-secondary w-full">{{ showFeedback?'Cancel':'Leave Feedback' }}</button>
            <div v-if="showFeedback" class="mt-3 space-y-3">
              <div class="flex gap-1">
                <button v-for="i in 5" :key="i" @click="feedbackForm.rating=i" class="text-2xl" :class="i<=feedbackForm.rating?'text-amber-400':'text-slate-200 dark:text-slate-700'">★</button>
              </div>
              <textarea v-model="feedbackForm.feedback" class="input min-h-16 resize-none text-sm" placeholder="Optional feedback…"></textarea>
              <button @click="submitFeedback" class="btn-primary w-full justify-center btn-sm">Submit Rating</button>
            </div>
          </div>
        </div>

        <!-- Meta -->
        <div class="card card-body text-sm space-y-2">
          <div class="flex justify-between"><span class="text-slate-400">Department</span><span class="font-medium">{{ complaint.department_id ? 'Assigned' : 'Unassigned' }}</span></div>
          <div class="flex justify-between"><span class="text-slate-400">Escalation</span><span class="font-medium">Level {{ complaint.escalation_level }}</span></div>
          <div v-if="complaint.latitude" class="flex justify-between"><span class="text-slate-400">Coordinates</span><span class="font-mono text-xs">{{ complaint.latitude?.toFixed(4) }}, {{ complaint.longitude?.toFixed(4) }}</span></div>
        </div>
      </div>
    </div>
  </div>
</template>
