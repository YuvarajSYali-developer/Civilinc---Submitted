<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ArrowLeft, ArrowRight, Building2, ClipboardList, ShieldCheck, Sparkles } from 'lucide-vue-next'

const router = useRouter()
const auth = useAuthStore()

const form = reactive({ email: '', password: '' })
const error = ref('')

async function submit() {
  error.value = ''
  try {
    await auth.login(form.email, form.password)
    router.push('/dashboard')
  } catch (e: any) {
    error.value = e?.response?.data?.detail || 'Login failed. Check your credentials.'
  }
}

const demoLogins = [
  { label: 'Commissioner', email: 'commissioner@civilinc.gov.in', password: 'Admin@1234', color: 'border-fuchsia-500/20 bg-fuchsia-500/10 text-fuchsia-200' },
  { label: 'Engineer', email: 'engineer.roads@civilinc.gov.in', password: 'Engineer@1234', color: 'border-sky-500/20 bg-sky-500/10 text-sky-200' },
  { label: 'Coordinator', email: 'coordinator@civilinc.gov.in', password: 'Coord@1234', color: 'border-teal-500/20 bg-teal-500/10 text-teal-200' },
  { label: 'Citizen', email: 'citizen1@example.com', password: 'Citizen@1234', color: 'border-emerald-500/20 bg-emerald-500/10 text-emerald-200' },
]

function fillDemo(d: any) { form.email = d.email; form.password = d.password }
</script>
<template>
  <div class="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(0,229,160,0.12),_transparent_24%),radial-gradient(circle_at_bottom_right,_rgba(37,99,235,0.16),_transparent_28%),linear-gradient(135deg,_#050b10_0%,_#0f172a_42%,_#10263b_100%)] p-4 sm:p-6">
    <div class="mx-auto grid min-h-screen max-w-7xl items-center gap-10 lg:grid-cols-[1.15fr_0.85fr]">
      <div class="hidden text-white lg:block">
        <div class="mb-6 inline-flex items-center gap-3 rounded-full border border-white/15 bg-white/8 px-4 py-2 backdrop-blur">
          <Sparkles class="h-4 w-4" />
          <span class="text-sm font-semibold">Professional civic operations workspace</span>
        </div>
        <h1 class="max-w-xl font-display text-5xl font-bold leading-[0.95] tracking-tight xl:text-6xl">
          Sign in to the command layer behind city execution.
        </h1>
        <p class="mt-5 max-w-2xl text-base leading-7 text-white/72">
          CivilInc gives leadership, engineers, coordinators, and citizens one disciplined system for complaint response, project oversight, and ward-level accountability.
        </p>
        <div class="mt-10 grid max-w-2xl gap-4 sm:grid-cols-3">
          <div class="rounded-3xl border border-white/12 bg-white/7 p-5 backdrop-blur">
            <Building2 class="h-5 w-5 text-white/90" />
            <div class="mt-4 text-2xl font-display font-bold">198</div>
            <div class="mt-1 text-sm text-white/70">Active civic projects tracked</div>
          </div>
          <div class="rounded-3xl border border-white/12 bg-white/7 p-5 backdrop-blur">
            <ShieldCheck class="h-5 w-5 text-white/90" />
            <div class="mt-4 text-2xl font-display font-bold">24/7</div>
            <div class="mt-1 text-sm text-white/70">Operational visibility across roles</div>
          </div>
          <div class="rounded-3xl border border-white/12 bg-white/7 p-5 backdrop-blur">
            <ClipboardList class="h-5 w-5 text-white/90" />
            <div class="mt-4 text-2xl font-display font-bold">1 Hub</div>
            <div class="mt-1 text-sm text-white/70">Complaints, projects, and escalations in sync</div>
          </div>
        </div>
        <div class="mt-8 flex flex-wrap gap-3 text-xs font-medium text-white/60">
          <span class="rounded-full border border-white/10 px-3 py-1.5">Commissioner visibility</span>
          <span class="rounded-full border border-white/10 px-3 py-1.5">Engineer workflow clarity</span>
          <span class="rounded-full border border-white/10 px-3 py-1.5">Citizen issue tracking</span>
        </div>
      </div>

      <div class="w-full max-w-lg justify-self-center rounded-[32px] border border-white/12 bg-slate-950/78 p-8 text-slate-100 shadow-[0_40px_120px_rgba(2,6,23,0.55)] backdrop-blur-2xl">
        <div class="mb-8">
          <RouterLink to="/" class="inline-flex items-center gap-2 text-sm font-medium text-slate-400 transition-colors hover:text-white">
            <ArrowLeft class="h-4 w-4" />
            Back to landing page
          </RouterLink>
          <div class="mt-6">
            <div class="muted-kicker">CivilInc Access</div>
            <h2 class="mt-2 text-3xl font-display font-bold tracking-tight text-white">Sign in</h2>
            <p class="mt-2 text-sm text-slate-400">Enter the BBMP urban intelligence workspace and continue where your team left off.</p>
          </div>
        </div>

        <div v-if="error" class="mb-4 rounded-2xl border border-red-500/25 bg-red-500/10 p-3 text-sm text-red-200">
          {{ error }}
        </div>

        <form @submit.prevent="submit" class="space-y-4">
          <div>
            <label class="label">Email address</label>
            <input v-model="form.email" type="email" required autocomplete="email" class="input border-white/10 bg-white/5 text-white placeholder:text-slate-500" placeholder="you@civilinc.gov.in" />
          </div>
          <div>
            <label class="label">Password</label>
            <input v-model="form.password" type="password" required autocomplete="current-password" class="input border-white/10 bg-white/5 text-white placeholder:text-slate-500" placeholder="••••••••" />
          </div>
          <button type="submit" :disabled="auth.loading" class="btn-primary w-full justify-center rounded-2xl py-3">
            <span v-if="auth.loading">Signing in…</span>
            <span v-else class="inline-flex items-center gap-2">Sign In <ArrowRight class="h-4 w-4" /></span>
          </button>
        </form>

        <div class="mt-5 grid gap-3 rounded-2xl border border-white/8 bg-white/4 p-4 text-sm text-slate-300 sm:grid-cols-2">
          <div>
            <div class="font-semibold text-white">Need citizen access?</div>
            <div class="mt-1 text-xs leading-5 text-slate-400">Register to raise complaints and track civic responses in your ward.</div>
          </div>
          <div class="flex items-center sm:justify-end">
            <RouterLink to="/register" class="inline-flex items-center gap-2 text-sm font-semibold text-emerald-300 hover:text-emerald-200">
              Register here
              <ArrowRight class="h-4 w-4" />
            </RouterLink>
          </div>
        </div>

        <!-- Demo logins -->
        <div class="mt-6 border-t border-white/8 pt-5">
          <div class="mb-3 flex items-center justify-between">
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Demo Accounts</p>
            <p class="text-[11px] text-slate-500">Tap to autofill</p>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <button v-for="d in demoLogins" :key="d.label" @click="fillDemo(d)"
              :class="['rounded-2xl border px-3 py-3 text-left text-xs font-semibold transition-colors hover:border-white/20', d.color]">
              <span class="block">{{ d.label }}</span>
              <span class="mt-1 block text-[11px] opacity-70">{{ d.email }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
