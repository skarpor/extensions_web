<template>
  <div class="image-result-display">
    <!-- 图片工具栏 -->
    <div class="image-toolbar">
      <div class="toolbar-left">
        <el-tag type="info" size="small">
          图片结果
        </el-tag>
        <el-tag v-if="imageInfo.size" type="success" size="small">
          {{ formatFileSize(imageInfo.size) }}
        </el-tag>
      </div>
      
      <div class="toolbar-right">
        <el-button-group size="small">
          <el-button @click="zoomOut" :disabled="scale <= 0.2">
            <el-icon><ZoomOut /></el-icon>
          </el-button>
          <el-button @click="resetZoom">
            {{ Math.round(scale * 100) }}%
          </el-button>
          <el-button @click="zoomIn" :disabled="scale >= 3">
            <el-icon><ZoomIn /></el-icon>
          </el-button>
          <el-button @click="downloadImage">
            <el-icon><Download /></el-icon>
            下载
          </el-button>
          <el-button @click="copyImage" v-if="canCopy">
            <el-icon><CopyDocument /></el-icon>
            复制
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 图片显示区域 -->
    <div class="image-container" ref="imageContainer">
      <div class="image-wrapper" :style="imageWrapperStyle">
        <img 
          :src="src" 
          :alt="imageInfo.alt || '扩展生成的图片'"
          :style="imageStyle"
          @load="onImageLoad"
          @error="onImageError"
          @click="toggleFullscreen"
          class="result-image"
        />
        
        <!-- 加载状态 -->
        <div v-if="loading" class="loading-overlay">
          <el-icon class="loading-icon"><Loading /></el-icon>
          <p>图片加载中...</p>
        </div>
        
        <!-- 错误状态 -->
        <div v-if="error" class="error-overlay">
          <el-icon class="error-icon"><Warning /></el-icon>
          <p>图片加载失败</p>
          <el-button @click="retryLoad" size="small">重试</el-button>
        </div>
      </div>
    </div>

    <!-- 图片信息 -->
    <div class="image-info" v-if="imageInfo.width && imageInfo.height">
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">尺寸:</span>
          <span class="info-value">{{ imageInfo.width }} × {{ imageInfo.height }}</span>
        </div>
        <div class="info-item" v-if="imageInfo.format">
          <span class="info-label">格式:</span>
          <span class="info-value">{{ imageInfo.format.toUpperCase() }}</span>
        </div>
        <div class="info-item" v-if="meta?.生成时间">
          <span class="info-label">生成时间:</span>
          <span class="info-value">{{ meta.生成时间 }}</span>
        </div>
        <div class="info-item" v-if="meta?.图表类型">
          <span class="info-label">类型:</span>
          <span class="info-value">{{ meta.图表类型 }}</span>
        </div>
      </div>
    </div>

    <!-- 全屏预览 -->
    <el-dialog 
      v-model="fullscreenVisible" 
      :show-close="false"
      :close-on-click-modal="true"
      fullscreen
      class="fullscreen-dialog"
    >
      <div class="fullscreen-container" @click="toggleFullscreen">
        <img 
          :src="src" 
          :alt="imageInfo.alt || '扩展生成的图片'"
          class="fullscreen-image"
        />
        
        <div class="fullscreen-controls">
          <el-button-group>
            <el-button @click.stop="zoomOut" :disabled="fullscreenScale <= 0.2">
              <el-icon><ZoomOut /></el-icon>
            </el-button>
            <el-button @click.stop="resetFullscreenZoom">
              {{ Math.round(fullscreenScale * 100) }}%
            </el-button>
            <el-button @click.stop="zoomIn" :disabled="fullscreenScale >= 5">
              <el-icon><ZoomIn /></el-icon>
            </el-button>
            <el-button @click.stop="downloadImage">
              <el-icon><Download /></el-icon>
            </el-button>
            <el-button @click.stop="toggleFullscreen">
              <el-icon><Close /></el-icon>
            </el-button>
          </el-button-group>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  ZoomOut, 
  ZoomIn, 
  Download, 
  CopyDocument, 
  Loading, 
  Warning,
  Close
} from '@element-plus/icons-vue'

