<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center p-4" @click.self="$emit('close')">
    <div class="absolute inset-0 bg-black/60 backdrop-blur-sm"></div>

    <div class="relative glass-card !p-6 w-full max-w-lg max-h-[85vh] overflow-y-auto animate-fade-in-up">
      <button @click="$emit('close')" class="absolute top-4 right-4 text-gray-400 hover:text-white text-xl z-10">&times;</button>

      <div v-if="info" class="space-y-5">
        <!-- 封面大图 -->
        <div v-if="info.thumbnail" class="relative rounded-xl overflow-hidden">
          <img :src="info.thumbnail" alt="" class="w-full h-48 object-cover" referrerpolicy="no-referrer" />
          <!-- 时长标签 -->
          <span v-if="info.duration"
                class="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
            {{ formatDuration(info.duration) }}
          </span>
          <!-- 平台标签 -->
          <span class="absolute top-2 left-2 bg-purple-primary/80 text-white text-xs px-2 py-1 rounded-full">
            {{ info.platform }}
          </span>
        </div>

        <!-- 标题 -->
        <h3 class="text-white font-semibold text-lg leading-snug">{{ info.title }}</h3>

        <!-- UP主信息 -->
        <div class="flex items-center gap-3">
          <img v-if="info.uploader_avatar" :src="info.uploader_avatar"
               class="w-8 h-8 rounded-full border border-white/10" referrerpolicy="no-referrer" />
          <div>
            <p class="text-white text-sm font-medium">{{ info.uploader }}</p>
            <p v-if="info.description" class="text-gray-500 text-xs line-clamp-1 mt-0.5">{{ info.description }}</p>
          </div>
        </div>

        <!-- 数据统计 -->
        <div v-if="info.view_count !== undefined" class="flex flex-wrap gap-3">
          <span v-if="info.view_count" class="flex items-center gap-1 text-xs text-gray-400">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
            {{ formatCount(info.view_count) }}
          </span>
          <span v-if="info.like_count" class="flex items-center gap-1 text-xs text-gray-400">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/></svg>
            {{ formatCount(info.like_count) }}
          </span>
          <span v-if="info.coin_count" class="flex items-center gap-1 text-xs text-gray-400">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><text x="12" y="16" text-anchor="middle" font-size="10" fill="currentColor">$</text></svg>
            {{ formatCount(info.coin_count) }}
          </span>
          <span v-if="info.danmaku_count" class="flex items-center gap-1 text-xs text-gray-400">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
            {{ formatCount(info.danmaku_count) }}
          </span>
        </div>

        <!-- 视频详情（可展开） -->
        <div v-if="info.description" class="glass-card !p-3 !bg-white/3">
          <p class="text-gray-400 text-xs leading-relaxed"
             :class="{ 'line-clamp-2': !showDesc }">{{ info.description }}</p>
          <button v-if="info.description.length > 60" @click="showDesc = !showDesc"
                  class="text-purple-primary text-xs mt-1 hover:underline">
            {{ showDesc ? '收起' : '展开详情' }}
          </button>
        </div>

        <!-- 画质选择 -->
        <div>
          <h4 class="text-sm font-medium text-gray-300 mb-3">选择画质</h4>
          <div class="space-y-2 max-h-48 overflow-y-auto">
            <button
              v-for="f in filteredFormats"
              :key="f.format_id"
              @click="selectedFormat = f"
              class="w-full flex items-center justify-between px-4 py-3 rounded-xl transition-all text-sm"
              :class="selectedFormat?.format_id === f.format_id
                ? 'bg-purple-primary/20 border border-purple-primary/50 text-white'
                : 'bg-white/3 border border-white/5 text-gray-300 hover:bg-white/5'"
            >
              <div class="flex items-center gap-3">
                <span class="font-medium">{{ f.quality }}</span>
                <span class="text-gray-500">.{{ f.ext }}</span>
                <span v-if="!f.has_audio && f.has_video" class="text-xs px-2 py-0.5 rounded bg-green-500/20 text-green-400">视频+音频</span>
              </div>
              <span v-if="f.filesize" class="text-gray-500 text-xs">{{ formatSize(f.filesize) }}</span>
            </button>
          </div>
        </div>

        <!-- 下载按钮 -->
        <button
          @click="handleDownload"
          :disabled="!selectedFormat || downloading"
          class="gradient-btn w-full !py-3 text-center"
        >
          {{ downloading ? '下载中...' : '开始下载' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  visible: Boolean,
  info: Object,
  downloading: Boolean,
})

const emit = defineEmits(['close', 'download'])

const selectedFormat = ref(null)
const showDesc = ref(false)

const filteredFormats = computed(() => {
  if (!props.info?.formats) return []
  // 只显示视频格式（音频会自动合并）
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
