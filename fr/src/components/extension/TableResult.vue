<template>
    <div class="table-result">
      <div v-if="!result || loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>
      <div v-else-if="error" class="error-container">
        <el-alert
          title="加载数据失败"
          type="error"
          :description="error"
          show-icon
        />
      </div>
      <div v-else-if="!hasData" class="empty-container">
        <el-empty description="没有数据" />
      </div>
      <div v-else class="table-container">
        <el-table
          :data="tableData"
          border
          stripe
          style="width: 100%"
          :max-height="500"
        >
          <el-table-column
            v-for="(column, index) in columns"
            :key="index"
            :prop="column.prop"
            :label="column.label"
            :width="column.width"
            :sortable="column.sortable !== false"
          >
            <template #default="scope">
              <span v-if="column.formatter">
                {{ column.formatter(scope.row[column.prop], scope.row) }}
              </span>
              <span v-else>{{ scope.row[column.prop] }}</span>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="table-footer" v-if="showPagination">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            :total="total"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { defineComponent, ref, computed, watch } from 'vue'
  
  export default defineComponent({
    name: 'TableResult',
    props: {
      result: {
        type: [Object, Array],
        default: () => ({})
      },
      loading: {
        type: Boolean,
        default: false
      },
      error: {
        type: String,
        default: ''
      },
      extension: {
        type: Object,
        default: () => ({})
      }
    },
    setup(props) {
      const currentPage = ref(1)
      const pageSize = ref(10)
      
      // 计算表格数据
      const tableData = computed(() => {
        if (!props.result) return []
        
        // 如果结果是数组，直接使用
        if (Array.isArray(props.result)) {
          return props.result
        }
        
        // 如果结果是对象，尝试获取data属性
        if (props.result.data && Array.isArray(props.result.data)) {
          return props.result.data
        }
        
        // 如果结果是对象，尝试获取rows属性
        if (props.result.rows && Array.isArray(props.result.rows)) {
          return props.result.rows
        }
        
        // 如果结果是对象，尝试获取items属性
        if (props.result.items && Array.isArray(props.result.items)) {
          return props.result.items
        }
        
        // 如果结果是对象，尝试获取records属性
        if (props.result.records && Array.isArray(props.result.records)) {
          return props.result.records
        }
        
        // 如果结果是对象但没有标准数据属性，将其转换为数组
        if (typeof props.result === 'object' && !Array.isArray(props.result)) {
          return [props.result]
        }
        
        return []
      })
      
      // 检查是否有数据
      const hasData = computed(() => tableData.value && tableData.value.length > 0)
      
      // 计算总记录数
      const total = computed(() => {
        if (!props.result) return 0
        
        // 如果结果对象中有total属性，使用它
        if (props.result.total !== undefined) {
          return props.result.total
        }
        
        // 否则使用数组长度
        return tableData.value.length
      })
      
      // 计算是否显示分页
      const showPagination = computed(() => {
        return total.value > 10
      })
      
      // 计算表格列
      const columns = computed(() => {
        if (!hasData.value) return []
        
        // 从第一行数据中提取列
        const firstRow = tableData.value[0]
        return Object.keys(firstRow).map(key => ({
          prop: key,
          label: key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' '),
          sortable: true
        }))
      })
      
      // 处理页大小变化
      const handleSizeChange = (size) => {
        pageSize.value = size
      }
      
      // 处理页码变化
      const handleCurrentChange = (page) => {
        currentPage.value = page
      }
      
      // 当结果变化时重置分页
      watch(() => props.result, () => {
        currentPage.value = 1
      })
      
      return {
        currentPage,
        pageSize,
        tableData,
        hasData,
        total,
        showPagination,
        columns,
        handleSizeChange,
        handleCurrentChange
      }
    }
  })
  </script>
  
  <style scoped>
  .table-result {
    width: 100%;
  }
  
  .loading-container,
  .error-container,
  .empty-container {
    padding: 20px;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  
  .table-container {
    margin-top: 10px;
  }
  
  .table-footer {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
  </style>