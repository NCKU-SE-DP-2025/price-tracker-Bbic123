<template>
	<nav class="navbar">
		<!-- 左側品牌 -->
		<div class="title">
			<RouterLink to="/overview">價格追蹤小幫手</RouterLink>
		</div>

		<!-- 漢堡（僅手機顯示） -->
		<button
			class="hamburger"
			type="button"
			:aria-expanded="menuOpen ? 'true' : 'false'"
			aria-controls="primary-menu"
			aria-label="切換主選單"
			@click="toggleMenu"
		>☰</button>

		<!-- 選單：桌機水平；手機收合/展開 -->
		<ul
			id="primary-menu"
			class="options"
			:class="{ open: menuOpen }"
			@click="autoCloseOnMobile"
		>
			<li><RouterLink to="/overview" class="bar_btn">物價概覽</RouterLink></li>
			<li><RouterLink to="/trends" class="bar_btn">物價趨勢</RouterLink></li>
			<li><RouterLink to="/news" class="bar_btn">相關新聞</RouterLink></li>
			<li v-if="!isLoggedIn"><RouterLink to="/login" class="bar_btn">登入</RouterLink></li>
			<li
				v-else
				class="bar_btn"
				role="button"
				tabindex="0"
				@click="handleLogout"
				@keyup.enter="handleLogout"
			>
				Hi, {{ getUserName }}！登出
			</li>
		</ul>
	</nav>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'

const auth = useAuthStore()
const { isLoggedIn, getUserName } = storeToRefs(auth)
const handleLogout = () => {
	auth.logout()
	if (window.innerWidth <= 768) menuOpen.value = false
}

const menuOpen = ref(false)
const toggleMenu = () => { menuOpen.value = !menuOpen.value }
const autoCloseOnMobile = () => {
	if (window.innerWidth <= 768) menuOpen.value = false
}
</script>

<style scoped>
.navbar {
	display: flex;
	justify-content: space-between;
	align-items: center;
	background: #252525;
	border-bottom: 1px solid #333;
	padding: 10px;
	height: 4.5em;
	width: 100%;
}

/* 品牌：固定透明背景，不受 active/hover 影響 */
.title > a {
	font-size: 1.4em;
	font-weight: bold;
	color: #eaeaea !important;
	text-decoration: none;
	background: transparent !important; /* 關鍵：品牌永遠不變底色 */
}

/* 右側清單（桌機水平） */
.options {
	list-style: none;
	display: flex;
	gap: 13px;
	margin: 0;
	padding: 0;
}

/* 連結／按鈕共用的膠囊外觀 */
.bar_btn {
	color: #eaeaea;
	text-decoration: none;
	display: inline-block;
	padding: 4px 9px;
	border-radius: 6px;
	background: transparent;
}

/* 滑過 / 鍵盤聚焦：變深（只作用在選單的按鈕） */
.bar_btn:is(:hover, :focus-visible) { background: #3c3c3c; }

/* 按下（滑鼠按住）：更深 */
.bar_btn:active { background: #414141; }

/* ✅ 只在右側選單的 active link 上色；品牌不受影響 */
.options :deep(.router-link-active) {
	background: #3c3c3c;
	font-weight: 600;
}

/* 漢堡預設隱藏（桌機） */
.hamburger {
	display: none;
	background: transparent;
	border: 0;
	color: #eaeaea;
	font-size: 1.4em;
	line-height: 1;
	cursor: pointer;
}

/* 手機（≤768px）：預設收合，點漢堡展開 */
@media (max-width: 768px) {
	.navbar { flex-wrap: wrap; height: auto; }

	.hamburger { display: inline-block; margin-left: auto; }

	.options {
		display: none;              /* 手機預設收起 */
		flex-direction: column;
		width: 100%;
		margin-top: 8px;
		border-top: 1px solid #333;
	}
	.options.open { display: flex; } /* menuOpen 時展開 */

	.options li {
		text-align: center;
		padding: 7px 0;
	}
}
</style>
