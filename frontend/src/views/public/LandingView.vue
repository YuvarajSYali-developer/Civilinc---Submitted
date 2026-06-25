<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from 'vue'
import landingSource from '@/content/landing-page.html?raw'

const styleId = 'civilinc-landing-styles'

const landingStyle = computed(() => landingSource.match(/<style>([\s\S]*?)<\/style>/)?.[1] ?? '')
const landingMarkup = computed(() => landingSource.match(/<body>([\s\S]*?)<\/body>/)?.[1] ?? landingSource)

onMounted(() => {
  let styleEl = document.getElementById(styleId) as HTMLStyleElement | null
  if (!styleEl) {
    styleEl = document.createElement('style')
    styleEl.id = styleId
    document.head.appendChild(styleEl)
  }
  styleEl.textContent = landingStyle.value
})

onBeforeUnmount(() => {
  const styleEl = document.getElementById(styleId)
  styleEl?.remove()
})
</script>

<template>
  <div class="landing-view" v-html="landingMarkup" />
</template>

<style scoped>
.landing-view {
  min-height: 100vh;
  overflow-x: hidden;
  background: #070d12;
  color: #d4e8f0;
}
</style>
