<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{ title: string; value: string; icon?: Component; sub?: string; color?: string }>()
const colorMap: Record<string,string> = {
  blue: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-300',
  green: 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-300',
  red: 'bg-rose-50 dark:bg-rose-900/20 text-rose-600 dark:text-rose-300',
  amber: 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-300',
  purple: 'bg-violet-50 dark:bg-violet-900/20 text-violet-600 dark:text-violet-300',
}
</script>
<template>
  <div class="stat-card">
    <div class="flex items-start justify-between gap-4">
      <div>
        <div class="muted-kicker mb-2">{{ title }}</div>
        <div class="stat-value">{{ value }}</div>
      </div>
      <span v-if="icon" :class="['inline-flex h-11 w-11 items-center justify-center rounded-2xl text-lg', colorMap[color ?? 'blue']]">
        <component :is="icon" class="h-5 w-5" />
      </span>
    </div>
    <div v-if="sub" class="stat-label">{{ sub }}</div>
  </div>
</template>
