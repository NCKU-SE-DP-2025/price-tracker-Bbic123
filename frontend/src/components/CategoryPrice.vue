<template>
	<div class="category-price-wrapper">
		<h2>{{ categoryName }}</h2>

		<div v-if="isLoading" class="loading-text">Loading...</div>
		<div v-if="errorMessage" class="error">{{ errorMessage }}</div>

		<table v-if="!isLoading && !errorMessage">
			<thead>
				<tr>
					<th>商品名稱</th>
					<th>規格</th>
					<th>{{ latestDataTime }} 最新價格</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="data in priceData" :key="data.編號">
					<td>{{ data.產品名稱 }}</td>
					<td>{{ data.規格 }}</td>
					<td>{{ latestPrice(data.統計值) }}</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>

<script setup>
import { computed } from 'vue'
import Categories from '@/constants/categories'

/* === props（沿用你原本的需求） === */
const props = defineProps({
	category: { type: String, required: true },
	priceData: { type: Array, required: true },
	isLoading: { type: Boolean, required: true },
	errorMessage: { type: String, required: false }
})

/* === computed：類別中文名稱 === */
const categoryName = computed(() => {
	return Categories[props.category]
})

/* === computed：表頭的最新資料時間（yyyy.mm） ===
   - 防呆：沒有資料或格式不是 a-b-c 時，顯示 '-' 或原字串 */
const latestDataTime = computed(() => {
	const first = props.priceData?.[0]
	if (!first || !first.時間終點) return '-'
	const parts = String(first.時間終點).split('-')
	if (parts.length < 2) return String(first.時間終點)
	return `${parts[0]}.${parts[1]}`
})

/* === 方法：取得最後一個非 0 的價格 ===
   - 防呆：空字串/undefined/NaN 都會回 '-' */
function latestPrice(prices_str) {
	if (prices_str === undefined || prices_str === null || prices_str === '') return '-'
	const number = String(prices_str).split(',').map(n => Number(n))
	let i = number.length - 1
	while (i >= 0 && (isNaN(number[i]) || number[i] === 0)) i--
	return i === -1 ? '-' : number[i]
}
</script>

<style scoped>
.error {
	color: #FF6F6F;
}
table {
	width: 100%;
	border-collapse: collapse;
	background-color: #2E2E2E;
	/* text-align: center; */
}
th, td {
	border: 1px solid #888888;
	text-align: center;
	padding: .5em 1em;
}
th{
	background-color: #0F2C44;
	color: white;
}
h2{
	margin-bottom: .5em;
	font-size: 1.5em;
	font-weight: bold;
}
.category-price-wrapper{
	background-color: #2E2E2E;
	border-radius: 1em;
	padding: 2em;
	border: 2px solid #464646;
}
.loading-text { color: #99CEFF; }
</style>
