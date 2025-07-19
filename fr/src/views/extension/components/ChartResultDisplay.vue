<template>
  <div class="chart-result-display">
    <!-- 图表工具栏 -->
    <div class="chart-toolbar">
      <div class="toolbar-left">
        <el-tag type="info" size="small">
          {{ chartConfig.type || 'chart' }} 图表
        </el-tag>
        <el-tag v-if="meta?.generated_at" type="success" size="small">
          {{ formatDate(meta.generated_at) }}
        </el-tag>
      </div>
      
      <div class="toolbar-right">
        <el-button-group size="small">
          <el-button @click="refreshChart">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <el-button @click="exportChart('png')">
            <el-icon><Picture /></el-icon>
            PNG
          </el-button>
          <el-button @click="exportChart('svg')">
            <el-icon><Document /></el-icon>
            SVG
          </el-button>
          <el-button @click="toggleFullscreen">
            <el-icon><FullScreen /></el-icon>
            全屏
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 图表容器 -->
    <div class="chart-container" :class="{ fullscreen: isFullscreen }">
      <div ref="chartElement" class="chart-element" :style="chartStyle"></div>
      
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-overlay">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <p>图表渲染中...</p>
      </div>
      
      <!-- 错误状态 -->
      <div v-if="error" class="error-overlay">
        <el-icon class="error-icon"><Warning /></el-icon>
        <p>图表渲染失败</p>
        <p class="error-message">{{ error }}</p>
        <el-button @click="retryRender" size="small">重试</el-button>
      </div>
    </div>

    <!-- 图表信息 -->
    <div class="chart-info" v-if="chartConfig.data">
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">图表类型:</span>
          <span class="info-value">{{ getChartTypeLabel() }}</span>
        </div>
        <div class="info-item" v-if="getDataPointsCount()">
          <span class="info-label">数据点:</span>
          <span class="info-value">{{ getDataPointsCount() }}</span>
        </div>
        <div class="info-item" v-if="meta?.metric_type">
          <span class="info-label">指标类型:</span>
          <span class="info-value">{{ meta.metric_type }}</span>
        </div>
        <div class="info-item" v-if="meta?.time_range">
          <span class="info-label">时间范围:</span>
          <span class="info-value">{{ meta.time_range }}</span>
        </div>
      </div>
    </div>

    <!-- 图表数据表格 -->
    <div v-if="showDataTable" class="data-table">
      <div class="table-header">
        <h4>图表数据</h4>
        <el-button @click="toggleDataTable" size="small">
          <el-icon><Close /></el-icon>
          关闭
        </el-button>
      </div>
      
      <el-table :data="tableData" border stripe max-height="300">
        <el-table-column 
          v-for="column in tableColumns" 
          :key="column.prop"
          :prop="column.prop"
          :label="column.label"
          show-overflow-tooltip
        />
      </el-table>
    </div>

    <!-- 元数据信息 -->
    <div v-if="meta && Object.keys(meta).length > 0" class="meta-info">
      <el-collapse>
        <el-collapse-item title="图表详细信息" name="meta">
          <div class="meta-content">
            <div v-for="(value, key) in meta" :key="key" class="meta-item">
              <span class="meta-key">{{ key }}:</span>
              <span class="meta-value">
                <span v-if="typeof value === 'object'">
                  <pre>{{ JSON.stringify(value, null, 2) }}</pre>
                </span>
                <span v-else>{{ value }}</span>
              </span>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>

    <!-- 全屏模式 -->
    <el-dialog 
      v-model="isFullscreen" 
      :show-close="false"
      fullscreen
      class="fullscreen-chart-dialog"
    >
      <div class="fullscreen-chart-container">
        <div class="fullscreen-toolbar">
          <div class="toolbar-left">
            <h3>图表查看器</h3>
          </div>
          <div class="toolbar-right">
            <el-button-group>
              <el-button @click="exportChart('png')">
                <el-icon><Picture /></el-icon>
                导出PNG
              </el-button>
              <el-button @click="toggleDataTable">
                <el-icon><Grid /></el-icon>
                数据表格
              </el-button>
              <el-button @click="toggleFullscreen">
                <el-icon><Close /></el-icon>
                关闭
              </el-button>
            </el-button-group>
          </div>
        </div>
        
        <div ref="fullscreenChartElement" class="fullscreen-chart"></div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Refresh,
  Picture, 
  Document, 
  FullScreen,
  Loading,
  Warning,
  Close,
  Grid
} from '@element-plus/icons-vue'

