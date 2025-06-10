<script setup>
import { RouterLink, RouterView } from 'vue-router'
import { ref, onMounted } from 'vue'
import axios from '@/utils/axios'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const currentUser = ref(null)
const isLoggedIn = ref(false)

onMounted(async () => {
  try {
    showToast('欢迎访问！', 'success')
  } catch (error) {
    
  }
})

const logout = async () => {
  try {
    await axios.post('/api/auth/logout')
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('role')
    currentUser.value = null
    isLoggedIn.value = false
  } catch (error) {
    console.error('退出登录失败', error)
  }
}

// 显示提示信息
const showToast = (message, type = 'success') => {
  const toast = document.createElement('div')
  toast.className = `toast align-items-center text-white bg-${type} border-0`
  toast.setAttribute('role', 'alert')
  toast.setAttribute('aria-live', 'assertive')
  toast.setAttribute('aria-atomic', 'true')
  toast.style.minWidth = '250px'
  
  const toastBody = document.createElement('div')
  toastBody.className = 'd-flex'
  
  const messageDiv = document.createElement('div')
  messageDiv.className = 'toast-body'
  messageDiv.textContent = message
  
  const closeButton = document.createElement('button')
  closeButton.className = 'btn-close btn-close-white me-2 m-auto'
  closeButton.setAttribute('data-bs-dismiss', 'toast')
  closeButton.setAttribute('aria-label', 'Close')
  
  toastBody.appendChild(messageDiv)
  toastBody.appendChild(closeButton)
  toast.appendChild(toastBody)
  
  const toastContainer = document.getElementById('toast-container')
  toastContainer.appendChild(toast)
  
  const bsToast = new bootstrap.Toast(toast)
  bsToast.show()
  
  toast.addEventListener('hidden.bs.toast', () => {
    toast.remove()
  })
}
</script>

<template>
  <div class="app-container">
    <!-- 顶部导航栏 -->
    <div class="top-navbar">
      <div class="navbar-brand">数据查询系统</div>

      <ul class="navbar-nav1">
        <li class="nav-item">
          <RouterLink class="nav-link" to="/" :class="{ 'active': $route.path === '/' }">
            <i class="fas fa-home"></i> 首页
          </RouterLink>
        </li>
        <li class="nav-item">
          <RouterLink class="nav-link" to="/file-manager" :class="{ 'active': $route.path === '/file-manager' }">
            <i class="fas fa-file-alt"></i> 文件管理
          </RouterLink>
        </li>
        <li class="nav-item" v-if="isLoggedIn && currentUser?.role === 'admin'">
          <RouterLink class="nav-link" to="/extensions" :class="{ 'active': $route.path === '/extensions' }">
            <i class="fas fa-cog"></i> 扩展配置
          </RouterLink>
        </li>
        <li class="nav-item">
          <RouterLink class="nav-link" to="/example" :class="{ 'active': $route.path === '/example' }">
            <i class="fas fa-question-circle"></i> 帮助文档
          </RouterLink>
        </li>
        <li class="nav-item">
          <RouterLink class="nav-link" to="/chat" :class="{ 'active': $route.path === '/chat' }">
            <i class="fas fa-comments"></i> 聊天
          </RouterLink>
        </li>
        <li class="nav-item">
          <RouterLink class="nav-link" to="/settings" :class="{ 'active': $route.path === '/settings' }">
            <i class="fas fa-cog"></i> 设置
          </RouterLink>
        </li>
        <li class="nav-item">
          <RouterLink class="nav-link" to="/scheduler" :class="{ 'active': $route.path === '/scheduler' }">
            <i class="fas fa-clock"></i> 定时任务
          </RouterLink>
        </li>
        <li class="nav-item">
          <RouterLink class="nav-link" to="/help" :class="{ 'active': $route.path === '/help' }">
            <i class="fas fa-question-circle"></i> 帮助中心
          </RouterLink>
        </li>
        <li class="nav-item">
          <RouterLink v-if="!isLoggedIn" class="nav-link" to="/login">登录</RouterLink>
          <a v-else class="nav-link" href="javascript:void(0)" @click="logout">退出</a>
        </li>
      </ul>
    </div>
  
  
    <!-- 主容器 -->
    <div class="main-container">
      <RouterView />
    </div>

  
    <!-- Toast容器 -->
    <div id="toast-container" class="position-fixed top-0 end-0 p-3">
    </div>
  </div>