export default {
  name: 'ImageResultDisplay',
  components: {
    ZoomOut,
    ZoomIn,
    Download,
    CopyDocument,
    Loading,
    Warning,
    Close
  },
  props: {
    src: {
      type: String,
      required: true
    },
    meta: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['download'],
  setup(props, { emit }) {
    const loading = ref(true)
    const error = ref(false)
    const scale = ref(1)
    const fullscreenScale = ref(1)
    const fullscreenVisible = ref(false)
    const imageContainer = ref(null)
    
    const imageInfo = ref({
      width: 0,
      height: 0,
      size: 0,
      format: '',
      alt: ''
    })

    // 计算属性
    const canCopy = computed(() => {
      return navigator.clipboard && props.src.startsWith('data:')
    })

    const imageStyle = computed(() => ({
      transform: `scale(${scale.value})`,
      transformOrigin: 'center center',
      transition: 'transform 0.3s ease',
      cursor: 'pointer'
    }))

    const imageWrapperStyle = computed(() => ({
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '300px',
      position: 'relative'
    }))

    // 方法
    const onImageLoad = (event) => {
      loading.value = false
      error.value = false
      
      const img = event.target
      imageInfo.value.width = img.naturalWidth
      imageInfo.value.height = img.naturalHeight
      
      // 从src中提取格式信息
      if (props.src.startsWith('data:image/')) {
        const format = props.src.split(';')[0].split('/')[1]
        imageInfo.value.format = format
      }
      
      // 估算文件大小（base64）
      if (props.src.startsWith('data:')) {
        const base64Data = props.src.split(',')[1]
        imageInfo.value.size = Math.round((base64Data.length * 3) / 4)
      }
    }

    const onImageError = () => {
      loading.value = false
      error.value = true
      ElMessage.error('图片加载失败')
    }

    const retryLoad = () => {
      loading.value = true
      error.value = false
      // 触发重新加载
      const img = document.querySelector('.result-image')
      if (img) {
        img.src = props.src
      }
    }

    const zoomIn = () => {
      if (fullscreenVisible.value) {
        fullscreenScale.value = Math.min(fullscreenScale.value * 1.2, 5)
      } else {
        scale.value = Math.min(scale.value * 1.2, 3)
      }
    }

    const zoomOut = () => {
      if (fullscreenVisible.value) {
        fullscreenScale.value = Math.max(fullscreenScale.value / 1.2, 0.2)
      } else {
        scale.value = Math.max(scale.value / 1.2, 0.2)
      }
    }

    const resetZoom = () => {
      scale.value = 1
    }

    const resetFullscreenZoom = () => {
      fullscreenScale.value = 1
    }

    const toggleFullscreen = () => {
      fullscreenVisible.value = !fullscreenVisible.value
      if (fullscreenVisible.value) {
        fullscreenScale.value = 1
      }
    }

    const downloadImage = () => {
      emit('download')
      
      try {
        if (props.src.startsWith('data:')) {
          // Base64图片直接下载
          const link = document.createElement('a')
          link.href = props.src
          link.download = `image-${Date.now()}.${imageInfo.value.format || 'png'}`
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
          ElMessage.success('图片下载成功')
        } else {
          // URL图片
          fetch(props.src)
            .then(response => response.blob())
            .then(blob => {
              const url = URL.createObjectURL(blob)
              const link = document.createElement('a')
              link.href = url
              link.download = `image-${Date.now()}.png`
              document.body.appendChild(link)
              link.click()
              document.body.removeChild(link)
              URL.revokeObjectURL(url)
              ElMessage.success('图片下载成功')
            })
            .catch(() => {
              ElMessage.error('图片下载失败')
            })
        }
      } catch (error) {
        ElMessage.error('下载失败: ' + error.message)
      }
    }

    const copyImage = async () => {
      if (!canCopy.value) {
        ElMessage.warning('当前环境不支持复制功能')
        return
      }

      try {
        if (props.src.startsWith('data:image/')) {
          // 将base64转换为blob
          const response = await fetch(props.src)
          const blob = await response.blob()
          
          await navigator.clipboard.write([
            new ClipboardItem({ [blob.type]: blob })
          ])
          
          ElMessage.success('图片已复制到剪贴板')
        } else {
          ElMessage.warning('只支持复制base64格式的图片')
        }
      } catch (error) {
        ElMessage.error('复制失败: ' + error.message)
      }
    }

    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    // 键盘事件处理
    const handleKeydown = (event) => {
      if (fullscreenVisible.value) {
        switch (event.key) {
          case 'Escape':
            toggleFullscreen()
            break
          case '+':
          case '=':
            zoomIn()
            break
          case '-':
            zoomOut()
            break
          case '0':
            resetFullscreenZoom()
            break
        }
      }
    }

    onMounted(() => {
      document.addEventListener('keydown', handleKeydown)
    })

    return {
      loading,
      error,
      scale,
      fullscreenScale,
      fullscreenVisible,
      imageContainer,
      imageInfo,
      canCopy,
      imageStyle,
      imageWrapperStyle,
      onImageLoad,
      onImageError,
      retryLoad,
      zoomIn,
      zoomOut,
      resetZoom,
      resetFullscreenZoom,
      toggleFullscreen,
      downloadImage,
      copyImage,
      formatFileSize
    }
  }
}
</script>

<style scoped>
.image-result-display {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.image-toolbar {
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

.image-container {
  min-height: 300px;
  max-height: 600px;
  overflow: auto;
  background: #f8f9fa;
  position: relative;
}

.image-wrapper {
  padding: 20px;
}

.result-image {
  max-width: 100%;
  max-height: 100%;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.loading-overlay,
.error-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #6c757d;
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

.image-info {
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
}

.info-label {
  font-weight: 600;
  color: #495057;
}

.info-value {
  color: #6c757d;
  font-family: 'Monaco', 'Menlo', monospace;
}

/* 全屏样式 */
.fullscreen-dialog :deep(.el-dialog__body) {
  padding: 0;
  height: 100vh;
  background: rgba(0, 0, 0, 0.9);
}

.fullscreen-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
}

.fullscreen-image {
  max-width: 90vw;
  max-height: 90vh;
  object-fit: contain;
}

.fullscreen-controls {
  position: absolute;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
}

.fullscreen-controls .el-button {
  background: rgba(0, 0, 0, 0.7);
  border-color: rgba(255, 255, 255, 0.3);
  color: white;
}

.fullscreen-controls .el-button:hover {
  background: rgba(0, 0, 0, 0.8);
}
</style>
