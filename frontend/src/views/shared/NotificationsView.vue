<script setup lang="ts">
import { onMounted, type Component } from 'vue'
import { useNotificationsStore } from '@/stores/notifications'
import { Bell, BellRing, Megaphone, MessageSquareReply, RefreshCw, Siren, TriangleAlert, UserRound, Wrench } from 'lucide-vue-next'
const notifs = useNotificationsStore()
onMounted(notifs.fetchNotifications)
const TYPE_ICON: Record<string, Component> = { complaint_created: BellRing, complaint_updated: RefreshCw, project_updated: Wrench, assignment: UserRound, forum_reply: MessageSquareReply, system: Bell, broadcast: Megaphone, escalation: Siren, sla_breach: TriangleAlert }
</script>
<template>
  <div class="max-w-2xl mx-auto space-y-4">
    <div class="page-header flex items-center justify-between">
      <div><div class="muted-kicker">Inbox</div><h1 class="page-title">Notifications</h1><p class="page-subtitle">{{ notifs.unreadCount }} unread updates across complaints, projects, and discussions.</p></div>
      <button v-if="notifs.unreadCount > 0" @click="notifs.markAllRead()" class="btn-secondary btn-sm">Mark all read</button>
    </div>
    <div class="space-y-2">
      <div v-for="n in notifs.items" :key="n.id" @click="notifs.markRead(n.id)"
        :class="['card card-body flex gap-3 cursor-pointer transition-colors', !n.is_read ? 'border-primary-200 dark:border-primary-800 bg-primary-50/30 dark:bg-primary-900/10' : '']">
        <div class="icon-chip shrink-0">
          <component :is="TYPE_ICON[n.notification_type] ?? Bell" class="h-4 w-4" />
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-start justify-between gap-2">
            <div class="font-medium text-sm text-slate-900 dark:text-white">{{ n.title }}</div>
            <div v-if="!n.is_read" class="w-2 h-2 bg-primary-500 rounded-full shrink-0 mt-1.5"></div>
          </div>
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-2">{{ n.message }}</p>
          <div class="text-xs text-slate-400 mt-1">{{ new Date(n.created_at).toLocaleString('en-IN') }}</div>
        </div>
      </div>
      <div v-if="notifs.items.length===0" class="text-center text-slate-400 py-10">No notifications</div>
    </div>
  </div>
</template>
