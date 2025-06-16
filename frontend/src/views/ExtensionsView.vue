<template>
  <div class="extensions-container">
    <h1>扩展管理</h1>
    
    <div class="actions mb-4">
      <button class="btn btn-primary me-2" @click="showInstallModal = true">
        <i class="fas fa-plus-circle"></i> 安装扩展
      </button>
      <button class="btn btn-secondary me-2" @click="refreshExtensions">
        <i class="fas fa-sync"></i> 刷新
      </button>
      <RouterLink to="/extension-query" class="btn btn-info">
        <i class="fas fa-search"></i> 扩展查询界面
      </RouterLink>
    </div>
    
    <div class="alert alert-info" v-if="!extensions.length">
      <p>没有已安装的扩展。</p>
    </div>
    
    <div class="extensions-grid" v-else>
      <div 
        v-for="extension in extensions" 
        :key="extension.id" 
        class="extension-card"
        :class="{ disabled: !extension.enabled }"
      >
        <div class="extension-header">
          <h3>{{ extension.name }}</h3>
          <div class="extension-version">{{ extension.version || '1.0' }}</div>
        </div>
        <div class="extension-body">
          <p>{{ extension.description }}</p>
          <div class="extension-meta">
            <div class="extension-author">创建者: {{ extension.creator_id || '系统' }}</div>
            <div class="extension-updated">更新时间: {{ formatDate(extension.updated_at || extension.created_at) }}</div>
          </div>
          <div class="extension-features">
            <span v-if="extension.has_config_form" class="feature-badge">
              <i class="fas fa-cog"></i> 配置
            </span>
            <span v-if="extension.has_query_form" class="feature-badge">
              <i class="fas fa-search"></i> 查询
            </span>
            <span v-if="extension.show_in_home" class="feature-badge">
              <i class="fas fa-home"></i> 首页显示
            </span>
            <span class="feature-badge" :class="{'active': extension.enabled}">
              <i class="fas fa-power-off"></i> {{ extension.enabled ? '已启用' : '已禁用' }}
            </span>
          </div>
        </div>
        <div class="extension-footer">
          <div class="form-check form-switch">
            <input 
              class="form-check-input" 
              type="checkbox" 
              :id="`extension-${extension.id}`" 
              v-model="extension.enabled"
              @change="toggleExtension(extension)"
            >
            <label class="form-check-label" :for="`extension-${extension.id}`">
              {{ extension.enabled ? '已启用' : '已禁用' }}
            </label>
          </div>
          <div class="extension-actions">
            <button class="btn btn-sm btn-outline-primary" @click="configureExtension(extension)" v-if="extension.has_config_form">
              <i class="fas fa-cog"></i>
            </button>
            <RouterLink :to="`/extensions/${extension.id}`" class="btn btn-sm btn-outline-info">
              <i class="fas fa-info-circle"></i>
            </RouterLink>
            <button class="btn btn-sm btn-outline-danger" @click="uninstallExtension(extension)">
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 安装扩展模态框 -->
    <div class="modal" v-if="showInstallModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">安装扩展</h5>
            <button type="button" class="btn-close" @click="showInstallModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">扩展信息</label>
              <div class="mb-3">
                <label for="extensionName" class="form-label">扩展名称</label>
                <input 
                  type="text" 
                  id="extensionName" 
                  class="form-control" 
                  v-model="extensionName"
                  placeholder="输入扩展名称"
                />
              </div>
              
              <div class="mb-3">
                <label for="extensionDescription" class="form-label">扩展描述</label>
                <textarea 
                  id="extensionDescription" 
                  class="form-control" 
                  v-model="extensionDescription"
                  placeholder="输入扩展描述"
                  rows="3"
                ></textarea>
              </div>
              
              <div class="mb-3">
                <label for="executionMode" class="form-label">执行模式</label>
                <select id="executionMode" class="form-select" v-model="executionMode">
                  <option value="sync">同步</option>
                  <option value="async">异步</option>
                </select>
              </div>
              
              <div class="mb-3">
                <label for="renderType" class="form-label">渲染类型</label>
                <select id="renderType" class="form-select" v-model="renderType">
                  <option value="html">HTML</option>
                  <option value="table">表格</option>
                  <option value="image">图片</option>
                  <option value="file">文件</option>
                  <option value="text">文本</option>
                </select>
              </div>
              
              <div class="form-check mb-3">
                <input 
                  type="checkbox" 
                  id="showInHome" 
                  class="form-check-input" 
                  v-model="showInHome"
                />
                <label class="form-check-label" for="showInHome">在首页显示</label>
              </div>
            </div>
            
            <div class="mb-3">
              <label for="extensionFile" class="form-label">选择扩展文件</label>
              <input 
                type="file" 
                id="extensionFile" 
                class="form-control" 
                @change="handleFileSelect"
                accept=".py"
              />
            </div>
            
            <div class="install-progress" v-if="installProgress > 0">
              <div class="progress">
                <div 
                  class="progress-bar" 
                  role="progressbar" 
                  :style="{ width: installProgress + '%' }" 
                  :aria-valuenow="installProgress" 
                  aria-valuemin="0" 
                  aria-valuemax="100"
                >
                  {{ installProgress }}%
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showInstallModal = false">取消</button>
            <button 
              type="button" 
              class="btn btn-primary" 
              @click="installExtension" 
              :disabled="!canInstall"
            >
              安装
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 配置扩展模态框 -->
    <div class="modal" v-if="showConfigModal">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">配置扩展: {{ currentExtension?.name }}</h5>
            <button type="button" class="btn-close" @click="showConfigModal = false"></button>
          </div>
          <div class="modal-body">
            <div v-if="configLoading" class="text-center">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
              <p class="mt-2">加载配置...</p>
            </div>
            <div v-else-if="configError" class="alert alert-danger">
              {{ configError }}
            </div>
            <div v-else>
              <div v-for="(field, key) in configFields" :key="key" class="mb-3">
                <label :for="`config-${key}`" class="form-label">{{ field.label }}</label>
                
                <input 
                  v-if="field.type === 'text' || field.type === 'number' || field.type === 'password'" 
                  :type="field.type" 
                  :id="`config-${key}`" 
                  class="form-control" 
                  v-model="configValues[key]"
                  :placeholder="field.placeholder"
                />
                
                <textarea 
                  v-else-if="field.type === 'textarea'" 
                  :id="`config-${key}`" 
                  class="form-control" 
                  v-model="configValues[key]"
                  :placeholder="field.placeholder"
                  rows="3"
                ></textarea>
                
                <select 
                  v-else-if="field.type === 'select'" 
                  :id="`config-${key}`" 
                  class="form-select" 
                  v-model="configValues[key]"
                >
                  <option v-for="option in field.options" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
                
                <div class="form-check" v-else-if="field.type === 'checkbox'">
                  <input 
                    type="checkbox" 
                    :id="`config-${key}`" 
                    class="form-check-input" 
                    v-model="configValues[key]"
                  />
                  <label class="form-check-label" :for="`config-${key}`">{{ field.checkboxLabel }}</label>
                </div>
                
                <small class="form-text text-muted" v-if="field.help">{{ field.help }}</small>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showConfigModal = false">取消</button>
            <button 
              type="button" 
              class="btn btn-primary" 
              @click="saveConfig" 
              :disabled="configLoading"
            >
              保存
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { 
  getExtensions, 
  createExtension, 
  updateExtension, 
  deleteExtension, 
  getExtensionConfig, 
  saveExtensionConfig 
} from '@/api/extension';
import Toast from '@/utils/toast'

