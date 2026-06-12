<template>
  <section class="py-20 px-4">
    <div class="max-w-4xl mx-auto">
      <h2 class="text-3xl md:text-4xl font-bold text-center mb-12">
        三步搞定，<span class="gradient-text">简单到不行</span>
      </h2>

      <div class="flex flex-col md:flex-row items-center gap-8">
        <div v-for="(step, i) in steps" :key="i"
             class="flex-1 text-center animate-fade-in-up"
             :style="{ animationDelay: i * 0.15 + 's' }">
          <!-- 步骤编号 -->
          <div class="w-14 h-14 rounded-full bg-gradient-to-br from-purple-primary to-blue-primary flex items-center justify-center mx-auto mb-4">
            <span class="text-white font-bold text-xl">{{ i + 1 }}</span>
          </div>
          <h3 class="text-white font-semibold text-lg mb-2">{{ step.title }}</h3>
          <p class="text-gray-400 text-sm">{{ step.desc }}</p>

          <!-- 箭头（非最后一步） -->
          <div v-if="i < steps.length - 1" class="hidden md:block absolute">
            <svg class="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
const steps = [
  { title: '粘贴链接', desc: '复制你要下载的视频链接，粘贴到输入框中' },
  { title: '选择画质', desc: '解析完成后，选择你需要的画质和格式' },
  { title: '一键下载', desc: '点击下载按钮，等待完成即可保存到本地' },
]
</script>
