<template>
  <section class="py-20 px-4">
    <div class="max-w-4xl mx-auto">
      <h2 class="text-2xl font-bold mb-6">下载历史</h2>
      <div v-if="records.length === 0" class="glass-card !p-10 text-center text-gray-400">
        暂无下载记录
      </div>
      <div v-else class="space-y-3">
        <div v-for="r in records" :key="r.id" class="glass-card !p-4 flex items-center gap-4">
          <img v-if="r.thumbnail" :src="r.thumbnail" class="w-20 h-12 object-cover rounded-lg flex-shrink-0" referrerpolicy="no-referrer" />
          <div class="flex-1 min-w-0">
            <p class="text-white text-sm font-medium truncate">{{ r.title || r.url }}</p>
            <p class="text-gray-500 text-xs mt-1">{{ r.platform }} · {{ r.quality }} · {{ formatDate(r.created_at) }}</p>
          </div>
          <span class="text-xs px-2 py-1 rounded-full"
                :class="statusClass(r.status)">{{ r.status }}</span>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({ records: Array })

function statusClass(status) {
  const map = {
    completed: 'bg-green-500/20 text-green-400',
    downloading: 'bg-blue-500/20 text-blue-400',
    failed: 'bg-red-500/20 text-red-400',
    pending: 'bg-gray-500/20 text-gray-400',
  }
  return map[status] || map.pending
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>
