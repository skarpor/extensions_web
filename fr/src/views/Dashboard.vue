<template>
  <div class="dashboard">
    <h1>控制面板</h1>
    
    <v-row>
      <!-- 统计卡片 -->
      <v-col cols="12" md="3">
        <v-card class="stat-card">
          <v-card-text>
            <div class="stat-title">用户总数</div>
            <div class="stat-value">{{ stats.users_count || 0 }}</div>
            <v-icon class="stat-icon">mdi-account-group</v-icon>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="3">
        <v-card class="stat-card">
          <v-card-text>
            <div class="stat-title">扩展总数</div>
            <div class="stat-value">{{ stats.extensions_count || 0 }}</div>
            <v-icon class="stat-icon">mdi-puzzle</v-icon>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="3">
        <v-card class="stat-card">
          <v-card-text>
            <div class="stat-title">文件总数</div>
            <div class="stat-value">{{ stats.files_count || 0 }}</div>
            <v-icon class="stat-icon">mdi-file-multiple</v-icon>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="3">
        <v-card class="stat-card">
          <v-card-text>
            <div class="stat-title">聊天消息</div>
            <div class="stat-value">{{ stats.messages_count || 0 }}</div>
            <v-icon class="stat-icon">mdi-message-text</v-icon>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    
    <v-row class="mt-4">
      <!-- 系统状态 -->
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title>系统状态</v-card-title>
          <v-card-text>
            <div class="status-item">
              <div class="status-label">系统版本:</div>
              <div class="status-value">{{ systemInfo.version || '未知' }}</div>
            </div>
            <div class="status-item">
              <div class="status-label">运行状态:</div>
              <div class="status-value">
                <v-chip
                  color="success"
                  text-color="white"
                  small
                >
                  正常运行
                </v-chip>
              </div>
            </div>
            <div class="status-item">
              <div class="status-label">启动时间:</div>
              <div class="status-value">{{ formatDate(systemInfo.start_time) }}</div>
            </div>
            <div class="status-item">
              <div class="status-label">CPU使用率:</div>
              <div class="status-value">{{ systemInfo.cpu_usage || '0' }}%</div>
            </div>
            <div class="status-item">
              <div class="status-label">内存使用:</div>
              <div class="status-value">{{ formatMemory(systemInfo.memory_usage) }}</div>
            </div>
            <div class="status-item">
              <div class="status-label">磁盘使用:</div>
              <div class="status-value">{{ formatStorage(systemInfo.disk_usage) }}</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <!-- 最近活动 -->
      <v-col cols="12" md="8">
        <v-card>
          <v-card-title class="d-flex justify-space-between">
            <span>最近活动</span>
            <v-btn small text color="primary" @click="refreshActivity">刷新</v-btn>
          </v-card-title>
          <v-card-text>
            <v-data-table
              :headers="activityHeaders"
              :items="recentActivity"
              :items-per-page="5"
              hide-default-footer
              class="activity-table"
            >
              <template v-slot:item.timestamp="{ item }">
                {{ formatDate(item.timestamp) }}
              </template>
              <template v-slot:item.type="{ item }">
                <v-chip
                  :color="getActivityTypeColor(item.type)"
                  text-color="white"
                  small
                >
                  {{ item.type }}
                </v-chip>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    
    <v-row class="mt-4">
      <!-- 快速操作 -->
      <v-col cols="12">
        <v-card>
          <v-card-title>快速操作</v-card-title>
          <v-card-text>
            <div class="quick-actions">
              <v-btn
                color="primary"
                class="mx-2"
                @click="$router.push('/extensions')"
              >
                <v-icon left>mdi-puzzle</v-icon>
                管理扩展
              </v-btn>
              
              <v-btn
                color="info"
                class="mx-2"
                @click="$router.push('/files')"
              >
                <v-icon left>mdi-folder</v-icon>
                文件管理
              </v-btn>
              
              <v-btn
                color="success"
                class="mx-2"
                @click="$router.push('/settings')"
              >
                <v-icon left>mdi-cog</v-icon>
                系统设置
              </v-btn>
              
              <v-btn
                color="warning"
                class="mx-2"
                @click="$router.push('/profile')"
              >
                <v-icon left>mdi-account</v-icon>
                个人资料
              </v-btn>
              
              <v-btn
                color="error"
                class="mx-2"
                @click="$router.push('/help')"
              >
                <v-icon left>mdi-help-circle</v-icon>
                帮助中心
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script>
import { getDashboardData, getSystemInfo, getRecentActivity } from '@/api/dashboard'
import Toast from '@/utils/toast'
export default {
  name: 'Dashboard',
  data() {
    return {
      loading: false,
      stats: {
        users_count: 0,
        extensions_count: 0,
        files_count: 0,
        messages_count: 0
      },
      systemInfo: {
        version: '',
        start_time: null,
        cpu_usage: 0,
        memory_usage: 0,
        disk_usage: 0
      },
      recentActivity: [],
      activityHeaders: [
        { text: '时间', value: 'timestamp' },
        { text: '用户', value: 'username' },
        { text: '类型', value: 'type' },
        { text: '详情', value: 'description' }
      ]
    }
  },
  async created() {
    await this.fetchData()
  },
  methods: {
    async fetchData() {
      this.loading = true
      try {
        await Promise.all([
          this.fetchStats(),
          this.fetchSystemInfo(),
          this.fetchRecentActivity()
        ])
      } catch (error) {
        console.error('获取控制面板数据失败', error)
        Toast.error('获取控制面板数据失败')
      } finally {
        this.loading = false
      }
    },
    async fetchStats() {
      try {
        const response = await getDashboardData()
        console.log(response)
        this.stats = response
      } catch (error) {
        console.error('获取统计数据失败', error)
      }
    },
    async fetchSystemInfo() {
      try {
        const response = await getSystemInfo()
        this.systemInfo = response
      } catch (error) {
        console.error('获取系统信息失败', error)
      }
    },
    async fetchRecentActivity() {
      try {
        const response = await getRecentActivity()
        this.recentActivity = response
      } catch (error) {
        console.error('获取最近活动失败', error)
      }
    },
    async refreshActivity() {
      try {
        await this.fetchRecentActivity()
        Toast.success('活动列表已刷新')
      } catch (error) {
        console.error('刷新活动列表失败', error)
        Toast.error('刷新活动列表失败')
      }
    },
    formatDate(dateString) {
      if (!dateString) return '未知'
      
      const date = new Date(dateString)
      return new Intl.DateTimeFormat('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }).format(date)
    },
    formatMemory(bytes) {
      if (bytes === undefined || bytes === null) return '未知'
      
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
      if (bytes === 0) return '0 B'
      
      const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)), 10)
      if (i === 0) return `${bytes} ${sizes[i]}`
      
      return `${(bytes / (1024 ** i)).toFixed(2)} ${sizes[i]}`
    },
    formatStorage(bytes) {
      return this.formatMemory(bytes)
    },
    getActivityTypeColor(type) {
      const typeColors = {
        login: 'success',
        logout: 'grey',
        register: 'info',
        file_upload: 'primary',
        file_delete: 'error',
        extension_install: 'purple',
        extension_uninstall: 'red',
        setting_change: 'orange',
        user_update: 'blue'
      }
      
      return typeColors[type.toLowerCase()] || 'primary'
    }
  }
}
</script>

<style scoped>
.dashboard {
  padding: 20px;width: 100%;
}

.stat-card {
  position: relative;
  overflow: hidden;
  height: 100%;
}

.stat-title {
  font-size: 1rem;
  color: rgba(0, 0, 0, 0.6);
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  margin: 10px 0;
}

.stat-icon {
  position: absolute;
  right: 10px;
  bottom: 10px;
  font-size: 3rem;
  opacity: 0.2;
}

.status-item {
  display: flex;
  margin-bottom: 12px;
}

.status-label {
  font-weight: bold;
  width: 120px;
  flex-shrink: 0;
}

.status-value {
  flex-grow: 1;
}

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.activity-table {
  border: none;
}
</style> 