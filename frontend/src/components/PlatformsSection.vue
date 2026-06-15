<template>
  <section class="py-16 px-4 overflow-hidden">
    <h2 class="text-2xl font-bold text-center mb-3">
      支持 <span class="gradient-text">主流</span> 视频平台
    </h2>
    <p class="text-gray-500 text-center text-sm mb-8">基于 yt-dlp（14万+ Star），持续更新平台支持</p>

    <!-- 平台状态网格 -->
    <div class="max-w-4xl mx-auto grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 mb-8">
      <div v-for="p in platforms" :key="p.name"
           class="bg-white border border-gray-200 rounded-xl !p-3 flex items-center gap-2.5">
        <span class="w-2 h-2 rounded-full flex-shrink-0"
              :class="statusColor(p.status)"></span>
        <div class="min-w-0">
          <p class="text-gray-800 text-sm font-medium truncate">{{ p.name }}</p>
          <p class="text-gray-500 text-xs truncate">{{ p.note }}</p>
        </div>
      </div>
    </div>

    <!-- 图例 -->
    <div class="flex justify-center gap-6 text-xs text-gray-400">
      <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-green-400"></span>可直接使用</span>
      <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-yellow-400"></span>需要 Cookies</span>
      <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-orange-400"></span>CDN 限速</span>
      <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-red-400"></span>暂不支持</span>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const platforms = ref([])

onMounted(async () => {
  try {
    const res = await api.getPlatforms()
    platforms.value = res.data || []
  } catch {
    // 回退到静态数据
    platforms.value = [
      { name: 'B站', status: 'ok', note: '自定义API处理器' },
      { name: '优酷', status: 'ok', note: 'yt-dlp直接支持' },
      { name: '抖音', status: 'ok', note: '大部分视频可用' },
      { name: 'AcFun', status: 'ok', note: 'yt-dlp直接支持' },
      { name: '芒果TV', status: 'ok', note: 'yt-dlp直接支持' },
      { name: '西瓜视频', status: 'cookies', note: '需要上传cookies' },
      { name: '爱奇艺', status: 'broken', note: 'yt-dlp extractor已过时' },
      { name: '腾讯视频', status: 'drm', note: 'DRM版权保护' },
    ]
  }
})

function statusColor(status) {
  const map = {
    ok: 'bg-green-400',
    cookies: 'bg-yellow-400',
    throttled: 'bg-orange-400',
    broken: 'bg-red-400',
    drm: 'bg-red-400',
    noext: 'bg-red-400',
  }
  return map[status] || 'bg-gray-400'
}
</script>
