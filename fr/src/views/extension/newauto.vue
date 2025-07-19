<template>
    <div class="extension-query-container">
      <div class="page-header">
        <h2>扩展查询中心</h2>
        <div class="header-actions">
          <div class="timer-controls">
            <el-tooltip content="自动刷新状态">
              <el-tag
                v-if="autoRefreshEnabled"
                type="success"
                size="small"
                effect="plain"
              >
                <el-icon><Timer /></el-icon>
                {{ autoRefreshInterval }}s
              </el-tag>
              <el-tag v-else type="info" size="small" effect="plain">
                <el-icon><SwitchButton /></el-icon>
                已暂停
              </el-tag>
            </el-tooltip>
            <el-button-group size="small">
              <el-tooltip :content="autoRefreshEnabled ? '暂停自动刷新' : '启动自动刷新'">
                <el-button
                  @click="toggleAutoRefresh"
                  :type="autoRefreshEnabled ? 'warning' : 'success'"
                >
                  <el-icon v-if="autoRefreshEnabled"><SwitchButton /></el-icon>
                  <el-icon v-else><CaretRight /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="设置刷新间隔">
                <el-button @click="showTimerSettings = true">
                  <el-icon><Tools /></el-icon>
                </el-button>
              </el-tooltip>
            </el-button-group>
          </div>
          <el-button @click="refreshAllAuto" type="primary" :loading="refreshing">
            <el-icon><Refresh /></el-icon> 手动刷新
          </el-button>
        </div>
      </div>
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="6" animated />
      </div>
  
      <!-- 主要内容 -->
      <div v-else class="extension-content">
        <!-- 自动执行扩展区域 -->
        <div class="extensions-section auto-extensions">
          <div class="section-header">
            <h3>自动执行扩展</h3>
            <span class="section-desc">页面加载时自动执行的扩展，显示系统状态和关键指标</span>
          </div>
  
          <div v-if="autoExtensions.length === 0" class="empty-section">
            <el-empty description="暂无自动执行扩展" />
          </div>
          <div v-else class="extension-cards">
            <el-card 
              v-for="ext in autoExtensions" 
              :key="ext.id" 
              class="extension-card"
              :class="{ 'card-loading': ext.loading, 'card-error': ext.error }"
              shadow="hover"
            >
              <template #header>
                <div class="card-header">
                  <h4>{{ ext.name }}</h4>
                  <div class="card-actions">
                    <el-tooltip content="刷新">
                      <el-button 
                        circle 
                        size="small" 
                        @click="refreshExtension(ext)" 
                        :loading="ext.loading"
                      >
                        <el-icon><Refresh /></el-icon>
                      </el-button>
                    </el-tooltip>
                    <el-tooltip content="详情">
                      <el-button 
                        circle 
                        size="small" 
                        @click="viewExtensionDetail(ext)"
                      >
                        <el-icon><InfoFilled /></el-icon>
                      </el-button>
                    </el-tooltip>
                  </div>
                </div>
              </template>
              
              <div v-if="ext.loading" class="card-content loading">
                <el-skeleton :rows="2" animated />
              </div>
              <div v-else-if="ext.error" class="card-content error">
                <el-alert
                  type="error"
                  :title="ext.error"
                  :closable="false"
                  show-icon
                />
              </div>
              <div v-else class="card-content">
                <!-- 智能结果显示 -->
                <div class="result-container" @click="expandResult(ext)">
                  <!-- HTML类型 -->
                  <div v-if="getResultType(ext.result) === 'html'" class="html-result">
                    <div v-html="getResultData(ext.result)" class="html-content"></div>
                  </div>

                  <!-- 表格类型 -->
                  <div v-else-if="getResultType(ext.result) === 'table'" class="table-result">
                    <div class="table-summary">
                      <el-icon><Grid /></el-icon>
                      <span>{{ getTableRowCount(ext.result) }} 条记录</span>
                      <el-tag size="small" type="info">表格数据</el-tag>
                    </div>
                    <div class="table-preview">
                      <el-table
                        :data="getTablePreview(ext.result)"
                        size="small"
                        max-height="200"
                        border
                      >
                        <el-table-column
                          v-for="column in getTableColumns(ext.result)"
                          :key="column.prop"
                          :prop="column.prop"
                          :label="column.label"
                          show-overflow-tooltip
                          min-width="80"
                        />
                      </el-table>
                      <div v-if="getTableRowCount(ext.result) > 3" class="table-more">
                        还有 {{ getTableRowCount(ext.result) - 3 }} 条记录，点击查看全部
                      </div>
                    </div>
                  </div>

                  <!-- 图表类型 -->
                  <div v-else-if="getResultType(ext.result) === 'chart'" class="chart-result">
                    <div class="chart-summary">
                      <el-icon><PieChart /></el-icon>
                      <span>{{ getChartType(ext.result) }}</span>
                      <el-tag size="small" type="success">图表数据</el-tag>
                    </div>
                    <div class="chart-preview">
                      <canvas :ref="`chart-${ext.id}`" class="chart-canvas"></canvas>
                    </div>
                  </div>

                  <!-- 文本类型 -->
                  <div v-else-if="getResultType(ext.result) === 'text'" class="text-result">
                    <div class="text-preview">
                      {{ getTextPreview(ext.result) }}
                    </div>
                    <div v-if="isTextTruncated(ext.result)" class="text-more">
                      点击查看完整内容
                    </div>
                  </div>

                  <!-- 图片类型 -->
                  <div v-else-if="getResultType(ext.result) === 'image'" class="image-result">
                    <div class="image-summary">
                      <el-icon><Picture /></el-icon>
                      <span>图片结果</span>
                      <el-tag size="small" type="warning">图片</el-tag>
                    </div>
                    <div class="image-preview">
                      <img :src="getResultData(ext.result)" alt="扩展结果图片" />
                    </div>
                  </div>

                  <!-- 文件类型 -->
                  <div v-else-if="getResultType(ext.result) === 'file'" class="file-result">
                    <div class="file-summary">
                      <el-icon><Folder /></el-icon>
                      <span>{{ getFileName(ext.result) }}</span>
                      <el-tag size="small" type="primary">文件</el-tag>
                    </div>
                    <div class="file-info">
                      <p>类型: {{ getFileType(ext.result) }}</p>
                      <p>大小: {{ getFileSize(ext.result) }}</p>
                    </div>
                  </div>

                  <!-- 状态类型 -->
                  <div v-else-if="ext.render_type === 'status'" class="status-result">
                    <el-tag
                      :type="getStatusType(ext.result)"
                      size="large"
                      effect="dark"
                    >
                      {{ getResultData(ext.result) }}
                    </el-tag>
                  </div>

                  <!-- 未知类型 -->
                  <div v-else class="unknown-result">
                    <div class="unknown-summary">
                      <el-icon><Document /></el-icon>
                      <span>数据结果</span>
                      <el-tag size="small">{{ getResultType(ext.result) }}</el-tag>
                    </div>
                    <div class="unknown-preview">
                      {{ getUnknownPreview(ext.result) }}
                    </div>
                  </div>
                </div>

                <div class="card-footer">
                  <div class="footer-left">
                    <span class="update-time">{{ formatTime(ext.lastUpdate) }}</span>
                  </div>
                  <div class="footer-right">
                    <el-button size="small" text @click.stop="expandResult(ext)">
                      <el-icon><FullScreen /></el-icon>
                      查看详情
                    </el-button>
                  </div>
                </div>
              </div>
            </el-card>
          </div>
        </div>
  
        <!-- 手动执行扩展区域 -->
        <div class="extensions-section manual-extensions">
          <div class="section-header">
            <h3>手动执行扩展</h3>
            <span class="section-desc">需要手动触发的数据查询和分析工具</span>
          </div>
  
          <div v-if="manualExtensions.length === 0" class="empty-section">
            <el-empty description="暂无手动执行扩展" />
          </div>
          <div v-else class="extension-list">
            <el-table
              :data="manualExtensions"
              style="width: 100%"
              border
            >
              <el-table-column prop="name" label="扩展名称" min-width="180">
                <template #default="scope">
                  <div class="extension-name">
                    <el-icon v-if="scope.row.render_type === 'table'"><Grid /></el-icon>
                    <el-icon v-else-if="scope.row.render_type === 'chart'"><PieChart /></el-icon>
                    <el-icon v-else-if="scope.row.render_type === 'image'"><Picture /></el-icon>
                    <el-icon v-else><Document /></el-icon>
                    <span>{{ scope.row.name }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="description" label="描述" min-width="300" show-overflow-tooltip />
              <el-table-column prop="render_type" label="结果类型" width="120">
                <template #default="scope">
                  <el-tag>{{ formatRenderType(scope.row.render_type) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="180">
                <template #default="scope">
                  <el-button 
                    type="primary" 
                    size="small" 
                    @click="executeManualExtension(scope.row)"
                  >
                    执行查询
                  </el-button>
                  <el-button
                    size="small"
                    @click="viewExtensionDetail(scope.row)"
                  >
                    详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
  
      <!-- 定时器设置对话框 -->
      <el-dialog
        v-model="showTimerSettings"
        title="自动刷新设置"
        width="500px"
      >
        <el-form :model="timerSettings" label-width="120px">
          <el-form-item label="启用自动刷新">
            <el-switch v-model="timerSettings.enabled" />
          </el-form-item>
          <el-form-item label="刷新间隔" v-if="timerSettings.enabled">
            <el-input-number
              v-model="timerSettings.interval"
              :min="5"
              :max="300"
              :step="5"
            />
            <span style="margin-left: 8px; color: #6c757d;">秒</span>
          </el-form-item>
          <el-form-item label="刷新提醒">
            <el-switch v-model="timerSettings.showNotification" />
            <div style="font-size: 12px; color: #6c757d; margin-top: 4px;">
              刷新完成后显示通知消息
            </div>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showTimerSettings = false">取消</el-button>
          <el-button type="primary" @click="saveTimerSettings">保存设置</el-button>
        </template>
      </el-dialog>

      <!-- 扩展结果详情对话框 -->
      <el-dialog
        v-model="resultDialogVisible"
        :title="currentExtension.name || '扩展结果'"
        width="90%"
        :fullscreen="resultFullscreen"
        destroy-on-close
        class="result-detail-dialog"
      >
        <template #header="{ titleId, titleClass }">
          <div class="dialog-header">
            <h4 :id="titleId" :class="titleClass">
              {{ currentExtension.name || '扩展结果' }}
            </h4>
            <div class="dialog-header-actions">
              <el-tag v-if="currentResult" :type="getResultStatusType()" size="small">
                {{ getResultType(currentResult) }}
              </el-tag>
              <el-button-group size="small">
                <el-tooltip content="全屏切换">
                  <el-button @click="resultFullscreen = !resultFullscreen">
                    <el-icon><FullScreen /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="重新执行">
                  <el-button @click="refreshCurrentExtension" :loading="resultLoading">
                    <el-icon><Refresh /></el-icon>
                  </el-button>
                </el-tooltip>
              </el-button-group>
            </div>
          </div>
        </template>

        <div v-if="resultLoading" class="dialog-loading">
          <el-skeleton :rows="10" animated />
        </div>
        <div v-else-if="resultError" class="dialog-error">
          <el-alert
            type="error"
            :title="resultError"
            :description="'执行扩展查询失败'"
            show-icon
          />
        </div>
        <div v-else class="dialog-content">
          <!-- 智能结果渲染 -->
          <div class="result-detail">
            <!-- HTML类型 -->
            <div v-if="getResultType(currentResult) === 'html'" class="html-detail">
              <div v-html="getResultData(currentResult)" class="html-content-full"></div>
            </div>

            <!-- 表格类型 -->
            <div v-else-if="getResultType(currentResult) === 'table'" class="table-detail">
              <div class="table-toolbar">
                <div class="table-info">
                  <el-tag type="info">{{ getTableRowCount(currentResult) }} 条记录</el-tag>
                  <el-tag type="success">{{ getTableColumns(currentResult).length }} 列</el-tag>
                </div>
                <div class="table-actions">
                  <el-button size="small" @click="exportTableData('csv')">
                    <el-icon><Download /></el-icon>
                    导出CSV
                  </el-button>
                  <el-button size="small" @click="exportTableData('json')">
                    <el-icon><Folder /></el-icon>
                    导出JSON
                  </el-button>
                </div>
              </div>
              <el-table
                :data="getTableData(currentResult)"
                border
                stripe
                height="60vh"
                style="width: 100%"
              >
                <el-table-column
                  v-for="column in getTableColumns(currentResult)"
                  :key="column.prop"
                  :prop="column.prop"
                  :label="column.label"
                  show-overflow-tooltip
                  sortable
                />
              </el-table>
            </div>

            <!-- 图表类型 -->
            <div v-else-if="getResultType(currentResult) === 'chart'" class="chart-detail">
              <div class="chart-toolbar">
                <div class="chart-info">
                  <el-tag type="success">{{ getChartType(currentResult) }}</el-tag>
                </div>
                <div class="chart-actions">
                  <el-button size="small" @click="exportChart('png')">
                    <el-icon><Picture /></el-icon>
                    导出PNG
                  </el-button>
                  <el-button size="small" @click="showChartData = !showChartData">
                    <el-icon><Grid /></el-icon>
                    {{ showChartData ? '隐藏数据' : '显示数据' }}
                  </el-button>
                </div>
              </div>
              <div class="chart-container">
                <canvas :ref="`detail-chart-${currentExtension.id}`" class="chart-canvas-full"></canvas>
              </div>
              <div v-if="showChartData" class="chart-data-table">
                <el-table :data="getChartTableData(currentResult)" border stripe max-height="300">
                  <el-table-column
                    v-for="column in getChartTableColumns(currentResult)"
                    :key="column.prop"
                    :prop="column.prop"
                    :label="column.label"
                    show-overflow-tooltip
                  />
                </el-table>
              </div>
            </div>

            <!-- 文本类型 -->
            <div v-else-if="getResultType(currentResult) === 'text'" class="text-detail">
              <div class="text-toolbar">
                <div class="text-info">
                  <el-tag type="info">{{ getTextStats(currentResult).chars }} 字符</el-tag>
                  <el-tag type="success">{{ getTextStats(currentResult).lines }} 行</el-tag>
                </div>
                <div class="text-actions">
                  <el-button size="small" @click="copyText">
                    <el-icon><DocumentCopy /></el-icon>
                    复制文本
                  </el-button>
                </div>
              </div>
              <div class="text-content-full">
                <pre>{{ getResultData(currentResult) }}</pre>
              </div>
            </div>

            <!-- 图片类型 -->
            <div v-else-if="getResultType(currentResult) === 'image'" class="image-detail">
              <div class="image-toolbar">
                <div class="image-info">
                  <el-tag type="warning">图片结果</el-tag>
                </div>
                <div class="image-actions">
                  <el-button size="small" @click="downloadImage">
                    <el-icon><Download /></el-icon>
                    下载图片
                  </el-button>
                </div>
              </div>
              <div class="image-container">
                <img :src="getResultData(currentResult)" alt="扩展结果图片" class="image-full" />
              </div>
            </div>

            <!-- 文件类型 -->
            <div v-else-if="getResultType(currentResult) === 'file'" class="file-detail">
              <div class="file-info-card">
                <div class="file-icon">
                  <el-icon size="48"><Folder /></el-icon>
                </div>
                <div class="file-details">
                  <h3>{{ getFileName(currentResult) }}</h3>
                  <p>类型: {{ getFileType(currentResult) }}</p>
                  <p>大小: {{ getFileSize(currentResult) }}</p>
                </div>
                <div class="file-actions">
                  <el-button type="primary" @click="downloadFile" size="large">
                    <el-icon><Download /></el-icon>
                    下载文件
                  </el-button>
                </div>
              </div>
            </div>

            <!-- 未知类型 -->
            <div v-else class="unknown-detail">
              <div class="unknown-toolbar">
                <el-tag>{{ getResultType(currentResult) }}</el-tag>
                <el-button size="small" @click="copyRawData">
                  <el-icon><DocumentCopy /></el-icon>
                  复制原始数据
                </el-button>
              </div>
              <div class="unknown-content">
                <pre>{{ JSON.stringify(currentResult, null, 2) }}</pre>
              </div>
            </div>
          </div>
        </div>

        <template #footer>
          <span class="dialog-footer">
            <el-button @click="resultDialogVisible = false">关闭</el-button>
            <el-button type="primary" @click="refreshCurrentExtension" :loading="resultLoading">
              重新执行
            </el-button>
          </span>
        </template>
      </el-dialog>
    </div>
  </template>
  
  <script>
  import { defineComponent, ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
  import { useRouter } from 'vue-router'
  import { ElMessage } from 'element-plus'
  import {
    Refresh, InfoFilled, Document, Grid, PieChart, Picture,
    Timer, SwitchButton, CaretRight, Tools, FullScreen,
    Folder, Download, DocumentCopy
  } from '@element-plus/icons-vue'
  import axios from '@/utils/axios'
  import TableResult from '@/components/extension/TableResult.vue'
  import TextResult from '@/components/extension/TextResult.vue'
  import ChartResult from '@/components/extension/ChartResult.vue'
  import ImageResult from '@/components/extension/ImageResult.vue'
  
  // 正确的API函数
  const getExtensions = async () => {
    const res = await axios.get('/api/extensions')
      return res.data
  }
  
  const getExtension = async (id) => {
    const res = await axios.get(`/api/extensions/${id}`)
      return res.data
  }
  
  // 修正后的查询函数 - 使用正确的路径格式
  const executeExtensionQuery = async (id, formData) => {
    const form = new FormData()
    
  // 即使没有数据，也确保表单格式正确
  if (Object.keys(formData).length === 0) {
    // 添加一个空字段确保格式正确
    form.append('_dummy', '')
  } else {
    // 将formData中的数据添加到FormData对象
    Object.keys(formData).forEach(key => {
      const value = formData[key]
      if (value instanceof File) {
        form.append(key, value, value.name)
      } else if (value !== null && value !== undefined) {
        form.append(key, value)
      }
    })
  }
    
  // 发送请求，确保使用正确的content-type
  return axios.post(`/query/${id}`, form, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  }).then(res => res.data)
}
  
  export default defineComponent({
    name: 'ExtensionQueryView',
    components: {
      TableResult,
      TextResult,
      ChartResult,
      ImageResult,
      Refresh,
      InfoFilled,
      Document,
      Grid,
      PieChart,
      Picture
    },
    setup() {
      const router = useRouter()
      const loading = ref(true)
      const refreshing = ref(false)
      const extensions = ref([])
      const resultDialogVisible = ref(false)
      const resultLoading = ref(false)
      const resultError = ref('')
      const queryResult = ref(null)
      const currentExtension = ref({})
      const currentResult = ref(null)
      const resultFullscreen = ref(false)
      const showChartData = ref(false)

      // 定时器相关
      const autoRefreshEnabled = ref(false)
      const autoRefreshInterval = ref(30)
      const autoRefreshTimer = ref(null)
      const showTimerSettings = ref(false)
      const timerSettings = ref({
        enabled: false,
        interval: 30,
        showNotification: true
      })
  
      // 计算属性：自动执行扩展
      const autoExtensions = computed(() => {
        return extensions.value.filter(ext => ext.execution_mode === 'auto')
      })
  
      // 计算属性：手动执行扩展
      const manualExtensions = computed(() => {
        return extensions.value.filter(ext => ext.execution_mode === 'manual')
      })
  
      // 加载所有扩展
      const loadExtensions = async () => {
        try {
          loading.value = true
          const response = await getExtensions()
          extensions.value = response.map(ext => ({
            ...ext,
            loading: false,
            error: null,
            result: null,
            lastUpdate: null
          }))
          
          // 自动执行所有自动扩展
          await executeAutoExtensions()
        } catch (error) {
          ElMessage.error('加载扩展列表失败: ' + (error.message || '未知错误'))
          console.error('加载扩展列表失败:', error)
        } finally {
          loading.value = false
        }
      }
  
      // 执行所有自动扩展
      const executeAutoExtensions = async () => {
        const autoExts = extensions.value.filter(ext => ext.execution_mode === 'auto')
        
        // 并行执行所有自动扩展
        await Promise.all(autoExts.map(async (ext) => {
          await executeExtension(ext)
        }))
      }
  
// 执行单个扩展
const executeExtension = async (extension) => {
  // 找到扩展在数组中的索引
  const index = extensions.value.findIndex(e => e.id === extension.id)
  if (index === -1) return
  
  try {
    // 设置加载状态
    extensions.value[index].loading = true
    extensions.value[index].error = null
    
    // 执行查询 - 传递一个空对象确保表单格式正确
    const response = await executeExtensionQuery(extension.id, { _dummy: '' })
    
    // 更新结果
    extensions.value[index].result = response.result || response
    extensions.value[index].lastUpdate = new Date()
  } catch (error) {
    extensions.value[index].error = error.message || '查询执行失败'
    console.error(`执行扩展 ${extension.name} 失败:`, error)
  } finally {
    extensions.value[index].loading = false
  }
}  
      // 刷新所有自动扩展
      const refreshAllAuto = async () => {
        if (refreshing.value) return
        
        try {
          refreshing.value = true
          await executeAutoExtensions()
          ElMessage.success('自动扩展刷新完成')
        } catch (error) {
          ElMessage.error('刷新自动扩展失败')
        } finally {
          refreshing.value = false
        }
      }
  
      // 刷新单个扩展
      const refreshExtension = async (extension) => {
        await executeExtension(extension)
      }
  
      // 查看扩展详情
      const viewExtensionDetail = (extension) => {
        router.push(`/extension/${extension.id}`)
      }
  
      // 执行手动扩展
      const executeManualExtension = async (extension) => {
        currentExtension.value = extension
        resultDialogVisible.value = true
        resultLoading.value = true
        resultError.value = ''
        queryResult.value = null
        
        try {
          const response = await executeExtensionQuery(extension.id, {})
          queryResult.value = response.result || response
        } catch (error) {
          resultError.value = error.message || '查询执行失败'
          console.error(`执行扩展 ${extension.name} 失败:`, error)
        } finally {
          resultLoading.value = false
        }
      }
  
      // 定时器相关方法
      const toggleAutoRefresh = () => {
        autoRefreshEnabled.value = !autoRefreshEnabled.value
        if (autoRefreshEnabled.value) {
          startAutoRefresh()
        } else {
          stopAutoRefresh()
        }
      }

      const startAutoRefresh = () => {
        stopAutoRefresh() // 先停止现有定时器
        autoRefreshTimer.value = setInterval(() => {
          refreshAllAuto()
          if (timerSettings.value.showNotification) {
            ElMessage.success('自动刷新完成')
          }
        }, autoRefreshInterval.value * 1000)
      }

      const stopAutoRefresh = () => {
        if (autoRefreshTimer.value) {
          clearInterval(autoRefreshTimer.value)
          autoRefreshTimer.value = null
        }
      }

      const saveTimerSettings = () => {
        autoRefreshEnabled.value = timerSettings.value.enabled
        autoRefreshInterval.value = timerSettings.value.interval

        if (autoRefreshEnabled.value) {
          startAutoRefresh()
        } else {
          stopAutoRefresh()
        }

        // 保存到localStorage
        localStorage.setItem('autoRefreshSettings', JSON.stringify(timerSettings.value))

        showTimerSettings.value = false
        ElMessage.success('设置已保存')
      }

      const loadTimerSettings = () => {
        try {
          const saved = localStorage.getItem('autoRefreshSettings')
          if (saved) {
            const settings = JSON.parse(saved)
            timerSettings.value = { ...timerSettings.value, ...settings }
            autoRefreshEnabled.value = settings.enabled
            autoRefreshInterval.value = settings.interval

            if (autoRefreshEnabled.value) {
              startAutoRefresh()
            }
          }
        } catch (error) {
          console.error('加载定时器设置失败:', error)
        }
      }

      // 结果详情相关方法
      const expandResult = (extension) => {
        currentExtension.value = extension
        currentResult.value = extension.result
        resultDialogVisible.value = true
      }

      // 导出相关方法
      const exportTableData = (format) => {
        const data = getTableData(currentResult.value)
        if (data.length === 0) {
          ElMessage.warning('没有数据可导出')
          return
        }

        try {
          if (format === 'csv') {
            const columns = getTableColumns(currentResult.value)
            const headers = columns.map(col => col.label).join(',')
            const rows = data.map(row =>
              columns.map(col => {
                const value = row[col.prop]
                return typeof value === 'string' && value.includes(',')
                  ? `"${value}"`
                  : value
              }).join(',')
            )
            const csvContent = [headers, ...rows].join('\n')
            downloadFile(csvContent, 'table-data.csv', 'text/csv')
          } else if (format === 'json') {
            const jsonContent = JSON.stringify(data, null, 2)
            downloadFile(jsonContent, 'table-data.json', 'application/json')
          }
          ElMessage.success(`${format.toUpperCase()}文件已下载`)
        } catch (error) {
          ElMessage.error('导出失败: ' + error.message)
        }
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

      const copyText = async () => {
        try {
          const text = getResultData(currentResult.value)
          await navigator.clipboard.writeText(text)
          ElMessage.success('文本已复制到剪贴板')
        } catch (error) {
          ElMessage.error('复制失败')
        }
      }

      const copyRawData = async () => {
        try {
          const text = JSON.stringify(currentResult.value, null, 2)
          await navigator.clipboard.writeText(text)
          ElMessage.success('原始数据已复制到剪贴板')
        } catch (error) {
          ElMessage.error('复制失败')
        }
      }

      // 刷新当前手动扩展
      const refreshCurrentExtension = () => {
        executeManualExtension(currentExtension.value)
      }
  
      // 格式化渲染类型
      const formatRenderType = (type) => {
        switch (type) {
          case 'table': return '表格'
          case 'chart': return '图表'
          case 'image': return '图片'
          case 'text': return '文本'
          case 'status': return '状态'
          default: return type
        }
      }
  
      // 结果类型识别和处理方法
      const getResultType = (result) => {
        if (result && typeof result === 'object' && result.type) {
          return result.type
        }
        // 根据数据结构推断类型
        if (typeof result === 'string') {
          if (result.includes('<') && result.includes('>')) {
            return 'html'
          }
          return 'text'
        }
        if (Array.isArray(result)) {
          return 'table'
        }
        if (result && typeof result === 'object') {
          if (result.chart_type || result.chart_data) {
            return 'chart'
          }
          if (result.filename || result.file_path) {
            return 'file'
          }
        }
        return 'unknown'
      }

      const getResultData = (result) => {
        if (result && typeof result === 'object' && result.data !== undefined) {
          return result.data
        }
        return result
      }

      const getResultMeta = (result) => {
        if (result && typeof result === 'object' && result.meta) {
          return result.meta
        }
        return {}
      }

      // 表格相关方法
      const getTableData = (result) => {
        const data = getResultData(result)
        return Array.isArray(data) ? data : []
      }

      const getTableRowCount = (result) => {
        return getTableData(result).length
      }

      const getTablePreview = (result) => {
        return getTableData(result).slice(0, 3)
      }

      const getTableColumns = (result) => {
        const data = getTableData(result)
        if (data.length === 0) return []

        const firstRow = data[0]
        return Object.keys(firstRow).map(key => ({
          prop: key,
          label: key
        }))
      }

      // 图表相关方法
      const getChartType = (result) => {
        const data = getResultData(result)
        if (data && data.chart_type) {
          return data.chart_type
        }
        return '图表'
      }

      // 文本相关方法
      const getTextPreview = (result) => {
        const text = getResultData(result)
        if (typeof text !== 'string') return String(text)
        return text.length > 200 ? text.substring(0, 200) + '...' : text
      }

      const isTextTruncated = (result) => {
        const text = getResultData(result)
        return typeof text === 'string' && text.length > 200
      }

      const getTextStats = (result) => {
        const text = getResultData(result)
        if (typeof text !== 'string') return { chars: 0, lines: 0 }
        return {
          chars: text.length,
          lines: text.split('\n').length
        }
      }

      // 文件相关方法
      const getFileName = (result) => {
        const data = getResultData(result)
        return data?.filename || data?.file_path || '未知文件'
      }

      const getFileType = (result) => {
        const data = getResultData(result)
        return data?.content_type || '未知类型'
      }

      const getFileSize = (result) => {
        const data = getResultData(result)
        const size = data?.size
        if (!size) return '未知大小'

        const units = ['B', 'KB', 'MB', 'GB']
        let unitIndex = 0
        let fileSize = size

        while (fileSize >= 1024 && unitIndex < units.length - 1) {
          fileSize /= 1024
          unitIndex++
        }

        return `${fileSize.toFixed(1)} ${units[unitIndex]}`
      }

      // 未知类型预览
      const getUnknownPreview = (result) => {
        const str = JSON.stringify(result, null, 2)
        return str.length > 300 ? str.substring(0, 300) + '...' : str
      }

      const getResultStatusType = () => {
        if (!currentResult.value) return 'info'
        const type = getResultType(currentResult.value)
        const typeMap = {
          'html': 'primary',
          'table': 'success',
          'text': 'info',
          'chart': 'warning',
          'image': 'danger',
          'file': 'primary'
        }
        return typeMap[type] || 'info'
      }

      // 获取状态类型
      const getStatusType = (status) => {
        if (!status) return 'info'
        
        const statusText = String(status).toLowerCase()
        if (statusText.includes('正常') || 
            statusText.includes('成功') || 
            statusText.includes('ok') || 
            statusText.includes('normal') || 
            statusText.includes('success')) {
          return 'success'
        }
        
        if (statusText.includes('警告') || 
            statusText.includes('注意') || 
            statusText.includes('warn') || 
            statusText.includes('warning')) {
          return 'warning'
        }
        
        if (statusText.includes('错误') || 
            statusText.includes('失败') || 
            statusText.includes('error') || 
            statusText.includes('fail') || 
            statusText.includes('down')) {
          return 'danger'
        }
        
        return 'info'
      }
  
      // 获取结果组件
      const getResultComponent = (renderType) => {
        switch (renderType) {
          case 'table': return 'TableResult'
          case 'chart': return 'ChartResult'
          case 'image': return 'ImageResult'
          case 'text':
          case 'status':
          default: return 'TextResult'
        }
      }
  
      // 格式化时间
      const formatTime = (time) => {
        if (!time) return '未更新'
        return new Date(time).toLocaleString()
      }
  
      // 生命周期钩子
      onMounted(() => {
        loadExtensions()
        loadTimerSettings()
      })

      // 组件卸载时清理定时器
      onUnmounted(() => {
        stopAutoRefresh()
      })
  
      return {
        loading,
        refreshing,
        extensions,
        autoExtensions,
        manualExtensions,
        resultDialogVisible,
        resultLoading,
        resultError,
        queryResult,
        currentExtension,
        currentResult,
        resultFullscreen,
        showChartData,
        // 定时器相关
        autoRefreshEnabled,
        autoRefreshInterval,
        showTimerSettings,
        timerSettings,
        toggleAutoRefresh,
        saveTimerSettings,
        // 结果处理方法
        getResultType,
        getResultData,
        getResultMeta,
        getTableData,
        getTableRowCount,
        getTablePreview,
        getTableColumns,
        getChartType,
        getTextPreview,
        isTextTruncated,
        getTextStats,
        getFileName,
        getFileType,
        getFileSize,
        getUnknownPreview,
        getResultStatusType,
        expandResult,
        exportTableData,
        copyText,
        copyRawData,
        // 原有方法
        loadExtensions,
        refreshAllAuto,
        refreshExtension,
        viewExtensionDetail,
        executeManualExtension,
        refreshCurrentExtension,
        formatRenderType,
        getStatusType,
        getResultComponent,
        formatTime
      }
    }
  })
  </script>
  
  <style scoped>
  .extension-query-container {
    padding: 20px;
    width: 100%;
    margin: 0 auto;
  }
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid #ebeef5;
  }
  
  .page-header h2 {
    margin: 0;
    font-size: 24px;
    color: #303133;
  }
  
  .extensions-section {
    margin-bottom: 30px;
    padding: 20px;
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  }
  
  .auto-extensions {
    border-left: 4px solid #409eff;
  }
  
  .manual-extensions {
    border-left: 4px solid #67c23a;
  }
  
  .section-header {
    margin-bottom: 20px;
  }
  
  .section-header h3 {
    margin: 0 0 8px 0;
    font-size: 18px;
    color: #303133;
  }
  
  .section-desc {
    font-size: 14px;
    color: #909399;
  }
  
  .extension-cards {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
  }
  
  .extension-card {
    transition: all 0.3s;
  }
  
  .extension-card:hover {
    transform: translateY(-5px);
  }
  
  .card-loading {
    opacity: 0.8;
  }
  
  .card-error {
    border: 1px solid #f56c6c;
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .card-header h4 {
    margin: 0;
    font-size: 16px;
    font-weight: 500;
  }
  
  .card-actions {
    display: flex;
    gap: 5px;
  }
  
  .card-content {
    min-height: 80px;
    display: flex;
    flex-direction: column;
  }
  
  .card-content.loading,
  .card-content.error {
    justify-content: center;
  }
  
  .text-result {
    font-size: 16px;
    line-height: 1.5;
    word-break: break-word;
  }
  
  .status-result {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 80px;
  }
  
  .status-result .el-tag {
    font-size: 18px;
    padding: 8px 16px;
  }
  
  .card-footer {
    margin-top: 15px;
    font-size: 12px;
    color: #909399;
    text-align: right;
  }
  
  .extension-name {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .empty-section {
    padding: 30px;
  }
  
  .dialog-loading,
  .dialog-error {
    padding: 20px;
  }
  
  .dialog-content {
    max-height: 70vh;
    overflow-y: auto;
  }
  
  @media (max-width: 768px) {
    .extension-cards {
      grid-template-columns: 1fr;
    }
  }

  /* 新增样式 */
  .header-actions {
    display: flex;
    gap: 12px;
    align-items: center;
  }

  .timer-controls {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  /* 结果容器样式 */
  .result-container {
    cursor: pointer;
    transition: all 0.3s ease;
    border-radius: 6px;
    padding: 12px;
    background: #f8f9fa;
    margin-bottom: 12px;
  }

  .result-container:hover {
    background: #e9ecef;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  /* 表格预览样式 */
  .table-summary {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    font-weight: 600;
    color: #495057;
  }

  .table-preview {
    background: white;
    border-radius: 4px;
    overflow: hidden;
  }

  .table-more {
    text-align: center;
    padding: 8px;
    background: #f8f9fa;
    color: #6c757d;
    font-size: 12px;
  }

  /* 图表预览样式 */
  .chart-summary {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    font-weight: 600;
    color: #495057;
  }

  .chart-preview {
    background: white;
    border-radius: 4px;
    padding: 16px;
    text-align: center;
  }

  .chart-canvas {
    max-width: 100%;
    max-height: 200px;
  }

  /* 文本预览样式 */
  .text-preview {
    background: white;
    border-radius: 4px;
    padding: 12px;
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 13px;
    line-height: 1.5;
    white-space: pre-wrap;
    word-wrap: break-word;
    max-height: 150px;
    overflow: hidden;
  }

  .text-more {
    text-align: center;
    padding: 8px;
    color: #6c757d;
    font-size: 12px;
  }

  /* 图片预览样式 */
  .image-summary {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    font-weight: 600;
    color: #495057;
  }

  .image-preview {
    text-align: center;
    background: white;
    border-radius: 4px;
    padding: 12px;
  }

  .image-preview img {
    max-width: 100%;
    max-height: 200px;
    object-fit: contain;
    border-radius: 4px;
  }

  /* 文件预览样式 */
  .file-summary {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    font-weight: 600;
    color: #495057;
  }

  .file-info {
    background: white;
    border-radius: 4px;
    padding: 12px;
  }

  .file-info p {
    margin: 4px 0;
    font-size: 13px;
    color: #6c757d;
  }

  /* 卡片底部样式 */
  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #e9ecef;
  }

  .footer-left {
    flex: 1;
  }

  .footer-right {
    flex-shrink: 0;
  }

  /* 对话框样式 */
  .result-detail-dialog .el-dialog__body {
    padding: 0;
  }

  .dialog-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
  }

  .dialog-header-actions {
    display: flex;
    gap: 12px;
    align-items: center;
  }

  /* 详情页面样式 */
  .result-detail {
    padding: 20px;
  }

  .html-content-full {
    background: white;
    border-radius: 8px;
    padding: 20px;
    min-height: 400px;
  }

  .table-toolbar,
  .chart-toolbar,
  .text-toolbar,
  .image-toolbar,
  .unknown-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding: 12px 16px;
    background: #f8f9fa;
    border-radius: 6px;
  }

  .table-info,
  .chart-info,
  .text-info,
  .image-info {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .table-actions,
  .chart-actions,
  .text-actions,
  .image-actions {
    display: flex;
    gap: 8px;
  }

  .chart-container {
    background: white;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 16px;
  }

  .chart-canvas-full {
    width: 100% !important;
    height: 400px !important;
  }

  .text-content-full {
    background: white;
    border-radius: 8px;
    padding: 20px;
    max-height: 60vh;
    overflow: auto;
  }

  .text-content-full pre {
    margin: 0;
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 14px;
    line-height: 1.6;
    white-space: pre-wrap;
    word-wrap: break-word;
  }

  .image-container {
    text-align: center;
    background: white;
    border-radius: 8px;
    padding: 20px;
  }

  .image-full {
    max-width: 100%;
    max-height: 70vh;
    object-fit: contain;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .file-info-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    background: white;
    border-radius: 12px;
    padding: 40px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    max-width: 400px;
    margin: 0 auto;
  }

  .file-icon {
    color: #409eff;
    margin-bottom: 20px;
  }

  .file-details h3 {
    margin: 0 0 16px 0;
    color: #2c3e50;
  }

  .file-details p {
    margin: 8px 0;
    color: #6c757d;
  }

  .file-actions {
    margin-top: 24px;
  }
  </style>