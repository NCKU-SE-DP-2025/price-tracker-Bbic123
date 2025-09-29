<template>
	<div v-if="visible" class="cover" @click.self="close">
		<div
			class="news-dialog"
			role="dialog"
			aria-modal="true"
			:aria-label="news?.title || 'News dialog'"
		>
			<button class="close-btn" type="button" aria-label="關閉" @click="close">
				<i class="bi bi-x-lg"></i>
			</button>

			<div class="content">
				<h2 class="title">{{ news.title }}</h2>
				<p class="time">{{ news.time }}</p>

				<p class="link-row">
					<span>原文連結：</span>
					<a :href="news.url" target="_blank" rel="noopener noreferrer">
						{{ news.url }}
					</a>
				</p>

				<p v-for="(paragraph, index) in formattedContent" :key="index" class="para">
					{{ paragraph }}
				</p>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
	news: { type: Object, required: true },
	visible: { type: Boolean, default: false }
})
const emit = defineEmits(['update:visible'])

const close = () => emit('update:visible', false)

const formattedContent = computed(() => {
	const raw = props.news?.content
	if (!raw) return []
	return String(raw).split(/\r?\n/).filter(s => s.trim() !== '')
})

const news = computed(() => props.news)
const visible = computed(() => props.visible)
</script>

<style scoped>
/* 背景遮罩 */
.cover{
	position: fixed;
	inset: 0;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(0,0,0,.6);
	z-index: 1000;
}

/* 對話框（深色） */
.news-dialog{
	/* 尺寸與置中 */
	width: min(92vw, 980px);
	height: min(86vh, 780px);
	border-radius: 16px;
	overflow: hidden;

	/* 視覺 */
	background:#2e2e2e;
	color:#eaeaea;
	border:1px solid #464646;
	box-shadow: 0 12px 40px rgba(0,0,0,.45);
	position: relative;
}

/* 內容可滾動 */
.content{
	height: 100%;
	padding: 28px 36px 32px;
	overflow: auto;
	text-align: start;
}

/* 標題與時間 */
.title{
	margin: 0 0 .25em 0;
	font-size: 1.6em;
	line-height: 1.3;
	font-weight: 700;
}
.time{
	color:#9aa0a6;
	font-size:.95em;
	margin:.2em 0 1em;
}

/* 原文連結 */
.link-row{
	margin: .6em 0 1.2em;
}
.link-row a{
	color:#99CEFF;
	text-decoration: none;
	word-break: break-all;
}
.link-row a:hover{ text-decoration: underline; }

/* 內文段落 */
.para{
	font-size:1.06em;
	line-height:1.75;
	margin: .9em 0;
}

/* 關閉按鈕 */
.close-btn{
	position:absolute;
	top:10px;
	right:10px;
	display:inline-grid;
	place-items:center;
	width:40px;
	height:40px;
	border:1px solid #5a5a5a;
	border-radius:10px;
	background:#2a2a2a;
	color:#bdbdbd;
	cursor:pointer;
	transition: background .15s ease, color .15s ease, border-color .15s ease;
}
.close-btn:hover{
	background:#3a3a3a;
	color:#ffffff;
	border-color:#7a7a7a;
}

/* 自訂卷軸（僅深色外觀） */
.content::-webkit-scrollbar{ width:10px; height:10px; }
.content::-webkit-scrollbar-thumb{ background:#565656; border-radius:8px; }
.content::-webkit-scrollbar-thumb:hover{ background:#6a6a6a; }
.content::-webkit-scrollbar-track{ background:#2e2e2e; }
</style>