export default {
  name: 'ExtensionsView',
  data() {
    return {
      extensions: [],
      showInstallModal: false,
      showConfigModal: false,
      extensionFile: null,
      extensionName: '',
      extensionDescription: '',
      executionMode: 'sync',
      renderType: 'html',
      showInHome: true,
      installProgress: 0,
      currentExtension: null,
      configFields: {},
      configValues: {},
      configLoading: false,
      configError: null
    }
  },
  computed: {
    canInstall() {
      return this.extensionFile && this.extensionName
    }
  },
  created() {
    this.fetchExtensions()
  },
  methods: {
    async fetchExtensions() {
      try {
        const response = await getExtensions()
        this.extensions = response.data
      } catch (error) {
        console.error('获取扩展列表失败', error)
        Toast.error('获取扩展列表失败: ' + (error.response?.data?.detail || error.message))
      }
    },
    
    refreshExtensions() {
      this.fetchExtensions()
    },
    
    handleFileSelect(event) {
      this.extensionFile = event.target.files[0]
    },
    
    async installExtension() {
      if (!this.extensionFile) {
        Toast.error('请选择扩展文件')
        return
      }
      
      if (!this.extensionName) {
        Toast.error('请输入扩展名称')
        return
      }
      
      try {
        const formData = new FormData()
        formData.append('file', this.extensionFile)
        formData.append('name', this.extensionName)
        formData.append('description', this.extensionDescription)
        formData.append('execution_mode', this.executionMode)
        formData.append('render_type', this.renderType)
        formData.append('show_in_home', this.showInHome)
        
        await createExtension(formData)
        
        
        Toast.success('扩展安装成功')
        this.showInstallModal = false
        this.extensionFile = null
        this.extensionName = ''
        this.extensionDescription = ''
        this.executionMode = 'sync'
        this.renderType = 'html'
        this.showInHome = true
        this.installProgress = 0
        this.fetchExtensions()
      } catch (error) {
        console.error('安装扩展失败', error)
        Toast.error('安装扩展失败: ' + (error.response?.data?.detail || error.message))
      }
    },
    
    async toggleExtension(extension) {
      try {
        await updateExtension(extension.id, {
          enabled: extension.enabled
        })
        Toast.success(`扩展已${extension.enabled ? '启用' : '禁用'}`)
      } catch (error) {
        console.error('切换扩展状态失败', error)
        extension.enabled = !extension.enabled // 恢复状态
        Toast.error('切换扩展状态失败: ' + (error.response?.data?.detail || error.message))
      }
    },
    
    async configureExtension(extension) {
      this.currentExtension = extension
      this.configLoading = true
      this.configError = null
      this.showConfigModal = true
      
      try {
        const response = await getExtensionConfig(extension.id)
        this.configFields = response.data.fields || {}
        this.configValues = response.data.values || {}
      } catch (error) {
        console.error('获取扩展配置失败', error)
        this.configError = '获取扩展配置失败: ' + (error.response?.data?.detail || error.message)
      } finally {
        this.configLoading = false
      }
    },
    
    async saveConfig() {
      if (!this.currentExtension) return
      
      try {
        await saveExtensionConfig(this.currentExtension.id, this.configValues)
        
        Toast.success('配置保存成功')
        this.showConfigModal = false
        this.currentExtension = null
        this.configFields = {}
        this.configValues = {}
      } catch (error) {
        console.error('保存扩展配置失败', error)
        Toast.error('保存扩展配置失败: ' + (error.response?.data?.detail || error.message))
      }
    },
    
    async uninstallExtension(extension) {
      if (!confirm(`确定要卸载扩展 ${extension.name} 吗？这将删除所有相关数据。`)) {
        return
      }
      
      try {
        await deleteExtension(extension.id)
        Toast.success('扩展已卸载')
        this.fetchExtensions()
      } catch (error) {
        console.error('卸载扩展失败', error)
        Toast.error('卸载扩展失败: ' + (error.response?.data?.detail || error.message))
      }
    },
    
    formatDate(timestamp) {
      if (!timestamp) return '-'
      
      const date = new Date(timestamp)
      return date.toLocaleString()
    }
  }
}
</script>

