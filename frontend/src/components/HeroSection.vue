<template>
  <section class="relative min-h-[80vh] flex flex-col items-center justify-center text-center px-4 pt-20 bg-grid overflow-hidden">
    <!-- 背景装饰 -->
    <div class="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full opacity-30"
         style="background: radial-gradient(circle, rgba(37,99,235,0.1) 0%, transparent 70%)"></div>

    <!-- 标题 -->
    <h1 class="text-4xl md:text-6xl font-bold mb-4 animate-fade-in-up relative z-10 text-gray-900">
      万能视频下载，<span class="gradient-text">一键搞定</span>
    </h1>
    <p class="text-gray-500 text-lg md:text-xl mb-10 max-w-2xl animate-fade-in-up relative z-10" style="animation-delay: 0.1s">
      支持 1800+ 平台，高清无损，手机电脑都能用
    </p>

    <!-- 输入框 -->
    <div class="w-full max-w-2xl animate-fade-in-up relative z-10" style="animation-delay: 0.2s">
      <div class="bg-white border border-gray-200 !p-2 flex items-center gap-2 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
        <input
          v-model="url"
          type="text"
          placeholder="粘贴视频链接... (YouTube, B站, 抖音, Twitter...)"
          class="flex-1 bg-transparent px-4 py-3 text-gray-800 outline-none placeholder-gray-400"
          @keyup.enter="handleParse"
        />
        <button
          @click="handleParse"
          :disabled="!url.trim() || loading"
          class="gradient-btn !py-3 !px-6 flex items-center gap-2 whitespace-nowrap"
        >
          <svg v-if="loading" class="animate-spin w-5 h-5" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/>
          </svg>
          <span>{{ loading ? '解析中...' : '解析视频' }}</span>
        </button>
      </div>
      <p v-if="error" class="text-red-500 text-sm mt-3">{{ error }}</p>
    </div>

    <!-- 支持的平台图标提示 -->
    <div class="mt-8 flex flex-wrap justify-center gap-3 text-gray-400 text-sm animate-fade-in-up relative z-10" style="animation-delay: 0.3s">
      <span v-for="p in platforms" :key="p" class="px-3 py-1 rounded-full border border-gray-200 bg-white text-gray-500">{{ p }}</span>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  loading: Boolean,
  error: String,
})

const emit = defineEmits(['parse'])

const url = ref('')
const platforms = ['YouTube', 'B站', '抖音', 'Twitter/X', 'Instagram', 'TikTok', 'Facebook', 'Vimeo']

function handleParse() {
  if (url.value.trim()) {
    emit('parse', url.value.trim())
  }
}
</script>
