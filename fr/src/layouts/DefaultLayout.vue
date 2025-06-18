<template>
  <div class="app-layout">
    <app-sidebar />
    
    <div class="main-content">
      <header class="app-header">
        <div class="search-container">
          <div class="search-input">
            <i class="fas fa-search"></i>
            <input type="text" placeholder="搜索..." />
          </div>
        </div>
        
        <div class="header-actions">
          <div class="notifications">
            <button class="btn-icon">
              <i class="fas fa-bell"></i>
              <span class="badge" v-if="notificationCount > 0">{{ notificationCount }}</span>
            </button>
          </div>
          
          <div class="user-dropdown">
            <router-link to="/profile" class="user-link">
              <img :src="userAvatar" alt="User Avatar" class="avatar" />
              <span class="username">{{ username }}</span>
            </router-link>
          </div>
        </div>
      </header>
      
      <main class="content">
        <router-view></router-view>
      </main>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import AppSidebar from '../components/AppSidebar.vue';

export default {
  name: 'DefaultLayout',
  components: {
    AppSidebar
  },
  setup() {
    const notificationCount = ref(0);
    const userInfo = ref({});
    
    // 从本地存储中获取用户信息
    const loadUserInfo = () => {
      const userInfoStr = localStorage.getItem('userInfo');
      if (userInfoStr) {
        try {
          userInfo.value = JSON.parse(userInfoStr);
        } catch (e) {
          console.error('解析用户信息失败:', e);
        }
      }
    };
    
    // 计算用户头像
    const userAvatar = computed(() => {
      return userInfo.value.avatar || '/img/default-avatar.png';
    });
    
    // 计算用户名
    const username = computed(() => {
      return userInfo.value.username || '用户';
    });
    
    // 模拟获取通知数量
    const fetchNotifications = () => {
      // 这里应该从API获取实际的通知数量
      notificationCount.value = Math.floor(Math.random() * 5);
    };
    
    onMounted(() => {
      loadUserInfo();
      fetchNotifications();
      
      // 监听用户信息变化
      window.addEventListener('storage', (e) => {
        if (e.key === 'userInfo') {
          loadUserInfo();
        }
      });
    });
    
    return {
      notificationCount,
      userAvatar,
      username
    };
  }
};
</script>

<style scoped>
.app-layout {
  display: flex;
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #f5f5f5;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
  padding: 0 1.5rem;
  background-color: #ffffff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.search-container {
  flex: 1;
  max-width: 400px;
}

.search-input {
  position: relative;
  width: 100%;
}

.search-input i {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #aaa;
}

.search-input input {
  width: 100%;
  padding: 0.5rem 0.5rem 0.5rem 2rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.header-actions {
  display: flex;
  align-items: center;
}

.notifications {
  position: relative;
  margin-right: 1.5rem;
}

.btn-icon {
  background: none;
  border: none;
  font-size: 1.2rem;
  color: #555;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.btn-icon:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background-color: #e74c3c;
  color: white;
  font-size: 0.7rem;
  padding: 0.1rem 0.4rem;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
}

.user-link {
  display: flex;
  align-items: center;
  text-decoration: none;
  color: #333;
  padding: 0.5rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.user-link:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  margin-right: 0.5rem;
  object-fit: cover;
}

.username {
  font-size: 0.9rem;
  font-weight: 500;
}

.content {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
}
</style> 