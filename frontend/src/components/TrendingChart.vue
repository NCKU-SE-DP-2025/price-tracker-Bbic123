<template>
	<div class="chart-container">
		<canvas id="trendingChart" ref="canvasEl"></canvas>
	</div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)

/* ========== props ========== */
const props = defineProps({
	data: { type: Object, required: true } // 內含：產品名稱、統計值(逗號字串)、時間起點、時間終點
})

/* ========== 本地狀態（ref） ========== */
const canvasEl = ref(null)      // 對應 <canvas ref="canvasEl">
const chart = ref(null)         // Chart.js 實例

/* ========== 入口與清理 ========== */
onMounted(() => {
	// 初次渲染
	createChart(props.data)
})

onBeforeUnmount(() => {
	// 元件卸載時銷毀圖表，避免記憶體洩漏
	if (chart.value) chart.value.destroy()
})

/* ========== 監聽資料變化（取代 options.watch） ========== */
watch(
	() => props.data,
	(newData, oldData) => {
		if (newData !== oldData) createChart(newData)
	},
	{ immediate: false }
)

/* ========== 方法（取代 options.methods） ========== */
function createChart(data) {
	if (!canvasEl.value || !data) return

	// 有舊圖先銷毀
	if (chart.value) chart.value.destroy()

	const ctx = canvasEl.value.getContext('2d')

	// 統計值轉為陣列
	let prices = String(data.統計值).split(',').map(v => parseInt(v, 10))
	let labels = generateLabels(data.時間起點, data.時間終點, prices.length)

	// 1) 去除前導 0 並同步修正標籤
	const firstNonZeroIndex = prices.findIndex(p => p !== 0)
	if (firstNonZeroIndex > 0) {
		prices = prices.slice(firstNonZeroIndex)
		labels = labels.slice(firstNonZeroIndex)
	}

	// 2) 中間的 0 以前一個有效值補上，同時做記號以改變點樣式
	let lastValid = prices[0]
	const markIdx = new Set() // 用 Set 加速查詢
	prices = prices.map((p, i) => {
		if (p === 0) {
			markIdx.add(i)
			return lastValid
		}
		lastValid = p
		return p
	})

	chart.value = new Chart(ctx, {
		type: 'line',
		data: {
			labels,
			datasets: [{
				label: data.產品名稱,
				data: prices,
				fill: false,
				borderColor: 'rgb(75, 192, 192)',
				tension: 0.1,
				pointRadius: prices.map((_, i) => markIdx.has(i) ? 5 : 3),
				pointStyle: prices.map((_, i) => markIdx.has(i) ? 'crossRot' : 'circle') // 無資料點以 cross 標示
			}]
		},
		options: {
			scales: { y: { beginAtZero: false } },
			animation: { duration: 300 },
			responsive: true,
			maintainAspectRatio: false
		}
	})
}

function generateLabels(startDate, endDate, count) {
	const start = new Date(startDate)
	const labels = []
	for (let i = 0; i < count; i++) {
		const d = new Date(start.getFullYear(), start.getMonth() + i, 1)
		const y = d.getFullYear()
		const m = String(d.getMonth() + 1).padStart(2, '0') // 月份補 0 → 01, 02, ...
		labels.push(`${y}.${m}`)
	}
	return labels
}
</script>

<style scoped>
.chart-container {
	position: relative;
	margin: auto;
	height: 30vh;
	width: 100wh; /* 保留你的原本設定，如需更準確可改為 100% 或 100vw */
}
</style>
