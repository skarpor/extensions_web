<template>
  <div class="file-result-display">
    <!-- 文件信息卡片 -->
    <div class="file-info-card">
      <div class="file-icon">
        <el-icon size="48">
          <component :is="getFileIcon()" />
        </el-icon>
      </div>
      
      <div class="file-details">
        <h3 class="file-name">{{ fileInfo.filename || '下载文件' }}</h3>
        <div class="file-meta">
          <span class="file-size">{{ formatFileSize(fileInfo.size) }}</span>
          <span class="file-type">{{ getFileType() }}</span>
          <span v-if="fileInfo.created_at" class="file-date">
            {{ formatDate(fileInfo.created_at) }}
          </span>
        </div>
        <p v-if="fileInfo.description" class="file-description">
          {{ fileInfo.description }}
        </p>
      </div>
      
      <div class="file-actions">
        <el-button type="primary" @click="downloadFile" :loading="downloading">
          <el-icon><Download /></el-icon>
          下载文件
        </el-button>
        <el-button v-if="canPreview" @click="previewFile">
          <el-icon><View /></el-icon>
          预览
        </el-button>
      </div>
    </div>

    <!-- 文件预览 -->
    <div v-if="showPreview" class="file-preview">
      <div class="preview-header">
        <h4>文件预览</h4>
        <el-button @click="closePreview" size="small">
          <el-icon><Close /></el-icon>
          关闭预览
        </el-button>
      </div>
      
      <div class="preview-content">
        <!-- 文本文件预览 -->
        <div v-if="previewType === 'text'" class="text-preview">
          <pre>{{ previewContent }}</pre>
        </div>
        
        <!-- 图片文件预览 -->
        <div v-else-if="previewType === 'image'" class="image-preview">
          <img :src="previewContent" :alt="fileInfo.filename" />
        </div>
        
        <!-- JSON文件预览 -->
        <div v-else-if="previewType === 'json'" class="json-preview">
          <pre>{{ formatJson(previewContent) }}</pre>
        </div>
        
        <!-- CSV文件预览 -->
        <div v-else-if="previewType === 'csv'" class="csv-preview">
          <el-table :data="csvData" border stripe max-height="400">
            <el-table-column 
              v-for="(column, index) in csvColumns" 
              :key="index"
              :prop="column"
              :label="column"
              show-overflow-tooltip
            />
          </el-table>
        </div>
        
        <!-- 不支持预览 -->
        <div v-else class="no-preview">
          <el-empty description="此文件类型不支持预览">
            <el-button @click="downloadFile">直接下载</el-button>
          </el-empty>
        </div>
      </div>
    </div>

    <!-- 下载进度 -->
    <div v-if="downloading" class="download-progress">
      <el-progress 
        :percentage="downloadProgress" 
        :status="downloadProgress === 100 ? 'success' : null"
      />
      <p class="progress-text">{{ downloadText }}</p>
    </div>

    <!-- 元数据信息 -->
    <div v-if="meta && Object.keys(meta).length > 0" class="meta-info">
      <el-collapse>
        <el-collapse-item title="文件详细信息" name="meta">
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
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Download, 
  View, 
  Close,
  Document,
  Files,
  Picture,
  VideoPlay,
  Headset,
  Box
} from '@element-plus/icons-vue'

