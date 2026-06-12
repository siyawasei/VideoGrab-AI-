<template>
  <div class="min-h-screen">
    <Navbar @showLogin="showLogin = true" />
    <router-view />
    <FooterSection />
    <LoginModal :visible="showLogin" @close="showLogin = false" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Navbar from '@/components/Navbar.vue'
import FooterSection from '@/components/FooterSection.vue'
import LoginModal from '@/components/LoginModal.vue'

const showLogin = ref(false)
</script>
