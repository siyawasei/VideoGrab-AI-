<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-end md:items-center justify-center p-0 md:p-4" @click.self="$emit('close')">
    <div class="absolute inset-0 bg-black/40 backdrop-blur-sm"></div>

    <div class="relative bg-white w-full max-w-5xl h-[95vh] md:h-auto md:max-h-[90vh] overflow-hidden animate-fade-in-up md:rounded-2xl rounded-t-2xl rounded-b-none shadow-2xl border border-gray-200">
      <!-- 关闭按钮 -->
      <button @click="$emit('close')" class="absolute top-3 right-3 text-gray-400 hover:text-gray-800 text-xl z-20">&times;</button>

      <div v-if="info" class="flex flex-col md:flex-row h-full">
        <!-- ========== 左栏：视频信息 + 下载 ========== -->
        <div class="md:w-[40%] p-4 md:p-5 space-y-3 md:space-y-4 md:border-r border-gray-100 overflow-y-auto shrink-0 md:h-auto">
          <!-- 封面 -->
          <div v-if="info.thumbnail" class="relative rounded-xl overflow-hidden">
            <img :src="info.thumbnail" alt="" class="w-full h-40 object-cover" referrerpolicy="no-referrer" />
            <span v-if="info.duration" class="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
              {{ formatDuration(info.duration) }}
            </span>
            <span class="absolute top-2 left-2 bg-blue-600 text-white text-xs px-2 py-1 rounded-full">
              {{ info.platform }}
            </span>
          </div>

          <!-- 标题 -->
          <h3 class="text-gray-900 font-semibold text-sm md:text-base leading-snug line-clamp-2">{{ info.title }}</h3>

          <!-- UP主 -->
          <div class="flex items-center gap-2.5">
            <img v-if="info.uploader_avatar" :src="info.uploader_avatar"
                 class="w-6 h-6 md:w-7 md:h-7 rounded-full border border-gray-200" referrerpolicy="no-referrer" />
            <p class="text-gray-700 text-xs md:text-sm font-medium truncate">{{ info.uploader }}</p>
          </div>

          <!-- 数据统计 -->
          <div v-if="info.view_count !== undefined" class="flex flex-wrap gap-2">
            <span v-if="info.view_count" class="flex items-center gap-1 text-[11px] text-gray-400">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
              {{ formatCount(info.view_count) }}
            </span>
            <span v-if="info.like_count" class="flex items-center gap-1 text-[11px] text-gray-400">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/></svg>
              {{ formatCount(info.like_count) }}
            </span>
            <span v-if="info.coin_count" class="flex items-center gap-1 text-[11px] text-gray-400">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><text x="12" y="16" text-anchor="middle" font-size="10" fill="currentColor">$</text></svg>
              {{ formatCount(info.coin_count) }}
            </span>
            <span v-if="info.danmaku_count" class="flex items-center gap-1 text-[11px] text-gray-400">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
              {{ formatCount(info.danmaku_count) }}
            </span>
          </div>

          <!-- 画质选择 -->
          <div>
            <h4 class="text-xs font-medium text-gray-500 mb-2">选择画质</h4>
            <div class="space-y-1.5 max-h-28 md:max-h-36 overflow-y-auto">
              <button
                v-for="f in filteredFormats"
                :key="f.format_id"
                @click="selectedFormat = f"
                class="w-full flex items-center justify-between px-3 py-2 rounded-lg transition-all text-sm"
                :class="selectedFormat?.format_id === f.format_id
                  ? 'bg-blue-50 border border-blue-300 text-blue-700'
                  : 'bg-gray-50 border border-gray-200 text-gray-600 hover:bg-gray-100'"
              >
                <div class="flex items-center gap-2">
                  <span class="font-medium text-xs">{{ f.quality }}</span>
                  <span class="text-gray-400 text-xs">.{{ f.ext }}</span>
                  <span v-if="!f.has_audio && f.has_video" class="text-[10px] px-1.5 py-0.5 rounded bg-green-50 text-green-600 border border-green-200">合并</span>
                </div>
                <span v-if="f.filesize" class="text-gray-400 text-xs">{{ formatSize(f.filesize) }}</span>
              </button>
            </div>
          </div>

          <!-- 下载按钮 -->
          <button
            @click="handleDownload"
            :disabled="!selectedFormat || downloading"
            class="gradient-btn w-full !py-2.5 text-center text-sm"
          >
            {{ downloading ? '下载中...' : '开始下载' }}
          </button>
        </div>

        <!-- ========== 右栏：AI 智能总结 ========== -->
        <div class="md:w-[60%] p-4 md:p-5 overflow-y-auto flex-1 min-h-0 bg-gray-50">
          <VideoSummary v-if="props.url" :url="props.url" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import VideoSummary from './VideoSummary.vue'

const props = defineProps({
  visible: Boolean,
  info: Object,
  downloading: Boolean,
  url: { type: String, default: '' },
})

const emit = defineEmits(['close', 'download'])

const selectedFormat = ref(null)

const filteredFormats = computed(() => {
  if (!props.info?.formats) return []
  return props.info.formats.filter(f => f.has_video)
})

function handleDownload() {
  if (selectedFormat.value) {
    emit('download', selectedFormat.value)
  }
}

function formatDuration(seconds) {
  if (!seconds) return ''
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function formatSize(bytes) {
  if (!bytes) return ''
  if (bytes > 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024 / 1024).toFixed(1)} GB`
  if (bytes > 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  return `${(bytes / 1024).toFixed(1)} KB`
}

function formatCount(n) {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return n.toString()
}
</script>
