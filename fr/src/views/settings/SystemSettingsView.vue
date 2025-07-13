<template>
  <div class="system-settings">
    <div class="page-header">
      <h2>系统设置</h2>
      <p class="page-description">管理系统配置参数和运行环境</p>
    </div>

    <!-- 系统状态卡片 -->
    <el-card class="status-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon class="header-icon"><Monitor /></el-icon>
          <span>系统状态</span>
        </div>
      </template>
      
      <div class="status-grid">
        <div class="status-item">
          <div class="status-label">系统状态</div>
          <div class="status-value">
            <el-tag :type="expiryInfo.expired ? 'danger' : 'success'" size="large">
              {{ expiryInfo.expired ? '已过期' : '正常运行' }}
            </el-tag>
          </div>
        </div>
        
        <div class="status-item" v-if="!expiryInfo.expired">
          <div class="status-label">剩余天数</div>
          <div class="status-value">
            <span class="days-left">{{ expiryInfo.days_left }}</span> 天
          </div>
        </div>
        
        <div class="status-item" v-if="configStatus.initialized_at">
          <div class="status-label">初始化时间</div>
          <div class="status-value">
            {{ formatDate(configStatus.initialized_at) }}
          </div>
        </div>
        
        <div class="status-item" v-if="configStatus.updated_at">
          <div class="status-label">最后更新</div>
          <div class="status-value">
            {{ formatDate(configStatus.updated_at) }}
          </div>
        </div>
      </div>
    </el-card>

    <!-- 设置表单 -->
    <el-card class="settings-card" shadow="hover" v-loading="loading">
      <template #header>
        <div class="card-header">
          <el-icon class="header-icon"><Setting /></el-icon>
          <span>配置参数</span>
          <div class="header-actions">
            <el-button type="primary" @click="saveSettings" :loading="saving">
              <el-icon><Check /></el-icon>
              保存设置
            </el-button>
            <el-button @click="resetSettings">
              <el-icon><RefreshLeft /></el-icon>
              重置
            </el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab" class="settings-tabs">
        <!-- 基础配置 -->
        <el-tab-pane label="基础配置" name="basic">
          <div class="settings-section">
            <h3>应用配置</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="应用名称">
                  <el-input v-model="settings.APP_NAME" placeholder="请输入应用名称" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="调试模式">
                  <el-switch v-model="settings.DEBUG" />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="监听地址">
                  <el-input v-model="settings.HOST" placeholder="0.0.0.0" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="监听端口">
                  <el-input-number v-model="settings.PORT" :min="1" :max="65535" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <div class="settings-section">
            <h3>国际化配置</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="时区">
                  <el-select v-model="settings.TIMEZONE" placeholder="选择时区">
                    <el-option label="Asia/Shanghai" value="Asia/Shanghai" />
                    <el-option label="UTC" value="UTC" />
                    <el-option label="America/New_York" value="America/New_York" />
                    <el-option label="Europe/London" value="Europe/London" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="语言">
                  <el-select v-model="settings.LANGUAGE" placeholder="选择语言">
                    <el-option label="简体中文" value="zh-CN" />
                    <el-option label="English" value="en-US" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <!-- 安全配置 -->
        <el-tab-pane label="安全配置" name="security">
          <div class="settings-section">
            <h3>认证配置</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="令牌过期时间(分钟)">
                  <el-input-number v-model="settings.ACCESS_TOKEN_EXPIRE_MINUTES" :min="1" :max="10080" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="加密算法">
                  <el-select v-model="settings.ALGORITHM" placeholder="选择算法">
                    <el-option label="HS256" value="HS256" />
                    <el-option label="HS384" value="HS384" />
                    <el-option label="HS512" value="HS512" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-form-item label="系统密钥">
              <div class="secret-key-section">
                <el-tag :type="settings.SECRET_KEY_SET ? 'success' : 'warning'">
                  {{ settings.SECRET_KEY_SET ? '已设置' : '未设置' }}
                </el-tag>
                <el-button type="primary" size="small" @click="showSecretKeyDialog = true">
                  {{ settings.SECRET_KEY_SET ? '更新密钥' : '设置密钥' }}
                </el-button>
              </div>
            </el-form-item>
          </div>
        </el-tab-pane>

        <!-- 数据库配置 -->
        <el-tab-pane label="数据库配置" name="database">
          <div class="settings-section">
            <h3>数据库连接</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="数据库类型">
                  <el-select v-model="settings.DATABASE_TYPE" placeholder="选择数据库类型">
                    <el-option label="SQLite" value="sqlite" />
                    <el-option label="MySQL" value="mysql" />
                    <el-option label="PostgreSQL" value="postgresql" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="连接URL">
                  <el-input v-model="settings.DATABASE_URL" placeholder="数据库连接字符串" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <!-- 文件配置 -->
        <el-tab-pane label="文件配置" name="files">
          <div class="settings-section">
            <h3>文件上传</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="上传目录">
                  <el-input v-model="settings.UPLOAD_DIR" placeholder="文件上传目录" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="最大文件大小(MB)">
                  <el-input-number 
                    v-model="maxFileSizeMB" 
                    :min="1" 
                    :max="1024"
                    @change="updateMaxFileSize"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-form-item label="允许的文件扩展名">
              <el-tag
                v-for="(ext, index) in settings.ALLOWED_EXTENSIONS"
                :key="index"
                closable
                @close="removeExtension(index)"
                class="extension-tag"
              >
                {{ ext }}
              </el-tag>
              <el-input
                v-if="inputVisible"
                ref="inputRef"
                v-model="inputValue"
                size="small"
                @keyup.enter="handleInputConfirm"
                @blur="handleInputConfirm"
                class="extension-input"
              />
              <el-button v-else size="small" @click="showInput">
                <el-icon><Plus /></el-icon>
                添加扩展名
              </el-button>
            </el-form-item>
          </div>

          <div class="settings-section">
            <h3>扩展管理</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="扩展目录">
                  <el-input v-model="settings.EXTENSIONS_DIR" placeholder="扩展存储目录" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="允许上传扩展">
                  <el-switch v-model="settings.ALLOW_EXTENSION_UPLOAD" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <!-- 用户配置 -->
        <el-tab-pane label="用户配置" name="users">
          <div class="settings-section">
            <h3>用户注册</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="允许用户注册">
                  <el-switch v-model="settings.ALLOW_REGISTER" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="默认用户角色">
                  <el-input v-model="settings.DEFAULT_USER_ROLE" placeholder="新用户默认角色" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <!-- 邮件配置 -->
        <el-tab-pane label="邮件配置" name="email">
          <div class="settings-section">
            <h3>SMTP设置</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="SMTP服务器">
                  <el-input v-model="settings.SMTP_HOST" placeholder="smtp.example.com" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="SMTP端口">
                  <el-input-number v-model="settings.SMTP_PORT" :min="1" :max="65535" />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="用户名">
                  <el-input v-model="settings.SMTP_USER" placeholder="邮箱用户名" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="密码">
                  <el-input v-model="settings.SMTP_PASSWORD" type="password" placeholder="邮箱密码" />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-form-item label="启用TLS">
              <el-switch v-model="settings.SMTP_TLS" />
            </el-form-item>
          </div>
        </el-tab-pane>

        <!-- 日志配置 -->
        <el-tab-pane label="日志配置" name="logging">
          <div class="settings-section">
            <h3>日志设置</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="日志级别">
                  <el-select v-model="settings.LOG_LEVEL" placeholder="选择日志级别">
                    <el-option label="DEBUG" value="DEBUG" />
                    <el-option label="INFO" value="INFO" />
                    <el-option label="WARNING" value="WARNING" />
                    <el-option label="ERROR" value="ERROR" />
                    <el-option label="CRITICAL" value="CRITICAL" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="日志文件路径">
                  <el-input v-model="settings.LOG_FILE" placeholder="日志文件存储路径" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 密钥设置对话框 -->
    <el-dialog
      v-model="showSecretKeyDialog"
      title="设置系统密钥"
      width="500px"
    >
      <el-form :model="secretKeyForm" label-width="120px">
        <el-form-item label="新密钥" required>
          <el-input
            v-model="secretKeyForm.secret_key"
            type="password"
            placeholder="请输入至少32位的密钥"
            show-password
          />
          <div class="form-tip">
            密钥用于JWT令牌签名，请妥善保管。建议使用随机生成的强密钥。
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="generateSecretKey">
            <el-icon><Refresh /></el-icon>
            生成随机密钥
          </el-button>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showSecretKeyDialog = false">取消</el-button>
        <el-button type="primary" @click="updateSecretKey" :loading="updatingKey">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Monitor,
  Setting,
  Check,
  RefreshLeft,
  Plus,
  Refresh
} from '@element-plus/icons-vue'
import axios from 'axios'

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const updatingKey = ref(false)
const activeTab = ref('basic')

