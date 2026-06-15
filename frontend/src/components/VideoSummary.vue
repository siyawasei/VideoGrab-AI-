<template>
  <div class="video-summary">
    <!-- Tab 和内容（自动开始，无需手动点击） -->
    <div class="space-y-3">
      <!-- Tab 切换 -->
      <div class="flex gap-1 bg-gray-100 rounded-xl p-1">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="switchTab(tab.key)"
          class="flex-1 py-2 px-2 rounded-lg text-xs sm:text-sm font-medium transition-all whitespace-nowrap"
          :class="activeTab === tab.key
            ? 'bg-blue-600 text-white shadow-sm'
            : 'text-gray-500 hover:text-gray-800 hover:bg-white'"
        >
          {{ tab.icon }} {{ tab.label }}
        </button>
      </div>

      <!-- ========== Tab 1: 内容总结 ========== -->
      <div v-if="activeTab === 'summary'" class="space-y-2">
        <button
          v-if="summaryText"
          @click="collapsed.summary = !collapsed.summary"
          class="w-full flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors text-sm text-gray-600"
        >
          <span>📝 内容总结</span>
          <svg class="w-4 h-4 transition-transform" :class="{ '-rotate-180': !collapsed.summary }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        <div v-if="summaryState === 'loading'" class="flex items-center gap-3 py-8 justify-center">
          <div class="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <span class="text-gray-400 text-sm">正在分析视频内容...</span>
        </div>
        <div v-if="summaryText && !collapsed.summary">
          <div class="summary-markdown text-sm text-gray-300 leading-relaxed" v-html="renderedSummary"></div>
          <span v-if="summaryState === 'streaming'" class="inline-block w-2 h-4 bg-blue-600 animate-pulse ml-1"></span>
        </div>
        <div v-if="summaryState === 'error'" class="text-center py-6">
          <p class="text-red-400 text-sm">⚠️ {{ summaryError }}</p>
          <button @click="handleStart" class="text-purple-primary text-sm mt-2 hover:underline">重试</button>
        </div>
      </div>

      <!-- ========== Tab 2: 思维导图 ========== -->
      <div v-if="activeTab === 'mindmap'" class="space-y-2">
        <!-- 折叠头 + 操作按钮 -->
        <div v-if="mermaidCode" class="flex items-center gap-2">
          <button
            @click="collapsed.mindmap = !collapsed.mindmap"
            class="flex-1 flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors text-sm text-gray-600"
          >
            <span>🧠 思维导图</span>
            <svg class="w-4 h-4 transition-transform" :class="{ '-rotate-180': !collapsed.mindmap }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <!-- 全屏按钮 -->
          <button @click="mindmapFullscreen = true" title="全屏查看"
            class="p-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors text-gray-500 hover:text-gray-800">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"/></svg>
          </button>
          <!-- 下载 SVG 按钮 -->
          <button @click="downloadMindmapSvg" title="下载 SVG"
            class="px-2 py-1.5 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors text-gray-500 hover:text-gray-800 text-xs">
            SVG
          </button>
          <!-- 下载 PNG 按钮 -->
          <button @click="downloadMindmapPng" title="下载 PNG"
            class="px-2 py-1.5 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors text-gray-500 hover:text-gray-800 text-xs">
            PNG
          </button>
        </div>

        <div v-if="mermaidCode && !collapsed.mindmap" class="bg-white border border-gray-200 rounded-xl p-4 overflow-x-auto">
          <div ref="mermaidContainer" class="mermaid-container"></div>
        </div>
        <div v-else-if="summaryState === 'done' && !mermaidCode" class="text-center py-8">
          <p class="text-gray-500 text-sm">未生成思维导图</p>
        </div>
        <div v-else-if="!mermaidCode" class="text-center py-8">
          <p class="text-gray-500 text-sm">请先等待内容总结完成</p>
        </div>

        <!-- 全屏 Overlay -->
        <Teleport to="body">
          <div v-if="mindmapFullscreen" class="fixed inset-0 z-[100] bg-black/90 flex flex-col" @keydown.esc="mindmapFullscreen = false" tabindex="0" ref="fullscreenEl" @wheel.prevent="handleWheel">
            <div class="flex items-center justify-between px-6 py-3 shrink-0 gap-3">
              <h3 class="text-white font-medium shrink-0">🧠 思维导图</h3>
              <div class="flex items-center gap-2 text-sm text-gray-400">
                <button @click="mindmapScale = Math.max(0.3, mindmapScale - 0.2)" class="px-2 py-1 bg-white/10 hover:bg-white/20 rounded text-white">−</button>
                <span class="w-12 text-center cursor-pointer" @click="resetZoom" title="重置缩放">{{ Math.round(mindmapScale * 100) }}%</span>
                <button @click="mindmapScale = Math.min(5, mindmapScale + 0.2)" class="px-2 py-1 bg-white/10 hover:bg-white/20 rounded text-white">+</button>
              </div>
              <div class="flex items-center gap-2 shrink-0">
                <button @click="downloadMindmapSvg" class="px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-white text-sm transition-colors">SVG</button>
                <button @click="downloadMindmapPng" class="px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-white text-sm transition-colors">PNG</button>
                <button @click="mindmapFullscreen = false; resetZoom()" class="text-gray-400 hover:text-white text-2xl leading-none">&times;</button>
              </div>
            </div>
            <div class="flex-1 overflow-auto flex items-center justify-center p-8">
              <div ref="fullscreenMermaidContainer" class="mermaid-container" :style="{ transform: `scale(${mindmapScale})`, transformOrigin: 'center center', transition: 'transform 0.15s ease' }"></div>
            </div>
          </div>
        </Teleport>
      </div>

      <!-- ========== Tab 3: 字幕列表 ========== -->
      <div v-if="activeTab === 'subtitles'" class="space-y-2">
        <!-- 折叠头 + 下载按钮 -->
        <div v-if="transcriptSegments.length" class="flex items-center gap-2">
          <button
            @click="collapsed.subtitles = !collapsed.subtitles"
            class="flex-1 flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors text-sm text-gray-600"
          >
            <span>📋 字幕（{{ transcriptSegments.length }} 条{{ transcriptSource === 'subtitle' ? '' : ' · 来自描述' }}）</span>
            <svg class="w-4 h-4 transition-transform" :class="{ '-rotate-180': !collapsed.subtitles }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <!-- 下载 SRT 按钮 -->
          <button @click="downloadSrt" title="下载 SRT 字幕文件"
            class="p-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors text-gray-500 hover:text-gray-800">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
          </button>
        </div>

        <div v-if="transcriptState === 'loading'" class="flex items-center gap-3 py-8 justify-center">
          <div class="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <span class="text-gray-400 text-sm">正在获取字幕...</span>
        </div>

        <div v-if="transcriptSegments.length && !collapsed.subtitles" class="subtitle-list max-h-80 overflow-y-auto space-y-0.5 pr-1">
          <div
            v-for="(seg, idx) in transcriptSegments"
            :key="idx"
            class="flex gap-3 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition-colors group"
          >
            <span class="text-blue-500/70 text-xs font-mono shrink-0 w-14 text-right pt-0.5 group-hover:text-blue-600">
              {{ formatTime(seg.from) }}
            </span>
            <span class="text-gray-700 text-sm leading-relaxed">{{ seg.content }}</span>
          </div>
        </div>

        <div v-if="transcriptState === 'done' && !transcriptSegments.length" class="text-center py-6 space-y-2">
          <p class="text-gray-500 text-sm">该视频未获取到字幕</p>
          <p v-if="!transcriptHasSessdata" class="text-amber-400/80 text-xs leading-relaxed">
            ⚠️ 未配置 B站 SESSDATA，无法获取字幕<br/>
            请在右上角 <strong>设置 → B站 SESSDATA</strong> 中配置
          </p>
        </div>

        <div v-if="transcriptState === 'error'" class="text-center py-6">
          <p class="text-red-400 text-sm">⚠️ {{ transcriptError }}</p>
          <button @click="fetchTranscript(props.url)" class="text-purple-primary text-sm mt-2 hover:underline">重试</button>
        </div>
      </div>

      <!-- ========== Tab 4: AI 问答 ========== -->
      <div v-if="activeTab === 'chat'" class="space-y-3">
        <button
          v-if="chatMessages.length"
          @click="collapsed.chat = !collapsed.chat"
          class="w-full flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors text-sm text-gray-600"
        >
          <span>💬 对话记录（{{ chatMessages.filter(m => m.role === 'user').length }} 轮）</span>
          <svg class="w-4 h-4 transition-transform" :class="{ '-rotate-180': !collapsed.chat }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        <div v-if="!collapsed.chat" class="space-y-3 max-h-64 overflow-y-auto pr-1">
          <div v-for="(msg, idx) in chatMessages" :key="idx">
            <div v-if="msg.role === 'user'" class="flex justify-end">
              <div class="bg-blue-600 text-white text-sm px-4 py-2 rounded-2xl rounded-tr-md max-w-[80%]">
                {{ msg.content }}
              </div>
            </div>
            <div v-else class="flex justify-start">
              <div class="bg-gray-100 text-gray-700 text-sm px-4 py-2 rounded-2xl rounded-tl-md max-w-[80%] chat-markdown" v-html="renderMarkdown(msg.content)"></div>
            </div>
          </div>
          <div v-if="chatState === 'loading'" class="flex justify-start">
            <div class="bg-gray-100 text-gray-400 text-sm px-4 py-2 rounded-2xl rounded-tl-md">
              <span class="animate-pulse">思考中...</span>
            </div>
          </div>
        </div>

        <div class="flex gap-2">
          <input
            v-model="chatInput"
            @keyup.enter="handleAsk"
            placeholder="输入关于视频内容的问题..."
            class="flex-1 bg-gray-50 border border-gray-200 rounded-xl px-4 py-2.5 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-blue-500 transition-colors"
            :disabled="chatState === 'loading' || chatState === 'streaming'"
          />
          <button
            @click="handleAsk"
            :disabled="!chatInput.trim() || chatState === 'loading' || chatState === 'streaming'"
            class="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'