<style scoped>
.extensions-container {
  width: 100%;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 2rem;
}

h1 {
  margin-bottom: 2rem;
  color: #2c3e50;
}

.extensions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.extension-card {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.extension-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.extension-card.disabled {
  opacity: 0.6;
}

.extension-header {
  padding: 1rem;
  background-color: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.extension-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #2c3e50;
}

.extension-version {
  font-size: 0.875rem;
  color: #6c757d;
  background-color: #e9ecef;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.extension-body {
  padding: 1rem;
}

.extension-body p {
  margin-bottom: 1rem;
}

.extension-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.875rem;
  color: #6c757d;
  margin-bottom: 1rem;
}

.extension-features {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.feature-badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  background-color: #e9ecef;
  color: #6c757d;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.feature-badge.active {
  background-color: #28a745;
  color: white;
}

.extension-footer {
  padding: 1rem;
  border-top: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.extension-actions {
  display: flex;
  gap: 0.5rem;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-dialog {
  width: 100%;
  max-width: 500px;
  margin: 1.75rem auto;
}

.modal-dialog.modal-lg {
  max-width: 800px;
}

.modal-content {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e9ecef;
}

.modal-title {
  margin: 0;
}

.btn-close {
  background: transparent;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
}

.modal-body {
  padding: 1rem;
}

.modal-footer {
  padding: 1rem;
  border-top: 1px solid #e9ecef;
  display: flex;
  justify-content: flex-end;
}

.install-progress {
  margin-top: 1rem;
}

.progress {
  height: 10px;
  border-radius: 5px;
  overflow: hidden;
}
</style>