// 系统状态
const expiryInfo = ref({
  expired: false,
  days_left: 0,
  expiry_date: null,
  initialized_at: null
})

const configStatus = ref({
  config_file_exists: false,
  config_dir: '',
  initialized_at: null,
  updated_at: null,
  total_config_items: 0
})

// 设置数据
const settings = reactive({
  APP_NAME: '',
  DEBUG: false,
  HOST: '0.0.0.0',
  PORT: 8000,
  ACCESS_TOKEN_EXPIRE_MINUTES: 30,
  ALGORITHM: 'HS256',
  SECRET_KEY_SET: false,
  DATABASE_URL: '',
  DATABASE_TYPE: 'sqlite',
  UPLOAD_DIR: 'data/uploads',
  MAX_FILE_SIZE: 104857600,
  ALLOWED_EXTENSIONS: [],
  EXTENSIONS_DIR: 'data/extensions',
  ALLOW_EXTENSION_UPLOAD: true,
  ALLOW_REGISTER: true,
  DEFAULT_USER_ROLE: 'user',
  LOG_LEVEL: 'INFO',
  LOG_FILE: 'data/logs/app.log',
  SMTP_HOST: '',
  SMTP_PORT: 587,
  SMTP_USER: '',
  SMTP_PASSWORD: '',
  SMTP_TLS: true,
  TIMEZONE: 'Asia/Shanghai',
  LANGUAGE: 'zh-CN'
})

