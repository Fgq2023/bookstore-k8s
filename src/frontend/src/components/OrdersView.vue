<script setup>
import { ref, onMounted, inject } from 'vue'
import { get } from '../api/client'

const orders = ref([])
const loading = ref(false)
const selectedOrder = ref(null)
const toast = inject('toast')

async function loadOrders() {
  loading.value = true
  selectedOrder.value = null
  try {
    const data = await get('/orders')
    orders.value = data.orders || []
  } catch (e) {
    toast?.(e.message || 'Error loading orders')
  } finally {
    loading.value = false
  }
}

function statusClass(status) {
  return {
    'confirmed': 'bg-emerald-100 text-emerald-700',
    'pending': 'bg-amber-100 text-amber-700',
    'shipped': 'bg-blue-100 text-blue-700',
    'delivered': 'bg-violet-100 text-violet-700',
    'cancelled': 'bg-red-100 text-red-700',
  }[status] || 'bg-slate-100 text-slate-600'
}

async function showDetail(orderId) {
  try {
    const data = await get(`/orders/${orderId}`)
    selectedOrder.value = data
  } catch (e) {
    toast?.(e.message || 'Error loading order detail')
  }
}

function backToList() {
  selectedOrder.value = null
}

onMounted(loadOrders)
</script>

<template>
  <div class="max-w-4xl mx-auto p-4">
    <h2 class="text-2xl font-bold mb-6 text-slate-800">My Orders</h2>
    <div v-if="loading" class="text-center py-16">
      <div class="inline-block w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      <p class="mt-2 text-slate-400 text-sm">Loading orders...</p>
    </div>
    <div v-else-if="!orders.length" class="text-center py-16 bg-white border border-slate-200 rounded-xl">
      <div class="text-4xl mb-2">📦</div>
      <h3 class="text-lg font-semibold text-slate-700 mb-1">No orders yet</h3>
      <p class="text-slate-500 text-sm">Place your first order from the cart!</p>
      <router-link to="/cart" class="inline-block mt-4 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-xl font-semibold text-sm transition-colors">
        Go to Cart
      </router-link>
    </div>
    <div v-else-if="selectedOrder" class="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-bold text-slate-800">Order #{{ selectedOrder.id }}</h3>
        <span
          class="text-xs font-bold px-2.5 py-1 rounded-full uppercase tracking-wide"
          :class="statusClass(selectedOrder.status)"
        >
          {{ selectedOrder.status }}
        </span>
      </div>
      <div class="text-sm text-slate-500 mb-4">
        {{ new Date(selectedOrder.created_at).toLocaleString() }}
      </div>
      <ul class="space-y-2 mb-4 divide-y divide-slate-100">
        <li v-for="item in selectedOrder.items" :key="item.book_id" class="py-2 text-sm text-slate-700 flex justify-between">
          <span>{{ item.title }} <span class="text-slate-400">x{{ item.quantity }}</span></span>
          <span class="font-medium">${{ (item.price * item.quantity).toFixed(2) }}</span>
        </li>
      </ul>
      <div class="flex items-center justify-between pt-4 border-t border-slate-100">
        <span class="text-lg font-extrabold text-slate-800">Total: ${{ Number(selectedOrder.total_amount || 0).toFixed(2) }}</span>
        <button
          @click="backToList"
          class="bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 px-4 py-2 rounded-xl font-semibold text-sm transition-colors"
        >
          Back
        </button>
      </div>
    </div>
    <div v-else class="space-y-3">
      <div
        v-for="order in orders"
        :key="order.id"
        @click="showDetail(order.id)"
        class="bg-white border border-slate-200 rounded-xl p-4 cursor-pointer hover:border-blue-300 hover:shadow-sm transition-all"
      >
        <div class="flex items-center justify-between mb-1">
          <div class="flex items-center gap-2">
            <span class="font-semibold text-slate-800">Order #{{ order.id }}</span>
            <span
              class="text-xs font-bold px-2 py-0.5 rounded-full uppercase tracking-wide"
              :class="statusClass(order.status)"
            >
              {{ order.status }}
            </span>
          </div>
          <span class="text-lg font-extrabold text-blue-600">${{ Number(order.total_amount || 0).toFixed(2) }}</span>
        </div>
        <div class="text-sm text-slate-500">{{ new Date(order.created_at).toLocaleString() }}</div>
      </div>
    </div>
  </div>
</template>