export default {
  name: 'FileResultDisplay',
  components: {
    Download,
    View,
    Close,
    Document,
    Files,
    Picture,
    VideoPlay,
    Headset,
    Box
  },
  props: {
    fileInfo: {
      type: Object,
      required: true
    },
    meta: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['download'],
  setup(props, { emit }) {
    const downloading = ref(false)
    const downloadProgress = ref(0)
    const downloadText = ref('')
    const showPreview = ref(false)
    const previewContent = ref('')
    const previewType = ref('')
    const csvData = ref([])
    const csvColumns = ref([])

    // 计算属性
    const canPreview = computed(() => {
      const filename = props.fileInfo.filename || ''
      const ext = filename.split('.').pop()?.toLowerCase()
      return ['txt', 'json', 'csv', 'md', 'log', 'xml', 'html', 'js', 'css', 'py', 'java'].includes(ext)
    })

    // 方法
    const getFileIcon = () => {
      const filename = props.fileInfo.filename || ''
      const ext = filename.split('.').pop()?.toLowerCase()
      
      const iconMap = {
        // 文档
        'txt': Document,
        'md': Document,
        'doc': Document,
        'docx': Document,
        'pdf': Document,
        
        // 表格
        'csv': Files,
        'xls': Files,
        'xlsx': Files,
        
        // 图片
        'jpg': Picture,
        'jpeg': Picture,
        'png': Picture,
        'gif': Picture,
        'svg': Picture,
        
        // 视频
        'mp4': VideoPlay,
        'avi': VideoPlay,
        'mov': VideoPlay,
        
        // 音频
        'mp3': Headset,
        'wav': Headset,
        'flac': Headset,
        
        // 压缩包
        'zip': Box,
        'rar': Box,
        '7z': Box
      }
      
      return iconMap[ext] || Files
    }

    const getFileType = () => {
      const filename = props.fileInfo.filename || ''
      const ext = filename.split('.').pop()?.toLowerCase()
      
      const typeMap = {
        'txt': '文本文件',
        'csv': 'CSV表格',
        'json': 'JSON数据',
        'md': 'Markdown文档',
        'pdf': 'PDF文档',
        'jpg': 'JPEG图片',
        'png': 'PNG图片',
        'zip': '压缩文件',
        'log': '日志文件'
      }
      
      return typeMap[ext] || (ext ? ext.toUpperCase() + '文件' : '未知类型')
    }

    const formatFileSize = (bytes) => {
      if (!bytes || bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    const formatDate = (dateString) => {
      try {
        return new Date(dateString).toLocaleString()
      } catch {
        return dateString
      }
    }

    const downloadFile = async () => {
      emit('download')
      
      try {
        downloading.value = true
        downloadProgress.value = 0
        downloadText.value = '准备下载...'

        // 模拟下载进度
        const progressInterval = setInterval(() => {
          if (downloadProgress.value < 90) {
            downloadProgress.value += 10
            updateDownloadText()
          }
        }, 100)

        // 实际下载逻辑
        if (props.fileInfo.file_path) {
          // 服务器文件路径
          const response = await fetch(`/api/files/download?path=${encodeURIComponent(props.fileInfo.file_path)}`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          })
          
          if (!response.ok) {
            throw new Error('下载失败')
          }
          
          const blob = await response.blob()
          downloadBlob(blob, props.fileInfo.filename)
        } else if (props.fileInfo.content) {
          // 直接内容
          const blob = new Blob([props.fileInfo.content], { 
            type: props.fileInfo.content_type || 'application/octet-stream' 
          })
          downloadBlob(blob, props.fileInfo.filename)
        }

        clearInterval(progressInterval)
        downloadProgress.value = 100
        downloadText.value = '下载完成'
        
        setTimeout(() => {
          downloading.value = false
        }, 1000)
        
        ElMessage.success('文件下载成功')
        
      } catch (error) {
        downloading.value = false
        ElMessage.error('下载失败: ' + error.message)
      }
    }

    const downloadBlob = (blob, filename) => {
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename || 'download'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    }

    const updateDownloadText = () => {
      const texts = [
        '连接服务器...',
        '获取文件信息...',
        '开始下载...',
        '下载中...',
        '处理文件...',
        '即将完成...'
      ]
      const index = Math.floor(downloadProgress.value / 15)
      downloadText.value = texts[index] || '下载中...'
    }

    const previewFile = async () => {
      try {
        const filename = props.fileInfo.filename || ''
        const ext = filename.split('.').pop()?.toLowerCase()
        
        // 获取文件内容
        let content = ''
        if (props.fileInfo.file_path) {
          const response = await fetch(`/api/files/preview?path=${encodeURIComponent(props.fileInfo.file_path)}`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          })
          content = await response.text()
        } else if (props.fileInfo.content) {
          content = props.fileInfo.content
        }

        // 设置预览类型和内容
        if (['txt', 'md', 'log', 'py', 'js', 'css', 'html', 'xml'].includes(ext)) {
          previewType.value = 'text'
          previewContent.value = content
        } else if (ext === 'json') {
          previewType.value = 'json'
          previewContent.value = content
        } else if (ext === 'csv') {
          previewType.value = 'csv'
          parseCsvContent(content)
        }
        
        showPreview.value = true
        
      } catch (error) {
        ElMessage.error('预览失败: ' + error.message)
      }
    }

    const closePreview = () => {
      showPreview.value = false
      previewContent.value = ''
      previewType.value = ''
      csvData.value = []
      csvColumns.value = []
    }

    const formatJson = (jsonString) => {
      try {
        const obj = JSON.parse(jsonString)
        return JSON.stringify(obj, null, 2)
      } catch {
        return jsonString
      }
    }

    const parseCsvContent = (csvContent) => {
      try {
        const lines = csvContent.split('\n').filter(line => line.trim())
        if (lines.length === 0) return

        // 解析表头
        const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''))
        csvColumns.value = headers

        // 解析数据行
        const data = lines.slice(1, 101).map((line, index) => { // 限制显示100行
          const values = line.split(',').map(v => v.trim().replace(/"/g, ''))
          const row = {}
          headers.forEach((header, i) => {
            row[header] = values[i] || ''
          })
          return row
        })

        csvData.value = data
      } catch (error) {
        ElMessage.error('CSV解析失败')
      }
    }

    return {
      downloading,
      downloadProgress,
      downloadText,
      showPreview,
      previewContent,
      previewType,
      csvData,
      csvColumns,
      canPreview,
      getFileIcon,
      getFileType,
      formatFileSize,
      formatDate,
      downloadFile,
      previewFile,
      closePreview,
      formatJson
    }
  }
}
</script>

<style scoped>
.file-result-display {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.file-info-card {
  display: flex;
  align-items: center;
  padding: 24px;
  gap: 20px;
  border-bottom: 1px solid #e9ecef;
}

.file-icon {
  color: #409eff;
  background: #e6f7ff;
  padding: 16px;
  border-radius: 12px;
}

.file-details {
  flex: 1;
}

.file-name {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.file-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
}

.file-meta span {
  font-size: 14px;
  color: #6c757d;
  padding: 4px 8px;
  background: #f8f9fa;
  border-radius: 4px;
}

.file-description {
  margin: 0;
  color: #6c757d;
  font-size: 14px;
}

.file-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.download-progress {
  padding: 20px;
  text-align: center;
  background: #f8f9fa;
}

.progress-text {
  margin-top: 8px;
  color: #6c757d;
  font-size: 14px;
}

.file-preview {
  border-top: 1px solid #e9ecef;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.preview-header h4 {
  margin: 0;
  color: #2c3e50;
}

.preview-content {
  max-height: 400px;
  overflow: auto;
  padding: 20px;
}

.text-preview pre,
.json-preview pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 14px;
  line-height: 1.6;
  background: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
  border: 1px solid #e9ecef;
  overflow-x: auto;
}

.image-preview {
  text-align: center;
}

.image-preview img {
  max-width: 100%;
  max-height: 300px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.csv-preview {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 16px;
}

.no-preview {
  text-align: center;
  padding: 40px;
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

@media (max-width: 768px) {
  .file-info-card {
    flex-direction: column;
    text-align: center;
  }
  
  .file-actions {
    flex-direction: row;
    justify-content: center;
  }
}
</style>
