<template>
	<div class="trending-table">
		<table>
			<thead>
				<tr>
					<th rowspan="2">年份</th>
					<th v-for="month in months" :key="month">{{ month }}</th>
				</tr>
			</thead>
			<tbody>
				<template v-for="year in years" :key="year">
					<tr>
						<td>{{ year }}</td>
						<template
							v-for="(value, monthIndex) in getYearData(year)"
							:key="year + '-month-' + monthIndex"
						>
							<td>{{ valueDisplay(value) }}</td>
						</template>
					</tr>
				</template>
			</tbody>
		</table>
	</div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

/* ===== props ===== */
const props = defineProps({
	data: { type: Object, required: true } // 內含：時間起點、時間終點、統計值(逗號字串)
})

/* ===== 本地狀態（ref） ===== */
const yearData = ref({}) // { 2024: [ '0','0',... ], 2025: [ ... ] }

/* ===== 常數 / 計算屬性 ===== */
const months = [
	'Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'
]

const years = computed(() => {
	const start = safeDate(props.data?.時間起點)
	const end = safeDate(props.data?.時間終點)
	if (!start || !end) return []
	const arr = []
	for (let y = start.getFullYear(); y <= end.getFullYear(); y++) arr.push(y)
	return arr
})

/* ===== 方法（取代 options.methods） ===== */
function getYearData(year) {
	return yearData.value[year] ?? Array(12).fill('0')
}

function valueDisplay(value) {
	return (value === '0' || value === 0 || value === '' || value == null) ? '-' : value
}

function processInitData() {
	const start = safeDate(props.data?.時間起點)
	const end = safeDate(props.data?.時間終點)
	if (!start || !end) {
		yearData.value = {}
		return
	}

	// 1) 將「統計值」字串拆成陣列（一次就好）
	const values = String(props.data?.統計值 ?? '')
		.split(',')
		.map(v => (v === '' ? '0' : v))

	const startMonth = start.getMonth() + 1
	const endMonth = end.getMonth() + 1
	const startYear = start.getFullYear()
	const endYear = end.getFullYear()

	const result = {}

	for (let y = startYear; y <= endYear; y++) {
		const row = []
		for (let m = 1; m <= 12; m++) {
			// 邊界以外補 0
			if ((y === startYear && m < startMonth) || (y === endYear && m > endMonth)) {
				row.push('0')
				continue
			}
			// 在範圍內：計算 values 的索引
			const idx = (y - startYear) * 12 + (m - startMonth)
			row.push(values[idx] ?? '0')
		}
		result[y] = row
	}

	yearData.value = result
}

/* ===== 監聽 props 變化（取代 watch + created） ===== */
watch(
	() => props.data,
	(newVal) => {
		if (newVal) processInitData()
	},
	{ deep: true, immediate: true }
)

/* ===== 小工具 ===== */
function safeDate(input) {
	const d = new Date(input)
	return isNaN(d.getTime()) ? null : d
}
</script>

<style scoped>
.trending-table {
	margin-top: 2em;
}

table {
	width: 100%;
	border-collapse: collapse;
}

th,
td {
	border: 1px solid #464646;
	padding: 0.5em;
	text-align: center;
}
</style>
