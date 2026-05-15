<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { store } from '../store'

const route = useRoute()
const current = computed(() => route.name)
</script>

<template>
  <header class="bg-white border-b border-slate-200 sticky top-0 z-10 shadow-sm">
    <nav class="max-w-6xl mx-auto flex items-center justify-between h-14 px-4">
      <router-link to="/" class="text-xl font-bold text-blue-600 tracking-tight hover:opacity-80 transition-opacity">
        📚 Cloud Bookstore
      </router-link>
      <div class="flex gap-1">
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
      </div>
    </nav>
  </header>
</template>
