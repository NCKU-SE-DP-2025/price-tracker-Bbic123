import { createWebHistory, createRouter } from 'vue-router'

// 📦 Lazy load（動態載入）頁面元件
const PriceOverview = () => import('../pages/PriceOverview.vue')
const PriceTrending = () => import('../pages/PriceTrending.vue')
const NewsList      = () => import('../pages/NewsList.vue')
const UserLogin     = () => import('../pages/UserLogin.vue')
const UserRegister  = () => import('../pages/UserRegister.vue')

const routes = [
	{ path: '/', redirect: '/overview' },
	{ path: '/overview', name: 'PriceOverview', component: PriceOverview },

	// ✅ 改成 /trends（請確保 NavBar 與其他 RouterLink 也用 /trends）
	{ path: '/trends', name: 'PriceTrending', component: PriceTrending },

	{ path: '/news', name: 'NewsList', component: NewsList },
	{ path: '/login', name: 'UserLogin', component: UserLogin },
	{ path: '/register', name: 'UserRegister', component: UserRegister },

	// 兜底：未知路徑導回 overview
	{ path: '/:pathMatch(.*)*', redirect: '/overview' }
]

const router = createRouter({
	history: createWebHistory(),
	routes,
	scrollBehavior() {
		// 切頁時捲到頂，避免上一頁的捲動位置殘留
		return { top: 0 }
	}
})

export default router
