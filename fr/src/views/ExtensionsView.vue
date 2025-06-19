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
          <p>{{ extension.description || '暂无描述' }}</p>
          <div class="extension-meta">
            <div class="extension-author">创建者: {{ extension.creator.nickname || '系统' }}</div>
            <div class="extension-updated">更新时间: {{ formatDate(extension.updated_at || extension.created_at) }}</div>
          </div>
          <div class="extension-features">
            <span v-if="extension.has_config_form" class="feature-badge">
              <i class="fas fa-cog"></i> 配置
            </span>
            <span v-if="extension.has_query_form" class="feature-badge">
              <i class="fas fa-search"></i> 查询
            </span>
            <span class="feature-badge" :class="{'active': extension.enabled}">
              <i class="fas fa-power-off"></i> {{ extension.enabled ? '已启用' : '已禁用' }}
            </span>
            <span class="feature-badge" :class="{'active': extension.show_in_home}">
              <i class="fas fa-home"></i> {{ extension.show_in_home ? '首页显示' : '首页隐藏' }}
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
              @change="toggleExtension(extension, 'enabled')"
            >
            <label class="form-check-label" :for="`extension-${extension.id}`">
              {{ extension.enabled ? '启用' : '禁用' }}
            </label>
          </div>
          <div class="form-check form-switch">
            <input 
              class="form-check-input" 
              type="checkbox" 
              :id="`extension-${extension.id}-show-in-home`" 
              v-model="extension.show_in_home"
              @change="toggleExtension(extension, 'show_in_home')"
            >
            <label class="form-check-label" :for="`extension-${extension.id}-show-in-home`">
              {{ extension.show_in_home ? '显示' : '隐藏' }}
            </label>
          </div>
          <div class="extension-actions">
            <button class="btn btn-sm btn-outline-primary" @click="configureExtension(extension)">
              <i class="fas fa-cog"></i>
            </button>
            <!-- <RouterLink :to="`/extensions/${extension.id}`" class="btn btn-sm btn-outline-info">
              <i class="fas fa-info-circle"></i>
            </RouterLink> -->
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
            <form id="uploadForm" enctype="multipart/form-data">
              <div class="mb-3">
                <label for="name" class="form-label">名称</label>
                <input 
                  type="text" 
                  id="name" 
                  class="form-control" 
                  v-model="extensionName"
                  placeholder="输入扩展名称"
                  required
                />
              </div>
              
              <div class="mb-3">
                <label for="description" class="form-label">描述信息</label>
                <textarea 
                  id="description" 
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
              
              <div class="form-check form-switch mb-3">
                <input 
                  type="checkbox" 
                  id="showinindex" 
                  class="form-check-input" 
                  v-model="showInHome"
                  checked
                />
                <label class="form-check-label" for="showinindex">首页显示</label>
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
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showInstallModal = false">取消</button>
            <button 
              type="button" 
              class="btn btn-primary" 
              @click="installExtension" 
              :disabled="!canInstall"
            >
              <i class="fas fa-upload me-2"></i>安装扩展
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
              <form id="extensionConfigForm" @submit.prevent="saveConfig">
                <input type="hidden" name="id" :value="currentExtension?.id">
                
                <div class="card mb-3">
                  <div class="card-header">基本设置</div>
                  <div class="card-body">
                    <div class="mb-3">
                      <label class="form-label">名称</label>
                      <input type="text" class="form-control" v-model="configValues.name" required>
                    </div>
                    <div class="mb-3">
                      <label class="form-label">描述</label>
                      <textarea class="form-control" v-model="configValues.description"></textarea>
                    </div>
                    <div class="mb-3">
                      <label class="form-label">API端点</label>
                      <input type="text" class="form-control" v-model="configValues.endpoint" required>
                    </div>
                    <div class="mb-3">
                      <label class="form-label">返回值类型</label>
                      <select class="form-select" v-model="configValues.return_type">
                        <option value="html">HTML</option>
                        <option value="table">JSON列表</option>
                      </select>
                    </div>
                    <div class="form-check form-switch mb-3">
                      <input class="form-check-input" type="checkbox" id="showinindex" v-model="configValues.showinindex">
                      <label class="form-check-label" for="showinindex">首页显示</label>
                    </div>
                    
                    <div class="form-check form-switch mb-3">
                      <input class="form-check-input" type="checkbox" id="enabled" v-model="configValues.enabled">
                      <label class="form-check-label" for="enabled">启用扩展</label>
                    </div>
                  </div>
                </div>
                
                <!-- 扩展文档 -->
                <div class="card mb-3" v-if="extensionDocumentation">
                  <div class="card-header">使用说明</div>
                  <div class="card-body">
                    <h4>模块说明</h4>
                    <div class="bg-light p-3 rounded" v-html="parsedModuleDoc"></div>
                    <div class="docs-container">
                      <h4>方法说明</h4>
                      <ul>
                        <li><strong>execute_query:</strong> <span v-html="parsedExecuteQueryDoc"></span></li>
                        <li><strong>get_config_form:</strong> <span v-html="parsedGetConfigFormDoc"></span></li>
                        <li><strong>get_default_config:</strong> <span v-html="parsedGetDefaultConfigDoc"></span></li>
                      </ul>
                    </div>
                  </div>
                </div>
                
                <!-- 扩展配置表单 -->
                <div class="card mb-3" v-if="currentExtension?.has_config_form">
                  <div class="card-header">扩展设置</div>
                  <div class="card-body">
                    <div v-html="configFormHtml"></div>
                  </div>
                </div>
                
                <div class="d-flex justify-content-end">
                  <button type="button" class="btn btn-secondary" @click="showConfigModal = false">取消</button>
                  <button type="submit" class="btn btn-primary ms-2">
                    <i class="fas fa-save me-2"></i>保存配置
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { 
  getExtension,
  getExtensions, 
  createExtension, 
  updateExtension, 
  deleteExtension, 
  getExtensionConfig, 
  saveExtensionConfig 
} from '@/api/extension';
import Toast from '@/utils/toast'
import { marked } from 'marked'  // 正确导入marked

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
      configValues: {},
      configLoading: false,
      configError: null,
      configFormHtml: null,
      extensionDocumentation: null
    }
  },
  computed: {
    compiledMarkdown(markdownContent) {
      return marked(markdownContent);
    },

    canInstall() {
      return this.extensionFile && this.extensionName
    },
    parsedModuleDoc() {
      return this.extensionDocumentation?.module ? 
        this.compiledMarkdown(this.extensionDocumentation.module) : 
        "无说明"
    },
    parsedExecuteQueryDoc() {
      return this.extensionDocumentation?.functions?.execute_query ? 
        this.compiledMarkdown(this.extensionDocumentation.functions.execute_query) : 
        "无方法说明"
    },
    parsedGetConfigFormDoc() {
      return this.extensionDocumentation?.functions?.get_config_form ? 
        this.compiledMarkdown(this.extensionDocumentation.functions.get_config_form) : 
        "无方法说明"
    },
    parsedGetDefaultConfigDoc() {
      return this.extensionDocumentation?.functions?.get_default_config ? 
        this.compiledMarkdown(this.extensionDocumentation.functions.get_default_config) : 
        "无方法说明"
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
      } finally {
        const submitBtn = document.querySelector('#uploadForm + .modal-footer button[type="button"].btn-primary')
        if (submitBtn) {
          submitBtn.disabled = false
          submitBtn.innerHTML = '<i class="fas fa-upload me-2"></i>安装扩展'
        }
      }
    },
    
    async toggleExtension(extension, field) {
      try {
        await updateExtension(extension.id, {
          [field]: extension[field]
        })
        Toast.success(`扩展已${extension[field] ? '启用' : '禁用'}`)
      } catch (error) {
        console.error('切换扩展状态失败', error)
        extension[field] = !extension[field] // 恢复状态
        Toast.error('切换扩展状态失败: ' + (error.response?.data?.detail || error.message))
      }
    },
    
    async configureExtension(extension) {
      this.currentExtension = extension
      this.configLoading = true
      this.configError = null
      this.showConfigModal = true
      this.configValues = {}
      this.configFormHtml = null
      this.extensionDocumentation = null
      
      try {
        // 获取扩展详情
        const response = await getExtension(extension.id)
        const extensionData = response.data
        
        // 设置基本配置值
        this.configValues = {
          id: extensionData.id,
          name: extensionData.name,
          description: extensionData.description || '',
          endpoint: extensionData.entry_point,
          return_type: extensionData.render_type || 'html',
          showinindex: extensionData.show_in_home || false,
          enabled: extensionData.enabled || false
        }
        
        // 获取文档信息
        this.extensionDocumentation = extensionData.documentation
        
        // 如果有配置表单，获取配置表单
        if (extensionData.has_config_form) {
          try {
            const configResponse = await getExtensionConfig(extension.id)
            let configFormHtml = configResponse.data.config_form
            const configData = configResponse.data.config || {}
            
            // 处理配置表单中的变量
            if (configData) {
              // 替换所有的 {{config.xxx}} 为实际的配置值
              configFormHtml = this.replaceConfigVariables(configFormHtml, configData)
            }
            
            this.configFormHtml = configFormHtml
          } catch (error) {
            console.error('获取配置表单失败', error)
            this.configFormHtml = `
              <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                加载扩展配置表单失败: ${error.message}
              </div>
            `
          }
        }
      } catch (error) {
        console.error('获取扩展配置失败', error)
        this.configError = '获取扩展配置失败: ' + (error.response?.data?.detail || error.message)
      } finally {
        this.configLoading = false
      }
    },
    
    async saveConfig(event) {
      if (!this.currentExtension) return
      
      try {
        const form = event.target
        const formData = new FormData(form)
        const data = Object.fromEntries(formData.entries())
        
        // 处理布尔值
        data.showinindex = data.showinindex === 'on'
        data.enabled = data.enabled === 'on'
        
        // 处理嵌套配置
        const config = {}
        for (const [key, value] of Object.entries(data)) {
          if (key.startsWith('config.')) {
            const parts = key.split('.')
            let current = config
            for (let i = 1; i < parts.length - 1; i++) {
              if (!current[parts[i]]) {
                current[parts[i]] = {}
              }
              current = current[parts[i]]
            }
            current[parts[parts.length - 1]] = value
            delete data[key]
          }
        }
        
        if (Object.keys(config).length > 0) {
          data.config = config
        }
        
        await updateExtension(this.currentExtension.id, data)
        
        Toast.success('配置保存成功')
        this.showConfigModal = false
        this.currentExtension = null
        this.configValues = {}
        this.configFormHtml = null
        this.extensionDocumentation = null
        this.fetchExtensions()
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
    },
    
    // HTML 转义辅助函数
    escapeHtml(unsafe) {
      return unsafe?.toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;") || ''
    },
    replaceConfigVariables(html, configData) {
      if (!html) return '';
      
      return html.replace(/\{\{(config\.([\w\.]+))\}\}/g, (match, p1, p2) => {
        try {
          // 处理嵌套路径，例如 config.api.key
          const path = p2.split('.');
          let value = configData;
          
          for (const key of path) {
            if (value === undefined || value === null) {
              return match; // 如果中间路径不存在，保留原始模板变量
            }
            value = value[key];
          }
          
          // 如果找到值，则返回值；否则返回原始模板变量
          return value !== undefined ? value : match;
        } catch (error) {
          console.error('替换配置变量失败:', error, match);
          return match; // 发生错误时保留原始模板变量
        }
      });
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