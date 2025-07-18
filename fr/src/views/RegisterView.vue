<template>
    <div class="register-container">
      <div class="register-form">
        <h2>注册</h2>
        <div class="alert alert-danger" v-if="error">{{ error }}</div>
        <form @submit.prevent="handleRegister">
          <div class="form-group">
            <label for="username">用户名</label>
            <input 
              type="text" 
              id="username" 
              v-model="form.username" 
              class="form-control" 
              required 
              placeholder="请输入用户名"
            />
            <small class="form-text text-muted">用户名长度至少3个字符，只能包含字母和数字</small>
          </div>
          <div class="form-group">
            <label for="nickname">昵称</label>
            <input 
              type="text" 
              id="nickname" 
              v-model="form.nickname" 
              class="form-control" 
              placeholder="请输入昵称（可选）"
            />
          </div>
          <div class="form-group">
            <label for="email">邮箱</label>
            <input 
              type="email" 
              id="email" 
              v-model="form.email" 
              class="form-control" 
              placeholder="请输入邮箱（可选）"
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
            />
            <small class="form-text text-muted">密码长度至少6个字符</small>
          </div>
          <div class="form-group">
            <label for="confirmPassword">确认密码</label>
            <input 
              type="password" 
              id="confirmPassword" 
              v-model="form.confirmPassword" 
              class="form-control" 
              required 
              placeholder="请再次输入密码"
            />
          </div>
          <button type="submit" class="btn btn-primary" :disabled="loading">
            {{ loading ? '注册中...' : '注册' }}
          </button>
        </form>
        <div class="links">
          <router-link to="/login">已有账号？登录</router-link>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { registerApi } from '@/api/auth'
  import Toast from '@/utils/toast'
  export default {
    name: 'RegisterView',
    data() {
      return {
        form: {
          username: '',
          nickname: '',
          email: '',
          password: '',
          confirmPassword: '',
          toast:Toast
        },
        loading: false,
        error: null
      }
    },
    methods: {
      async handleRegister() {
        // 表单验证
        if (this.form.password !== this.form.confirmPassword) {
          this.error = '两次输入的密码不一致'
          return
        }
        
        // if (this.form.username.length < 3) {
        //   this.error = '用户名长度至少3个字符'
        //   return
        // }
        
        // if (!/^[a-zA-Z0-9]+$/.test(this.form.username)) {
        //   this.error = '用户名只能包含字母和数字'
        //   return
        // }
        
        // if (this.form.password.length < 6) {
        //   this.error = '密码长度至少6个字符'
        //   return
        // }
        
        this.loading = true
        this.error = null
        
        try {
          const response = await registerApi({
            username: this.form.username,
            nickname: this.form.nickname || this.form.username,
            email: this.form.email || undefined,
            password: this.form.password
          })
          if (response && response.data) {
            // 注册成功，跳转到登录页
            Toast.success(`${response.data.username} 注册成功！`)
            this.$router.push({
              name: 'login',
              query: { registered: 'success' }
            })
          }
        } catch (error) {
          console.error('注册错误', error)
          this.error = error.response?.data?.detail || '注册失败，请稍后再试'
        } finally {
          this.loading = false
        }
      }
    }
  }
  </script>
  
  <style scoped>
  .register-container {
    display: flex;
    width: 100%;
    justify-content: center;
    align-items: center;
    min-height: 80vh;
    padding: 2rem 0;
  }
  
  .register-form {
    width: 100%;
    max-width: 500px;
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
  
  .form-text {
    display: block;
    margin-top: 0.25rem;
    font-size: 0.875rem;
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