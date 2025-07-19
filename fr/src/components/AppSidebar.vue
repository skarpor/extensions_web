<template>
  <div class="sidebar">
    <div class="logo-container">
      <img src="../assets/logo.png" alt="Logo" class="logo" />
      <h1 class="app-title">智能助手系统</h1>
    </div>
    
    <div class="user-info" v-if="user">
      <div class="avatar">
        <img :src="user.avatar || '/img/default-avatar.png'" alt="用户头像" />
      </div>
      <div class="user-details">
        <h5>{{ user.username }}</h5>
        <p>{{ user.role || '用户' }}</p>
      </div>
    </div>
    
    <nav class="menu">
      <ul>
        <li>
          <router-link to="/dashboard" active-class="active">
            <i class="fas fa-home"></i>
            <span>仪表盘</span>
          </router-link>
        </li>
        
        <li>
          <router-link to="/chat" active-class="active">
            <i class="fas fa-comments"></i>
            <span>聊天</span>
          </router-link>
        </li>

        <li>
          <router-link to="/modern-chat" class="sidebar-item" active-class="active">
            <i class="fas fa-comment-dots"></i>
            <span class="sidebar-text">现代聊天室</span>
          </router-link>
        </li>
        
        <li>
          <router-link to="/extensions" active-class="active">
            <i class="fas fa-puzzle-piece"></i>
            <span>扩展管理</span>
          </router-link>
        </li>

        <li>
          <router-link to="/markdown" active-class="active">
            <i class="fas fa-edit"></i>
            <span>Markdown编辑器</span>
          </router-link>
        </li>
        
        <li v-if="canManageDatabase">
          <router-link to="/database" active-class="active">
            <i class="fas fa-database"></i>
            <span>数据库管理</span>
          </router-link>
        </li>
        
        <li>
          <router-link to="/files" active-class="active">
            <i class="fas fa-file-alt"></i>
            <span>文件管理</span>
          </router-link>
        </li>
        
        <li>
          <router-link to="/qrfile" class="sidebar-item" active-class="active">
            <i class="fas fa-qrcode"></i>
            <span class="sidebar-text">文件二维码</span>
          </router-link>
        </li>
        
        <li>
          <router-link to="/settings" active-class="active">
            <i class="fas fa-cog"></i>
            <span>系统设置</span>
          </router-link>
        </li>

        <li v-if="userStore.user?.is_superuser">
          <router-link to="/system-settings" class="sidebar-item" active-class="active">
            <i class="fas fa-server"></i>
            <span class="sidebar-text">高级设置</span>
          </router-link>
        </li>
      </ul>
    </nav>
    
    <div class="sidebar-footer">
      <button class="btn-logout" @click="logout">
        <i class="fas fa-sign-out-alt"></i>
        <span>退出登录</span>
      </button>
    </div>
  </div>
</template>

<script>
import { computed, ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

export default {
  name: 'AppSidebar',
  setup() {
    const router = useRouter();
    const user = ref(null);
    
    // 从本地存储中获取用户信息
    const loadUserInfo = () => {
      const userInfoStr = localStorage.getItem('userInfo');
      if (userInfoStr) {
        try {
          user.value = JSON.parse(userInfoStr);
        } catch (e) {
          console.error('解析用户信息失败:', e);
        }
      }
    };
    
    // 判断用户是否可以管理数据库
    const canManageDatabase = computed(() => {
      if (!user.value || !user.value.permissions) return false;
      return user.value.permissions.some(p => 
        p === 'manage_extension_db' || p === 'view_extension_db'
      );
    });
    
    // 退出登录
    const logout = () => {
      localStorage.removeItem('token');
      localStorage.removeItem('userInfo');
      router.push('/login');
    };
    
    onMounted(() => {
      loadUserInfo();
      
      // 监听用户信息变化
      window.addEventListener('storage', (e) => {
        if (e.key === 'userInfo') {
          loadUserInfo();
        }
      });
    });
    
    return {
      user,
      canManageDatabase,
      logout
    };
  }
};
</script>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  width: 250px;
  height: 100vh;
  background-color: #2c3e50;
  color: #ecf0f1;
  padding: 0;
  transition: all 0.3s;
  overflow-y: auto;
}

.logo-container {
  display: flex;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo {
  width: 40px;
  height: 40px;
  margin-right: 10px;
}

.app-title {
  font-size: 1.25rem;
  margin: 0;
  font-weight: 600;
}

.user-info {
  display: flex;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  overflow: hidden;
  margin-right: 15px;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-details h5 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.user-details p {
  margin: 0;
  font-size: 0.8rem;
  opacity: 0.8;
}

.menu {
  flex: 1;
  padding: 1rem 0;
}

.menu ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.menu li {
  margin-bottom: 0.5rem;
}

.menu a {
  display: flex;
  align-items: center;
  padding: 0.75rem 1.5rem;
  color: #ecf0f1;
  text-decoration: none;
  transition: all 0.2s;
}

.menu a:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.menu a.active {
  background-color: #3498db;
  color: white;
  font-weight: 500;
}

.menu a i {
  margin-right: 15px;
  width: 20px;
  text-align: center;
}

.sidebar-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-logout {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 0.75rem;
  background-color: rgba(231, 76, 60, 0.2);
  color: #e74c3c;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-logout:hover {
  background-color: rgba(231, 76, 60, 0.3);
}

.btn-logout i {
  margin-right: 10px;
}
</style> 