// stores/auth.js
import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { loginApi, logoutApi, refreshTokenApi, fetchUserInfo } from '@/api/auth'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
  // 状态
  const user = ref(null)
  const token = ref(null)
  const isLoggedIn = computed(() => !!user.value)

  // 方法
  const login = async (credentials) => {
    try {
      const response = await loginApi(credentials)
      if (response.access_token) {
        token.value = response.access_token
        if (response.user) {
          user.value = response.user
        } else {
          // 如果响应中没有用户信息，尝试获取
          await getUserInfo()
        }
      } else {
        throw new Error(response.detail || '登录失败')
      }
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
      localStorage.removeItem('token')
      // 跳转到登录页
      router.push('/login')
    }
  }

  // 获取用户信息
  const getUserInfo = async () => {
    if (token.value) {
      try {
        const userInfo = await fetchUserInfo()
        user.value = userInfo
        return userInfo
      } catch (error) {
        console.error('获取用户信息失败:', error)
        // 如果获取用户信息失败（可能是token过期），清除token
        token.value = null
        localStorage.removeItem('token')
        throw error
      }
    }
    return null
  }

  // 初始化时从本地存储恢复状态
  const init = async () => {
    const savedToken = localStorage.getItem('token')
    if (savedToken) {
      token.value = savedToken
      try {
        // 尝试获取用户信息
        await getUserInfo()
      } catch (error) {
        console.error('初始化用户状态失败:', error)
      }
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
    getUserInfo,
    init
  }
})