<template>
  <section class="py-20 px-4">
    <div class="max-w-6xl mx-auto">
      <h2 class="text-3xl md:text-4xl font-bold text-center mb-4">
        为什么选择 <span class="gradient-text">VideoGrab</span>
      </h2>
      <p class="text-gray-400 text-center mb-12 max-w-xl mx-auto">一站式解决所有视频下载需求，简单、快速、安全</p>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div v-for="(f, i) in features" :key="i"
             class="glass-card !p-6 text-center animate-fade-in-up"
             :style="{ animationDelay: i * 0.1 + 's' }">
          <div class="text-4xl mb-4">{{ f.icon }}</div>
          <h3 class="text-white font-semibold text-lg mb-2">{{ f.title }}</h3>
          <p class="text-gray-400 text-sm leading-relaxed">{{ f.desc }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
const features = [
  { icon: '🌐', title: '全平台支持', desc: 'YouTube、B站、抖音、Twitter、Instagram 等 1800+ 平台，一个工具搞定' },
  { icon: '🎬', title: '高清画质', desc: '支持 4K/1080p/720p 多种画质自由选择，原画质无损下载' },
  { icon: '⚡', title: '极速下载', desc: '不限速、不卡顿，多线程并发下载，秒级响应' },
  { icon: '🔒', title: '安全隐私', desc: '不记录浏览历史，不留痕迹，隐私安全有保障' },
]
</script>