export default {
  name: 'ChartResultDisplay',
  components: {
    Refresh,
    Picture,
    Document,
    FullScreen,
    Loading,
    Warning,
    Close,
    Grid
  },
  props: {
    chartConfig: {
      type: Object,
      required: true
    },
    meta: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['export'],
  setup(props, { emit }) {
    const loading = ref(true)
    const error = ref('')
    const isFullscreen = ref(false)
    const showDataTable = ref(false)
    const chartElement = ref(null)
    const fullscreenChartElement = ref(null)
    const chartInstance = ref(null)
    const fullscreenChartInstance = ref(null)

    // 计算属性
    const chartStyle = computed(() => ({
      width: '100%',
      height: '400px'
    }))

    const tableData = computed(() => {
      if (!props.chartConfig.data?.datasets) return []
      
      const labels = props.chartConfig.data.labels || []
      const datasets = props.chartConfig.data.datasets || []
      
      return labels.map((label, index) => {
        const row = { label }
        datasets.forEach(dataset => {
          row[dataset.label || 'data'] = dataset.data[index]
        })
        return row
      })
    })

    const tableColumns = computed(() => {
      if (!props.chartConfig.data?.datasets) return []
      
      const columns = [{ prop: 'label', label: '标签' }]
      const datasets = props.chartConfig.data.datasets || []
      
      datasets.forEach(dataset => {
        columns.push({
          prop: dataset.label || 'data',
          label: dataset.label || '数据'
        })
      })
      
      return columns
    })

    // 方法
    const initChart = async () => {
      try {
        // 动态导入Chart.js
        const { Chart, registerables } = await import('chart.js')
        Chart.register(...registerables)

        if (chartElement.value) {
          chartInstance.value = new Chart(chartElement.value, {
            type: props.chartConfig.type || 'line',
            data: props.chartConfig.data || {},
            options: {
              ...props.chartConfig.options,
              responsive: true,
              maintainAspectRatio: false
            }
          })
        }

        loading.value = false
      } catch (err) {
        error.value = '图表库加载失败，请确保已安装Chart.js'
        loading.value = false
        console.error('Chart.js error:', err)
      }
    }

    const initFullscreenChart = async () => {
      if (!isFullscreen.value || !fullscreenChartElement.value) return

      try {
        const { Chart, registerables } = await import('chart.js')
        Chart.register(...registerables)

        if (fullscreenChartInstance.value) {
          fullscreenChartInstance.value.destroy()
        }

        fullscreenChartInstance.value = new Chart(fullscreenChartElement.value, {
          type: props.chartConfig.type || 'line',
          data: props.chartConfig.data || {},
          options: {
            ...props.chartConfig.options,
            responsive: true,
            maintainAspectRatio: false
          }
        })
      } catch (err) {
        console.error('Fullscreen chart error:', err)
      }
    }

    const retryRender = () => {
      loading.value = true
      error.value = ''
      nextTick(() => {
        initChart()
      })
    }

    const refreshChart = () => {
      if (chartInstance.value) {
        chartInstance.value.update()
      }
      ElMessage.success('图表已刷新')
    }

    const exportChart = (format) => {
      emit('export', format)
      
      try {
        const canvas = chartElement.value
        if (!canvas) {
          ElMessage.error('图表未准备就绪')
          return
        }

        if (format === 'png') {
          const url = canvas.toDataURL('image/png')
          const link = document.createElement('a')
          link.href = url
          link.download = `chart-${Date.now()}.png`
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
          ElMessage.success('PNG图片已下载')
        } else if (format === 'svg') {
          ElMessage.info('SVG导出功能开发中...')
        }
      } catch (error) {
        ElMessage.error('导出失败: ' + error.message)
      }
    }

    const toggleFullscreen = () => {
      isFullscreen.value = !isFullscreen.value
      if (isFullscreen.value) {
        nextTick(() => {
          initFullscreenChart()
        })
      } else if (fullscreenChartInstance.value) {
        fullscreenChartInstance.value.destroy()
        fullscreenChartInstance.value = null
      }
    }

    const toggleDataTable = () => {
      showDataTable.value = !showDataTable.value
    }

    const getChartTypeLabel = () => {
      const typeMap = {
        'line': '折线图',
        'bar': '柱状图',
        'pie': '饼图',
        'doughnut': '环形图',
        'radar': '雷达图',
        'area': '面积图',
        'scatter': '散点图'
      }
      return typeMap[props.chartConfig.type] || props.chartConfig.type || '未知'
    }

    const getDataPointsCount = () => {
      const data = props.chartConfig.data
      if (!data) return 0
      
      if (data.labels) {
        return data.labels.length
      } else if (data.datasets && data.datasets[0]) {
        return data.datasets[0].data.length
      }
      
      return 0
    }

    const formatDate = (dateString) => {
      try {
        return new Date(dateString).toLocaleString()
      } catch {
        return dateString
      }
    }

    // 监听配置变化
    watch(() => props.chartConfig, () => {
      if (chartInstance.value) {
        chartInstance.value.destroy()
      }
      nextTick(() => {
        initChart()
      })
    }, { deep: true })

    // 生命周期
    onMounted(() => {
      nextTick(() => {
        initChart()
      })
    })

    onUnmounted(() => {
      if (chartInstance.value) {
        chartInstance.value.destroy()
      }
      if (fullscreenChartInstance.value) {
        fullscreenChartInstance.value.destroy()
      }
    })

    return {
      loading,
      error,
      isFullscreen,
      showDataTable,
      chartElement,
      fullscreenChartElement,
      chartStyle,
      tableData,
      tableColumns,
      retryRender,
      refreshChart,
      exportChart,
      toggleFullscreen,
      toggleDataTable,
      getChartTypeLabel,
      getDataPointsCount,
      formatDate
    }
  }
}
</script>

<style scoped>
.chart-result-display {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.chart-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.toolbar-left {
  display: flex;
  gap: 8px;
  align-items: center;
}

.chart-container {
  position: relative;
  padding: 20px;
  background: white;
}

.chart-element {
  position: relative;
}

.loading-overlay,
.error-overlay {
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

.error-message {
  font-size: 12px;
  color: #dc3545;
  margin: 8px 0;
}

.chart-info {
  padding: 16px;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.info-label {
  font-weight: 600;
  color: #495057;
}

.info-value {
  color: #6c757d;
  font-family: 'Monaco', 'Menlo', monospace;
}

.data-table {
  border-top: 1px solid #e9ecef;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.table-header h4 {
  margin: 0;
  color: #2c3e50;
}

.meta-info {
  border-top: 1px solid #e9ecef;
}

.meta-content {
  padding: 16px;
  background: #f8f9fa;
}

.meta-item {
  display: flex;
  margin-bottom: 8px;
  align-items: flex-start;
}

.meta-key {
  font-weight: 600;
  min-width: 120px;
  color: #495057;
}

.meta-value {
  flex: 1;
  color: #6c757d;
}

.meta-value pre {
  background: white;
  padding: 8px;
  border-radius: 4px;
  font-size: 12px;
  margin: 0;
  border: 1px solid #dee2e6;
}

/* 全屏样式 */
.fullscreen-chart-dialog :deep(.el-dialog__body) {
  padding: 0;
  height: 100vh;
  background: #f8f9fa;
}

.fullscreen-chart-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.fullscreen-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #e9ecef;
}

.fullscreen-toolbar h3 {
  margin: 0;
  color: #2c3e50;
}

.fullscreen-chart {
  flex: 1;
  padding: 24px;
  position: relative;
}
</style>
