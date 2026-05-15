import { createRouter, createWebHistory } from 'vue-router'
import BookList from '../components/BookList.vue'
import CartView from '../components/CartView.vue'
import OrdersView from '../components/OrdersView.vue'

const routes = [
  { path: '/', name: 'books', component: BookList },
  { path: '/cart', name: 'cart', component: CartView },
  { path: '/orders', name: 'orders', component: OrdersView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
