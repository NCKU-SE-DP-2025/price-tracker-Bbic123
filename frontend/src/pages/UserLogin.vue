<template>
	<div class="login-page">
		<h1>使用者登入</h1>

		<div class="card">
			<form @submit.prevent="login">
				<input v-model="username" type="text" placeholder="Username" required />
				<input v-model="password" type="password" placeholder="Password" required />
				<p v-if="loginError" class="error">{{ loginError }}</p>

				<div class="ops">
					<RouterLink to="/register" class="btn ghost">註冊</RouterLink>
					<button type="submit" class="btn primary">登入</button>
				</div>
			</form>
		</div>
	</div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'

const username = ref('')
const password = ref('')

const auth = useAuthStore()
const { getLoginError: loginError } = storeToRefs(auth)

function login() {
	auth.login(username.value, password.value)
}
</script>

<style scoped>
/* Page */
.login-page{
	padding: 3em 5em;
	background: #1e1e1e;
	min-height: calc(100vh - 4.5em);
	box-sizing: border-box;
	color:#eaeaea;
}

/* Card */
.card{
	margin-top: 2em;
	background: #2e2e2e;
	border: 2px solid #464646;
	border-radius: 14px;
	padding: 2em;
}

/* Form */
form{
	display: flex;
	flex-direction: column;
	gap: .6em;
}
form > input{
	color:#fff;
	background:#1f1f1f;
	border:1px solid #3a3a3a;
	border-radius:10px;
	padding:.75em 1em;
	font-size:1.05rem;
	outline:none;
	transition: border-color .12s ease, background .12s ease;
}
form > input::placeholder{ color:#757575; }
form > input:focus{
	border-color:#6aa9c8;
	background:#222;
}

/* Error */
.error{ color:#ff6f6f; margin:.2em 0 .4em; }

/* Actions */
.ops{
	margin-top:.75em;
	display:flex;
	gap:.75em;
	justify-content:center;
	align-items:center;
}

/* Buttons */
.btn{
	display:inline-block;
	padding:.6em 1.4em;
	font-size:1.05rem;
	border-radius:999px;
	font-weight:600;
	cursor:pointer;
	text-decoration:none;
	transition: filter .12s ease, transform .02s ease, background .12s ease, color .12s ease, border-color .12s ease;
}

/* Ghost (註冊) */
.ghost{
	background:transparent;
	color:#eaeaea;
	border:1px solid #555;
}
.ghost:hover{ filter:brightness(1.05); border-color:#6aa9c8; }

/* Primary (登入) */
.primary{
	background:#55c0df;
	border:1px solid #4aaece;
	color:#0e0e0e;
}
.primary:hover{ filter:brightness(1.05); }
.btn:active{ transform: translateY(1px); }
</style>
