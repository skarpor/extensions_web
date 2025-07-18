<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'
import Toast from '@/utils/toast'
import 'vue-toastification/dist/index.css'

// 直接从 store 获取响应式状态
const userStore = useUserStore()
const { user, isLoggedIn } = storeToRefs(userStore)
const { logout, init } = userStore
let danmuSocket = ref(null)
let damu_container = ref(null)
// 添加用户信息悬浮显示状态
const showUserCard = ref(false)
// 添加默认头像（实际项目中应替换为您的默认头像路径）
const defaultAvatar =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%234e73df' d='M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z'/%3E%3C/svg%3E"
onMounted(async () => {
  try {
    Toast.info('欢迎访问！')
    // 初始化用户状态
    await init()
    await initWebSocket()
    // 页面加载时初始化
    damu_container = document.getElementById('danmu-container')
  } catch (error) {
    console.error('获取当前用户失败', error)
  }
})

async function initWebSocket() {
  if (danmuSocket && danmuSocket.readyState === WebSocket.OPEN) {
    return
  }

  danmuSocket = new WebSocket(
    `ws://${import.meta.env.VITE_HOST}:${import.meta.env.VITE_PORT}/api/danmu/ws`,
  )

  danmuSocket.onopen = () => {
    Toast.success('WebSocket连接已建立')
    // 可以发送初始消息或心跳
    sendHeartbeat()
  }

  danmuSocket.onmessage = (event) => {
    if (event.data === 'ping') {
      console.log('收到心跳')
      // 响应心跳
      return
    }
    const danmu = JSON.parse(event.data)
    createDanmu(danmu.text, danmu.color)
  }

  danmuSocket.onclose = () => {
    setTimeout(initWebSocket, 5000)
  }

  danmuSocket.onerror = (error) => {}
}

// 全局保存WebSocket引用

// 心跳保持
function sendHeartbeat() {
  if (danmuSocket && danmuSocket.readyState === WebSocket.OPEN) {
    danmuSocket.send('ping')
    setTimeout(sendHeartbeat, 25000) // 25秒一次心跳
  }
}

// 随机生成Y轴位置
function getRandomY() {
  return Math.floor(Math.random() * (window.innerHeight - 30))
}

// 创建弹幕元素
function createDanmu(text, color) {
  const danmu = document.createElement('div')
  danmu.className = 'danmu'
  danmu.textContent = text
  danmu.style.color = color
  danmu.style.left = `${window.innerWidth}px`
  danmu.style.top = `${getRandomY()}px`

  damu_container.appendChild(danmu)

  // 弹幕动画
  const duration = 10000 // 10秒
  const startTime = Date.now()

  function animate() {
    const elapsed = Date.now() - startTime
    const progress = elapsed / duration

    if (progress >= 1) {
      damu_container.removeChild(danmu)
      return
    }

    const x = window.innerWidth - (window.innerWidth + danmu.offsetWidth) * progress
    danmu.style.left = `${x}px`
    requestAnimationFrame(animate)
  }

  requestAnimationFrame(animate)
}
</script>

<template>
  <div class="app-container">
    <!-- 顶部导航栏 -->
    <div class="top-navbar">
      <div class="navbar-brand">数据查询系统</div>

      <ul class="navbar-nav1">
        <li class="nav-item">
          <RouterLink class="nav-link" to="/" :class="{ active: $route.path === '/' }">
            <i class="fas fa-home"></i> 首页
          </RouterLink>
        </li>
        <li class="nav-item">
          <RouterLink class="nav-link" to="/files" :class="{ active: $route.path === '/files' }">
            <i class="fas fa-file-alt"></i> 文件管理
          </RouterLink>
        </li>
        <li class="nav-item" v-if="isLoggedIn">
          <RouterLink
            class="nav-link"
            to="/extensions"
            :class="{ active: $route.path === '/extensions' }"
          >
            <i class="fas fa-cog"></i> 扩展配置
          </RouterLink>
        </li>
        <li class="nav-item">
          <RouterLink class="nav-link" to="/qrfile" :class="{ active: $route.path === '/qrfile' }">
            <i class="fas fa-qrcode"></i> 文件二维码
          </RouterLink>
        </li>
        <li class="nav-item">
          <RouterLink
            class="nav-link"
            to="/example"
            :class="{ active: $route.path === '/example' }"
          >
            <i class="fas fa-question-circle"></i> 帮助文档
          </RouterLink>
        </li>
        <li class="nav-item">
          <RouterLink
            class="nav-link"
            to="/modern-chat"
            :class="{ active: $route.path === '/modern-chat' }"
          >
            <i class="fas fa-comments"></i> 聊天
          </RouterLink>
        </li>
        <li class="nav-item">
          <RouterLink
            class="nav-link"
            to="/settings"
            :class="{ active: $route.path === '/settings' }"
          >
            <i class="fas fa-cog"></i> 设置
          </RouterLink>
        </li>
        <li class="nav-item" v-if="isLoggedIn && user && user.is_superuser">
          <RouterLink
            class="nav-link"
            to="/permissions"
            :class="{ active: $route.path === '/permissions' }"
          >
            <i class="fas fa-user-shield"></i> 权限管理
          </RouterLink>
        </li>
        <li class="nav-item">
          <RouterLink
            class="nav-link"
            to="/scheduler"
            :class="{ active: $route.path === '/scheduler' }"
          >
            <i class="fas fa-clock"></i> 定时任务
          </RouterLink>
        </li>
        <li class="nav-item">
          <RouterLink class="nav-link" to="/help" :class="{ active: $route.path === '/help' }">
            <i class="fas fa-question-circle"></i> 帮助中心
          </RouterLink>
        </li>
        <li class="nav-item">
          <RouterLink v-if="!isLoggedIn" class="nav-link" to="/login">登录</RouterLink>
          <a v-else class="nav-link" href="javascript:void(0)" @click="logout">退出</a>
        </li>
      </ul>
      <!-- 添加用户信息区域 -->
      <div
        class="user-info"
        v-if="isLoggedIn"
        @mouseenter="showUserCard = true"
        @mouseleave="showUserCard = false"
      >
        <span class="username">{{ user?.username || '用户' }}</span>

        <!-- 用户信息卡片 -->
        <div class="user-card" v-show="showUserCard">
          <div class="card-header">
            <div>
              <h3>{{ user?.username || '用户' }}</h3>
              <p>{{ user?.email || 'example@domain.com' }}</p>
            </div>
          </div>
          <div class="card-body">
            <RouterLink to="/profile" class="card-link">
              <i class="fas fa-user"></i> 个人资料
            </RouterLink>
            <RouterLink to="/settings" class="card-link">
              <i class="fas fa-cog"></i> 账户设置
            </RouterLink>
            <a href="javascript:void(0)" class="card-link logout-link" @click="logout">
              <i class="fas fa-sign-out-alt"></i> 退出登录
            </a>
          </div>
        </div>
      </div>
      <RouterLink v-else class="login-btn" to="/login">
        <i class="fas fa-sign-in-alt"></i> 登录
      </RouterLink>
    </div>

    <!-- 主容器 -->
    <div class="main-container">
      <RouterView />
    </div>
  </div>
