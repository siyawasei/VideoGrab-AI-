<template>
  <nav class="fixed top-0 left-0 right-0 z-50 glass-card !rounded-none border-t-0 border-x-0">
    <div class="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
      <!-- Logo -->
      <router-link to="/" class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-primary to-blue-primary flex items-center justify-center">
          <span class="text-white font-bold text-sm">V</span>
        </div>
        <span class="text-lg font-bold gradient-text">VideoGrab</span>
      </router-link>

      <!-- 导航链接 -->
      <div class="hidden md:flex items-center gap-6">
        <router-link to="/" class="text-sm text-gray-300 hover:text-white transition-colors">首页</router-link>
        <router-link to="/history" class="text-sm text-gray-300 hover:text-white transition-colors">下载历史</router-link>
        <a href="#pricing" class="text-sm text-gray-300 hover:text-white transition-colors">定价</a>
      </div>

      <!-- 用户操作 -->
      <div class="flex items-center gap-3">
        <!-- Cookies 上传 -->
        <div class="relative">
          <button @click="showCookieUpload = !showCookieUpload"
                  class="text-xs text-gray-400 hover:text-white transition-colors flex items-center gap-1"
                  title="上传 Cookies（解锁更多平台）">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/></svg>
            Cookies
          </button>
          <!-- 上传弹窗 -->
          <div v-if="showCookieUpload" class="absolute right-0 top-full mt-2 glass-card !p-4 w-80 z-50 space-y-4">
            <!-- B站 SESSDATA -->
            <div>
              <p class="text-xs text-white font-medium mb-1">B站高清画质（SESSDATA）</p>
              <p class="text-xs text-gray-500 mb-2">F12 → Application → Cookies → bilibili.com → SESSDATA</p>
              <div class="flex gap-2">
                <input v-model="sessdata" type="text" placeholder="粘贴 SESSDATA 值"
                       class="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white outline-none" />
                <button @click="handleSetSessdata" class="text-xs px-3 py-1.5 rounded-lg bg-purple-primary/30 text-purple-300 hover:bg-purple-primary/50">保存</button>
              </div>
            </div>
            <!-- 通用 cookies.txt -->
            <div>
              <p class="text-xs text-white font-medium mb-1">其他平台 Cookies</p>
              <p class="text-xs text-gray-500 mb-2">用 "Get cookies.txt LOCALLY" 扩展导出</p>
              <input type="file" accept=".txt" @change="handleCookieUpload" class="text-xs text-gray-300 w-full" />
            </div>
            <p v-if="cookieMsg" class="text-xs" :class="cookieMsg.includes('成功') ? 'text-green-400' : 'text-red-400'">{{ cookieMsg }}</p>
          </div>
        </div>

        <template v-if="userStore.isLoggedIn">
          <span class="text-xs px-2 py-1 rounded-full"
                :class="membershipBadgeClass">
            {{ userStore.membership.toUpperCase() }}
          </span>
          <span class="text-sm text-gray-300">{{ userStore.user?.username }}</span>
          <button @click="userStore.logout()" class="text-sm text-gray-400 hover:text-white transition-colors">退出</button>
        </template>
        <template v-else>
          <button @click="$emit('showLogin')" class="gradient-btn !py-2 !px-5 text-sm">登录 / 注册</button>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import api from '@/api'

defineEmits(['showLogin'])

const userStore = useUserStore()
const showCookieUpload = ref(false)
const cookieMsg = ref('')
const sessdata = ref('')

const membershipBadgeClass = computed(() => {
  const map = {
    free: 'bg-gray-600 text-gray-200',
    pro: 'bg-gradient-to-r from-purple-primary to-blue-primary text-white',
    premium: 'bg-gradient-to-r from-gold to-yellow-600 text-black',
  }
  return map[userStore.membership] || map.free
})

async function handleCookieUpload(e) {
  const file = e.target.files[0]
  if (!file) return
  try {
    await api.uploadCookies(file)
    cookieMsg.value = 'Cookies 上传成功！'
    setTimeout(() => { cookieMsg.value = ''; showCookieUpload.value = false }, 2000)
  } catch (err) {
    cookieMsg.value = '上传失败: ' + (err.message || '未知错误')
  }
}

async function handleSetSessdata() {
  if (!sessdata.value.trim()) return
  try {
    await api.setBiliSessdata(sessdata.value.trim())
    cookieMsg.value = 'B站 SESSDATA 保存成功！高清画质已解锁'
    sessdata.value = ''
    setTimeout(() => { cookieMsg.value = '' }, 3000)
  } catch (err) {
    cookieMsg.value = '保存失败: ' + (err.message || '未知错误')
  }
}
</script>
