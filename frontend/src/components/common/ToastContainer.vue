<script setup lang="ts">
import { useUIStore } from '@/stores/ui'
import { AlertTriangle, CheckCircle2, Info, XCircle } from 'lucide-vue-next'
const ui = useUIStore()
const icons = { success: CheckCircle2, error: XCircle, warning: AlertTriangle, info: Info }
const colors: Record<string,string> = {
  success:'bg-emerald-600', error:'bg-rose-600', warning:'bg-amber-500', info:'bg-blue-600'
}
</script>
<template>
  <div class="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-80">
    <TransitionGroup name="slide-up">
      <div v-for="n in ui.notifications" :key="n.id"
           :class="[colors[n.type], 'flex items-center gap-3 px-4 py-3 rounded-2xl text-white text-sm shadow-xl']">
        <span class="shrink-0 flex h-8 w-8 items-center justify-center rounded-xl bg-white/16">
          <component :is="icons[n.type]" class="h-4 w-4" />
        </span>
        <span class="font-medium">{{ n.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>
