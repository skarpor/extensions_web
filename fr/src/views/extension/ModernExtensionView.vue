<template>
  <div class="modern-extension-view">
    <!-- 顶部导航栏 -->
    <div class="top-navbar">
      <div class="navbar-content">
        <div class="navbar-left">
          <h1 class="page-title">
            <el-icon><Operation /></el-icon>
            扩展工作台
          </h1>
          <span class="page-subtitle">现代化扩展执行环境</span>
        </div>
        
        <div class="navbar-right">
          <el-button-group>
            <el-button @click="refreshExtensions" :loading="loading" size="small">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button @click="showSettings = true" size="small">
              <el-icon><Setting /></el-icon>
              设置
            </el-button>
          </el-button-group>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 侧边栏 -->
      <div class="sidebar">
        <div class="sidebar-header">
          <h3>可用扩展</h3>
          <el-tag :type="extensions.length > 0 ? 'success' : 'info'" size="small">
            {{ extensions.length }} 个
          </el-tag>
        </div>
        
        <div class="extension-list">
          <div 
            v-for="ext in extensions" 
            :key="ext.id"
            class="extension-item"
            :class="{ active: selectedExtension?.id === ext.id }"
            @click="selectExtension(ext)"
          >
            <div class="extension-icon">
              <el-icon>
                <component :is="getExtensionIcon(ext.render_type)" />
              </el-icon>
            </div>
            
            <div class="extension-info">
              <div class="extension-name">{{ ext.name }}</div>
              <div class="extension-type">{{ getTypeLabel(ext.render_type) }}</div>
            </div>
            
            <div class="extension-status">
              <el-tag 
                :type="ext.enabled ? 'success' : 'danger'" 
                size="small"
                effect="plain"
              >
                {{ ext.enabled ? '启用' : '禁用' }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>

      <!-- 工作区域 -->
      <div class="workspace">
        <!-- 扩展未选择状态 -->
        <div v-if="!selectedExtension" class="empty-state">
          <el-empty description="请从左侧选择一个扩展开始使用">
            <template #image>
              <el-icon size="100" color="#409eff"><Operation /></el-icon>
            </template>
          </el-empty>
        </div>

        <!-- 扩展详情和执行区域 -->
        <div v-else class="extension-workspace">
          <!-- 扩展信息卡片 -->
          <el-card class="extension-info-card" shadow="never">
            <template #header>
              <div class="card-header">
                <div class="extension-title">
                  <el-icon size="24">
                    <component :is="getExtensionIcon(selectedExtension.render_type)" />
                  </el-icon>
                  <div>
                    <h2>{{ selectedExtension.name }}</h2>
                    <p class="extension-description">{{ selectedExtension.description || '暂无描述' }}</p>
                  </div>
                </div>
                
                <div class="extension-meta">
                  <el-tag :type="getTypeColor(selectedExtension.render_type)" effect="light">
                    {{ getTypeLabel(selectedExtension.render_type) }}
                  </el-tag>
                  <el-tag type="info" effect="plain" size="small">
                    {{ selectedExtension.endpoint }}
                  </el-tag>
                </div>
              </div>
            </template>

            <!-- 查询表单区域 -->
            <div class="query-section">
              <div class="section-header">
                <h3>
                  <el-icon><Edit /></el-icon>
                  查询参数
                </h3>
                <el-button 
                  type="primary" 
                  @click="executeExtension"
                  :loading="executing"
                  :disabled="!selectedExtension.enabled"
                >
                  <el-icon><CaretRight /></el-icon>
                  执行查询
                </el-button>
              </div>

              <div class="query-form-container">
                <div v-if="loadingForm" class="loading-state">
                  <el-skeleton :rows="3" animated />
                </div>
                
                <div v-else-if="formError" class="error-state">
                  <el-alert type="error" :title="formError" show-icon />
                </div>
                
                <div v-else-if="selectedExtension.has_query_form" class="dynamic-form">
                  <div v-html="queryFormHtml" class="form-content"></div>
                </div>
                
                <div v-else class="no-params">
                  <el-empty description="此扩展无需额外参数" :image-size="80">
                    <template #image>
                      <el-icon size="80" color="#909399"><Check /></el-icon>
                    </template>
                  </el-empty>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 结果显示区域 -->
          <div v-if="hasResult" class="result-section">
            <el-card shadow="never">
              <template #header>
                <div class="result-header">
                  <div class="result-title">
                    <el-icon><DataAnalysis /></el-icon>
                    <span>执行结果</span>
                    <el-tag :type="getResultStatusType()" size="small">
                      {{ getResultStatusText() }}
                    </el-tag>
                  </div>
                  
                  <div class="result-actions">
                    <el-button-group size="small">
                      <el-button @click="copyResult" v-if="canCopyResult">
                        <el-icon><CopyDocument /></el-icon>
                        复制
                      </el-button>
                      <el-button @click="downloadResult" v-if="canDownloadResult">
                        <el-icon><Download /></el-icon>
                        下载
                      </el-button>
                      <el-button @click="clearResult">
                        <el-icon><Delete /></el-icon>
                        清除
                      </el-button>
                    </el-button-group>
                  </div>
                </div>
              </template>

              <!-- 结果内容 -->
              <div class="result-content">
                <!-- 执行中状态 -->
                <div v-if="executing" class="executing-state">
                  <div class="execution-progress">
                    <el-progress 
                      :percentage="executionProgress" 
                      :status="executionProgress === 100 ? 'success' : null"
                      :stroke-width="8"
                    />
                    <p class="progress-text">{{ executionText }}</p>
                  </div>
                </div>

                <!-- 错误状态 -->
                <div v-else-if="executionError" class="error-result">
                  <el-alert 
                    type="error" 
                    :title="executionError" 
                    show-icon 
                    :closable="false"
                  />
                </div>

                <!-- 成功结果 -->
                <div v-else class="success-result">
                  <!-- HTML结果 -->
                  <div v-if="resultType === 'html'" class="html-result">
                    <div v-html="resultData" class="html-content"></div>
                  </div>

                  <!-- 表格结果 -->
                  <div v-else-if="resultType === 'table'" class="table-result">
                    <TableResultDisplay 
                      :data="resultData" 
                      :meta="resultMeta"
                      @export="handleTableExport"
                    />
                  </div>

                  <!-- 图片结果 -->
                  <div v-else-if="resultType === 'image'" class="image-result">
                    <ImageResultDisplay 
                      :src="resultData"
                      :meta="resultMeta"
                      @download="handleImageDownload"
                    />
                  </div>

                  <!-- 文件结果 -->
                  <div v-else-if="resultType === 'file'" class="file-result">
                    <FileResultDisplay 
                      :file-info="resultData"
                      :meta="resultMeta"
                      @download="handleFileDownload"
                    />
                  </div>

                  <!-- 图表结果 -->
                  <div v-else-if="resultType === 'chart'" class="chart-result">
                    <ChartResultDisplay 
                      :chart-config="resultData"
                      :meta="resultMeta"
                      @export="handleChartExport"
                    />
                  </div>

                  <!-- 文本结果 -->
                  <div v-else-if="resultType === 'text'" class="text-result">
                    <TextResultDisplay 
                      :content="resultData"
                      :meta="resultMeta"
                      @copy="handleTextCopy"
                    />
                  </div>

                  <!-- 未知类型 -->
                  <div v-else class="unknown-result">
                    <el-alert 
                      type="warning" 
                      title="未知的结果类型" 
                      :description="`类型: ${resultType}`"
                      show-icon 
                    />
                    <pre class="raw-result">{{ resultData }}</pre>
                  </div>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </div>
    </div>

    <!-- 设置对话框 -->
    <el-dialog v-model="showSettings" title="扩展工作台设置" width="600px">
      <WorkspaceSettings 
        v-model="workspaceSettings"
        @save="saveSettings"
      />
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Operation,
  Refresh,
  Setting,
  Edit,
  CaretRight,
  Check,
  DataAnalysis,
  CopyDocument,
  Download,
  Delete,
  Document,
  Grid,
  Picture,
  Files,
  TrendCharts,
  Memo
} from '@element-plus/icons-vue'

