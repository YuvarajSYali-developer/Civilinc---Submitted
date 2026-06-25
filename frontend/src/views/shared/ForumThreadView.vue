<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { forumApi } from '@/services/api'
import { ArrowLeft } from 'lucide-vue-next'
const route = useRoute()
const thread = ref<any>(null); const comments = ref<any[]>([]); const newComment = ref('')
onMounted(async () => {
  const [t, c] = await Promise.all([forumApi.getThread(route.params.id as string), forumApi.listComments(route.params.id as string)])
  thread.value = t.data; comments.value = c.data
})
async function postComment() {
  if (!newComment.value.trim()) return
  const { data } = await forumApi.addComment(route.params.id as string, { body: newComment.value })
  comments.value.push(data); newComment.value = ''
}
</script>
<template>
  <div class="max-w-3xl mx-auto space-y-5">
    <RouterLink to="/forum" class="btn-ghost btn-sm"><ArrowLeft class="h-4 w-4" />Forum</RouterLink>
    <div v-if="thread" class="card card-body">
      <h1 class="text-xl font-bold text-slate-900 dark:text-white mb-2">{{ thread.title }}</h1>
      <div class="text-xs text-slate-400 mb-4">{{ thread.category }} · {{ new Date(thread.created_at).toLocaleString('en-IN') }}</div>
      <p class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">{{ thread.body }}</p>
    </div>
    <div class="space-y-3">
      <h3 class="font-semibold text-slate-900 dark:text-white">{{ comments.length }} Comments</h3>
      <div v-for="c in comments" :key="c.id" class="card card-body">
        <p class="text-sm text-slate-700 dark:text-slate-200">{{ c.body }}</p>
        <div class="text-xs text-slate-400 mt-2">{{ new Date(c.created_at).toLocaleString('en-IN') }}</div>
      </div>
    </div>
    <div class="card card-body space-y-3">
      <label class="label">Add Comment</label>
      <textarea v-model="newComment" class="input min-h-24 resize-y" placeholder="Write your reply…"></textarea>
      <button @click="postComment" class="btn-primary">Post Comment</button>
    </div>
  </div>
</template>
