<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { complaintsApi, aiApi } from '@/services/api'
import { useUIStore } from '@/stores/ui'
import type { AITriageResult } from '@/types'
import { ArrowLeft, Bot, MapPin, Sparkles } from 'lucide-vue-next'

const router = useRouter()
const ui = useUIStore()
const submitting = ref(false)
const aiResult = ref<AITriageResult | null>(null)
const aiLoading = ref(false)

const CATEGORIES = ['roads','water_supply','drainage','electricity','parks','buildings','sanitation']
const form = reactive({
  title:'', description:'', category:'', sub_category:'',
  address:'', ward_number:'', latitude: undefined as number|undefined,
  longitude: undefined as number|undefined, source:'web'
})

let aiTimer: any
watch([() => form.title, () => form.description], () => {
  if (form.title.length > 15 && form.description.length > 25) {
    clearTimeout(aiTimer)
    aiTimer = setTimeout(runAI, 1000)
  }
})

async function runAI() {
  aiLoading.value = true
  try {
    const { data } = await aiApi.triage({ title: form.title, description: form.description, source: form.source })
    aiResult.value = data
    if (!form.category) form.category = data.category
  } catch {} finally { aiLoading.value = false }
}

function applyAI() {
  if (!aiResult.value) return
  form.category = aiResult.value.category
}

async function submit() {
  if (!form.title || !form.description || !form.category) {
    ui.toast('Please fill in all required fields', 'warning'); return
  }
  submitting.value = true
  try {
    const { data } = await complaintsApi.create(form)
    ui.toast(`Complaint ${data.complaint_number} filed successfully!`, 'success')
    router.push(`/complaints/${data.id}`)
  } catch (e:any) {
    ui.toast(e?.response?.data?.detail || 'Failed to submit complaint', 'error')
  } finally { submitting.value = false }
}
</script>
<template>
  <div class="max-w-2xl mx-auto space-y-5">
    <div class="page-header flex items-center gap-3">
      <RouterLink to="/complaints" class="btn-ghost btn-sm"><ArrowLeft class="h-4 w-4" />Back</RouterLink>
      <div><div class="muted-kicker">Citizen reporting</div><h1 class="page-title">Report an Issue</h1><p class="page-subtitle">Submit a civic complaint to BBMP with enough detail for faster triage and routing.</p></div>
    </div>

    <!-- AI Triage Panel -->
    <div v-if="aiResult || aiLoading" class="card card-body bg-blue-50 dark:bg-blue-900/10 border-blue-200 dark:border-blue-800">
      <div class="flex items-start gap-3">
        <span class="icon-chip bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
          <Sparkles class="h-4 w-4" />
        </span>
        <div class="flex-1">
          <div class="font-semibold text-blue-800 dark:text-blue-300 text-sm mb-1">AI Triage Assistant</div>
          <div v-if="aiLoading" class="text-blue-600 dark:text-blue-400 text-sm">Analysing your complaint…</div>
          <div v-else-if="aiResult" class="space-y-2">
            <div class="flex flex-wrap gap-3 text-sm">
              <span class="font-medium text-slate-700 dark:text-slate-200">Category: <span class="text-blue-700 dark:text-blue-300 capitalize">{{ aiResult.category?.replace('_',' ') }}</span></span>
              <span class="font-medium text-slate-700 dark:text-slate-200">Priority: <span class="capitalize" :class="aiResult.priority==='critical'?'text-red-600':aiResult.priority==='high'?'text-orange-500':'text-yellow-600'">{{ aiResult.priority }}</span></span>
              <span class="font-medium text-slate-700 dark:text-slate-200">Est. Resolution: <span class="text-blue-700 dark:text-blue-300">{{ aiResult.resolution_days }} days</span></span>
              <span class="font-medium text-slate-700 dark:text-slate-200">Confidence: <span class="text-blue-700 dark:text-blue-300">{{ Math.round((aiResult.confidence||0)*100) }}%</span></span>
            </div>
            <button @click="applyAI" class="btn-secondary btn-sm">Apply AI Suggestion</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Form -->
    <div class="card card-body space-y-4">
      <div>
        <label class="label">Title <span class="text-red-500">*</span></label>
        <input v-model="form.title" class="input" placeholder="Briefly describe the issue (min 10 chars)" maxlength="200" />
        <div class="text-xs text-slate-400 mt-1">{{ form.title.length }}/200</div>
      </div>
      <div>
        <label class="label">Description <span class="text-red-500">*</span></label>
        <textarea v-model="form.description" class="input min-h-28 resize-y" placeholder="Provide detailed description including location, duration, impact…" maxlength="2000" />
        <div class="text-xs text-slate-400 mt-1">{{ form.description.length }}/2000</div>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="label">Category <span class="text-red-500">*</span></label>
          <select v-model="form.category" class="select">
            <option value="">Select category…</option>
            <option v-for="c in CATEGORIES" :key="c" :value="c">{{ c.replace('_',' ').replace(/\w/g,l=>l.toUpperCase()) }}</option>
          </select>
        </div>
        <div>
          <label class="label">Ward Number</label>
          <input v-model="form.ward_number" class="input" placeholder="e.g. Ward-42" />
        </div>
      </div>
      <div>
        <label class="label">Address / Location</label>
        <div class="relative">
          <MapPin class="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input v-model="form.address" class="input pl-11" placeholder="Full address or landmark" />
        </div>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="label">Latitude (optional)</label>
          <input v-model.number="form.latitude" type="number" step="0.000001" class="input" placeholder="12.9716" />
        </div>
        <div>
          <label class="label">Longitude (optional)</label>
          <input v-model.number="form.longitude" type="number" step="0.000001" class="input" placeholder="77.5946" />
        </div>
      </div>
      <div class="flex justify-end gap-3 pt-2 border-t">
        <RouterLink to="/complaints" class="btn-secondary">Cancel</RouterLink>
        <button @click="submit" :disabled="submitting" class="btn-primary">
          <span v-if="submitting">Submitting…</span>
          <span v-else class="inline-flex items-center gap-2"><Bot class="h-4 w-4" />Submit Complaint</span>
        </button>
      </div>
    </div>
  </div>
</template>
