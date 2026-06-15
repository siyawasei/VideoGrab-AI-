<template>
  <section class="py-16 px-4">
    <div class="max-w-5xl mx-auto">
      <h2 class="text-2xl md:text-3xl font-bold text-center mb-3 text-gray-900">
        如何下载视频？<span class="gradient-text">3 步搞定</span>
      </h2>
      <p class="text-gray-500 text-center mb-10 text-sm">无需安装软件，打开浏览器就能用</p>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div v-for="(step, i) in steps" :key="i" class="relative">
          <!-- 连接箭头（非最后一步） -->
          <div v-if="i < steps.length - 1" class="hidden md:block absolute top-12 -right-3 z-10">
            <svg class="w-6 h-6 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </div>

          <div class="bg-white border border-gray-200 rounded-xl p-6 text-center hover:shadow-md transition-all h-full">
            <!-- 步骤编号 -->
            <div class="w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center mx-auto mb-4 text-lg font-bold">
              {{ i + 1 }}
            </div>
            <div class="text-2xl mb-3">{{ step.icon }}</div>
            <h3 class="text-gray-800 font-semibold text-base mb-2">{{ step.title }}</h3>
            <p class="text-gray-500 text-sm leading-relaxed">{{ step.desc }}</p>
          </div>
        </div>
      </div>

      <!-- 支持的平台 -->
      <div class="mt-10 text-center">
        <p class="text-gray-400 text-xs mb-3">支持平台示例</p>
        <div class="flex flex-wrap justify-center gap-2">
          <span v-for="p in platforms" :key="p" class="px-3 py-1 rounded-full border border-gray-200 bg-white text-gray-500 text-xs">{{ p }}</span>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
const steps = [
  {
    icon: '📋',
    title: '复制链接',
    desc: '从任意视频网站（B站、YouTube、抖音等）复制视频链接，支持标准链接、短链、分享链接。',
  },
  {
    icon: '🔍',
    title: '粘贴解析',
    desc: '将链接粘贴到 VideoGrab 输入框，点击「解析视频」。系统自动识别平台，获取视频信息和可用画质。',
  },
  {
    icon: '⬇️',
    title: '选择下载',
    desc: '选择需要的画质（最高 8K），点击下载。音视频自动合并，实时显示进度，完成后保存到本地。',
  },
]

const platforms = ['B站', 'YouTube', '抖音', 'Twitter/X', 'Instagram', 'TikTok', '腾讯视频', '优酷', 'Facebook', 'Vimeo']
</script>