</template>

<style>
/* 弹幕容器*/
#danmu-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999;
  pointer-events: none;
  overflow: hidden; /**/
}

/* 弹幕样式 */
.danmu {
  position: absolute;
  white-space: nowrap;
  font-size: 100px;
  color: red;
  text-shadow: 1px 1px 2px black;
}

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
  font-family:
    'Nunito',
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    Roboto,
    'Helvetica Neue',
    Arial,
    sans-serif;
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
  /* 固定在顶部 */
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  /* 四边圆角，圆角大小为10px，高度为50px */
  border-radius: 10px;
  height: 50px;
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  background-color: white;
  padding: 10px 20px;
  box-shadow: 0 2px 4px rgba(135, 154, 14, 0.1);
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

/* 添加用户信息样式 */
.user-info {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 12px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-left: auto;
}

.user-info:hover {
  background-color: rgba(78, 115, 223, 0.1);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #4e73df;
}

.username {
  font-weight: 600;
  color: #4e73df;
}

.user-card {
  position: absolute;
  top: 100%;
  right: 0;
  width: 280px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  overflow: hidden;
  margin-top: 10px;
}

.card-header {
  display: flex;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #4e73df 0%, #2e59d9 100%);
  color: white;
}

.card-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  border: 3px solid rgba(255, 255, 255, 0.3);
  margin-right: 15px;
}

.card-header h3 {
  margin: 0;
  font-size: 1.2rem;
}

.card-header p {
  margin: 5px 0 0;
  font-size: 0.85rem;
  opacity: 0.9;
}

.card-body {
  padding: 15px 0;
}

.card-link {
  display: flex;
  align-items: center;
  padding: 10px 20px;
  color: #5a5c69;
  text-decoration: none;
  transition: all 0.2s;
}

.card-link i {
  margin-right: 10px;
  width: 20px;
  text-align: center;
  color: #4e73df;
}

.card-link:hover {
  background-color: #f8f9fc;
  color: #4e73df;
}

.logout-link {
  color: #e74a3b;
}

.logout-link i {
  color: #e74a3b;
}

.logout-link:hover {
  background-color: rgba(231, 74, 59, 0.1);
  color: #e74a3b;
}

.login-btn {
  margin-left: auto;
  background: linear-gradient(135deg, #4e73df 0%, #2e59d9 100%);
  color: white;
  padding: 8px 15px;
  border-radius: 20px;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 2px 5px rgba(78, 115, 223, 0.3);
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(78, 115, 223, 0.4);
}

/* 优化导航栏按钮样式 */
.nav-link {
  background: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.9);
  transition: all 0.3s ease;
  padding: 8px 15px;
  border-radius: 20px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.nav-link.active {
  background: rgba(255, 255, 255, 0.3);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* 响应式调整 */
@media (max-width: 768px) {
  .user-info {
    padding: 5px;
  }

  .username {
    display: none;
  }

  .user-card {
    width: 250px;
    right: -10px;
  }

  .login-btn span {
    display: none;
  }

  .login-btn i {
    margin: 0;
  }
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
  display: flex;
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

.nav-link:hover {
  color: red;
  background-color: rgba(0, 131, 44, 0.1);
}

.nav-link.active {
  color: rgba(38,38,38,38);
  background-color: #4bc482;
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
  padding: 20px 30px; /* 增加水平内边距 */
  margin: 20px auto; /* 上下边距20px，左右自动居中 */
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

.col,
.col-md-3,
.col-md-4,
.col-md-6,
.col-md-8,
.col-md-9,
.col-md-12 {
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
