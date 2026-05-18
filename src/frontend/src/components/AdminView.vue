<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { get, isLoggedIn } from '../api/client'

const router = useRouter()
const metrics = ref(null)
const loading = ref(true)
const error = ref('')

async function loadMetrics() {
  if (!isLoggedIn()) {
    router.push('/login')
    return
  }
  loading.value = true
  try {
    // Check if admin via /auth/me
    const me = await get('/auth/me')
    if (!me.success || !me.data.is_admin) {
      error.value = 'Access denied: Admin only'
      loading.value = false
      return
    }
    const data = await fetch('/metrics')
    const text = await data.text()
    metrics.value = text
  } catch (e) {
    error.value = 'Failed to load metrics'
  } finally {
    loading.value = false
  }
}

onMounted(loadMetrics)
</script>

<template>
  <div class="max-w-4xl mx-auto p-4">
    <h1 class="text-2xl font-bold text-slate-800 mb-4">Admin Dashboard</h1>
    <div v-if="loading" class="text-center py-16">
      <div class="inline-block w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
    </div>
    <div v-else-if="error" class="bg-red-50 text-red-600 px-4 py-3 rounded-xl">
      {{ error }}
    </div>
    <div v-else class="bg-slate-900 text-slate-200 rounded-2xl p-6 overflow-x-auto">
      <pre class="text-xs leading-relaxed font-mono">{{ metrics }}</pre>
    </div>
  </div>
</template>