import { useAiSummary } from '../composables/useAiSummary.js'

const props = defineProps({
  url: { type: String, required: true },
})

const {
  summaryText, summaryState, summaryError, startSummary, extractMermaid,
  chatMessages, chatState, askQuestion,
  transcriptSegments, transcriptState, transcriptError, transcriptSource, transcriptHasSessdata, fetchTranscript,
  reset,
} = useAiSummary()

const tabs = [
  { key: 'summary', label: '总结', icon: '📝' },
  { key: 'mindmap', label: '导图', icon: '🧠' },
  { key: 'subtitles', label: '字幕', icon: '📋' },
  { key: 'chat', label: '问答', icon: '💬' },
]

const activeTab = ref('summary')
const chatInput = ref('')
const mermaidContainer = ref(null)
const fullscreenMermaidContainer = ref(null)
const fullscreenEl = ref(null)
const mermaidCode = ref(null)
const mindmapFullscreen = ref(false)
let mermaidRenderId = 0

const collapsed = reactive({ summary: false, mindmap: false, subtitles: false, chat: false })

marked.setOptions({ gfm: true, breaks: true })
const renderedSummary = ref('')

// ── Tab 切换 ───────────────────────────────────────────────
function switchTab(key) {
  activeTab.value = key
  if (key === 'subtitles' && transcriptState.value === 'idle') {
    fetchTranscript(props.url)
  }
}

