<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center p-4" @click.self="$emit('close')">
    <div class="absolute inset-0 bg-black/40 backdrop-blur-sm"></div>

    <div class="relative bg-white !p-8 w-full max-w-md animate-fade-in-up rounded-2xl shadow-2xl border border-gray-200">
      <button @click="$emit('close')" class="absolute top-4 right-4 text-gray-400 hover:text-gray-800 text-xl">&times;</button>

      <!-- Tab 切换 -->
      <div class="flex gap-4 mb-6">
        <button @click="switchMode('login')" class="pb-2 text-sm font-medium transition-colors"
                :class="mode === 'login' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-400'">登录</button>
        <button @click="switchMode('register')" class="pb-2 text-sm font-medium transition-colors"
                :class="mode === 'register' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-400'">注册</button>
      </div>

      <!-- 成功提示 -->
      <div v-if="success" class="mb-4 p-3 bg-green-50 border border-green-200 rounded-xl text-green-700 text-sm">
        ✅ {{ success }}
      </div>

      <!-- 错误提示 -->
      <p v-if="error" class="mb-4 text-red-500 text-sm">{{ error }}</p>

      <!-- 登录表单 -->
      <form v-if="mode === 'login'" @submit.prevent="handleLogin" class="space-y-4">
        <input v-model="form.account" type="text" placeholder="用户名"
               class="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-gray-800 outline-none focus:border-blue-500 transition-colors placeholder-gray-400" />
        <input v-model="form.password" type="password" placeholder="密码"
               class="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-gray-800 outline-none focus:border-blue-500 transition-colors placeholder-gray-400" />
        <button type="submit" :disabled="submitting" class="gradient-btn w-full !py-3">{{ submitting ? '登录中...' : '登录' }}</button>
      </form>

      <!-- 注册表单 -->
      <form v-else @submit.prevent="handleRegister" class="space-y-4">
        <input v-model="form.username" type="text" placeholder="用户名（2-20个字符）"
               class="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-gray-800 outline-none focus:border-blue-500 transition-colors placeholder-gray-400" />
        <input v-model="form.password" type="password" placeholder="密码（至少6位）"
               class="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-gray-800 outline-none focus:border-blue-500 transition-colors placeholder-gray-400" />
        <input v-model="form.confirmPassword" type="password" placeholder="再次输入密码"
               class="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-gray-800 outline-none focus:border-blue-500 transition-colors placeholder-gray-400" />
        <button type="submit" :disabled="submitting" class="gradient-btn w-full !py-3">{{ submitting ? '注册中...' : '注册' }}</button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { useUserStore } from '@/stores/user'

const props = defineProps({ visible: Boolean })
const emit = defineEmits(['close'])

// 阻止背景页面滚动
watch(() => props.visible, (val) => {
  document.body.style.overflow = val ? 'hidden' : ''
})

const userStore = useUserStore()
const mode = ref('login')
const error = ref('')
const success = ref('')
const submitting = ref(false)
const form = reactive({ account: '', username: '', password: '', confirmPassword: '' })

function switchMode(newMode) {
  mode.value = newMode
  error.value = ''
  success.value = ''
}

async function handleLogin() {
  error.value = ''
  success.value = ''
  if (!form.account || !form.password) {
    error.value = '请填写用户名和密码'
    return
  }
  submitting.value = true
  try {
    await userStore.login(form.account, form.password)
    success.value = '登录成功！'
    setTimeout(() => {
      emit('close')
      success.value = ''
    }, 1000)
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}

async function handleRegister() {
  error.value = ''
  success.value = ''
  if (!form.username || form.username.length < 2) {
    error.value = '用户名至少 2 个字符'
    return
  }
  if (!form.password || form.password.length < 6) {
    error.value = '密码至少 6 位'
    return
  }
  if (form.password !== form.confirmPassword) {
    error.value = '两次输入的密码不一致'
    return
  }
  submitting.value = true
  try {
    await userStore.register(form.username, form.password)
    success.value = '注册成功！请登录'
    form.account = form.username
    form.password = ''
    form.confirmPassword = ''
    mode.value = 'login'
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}
</script>
