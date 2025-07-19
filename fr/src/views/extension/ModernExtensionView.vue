<template>
  <div class="modern-extension-view" :class="themeClass">
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
      <div class="sidebar" :style="sidebarStyle">
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
                  <div class="form-debug" v-if="queryFormHtml">
                    <small style="color: #6c757d;">表单HTML长度: {{ queryFormHtml.length }} 字符</small>
                  </div>
                  <form class="form-content" @submit.prevent="executeExtension">
                    <div v-html="queryFormHtml"></div>
                  </form>
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
              <div class="result-content" :style="resultContentStyle">
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
                    <div class="table-header">
                      <h4>📊 表格数据</h4>
                      <div class="table-meta">
                        <el-tag type="info" size="small">{{ getTableRowCount() }} 条记录</el-tag>
                        <el-tag v-if="resultMeta?.查询时间" type="success" size="small">
                          {{ resultMeta.查询时间 }}
                        </el-tag>
                      </div>
                      <div class="table-actions">
                        <el-button-group size="small">
                          <el-button @click="exportTableData('csv')">
                            <el-icon><Document /></el-icon>
                            CSV
                          </el-button>
                          <el-button @click="exportTableData('json')">
                            <el-icon><Files /></el-icon>
                            JSON
                          </el-button>
                          <el-button @click="toggleTableFullscreen">
                            <el-icon><FullScreen /></el-icon>
                            全屏
                          </el-button>
                        </el-button-group>
                      </div>
                    </div>
                    <div class="table-container" :class="{ fullscreen: tableFullscreen }">
                      <el-table
                        :data="paginatedTableData"
                        border
                        stripe
                        :height="tableFullscreen ? '70vh' : '400px'"
                        @sort-change="handleTableSort"
                      >
                        <el-table-column
                          v-for="column in tableColumns"
                          :key="column.prop"
                          :prop="column.prop"
                          :label="column.label"
                          :sortable="column.sortable"
                          :width="column.width"
                          show-overflow-tooltip
                        >
                          <template #default="scope">
                            <span v-if="column.type === 'number'" class="number-cell">
                              {{ formatNumber(scope.row[column.prop]) }}
                            </span>
                            <el-tag
                              v-else-if="column.type === 'status'"
                              :type="getStatusType(scope.row[column.prop])"
                              size="small"
                            >
                              {{ scope.row[column.prop] }}
                            </el-tag>
                            <span v-else>{{ scope.row[column.prop] }}</span>
                          </template>
                        </el-table-column>
                      </el-table>

                      <!-- 分页器 -->
                      <div v-if="getTableRowCount() > tablePageSize" class="table-pagination">
                        <el-pagination
                          v-model:current-page="tableCurrentPage"
                          v-model:page-size="tablePageSize"
                          :page-sizes="[10, 20, 50, 100]"
                          :total="getTableRowCount()"
                          layout="total, sizes, prev, pager, next, jumper"
                          @size-change="handleTableSizeChange"
                          @current-change="handleTableCurrentChange"
                        />
                      </div>
                    </div>
                  </div>

                  <!-- 图片结果 -->
                  <div v-else-if="resultType === 'image'" class="image-result">
                    <div class="image-header">
                      <h4>🖼️ 图片结果</h4>
                    </div>
                    <div class="image-container">
                      <img :src="resultData" alt="扩展生成的图片" style="max-width: 100%; height: auto;" />
                    </div>
                  </div>

                  <!-- 文件结果 -->
                  <div v-else-if="resultType === 'file'" class="file-result">
                    <div class="file-header">
                      <h4>📁 文件结果</h4>
                    </div>
                    <div class="file-info">
                      <p><strong>文件名:</strong> {{ resultData?.filename || '未知文件' }}</p>
                      <p><strong>类型:</strong> {{ resultData?.content_type || '未知类型' }}</p>
                      <el-button type="primary" @click="handleFileDownload">
                        <el-icon><Download /></el-icon>
                        下载文件
                      </el-button>
                    </div>
                  </div>

                  <!-- 图表结果 -->
                  <div v-else-if="resultType === 'chart'" class="chart-result">
                    <div class="chart-header">
                      <h4>📈 图表结果</h4>
                      <el-tag type="success" size="small">{{ resultData?.chart_type || '图表' }}</el-tag>
                      <div class="chart-actions">
                        <el-button-group size="small">
                          <el-button @click="exportChart('png')">
                            <el-icon><Picture /></el-icon>
                            PNG
                          </el-button>
                          <el-button @click="toggleChartFullscreen">
                            <el-icon><FullScreen /></el-icon>
                            全屏
                          </el-button>
                          <el-button @click="showChartData = !showChartData">
                            <el-icon><Grid /></el-icon>
                            数据
                          </el-button>
                        </el-button-group>
                      </div>
                    </div>
                    <div class="chart-container">
                      <canvas ref="chartCanvas" :style="chartCanvasStyle"></canvas>
                      <div v-if="chartLoading" class="chart-loading">
                        <el-icon class="loading-icon"><Loading /></el-icon>
                        <p>图表渲染中...</p>
                      </div>
                      <div v-if="chartError" class="chart-error">
                        <el-icon class="error-icon"><Warning /></el-icon>
                        <p>{{ chartError }}</p>
                        <el-button @click="retryChart" size="small">重试</el-button>
                      </div>
                    </div>

                    <!-- 图表数据表格 -->
                    <div v-if="showChartData && chartTableData.length > 0" class="chart-data-table">
                      <div class="table-header">
                        <h5>📊 图表数据</h5>
                        <el-button @click="showChartData = false" size="small">
                          <el-icon><Close /></el-icon>
                          关闭
                        </el-button>
                      </div>
                      <el-table :data="chartTableData" border stripe max-height="300">
                        <el-table-column
                          v-for="column in chartTableColumns"
                          :key="column.prop"
                          :prop="column.prop"
                          :label="column.label"
                          show-overflow-tooltip
                        />
                      </el-table>
                    </div>
                  </div>

                  <!-- 文本结果 -->
                  <div v-else-if="resultType === 'text'" class="text-result">
                    <div class="text-header">
                      <h4>📝 文本结果</h4>
                      <el-button @click="copyText" size="small">
                        <el-icon><CopyDocument /></el-icon>
                        复制
                      </el-button>
                    </div>
                    <div class="text-content">
                      <pre>{{ resultData }}</pre>
                    </div>
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
      <el-form :model="workspaceSettings" label-width="120px">
        <el-form-item label="自动刷新">
          <el-switch v-model="workspaceSettings.autoRefresh" />
        </el-form-item>
        <el-form-item label="刷新间隔(秒)" v-if="workspaceSettings.autoRefresh">
          <el-input-number v-model="workspaceSettings.refreshInterval" :min="5" :max="300" />
        </el-form-item>
        <el-form-item label="侧边栏宽度">
          <el-slider v-model="workspaceSettings.sidebarWidth" :min="250" :max="500" />
        </el-form-item>
        <el-form-item label="结果区域高度">
          <el-slider v-model="workspaceSettings.resultAreaHeight" :min="300" :max="800" />
        </el-form-item>
        <el-form-item label="主题模式">
          <el-radio-group v-model="workspaceSettings.themeMode">
            <el-radio label="light">浅色</el-radio>
            <el-radio label="dark">深色</el-radio>
            <el-radio label="auto">自动</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSettings = false">取消</el-button>
        <el-button type="primary" @click="saveSettings(workspaceSettings)">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
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

