<template>
	<div class="register-page">
		<h1>使用者註冊</h1>

		<div class="card">
			<form @submit.prevent="register">
				<input v-model="username" type="text" placeholder="Username" required />
				<p v-if="errors.username" class="error">{{ errors.username }}</p>

				<input v-model="password" type="password" placeholder="Password" required />
				<p v-if="errors.password" class="error">{{ errors.password }}</p>

				<input v-model="passwordConfirm" type="password" placeholder="Password confirm" required />
				<p v-if="errors.passwordConfirm" class="error">{{ errors.passwordConfirm }}</p>

				<div class="ops">
					<button type="submit" id="register">註冊</button>
				</div>
			</form>
		</div>
	</div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'

const username = ref('')
const password = ref('')
const passwordConfirm = ref('')

const errors = reactive({
	username: '',
	password: '',
	passwordConfirm: ''
})

const auth = useAuthStore()

function register() {
	if (!validate()) return
	auth.register(username.value, password.value)
}

function validate() {
	let ok = true
	errors.username = ''
	errors.password = ''
	errors.passwordConfirm = ''

	if (!username.value.trim()) {
		errors.username = 'Username is required.'
		ok = false
	}
	if (!password.value) {
		errors.password = 'Password is required.'
		ok = false
	}
	if (password.value !== passwordConfirm.value) {
		errors.passwordConfirm = 'Passwords do not match!'
		ok = false
	}
	return ok
}
</script>

<style scoped>
/* Page */
.register-page{
	padding: 3em 5em;
	background: #1e1e1e;
	min-height: calc(100vh - 4.5em);
	box-sizing: border-box;
	color: #eaeaea;
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
	gap: .5em;
}

form > input{
	color: #fff;
	background: #1f1f1f;
	border: 1px solid #3a3a3a;
	border-radius: 10px;
	padding: .75em 1em;
	font-size: 1.05rem;
	outline: none;
	transition: border-color .12s ease, background .12s ease;
}
form > input::placeholder{ color:#757575; }
form > input:focus{
	border-color: #6aa9c8;
	background: #222;
}

/* Error */
.error{ color:#ff6f6f; margin:.1em 0 .4em; font-size:.95rem; }

/* Actions */
.ops{
	margin-top: .75em;
	display: flex;
	justify-content: center;
}
#register{
	padding: .6em 1.4em;
	font-size: 1.05rem;
	border: 1px solid #4aaece;
	border-radius: 999px;
	background: #55c0df;
	color: #0e0e0e;
	font-weight: 600;
	cursor: pointer;
	transition: filter .12s ease, transform .02s ease;
}
#register:hover{ filter: brightness(1.05); }
#register:active{ transform: translateY(1px); }
</style>