function formatTime(seconds) {
  if (!seconds && seconds !== 0) return ''
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

// ── Markdown 渲染 ──────────────────────────────────────────
watch(summaryText, (newText) => {
  if (newText) {
    const textWithoutMermaid = newText.replace(/```mermaid[\s\S]*?```/g, '')
    renderedSummary.value = marked.parse(textWithoutMermaid)
    const code = extractMermaid(newText)
    if (code) mermaidCode.value = code
  }
})

// ── 思维导图渲染 ───────────────────────────────────────────
watch([mermaidCode, activeTab], async ([code, tab]) => {
  if (tab === 'mindmap' && code) {
    await nextTick(); await nextTick()
    await renderMermaid(code, mermaidContainer.value)
  }
})

watch(summaryText, async () => {
  if (activeTab.value === 'mindmap' && mermaidCode.value) {
    await nextTick()
    await renderMermaid(mermaidCode.value, mermaidContainer.value)
  }
})

// 全屏时渲染导图
watch(mindmapFullscreen, async (val) => {
  if (val && mermaidCode.value) {
    await nextTick(); await nextTick()
    await renderMermaid(mermaidCode.value, fullscreenMermaidContainer.value)
    fullscreenEl.value?.focus()
  }
})

// ── mermaid 模块缓存 ───────────────────────────────────────
let mermaidModule = null

async function getMermaid() {
  if (mermaidModule) return mermaidModule
  try {
    mermaidModule = (await import('mermaid')).default
  } catch (e) {
    console.error('Mermaid import failed, trying CDN fallback:', e)
    // CDN 兜底：动态加载 mermaid
    await new Promise((resolve, reject) => {
      const s = document.createElement('script')
      s.src = 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js'
      s.onload = resolve
      s.onerror = reject
      document.head.appendChild(s)
    })
    mermaidModule = window.mermaid
  }
  return mermaidModule
}

async function renderMermaid(code, container) {
  if (!container || !code) return
  const currentId = ++mermaidRenderId
  try {
    const mermaid = await getMermaid()
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      themeVariables: {
        primaryColor: '#7c3aed', primaryTextColor: '#e5e7eb',
        primaryBorderColor: '#7c3aed', lineColor: '#6b7280',
        secondaryColor: '#1f2937', tertiaryColor: '#374151',
      },
    })
    const id = 'mermaid-' + Date.now() + '-' + Math.random().toString(36).slice(2, 6)
    const { svg } = await mermaid.render(id, code)
    if (currentId === mermaidRenderId && container) {
      container.innerHTML = svg
    }
  } catch (e) {
    console.error('Mermaid rendering failed:', e)
    if (currentId === mermaidRenderId && container) {
      container.innerHTML = `<div style="text-align:center;padding:1rem;"><p style="color:#f87171;font-size:0.875rem;">渲染失败: ${e.message}</p><button onclick="location.reload()" style="margin-top:0.5rem;padding:0.25rem 1rem;background:#7c3aed;color:white;border:none;border-radius:0.5rem;cursor:pointer;font-size:0.8rem;">刷新重试</button></div>`
    }
  }
}

