<template>
    <div class="image-result">
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
      <div v-else-if="!hasImage" class="empty-container">
        <el-empty description="没有图像数据" />
      </div>
      <div v-else class="image-container">
        <div class="image-wrapper">
          <img :src="imageUrl" :alt="imageAlt" class="result-image" />
        </div>
        
        <div class="image-actions">
          <el-button size="small" type="primary" @click="downloadImage">
            <el-icon><Download /></el-icon> 下载图像
          </el-button>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { defineComponent, ref, computed } from 'vue'
  import { Download } from '@element-plus/icons-vue'
  import { ElMessage } from 'element-plus'
  
  export default defineComponent({
    name: 'ImageResult',
    components: {
      Download
    },
    props: {
      result: {
        type: [Object, String],
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
      // 计算图像URL
      const imageUrl = computed(() => {
        if (!props.result) return ''
        
        // 如果结果是字符串，可能是URL或Base64
        if (typeof props.result === 'string') {
          // 检查是否是Base64
          if (props.result.startsWith('data:image/')) {
            return props.result
          }
          
          // 检查是否是URL
          try {
            new URL(props.result)
            return props.result
          } catch (e) {
            // 不是有效URL，尝试作为相对路径处理
            return props.result
          }
        }
        
        // 如果结果是对象，尝试获取url或src属性
        if (typeof props.result === 'object') {
          if (props.result.url) return props.result.url
          if (props.result.src) return props.result.src
          if (props.result.image) return props.result.image
          if (props.result.data && typeof props.result.data === 'string') {
            return props.result.data
          }
        }
        
        return ''
      })
      
      // 计算图像alt文本
      const imageAlt = computed(() => {
        if (!props.result) return '结果图像'
        
        if (typeof props.result === 'object') {
          if (props.result.alt) return props.result.alt
          if (props.result.title) return props.result.title
          if (props.result.description) return props.result.description
        }
        
        return '结果图像'
      })
      
      // 检查是否有图像
      const hasImage = computed(() => {
        return imageUrl.value && imageUrl.value.trim() !== ''
      })
      
      // 下载图像
      const downloadImage = () => {
        try {
          const link = document.createElement('a')
          link.href = imageUrl.value
          link.download = `image_${new Date().getTime()}.png`
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
        } catch (e) {
          ElMessage.error('下载图像失败: ' + e.message)
        }
      }
      
      return {
        imageUrl,
        imageAlt,
        hasImage,
        downloadImage
      }
    }
  })
  </script>
  
  <style scoped>
  .image-result {
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
  
  .image-container {
    margin-top: 10px;
  }
  
  .image-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 10px;
    background-color: #f5f7fa;
    border: 1px solid #e4e7ed;
    border-radius: 4px;
  }
  
  .result-image {
    max-width: 100%;
    max-height: 500px;
    object-fit: contain;
  }
  
  .image-actions {
    margin-top: 15px;
    display: flex;
    justify-content: center;
  }
  </style>