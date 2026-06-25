<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import CommissionerDashboard from '@/views/commissioner/CommissionerDashboard.vue'
import EngineerDashboard from '@/views/engineer/EngineerDashboard.vue'
import CoordinatorDashboard from '@/views/coordinator/CoordinatorDashboard.vue'
import CitizenDashboard from '@/views/citizen/CitizenDashboard.vue'
const auth = useAuthStore()
const dashComponent = computed(() => {
  if (auth.isCommissioner) return CommissionerDashboard
  if (auth.isEngineer) return EngineerDashboard
  if (auth.isCoordinator) return CoordinatorDashboard
  return CitizenDashboard
})
</script>
<template><component :is="dashComponent" /></template>
