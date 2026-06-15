/**
 * AI 视频总结 composable — 管理 SSE 流式消费状态
 *
 * 提供：
 * - startSummary(url): 触发视频总结，流式接收 Markdown
 * - askQuestion(url, question): AI 问答，流式接收回答
 * - summaryText / chatMessages: 响应式状态
 * - extractMermaid(text): 从总结中提取 Mermaid 代码块
 */

import { ref, reactive } from 'vue'
import { aiApi } from '../api/index.js'

export function useAiSummary() {
  // ── 总结状态 ──────────────────────────────────────────────
  const summaryText = ref('')
  const summaryState = ref('idle') // idle | loading | streaming | done | error
  const summaryError = ref('')

  // ── 问答状态 ──────────────────────────────────────────────
  const chatMessages = reactive([]) // [{role: 'user'|'assistant', content: '...'}]
  const chatState = ref('idle') // idle | loading | streaming | done | error
  const chatError = ref('')

  // ── 字幕状态 ──────────────────────────────────────────────
  const transcriptSegments = ref([]) // [{from, to, content}]
  const transcriptState = ref('idle') // idle | loading | done | error
  const transcriptError = ref('')
  const transcriptSource = ref('') // 'subtitle' | 'description'
  const transcriptHasSessdata = ref(true) // 是否有 SESSDATA

  // ── 当前视频 URL ──────────────────────────────────────────
  const currentUrl = ref('')

  /**
   * 消费 SSE 流，逐 chunk 回调
   * @param {Response} response - fetch Response
   * @param {function} onChunk - 收到文本 chunk 时的回调
   * @param {function} onDone - 流结束时的回调
   * @param {function} onError - 出错时的回调
   */
  async function _consumeSSE(response, onChunk, onDone, onError) {
    if (!response.ok) {
      const errText = await response.text()
      let msg = '请求失败'
      try {
        const errJson = JSON.parse(errText)
        msg = errJson.detail || msg
      } catch {}
      onError(msg)
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // 保留不完整的行

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const jsonStr = line.slice(6).trim()
          if (!jsonStr) continue

          try {
            const data = JSON.parse(jsonStr)
            if (data.error) {
              onError(data.error)
              return
            }
            if (data.done) {
              onDone()
              return
            }
            if (data.content) {
              onChunk(data.content)
            }
          } catch {}
        }
      }
      onDone()
    } catch (e) {
      onError(e.message || '连接中断')
    }
  }

  /**
   * 开始视频总结
   * @param {string} url - 视频 URL
   */
  async function startSummary(url) {
    currentUrl.value = url
    summaryText.value = ''
    summaryState.value = 'loading'
    summaryError.value = ''

    try {
      const response = await aiApi.summarizeVideo(url)

      summaryState.value = 'streaming'

      await _consumeSSE(
        response,
        // onChunk
        (chunk) => {
          summaryText.value += chunk
        },
        // onDone
        () => {
          summaryState.value = 'done'
        },
        // onError
        (err) => {
          summaryError.value = err
          summaryState.value = 'error'
        },
      )
    } catch (e) {
      summaryError.value = e.message || '网络错误'
      summaryState.value = 'error'
    }
  }

  /**
   * AI 问答
   * @param {string} url - 视频 URL
   * @param {string} question - 用户问题
   */
  async function askQuestion(url, question) {
    if (!question.trim()) return

    // 添加用户消息
    chatMessages.push({ role: 'user', content: question })
    chatState.value = 'loading'
    chatError.value = ''

    // 添加空的 assistant 消息（用于流式填充）
    const assistantIndex = chatMessages.length
    chatMessages.push({ role: 'assistant', content: '' })

    try {
      // 构建历史（不包含当前空的 assistant 消息）
      const history = chatMessages
        .slice(0, -1)
        .filter((m) => m.content)

      const response = await aiApi.aiChat(url, question, history)

      chatState.value = 'streaming'

      await _consumeSSE(
        response,
        // onChunk
        (chunk) => {
          chatMessages[assistantIndex].content += chunk
        },
        // onDone
        () => {
          chatState.value = 'done'
        },
        // onError
        (err) => {
          chatError.value = err
          chatMessages[assistantIndex].content = `⚠️ ${err}`
          chatState.value = 'error'
        },
      )
    } catch (e) {
      chatError.value = e.message || '网络错误'
      chatMessages[assistantIndex].content = `⚠️ ${chatError.value}`
      chatState.value = 'error'
    }
  }

  /**
   * 从总结文本中提取 Mermaid 代码块
   * 支持完整和未完成的代码块（流式场景）
   * @param {string} text - 总结 Markdown 文本
   * @returns {string|null} - Mermaid 代码或 null
   */
  function extractMermaid(text) {
    if (!text) return null
    // 优先匹配完整代码块
    const complete = text.match(/```mermaid\s*\n([\s\S]*?)```/)
    if (complete) return complete[1].trim()
    // 流式场景：匹配未关闭的代码块
    const partial = text.match(/```mermaid\s*\n([\s\S]*)/)
    if (partial) {
      const code = partial[1].trim()
      // 至少需要有 mindmap 关键字才算有效
      if (code.includes('mindmap') || code.includes('root')) return code
    }
    return null
  }

  /**
   * 获取视频字幕/转录文本
   * @param {string} url - 视频 URL
   */
  async function fetchTranscript(url) {
    transcriptState.value = 'loading'
    transcriptError.value = ''
    transcriptSegments.value = []
    try {
      const res = await aiApi.getTranscript(url)
      const data = res.data || res
      transcriptSegments.value = data.segments || []
      transcriptSource.value = data.source || 'unknown'
      transcriptHasSessdata.value = data.has_sessdata !== false
      transcriptState.value = 'done'
    } catch (e) {
      transcriptError.value = e.message || '获取字幕失败'
      transcriptState.value = 'error'
    }
  }

  /**
   * 清空所有状态
   */
  function reset() {
    summaryText.value = ''
    summaryState.value = 'idle'
    summaryError.value = ''
    chatMessages.length = 0
    chatState.value = 'idle'
    chatError.value = ''
    transcriptSegments.value = []
    transcriptState.value = 'idle'
    transcriptError.value = ''
    transcriptSource.value = ''
    transcriptHasSessdata.value = true
    currentUrl.value = ''
  }

  return {
    // 总结
    summaryText,
    summaryState,
    summaryError,
    startSummary,
    extractMermaid,

    // 问答
    chatMessages,
    chatState,
    chatError,
    askQuestion,

    // 字幕
    transcriptSegments,
    transcriptState,
    transcriptError,
    transcriptSource,
    transcriptHasSessdata,
    fetchTranscript,

    // 通用
    currentUrl,
    reset,
  }
}
