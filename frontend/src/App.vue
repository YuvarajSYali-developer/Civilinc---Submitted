<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import ToastContainer from '@/components/common/ToastContainer.vue'

const auth = useAuthStore()
const ui = useUIStore()
onMounted(() => auth.init())
</script>

<template>
  <RouterView />
  <ToastContainer />
</template>
