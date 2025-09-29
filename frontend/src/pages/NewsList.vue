<template>
	<div class="wrapper">
		<h1>相關新聞</h1>

		<div class="search-bar">
			<input
				v-model="prompt"
				placeholder="輸入你的搜尋prompt，讓AI幫你找相關的新聞吧！例如：「我想獲取雞蛋價格的資訊」"
				class="search-input"
				@keyup.enter="searchNewsBasedOnPrompt"
			/>
			<i class="bi bi-search" @click="searchNewsBasedOnPrompt"></i>
		</div>

		<div class="content">
			<div v-if="isLoading" style="color:#99CEFF;">loading...</div>

			<div v-else>
				<NewsItem
					v-for="(news, index) in shownList"
					:key="news.id"
					:news="news"
					@show-dialog="showDialog(news)"
					@fetch-summary="fetchSummary(news.content, index)"
				/>
				<div v-if="isEmpty">
					<p style="color:#99CEFF;">找不到相關新聞！</p>
				</div>
			</div>
		</div>

		<NewsDialog :news="selectedNews" v-model:visible="isDialogVisible" />
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useNewsStore } from '@/stores/news'
import { storeToRefs } from 'pinia'
import NewsItem from '@/components/NewsItem.vue'
import NewsDialog from '@/components/NewsDialog.vue'

/* ---- Pinia store ---- */
const newsStore = useNewsStore()
const { getNews, isLoading, newsList } = storeToRefs(newsStore)
// 你的畫面原本就是用 getter 當來源，保留此邏輯
const shownList = computed(() => getNews.value)

/* ---- 本地狀態 ---- */
const prompt = ref('')
const selectedNews = ref(null)
const isDialogVisible = ref(false)

/* ---- lifecycle ---- */
onMounted(() => {
	newsStore.fetchNews()
})

/* ---- methods ---- */
function searchNewsBasedOnPrompt() {
	const q = prompt.value.trim()
	if (!q) return
	// 觸發以 prompt 搜尋新聞
	nwsPromptSearch(q)
	prompt.value = ''
}
function nwsPromptSearch(q) {
	// 抽出函式，未來若要做防抖/節流可在這裡擴充
	newsStore.promptSearchNews(q)
}

function showDialog(news) {
	selectedNews.value = news
	isDialogVisible.value = true
}
function fetchSummary(content, index) {
	newsStore.fetchNewsSummary(content, index)
}

/* ---- computed ---- */
const isEmpty = computed(() => (newsList.value?.length ?? 0) === 0)
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
	background-color: #2E2E2E;
	margin-top: 1em;
	border-radius: 1em;
	padding: 1em 3em;
	border: 2px solid #464646;
}
.news-item{
	border-bottom: #aaaaaa 1px solid;
}
.news-item:last-child{
	border-bottom: none;
}
.search-bar{
	background-color: #2E2E2E;
	display: inline-flex;
	border-radius: .5em;
	box-sizing: border-box;
	text-align: start;
	margin-top: 1em;
	padding: 1em;
	width: 80%;
	border: 2px solid #464646;
}

.search-bar input{
	border: none;
	outline: none;
	font-size: .9em;
	box-sizing: border-box;
	flex-grow: 1;
	margin-right: 1em;
}

.search-bar .search-input::placeholder { color: #757575; }

.search-bar i{
	cursor: pointer;
}

.search-bar button:hover{
	cursor: pointer;
}

.search-bar .search-input{ color: #fff; }

.content::-webkit-scrollbar{ height:10px; width:10px; }
.content::-webkit-scrollbar-thumb{ background:#555; border-radius:8px; }
.content::-webkit-scrollbar-track{ background:#2e2e2e; }

</style>
