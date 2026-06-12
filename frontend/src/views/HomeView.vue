<template>
  <div>
    <!-- Hero + 输入框 -->
    <HeroSection :loading="downloader.loading.value" :error="downloader.error.value" @parse="handleParse" />

    <!-- 下载进度 -->
    <div class="flex justify-center px-4 -mt-4 relative z-20" v-if="downloader.downloadStatus.value">
      <ProgressPanel
        :visible="true"
        :progress="downloader.progress.value"
        :speed="downloader.speed.value"
        :eta="downloader.eta.value"
        :status="downloader.downloadStatus.value"
        :error="downloader.error.value"
        @downloadFile="downloader.downloadFile()"
      />
    </div>

    <!-- 功能特性 -->
    <FeaturesSection />

    <!-- 使用步骤 -->
    <StepsSection />

    <!-- 定价 -->
    <PricingSection @subscribe="handleSubscribe" />

    <!-- 平台展示 -->
    <PlatformsSection />

    <!-- 解析结果弹窗 -->
    <DownloadModal
      :visible="showModal"
      :info="downloader.videoInfo.value"
      :downloading="downloader.downloadStatus.value === 'downloading'"
      @close="showModal = false"
      @download="handleDownload"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useDownloader } from '@/composables/useDownloader'
import HeroSection from '@/components/HeroSection.vue'
import ProgressPanel from '@/components/ProgressPanel.vue'
import FeaturesSection from '@/components/FeaturesSection.vue'
import StepsSection from '@/components/StepsSection.vue'
import PricingSection from '@/components/PricingSection.vue'
import PlatformsSection from '@/components/PlatformsSection.vue'
import DownloadModal from '@/components/DownloadModal.vue'

const downloader = useDownloader()
const showModal = ref(false)

async function handleParse(url) {
  await downloader.parseUrl(url)
  if (downloader.videoInfo.value) {
    showModal.value = true
  }
}

function handleDownload(format) {
  showModal.value = false
  downloader.startDownload(downloader.parsedUrl.value, String(format.format_id), String(format.quality))
}

function handleSubscribe(plan) {
  alert(`${plan.toUpperCase()} 套餐订阅功能开发中，敬请期待！`)
}
</script>
