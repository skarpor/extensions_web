// stores/auth.js
import { defineStore } from 'pinia'
import { ref,computed,watch } from 'vue'
import { loginApi, logoutApi, refreshTokenApi, fetchUserInfo } from '@/api/auth'
import router from '@/router'

export const useUserStore = defineStore('auth', () => {
  // 状态
  const user = ref(null)
  const token = ref(null)
  const isLoggedIn = computed(() => !!token.value)

  // 方法
  const login = async (credentials) => {
    try {
    const response = await loginApi(credentials)
    user.value = response.user
    token.value = response.access_token
    return response
} catch (error) {
      throw error // 让调用者处理错误
    }
  }

  const logout = async () => {
    try {
      await logoutApi()
    } finally {
      // 无论后端登出是否成功，都清除前端状态
      user.value = null
      token.value = null
      // 跳转到登录页
      router.push('/login')
    }
  }

  // 初始化时从本地存储恢复状态
  const init = () => {
    const savedToken = localStorage.getItem('token')
    if (savedToken) {
      token.value = savedToken
      // 可以在这里添加获取用户信息的逻辑
    }
  }

  // 监听 token 变化并持久化
  watch(token, (newToken) => {
    if (newToken) {
      localStorage.setItem('token', newToken)
    } else {
      localStorage.removeItem('token')
    }
  }, { immediate: true })

  return {
    user,
    token,
    isLoggedIn,
    login,
    logout,
    init
  }
})