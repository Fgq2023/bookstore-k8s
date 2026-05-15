<script setup>
defineProps(['book'])
const emit = defineEmits(['add'])
</script>

<template>
  <div class="bg-white border border-slate-200 rounded-xl p-4 flex flex-col gap-2 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200">
    <h3 class="font-bold text-base leading-tight text-slate-800">{{ book.title }}</h3>
    <p class="text-sm text-slate-500">{{ book.author }}<br>ISBN: {{ book.isbn || '-' }}</p>
    <div class="mt-auto pt-2 flex items-center justify-between">
      <span class="text-lg font-extrabold text-blue-600">${{ Number(book.price || 0).toFixed(2) }}</span>
      <button
        @click="emit('add', book.id)"
        class="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-sm font-semibold px-3 py-2 rounded-lg transition-colors shadow-sm hover:shadow"
      >
        Add to Cart
      </button>
    </div>
  </div>
</template>
