<template>
	<nav class="navbar" :class="{ 'menu-open': menuOpen }">
		<div class="title"><RouterLink to="/overview">價格追蹤小幫手</RouterLink></div>

		<!-- ✅ 綁定 open class，menuOpen=true 才展開（在手機版生效） -->
		<ul class="options" :class="{ open: menuOpen }" @click="handleMenuClick">
			<li><RouterLink to="/overview">物價概覽</RouterLink></li>
			<li><RouterLink to="/trending">物價趨勢</RouterLink></li>
			<li><RouterLink to="/news">相關新聞</RouterLink></li>
			<li v-if="!isLoggedIn"><RouterLink to="/login">登入</RouterLink></li>
			<li v-else @click="logout">Hi, {{ getUserName }}! 登出</li>
		</ul>

		<!-- ✅ aria-expanded 動態綁定 -->
		<button
			class="hamburger"
			@click="toggleMenu"
			aria-label="切換選單"
			:aria-expanded="menuOpen.toString()"
		>☰</button>
	</nav>
</template>

<script setup>

import { ref, computed, watch } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRoute } from 'vue-router';

// state
const menuOpen = ref(false);

// stores & derived state
const userStore = useAuthStore();

const isLoggedIn = computed(
	() => userStore.isLoggedIn
);
const getUserName = computed(
	() => userStore.getUserName
);

function logout() {
	userStore.logout();
}

function toggleMenu() {
	menuOpen.value = !menuOpen.value;
}

function handleMenuClick(e) {
	if(window.matchMedia('(max-width: 768px)').matches) {
		const isLink = e.target.closest('a, li');
		if(isLink) menuOpen.value = false;
	}
}

const route = useRoute();
watch(
	() => route.fullPath,
	() => { menuOpen.value = false; }
);

</script>

<style scoped>
.navbar {
	display: flex;
	justify-content: space-between;
	background-color: #f3f3f3;
	padding: 1.5em;
	height: 4.5em;
	width: 100%;
	align-items: center;
	box-shadow: 0 0 5px #000000;
}

.navbar ul {
	list-style: none;
	display: flex;
	justify-content: space-around;
}

.title > a {
	font-size: 1.4em;
	font-weight: bold;
	color: #2c3e50 !important;
}

.navbar li {
	color: #575B5D;
	margin: 0 .5em;
	font-size: 1.2em;
}

.navbar li:hover{
	cursor: pointer;
	font-weight: bold;
}

.navbar a {
	text-decoration: none;
	color: #575B5D;
}

.navbar .hamburger {
	display: none;
}

@media (max-width: 768px) {
	.navbar {
		flex-wrap: wrap;
		height: auto;
		padding-bottom: 1.3em;
	}

	.navbar.menu-open {
		padding-bottom: 0;     /* ← 打開時 */
	}

	.navbar .title { order: 0; }

	.navbar .hamburger {
		order: 1;
		display: inline-block;
		margin-left: auto;
		background: transparent;
		border: 0;
		font-size: 1.4em;
		line-height: 1;
		cursor: pointer;
	}

	/* 📌 手機預設收合（none），加上 .open 才展開（flex） */
	.navbar .options {
		display: none;
		order: 2;
		flex-direction: column;
		width: 100%;
		margin: 8px 0 0 0;
		padding: 0;
	}
	.navbar .options.open {
		display: flex;
	}
	.navbar .options li {
		text-align: center;
		padding: 7px 0;
		border-top: 1px solid #BBBBBB;
		margin: 0;
	}
}
</style>
