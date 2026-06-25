<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/services/api'
import { ArrowLeft, ArrowRight, UserPlus } from 'lucide-vue-next'

const router = useRouter()
const form = reactive({ email: '', password: '', full_name: '', phone: '', ward_number: '' })
const error = ref(''); const loading = ref(false)

async function submit() {
  error.value = ''; loading.value = true
  try {
    await authApi.register(form)
    router.push('/login')
  } catch (e: any) {
    error.value = e?.response?.data?.detail || 'Registration failed.'
  } finally { loading.value = false }
}
</script>
<template>
  <div class="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(255,255,255,0.14),_transparent_22%),linear-gradient(135deg,_#0f172a_0%,_#1d4ed8_52%,_#0f766e_100%)] flex items-center justify-center p-4">
    <div class="w-full max-w-md rounded-[28px] border border-white/60 bg-white/90 p-8 shadow-[0_30px_80px_rgba(15,23,42,0.22)] backdrop-blur-xl dark:border-white/10 dark:bg-surface-900/84">
      <div class="mb-6">
        <div class="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-primary-100 text-primary-700 dark:bg-primary-900/40 dark:text-primary-300">
          <UserPlus class="h-5 w-5" />
        </div>
        <div class="mt-4 muted-kicker">Citizen onboarding</div>
        <h1 class="mt-2 text-3xl font-display font-bold tracking-tight text-slate-900 dark:text-white">Create account</h1>
        <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">Register to report issues, track civic responses, and follow project updates in your ward.</p>
      </div>
      <div v-if="error" class="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 rounded-lg text-red-700 dark:text-red-400 text-sm">{{ error }}</div>
      <form @submit.prevent="submit" class="space-y-4">
        <div><label class="label">Full Name</label><input v-model="form.full_name" required class="input" placeholder="Ravi Kumar" /></div>
        <div><label class="label">Email</label><input v-model="form.email" type="email" required class="input" placeholder="ravi@example.com" /></div>
        <div><label class="label">Phone</label><input v-model="form.phone" class="input" placeholder="+91 9876543210" /></div>
        <div><label class="label">Ward Number</label><input v-model="form.ward_number" class="input" placeholder="Ward-42" /></div>
        <div><label class="label">Password</label><input v-model="form.password" type="password" required class="input" placeholder="Min 8 chars with a digit" /></div>
        <button type="submit" :disabled="loading" class="btn-primary w-full justify-center py-2.5">
          <span v-if="loading">Creating account…</span>
          <span v-else class="inline-flex items-center gap-2">Create Account <ArrowRight class="h-4 w-4" /></span>
        </button>
      </form>
      <div class="mt-4 text-center text-sm">
        <RouterLink to="/login" class="inline-flex items-center gap-2 text-primary-600 dark:text-primary-400 hover:underline">
          <ArrowLeft class="h-4 w-4" />
          Back to Login
        </RouterLink>
        <div class="mt-3">
          <RouterLink to="/" class="text-slate-400 hover:text-slate-200">Return to landing page</RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>
