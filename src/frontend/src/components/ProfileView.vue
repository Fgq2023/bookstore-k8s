<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { get, clearToken, isLoggedIn } from '../api/client'

const router = useRouter()
const user = ref(null)
const loading = ref(true)
const orders = ref([])

async function loadProfile() {
  if (!isLoggedIn()) {
    router.push('/login')
    return
  }
  loading.value = true
  try {
    const me = await get('/auth/me')
    if (me.success) {
      user.value = me.data
    }
    // Load orders via session (same as before)
    const ord = await get('/orders')
    orders.value = ord.orders || []
  } catch (e) {
    console.error('Failed to load profile', e)
  } finally {
    loading.value = false
  }
}

function logout() {
  clearToken()
  router.push('/login')
}

onMounted(loadProfile)
</script>

<template>
  <div class="max-w-3xl mx-auto p-4">
    <div v-if="loading" class="text-center py-16">
      <div class="inline-block w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
    </div>
    <div v-else-if="user" class="space-y-6">
      <!-- Profile Card -->
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center text-2xl text-blue-600 font-bold">
              {{ user.username[0].toUpperCase() }}
            </div>
            <div>
              <h1 class="text-xl font-bold text-slate-800">{{ user.username }}</h1>
              <p class="text-slate-500 text-sm">User ID: {{ user.user_id }}</p>
              <span v-if="user.is_admin" class="inline-block mt-1 bg-purple-100 text-purple-700 text-xs px-2 py-0.5 rounded-full font-medium">
                Admin
              </span>
            </div>
          </div>
          <button @click="logout"
            class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-xl font-medium text-sm transition-colors">
            Log Out
          </button>
        </div>
      </div>

      <!-- Orders Summary -->
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
        <h2 class="text-lg font-bold text-slate-800 mb-4">Your Orders</h2>
        <div v-if="!orders.length" class="text-center py-8 text-slate-400">
          <div class="text-3xl mb-2">📦</div>
          <p>No orders yet</p>
        </div>
        <div v-else class="space-y-3">
          <div v-for="order in orders.slice(0, 5)" :key="order.id"
            class="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
            <div>
              <p class="font-medium text-slate-800">Order #{{ order.id }}</p>
              <p class="text-xs text-slate-500">{{ new Date(order.created_at).toLocaleDateString() }}</p>
            </div>
            <div class="text-right">
              <p class="font-semibold text-slate-800">${{ order.total_amount }}</p>
              <span class="inline-block mt-1 text-xs px-2 py-0.5 rounded-full"
                :class="{
                  'bg-yellow-100 text-yellow-700': order.status === 'pending',
                  'bg-green-100 text-green-700': order.status === 'confirmed',
                  'bg-blue-100 text-blue-700': order.status === 'shipped',
                  'bg-slate-100 text-slate-600': order.status === 'delivered',
                  'bg-red-100 text-red-700': order.status === 'cancelled'
                }">
                {{ order.status }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
