<script setup>
import { ref, onMounted, inject } from 'vue'
import { useRouter } from 'vue-router'
import { get, post, put, del } from '../api/client'
import { store } from '../store'

const cart = ref({ items: [], total: 0 })
const loading = ref(false)
const toast = inject('toast')
const router = useRouter()

async function loadCart() {
  loading.value = true
  try {
    const data = await get('/cart')
    cart.value = data
    store.cartCount = data.items?.length || 0
  } catch (e) {
    toast?.(e.message || 'Error loading cart')
  } finally {
    loading.value = false
  }
}

async function updateQty(itemId, qty) {
  qty = parseInt(qty) || 1
  try {
    await put(`/cart/item/${itemId}`, { quantity: qty })
    await loadCart()
  } catch (e) {
    toast?.(e.message || 'Error updating quantity')
  }
}

async function removeItem(itemId) {
  try {
    await del(`/cart/item/${itemId}`)
    await loadCart()
    toast?.('Removed from cart')
  } catch (e) {
    toast?.(e.message || 'Error removing item')
  }
}

async function placeOrder() {
  try {
    const data = await post('/orders')
    toast?.(`Order placed! #${data.order_id}`)
    await loadCart()
    router.push('/orders')
  } catch (e) {
    toast?.(e.message || 'Error placing order')
  }
}

onMounted(loadCart)
</script>

<template>
  <div class="max-w-4xl mx-auto p-4">
    <h2 class="text-2xl font-bold mb-6 text-slate-800">Shopping Cart</h2>
    <div v-if="loading" class="text-center py-16">
      <div class="inline-block w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      <p class="mt-2 text-slate-400 text-sm">Loading cart...</p>
    </div>
    <div v-else-if="!cart.items?.length" class="text-center py-16 bg-white border border-slate-200 rounded-xl">
      <div class="text-4xl mb-2">🛒</div>
      <h3 class="text-lg font-semibold text-slate-700 mb-1">Your cart is empty</h3>
      <p class="text-slate-500 text-sm">Browse books and add some!</p>
      <router-link to="/" class="inline-block mt-4 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-xl font-semibold text-sm transition-colors">
        Browse Books
      </router-link>
    </div>
    <div v-else>
      <div class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
        <table class="w-full">
          <thead>
            <tr class="bg-slate-50 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <th class="px-4 py-3">Book</th>
              <th class="px-4 py-3">Price</th>
              <th class="px-4 py-3">Qty</th>
              <th class="px-4 py-3">Subtotal</th>
              <th class="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in cart.items" :key="item.id" class="border-t border-slate-100 hover:bg-slate-50 transition-colors">
              <td class="px-4 py-3">
                <div class="font-semibold text-sm text-slate-800">{{ item.title }}</div>
                <div class="text-xs text-slate-500">{{ item.author }}</div>
              </td>
              <td class="px-4 py-3 text-sm text-slate-700">${{ Number(item.price).toFixed(2) }}</td>
              <td class="px-4 py-3">
                <input
                  type="number"
                  min="1"
                  :value="item.quantity"
                  @change="updateQty(item.id, $event.target.value)"
                  class="w-16 px-2 py-1 border border-slate-200 rounded-lg text-center text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-100 outline-none"
                />
              </td>
              <td class="px-4 py-3 text-sm font-medium text-slate-700">${{ (item.price * item.quantity).toFixed(2) }}</td>
              <td class="px-4 py-3">
                <button
                  @click="removeItem(item.id)"
                  class="bg-red-500 hover:bg-red-600 active:bg-red-700 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors"
                >
                  Remove
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="mt-4 bg-white border border-slate-200 rounded-xl p-4 flex items-center justify-between shadow-sm">
        <span class="text-xl font-extrabold text-slate-800">Total: ${{ Number(cart.total || 0).toFixed(2) }}</span>
        <button
          @click="placeOrder"
          class="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white px-6 py-2.5 rounded-xl font-semibold transition-colors shadow-sm"
        >
          Place Order
        </button>
      </div>
    </div>
  </div>
</template>
