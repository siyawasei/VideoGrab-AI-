<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center p-4" @click.self="$emit('close')">
    <div class="absolute inset-0 bg-black/60 backdrop-blur-sm"></div>

    <div class="relative glass-card !p-8 w-full max-w-md animate-fade-in-up">
      <button @click="$emit('close')" class="absolute top-4 right-4 text-gray-400 hover:text-white text-xl">&times;</button>

      <!-- Tab 切换 -->
      <div class="flex gap-4 mb-6">
        <button @click="mode = 'login'" class="pb-2 text-sm font-medium transition-colors"
                :class="mode === 'login' ? 'text-white border-b-2 border-purple-primary' : 'text-gray-400'">登录</button>
        <button @click="mode = 'register'" class="pb-2 text-sm font-medium transition-colors"
                :class="mode === 'register' ? 'text-white border-b-2 border-purple-primary' : 'text-gray-400'">注册</button>
      </div>

      <!-- 登录表单 -->
      <form v-if="mode === 'login'" @submit.prevent="handleLogin" class="space-y-4">
        <input v-model="form.username" type="text" placeholder="用户名"
               class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-purple-primary/50 transition-colors placeholder-gray-500" />
        <input v-model="form.password" type="password" placeholder="密码"
               class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-purple-primary/50 transition-colors placeholder-gray-500" />
        <p v-if="error" class="text-red-400 text-sm">{{ error }}</p>
        <button type="submit" :disabled="submitting" class="gradient-btn w-full !py-3">{{ submitting ? '登录中...' : '登录' }}</button>
      </form>

      <!-- 注册表单 -->
      <form v-else @submit.prevent="handleRegister" class="space-y-4">
        <input v-model="form.username" type="text" placeholder="用户名"
               class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-purple-primary/50 transition-colors placeholder-gray-500" />
        <input v-model="form.email" type="email" placeholder="邮箱"
               class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-purple-primary/50 transition-colors placeholder-gray-500" />
        <input v-model="form.password" type="password" placeholder="密码"
               class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-purple-primary/50 transition-colors placeholder-gray-500" />
        <p v-if="error" class="text-red-400 text-sm">{{ error }}</p>
        <button type="submit" :disabled="submitting" class="gradient-btn w-full !py-3">{{ submitting ? '注册中...' : '注册' }}</button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useUserStore } from '@/stores/user'

defineProps({ visible: Boolean })
defineEmits(['close'])

const userStore = useUserStore()
const mode = ref('login')
const error = ref('')
const submitting = ref(false)
const form = reactive({ username: '', email: '', password: '' })

async function handleLogin() {
  error.value = ''
  submitting.value = true
  try {
    await userStore.login(form.username, form.password)
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}

async function handleRegister() {
  error.value = ''
  submitting.value = true
  try {
    await userStore.register(form.username, form.email, form.password)
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}
</script>
