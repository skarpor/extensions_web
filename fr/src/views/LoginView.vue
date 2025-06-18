<template>
    <div class="login-container">
      <div class="login-form">
        <h2>登录</h2>
        <div class="alert alert-danger" v-if="error">{{ error }}</div>
        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label for="username">用户名</label>
            <input 
              type="text" 
              id="username" 
              v-model="form.username" 
              class="form-control" 
              required 
              placeholder="请输入用户名"
              autocomplete="username"
            />
          </div>
          <div class="form-group">
            <label for="password">密码</label>
            <input 
              type="password" 
              id="password" 
              v-model="form.password" 
              class="form-control" 
              required 
              placeholder="请输入密码"
              autocomplete="current-password"
            />
          </div>
          <div class="form-group form-check">
            <input type="checkbox" id="remember" v-model="form.remember" class="form-check-input" />
            <label for="remember" class="form-check-label">记住我</label>
          </div>
          <button type="submit" class="btn btn-primary" :disabled="loading">
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </form>
        <div class="links">
          <router-link to="/register">没有账号？注册</router-link>
        </div>
      </div>
    </div>
  </template>
  
  <script>
//引入全局的axios
import showToast from '@/utils/toast'
import {useUserStore} from '@/stores/user'
const auth = useUserStore()
export default {
    name: 'LoginView',
    data() {
      return {
        form: {
          username: '',
          password: '',
          //remember: false
        },
        loading: false,
        error: null
      }
    },
    methods: {
      async handleLogin() {
        this.loading = true
        this.error = null
        
        try {
          
          const formdata = new FormData()
          formdata.append('username', this.form.username)
          formdata.append('password', this.form.password)
          const response = await auth.login(formdata)
          if (response.access_token) {
            // 存储token
            localStorage.setItem('token', response.access_token)
            // 获取重定向URL或默认到首页
            const redirectUrl = this.$route.query.redirect || '/'
            showToast('跳转中...')
            this.$router.push(redirectUrl)
            showToast('登录成功')
          }
        } catch (error) { //后端不返回错误，只返回正常信息
          showToast(`登录失败, ${error}`  || '登录失败，请稍后再试')
        } finally {
          this.loading = false
        }
      }
    }
  }
  </script>
  
  <style scoped>
  .login-container {
    display: flex;
    width: 100%;
    justify-content: center;
    align-items: center;
    min-height: 80vh;
  }
  
  .login-form {
    width: 100%;
    max-width: 400px;
    padding: 2rem;
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }
  
  h2 {
    text-align: center;
    margin-bottom: 1.5rem;
    color: #2c3e50;
  }
  
  .form-group {
    margin-bottom: 1rem;
  }
  
  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
  }
  
  .form-control {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-size: 1rem;
  }
  
  .form-check {
    display: flex;
    align-items: center;
  }
  
  .form-check-input {
    margin-right: 0.5rem;
  }
  
  .btn {
    display: block;
    width: 100%;
    padding: 0.75rem;
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    margin-top: 1rem;
  }
  
  .btn:disabled {
    background-color: #95a5a6;
    cursor: not-allowed;
  }
  
  .links {
    margin-top: 1rem;
    text-align: center;
  }
  
  .links a {
    color: #3498db;
    text-decoration: none;
  }
  
  .links a:hover {
    text-decoration: underline;
  }
  
  .alert {
    padding: 0.75rem;
    margin-bottom: 1rem;
    border-radius: 4px;
    color: #721c24;
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
  }
  </style>