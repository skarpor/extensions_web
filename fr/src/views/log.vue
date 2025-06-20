<template>
  <div class="log-viewer">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="title">
        <i class="icon icon-logs"></i>
        <h1>实时日志查看系统</h1>
      </div>
      
      <div class="controls">
        <div class="file-selector">
          <select 
            v-model="selectedFile" 
            @change="handleFileChange"
            :disabled="loading"
          >
            <option value="">-- 选择日志文件 --</option>
            <option 
              v-for="file in logFiles" 
              :key="file.name" 
              :value="file.name"
            >
              {{ file.name }} ({{ file.size }})
            </option>
          </select>
        </div>
        
        <div class="line-control">
          <input
            type="number"
            min="10"
            max="10000"
            v-model.number="lineCount"
            @change="loadInitialLogs"
          >
          <span>行</span>
        </div>
        
        <button 
          class="btn btn-scroll" 
          :class="{ active: autoScroll }"
          @click="toggleAutoScroll"
        >
          <i class="icon" :class="autoScroll ? 'icon-autoscroll-on' : 'icon-autoscroll-off'"></i>
          {{ autoScroll ? '自动滚动' : '手动滚动' }}
        </button>
        
        <button class="btn btn-clear" @click="clearLogs">
          <i class="icon icon-clear"></i>
          清空
        </button>
        
        <button 
          class="btn btn-copy" 
          @click="copyLogs"
          :disabled="!logs.length"
        >
          <i class="icon icon-copy"></i>
          复制
        </button>
        
        <button 
          class="btn btn-download" 
          @click="downloadLogs"
          :disabled="!logs.length"
        >
          <i class="icon icon-download"></i>
          下载
        </button>
      </div>
    </div>

    <!-- 文件信息栏 -->
    <div class="file-info" v-if="selectedFile">
      <div class="file-meta">
        <span class="label">当前文件:</span>
        <span class="value">{{ selectedFile }}</span>
        
        <span class="divider">|</span>
        
        <span class="label">大小:</span>
        <span class="value">{{ currentFileSize }}</span>
        
        <span class="divider">|</span>
        
        <span class="label">修改时间:</span>
        <span class="value">{{ currentFileModified }}</span>
      </div>
      
      <div class="stats">
        <span class="lines">{{ logs.length.toLocaleString() }} 行</span>
        <span class="memory">{{ memoryUsage }}</span>
      </div>
    </div>

    <!-- 日志显示区域 -->
    <div 
      class="log-container" 
      ref="logContainer"
      @scroll="handleScroll"
    >
      <div v-if="loading && !logs.length" class="loading-indicator">
        <div class="spinner"></div>
        <span>正在加载日志...</span>
      </div>
      
      <div v-else-if="error" class="error-message">
        <i class="icon icon-error"></i>
        <span>{{ error }}</span>
      </div>
      
      <template v-else>
        <div 
          v-for="(log, index) in logs" 
          :key="`log-${index}-${log.hash || index}`"
          class="log-line"
          :class="log.level"
        >
          <span class="line-number">{{ index + 1 }}</span>
          <span class="timestamp">{{ log.timestamp || '[无时间戳]' }}</span>
          <span class="content">{{ log.content }}</span>
        </div>
        
        <div v-if="!logs.length" class="empty-logs">
          <i class="icon icon-empty"></i>
          <span>没有可显示的日志内容</span>
        </div>
      </template>
    </div>

    <!-- 状态栏 -->
    <div class="status-bar">
      <div class="connection-status" :class="connectionStatus">
        <i class="icon" :class="connectionIcon"></i>
        <span>{{ connectionText }}</span>
      </div>
      
      <div class="update-time">
        <i class="icon icon-clock"></i>
        <span>最后更新: {{ lastUpdateTime || '--' }}</span>
      </div>
      
      <div v-if="loadingMore" class="loading-more">
        <i class="icon icon-loading"></i>
        <span>加载更多日志...</span>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import logApi from '@/api/log'