// 原始设置（用于重置）
const originalSettings = ref({})

// 密钥设置
const showSecretKeyDialog = ref(false)
const secretKeyForm = reactive({
  secret_key: ''
})

// 文件扩展名输入
const inputVisible = ref(false)
const inputValue = ref('')
const inputRef = ref()

// 计算属性
const maxFileSizeMB = computed({
  get: () => Math.round(settings.MAX_FILE_SIZE / (1024 * 1024)),
  set: (value) => {
    settings.MAX_FILE_SIZE = value * 1024 * 1024
  }
})

// 方法
const loadSettings = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/system/settings')
    Object.assign(settings, response.data)
    originalSettings.value = JSON.parse(JSON.stringify(response.data))
    ElMessage.success('设置加载成功')
  } catch (error) {
    console.error('加载设置失败:', error)
    ElMessage.error('加载设置失败')
  } finally {
    loading.value = false
  }
}

const loadExpiryInfo = async () => {
  try {
    const response = await axios.get('/api/system/expiry-info')
    expiryInfo.value = response.data
  } catch (error) {
    console.error('加载过期信息失败:', error)
  }
}

const loadConfigStatus = async () => {
  try {
    const response = await axios.get('/api/system/config-status')
    configStatus.value = response.data
  } catch (error) {
    console.error('加载配置状态失败:', error)
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    await axios.put('/api/system/settings', settings)
    originalSettings.value = JSON.parse(JSON.stringify(settings))
    ElMessage.success('设置保存成功')

    // 重新加载状态信息
    await loadConfigStatus()
  } catch (error) {
    console.error('保存设置失败:', error)
    ElMessage.error('保存设置失败')
  } finally {
    saving.value = false
  }
}

const resetSettings = () => {
  ElMessageBox.confirm(
    '确定要重置所有设置吗？这将恢复到上次保存的状态。',
    '确认重置',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    Object.assign(settings, originalSettings.value)
    ElMessage.success('设置已重置')
  }).catch(() => {
    // 用户取消
  })
}

const updateMaxFileSize = (value) => {
  settings.MAX_FILE_SIZE = value * 1024 * 1024
}

const removeExtension = (index) => {
  settings.ALLOWED_EXTENSIONS.splice(index, 1)
}

