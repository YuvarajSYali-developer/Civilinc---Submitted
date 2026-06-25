<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { gisApi } from '@/services/api'
import type { Map as LMap } from 'leaflet'

const mapContainer = ref<HTMLElement|null>(null)
const layer = ref<'complaints'|'projects'|'heatmap'>('complaints')
const loading = ref(false)
let map: LMap|null = null; let L: any = null; let markers: any = null

async function initMap() {
  L = (await import('leaflet')).default
  await import('leaflet/dist/leaflet.css')
  if (!mapContainer.value || map) return
  map = L.map(mapContainer.value).setView([12.9716, 77.5946], 12)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors', maxZoom: 18
  }).addTo(map)
  await loadLayer()
}

async function loadLayer() {
  if (!map || !L) return
  if (markers) { map.removeLayer(markers) }
  loading.value = true
  try {
    if (layer.value === 'complaints') {
      const { data } = await gisApi.complaintPoints({ limit: 500 })
      const colors: Record<string,string> = { critical:'#ef4444', high:'#f97316', medium:'#eab308', low:'#22c55e' }
      markers = L.layerGroup(
        data.features.map((f: any) => {
          const c = f.properties; const col = colors[c.priority] || '#6b7280'
          return L.circleMarker([f.geometry.coordinates[1], f.geometry.coordinates[0]], {
            radius:6, fillColor:col, color:'white', weight:1.5, opacity:1, fillOpacity:0.85
          }).bindPopup(`<div class="text-xs"><b>${c.complaint_number}</b><br>${c.title}<br><span style="color:${col}">${c.priority}</span> · ${c.status}</div>`)
        })
      ).addTo(map)
    } else if (layer.value === 'projects') {
      const { data } = await gisApi.projectPoints({ limit: 300 })
      const STATUS_COLOR: Record<string,string> = { completed:'#22c55e', in_progress:'#3b82f6', planning:'#94a3b8', tendering:'#f59e0b', on_hold:'#ef4444' }
      markers = L.layerGroup(
        data.features.map((f: any) => {
          const p = f.properties; const col = STATUS_COLOR[p.status]||'#94a3b8'
          return L.circleMarker([f.geometry.coordinates[1], f.geometry.coordinates[0]], {
            radius:8, fillColor:col, color:'white', weight:2, opacity:1, fillOpacity:0.8
          }).bindPopup(`<div class="text-xs"><b>${p.project_number}</b><br>${p.title}<br>${p.status} · ${p.completion_percentage}%</div>`)
        })
      ).addTo(map)
    }
  } finally { loading.value = false }
}

onMounted(initMap)
onUnmounted(() => { if (map) { map.remove(); map = null } })
</script>
<template>
  <div class="space-y-4 h-full flex flex-col">
    <div class="page-header flex items-center justify-between flex-shrink-0">
      <div><h1 class="page-title">GIS Map</h1><p class="page-subtitle">Urban infrastructure spatial view — Bengaluru BBMP</p></div>
      <div class="flex gap-2">
        <button v-for="l in ['complaints','projects']" :key="l" @click="layer=l as any; loadLayer()"
          :class="['btn-sm capitalize', layer===l ? 'btn-primary' : 'btn-secondary']">{{ l }}</button>
      </div>
    </div>
    <div class="card flex-1 overflow-hidden relative" style="min-height:500px">
      <div v-if="loading" class="absolute inset-0 bg-white/50 dark:bg-surface-900/50 z-10 flex items-center justify-center">
        <span class="text-slate-500">Loading map data…</span>
      </div>
      <div ref="mapContainer" class="w-full h-full rounded-xl" style="min-height:500px"></div>
    </div>
    <!-- Legend -->
    <div class="card card-body py-3">
      <div class="flex flex-wrap gap-4 text-xs">
        <div v-if="layer==='complaints'" class="flex flex-wrap gap-3">
          <span v-for="[label,color] in [['Critical','#ef4444'],['High','#f97316'],['Medium','#eab308'],['Low','#22c55e']]" :key="label" class="flex items-center gap-1.5">
            <span class="w-3 h-3 rounded-full inline-block" :style="`background:${color}`"></span>{{ label }}
          </span>
        </div>
        <div v-else class="flex flex-wrap gap-3">
          <span v-for="[label,color] in [['Completed','#22c55e'],['In Progress','#3b82f6'],['Planning','#94a3b8'],['On Hold','#ef4444']]" :key="label" class="flex items-center gap-1.5">
            <span class="w-3 h-3 rounded-full inline-block" :style="`background:${color}`"></span>{{ label }}
          </span>
        </div>
        <span class="text-slate-400 ml-auto">Click any marker for details</span>
      </div>
    </div>
  </div>
</template>
