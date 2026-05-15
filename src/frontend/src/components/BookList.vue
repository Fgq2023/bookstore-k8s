<script setup>
import { ref, onMounted, inject } from 'vue'
import { get, post } from '../api/client'
import { store } from '../store'
import BookCard from './BookCard.vue'

const books = ref([])
const query = ref('')
const loading = ref(false)
const toast = inject('toast')

async function loadBooks() {
  loading.value = true
  query.value = ''
  try {
    const data = await get('/books')
    books.value = data.books || []
  } catch (e) {
    toast?.(e.message || 'Error loading books')
  } finally {
    loading.value = false
  }
}

async function searchBooks() {
  if (!query.value.trim()) {
    loadBooks()
    return
  }
  loading.value = true
  try {
    const data = await get('/books/search', { q: query.value.trim() })
    books.value = data.books || []
  } catch (e) {
    toast?.(e.message || 'Search error')
  } finally {
    loading.value = false
  }
}

async function addToCart(bookId) {
  try {
    await post('/cart', { book_id: bookId, quantity: 1 })
    store.cartCount += 1
    toast?.('Added to cart')
  } catch (e) {
    toast?.(e.message || 'Error adding to cart')
  }
}

onMounted(loadBooks)
</script>

<template>
  <div class="max-w-6xl mx-auto p-4">
    <div class="flex gap-3 mb-6 flex-wrap">
      <input
        v-model="query"
        @keyup.enter="searchBooks"
        placeholder="Search by title or author..."
        class="flex-1 min-w-[220px] px-4 py-2.5 border border-slate-200 rounded-xl text-base outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all bg-white"
      />
      <button
        @click="searchBooks"
        class="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white px-5 py-2.5 rounded-xl font-semibold text-sm transition-colors shadow-sm"
      >
        Search
      </button>
      <button
        @click="loadBooks"
        class="bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 px-5 py-2.5 rounded-xl font-semibold text-sm transition-colors"
      >
        Reset
      </button>
    </div>

    <div v-if="loading" class="text-center py-16">
      <div class="inline-block w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      <p class="mt-2 text-slate-400 text-sm">Loading books...</p>
    </div>
    <div v-else-if="!books.length" class="text-center py-16">
      <div class="text-4xl mb-2">📭</div>
      <h3 class="text-lg font-semibold text-slate-700 mb-1">No books found</h3>
      <p class="text-slate-500 text-sm">Try a different search term</p>
    </div>
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <BookCard v-for="book in books" :key="book.id" :book="book" @add="addToCart" />
    </div>
  </div>
</template>
