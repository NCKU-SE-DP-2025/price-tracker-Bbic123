<template>
	<div class="wrapper">
		<h1>物價趨勢</h1>
		<div class="content">
			<div class="selects">
				<select v-model="selectedCategory">
					<option disabled value="">請選擇商品類別</option>
					<option
						v-for="category in categoryKeys"
						:key="category"
						:value="category"
					>
						{{ categoryName(category) }}
					</option>
				</select>

				<select v-model="selectedProduct">
					<option disabled value="">請選擇商品</option>
					<option
						v-for="product in products"
						:key="product.產品名稱"
						:value="product"
					>
						{{ product.產品名稱 }}
					</option>
				</select>
			</div>

			<div v-if="selectedProduct" class="visualize">
				<TrendingChart :data="selectedProduct" />
				<TrendingTable :data="selectedProduct" />
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { usePricesStore } from '@/stores/prices'
import Categories from '@/constants/categories'
import TrendingTable from '@/components/TrendingTable.vue'
import TrendingChart from '@/components/TrendingChart.vue'

/* --- 本地狀態 --- */
const selectedCategory = ref('')   // 使用者選擇的類別（key）
const selectedProduct  = ref('')   // 使用者選擇的商品（物件；清空時設為 '' 以相容原本邏輯）

/* --- Store --- */
const store = usePricesStore()

/* --- 計算屬性 --- */
const categoryKeys = computed(() => Object.keys(Categories))

const products = computed(() => {
	return selectedCategory.value
		? store.getPricesByCategory(selectedCategory.value) ?? []
		: []
})

/* --- 方法（取代 methods） --- */
function categoryName(categoryKey) {
	return Categories[categoryKey]
}

/* --- 監聽（取代 watch 選項） --- */
watch(selectedCategory, () => {
	// 重置商品選擇
	selectedProduct.value = ''
	// 你原始程式有設定 productList 與 productData，但畫面未使用，我們省略不必要狀態
})

watch(selectedProduct, () => {
	// 與原邏輯一致：選到商品時在 console 看一下
	console.log(selectedProduct.value)
})

/* --- 生命週期（取代 created） --- */
onMounted(() => {
	store.fetchPrices()
})
</script>

<style scoped>
.wrapper {
	padding: 3em 5em;
	background: #1e1e1e;
	min-height: calc(100vh - 4.5em);
	height: calc(100% - 4.5em);
	box-sizing: border-box;
	width: 100%;
}

.content {
	margin-top: 2em;
	background-color: #2E2E2E;
	border-radius: 1em;
	padding: 2em;
	width: 100%;
	border: 2px solid #464646;
}

.selects {
	display: flex;
	justify-content: flex-start;
}

.selects > select {
	padding: .5em;
	font-size: 1.1em;
	margin-right: 1em;
	border-radius: .5em;
	border: 1px solid #464646;
	outline: none;
	cursor: pointer;
	appearance: auto !important;
	
	background: #2a2a2a;         /* ★ 深色底 */
	color: #eaeaea;              /* ★ 淺色字 */
}

.visualize > * {
	flex: 1 1 50%;
	box-sizing: border-box;
	padding: 1em;
}

.selects > select::-webkit-scrollbar{ width:10px; }
.selects > select::-webkit-scrollbar-thumb{ background:#555; border-radius:8px; }
.selects > select::-webkit-scrollbar-track{ background:#2a2a2a; }

</style>
