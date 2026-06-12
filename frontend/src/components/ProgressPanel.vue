<template>
  <div v-if="visible" class="glass-card !p-5 w-full max-w-md animate-fade-in-up">
    <div class="flex items-center justify-between mb-3">
      <h4 class="text-white font-medium text-sm">
        {{ status === 'completed' ? '下载完成' : status === 'failed' ? '下载失败' : '正在下载...' }}
      </h4>
      <span class="text-gray-400 text-xs">{{ eta ? `剩余 ${eta}` : '' }}</span>
    </div>

    <!-- 进度条 -->
    <div class="h-2 rounded-full bg-white/10 overflow-hidden mb-2">
      <div
        class="h-full rounded-full transition-all duration-300"
        :class="status === 'completed' ? 'bg-green-500' : 'progress-bar-animated'"
        :style="{ width: progress + '%' }"
      ></div>
    </div>

    <div class="flex items-center justify-between text-xs text-gray-400">
      <span>{{ progress.toFixed(1) }}%</span>
      <span>{{ speed }}</span>
    </div>

    <!-- 错误信息 -->
    <p v-if="error" class="text-red-400 text-sm mt-2">{{ error }}</p>

    <!-- 下载完成按钮 -->
    <button
      v-if="status === 'completed'"
      @click="$emit('downloadFile')"
      class="gradient-btn w-full !py-2.5 mt-3 text-sm"
    >
      保存文件
    </button>
  </div>
</template>

<script setup>
defineProps({
  visible: Boolean,
  progress: Number,
  speed: String,
  eta: String,
  status: String,
  error: String,
})

defineEmits(['downloadFile'])
</script>
