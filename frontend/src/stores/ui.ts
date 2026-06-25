import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useUIStore = defineStore('ui', () => {
  const darkMode = ref(true)
  const sidebarCollapsed = ref(false)
  const notifications = ref<{ id: string; type: 'success'|'error'|'warning'|'info'; message: string }[]>([])

  watch(darkMode, v => {
    localStorage.setItem('darkMode', 'true')
    document.documentElement.classList.add('dark')
  }, { immediate: true })

  function toast(message: string, type: 'success'|'error'|'warning'|'info' = 'info') {
    const id = Date.now().toString()
    notifications.value.push({ id, type, message })
    setTimeout(() => { notifications.value = notifications.value.filter(n => n.id !== id) }, 4000)
  }

  function toggleDark() { darkMode.value = true }
  function toggleSidebar() { sidebarCollapsed.value = !sidebarCollapsed.value }

  return { darkMode, sidebarCollapsed, notifications, toast, toggleDark, toggleSidebar }
})