// 导入结果显示组件（暂时注释掉不存在的组件）
// import TableResultDisplay from './components/TableResultDisplay.vue'
// import ImageResultDisplay from './components/ImageResultDisplay.vue'
// import FileResultDisplay from './components/FileResultDisplay.vue'
// import ChartResultDisplay from './components/ChartResultDisplay.vue'
// import TextResultDisplay from './components/TextResultDisplay.vue'
// import WorkspaceSettings from './components/WorkspaceSettings.vue'

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
    Memo
    // 暂时注释掉不存在的组件
    // TableResultDisplay,
    // ImageResultDisplay,
    // FileResultDisplay,
    // ChartResultDisplay,
    // TextResultDisplay,
    // WorkspaceSettings
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

    // 图表相关
    const chartCanvas = ref(null)
    const chartInstance = ref(null)
    const chartLoading = ref(false)
    const chartError = ref('')
    const showChartData = ref(false)
    const chartFullscreen = ref(false)

    // 表格相关
    const tableCurrentPage = ref(1)
    const tablePageSize = ref(20)
    const tableSortConfig = ref({ prop: '', order: '' })
    const tableFullscreen = ref(false)
    
    // 设置相关
    const showSettings = ref(false)
    const workspaceSettings = reactive({
      autoRefresh: false,
      refreshInterval: 30,
      showExecutionTime: true,
      enableNotifications: true,
      defaultResultView: 'auto',
      themeMode: 'light',
      sidebarWidth: 320,
      resultAreaHeight: 600,
      cacheResults: true,
      cacheTimeout: 5,
      maxConcurrency: 3,
      executionTimeout: 60
    })

    // 从localStorage加载设置
    const loadSettings = () => {
      const savedSettings = localStorage.getItem('workspace-settings')
      if (savedSettings) {
        try {
          const parsed = JSON.parse(savedSettings)
          Object.assign(workspaceSettings, parsed)
        } catch (error) {
          console.error('Failed to load settings:', error)
        }
      }
    }

    // 保存设置到localStorage
    const saveSettingsToStorage = () => {
      localStorage.setItem('workspace-settings', JSON.stringify(workspaceSettings))
    }

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

    // 样式计算属性
    const sidebarStyle = computed(() => ({
      width: `${workspaceSettings.sidebarWidth}px`,
      minWidth: `${workspaceSettings.sidebarWidth}px`
    }))

    const resultContentStyle = computed(() => ({
      maxHeight: `${workspaceSettings.resultAreaHeight}px`
    }))

    const themeClass = computed(() => {
      if (workspaceSettings.themeMode === 'auto') {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'theme-dark' : 'theme-light'
      }
      return `theme-${workspaceSettings.themeMode}`
    })

    // 图表相关计算属性
    const chartCanvasStyle = computed(() => ({
      width: '100%',
      height: chartFullscreen.value ? '70vh' : '400px'
    }))

    const chartTableData = computed(() => {
      if (!resultData.value?.chart_data?.datasets) return []

      const chartData = resultData.value.chart_data
      const labels = chartData.labels || []
      const datasets = chartData.datasets || []

      return labels.map((label, index) => {
        const row = { 标签: label }
        datasets.forEach(dataset => {
          row[dataset.label || '数据'] = dataset.data[index]
        })
        return row
      })
    })

    const chartTableColumns = computed(() => {
      if (!resultData.value?.chart_data?.datasets) return []

      const columns = [{ prop: '标签', label: '标签' }]
      const datasets = resultData.value.chart_data.datasets || []

      datasets.forEach(dataset => {
        columns.push({
          prop: dataset.label || '数据',
          label: dataset.label || '数据'
        })
      })

      return columns
    })

    // 表格相关计算属性
    const tableColumns = computed(() => {
      if (!resultData.value || !Array.isArray(resultData.value) || resultData.value.length === 0) {
        return []
      }

      const firstRow = resultData.value[0]
      return Object.keys(firstRow).map(key => {
        const column = {
          prop: key,
          label: key,
          sortable: true,
          width: undefined
        }

        // 根据数据类型设置列属性
        const value = firstRow[key]
        if (typeof value === 'number') {
          column.type = 'number'
          column.width = 120
        } else if (key.includes('状态') || key.includes('status') || key.toLowerCase().includes('state')) {
          column.type = 'status'
          column.width = 100
        } else if (typeof value === 'string' && value.length > 50) {
          column.width = 200
        }

        return column
      })
    })

    const sortedTableData = computed(() => {
      if (!resultData.value || !Array.isArray(resultData.value)) return []

      if (!tableSortConfig.value.prop) return resultData.value

      const { prop, order } = tableSortConfig.value
      return [...resultData.value].sort((a, b) => {
        const aVal = a[prop]
        const bVal = b[prop]

        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return order === 'ascending' ? aVal - bVal : bVal - aVal
        }

        const aStr = String(aVal).toLowerCase()
        const bStr = String(bVal).toLowerCase()

        if (order === 'ascending') {
          return aStr.localeCompare(bStr)
        } else {
          return bStr.localeCompare(aStr)
        }
      })
    })

    const paginatedTableData = computed(() => {
      const start = (tableCurrentPage.value - 1) * tablePageSize.value
      const end = start + tablePageSize.value
      return sortedTableData.value.slice(start, end)
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
      console.log('选择扩展:', extension)
      selectedExtension.value = extension
      clearResult()

      if (extension.has_query_form) {
        console.log('扩展有查询表单，开始加载...')
        await loadQueryForm(extension.id)
      } else {
        console.log('扩展没有查询表单')
      }
    }

    const loadQueryForm = async (extensionId) => {
      try {
        loadingForm.value = true
        formError.value = ''
        const response = await getExtensionQueryForm(extensionId)
        // 后端返回的字段名是query_form，不是form_html
        queryFormHtml.value = response.data.query_form || response.data.form_html
        console.log('加载查询表单成功:', queryFormHtml.value)
      } catch (error) {
        console.error('加载查询表单失败:', error)
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

        // 处理结果 - executeExtensionQuery已经返回了data部分
        handleExecutionResult(response)

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
        // 查找表单容器
        const formContainer = document.querySelector('.form-content')
        if (formContainer) {
          // 收集所有输入元素的值
          const inputs = formContainer.querySelectorAll('input, select, textarea')
          inputs.forEach(input => {
            if (input.name) {
              if (input.type === 'checkbox') {
                formData[input.name] = input.checked
              } else if (input.type === 'radio') {
                if (input.checked) {
                  formData[input.name] = input.value
                }
              } else {
                formData[input.name] = input.value
              }
            }
          })
          console.log('收集到的表单数据:', formData)
        }
      }
      return formData
    }

    const handleExecutionResult = (result) => {
      console.log('处理执行结果:', result)

      // 检查是否是我们修复后的扩展返回的标准格式
      if (result && typeof result === 'object' && result.type && result.data !== undefined) {
        // 标准扩展返回格式: {type: "html", data: "...", meta: {...}}
        resultType.value = result.type
        resultData.value = result.data
        resultMeta.value = result.meta || null
        console.log('使用标准格式:', resultType.value)

        // 如果是图表类型，渲染图表
        if (result.type === 'chart') {
          nextTick(() => {
            renderChart()
          })
        }
      } else {
        // 兼容旧格式或其他数据 - 根据扩展的render_type来判断如何显示
        const renderType = selectedExtension.value?.render_type || 'text'
        resultType.value = renderType
        resultData.value = result
        resultMeta.value = null
        console.log('使用兼容格式，render_type:', renderType)

        // 如果是图表类型，渲染图表
        if (renderType === 'chart') {
          nextTick(() => {
            renderChart()
          })
        }
      }
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

      // 清理图表
      if (chartInstance.value) {
        chartInstance.value.destroy()
        chartInstance.value = null
      }
      chartError.value = ''
      showChartData.value = false
      chartFullscreen.value = false
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

    const copyText = async () => {
      try {
        await navigator.clipboard.writeText(resultData.value)
        ElMessage.success('文本已复制到剪贴板')
      } catch (error) {
        ElMessage.error('复制失败')
      }
    }

    // 表格相关方法
    const getTableRowCount = () => {
      return Array.isArray(resultData.value) ? resultData.value.length : 0
    }

    const handleTableSort = ({ prop, order }) => {
      tableSortConfig.value = { prop, order }
    }

    const handleTableSizeChange = (size) => {
      tablePageSize.value = size
      tableCurrentPage.value = 1
    }

    const handleTableCurrentChange = (page) => {
      tableCurrentPage.value = page
    }

    const formatNumber = (value) => {
      if (typeof value !== 'number') return value
      return value.toLocaleString()
    }

    const getStatusType = (status) => {
      const statusMap = {
        '正常': 'success',
        '运行': 'success',
        '运行中': 'success',
        'running': 'success',
        '警告': 'warning',
        '异常': 'danger',
        '错误': 'danger',
        '停止': 'info',
        '已停止': 'info',
        'stopped': 'info'
      }
      return statusMap[status] || 'info'
    }

    const exportTableData = (format) => {
      if (!resultData.value || !Array.isArray(resultData.value)) {
        ElMessage.warning('没有数据可导出')
        return
      }

      try {
        if (format === 'csv') {
          exportTableToCsv()
        } else if (format === 'json') {
          exportTableToJson()
        }
      } catch (error) {
        ElMessage.error('导出失败: ' + error.message)
      }
    }

    const exportTableToCsv = () => {
      const headers = tableColumns.value.map(col => col.label).join(',')
      const rows = resultData.value.map(row =>
        tableColumns.value.map(col => {
          const value = row[col.prop]
          return typeof value === 'string' && value.includes(',')
            ? `"${value}"`
            : value
        }).join(',')
      )

      const csvContent = [headers, ...rows].join('\n')
      downloadFile(csvContent, 'table-data.csv', 'text/csv')
      ElMessage.success('CSV文件已下载')
    }

    const exportTableToJson = () => {
      const jsonContent = JSON.stringify({
        data: resultData.value,
        meta: resultMeta.value,
        exported_at: new Date().toISOString()
      }, null, 2)

      downloadFile(jsonContent, 'table-data.json', 'application/json')
      ElMessage.success('JSON文件已下载')
    }

    const downloadFile = (content, filename, mimeType) => {
      const blob = new Blob([content], { type: mimeType })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    }

    const toggleTableFullscreen = () => {
      tableFullscreen.value = !tableFullscreen.value
    }

    // 图表渲染函数
    const renderChart = async () => {
      if (!chartCanvas.value || !resultData.value) return

      try {
        chartLoading.value = true
        chartError.value = ''

        // 动态导入Chart.js
        const { Chart, registerables } = await import('chart.js')
        Chart.register(...registerables)

        // 销毁现有图表实例
        if (chartInstance.value) {
          chartInstance.value.destroy()
          chartInstance.value = null
        }

        // 获取图表配置
        const chartType = resultData.value.chart_type || 'line'
        const chartData = resultData.value.chart_data || {}
        const chartOptions = resultData.value.options || {}

        // 创建新的图表实例
        chartInstance.value = new Chart(chartCanvas.value, {
          type: chartType,
          data: chartData,
          options: {
            responsive: true,
            maintainAspectRatio: false,
            ...chartOptions,
            plugins: {
              ...chartOptions.plugins,
              legend: {
                display: true,
                position: 'top',
                ...chartOptions.plugins?.legend
              },
              tooltip: {
                enabled: true,
                ...chartOptions.plugins?.tooltip
              }
            },
            scales: {
              ...chartOptions.scales,
              y: {
                beginAtZero: true,
                ...chartOptions.scales?.y
              }
            }
          }
        })

        chartLoading.value = false
        console.log('图表渲染成功')

      } catch (error) {
        chartLoading.value = false
        chartError.value = '图表渲染失败: ' + error.message
        console.error('图表渲染失败:', error)
      }
    }

    const retryChart = () => {
      renderChart()
    }

    const exportChart = (format) => {
      if (!chartInstance.value) {
        ElMessage.error('图表未准备就绪')
        return
      }

      try {
        if (format === 'png') {
          const url = chartInstance.value.toBase64Image()
          const link = document.createElement('a')
          link.href = url
          link.download = `chart-${Date.now()}.png`
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
          ElMessage.success('图表已导出为PNG')
        }
      } catch (error) {
        ElMessage.error('导出失败: ' + error.message)
      }
    }

    const toggleChartFullscreen = () => {
      chartFullscreen.value = !chartFullscreen.value
      // 延迟一下让DOM更新，然后重新渲染图表
      nextTick(() => {
        if (chartInstance.value) {
          chartInstance.value.resize()
        }
      })
    }

    const saveSettings = (newSettings) => {
      Object.assign(workspaceSettings, newSettings)
      saveSettingsToStorage()
      ElMessage.success('设置已保存')
      showSettings.value = false
    }

    // 生命周期
    onMounted(() => {
      loadSettings()
      refreshExtensions()

      // 设置自动刷新
      if (workspaceSettings.autoRefresh) {
        setInterval(() => {
          refreshExtensions()
        }, workspaceSettings.refreshInterval * 1000)
      }
    })

    onUnmounted(() => {
      // 清理图表实例
      if (chartInstance.value) {
        chartInstance.value.destroy()
        chartInstance.value = null
      }
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
      saveSettings,
      sidebarStyle,
      resultContentStyle,
      themeClass,
      loadSettings,
      saveSettingsToStorage,
      copyText,
      // 图表相关
      chartCanvas,
      chartCanvasStyle,
      chartLoading,
      chartError,
      showChartData,
      chartTableData,
      chartTableColumns,
      renderChart,
      retryChart,
      exportChart,
      toggleChartFullscreen,
      // 表格相关
      tableCurrentPage,
      tablePageSize,
      tableFullscreen,
      tableColumns,
      paginatedTableData,
      getTableRowCount,
      handleTableSort,
      handleTableSizeChange,
      handleTableCurrentChange,
      formatNumber,
      getStatusType,
      exportTableData,
      toggleTableFullscreen
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
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
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

/* 查询表单样式 */
.form-content .form-group {
  margin-bottom: 16px;
}

.form-content .form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
  color: #495057;
}

.form-content .form-control {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.form-content .form-control:focus {
  border-color: #667eea;
  outline: 0;
  box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
}

.form-content input[type="checkbox"] {
  margin-right: 8px;
}

.form-content .query-form {
  padding: 0;
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

/* 主题样式 */
.theme-dark {
  background: #1a1a1a;
  color: #e0e0e0;
}

.theme-dark .sidebar,
.theme-dark .extension-info-card,
.theme-dark .result-section .el-card {
  background: #2d2d2d;
  color: #e0e0e0;
}

.theme-dark .sidebar-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.theme-dark .extension-item {
  border-color: #404040;
}

.theme-dark .extension-item:hover {
  background: #3a3a3a;
}

.theme-dark .extension-item.active {
  background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
  border-color: #667eea;
}

.theme-dark .query-form-container,
.theme-dark .text-stats,
.theme-dark .image-info,
.theme-dark .chart-info {
  background: #3a3a3a;
}

.theme-dark .form-content,
.theme-dark .stat-item,
.theme-dark .info-item {
  background: #2d2d2d;
  border-color: #404040;
}

.theme-light {
  background: #f5f7fa;
  color: #2c3e50;
}

/* 结果显示样式 */
.table-header,
.image-header,
.file-header,
.chart-header,
.text-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  margin-bottom: 16px;
}

.table-header h4,
.image-header h4,
.file-header h4,
.chart-header h4,
.text-header h4 {
  margin: 0;
  color: #2c3e50;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.table-meta {
  display: flex;
  gap: 8px;
  align-items: center;
}

.table-actions {
  display: flex;
  gap: 8px;
}

.table-container.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  background: white;
  padding: 20px;
}

.table-pagination {
  display: flex;
  justify-content: center;
  padding: 16px;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

.number-cell {
  font-family: 'Monaco', 'Menlo', monospace;
  font-weight: 600;
  text-align: right;
}

.image-container {
  text-align: center;
  padding: 20px;
}

.file-info {
  padding: 20px;
}

.file-info p {
  margin: 8px 0;
}

.chart-placeholder {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 6px;
  margin: 16px;
}

.chart-placeholder pre {
  background: white;
  padding: 16px;
  border-radius: 4px;
  border: 1px solid #e9ecef;
  max-height: 300px;
  overflow: auto;
}

.text-content {
  padding: 16px;
}

.text-content pre {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
  border: 1px solid #e9ecef;
  max-height: 400px;
  overflow: auto;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 14px;
  line-height: 1.6;
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

/* 图表样式 */
.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  margin-bottom: 16px;
}

.chart-actions {
  display: flex;
  gap: 8px;
}

.chart-container {
  position: relative;
  padding: 20px;
  background: white;
  border-radius: 6px;
  margin: 16px;
}

.chart-loading,
.chart-error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #6c757d;
  z-index: 10;
}

.loading-icon,
.error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.chart-data-table {
  margin-top: 20px;
  border-top: 1px solid #e9ecef;
}

.chart-data-table .table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.chart-data-table .table-header h5 {
  margin: 0;
  color: #2c3e50;
  font-size: 14px;
}

/* 图表全屏模式 */
.chart-result.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  background: white;
  padding: 20px;
}

.chart-result.fullscreen .chart-container {
  height: calc(100vh - 200px);
  margin: 0;
}
</style>

