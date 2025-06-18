<template>
  <div class="auth-layout">
    <div class="auth-container">
      <div class="auth-logo">
        <img src="../assets/logo.png" alt="Logo" />
        <h1>智能助手系统</h1>
      </div>
      
      <div class="auth-card">
        <router-view></router-view>
      </div>
      
      <div class="auth-footer">
        <p>&copy; {{ currentYear }} 智能助手系统. 保留所有权利.</p>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue';

export default {
  name: 'AuthLayout',
  setup() {
    const currentYear = computed(() => new Date().getFullYear());
    
    return {
      currentYear
    };
  }
};
</script>

<style scoped>
.auth-layout {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f7fa;
  background-image: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.auth-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 460px;
  width: 100%;
  padding: 2rem;
}

.auth-logo {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 2rem;
}

.auth-logo img {
  width: 80px;
  height: 80px;
  margin-bottom: 1rem;
}

.auth-logo h1 {
  font-size: 1.75rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.auth-card {
  background-color: #fff;
  border-radius: 10px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
  width: 100%;
  padding: 2rem;
}

.auth-footer {
  margin-top: 2rem;
  text-align: center;
  color: #7f8c8d;
  font-size: 0.9rem;
}
</style> 