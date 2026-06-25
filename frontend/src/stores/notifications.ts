import { defineStore } from 'pinia'
import { ref } from 'vue'
import { notificationsApi } from '@/services/api'
import type { Notification } from '@/types'

export const useNotificationsStore = defineStore('notifications', () => {
  const items = ref<Notification[]>([])
  const unreadCount = ref(0)
  const loading = ref(false)

  async function fetchNotifications() {
    loading.value = true
    try {
      const { data } = await notificationsApi.list({ page_size: 20 })
      items.value = data.items
    } finally { loading.value = false }
  }

  async function fetchUnreadCount() {
    const { data } = await notificationsApi.unreadCount()
    unreadCount.value = data.unread_count
  }

  async function markRead(id: string) {
    await notificationsApi.markRead(id)
    const n = items.value.find(n => n.id === id)
    if (n) { n.is_read = true; unreadCount.value = Math.max(0, unreadCount.value - 1) }
  }

  async function markAllRead() {
    await notificationsApi.markAllRead()
    items.value.forEach(n => n.is_read = true)
    unreadCount.value = 0
  }

  return { items, unreadCount, loading, fetchNotifications, fetchUnreadCount, markRead, markAllRead }
})