// ── 字幕下载 (SRT) ─────────────────────────────────────────
function downloadSrt() {
  if (!transcriptSegments.value.length) return
  const lines = transcriptSegments.value.map((seg, i) => {
    const start = secondsToSrtTime(seg.from)
    const end = secondsToSrtTime(seg.to)
    return `${i + 1}\n${start} --> ${end}\n${seg.content}\n`
  })
  const srt = lines.join('\n')
  const blob = new Blob([srt], { type: 'text/plain;charset=utf-8' })
  triggerDownload(blob, `${summaryText.value ? 'subtitle' : 'transcript'}.srt`)
}

function secondsToSrtTime(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  const ms = Math.round((seconds % 1) * 1000)
  return `${pad2(h)}:${pad2(m)}:${pad2(s)},${pad3(ms)}`
}

function pad2(n) { return String(n).padStart(2, '0') }
function pad3(n) { return String(n).padStart(3, '0') }

// ── 全屏缩放 ───────────────────────────────────────────────
const mindmapScale = ref(1)

function handleWheel(e) {
  e.preventDefault()
  const delta = e.deltaY > 0 ? -0.1 : 0.1
  mindmapScale.value = Math.min(5, Math.max(0.3, mindmapScale.value + delta))
}

function resetZoom() {
  mindmapScale.value = 1
}

