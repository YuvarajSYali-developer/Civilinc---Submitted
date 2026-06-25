<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { forumApi } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { Megaphone, MessageSquarePlus, Pin } from 'lucide-vue-next'
const auth = useAuthStore()
const threads = ref<any[]>([]); const loading = ref(true)
const showNew = ref(false); const newThread = ref({ title:'', body:'', category:'general' })
const CATEGORIES = ['general','infrastructure','complaint','budget','announcement','emergency']
onMounted(async () => { try { const { data } = await forumApi.listThreads({ page_size:30 }); threads.value = data.items } finally { loading.value = false } })
async function create() {
  const { data } = await forumApi.createThread(newThread.value)
  threads.value.unshift(data); showNew.value = false; newThread.value = { title:'', body:'', category:'general' }
}
</script>
<template>
  <div class="space-y-5">
    <div class="page-header flex items-center justify-between">
      <div><div class="muted-kicker">Collaboration</div><h1 class="page-title">Discussion Forum</h1><p class="page-subtitle">Interdepartmental collaboration, operational notes, and official announcements.</p></div>
      <button @click="showNew=!showNew" class="btn-primary"><MessageSquarePlus class="h-4 w-4" />New Thread</button>
    </div>
    <div v-if="showNew" class="card card-body space-y-3">
      <div><label class="label">Title</label><input v-model="newThread.title" class="input" placeholder="Thread title…" /></div>
      <div><label class="label">Category</label><select v-model="newThread.category" class="select"><option v-for="c in CATEGORIES" :key="c" :value="c">{{ c }}</option></select></div>
      <div><label class="label">Body</label><textarea v-model="newThread.body" class="input min-h-28 resize-y" placeholder="Write your post…"></textarea></div>
      <div class="flex gap-2 justify-end"><button @click="showNew=false" class="btn-secondary">Cancel</button><button @click="create" class="btn-primary">Post Thread</button></div>
    </div>
    <div class="space-y-3">
      <div v-for="t in threads" :key="t.id" class="card card-body hover:border-primary-200 dark:hover:border-primary-800 transition-colors">
        <div class="flex items-start gap-3">
          <div v-if="t.is_pinned" class="icon-chip h-9 w-9 shrink-0 text-amber-500"><Pin class="h-4 w-4" /></div>
          <div v-else-if="t.is_announcement" class="icon-chip h-9 w-9 shrink-0 text-red-500"><Megaphone class="h-4 w-4" /></div>
          <div class="flex-1 min-w-0">
            <RouterLink :to="`/forum/${t.id}`" class="font-semibold text-slate-900 dark:text-white hover:text-primary-600 dark:hover:text-primary-400 line-clamp-1">{{ t.title }}</RouterLink>
            <p class="text-sm text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">{{ t.body }}</p>
            <div class="flex flex-wrap gap-3 mt-2 text-xs text-slate-400">
              <span class="capitalize px-2 py-0.5 bg-surface-100 dark:bg-surface-800 rounded">{{ t.category }}</span>
              <span>{{ t.comment_count }} replies</span>
              <span>{{ t.view_count }} views</span>
              <span>{{ new Date(t.created_at).toLocaleDateString('en-IN') }}</span>
            </div>
          </div>
        </div>
      </div>
      <div v-if="threads.length===0 && !loading" class="text-center text-slate-400 py-8">No threads yet</div>
    </div>
  </div>
</template>
