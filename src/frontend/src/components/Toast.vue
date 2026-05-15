<script setup>
import { ref } from 'vue'

const message = ref('')
const visible = ref(false)
let timer = null

function show(msg) {
  message.value = msg
  visible.value = true
  clearTimeout(timer)
  timer = setTimeout(() => visible.value = false, 2500)
}

defineExpose({ show })
</script>

<template>
  <div
    class="fixed bottom-5 right-5 bg-slate-800 text-white px-4 py-3 rounded-xl shadow-lg transition-all duration-300 z-50"
    :class="visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'"
  >
    {{ message }}
  </div>
</template>
