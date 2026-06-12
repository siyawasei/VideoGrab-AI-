<template>
  <div class="pt-24 min-h-screen">
    <HistorySection :records="records" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'
import HistorySection from '@/components/HistorySection.vue'

const records = ref([])

onMounted(async () => {
  try {
    const res = await api.getHistory()
    records.value = res.data || []
  } catch (e) {
    console.error('获取历史记录失败:', e)
  }
})
</script>
