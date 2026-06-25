<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { usersApi } from '@/services/api'
import { useUIStore } from '@/stores/ui'
const auth = useAuthStore(); const ui = useUIStore()
const form = reactive({ full_name: auth.user?.full_name??'', phone:'', ward_number: auth.user?.ward_number??'', bio:'' })
const saving = ref(false)
async function save() {
  if (!auth.user) return
  saving.value = true
  try { await usersApi.update(auth.user.id, form); await auth.fetchMe(); ui.toast('Profile updated','success') }
  catch { ui.toast('Update failed','error') } finally { saving.value = false }
}
</script>
<template>
  <div class="max-w-xl mx-auto space-y-5">
    <div class="page-header"><h1 class="page-title">My Profile</h1></div>
    <div class="card card-body space-y-4">
      <div class="flex items-center gap-4">
        <div class="w-16 h-16 bg-primary-100 dark:bg-primary-900/40 rounded-full flex items-center justify-center text-primary-700 dark:text-primary-300 text-2xl font-bold">{{ auth.user?.full_name?.charAt(0) }}</div>
        <div>
          <div class="font-bold text-lg text-slate-900 dark:text-white">{{ auth.user?.full_name }}</div>
          <div class="text-sm text-slate-400">{{ auth.user?.email }}</div>
          <span class="badge bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 capitalize mt-1">{{ auth.user?.role }}</span>
        </div>
      </div>
      <hr>
      <div class="space-y-3">
        <div><label class="label">Full Name</label><input v-model="form.full_name" class="input" /></div>
        <div><label class="label">Phone</label><input v-model="form.phone" class="input" placeholder="+91 9876543210" /></div>
        <div><label class="label">Ward Number</label><input v-model="form.ward_number" class="input" placeholder="Ward-42" /></div>
        <div><label class="label">Bio</label><textarea v-model="form.bio" class="input min-h-20" placeholder="Brief description…"></textarea></div>
        <div class="flex gap-2 text-sm text-slate-400">
          <span>Employee ID: {{ auth.user?.employee_id ?? '—' }}</span>
          <span>·</span>
          <span>{{ auth.user?.designation ?? '—' }}</span>
        </div>
        <button @click="save" :disabled="saving" class="btn-primary">{{ saving ? 'Saving…' : 'Save Changes' }}</button>
      </div>
    </div>
  </div>
</template>