<!-- 操作反馈Toast -->
<div class="position-fixed bottom-0 end-0 p-3" style="z-index: 11">
    <div id="liveToast" class="toast hide" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="toast-header">
            <i class="fas fa-info-circle me-2"></i>
            <strong class="me-auto" id="toastTitle">操作结果</strong>
            <small>刚刚</small>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body" id="toastMessage">
            操作已完成。
        </div>
    </div>
</div>
</template>

<style>
#toast-container {
  z-index: 9999;
  /* fixed如何 */
  height: 100px;
}
:root {
  --primary-color: #4e73df;
  --secondary-color: #f8f9fc;
  --accent-color: #2e59d9;
  --text-color: #5a5c69;
  --border-color: #d1d3e2;
}

body {
  background-color: #f8f9fa;
  font-family: 'Nunito', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  margin: 0;
  padding: 0;
  min-height: 100vh;
}



.app-container {
  display: grid;
  /* 左右宽度拉满 */
  justify-items: stretch;
  grid-template-rows: 1fr 0fr;
  min-height: 100vh;
}

.top-navbar {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  background-color: var(--primary-color);
  padding: 10px 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position:fixed;
  top: 0;
  z-index: 100;
  width: 100%;
  box-sizing: border-box;
}

.navbar-brand {
  color: white;
  font-weight: bold;
  font-size: 1.2rem;
  margin: 0;
  padding: 0;
}

.navbar-nav1 {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.nav-item {
  display: flex;
  flex-direction: row;
}

.nav-link {
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  padding: 5px 10px;
  border-radius: 4px;
  white-space: nowrap; /* 防止文字换行 */
}


/* 响应式设计 */
@media (max-width: 768px) {
  .top-navbar {
    flex-direction: row; /* 保持水平排列 */
    flex-wrap: wrap;
    padding: 10px;
  }

  .navbar-nav1 {
    margin-top: 10px;
    justify-content: flex-end;
    gap: 5px;
    flex-wrap: wrap;
    flex-direction: row; /* 确保在小屏幕上仍然水平排列 */
  }
  
  .nav-item {
    display: inline-block;
  }
}


.nav-link {
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  transition: color 0.2s;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 1rem;
  white-space: nowrap; /* 防止文本换行 */
}
/* 导航栏中的图标 */
.nav-link i {
  margin-right: 5px;
}


.main-container {
  display:flex;
  flex-direction: row;
  flex: 2;
  background: white;
  padding: 20px;
  margin: 20px;
  border-radius: 8px;
  box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
  border: 1px solid var(--border-color);
  /* max-width: 1200px; */
  width: 100%;
  /* width: calc(100% - 40px); */
  align-self: center;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
  color: var(--primary-color);
  padding-bottom: 15px;
  border-bottom: 1px solid var(--border-color);
}

.action-btn {
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background-color: var(--accent-color);
  transform: translateY(-1px);
}






.nav-link:hover {
  color: white;
  background-color: rgba(255, 255, 255, 0.1);
}

.nav-link.active {
  color: white;
  background-color: rgba(255, 255, 255, 0.2);
}

.partial-content {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}



/* 页面内容的通用样式 */
.main-container {
  flex: 1;
  background: white;
  padding: 20px 30px;  /* 增加水平内边距 */
  margin: 20px auto;   /* 上下边距20px，左右自动居中 */
  border-radius: 8px;
  box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
  border: 1px solid var(--border-color);
  max-width: 1200px;
  width: calc(100% - 40px);
}

/* 确保页面内容响应式布局 */
.row {
  display: flex;
  flex-wrap: wrap;
  margin-right: -15px;
  margin-left: -15px;
  width: 100%;
}

.col, .col-md-3, .col-md-4, .col-md-6, .col-md-8, .col-md-9, .col-md-12 {
  position: relative;
  width: 100%;
  padding-right: 15px;
  padding-left: 15px;
}


/* 卡片布局优化 */
.card {
  width: 100%;
  margin-bottom: 20px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
  overflow: hidden;
}

.card-header {
  padding: 0.75rem 1.25rem;
  background-color: var(--secondary-color);
  border-bottom: 1px solid var(--border-color);
}

.card-body {
  padding: 1.25rem;
}

/* 表格响应式布局 */
.table-responsive {
  display: block;
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.table {
  width: 100%;
  margin-bottom: 1rem;
  color: var(--text-color);
  border-collapse: collapse;
}

.table th,
.table td {
  padding: 0.75rem;
  vertical-align: top;
  border-top: 1px solid var(--border-color);
}

.chat-container {
  display: flex;
  height: calc(100vh - 160px);
  min-height: 400px;
}


</style>