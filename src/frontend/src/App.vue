<script setup>
import { ref, provide } from 'vue'
import Navbar from './components/Navbar.vue'
import Toast from './components/Toast.vue'

const toastRef = ref(null)
provide('toast', (msg) => toastRef.value?.show(msg))
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <Navbar />
    <main class="pt-2 pb-10">
      <router-view />
    </main>
    <Toast ref="toastRef" />
  </div>
</template>