// 导入结果显示组件
import TableResultDisplay from './components/TableResultDisplay.vue'
import ImageResultDisplay from './components/ImageResultDisplay.vue'
import FileResultDisplay from './components/FileResultDisplay.vue'
import ChartResultDisplay from './components/ChartResultDisplay.vue'
import TextResultDisplay from './components/TextResultDisplay.vue'
import WorkspaceSettings from './components/WorkspaceSettings.vue'

// 导入API
import { getExtensions, getExtensionQueryForm, executeExtensionQuery } from '@/api/extension'

export default {
  name: 'ModernExtensionView',
  components: {
    Operation,
    Refresh,
    Setting,
    Edit,
    CaretRight,
    Check,
    DataAnalysis,
    CopyDocument,
    Download,
    Delete,
    Document,
    Grid,
    Picture,
    Files,
    TrendCharts,
    Memo,
    TableResultDisplay,
    ImageResultDisplay,
    FileResultDisplay,
    ChartResultDisplay,
    TextResultDisplay,
    WorkspaceSettings
  },
  setup() {
    // 响应式数据
    const extensions = ref([])
    const selectedExtension = ref(null)
    const loading = ref(false)
    const loadingForm = ref(false)
    const executing = ref(false)
    const executionProgress = ref(0)
    const executionText = ref('')
    
    // 表单相关
    const queryFormHtml = ref('')
    const formError = ref('')
    
    // 结果相关
    const resultType = ref('')
    const resultData = ref(null)
    const resultMeta = ref(null)
    const executionError = ref('')
    
    // 设置相关
    const showSettings = ref(false)
    const workspaceSettings = reactive({
      autoRefresh: false,
      refreshInterval: 30,
      showExecutionTime: true,
      enableNotifications: true,
      defaultResultView: 'auto'
    })

    // 计算属性
    const hasResult = computed(() => {
      return resultData.value !== null || executionError.value
    })

    const canCopyResult = computed(() => {
      return ['text', 'html'].includes(resultType.value)
    })

    const canDownloadResult = computed(() => {
      return ['file', 'image', 'chart', 'table'].includes(resultType.value)
    })

    // 方法
    const refreshExtensions = async () => {
      try {
        loading.value = true
        const response = await getExtensions()
        extensions.value = response.data.filter(ext => ext.enabled && ext.show_in_home)
        ElMessage.success(`加载了 ${extensions.value.length} 个扩展`)
      } catch (error) {
        ElMessage.error('加载扩展失败: ' + error.message)
      } finally {
        loading.value = false
      }
    }

    const selectExtension = async (extension) => {
      selectedExtension.value = extension
      clearResult()

      if (extension.has_query_form) {
        await loadQueryForm(extension.id)
      }
    }

    const loadQueryForm = async (extensionId) => {
      try {
        loadingForm.value = true
        formError.value = ''
        const response = await getExtensionQueryForm(extensionId)
        queryFormHtml.value = response.data.form_html
      } catch (error) {
        formError.value = '加载查询表单失败: ' + error.message
      } finally {
        loadingForm.value = false
      }
    }

    const executeExtension = async () => {
      if (!selectedExtension.value) return

      try {
        executing.value = true
        executionError.value = ''
        executionProgress.value = 0
        executionText.value = '准备执行...'

        // 模拟执行进度
        const progressInterval = setInterval(() => {
          if (executionProgress.value < 90) {
            executionProgress.value += 10
            updateExecutionText()
          }
        }, 200)

        // 收集表单数据
        const formData = collectFormData()

        // 执行查询
        const response = await executeExtensionQuery(selectedExtension.value.id, formData)

        clearInterval(progressInterval)
        executionProgress.value = 100
        executionText.value = '执行完成'

        // 处理结果
        handleExecutionResult(response.data)

        if (workspaceSettings.enableNotifications) {
          ElMessage.success('扩展执行成功')
        }

      } catch (error) {
        executionError.value = '执行失败: ' + error.message
        ElMessage.error('执行失败: ' + error.message)
      } finally {
        executing.value = false
      }
    }

    const collectFormData = () => {
      const formData = {}
      if (selectedExtension.value.has_query_form) {
        const formElement = document.querySelector('.form-content form')
        if (formElement) {
          const formDataObj = new FormData(formElement)
          for (const [key, value] of formDataObj.entries()) {
            formData[key] = value
          }
        }
      }
      return formData
    }

    const handleExecutionResult = (result) => {
      resultType.value = result.type || 'text'
      resultData.value = result.data || result.content || result
      resultMeta.value = result.meta || null
    }

    const updateExecutionText = () => {
      const texts = [
        '初始化扩展...',
        '加载配置...',
        '处理参数...',
        '执行查询...',
        '处理结果...',
        '渲染数据...'
      ]
      const index = Math.floor(executionProgress.value / 15)
      executionText.value = texts[index] || '处理中...'
    }

    const clearResult = () => {
      resultType.value = ''
      resultData.value = null
      resultMeta.value = null
      executionError.value = ''
      executionProgress.value = 0
    }

    const getExtensionIcon = (renderType) => {
      const iconMap = {
        'html': Document,
        'table': Grid,
        'image': Picture,
        'file': Files,
        'chart': TrendCharts,
        'text': Memo
      }
      return iconMap[renderType] || Operation
    }

    const getTypeLabel = (renderType) => {
      const labelMap = {
        'html': 'HTML页面',
        'table': '数据表格',
        'image': '图片图表',
        'file': '文件下载',
        'chart': '交互图表',
        'text': '文本报告'
      }
      return labelMap[renderType] || '未知类型'
    }

    const getTypeColor = (renderType) => {
      const colorMap = {
        'html': 'primary',
        'table': 'success',
        'image': 'warning',
        'file': 'info',
        'chart': 'danger',
        'text': ''
      }
      return colorMap[renderType] || 'info'
    }

    const getResultStatusType = () => {
      if (executionError.value) return 'danger'
      if (executing.value) return 'warning'
      return 'success'
    }

    const getResultStatusText = () => {
      if (executionError.value) return '执行失败'
      if (executing.value) return '执行中'
      return '执行成功'
    }

    // 结果操作方法
    const copyResult = () => {
      // 实现复制功能
      ElMessage.success('结果已复制到剪贴板')
    }

    const downloadResult = () => {
      // 实现下载功能
      ElMessage.success('开始下载')
    }

    const handleTableExport = (format) => {
      ElMessage.success(`导出为 ${format} 格式`)
    }

    const handleImageDownload = () => {
      ElMessage.success('图片下载中')
    }

    const handleFileDownload = () => {
      ElMessage.success('文件下载中')
    }

    const handleChartExport = (format) => {
      ElMessage.success(`图表导出为 ${format} 格式`)
    }

    const handleTextCopy = () => {
      ElMessage.success('文本已复制')
    }

    const saveSettings = () => {
      ElMessage.success('设置已保存')
      showSettings.value = false
    }

    // 生命周期
    onMounted(() => {
      refreshExtensions()
    })

    return {
      extensions,
      selectedExtension,
      loading,
      loadingForm,
      executing,
      executionProgress,
      executionText,
      queryFormHtml,
      formError,
      resultType,
      resultData,
      resultMeta,
      executionError,
      showSettings,
      workspaceSettings,
      hasResult,
      canCopyResult,
      canDownloadResult,
      refreshExtensions,
      selectExtension,
      executeExtension,
      clearResult,
      getExtensionIcon,
      getTypeLabel,
      getTypeColor,
      getResultStatusType,
      getResultStatusText,
      copyResult,
      downloadResult,
      handleTableExport,
      handleImageDownload,
      handleFileDownload,
      handleChartExport,
      handleTextCopy,
      saveSettings
    }
  }
}
</script>

