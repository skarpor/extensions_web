<template>
    <div class="text-result">
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
      <div v-else-if="!hasContent" class="empty-container">
        <el-empty description="没有数据" />
      </div>
      <div v-else class="content-container">
        <pre class="text-content">{{ formattedContent }}</pre>
        
        <div class="text-actions">
          <el-button size="small" type="primary" @click="copyContent">
            <el-icon><Document /></el-icon> 复制内容
          </el-button>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { defineComponent, ref, computed } from 'vue'
  import { Document } from '@element-plus/icons-vue'
  import { ElMessage } from 'element-plus'
  
  export default defineComponent({
    name: 'TextResult',
    components: {
      Document
    },
    props: {
      result: {
        type: [Object, Array, String],
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
      // 计算格式化后的内容
      const formattedContent = computed(() => {
        if (!props.result) return ''
        
        // 如果结果是字符串，直接使用
        if (typeof props.result === 'string') {
          return props.result
        }
        
        // 如果结果是数组或对象，格式化为JSON
        if (typeof props.result === 'object') {
          try {
            return JSON.stringify(props.result, null, 2)
          } catch (e) {
            return String(props.result)
          }
        }
        
        return String(props.result)
      })
      
      // 检查是否有内容
      const hasContent = computed(() => {
        return formattedContent.value && formattedContent.value.trim() !== ''
      })
      
      // 复制内容到剪贴板
      const copyContent = async () => {
        try {
          await navigator.clipboard.writeText(formattedContent.value)
          ElMessage.success('内容已复制到剪贴板')
        } catch (e) {
          ElMessage.error('复制失败: ' + e.message)
        }
      }
      
      return {
        formattedContent,
        hasContent,
        copyContent
      }
    }
  })
  </script>
  
  <style scoped>
  .text-result {
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
  
  .content-container {
    margin-top: 10px;
  }
  
  .text-content {
    background-color: #f5f7fa;
    border: 1px solid #e4e7ed;
    border-radius: 4px;
    padding: 15px;
    white-space: pre-wrap;
    word-break: break-word;
    font-family: 'Courier New', Courier, monospace;
    font-size: 14px;
    line-height: 1.5;
    max-height: 500px;
    overflow-y: auto;
  }
  
  .text-actions {
    margin-top: 15px;
    display: flex;
    justify-content: flex-end;
  }
  </style>