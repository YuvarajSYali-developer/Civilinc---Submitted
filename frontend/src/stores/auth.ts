import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/services/api'
import type { User, Role } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const role = computed<Role | null>(() => user.value?.role ?? null)
  const isCommissioner = computed(() => role.value === 'commissioner')
  const isEngineer = computed(() => role.value === 'engineer')
  const isCoordinator = computed(() => role.value === 'coordinator')
  const isCitizen = computed(() => role.value === 'citizen')
  const isStaff = computed(() => ['commissioner', 'engineer', 'coordinator'].includes(role.value ?? ''))

  async function login(email: string, password: string) {
    loading.value = true
    try {
      const { data } = await authApi.login(email, password)
      token.value = data.access_token
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      await fetchMe()
      return data
    } finally { loading.value = false }
  }

  async function fetchMe() {
    const { data } = await authApi.me()
    user.value = data
  }

  async function logout() {
    try { await authApi.logout() } catch {}
    token.value = null; user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  async function init() {
    if (token.value) {
      try { await fetchMe() } catch { await logout() }
    }
  }

  return { user, token, loading, isAuthenticated, role,
    isCommissioner, isEngineer, isCoordinator, isCitizen, isStaff,
    login, logout, fetchMe, init }
})
