<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/services/api'
import { Bot, SendHorizontal, Sparkles, Trash2, X } from 'lucide-vue-next'

const open = ref(false)
const query = ref('')
const messages = ref<{role:'user'|'assistant', text:string}[]>([])
const loading = ref(false)

const SUGGESTIONS = [
  'Which department has the highest backlog?',
  'Which projects have >70% delay risk?',
  'Show wards with highest complaint growth',
  'Summarize city infrastructure performance',
  'Generate weekly commissioner report',
]

async function ask(q?: string) {
  const question = q || query.value.trim()
  if (!question) return
  messages.value.push({ role: 'user', text: question })
  query.value = ''; loading.value = true
  try {
    const { data } = await api.post('/assistant/query', { query: question })
    messages.value.push({ role: 'assistant', text: data.answer })
  } catch {
    messages.value.push({ role: 'assistant', text: 'Unable to process query at this time.' })
  } finally { loading.value = false }
}
</script>
<template>
  <!-- Floating button -->
  <div class="fixed bottom-6 right-6 z-40">
    <button @click="open=!open"
      class="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-900 text-white shadow-[0_22px_44px_rgba(15,23,42,0.26)] transition-all hover:-translate-y-0.5 hover:bg-primary-700 dark:bg-white dark:text-slate-900"
      :title="open?'Close Assistant':'Commissioner AI Assistant'">
      <component :is="open ? X : Bot" class="h-5 w-5" />
    </button>
  </div>

  <!-- Panel -->
  <Transition name="slide-up">
    <div v-if="open" class="fixed bottom-24 right-6 z-40 flex w-96 max-w-[calc(100vw-2rem)] flex-col card shadow-2xl" style="max-height:560px">
      <div class="card-header flex items-center justify-between shrink-0">
        <div class="flex items-start gap-3">
          <span class="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300">
            <Sparkles class="h-4 w-4" />
          </span>
          <div>
            <div class="font-semibold text-slate-900 dark:text-white text-sm">Commissioner AI Assistant</div>
            <div class="text-xs text-slate-400">Query live BBMP operational data</div>
          </div>
        </div>
        <button @click="messages=[]" class="btn-ghost btn-sm text-xs">
          <Trash2 class="h-3.5 w-3.5" />
          Clear
        </button>
      </div>

      <!-- Messages -->
      <div class="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-thin" ref="msgContainer">
        <div v-if="messages.length===0" class="space-y-2">
          <p class="text-xs text-slate-400 mb-3">Try asking:</p>
          <button v-for="s in SUGGESTIONS" :key="s" @click="ask(s)"
            class="w-full rounded-xl border border-surface-200 bg-surface-50 p-3 text-left text-xs font-medium text-slate-600 transition-colors hover:bg-primary-50 hover:text-primary-700 dark:border-surface-700 dark:bg-surface-800 dark:text-slate-300 dark:hover:bg-primary-900/20 dark:hover:text-primary-300">
            {{ s }}
          </button>
        </div>
        <div v-for="(m,i) in messages" :key="i"
          :class="['rounded-2xl px-3 py-2.5 text-sm max-w-[85%]', m.role==='user' ? 'ml-auto bg-slate-900 text-white dark:bg-primary-600' : 'bg-surface-100 dark:bg-surface-800 text-slate-700 dark:text-slate-200 whitespace-pre-wrap']">
          {{ m.text }}
        </div>
        <div v-if="loading" class="flex gap-1 p-2">
          <span v-for="i in 3" :key="i" :style="`animation-delay:${i*150}ms`"
            class="w-2 h-2 bg-primary-400 rounded-full animate-bounce"></span>
        </div>
      </div>

      <!-- Input -->
      <div class="p-3 border-t shrink-0 flex gap-2">
        <input v-model="query" @keyup.enter="ask()" class="input flex-1 text-sm"
          placeholder="Ask anything about BBMP operations…" :disabled="loading" />
        <button @click="ask()" :disabled="loading||!query.trim()" class="btn-primary btn-sm shrink-0 px-3">
          <SendHorizontal class="h-4 w-4" />
        </button>
      </div>
    </div>
  </Transition>
</template>
