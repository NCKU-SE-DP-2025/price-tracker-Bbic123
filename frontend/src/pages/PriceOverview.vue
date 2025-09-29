<template>
	<div class="wrapper">
		<h1>各類商品物價概覽</h1>

		<h3 v-if="!isLoading" class="subtitle">
			資料更新時間：{{ updatedTime }}
		</h3>

		<div class="prices">
			<CategoryPrice
				class="category"
				v-for="category in categoryList"
				:key="category"
				:category="category"
				:isLoading="isLoading"
				:errorMessage="errorMessage"
				:priceData="getPriceData(category)"
			/>
		</div>
	</div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import CategoryPrice from '@/components/CategoryPrice.vue'
import Categories from '@/constants/categories'
import { usePricesStore } from '@/stores/prices'

/* Pinia store */
const pricesStore = usePricesStore()
const { isLoading, errorMessage, updatedTime } = storeToRefs(pricesStore)

/* 類別清單：從常數物件的 key 取得 */
const categoryList = computed(() => Object.keys(Categories))

/* 依類別取資料（呼叫 store 的 getter/action） */
const getPriceData = (category) => pricesStore.getPricesByCategory(category)

/* 掛載時抓資料（等同原本 created() 中的 fetchPrices） */
onMounted(() => {
	pricesStore.fetchPrices()
})
</script>

<style scoped>
.wrapper{
	padding: 3em 5em;
	background: #1e1e1e;
	min-height: calc(100vh - 4.5em);
	height: calc(100% - 4.5em);
	box-sizing: border-box;
}
.prices{
	display: flex;
	justify-content: space-around;
	flex-wrap: wrap;
}
.category{
	margin: 1em;
	flex-grow: 1;
}
.subtitle{
	font-weight: normal;
	margin-top: .5em;
}
</style>
