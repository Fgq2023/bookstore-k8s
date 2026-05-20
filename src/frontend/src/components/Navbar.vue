<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { store } from '../store'
import { isLoggedIn, clearToken, isAdmin } from '../api/client'

const route = useRoute()
const router = useRouter()
const current = computed(() => route.name)
const loggedIn = ref(isLoggedIn())
const isAdminUser = ref(isAdmin())

function updateAuth() {
  loggedIn.value = isLoggedIn()
  isAdminUser.value = isAdmin()
}

function logout() {
  clearToken()
  router.push('/login')
}

onMounted(() => {
  window.addEventListener('auth-changed', updateAuth)
})
onUnmounted(() => {
  window.removeEventListener('auth-changed', updateAuth)
})
</script>

<template>
  <header class="bg-white border-b border-slate-200 sticky top-0 z-10 shadow-sm">
    <nav class="max-w-6xl mx-auto flex items-center justify-between h-14 px-4">
      <router-link to="/" class="text-xl font-bold text-blue-600 tracking-tight hover:opacity-80 transition-opacity">
        📚 Cloud Bookstore
      </router-link>
      <div class="flex gap-1 items-center">
        <router-link
          to="/"
          class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="current === 'books' ? 'bg-blue-50 text-blue-600' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'"
        >
          📖 Books
        </router-link>
        <router-link
          to="/cart"
          class="px-3 py-2 rounded-lg text-sm font-medium transition-colors relative"
          :class="current === 'cart' ? 'bg-blue-50 text-blue-600' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'"
        >
          🛒 Cart
          <span
            v-if="store.cartCount > 0"
            class="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[18px] text-center"
          >
            {{ store.cartCount }}
          </span>
        </router-link>
        <router-link
          to="/orders"
          class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="current === 'orders' ? 'bg-blue-50 text-blue-600' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'"
        >
          📦 Orders
        </router-link>

        <div v-if="loggedIn" class="flex items-center gap-1 ml-2 pl-2 border-l border-slate-200">
          <router-link
            v-if="isAdminUser"
            to="/admin"
            class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="current === 'admin' ? 'bg-purple-50 text-purple-600' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'"
          >
            ⚙️ Admin
          </router-link>
          <router-link
            to="/profile"
            class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="current === 'profile' ? 'bg-blue-50 text-blue-600' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'"
          >
            👤 Profile
          </router-link>
          <button
            @click="logout"
            class="px-3 py-2 rounded-lg text-sm font-medium text-slate-500 hover:bg-slate-50 hover:text-red-600 transition-colors"
          >
            Logout
          </button>
        </div>
        <div v-else class="flex items-center gap-1 ml-2 pl-2 border-l border-slate-200">
          <router-link
            to="/login"
            class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="current === 'login' ? 'bg-blue-50 text-blue-600' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'"
          >
            Sign In
          </router-link>
          <router-link
            to="/register"
            class="px-3 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
          >
            Sign Up
          </router-link>
        </div>
      </div>
    </nav>
  </header>
</template>
