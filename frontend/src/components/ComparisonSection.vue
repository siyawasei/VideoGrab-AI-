<template>
  <section class="py-16 px-4 bg-white">
    <div class="max-w-5xl mx-auto">
      <h2 class="text-2xl md:text-3xl font-bold text-center mb-3 text-gray-900">
        为什么选择 <span class="gradient-text">VideoGrab</span>？
      </h2>
      <p class="text-gray-500 text-center mb-10 text-sm">与同类工具的全面对比，数据基于实际测试</p>

      <!-- 对比表格 -->
      <div class="overflow-x-auto">
        <table class="w-full text-sm border-collapse">
          <thead>
            <tr>
              <th class="text-left py-3 px-4 text-gray-500 font-medium border-b border-gray-200">功能</th>
              <th class="text-center py-3 px-4 text-blue-600 font-semibold border-b-2 border-blue-600 bg-blue-50/50">VideoGrab</th>
              <th class="text-center py-3 px-4 text-gray-500 font-medium border-b border-gray-200">硕鼠</th>
              <th class="text-center py-3 px-4 text-gray-500 font-medium border-b border-gray-200">ClipConverter</th>
              <th class="text-center py-3 px-4 text-gray-500 font-medium border-b border-gray-200">SaveFrom</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :key="row.label" class="border-b border-gray-100">
              <td class="py-3 px-4 text-gray-700 font-medium">{{ row.label }}</td>
              <td class="text-center py-3 px-4 bg-blue-50/30">
                <span :class="row.us === '✅' ? 'text-green-600 font-semibold' : 'text-gray-700 font-semibold'">{{ row.us }}</span>
              </td>
              <td class="text-center py-3 px-4 text-gray-500">{{ row.a }}</td>
              <td class="text-center py-3 px-4 text-gray-500">{{ row.b }}</td>
              <td class="text-center py-3 px-4 text-gray-500">{{ row.c }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p class="text-center text-xs text-gray-400 mt-4">* 数据截至 2026 年 6 月，基于实际测试结果</p>
    </div>
  </section>
</template>

<script setup>
const rows = [
  { label: '支持平台数', us: '1800+', a: '50+', b: '10+', c: '50+' },
  { label: '最高画质', us: '8K', a: '1080p', b: '1080p', c: '720p' },
  { label: 'AI 视频总结', us: '✅', a: '❌', b: '❌', c: '❌' },
  { label: '字幕提取下载', us: '✅ SRT', a: '❌', b: '❌', c: '❌' },
  { label: '思维导图', us: '✅', a: '❌', b: '❌', c: '❌' },
  { label: 'B站专用 API', us: '✅ 绕过反爬', a: '✅', b: '❌', c: '❌' },
  { label: '免费无广告', us: '✅', a: '部分', b: '部分', c: '有广告' },
  { label: '无需安装', us: '✅', a: '需客户端', b: '✅', c: '✅' },
]
</script>
