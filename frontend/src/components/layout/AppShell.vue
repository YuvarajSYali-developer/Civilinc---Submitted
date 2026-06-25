<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import Sidebar from './Sidebar.vue'
import TopBar from './TopBar.vue'
import AIAssistant from '@/components/common/AIAssistant.vue'

const auth = useAuthStore()
const notifs = useNotificationsStore()
onMounted(() => notifs.fetchUnreadCount())
</script>
<template>
  <div class="flex h-screen overflow-hidden">
    <Sidebar />
    <div class="flex flex-col flex-1 overflow-hidden">
      <TopBar />
      <main class="flex-1 overflow-y-auto px-4 py-5 sm:px-6 lg:px-8 scrollbar-thin">
        <RouterView />
      </main>
    </div>
  </div>
  <!-- Commissioner AI Assistant floating widget -->
  <AIAssistant v-if="auth.isCommissioner" />
</template>
