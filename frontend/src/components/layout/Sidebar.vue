<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import {
  BarChart3,
  Bell,
  Building2,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  LayoutDashboard,
  Map,
  MessageSquareText,
  Settings,
  ShieldCheck,
  Users,
} from 'lucide-vue-next'

const auth = useAuthStore()
const ui = useUIStore()
const route = useRoute()

const navItems = computed(() => {
  const all = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', roles: ['commissioner','engineer','coordinator','citizen'] },
    { to: '/complaints', icon: ClipboardList, label: 'Complaints', roles: ['commissioner','engineer','coordinator','citizen'] },
    { to: '/projects', icon: Building2, label: 'Projects', roles: ['commissioner','engineer','coordinator','citizen'] },
    { to: '/map', icon: Map, label: 'GIS Map', roles: ['commissioner','engineer','coordinator','citizen'] },
    { to: '/analytics', icon: BarChart3, label: 'Analytics', roles: ['commissioner','engineer','coordinator'] },
    { to: '/forum', icon: MessageSquareText, label: 'Forum', roles: ['commissioner','engineer','coordinator','citizen'] },
    { to: '/officers', icon: Users, label: 'Officers', roles: ['commissioner','engineer','coordinator'] },
    { to: '/departments', icon: ShieldCheck, label: 'Departments', roles: ['commissioner'] },
    { to: '/notifications', icon: Bell, label: 'Notifications', roles: ['commissioner','engineer','coordinator','citizen'] },
    { to: '/settings', icon: Settings, label: 'Settings', roles: ['commissioner','engineer','coordinator','citizen'] },
  ]
  return all.filter(item => item.roles.includes(auth.role ?? ''))
})

const isActive = (to: string) => route.path === to || (to !== '/dashboard' && route.path.startsWith(to))
</script>
<template>
  <aside :class="['m-3 mr-0 flex flex-col glass-panel transition-all duration-300 shrink-0',
    ui.sidebarCollapsed ? 'w-20' : 'w-72']">
    <!-- Logo -->
    <div class="flex items-center gap-3 px-4 py-5 border-b border-surface-200/70 dark:border-surface-800/70">
      <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-slate-900 text-white shadow-[0_18px_32px_rgba(15,23,42,0.22)] dark:bg-white dark:text-slate-900">
        <span class="font-display text-sm font-bold tracking-[0.22em]">CI</span>
      </div>
      <div v-if="!ui.sidebarCollapsed" class="overflow-hidden">
        <div class="text-base font-display font-bold text-slate-900 dark:text-white leading-tight">CivilInc</div>
        <div class="text-xs text-slate-400">Bengaluru civic command center</div>
      </div>
    </div>

    <!-- Role badge -->
    <div v-if="!ui.sidebarCollapsed" class="px-4 py-4 border-b border-surface-200/70 dark:border-surface-800/70">
      <div class="muted-kicker mb-2">Logged in as</div>
      <div class="text-sm font-semibold text-slate-900 dark:text-white truncate">{{ auth.user?.full_name }}</div>
      <span class="inline-flex mt-2 rounded-full bg-primary-50 px-2.5 py-1 text-xs font-semibold text-primary-700 dark:bg-primary-900/30 dark:text-primary-300 capitalize">
        {{ auth.role }}
      </span>
    </div>

    <!-- Nav -->
    <nav class="flex-1 py-4 px-3 space-y-1 overflow-y-auto scrollbar-thin">
      <RouterLink v-for="item in navItems" :key="item.to" :to="item.to"
        :class="['sidebar-link', { active: isActive(item.to) }]">
        <span class="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-black/5 text-current dark:bg-white/5">
          <component :is="item.icon" class="h-4.5 w-4.5" />
        </span>
        <span v-if="!ui.sidebarCollapsed" class="truncate">{{ item.label }}</span>
      </RouterLink>
    </nav>

    <!-- Collapse toggle -->
    <div class="p-3 border-t border-surface-200/70 dark:border-surface-800/70">
      <button @click="ui.toggleSidebar()" class="sidebar-link w-full justify-center">
        <component :is="ui.sidebarCollapsed ? ChevronRight : ChevronLeft" class="h-4 w-4 shrink-0" />
        <span v-if="!ui.sidebarCollapsed" class="text-xs">Collapse</span>
      </button>
    </div>
  </aside>
</template>