export default {
  name: 'LogViewer',
  setup() {
    // 状态管理
    const logFiles = ref([])
    const selectedFile = ref('')
    const logs = ref([])
    const lineCount = ref(500)
    const autoScroll = ref(true)
    const isScrolledUp = ref(false)
    const loading = ref(false)
    const loadingMore = ref(false)
    const error = ref(null)
    const lastUpdateTime = ref('')
    const connectionStatus = ref('disconnected')
    const logContainer = ref(null)
    let disconnectStream = null

    // 计算属性
    const currentFileInfo = computed(() => 
      logFiles.value.find(f => f.name === selectedFile.value) || {}
    )

    const currentFileSize = computed(() => 
      currentFileInfo.value.size || '--'
    )

    const currentFileModified = computed(() => 
      currentFileInfo.value.last_modified 
        ? logApi.formatDateTime(currentFileInfo.value.last_modified)
        : '--'
    )

    const memoryUsage = computed(() => {
      const size = new Blob([logs.value.map(l => l.raw).join('\n')]).size
      return logApi.formatFileSize(size)
    })

    const connectionText = computed(() => {
      switch (connectionStatus.value) {
        case 'connecting': return '连接中...'
        case 'connected': return '已连接'
        case 'error': return '连接错误'
        default: return '未连接'
      }
    })

    const connectionIcon = computed(() => {
      switch (connectionStatus.value) {
        case 'connecting': return 'icon-connecting'
        case 'connected': return 'icon-connected'
        case 'error': return 'icon-error'
        default: return 'icon-disconnected'
      }
    })

    // 方法
    const loadLogFiles = async () => {
      try {
        loading.value = true
        logFiles.value = await logApi.getLogFiles()
      } catch (err) {
        error.value = `获取日志文件列表失败: ${err.message}`
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const loadInitialLogs = async () => {
      if (!selectedFile.value) return
      
      try {
        loading.value = true
        error.value = null
        connectionStatus.value = 'connecting'
        
        const response = await logApi.getLogContent(selectedFile.value, lineCount.value)
        logs.value = response.content.map(log => logApi.parseLogEntry(log))
        
        lastUpdateTime.value = logApi.formatDateTime(new Date())
        
        if (autoScroll.value) {
          nextTick(scrollToBottom)
        }
        
        setupStreamConnection()
      } catch (err) {
        error.value = `获取日志内容失败: ${err.message}`
        connectionStatus.value = 'error'
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const setupStreamConnection = () => {
      disconnectExistingStream()
      
      disconnectStream = logApi.createLogStream(selectedFile.value, {
        onMessage: (log) => {
          logs.value.push(logApi.parseLogEntry(log))
          lastUpdateTime.value = logApi.formatDateTime(new Date())
          
          if (autoScroll.value && !isScrolledUp.value) {
            nextTick(scrollToBottom)
          }
        },
        onError: (err) => {
          error.value = `实时日志连接错误: ${err.message}`
          connectionStatus.value = 'error'
          console.error(err)
        },
        onOpen: () => {
          connectionStatus.value = 'connected'
        }
      })
    }

    const disconnectExistingStream = () => {
      if (disconnectStream) {
        disconnectStream()
        disconnectStream = null
      }
      connectionStatus.value = 'disconnected'
    }

    const scrollToBottom = () => {
      if (logContainer.value) {
        logContainer.value.scrollTop = logContainer.value.scrollHeight
      }
    }

    const handleScroll = () => {
      if (!logContainer.value) return
      
      const { scrollTop, scrollHeight, clientHeight } = logContainer.value
      isScrolledUp.value = scrollTop + clientHeight < scrollHeight - 50
      
      // 滚动到顶部时加载更多日志
      if (scrollTop < 100 && !loadingMore.value) {
        loadMoreLogs()
      }
    }

    const loadMoreLogs = async () => {
      if (loadingMore.value || !selectedFile.value) return
      
      try {
        loadingMore.value = true
        const currentScrollHeight = logContainer.value.scrollHeight
        
        const response = await logApi.getLogContent(
          selectedFile.value, 
          lineCount.value * 2
        )
        
        if (response.content.length > logs.value.length) {
          logs.value = response.content.map(log => logApi.parseLogEntry(log))
          
          nextTick(() => {
            if (logContainer.value) {
              logContainer.value.scrollTop = logContainer.value.scrollHeight - currentScrollHeight
            }
          })
        }
      } catch (err) {
        console.error('加载更多日志失败:', err)
      } finally {
        loadingMore.value = false
      }
    }

    const handleFileChange = () => {
      if (!selectedFile.value) {
        clearLogs()
        return
      }
      
      disconnectExistingStream()
      logs.value = []
      loadInitialLogs()
    }

    const toggleAutoScroll = () => {
      autoScroll.value = !autoScroll.value
      if (autoScroll.value) {
        isScrolledUp.value = false
        nextTick(scrollToBottom)
      }
    }

    const clearLogs = () => {
      disconnectExistingStream()
      logs.value = []
      selectedFile.value = ''
      error.value = null
    }

    const copyLogs = async () => {
      try {
        const logText = logs.value.map(l => l.raw).join('\n')
        await navigator.clipboard.writeText(logText)
        alert('日志已复制到剪贴板')
      } catch (err) {
        console.error('复制失败:', err)
        alert('复制失败，请手动选择日志内容复制')
      }
    }

    const downloadLogs = () => {
      const logText = logs.value.map(l => l.raw).join('\n')
      logApi.downloadLogFile(selectedFile.value || 'logs', logText)
    }

    // 生命周期
    onMounted(() => {
      loadLogFiles()
      window.addEventListener('resize', scrollToBottom)
    })

    onBeforeUnmount(() => {
      disconnectExistingStream()
      window.removeEventListener('resize', scrollToBottom)
    })

    return {
      // 状态
      logFiles,
      selectedFile,
      logs,
      lineCount,
      autoScroll,
      loading,
      loadingMore,
      error,
      lastUpdateTime,
      connectionStatus,
      logContainer,
      
      // 计算属性
      currentFileSize,
      currentFileModified,
      memoryUsage,
      connectionText,
      connectionIcon,
      
      // 方法
      handleFileChange,
      toggleAutoScroll,
      clearLogs,
      copyLogs,
      downloadLogs,
      handleScroll
    }
  }
}
</script>

<style scoped>
.log-viewer {
  display: flex;
  flex-direction: column;
  width:100%;
  height: 80vh;
  background-color: #1e1e1e;
  color: #e0e0e0;
  font-family: 'Fira Code', 'Consolas', 'Courier New', monospace;
}

/* 工具栏样式 */
.toolbar {
  padding: 0.8rem 1.2rem;
  background-color: #252526;
  border-bottom: 1px solid #3c3c3c;
}

.title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.8rem;
}

.title h1 {
  margin: 0;
  font-size: 1.4rem;
  color: #569cd6;
  font-weight: 500;
}

.controls {
  display: flex;
  gap: 0.8rem;
  flex-wrap: wrap;
  align-items: center;
}

.file-selector, .line-control {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

select, input {
  padding: 0.5rem;
  background-color: #2d2d2d;
  border: 1px solid #3c3c3c;
  color: #ffffff;
  border-radius: 4px;
  min-width: 200px;
}

.line-control input {
  width: 80px;
}

.line-control span {
  font-size: 0.9rem;
  color: #b5b5b5;
}

.btn {
  padding: 0.5rem 0.8rem;
  background-color: #333;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  transition: background-color 0.2s;
  font-size: 0.9rem;
}

.btn:hover {
  background-color: #3e3e3e;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn.active {
  background-color: #0e639c;
}

.btn-scroll.active {
  background-color: #27ae60;
}

/* 文件信息栏 */
.file-info {
  padding: 0.5rem 1rem;
  background-color: #252526;
  font-size: 0.85rem;
  color: #b5b5b5;
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  border-bottom: 1px solid #3c3c3c;
}

.file-meta, .stats {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.file-meta .label {
  color: #858585;
}

.file-meta .value {
  font-weight: 500;
}

.file-meta .divider {
  color: #3c3c3c;
  margin: 0 0.3rem;
}

.stats .lines {
  color: #569cd6;
}

.stats .memory {
  color: #b5cea8;
}

/* 日志容器 */
.log-container {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem 0;
  position: relative;
}

.loading-indicator, .error-message, .empty-logs {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  background-color: rgba(30, 30, 30, 0.9);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(86, 156, 214, 0.3);
  border-radius: 50%;
  border-top-color: #569cd6;
  animation: spin 1s linear infinite;
}

.error-message {
  color: #f14c4c;
}

.empty-logs {
  color: #858585;
}

/* 日志行样式 */
.log-line {
  padding: 0.2rem 1rem;
  display: flex;
  gap: 1rem;
  line-height: 1.5;
  border-left: 3px solid transparent;
}

.log-line:hover {
  background-color: #2a2d2e;
}

.line-number {
  color: #858585;
  min-width: 3.5rem;
  text-align: right;
  user-select: none;
}

.timestamp {
  color: #6a9955;
  min-width: 10rem;
}

.content {
  flex: 1;
  white-space: pre-wrap;
  word-break: break-all;
}

/* 日志级别样式 */
.log-error {
  border-left-color: #f14c4c;
  color: #f14c4c;
}

.log-warn {
  border-left-color: #d7ba7d;
  color: #d7ba7d;
}

.log-info {
  border-left-color: #569cd6;
  color: #569cd6;
}

.log-debug {
  border-left-color: #b5cea8;
  color: #b5cea8;
}

.log-trace {
  border-left-color: #c586c0;
  color: #c586c0;
}

.log-fatal {
  border-left-color: #ff0000;
  background-color: rgba(255, 0, 0, 0.1);
  color: #ff0000;
}

/* 状态栏 */
.status-bar {
  padding: 0.4rem 1rem;
  background-color: #007acc;
  color: white;
  font-size: 0.8rem;
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.connection-status, .update-time, .loading-more {
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.connection-status.connecting {
  color: #d7ba7d;
}

.connection-status.connected {
  color: #4ec9b0;
}

.connection-status.error {
  color: #f14c4c;
}

.connection-status.disconnected {
  color: #858585;
}

.loading-more {
  color: #d7ba7d;
}

/* 图标样式 */
.icon {
  font-style: normal;
}

.icon-logs:before { content: "📄"; }
.icon-autoscroll-on:before { content: "⇳"; color: #27ae60; }
.icon-autoscroll-off:before { content: "⇳"; }
.icon-clear:before { content: "🗑"; }
.icon-copy:before { content: "⎘"; }
.icon-download:before { content: "⤓"; }
.icon-error:before { content: "⚠"; }
.icon-empty:before { content: "📄"; }
.icon-connecting:before { content: "↻"; animation: spin 1s linear infinite; }
.icon-connected:before { content: "✓"; }
.icon-disconnected:before { content: "✗"; }
.icon-clock:before { content: "🕒"; }
.icon-loading:before { content: "↻"; animation: spin 1s linear infinite; }

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .controls {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .file-selector, .line-control {
    width: 100%;
  }
  
  select, input {
    width: 100%;
  }
  
  .file-info {
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style>