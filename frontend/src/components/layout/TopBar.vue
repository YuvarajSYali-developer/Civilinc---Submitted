<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import {
  Bell,
  ChevronDown,
  LogOut,
  Plus,
  Settings,
  UserRound,
} from 'lucide-vue-next'

const auth = useAuthStore()
const notifs = useNotificationsStore()
const router = useRouter()
const showUserMenu = ref(false)

async function logout() {
  await auth.logout()
  router.push('/login')
}
</script>
<template>
  <header class="mx-4 mt-3 flex h-16 shrink-0 items-center justify-between rounded-2xl border border-white/60 bg-white/78 px-5 shadow-[0_12px_40px_rgba(15,23,42,0.08)] backdrop-blur-xl dark:border-white/10 dark:bg-surface-900/72 sm:mx-6 lg:mx-8">
    <div>
      <div class="muted-kicker">Urban command platform</div>
      <div class="text-sm font-semibold text-slate-700 dark:text-slate-200">
        Bengaluru Municipal Corporation
      </div>
    </div>
    <div class="flex items-center gap-2">
      <!-- Notifications -->
      <RouterLink to="/notifications" class="btn-secondary btn-sm px-2.5 relative" aria-label="Notifications">
        <Bell class="h-4 w-4" />
        <span v-if="notifs.unreadCount > 0"
          class="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center leading-none">
          {{ Math.min(notifs.unreadCount, 9) }}
        </span>
      </RouterLink>
      <!-- New complaint (citizens) -->
      <RouterLink v-if="auth.isCitizen" to="/complaints/new" class="btn-primary btn-sm">
        <Plus class="h-4 w-4" />
        Report Issue
      </RouterLink>
      <!-- User menu -->
      <div class="relative">
        <button @click="showUserMenu = !showUserMenu"
          class="flex items-center gap-3 rounded-xl border border-transparent px-3 py-2 transition-colors hover:bg-surface-100 dark:hover:bg-surface-800">
          <div class="flex h-9 w-9 items-center justify-center rounded-full bg-primary-100 text-primary-700 dark:bg-primary-900/40 dark:text-primary-300 text-xs font-bold">
            {{ auth.user?.full_name?.charAt(0) ?? '?' }}
          </div>
          <div class="hidden text-left sm:block">
            <div class="text-sm font-semibold text-slate-700 dark:text-slate-200">{{ auth.user?.full_name?.split(' ')[0] }}</div>
            <div class="text-xs text-slate-400 capitalize">{{ auth.role }}</div>
          </div>
          <ChevronDown class="h-4 w-4 text-slate-400" />
        </button>
        <div v-if="showUserMenu" @click.away="showUserMenu = false"
          class="absolute right-0 top-full mt-1 w-48 card py-1 z-50">
          <RouterLink to="/profile" @click="showUserMenu=false" class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-surface-50 dark:hover:bg-surface-800">
            <UserRound class="h-4 w-4" />
            Profile
          </RouterLink>
          <RouterLink to="/settings" @click="showUserMenu=false" class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-surface-50 dark:hover:bg-surface-800">
            <Settings class="h-4 w-4" />
            Settings
          </RouterLink>
          <hr class="my-1">
          <button @click="logout()" class="w-full flex items-center gap-2 px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20">
            <LogOut class="h-4 w-4" />
            Sign Out
          </button>
        </div>
      </div>
    </div>
  </header>
</template>
