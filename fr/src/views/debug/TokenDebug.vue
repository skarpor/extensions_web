<template>
  <div class="token-debug">
    <h2>Token调试信息</h2>
    
    <el-card class="debug-card">
      <h3>用户Store状态</h3>
      <p><strong>isLoggedIn:</strong> {{ userStore.isLoggedIn }}</p>
      <p><strong>user:</strong> {{ userStore.user ? JSON.stringify(userStore.user, null, 2) : 'null' }}</p>
      <p><strong>token:</strong> {{ userStore.token ? userStore.token.substring(0, 50) + '...' : 'null' }}</p>
    </el-card>
    
    <el-card class="debug-card">
      <h3>LocalStorage</h3>
      <p><strong>token:</strong> {{ localStorage_token ? localStorage_token.substring(0, 50) + '...' : 'null' }}</p>
      <p><strong>access_token:</strong> {{ localStorage_access_token ? localStorage_access_token.substring(0, 50) + '...' : 'null' }}</p>
    </el-card>
    
    <el-card class="debug-card">
      <h3>SessionStorage</h3>
      <p><strong>token:</strong> {{ sessionStorage_token ? sessionStorage_token.substring(0, 50) + '...' : 'null' }}</p>
      <p><strong>access_token:</strong> {{ sessionStorage_access_token ? sessionStorage_access_token.substring(0, 50) + '...' : 'null' }}</p>
    </el-card>
    
    <el-card class="debug-card">
      <h3>操作</h3>
      <el-button @click="refreshData" type="primary">刷新数据</el-button>
      <el-button @click="testLogin" type="success">测试登录</el-button>
      <el-button @click="clearTokens" type="danger">清除所有Token</el-button>
    </el-card>
    
    <el-card class="debug-card">
      <h3>测试结果</h3>
      <pre>{{ testResult }}</pre>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import axios from '@/utils/axios'

const userStore = useUserStore()

const localStorage_token = ref(null)
const localStorage_access_token = ref(null)
const sessionStorage_token = ref(null)
const sessionStorage_access_token = ref(null)
const testResult = ref('')

const refreshData = () => {
  localStorage_token.value = localStorage.getItem('token')
  localStorage_access_token.value = localStorage.getItem('access_token')
  sessionStorage_token.value = sessionStorage.getItem('token')
  sessionStorage_access_token.value = sessionStorage.getItem('access_token')
  
  testResult.value = `刷新时间: ${new Date().toLocaleString()}\n`
  testResult.value += `用户Store Token: ${userStore.token ? '存在' : '不存在'}\n`
  testResult.value += `用户Store 登录状态: ${userStore.isLoggedIn}\n`
}

const testLogin = async () => {
  try {
    testResult.value = '正在测试登录...\n'
    
    const credentials = {
      username: 'admin',
      password: '123'
    }
    
    const response = await userStore.login(credentials)
    testResult.value += `登录成功: ${JSON.stringify(response, null, 2)}\n`
    
    // 刷新数据
    refreshData()
    
    ElMessage.success('登录成功')
  } catch (error) {
    testResult.value += `登录失败: ${error.message}\n`
    ElMessage.error('登录失败: ' + error.message)
  }
}

const clearTokens = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('access_token')
  sessionStorage.removeItem('token')
  sessionStorage.removeItem('access_token')
  
  userStore.logout()
  
  refreshData()
  
  ElMessage.info('所有Token已清除')
}

onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.token-debug {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.debug-card {
  margin-bottom: 20px;
}

.debug-card h3 {
  margin-top: 0;
  color: #409eff;
}

.debug-card p {
  margin: 8px 0;
  font-family: monospace;
  background: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
  word-break: break-all;
}

pre {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 300px;
  overflow-y: auto;
}
</style>