const showInput = () => {
  inputVisible.value = true
  nextTick(() => {
    inputRef.value?.focus()
  })
}

const handleInputConfirm = () => {
  if (inputValue.value) {
    let ext = inputValue.value.trim()
    if (!ext.startsWith('.')) {
      ext = '.' + ext
    }
    if (!settings.ALLOWED_EXTENSIONS.includes(ext)) {
      settings.ALLOWED_EXTENSIONS.push(ext)
    }
  }
  inputVisible.value = false
  inputValue.value = ''
}

const generateSecretKey = () => {
  // 生成32位随机密钥
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < 64; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  secretKeyForm.secret_key = result
}

const updateSecretKey = async () => {
  if (!secretKeyForm.secret_key || secretKeyForm.secret_key.length < 32) {
    ElMessage.error('密钥长度至少为32位')
    return
  }

  updatingKey.value = true
  try {
    await axios.put('/api/system/settings/secret-key', {
      secret_key: secretKeyForm.secret_key
    })

    settings.SECRET_KEY_SET = true
    showSecretKeyDialog.value = false
    secretKeyForm.secret_key = ''
    ElMessage.success('密钥更新成功')
  } catch (error) {
    console.error('更新密钥失败:', error)
    ElMessage.error('更新密钥失败')
  } finally {
    updatingKey.value = false
  }
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 生命周期
onMounted(async () => {
  await Promise.all([
    loadSettings(),
    loadExpiryInfo(),
    loadConfigStatus()
  ])
})
</script>

<style scoped>
.system-settings {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
  width: 100%;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 28px;
  font-weight: 600;
}

.page-description {
  margin: 0;
  color: #909399;
  font-size: 16px;
}

/* 状态卡片 */
.status-card {
  margin-bottom: 24px;
  border-radius: 12px;
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-icon {
  font-size: 18px;
  color: #409eff;
}

.header-actions {
  margin-left: auto;
  display: flex;
  gap: 12px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.status-item {
  text-align: center;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
}

.status-label {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 8px;
}

.status-value {
  font-size: 18px;
  font-weight: 600;
}

.days-left {
  font-size: 24px;
  font-weight: 700;
  color: #ffd700;
}

/* 设置卡片 */
.settings-card {
  border-radius: 12px;
  overflow: hidden;
}

.settings-tabs {
  margin-top: 20px;
}

.settings-section {
  margin-bottom: 32px;
  padding: 24px;
  background: #fafbfc;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.settings-section h3 {
  margin: 0 0 20px 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
  padding-bottom: 12px;
  border-bottom: 2px solid #409eff;
}

.settings-section .el-form-item {
  margin-bottom: 20px;
}

.settings-section .el-form-item__label {
  font-weight: 500;
  color: #606266;
}

/* 密钥设置 */
.secret-key-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.form-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

/* 扩展名标签 */
.extension-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

.extension-input {
  width: 120px;
  margin-right: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .system-settings {
    padding: 12px;
  }

  .status-grid {
    grid-template-columns: 1fr;
  }

  .header-actions {
    flex-direction: column;
    gap: 8px;
  }

  .settings-section {
    padding: 16px;
  }
}

/* 标签页样式 */
.settings-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
}

.settings-tabs :deep(.el-tabs__nav-wrap) {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 4px;
}

.settings-tabs :deep(.el-tabs__item) {
  border-radius: 6px;
  transition: all 0.3s ease;
}

.settings-tabs :deep(.el-tabs__item.is-active) {
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 表单样式增强 */
.settings-section .el-input,
.settings-section .el-select,
.settings-section .el-input-number {
  width: 100%;
}

.settings-section .el-switch {
  --el-switch-on-color: #409eff;
}

/* 卡片悬停效果 */
.status-card:hover,
.settings-card:hover {
  transform: translateY(-2px);
  transition: all 0.3s ease;
}

/* 按钮样式 */
.header-actions .el-button {
  border-radius: 6px;
  font-weight: 500;
}

.header-actions .el-button--primary {
  background: linear-gradient(135deg, #409eff 0%, #36a3f7 100%);
  border: none;
}

.header-actions .el-button--primary:hover {
  background: linear-gradient(135deg, #36a3f7 0%, #2b8ce6 100%);
}
</style>
