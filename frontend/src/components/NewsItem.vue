<template>
	<div class="news-item">
		<div class="row">
			<!-- 文字區：點擊開啟詳情 -->
			<div class="texts" role="button" tabindex="0" @click="showDialog" @keyup.enter="showDialog">
				<h2 class="title">{{ news.title }}</h2>
				<p class="time">{{ news.time }}</p>

				<div v-if="hasDetails">
					<p><strong>原因：</strong>{{ news.reason }}</p>
					<p><strong>影響：</strong>{{ news.summary }}</p>
				</div>
				<div v-else>
					<p class="preview">{{ shortContent }}</p>
				</div>
			</div>

			<!-- 產生摘要（僅登入、且尚未有摘要/非載入中） -->
			<button
				v-if="!hasDetails && !news.isSummaryLoading && isLoggedIn"
				class="summary-btn"
				type="button"
				aria-label="產生摘要"
				@click="fetchSummary"
			>
				<i class="bi bi-stars"></i>
			</button>
			<div v-if="!hasDetails && news.isSummaryLoading && isLoggedIn" class="loader" aria-hidden="true"></div>
		</div>

		<!-- 按讚 -->
		<button
			v-if="'upvotes' in news"
			class="upvote-btn"
			type="button"
			:aria-pressed="news.is_upvoted ? 'true' : 'false'"
			@click="toggleUpvote(news.id)"
		>
			<i class="bi bi-fire" :class="{ 'fire-upvoted': news.is_upvoted }"></i>
			<span class="upvote-count">{{ news.upvotes }}</span>
		</button>
	</div>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useNewsStore } from '@/stores/news'
import { storeToRefs } from 'pinia'

const props = defineProps({ news: { type: Object, required: true } })
const emit = defineEmits(['show-dialog', 'fetch-summary'])

/* Auth */
const { isLoggedIn } = storeToRefs(useAuthStore())

/* Actions */
const showDialog = () => emit('show-dialog')
const fetchSummary = () => {
	if (props.news?.isSummaryLoading) return
	emit('fetch-summary')
}
const toggleUpvote = (id) => useNewsStore().toggleUpvote(id)

/* Computed */
const news = computed(() => props.news)
const hasDetails = computed(() => !!(news.value && news.value.reason && news.value.summary))
const shortContent = computed(() => {
	const t = news.value?.content ?? ''
	return t.length > 200 ? t.slice(0, 200) + '…' : t
})
</script>

<style scoped>
/* 容器 */
.news-item {
	padding: 14px 12px;
	border-bottom: 1px solid #3a3a3a;
	color: #eaeaea;
}
.row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
}

/* 文字區 */
.texts {
	flex: 1 1 auto;
	padding: 14px;
	border-radius: 10px;
	outline: none;
	transition: background .12s ease, border-color .12s ease;
	border: 1px solid transparent;
}
.texts:hover,
.texts:focus-visible { background: #2a2a2a; border-color: #3e3e3e; cursor: pointer; }

.title { margin: 0 0 4px; font-size: 1.25rem; line-height: 1.35; }
.time { color: #9aa0a6; margin: 2px 0 10px; font-size: .95rem; }
.preview { color: #d9d9d9; }

/* 產生摘要 */
.summary-btn{
	display: inline-grid;
	place-items: center;
	width: 40px; height: 40px;
	border-radius: 10px;
	border: 1px solid #525252;
	background: #2a2a2a;
	color: #eaeaea;
	cursor: pointer;
	transition: background .12s ease, border-color .12s ease;
}
.summary-btn:hover { background:#3a3a3a; border-color:#6a6a6a; }

/* Hover 時才顯示按鈕（桌機體驗） */
@media (hover:hover){
	.summary-btn{ opacity:0; pointer-events:none; }
	.news-item:hover .summary-btn{ opacity:1; pointer-events:auto; }
}

/* Loader */
.loader {
	width: 30px; height: 30px; padding: 6px; border-radius: 50%;
	background:#20A7E8;
	--_m: conic-gradient(#0000 10%,#000), linear-gradient(#000 0 0) content-box;
	-webkit-mask: var(--_m); mask: var(--_m);
	-webkit-mask-composite: source-out; mask-composite: subtract;
	animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(1turn); } }

/* 按讚 */
.upvote-btn{
	margin-top: 8px;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: 6px;
	padding: 8px 14px;
	border-radius: 999px;
	background: #2a2a2a;
	border: 1px solid #4a4a4a;
	color: #eaeaea;
	cursor: pointer;
	transition: background .12s ease, border-color .12s ease;
}
.upvote-btn:hover{ background:#3a3a3a; border-color:#6a6a6a; }
.upvote-btn i{ font-size: 1.2rem; color:#bdbdbd; }
.fire-upvoted{ color:#f6620c !important; }
.upvote-count{ font-weight:600; color:#d0d0d0; }
</style>
