<template>
  <section id="pricing" class="py-20 px-4">
    <div class="max-w-5xl mx-auto">
      <h2 class="text-3xl md:text-4xl font-bold text-center mb-4">
        选择适合你的 <span class="gradient-text">套餐</span>
      </h2>
      <p class="text-gray-500 text-center mb-12">灵活定价，按需选择</p>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- 免费版 -->
        <div class="bg-white border border-gray-200 rounded-2xl !p-6 flex flex-col">
          <h3 class="text-xl font-bold text-gray-800 mb-1">免费版</h3>
          <p class="text-gray-400 text-sm mb-6">适合轻度使用</p>
          <div class="mb-6">
            <span class="text-3xl font-bold text-gray-800">¥0</span>
            <span class="text-gray-400 text-sm">/永久</span>
          </div>
          <ul class="space-y-3 flex-1 mb-6">
            <li v-for="f in freeFeatures" :key="f" class="flex items-center gap-2 text-sm text-gray-600">
              <span class="text-green-500">✓</span>{{ f }}
            </li>
          </ul>
          <button class="w-full py-3 rounded-xl border border-gray-200 text-gray-600 text-sm font-medium hover:bg-gray-50 transition-colors">
            当前方案
          </button>
        </div>

        <!-- Pro 版（推荐） -->
        <div class="bg-white border-2 border-blue-500 rounded-2xl !p-6 flex flex-col relative shadow-lg">
          <div class="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full text-xs font-bold bg-blue-600 text-white">
            最受欢迎
          </div>
          <h3 class="text-xl font-bold gradient-text mb-1">Pro 版</h3>
          <p class="text-gray-400 text-sm mb-6">适合高频下载用户</p>
          <div class="mb-6">
            <span class="text-3xl font-bold text-gray-800">¥19.9</span>
            <span class="text-gray-400 text-sm">/月</span>
          </div>
          <ul class="space-y-3 flex-1 mb-6">
            <li v-for="f in proFeatures" :key="f" class="flex items-center gap-2 text-sm text-gray-600">
              <span class="text-green-500">✓</span>{{ f }}
            </li>
          </ul>
          <button class="gradient-btn w-full !py-3 text-sm" @click="$emit('subscribe', 'pro')">
            立即订阅
          </button>
        </div>

        <!-- Premium 版 -->
        <div class="bg-white border border-gray-200 rounded-2xl !p-6 flex flex-col">
          <h3 class="text-xl font-bold text-green-700 mb-1">Premium 版</h3>
          <p class="text-gray-400 text-sm mb-6">全能创作者首选</p>
          <div class="mb-6">
            <span class="text-3xl font-bold text-gray-800">¥49.9</span>
            <span class="text-gray-400 text-sm">/月</span>
          </div>
          <ul class="space-y-3 flex-1 mb-6">
            <li v-for="f in premiumFeatures" :key="f" class="flex items-center gap-2 text-sm text-gray-600">
              <span class="text-green-500">✓</span>{{ f }}
            </li>
          </ul>
          <button class="w-full py-3 rounded-xl border border-green-500 text-green-700 text-sm font-medium hover:bg-green-50 transition-colors"
                  @click="$emit('subscribe', 'premium')">
            立即订阅
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
defineEmits(['subscribe'])

const freeFeatures = [
  '每日 5 次下载',
  '最高 720p 画质',
  '单文件下载',
  '基础格式支持',
]

const proFeatures = [
  '无限次下载',
  '最高 4K 画质',
  '批量下载',
  '去除水印',
  '所有格式支持',
  '优先下载速度',
]

const premiumFeatures = [
  'Pro 版全部功能',
  'AI 视频总结',
  '字幕自动翻译',
  '专属客服支持',
  'API 接口访问',
]
</script>
