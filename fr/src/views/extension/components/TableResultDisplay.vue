<template>
  <div class="table-result-display">
    <!-- 表格工具栏 -->
    <div class="table-toolbar">
      <div class="toolbar-left">
        <el-tag type="info" size="small">
          {{ data?.length || 0 }} 条记录
        </el-tag>
        <el-tag v-if="meta?.查询时间" type="success" size="small">
          {{ meta.查询时间 }}
        </el-tag>
      </div>
      
      <div class="toolbar-right">
        <el-button-group size="small">
          <el-button @click="exportData('csv')">
            <el-icon><Document /></el-icon>
            CSV
          </el-button>
          <el-button @click="exportData('excel')">
            <el-icon><Files /></el-icon>
            Excel
          </el-button>
          <el-button @click="exportData('json')">
            <el-icon><DataLine /></el-icon>
            JSON
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-container">
      <el-table 
        :data="paginatedData" 
        stripe 
        border
        :height="tableHeight"
        @sort-change="handleSortChange"
        v-loading="loading"
      >
        <el-table-column 
          v-for="column in columns" 
          :key="column.prop"
          :prop="column.prop"
          :label="column.label"
          :sortable="column.sortable"
          :width="column.width"
          :min-width="column.minWidth"
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
    </div>

    <!-- 分页器 -->
    <div class="pagination-container" v-if="data?.length > pageSize">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="data?.length || 0"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 元数据信息 -->
    <div v-if="meta" class="meta-info">
      <el-collapse>
        <el-collapse-item title="详细信息" name="meta">
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
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Files, DataLine } from '@element-plus/icons-vue'

export default {
  name: 'TableResultDisplay',
  components: {
    Document,
    Files,
    DataLine
  },
  props: {
    data: {
      type: Array,
      default: () => []
    },
    meta: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['export'],
  setup(props, { emit }) {
    const loading = ref(false)
    const currentPage = ref(1)
    const pageSize = ref(20)
    const sortConfig = ref({ prop: '', order: '' })
    const tableHeight = ref(400)

    // 计算表格列
    const columns = computed(() => {
      if (!props.data || props.data.length === 0) return []
      
      const firstRow = props.data[0]
      return Object.keys(firstRow).map(key => {
        const column = {
          prop: key,
          label: key,
          sortable: true,
          minWidth: 120
        }
        
        // 根据数据类型设置列属性
        const value = firstRow[key]
        if (typeof value === 'number') {
          column.type = 'number'
          column.width = 100
        } else if (key.includes('状态') || key.includes('status')) {
          column.type = 'status'
          column.width = 100
        } else if (typeof value === 'string' && value.length > 50) {
          column.minWidth = 200
        }
        
        return column
      })
    })

    // 排序后的数据
    const sortedData = computed(() => {
      if (!props.data || !sortConfig.value.prop) return props.data
      
      const { prop, order } = sortConfig.value
      return [...props.data].sort((a, b) => {
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

    // 分页数据
    const paginatedData = computed(() => {
      const start = (currentPage.value - 1) * pageSize.value
      const end = start + pageSize.value
      return sortedData.value.slice(start, end)
    })

    // 方法
    const handleSortChange = ({ prop, order }) => {
      sortConfig.value = { prop, order }
    }

    const handleSizeChange = (size) => {
      pageSize.value = size
      currentPage.value = 1
    }

    const handleCurrentChange = (page) => {
      currentPage.value = page
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

    const exportData = (format) => {
      emit('export', format)
      
      try {
        if (format === 'csv') {
          exportToCsv()
        } else if (format === 'json') {
          exportToJson()
        } else if (format === 'excel') {
          ElMessage.info('Excel导出功能开发中...')
        }
      } catch (error) {
        ElMessage.error('导出失败: ' + error.message)
      }
    }

    const exportToCsv = () => {
      if (!props.data || props.data.length === 0) {
        ElMessage.warning('没有数据可导出')
        return
      }

      const headers = columns.value.map(col => col.label).join(',')
      const rows = props.data.map(row => 
        columns.value.map(col => {
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

    const exportToJson = () => {
      if (!props.data || props.data.length === 0) {
        ElMessage.warning('没有数据可导出')
        return
      }

      const jsonContent = JSON.stringify({
        data: props.data,
        meta: props.meta,
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

    // 监听数据变化，重置分页
    watch(() => props.data, () => {
      currentPage.value = 1
    })

    return {
      loading,
      currentPage,
      pageSize,
      tableHeight,
      columns,
      paginatedData,
      handleSortChange,
      handleSizeChange,
      handleCurrentChange,
      formatNumber,
      getStatusType,
      exportData
    }
  }
}
</script>

<style scoped>
.table-result-display {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.table-toolbar {
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

.table-container {
  overflow: auto;
}

.number-cell {
  font-family: 'Monaco', 'Menlo', monospace;
  font-weight: 600;
}

.pagination-container {
  padding: 16px;
  display: flex;
  justify-content: center;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
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
</style>
