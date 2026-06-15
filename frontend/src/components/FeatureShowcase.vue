<template>
  <section class="py-16 px-4">
    <div class="max-w-6xl mx-auto">
      <h2 class="text-2xl md:text-3xl font-bold text-center mb-3 text-gray-900">
        一站式视频工具，<span class="gradient-text">不止于下载</span>
      </h2>
      <p class="text-gray-500 text-center mb-10 max-w-xl mx-auto text-sm">集视频下载、AI 分析、字幕提取于一体，覆盖你对视频的所有需求</p>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div v-for="(f, i) in features" :key="i"
             class="bg-white border border-gray-200 rounded-xl p-5 text-center hover:shadow-md hover:border-blue-200 transition-all group">
          <div class="text-3xl mb-3">{{ f.icon }}</div>
          <h3 class="text-gray-800 font-semibold text-sm mb-1.5">{{ f.title }}</h3>
          <p class="text-blue-600 text-xs font-medium mb-1">{{ f.highlight }}</p>
          <p class="text-gray-400 text-xs leading-relaxed">{{ f.desc }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
const features = [
  { icon: '🌐', title: '全平台支持', highlight: '1800+ 视频网站', desc: 'B站、YouTube、抖音、Twitter、Instagram 等全球主流平台' },
  { icon: '🤖', title: 'AI 智能总结', highlight: 'DeepSeek 大模型', desc: '自动分析视频内容，生成摘要、章节、要点' },
  { icon: '📋', title: '字幕提取', highlight: 'SRT 格式导出', desc: '自动获取视频字幕，支持多语言，一键下载' },
  { icon: '🎬', title: '高清下载', highlight: '最高 8K 画质', desc: '多画质自由选择，音视频自动合并' },
  { icon: '🧠', title: '思维导图', highlight: 'SVG/PNG 下载', desc: 'AI 生成知识图谱，全屏查看，滚轮缩放' },
  { icon: '💬', title: 'AI 问答', highlight: '多轮对话', desc: '基于视频内容的智能问答，快速定位信息' },
  { icon: '🔒', title: '安全隐私', highlight: '无需注册', desc: '完全免费，不存储内容，本地处理' },
  { icon: '⚡', title: '极速下载', highlight: '不限速', desc: '多线程并发，实时进度，秒级响应' },
]
</script>
