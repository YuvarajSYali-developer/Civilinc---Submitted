<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)
const props = defineProps<{ data: number[]; labels?: string[]; type?: string; color?: string }>()
const canvas = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null
onMounted(() => { if (canvas.value) initChart() })
watch(() => props.data, () => { chart?.destroy(); if (canvas.value) initChart() })
function initChart() {
  chart = new Chart(canvas.value!, {
    type: (props.type as any) ?? 'bar',
    data: {
      labels: props.labels ?? props.data.map((_,i) => String(i)),
      datasets: [{ data: props.data, backgroundColor: props.color ?? '#3b5fc0', borderRadius: 4 }]
    },
    options: { responsive: true, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { display: false } } }
  })
}
</script>
<template><canvas ref="canvas" /></template>
