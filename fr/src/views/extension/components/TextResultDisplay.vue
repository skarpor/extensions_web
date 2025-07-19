<template>
  <div class="text-result-display">
    <!-- 文本工具栏 -->
    <div class="text-toolbar">
      <div class="toolbar-left">
        <el-tag type="info" size="small">
          {{ formatTextStats() }}
        </el-tag>
        <el-tag v-if="meta?.生成时间" type="success" size="small">
          {{ meta.生成时间 }}
        </el-tag>
      </div>
      
      <div class="toolbar-right">
        <el-button-group size="small">
          <el-button @click="toggleWrap">
            <el-icon><Switch /></el-icon>
            {{ wordWrap ? '取消换行' : '自动换行' }}
          </el-button>
          <el-button @click="copyText">
            <el-icon><CopyDocument /></el-icon>
            复制
          </el-button>
          <el-button @click="downloadText">
            <el-icon><Download /></el-icon>
            下载
          </el-button>
          <el-button @click="toggleFullscreen">
            <el-icon><FullScreen /></el-icon>
            全屏
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 文本内容区域 -->
    <div class="text-container" :class="{ fullscreen: isFullscreen }">
      <div class="text-content" :class="{ 'word-wrap': wordWrap }" ref="textContent">
        <pre>{{ content }}</pre>
      </div>
      
      <!-- 搜索功能 -->
      <div v-if="showSearch" class="search-panel">
        <el-input
          v-model="searchText"
          placeholder="搜索文本..."
          size="small"
          clearable
          @input="performSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
          <template #append>
            <el-button-group>
              <el-button @click="findPrevious" :disabled="searchResults.length === 0">
                <el-icon><ArrowUp /></el-icon>
              </el-button>
              <el-button @click="findNext" :disabled="searchResults.length === 0">
                <el-icon><ArrowDown /></el-icon>
              </el-button>
            </el-button-group>
          </template>
        </el-input>
        
        <div v-if="searchText" class="search-info">
          {{ currentSearchIndex + 1 }} / {{ searchResults.length }}
        </div>
      </div>
    </div>

    <!-- 文本统计信息 -->
    <div class="text-stats" v-if="showStats">
      <div class="stats-grid">
        <div class="stat-item">
          <span class="stat-label">字符数:</span>
          <span class="stat-value">{{ textStats.characters }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">行数:</span>
          <span class="stat-value">{{ textStats.lines }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">单词数:</span>
          <span class="stat-value">{{ textStats.words }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">段落数:</span>
          <span class="stat-value">{{ textStats.paragraphs }}</span>
        </div>
      </div>
    </div>

    <!-- 元数据信息 -->
    <div v-if="meta && Object.keys(meta).length > 0" class="meta-info">
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

    <!-- 全屏模式 -->
    <el-dialog 
      v-model="isFullscreen" 
      :show-close="false"
      fullscreen
      class="fullscreen-text-dialog"
    >
      <div class="fullscreen-text-container">
        <div class="fullscreen-toolbar">
          <div class="toolbar-left">
            <h3>文本查看器</h3>
          </div>
          <div class="toolbar-right">
            <el-button-group>
              <el-button @click="toggleSearch">
                <el-icon><Search /></el-icon>
                搜索
              </el-button>
              <el-button @click="copyText">
                <el-icon><CopyDocument /></el-icon>
                复制
              </el-button>
              <el-button @click="toggleFullscreen">
                <el-icon><Close /></el-icon>
                关闭
              </el-button>
            </el-button-group>
          </div>
        </div>
        
        <div class="fullscreen-content" :class="{ 'word-wrap': wordWrap }">
          <pre>{{ content }}</pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Switch,
  CopyDocument, 
  Download, 
  FullScreen,
  Search,
  ArrowUp,
  ArrowDown,
  Close
} from '@element-plus/icons-vue'

export default {
  name: 'TextResultDisplay',
  components: {
    Switch,
    CopyDocument,
    Download,
    FullScreen,
    Search,
    ArrowUp,
    ArrowDown,
    Close
  },
  props: {
    content: {
      type: String,
      required: true
    },
    meta: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['copy'],
  setup(props, { emit }) {
    const wordWrap = ref(false)
    const isFullscreen = ref(false)
    const showSearch = ref(false)
    const showStats = ref(true)
    const searchText = ref('')
    const searchResults = ref([])
    const currentSearchIndex = ref(0)
    const textContent = ref(null)

    // 计算文本统计信息
    const textStats = computed(() => {
      const text = props.content || ''
      return {
        characters: text.length,
        lines: text.split('\n').length,
        words: text.trim() ? text.trim().split(/\s+/).length : 0,
        paragraphs: text.split(/\n\s*\n/).filter(p => p.trim()).length
      }
    })

    // 格式化文本统计
    const formatTextStats = () => {
      const stats = textStats.value
      return `${stats.characters} 字符, ${stats.lines} 行, ${stats.words} 单词`
    }

    // 方法
    const toggleWrap = () => {
      wordWrap.value = !wordWrap.value
    }

    const toggleFullscreen = () => {
      isFullscreen.value = !isFullscreen.value
    }

    const toggleSearch = () => {
      showSearch.value = !showSearch.value
      if (!showSearch.value) {
        searchText.value = ''
        searchResults.value = []
      }
    }

    const copyText = async () => {
      try {
        await navigator.clipboard.writeText(props.content)
        emit('copy')
        ElMessage.success('文本已复制到剪贴板')
      } catch (error) {
        // 降级方案
        const textArea = document.createElement('textarea')
        textArea.value = props.content
        document.body.appendChild(textArea)
        textArea.select()
        document.execCommand('copy')
        document.body.removeChild(textArea)
        ElMessage.success('文本已复制到剪贴板')
      }
    }

    const downloadText = () => {
      try {
        const blob = new Blob([props.content], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `text-result-${Date.now()}.txt`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
        ElMessage.success('文本文件已下载')
      } catch (error) {
        ElMessage.error('下载失败: ' + error.message)
      }
    }

    const performSearch = () => {
      if (!searchText.value.trim()) {
        searchResults.value = []
        currentSearchIndex.value = 0
        return
      }

      const text = props.content.toLowerCase()
      const search = searchText.value.toLowerCase()
      const results = []
      let index = 0

      while ((index = text.indexOf(search, index)) !== -1) {
        results.push(index)
        index += search.length
      }

      searchResults.value = results
      currentSearchIndex.value = 0

      if (results.length > 0) {
        highlightSearchResult()
      }
    }

    const findNext = () => {
      if (searchResults.value.length === 0) return
      
      currentSearchIndex.value = (currentSearchIndex.value + 1) % searchResults.value.length
      highlightSearchResult()
    }

    const findPrevious = () => {
      if (searchResults.value.length === 0) return
      
      currentSearchIndex.value = currentSearchIndex.value === 0 
        ? searchResults.value.length - 1 
        : currentSearchIndex.value - 1
      highlightSearchResult()
    }

    const highlightSearchResult = () => {
      // 这里可以实现高亮显示搜索结果的逻辑
      // 由于是纯文本，可以通过滚动到对应位置来实现
      nextTick(() => {
        if (textContent.value) {
          const element = textContent.value.querySelector('pre')
          if (element) {
            // 简单的滚动到搜索位置
            const position = searchResults.value[currentSearchIndex.value]
            const lines = props.content.substring(0, position).split('\n').length
            const lineHeight = 20 // 估算行高
            element.scrollTop = Math.max(0, (lines - 5) * lineHeight)
          }
        }
      })
    }

    // 监听搜索文本变化
    watch(searchText, () => {
      performSearch()
    })

    return {
      wordWrap,
      isFullscreen,
      showSearch,
      showStats,
      searchText,
      searchResults,
      currentSearchIndex,
      textContent,
      textStats,
      formatTextStats,
      toggleWrap,
      toggleFullscreen,
      toggleSearch,
      copyText,
      downloadText,
      performSearch,
      findNext,
      findPrevious
    }
  }
}
</script>

<style scoped>
.text-result-display {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.text-toolbar {
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

.text-container {
  position: relative;
  max-height: 600px;
  overflow: auto;
}

.text-container.fullscreen {
  max-height: none;
  height: 100vh;
}

.text-content {
  padding: 20px;
  background: #f8f9fa;
}

.text-content pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #2c3e50;
  background: white;
  padding: 20px;
  border-radius: 6px;
  border: 1px solid #e9ecef;
  overflow-x: auto;
}

.text-content.word-wrap pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-x: hidden;
}

.search-panel {
  position: absolute;
  top: 20px;
  right: 20px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 10;
}

.search-info {
  font-size: 12px;
  color: #6c757d;
  white-space: nowrap;
}

.text-stats {
  padding: 16px;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.stat-label {
  font-weight: 600;
  color: #495057;
}

.stat-value {
  color: #6c757d;
  font-family: 'Monaco', 'Menlo', monospace;
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
.fullscreen-text-dialog :deep(.el-dialog__body) {
  padding: 0;
  height: 100vh;
  background: #f8f9fa;
}

.fullscreen-text-container {
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

.fullscreen-content {
  flex: 1;
  padding: 24px;
  overflow: auto;
}

.fullscreen-content pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #2c3e50;
  background: white;
  padding: 24px;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  min-height: calc(100vh - 200px);
}

.fullscreen-content.word-wrap pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
