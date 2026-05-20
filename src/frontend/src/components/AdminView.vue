<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { get, post, put, del, isLoggedIn, isAdmin } from '../api/client'

const router = useRouter()
const activeTab = ref('books')
const loading = ref(true)
const error = ref('')
const books = ref([])
const metrics = ref(null)

// Book form state
const showForm = ref(false)
const editingBook = ref(null)
const form = reactive({
  title: '',
  author: '',
  isbn: '',
  price: '',
  stock_quantity: 0
})
const formError = ref('')
const formLoading = ref(false)

async function loadBooks() {
  try {
    const res = await get('/admin/books')
    if (res.success) {
      books.value = res.data.books
    } else {
      error.value = res.error?.message || 'Failed to load books'
    }
  } catch (e) {
    error.value = 'Failed to load books'
  }
}

async function loadMetrics() {
  try {
    const data = await fetch('/metrics')
    metrics.value = await data.text()
  } catch (e) {
    // metrics might not be available
  }
}

async function init() {
  if (!isLoggedIn()) {
    router.push('/login')
    return
  }
  if (!isAdmin()) {
    error.value = 'Access denied: Admin only'
    loading.value = false
    return
  }
  loading.value = true
  await Promise.all([loadBooks(), loadMetrics()])
  loading.value = false
}

function resetForm() {
  form.title = ''
  form.author = ''
  form.isbn = ''
  form.price = ''
  form.stock_quantity = 0
  formError.value = ''
  editingBook.value = null
}

function openCreateForm() {
  resetForm()
  showForm.value = true
}

function openEditForm(book) {
  editingBook.value = book
  form.title = book.title
  form.author = book.author
  form.isbn = book.isbn
  form.price = book.price
  form.stock_quantity = book.stock_quantity
  formError.value = ''
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  resetForm()
}

async function submitForm() {
  formLoading.value = true
  formError.value = ''
  try {
    const payload = {
      title: form.title,
      author: form.author,
      isbn: form.isbn,
      price: parseFloat(form.price),
      stock_quantity: parseInt(form.stock_quantity) || 0
    }
    let res
    if (editingBook.value) {
      // Only send changed fields
      const updatePayload = {}
      if (payload.title !== editingBook.value.title) updatePayload.title = payload.title
      if (payload.author !== editingBook.value.author) updatePayload.author = payload.author
      if (payload.isbn !== editingBook.value.isbn) updatePayload.isbn = payload.isbn
      if (payload.price !== editingBook.value.price) updatePayload.price = payload.price
      if (payload.stock_quantity !== editingBook.value.stock_quantity) updatePayload.stock_quantity = payload.stock_quantity
      
      if (Object.keys(updatePayload).length === 0) {
        closeForm()
        formLoading.value = false
        return
      }
      res = await put(`/admin/books/${editingBook.value.id}`, updatePayload)
    } else {
      res = await post('/admin/books', payload)
    }
    if (res.success) {
      closeForm()
      await loadBooks()
    } else {
      formError.value = res.error?.message || 'Operation failed'
    }
  } catch (e) {
    formError.value = e.response?.data?.error?.message || 'Network error'
  } finally {
    formLoading.value = false
  }
}

async function deleteBook(book) {
  if (!confirm(`Are you sure you want to delete "${book.title}"?`)) {
    return
  }
  try {
    const res = await del(`/admin/books/${book.id}`)
    if (res.success) {
      await loadBooks()
    } else {
      alert(res.error?.message || 'Delete failed')
    }
  } catch (e) {
    alert('Delete failed')
  }
}

onMounted(init)
</script>

