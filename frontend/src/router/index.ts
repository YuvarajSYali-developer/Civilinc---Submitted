import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('@/views/public/LandingView.vue'), meta: { public: true, allowAuthenticated: true } },

    // Auth
    { path: '/login', component: () => import('@/views/auth/LoginView.vue'), meta: { public: true } },
    { path: '/register', component: () => import('@/views/auth/RegisterView.vue'), meta: { public: true } },

    // Main app shell
    {
      path: '/',
      component: () => import('@/components/layout/AppShell.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: 'dashboard', component: () => import('@/views/shared/DashboardRouter.vue') },
        { path: 'complaints', component: () => import('@/views/shared/ComplaintsView.vue') },
        { path: 'complaints/new', component: () => import('@/views/shared/NewComplaintView.vue') },
        { path: 'complaints/:id', component: () => import('@/views/shared/ComplaintDetailView.vue') },
        { path: 'projects', component: () => import('@/views/shared/ProjectsView.vue') },
        { path: 'projects/:id', component: () => import('@/views/shared/ProjectDetailView.vue') },
        { path: 'map', component: () => import('@/views/shared/MapView.vue') },
        { path: 'forum', component: () => import('@/views/shared/ForumView.vue') },
        { path: 'forum/:id', component: () => import('@/views/shared/ForumThreadView.vue') },
        { path: 'analytics', component: () => import('@/views/shared/AnalyticsView.vue'), meta: { roles: ['commissioner', 'engineer', 'coordinator'] } },
        { path: 'officers', component: () => import('@/views/shared/OfficersView.vue'), meta: { roles: ['commissioner', 'engineer', 'coordinator'] } },
        { path: 'departments', component: () => import('@/views/shared/DepartmentsView.vue'), meta: { roles: ['commissioner'] } },
        { path: 'notifications', component: () => import('@/views/shared/NotificationsView.vue') },
        { path: 'settings', component: () => import('@/views/shared/SettingsView.vue') },
        { path: 'profile', component: () => import('@/views/shared/ProfileView.vue') },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.user && auth.token) await auth.init()
  if (to.meta.requiresAuth && !auth.isAuthenticated) return '/login'
  if (to.meta.public && auth.isAuthenticated && !to.meta.allowAuthenticated) return '/dashboard'
  if (to.meta.roles && !to.meta.roles.includes(auth.role)) return '/dashboard'
})

export default router