<style scoped>
.modern-extension-view {
  height: 90vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  width: 100%;
}

/* 顶部导航栏 */
.top-navbar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.navbar-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto;
}

.navbar-left {
  display: flex;
  flex-direction: column;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-subtitle {
  font-size: 14px;
  opacity: 0.8;
  margin-top: 4px;
}

/* 主要内容区域 */
.main-content {
  flex: 1;
  display: flex;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  gap: 24px;
  padding: 24px;
  overflow: hidden;
}

/* 侧边栏 */
.sidebar {
  width: 320px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.extension-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.extension-item {
  display: flex;
  align-items: center;
  padding: 16px;
  margin: 4px 0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.extension-item:hover {
  background: #f8f9ff;
  transform: translateX(4px);
}

.extension-item.active {
  background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

.extension-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-right: 12px;
}

.extension-info {
  flex: 1;
}

.extension-name {
  font-weight: 600;
  font-size: 14px;
  color: #2c3e50;
  margin-bottom: 4px;
}

.extension-type {
  font-size: 12px;
  color: #7f8c8d;
}

.extension-status {
  margin-left: 8px;
}

/* 工作区域 */
.workspace {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.extension-workspace {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
  overflow: hidden;
}

/* 扩展信息卡片 */
.extension-info-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.extension-title {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.extension-title h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}

.extension-description {
  margin: 0;
  color: #7f8c8d;
  font-size: 14px;
}

.extension-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-end;
}

/* 查询区域 */
.query-section {
  margin-top: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 8px;
}

.query-form-container {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  min-height: 120px;
}

.loading-state,
.error-state,
.no-params {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
}

.form-content {
  background: white;
  border-radius: 6px;
  padding: 16px;
}

/* 结果区域 */
.result-section {
  flex: 1;
  overflow: hidden;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.result-content {
  max-height: 600px;
  overflow: auto;
}

/* 执行状态 */
.executing-state {
  padding: 40px;
  text-align: center;
}

.execution-progress {
  max-width: 400px;
  margin: 0 auto;
}

.progress-text {
  margin-top: 16px;
  color: #7f8c8d;
  font-size: 14px;
}

/* 结果显示 */
.error-result,
.success-result {
  padding: 20px;
}

.html-content {
  background: white;
  border-radius: 6px;
  padding: 16px;
  border: 1px solid #e9ecef;
}

.raw-result {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 16px;
  margin-top: 16px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  overflow: auto;
  max-height: 300px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .main-content {
    flex-direction: column;
    gap: 16px;
  }

  .sidebar {
    width: 100%;
    max-height: 300px;
  }

  .extension-list {
    display: flex;
    gap: 8px;
    overflow-x: auto;
    padding: 8px 16px;
  }

  .extension-item {
    min-width: 200px;
    flex-shrink: 0;
  }
}

@media (max-width: 768px) {
  .navbar-content {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .main-content {
    padding: 16px;
  }

  .card-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .extension-meta {
    align-items: flex-start;
  }
}
</style>

