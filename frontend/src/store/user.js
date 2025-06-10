// 用户状态管理
import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null,
    isLoggedIn: false,
    isAdmin: false,
    isSuperAdmin: false,
    isLoading: false,
    error: null,
  }),
  actions: {
    async login(username, password) {
      this.isLoading = true
      this.error = null
      try {
        const response = await axios.post('/api/auth/login', {
          username,
          password,
        })
        this.user = response.data
        this.isLoggedIn = true
        this.isAdmin = response.data.is_admin
        this.isSuperAdmin = response.data.is_super_admin
      } catch (error) {
        this.error = error.response.data.message || '登录失败'
      } finally {
        this.isLoading = false
      }
    },
    async logout() {
      this.user = null
      this.isLoggedIn = false
      this.isAdmin = false
      this.isSuperAdmin = false
    },
    async register(username, email, password) {
      this.isLoading = true
      this.error = null
      try {
        const response = await axios.post('/api/auth/register', {
          username,
          email,
          password,
        })
        this.user = response.data
        this.isLoggedIn = true
      } catch (error) {
        this.error = error.response.data.message || '注册失败'
      } finally {
        this.isLoading = false
      }
    },
    async getUser() {
      try {
        const response = await axios.get('/api/auth/user')
        this.user = response.data
        this.isLoggedIn = true
        this.isAdmin = response.data.is_admin
        this.isSuperAdmin = response.data.is_super_admin
      } catch (error) {
        this.error = error.response.data.message || '获取用户信息失败'
      }
    },
    async updateUser(userData) {
      try {
        const response = await axios.put('/api/auth/user', userData)
        this.user = response.data
      } catch (error) {
        this.error = error.response.data.message || '更新用户信息失败'
      }
    },
    async deleteUser() {
      try {
        await axios.delete('/api/auth/user')
        this.user = null
        this.isLoggedIn = false
        this.isAdmin = false
        this.isSuperAdmin = false
      } catch (error) {
        this.error = error.response.data.message || '删除用户失败'
      }
    },
  },
  getters: {
    isAuthenticated: (state) => state.isLoggedIn,
    isAdmin: (state) => state.isAdmin,
    isSuperAdmin: (state) => state.isSuperAdmin,
    isLoading: (state) => state.isLoading,
    error: (state) => state.error,
  },
})




