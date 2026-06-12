import { ref } from 'vue'
import api from '@/api'

function safeStr(val) {
  if (!val) return ''
  if (typeof val === 'string') return val
  if (val instanceof Error) return val.message
  if (typeof val === 'object') return val.message || val.detail || val.error || JSON.stringify(val)
  return String(val)
}

export function useDownloader() {
  const loading = ref(false)
  const videoInfo = ref(null)
  const parsedUrl = ref('')
  const error = ref('')
  const taskId = ref('')
  const progress = ref(0)
  const speed = ref('')
  const eta = ref('')
  const downloadStatus = ref('')
  const filename = ref('')

  let eventSource = null

  async function parseUrl(url) {
    loading.value = true
    error.value = ''
    videoInfo.value = null
    parsedUrl.value = url
    try {
      const res = await api.getInfo(url)
      videoInfo.value = res.data
    } catch (e) {
      error.value = safeStr(e)
    } finally {
      loading.value = false
    }
  }

  async function startDownload(url, formatId, quality) {
    error.value = ''
    downloadStatus.value = 'pending'
    progress.value = 0
    try {
      const res = await api.download({ url, format_id: formatId, quality })
      taskId.value = res.data.task_id
      listenProgress(res.data.task_id)
    } catch (e) {
      error.value = safeStr(e)
      downloadStatus.value = 'failed'
    }
  }

  function listenProgress(id) {
    if (eventSource) eventSource.close()
    eventSource = new EventSource(`/api/progress/${id}`)

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        downloadStatus.value = data.status
        progress.value = data.progress || 0
        speed.value = data.speed || ''
        eta.value = data.eta || ''
        filename.value = data.filename || ''

        if (data.status === 'completed' || data.status === 'failed') {
          eventSource.close()
          eventSource = null
          if (data.error) error.value = safeStr(data.error)
        }
      } catch (e) {
        console.error('SSE parse error:', e)
      }
    }

    eventSource.onerror = () => {
      eventSource.close()
      eventSource = null
    }
  }

  function downloadFile() {
    if (taskId.value) {
      window.open(`/api/file/${taskId.value}`, '_blank')
    }
  }

  function reset() {
    videoInfo.value = null
    error.value = ''
    taskId.value = ''
    progress.value = 0
    speed.value = ''
    eta.value = ''
    downloadStatus.value = ''
    filename.value = ''
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
  }

  return {
    loading, videoInfo, parsedUrl, error, taskId, progress, speed, eta,
    downloadStatus, filename,
    parseUrl, startDownload, downloadFile, reset,
  }
}