// ── 思维导图下载 (SVG) ─────────────────────────────────────
function downloadMindmapSvg() {
  const container = mindmapFullscreen.value ? fullscreenMermaidContainer.value : mermaidContainer.value
  if (!container) { alert('思维导图尚未渲染完成，请稍后再试'); return }
  const svgEl = container.querySelector('svg')
  if (!svgEl) { alert('未找到思维导图，请先等待渲染完成'); return }

  const cloned = svgEl.cloneNode(true)
  cloned.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  cloned.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink')
  const svgData = new XMLSerializer().serializeToString(cloned)
  const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' })
  triggerDownload(blob, 'mindmap.svg')
}

// ── 思维导图下载 (PNG) ─────────────────────────────────────
function downloadMindmapPng() {
  const container = mindmapFullscreen.value ? fullscreenMermaidContainer.value : mermaidContainer.value
  if (!container) { alert('思维导图尚未渲染完成，请稍后再试'); return }
  const svgEl = container.querySelector('svg')
  if (!svgEl) { alert('未找到思维导图，请先等待渲染完成'); return }

  const cloned = svgEl.cloneNode(true)
  cloned.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  cloned.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink')

  const svgData = new XMLSerializer().serializeToString(cloned)
  const svgBase64 = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)))

  const img = new Image()
  img.onload = () => {
    const scale = 2
    const canvas = document.createElement('canvas')
    canvas.width = img.naturalWidth * scale
    canvas.height = img.naturalHeight * scale
    const ctx = canvas.getContext('2d')
    ctx.scale(scale, scale)
    ctx.fillStyle = '#1a1a2e'
    ctx.fillRect(0, 0, img.naturalWidth, img.naturalHeight)
    ctx.drawImage(img, 0, 0)

    canvas.toBlob((blob) => {
      if (blob) triggerDownload(blob, 'mindmap.png')
      else alert('PNG 生成失败，请尝试下载 SVG 格式')
    }, 'image/png')
  }
  img.onerror = () => {
    alert('PNG 生成失败，请尝试下载 SVG 格式')
  }
  img.src = svgBase64
}

function triggerDownload(blob, filename) {
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(a.href)
}

// ── 操作方法 ────────────────────────────────────────────────
function handleStart() {
  mermaidRenderId = 0
  startSummary(props.url)
  fetchTranscript(props.url)
}

// 组件挂载时自动开始总结
onMounted(() => {
  handleStart()
})

async function handleAsk() {
  if (!chatInput.value.trim()) return
  const question = chatInput.value
  chatInput.value = ''
  collapsed.chat = false
  await askQuestion(props.url, question)
}

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}

onUnmounted(() => { reset() })
</script>

<style scoped>
.summary-markdown :deep(h2) { color: #1f2937; font-size: 0.95rem; font-weight: 600; margin-top: 1rem; margin-bottom: 0.5rem; }
.summary-markdown :deep(h2:first-child) { margin-top: 0; }
.summary-markdown :deep(ul) { list-style: none; padding-left: 0; }
.summary-markdown :deep(li) { position: relative; padding-left: 1.25rem; margin-bottom: 0.375rem; }
.summary-markdown :deep(li::before) { content: '•'; position: absolute; left: 0; color: #2563eb; }
.summary-markdown :deep(p) { margin-bottom: 0.5rem; }
.summary-markdown :deep(strong) { color: #111827; font-weight: 600; }
.summary-markdown :deep(code) { background: #f3f4f6; padding: 0.125rem 0.375rem; border-radius: 0.25rem; font-size: 0.8125rem; }
.chat-markdown :deep(p) { margin-bottom: 0.25rem; }
.chat-markdown :deep(p:last-child) { margin-bottom: 0; }
.chat-markdown :deep(ul), .chat-markdown :deep(ol) { padding-left: 1.25rem; margin-bottom: 0.25rem; }
.chat-markdown :deep(code) { background: #e5e7eb; padding: 0.0625rem 0.25rem; border-radius: 0.1875rem; font-size: 0.8125rem; }
.mermaid-container :deep(svg) { max-width: 100%; height: auto; }
.subtitle-list::-webkit-scrollbar { width: 4px; }
.subtitle-list::-webkit-scrollbar-track { background: transparent; }
.subtitle-list::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }
</style>
