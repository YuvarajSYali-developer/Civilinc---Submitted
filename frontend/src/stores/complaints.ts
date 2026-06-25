import { defineStore } from 'pinia'
import { ref } from 'vue'
import { complaintsApi } from '@/services/api'
import type { Complaint, PaginatedResponse } from '@/types'

export const useComplaintsStore = defineStore('complaints', () => {
  const complaints = ref<Complaint[]>([])
  const total = ref(0)
  const page = ref(1)
  const loading = ref(false)
  const selected = ref<Complaint | null>(null)
  const filters = ref({ status: '', priority: '', category: '', ward_number: '', search: '' })

  async function fetchComplaints(params?: any) {
    loading.value = true
    try {
      const { data } = await complaintsApi.list({ page: page.value, page_size: 20, ...filters.value, ...params })
      complaints.value = data.items
      total.value = data.total
    } finally { loading.value = false }
  }

  async function createComplaint(data: any) {
    const { data: result } = await complaintsApi.create(data)
    await fetchComplaints()
    return result
  }

  async function updateComplaint(id: string, data: any) {
    const { data: result } = await complaintsApi.update(id, data)
    const idx = complaints.value.findIndex(c => c.id === id)
    if (idx !== -1) complaints.value[idx] = result
    return result
  }

  return { complaints, total, page, loading, selected, filters, fetchComplaints, createComplaint, updateComplaint }
})
