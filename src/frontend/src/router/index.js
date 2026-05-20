import { createRouter, createWebHistory } from 'vue-router'
import BookList from '../components/BookList.vue'
import CartView from '../components/CartView.vue'
import OrdersView from '../components/OrdersView.vue'
import LoginView from '../components/LoginView.vue'
import RegisterView from '../components/RegisterView.vue'
import ProfileView from '../components/ProfileView.vue'
import AdminView from '../components/AdminView.vue'

const routes = [
  { path: '/', name: 'books', component: BookList },
  { path: '/cart', name: 'cart', component: CartView },
  { path: '/orders', name: 'orders', component: OrdersView },
  { path: '/login', name: 'login', component: LoginView, meta: { guestOnly: true } },
  { path: '/register', name: 'register', component: RegisterView, meta: { guestOnly: true } },
  { path: '/profile', name: 'profile', component: ProfileView, meta: { requiresAuth: true } },
  { path: '/admin', name: 'admin', component: AdminView, meta: { requiresAuth: true, requiresAdmin: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

import { isAdmin } from '../api/client'

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('bookstore_token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.meta.guestOnly && token) {
    next('/')
  } else if (to.meta.requiresAdmin && !isAdmin()) {
    next('/')
  } else {
    next()
  }
})

export default router