<template>
  <div class="max-w-6xl mx-auto p-4">
    <h1 class="text-2xl font-bold text-slate-800 mb-6">Admin Dashboard</h1>
    
    <!-- Loading -->
    <div v-if="loading" class="text-center py-16">
      <div class="inline-block w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
    </div>
    
    <!-- Error -->
    <div v-else-if="error" class="bg-red-50 text-red-600 px-4 py-3 rounded-xl mb-4">
      {{ error }}
    </div>
    
    <!-- Tabs -->
    <div v-else class="mb-6">
      <div class="flex gap-2 border-b border-slate-200 mb-6">
        <button
          @click="activeTab = 'books'"
          :class="activeTab === 'books' ? 'border-b-2 border-blue-600 text-blue-600 font-medium' : 'text-slate-500 hover:text-slate-700'"
          class="px-4 py-2 transition-colors"
        >
          Book Management
        </button>
        <button
          @click="activeTab = 'metrics'"
          :class="activeTab === 'metrics' ? 'border-b-2 border-blue-600 text-blue-600 font-medium' : 'text-slate-500 hover:text-slate-700'"
          class="px-4 py-2 transition-colors"
        >
          Metrics
        </button>
      </div>
      
      <!-- Book Management Tab -->
      <div v-if="activeTab === 'books'">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-lg font-semibold text-slate-700">Books ({{ books.length }})</h2>
          <button
            @click="openCreateForm"
            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
            Add Book
          </button>
        </div>
        
        <!-- Book Form Modal -->
        <div v-if="showForm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6">
            <h3 class="text-xl font-bold text-slate-800 mb-4">
              {{ editingBook ? 'Edit Book' : 'Add New Book' }}
            </h3>
            
            <div v-if="formError" class="bg-red-50 text-red-600 px-4 py-2 rounded-lg mb-4 text-sm">
              {{ formError }}
            </div>
            
            <form @submit.prevent="submitForm" class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Title</label>
                <input
                  v-model="form.title"
                  type="text"
                  required
                  class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  placeholder="Book title"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Author</label>
                <input
                  v-model="form.author"
                  type="text"
                  required
                  class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  placeholder="Author name"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">ISBN</label>
                <input
                  v-model="form.isbn"
                  type="text"
                  required
                  class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  placeholder="978-0132350884"
                />
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Price ($)</label>
                  <input
                    v-model="form.price"
                    type="number"
                    step="0.01"
                    min="0.01"
                    required
                    class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    placeholder="29.99"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 mb-1">Stock</label>
                  <input
                    v-model="form.stock_quantity"
                    type="number"
                    min="0"
                    required
                    class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    placeholder="10"
                  />
                </div>
              </div>
              
              <div class="flex gap-3 pt-2">
                <button
                  type="button"
                  @click="closeForm"
                  class="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  :disabled="formLoading"
                  class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  {{ formLoading ? 'Saving...' : (editingBook ? 'Update' : 'Create') }}
                </button>
              </div>
            </form>
          </div>
        </div>
        
        <!-- Books Table -->
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full">
              <thead class="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">ID</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Title</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Author</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">ISBN</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Price</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Stock</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr v-for="book in books" :key="book.id" class="hover:bg-slate-50">
                  <td class="px-4 py-3 text-sm text-slate-600">{{ book.id }}</td>
                  <td class="px-4 py-3 text-sm font-medium text-slate-800">{{ book.title }}</td>
                  <td class="px-4 py-3 text-sm text-slate-600">{{ book.author }}</td>
                  <td class="px-4 py-3 text-sm text-slate-500 font-mono">{{ book.isbn }}</td>
                  <td class="px-4 py-3 text-sm text-slate-700">${{ book.price }}</td>
                  <td class="px-4 py-3">
                    <span
                      :class="book.stock_quantity > 5 ? 'bg-green-100 text-green-700' : book.stock_quantity > 0 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'"
                      class="inline-flex px-2 py-1 rounded-full text-xs font-medium"
                    >
                      {{ book.stock_quantity }}
                    </span>
                  </td>
                  <td class="px-4 py-3 text-right">
                    <div class="flex justify-end gap-2">
                      <button
                        @click="openEditForm(book)"
                        class="text-blue-600 hover:text-blue-800 p-1 rounded hover:bg-blue-50 transition-colors"
                        title="Edit"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                      </button>
                      <button
                        @click="deleteBook(book)"
                        class="text-red-600 hover:text-red-800 p-1 rounded hover:bg-red-50 transition-colors"
                        title="Delete"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="books.length === 0" class="text-center py-12 text-slate-400">
            No books found. Add your first book!
          </div>
        </div>
      </div>
      
      <!-- Metrics Tab -->
      <div v-else-if="activeTab === 'metrics'">
        <div v-if="metrics" class="bg-slate-900 text-slate-200 rounded-2xl p-6 overflow-x-auto">
          <pre class="text-xs leading-relaxed font-mono">{{ metrics }}</pre>
        </div>
        <div v-else class="text-center py-12 text-slate-400">
          Metrics not available. Ensure Prometheus is configured.
        </div>
      </div>
    </div>
  </div>
</template>
