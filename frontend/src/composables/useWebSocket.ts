import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

export function useWebSocket() {
  const auth = useAuthStore()
  const connected = ref(false)
  let ws: WebSocket | null = null
  const handlers: Record<string, ((payload: any) => void)[]> = {}

  function connect() {
    if (!auth.user) return
    const base = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
    const rooms = [auth.user.department_id ? `department:${auth.user.department_id}` : ''].filter(Boolean).join(',')
    ws = new WebSocket(`${base}/api/v1/ws?user_id=${auth.user.id}&rooms=${rooms}`)

    ws.onopen = () => { connected.value = true }
    ws.onclose = () => { connected.value = false; setTimeout(connect, 3000) }
    ws.onmessage = (e) => {
      try {
        const { type, payload } = JSON.parse(e.data)
        if (type === 'heartbeat') { ws?.send(JSON.stringify({ type: 'ping', ts: Date.now() })); return }
        handlers[type]?.forEach(h => h(payload))
        handlers['*']?.forEach(h => h({ type, payload }))
      } catch {}
    }
    ws.onerror = () => ws?.close()
  }

  function on(eventType: string, handler: (payload: any) => void) {
    handlers[eventType] = handlers[eventType] || []
    handlers[eventType].push(handler)
  }

  function off(eventType: string, handler: (payload: any) => void) {
    handlers[eventType] = (handlers[eventType] || []).filter(h => h !== handler)
  }

  onMounted(connect)
  onUnmounted(() => ws?.close())

  return { connected, on, off }
}
