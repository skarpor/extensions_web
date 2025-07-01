<template>
    <div class="extension-query-container">
      <div class="page-header">
        <h2>扩展查询中心</h2>
        <div class="header-actions">
          <el-button @click="refreshAllAuto" type="primary" :loading="refreshing">
            <el-icon><Refresh /></el-icon> 刷新自动扩展
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
                <!-- 根据扩展的render_type选择不同的渲染方式 -->
                <div v-if="ext.render_type === 'text'" class="text-result">
                  {{ ext.result }}
                </div>
                <div v-else-if="ext.render_type === 'status'" class="status-result">
                  <el-tag 
                    :type="getStatusType(ext.result)" 
                    size="large"
                    effect="dark"
                  >
                    {{ ext.result }}
                  </el-tag>
                </div>
                <div v-else class="generic-result">
                  <component 
                    :is="getResultComponent(ext.render_type)"
                    :result="ext.result"
                    :extension="ext"
                    :loading="false"
                    :compact="true"
                  />
                </div>
                
                <div class="card-footer">
                  <span class="update-time">更新时间: {{ formatTime(ext.lastUpdate) }}</span>
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
  
      <!-- 手动扩展执行结果对话框 -->
      <el-dialog
        v-model="resultDialogVisible"
        :title="currentExtension.name"
        width="80%"
        destroy-on-close
      >
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
          <component 
            :is="getResultComponent(currentExtension.render_type)"
            :result="queryResult"
            :extension="currentExtension"
            :loading="false"
          />
        </div>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="resultDialogVisible = false">关闭</el-button>
            <el-button type="primary" @click="refreshCurrentExtension">
              重新执行
            </el-button>
          </span>
        </template>
      </el-dialog>
    </div>
  </template>
  
  <script>
  import { defineComponent, ref, computed, onMounted } from 'vue'
  import { useRouter } from 'vue-router'
  import { ElMessage } from 'element-plus'
  import { 
    Refresh, InfoFilled, Document, Grid, PieChart, Picture 
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
    max-width: 1200px;
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
  </style>