<template>
  <div class="markdown-editor-container">
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button-group>
          <el-button @click="refreshFileList" :loading="loadingFiles">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <el-button @click="saveFile" :loading="saving" type="primary">
            <el-icon><Document /></el-icon>
            保存
          </el-button>
        </el-button-group>
        
        <el-button-group class="ml-3">
          <el-button @click="insertTemplate('heading')" size="small">
            <el-icon><List /></el-icon>
            标题
          </el-button>
          <el-button @click="insertTemplate('bold')" size="small">
            <strong>B</strong>
          </el-button>
          <el-button @click="insertTemplate('italic')" size="small">
            <em>I</em>
          </el-button>
          <el-button @click="insertTemplate('code')" size="small">
            <el-icon><EditPen /></el-icon>
            代码
          </el-button>
          <el-button @click="insertTemplate('link')" size="small">
            <el-icon><Link /></el-icon>
            链接
          </el-button>
          <el-button @click="insertTemplate('image')" size="small">
            <el-icon><Picture /></el-icon>
            图片
          </el-button>
          <el-button @click="insertTemplate('table')" size="small">
            <el-icon><Grid /></el-icon>
            表格
          </el-button>
        </el-button-group>
      </div>
      
      <div class="toolbar-right">
        <el-switch
          v-model="previewMode"
          active-text="预览模式"
          inactive-text="编辑模式"
          @change="togglePreviewMode"
        />
        
        <el-dropdown @command="handleFileAction" class="ml-3">
          <el-button>
            文件操作
            <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="new">新建文件</el-dropdown-item>
              <el-dropdown-item command="export">导出HTML</el-dropdown-item>
              <el-dropdown-item command="settings">设置文件路径</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 文件路径显示 -->
    <div class="file-path-bar" v-if="currentFilePath">
      <el-icon><Folder /></el-icon>
      <span class="file-path">{{ currentFilePath }}</span>
      <el-tag v-if="hasUnsavedChanges" type="warning" size="small">未保存</el-tag>
    </div>

    <!-- 编辑器主体 -->
    <div class="editor-main">
      <!-- 文件列表侧边栏 -->
      <div class="file-sidebar">
        <div class="sidebar-header">
          <span>Markdown文件</span>
          <el-button @click="refreshFileList" size="small" :loading="loadingFiles">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>

        <div class="sidebar-content">
          <div class="folder-path" v-if="folderPath">
            <el-icon><Folder /></el-icon>
            <span>{{ folderPath }}</span>
          </div>

          <div class="file-list">
            <div
              v-for="file in markdownFiles"
              :key="file.path"
              class="file-item"
              :class="{ active: file.path === currentFilePath }"
              @click="selectFile(file)"
            >
              <div class="file-info">
                <el-icon><Document /></el-icon>
                <span class="file-name">{{ file.name }}</span>
              </div>
              <div class="file-actions">
                <el-button
                  @click.stop="deleteFile(file)"
                  size="small"
                  type="danger"
                  text
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </div>

          <div class="sidebar-footer">
            <el-button @click="showNewFileDialog = true" type="primary" size="small" block>
              <el-icon><Plus /></el-icon>
              新建文件
            </el-button>
          </div>
        </div>
      </div>

      <!-- 编辑和预览区域 -->
      <div class="content-area" :class="{ 'preview-only': previewMode }">
        <!-- 编辑区域 -->
        <div class="editor-panel" v-show="!previewMode">
          <div class="editor-header">
            <span>{{ currentFileName || 'Markdown 编辑器' }}</span>
            <div class="editor-stats">
              <span>行数: {{ lineCount }}</span>
              <span class="ml-3">字数: {{ wordCount }}</span>
            </div>
          </div>
          <textarea
            ref="markdownTextarea"
            v-model="markdownContent"
            class="markdown-textarea"
            placeholder="选择一个文件开始编辑，或创建新文件..."
            @input="onContentChange"
            @scroll="syncScroll"
            @keydown="handleKeydown"
          ></textarea>
        </div>

        <!-- 预览区域 -->
        <div class="preview-panel">
          <div class="preview-header">
            <span>实时预览</span>
            <el-button-group size="small">
              <el-button @click="copyHtml" size="small">
                <el-icon><CopyDocument /></el-icon>
                复制HTML
              </el-button>
              <el-button @click="printPreview" size="small">
                <el-icon><Printer /></el-icon>
                打印
              </el-button>
            </el-button-group>
          </div>
          <div
            ref="previewContainer"
            class="preview-content"
            v-html="renderedHtml"
            @scroll="syncPreviewScroll"
          ></div>
        </div>
      </div>
    </div>

    <!-- 新建文件对话框 -->
    <el-dialog v-model="showNewFileDialog" title="新建Markdown文件" width="500px">
      <el-form :model="newFileForm" label-width="100px">
        <el-form-item label="文件名">
          <el-input
            v-model="newFileForm.name"
            placeholder="例如: new-document.md"
            clearable
          >
            <template #suffix>
              <span v-if="!newFileForm.name.endsWith('.md')">.md</span>
            </template>
          </el-input>
          <div class="form-tip">文件将创建在配置的Markdown文件夹中</div>
        </el-form-item>
        <el-form-item label="初始内容">
          <el-select v-model="newFileForm.template" placeholder="选择模板">
            <el-option label="空白文档" value="blank" />
            <el-option label="README模板" value="readme" />
            <el-option label="API文档模板" value="api" />
            <el-option label="项目文档模板" value="project" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showNewFileDialog = false">取消</el-button>
        <el-button type="primary" @click="createNewFile" :loading="creating">创建</el-button>
      </template>
    </el-dialog>


  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh,
  Document,
  Link,
  Picture,
  Folder,
  CopyDocument,
  Printer,
  ArrowDown,
  Delete,
  Plus,
  EditPen,
  List,
  Grid,
  Files
} from '@element-plus/icons-vue'
import { marked } from 'marked'
import {
  getMarkdownList,
  loadMarkdownFile,
  saveMarkdownFile,
  createMarkdownFile,
  deleteMarkdownFile
} from '@/api/markdown'

export default {
  name: 'MarkdownEditor',
  components: {
    Refresh,
    Document,
    Link,
    Picture,
    Folder,
    CopyDocument,
    Printer,
    ArrowDown,
    Delete,
    Plus,
    EditPen,
    List,
    Grid,
    Files
  },
  setup() {
    // 响应式数据
    const markdownContent = ref('')
    const originalContent = ref('')
    const currentFilePath = ref('')
    const currentFileName = ref('')
    const folderPath = ref('')
    const previewMode = ref(true)
    const loading = ref(false)
    const saving = ref(false)
    const creating = ref(false)
    const loadingFiles = ref(false)

    // 文件列表
    const markdownFiles = ref([])

    // 对话框状态
    const showNewFileDialog = ref(false)

    // 表单数据
    const newFileForm = ref({
      name: '',
      template: 'blank'
    })
    
    // DOM引用
    const markdownTextarea = ref(null)
    const previewContainer = ref(null)
    
    // 计算属性
    const hasUnsavedChanges = computed(() => {
      return markdownContent.value !== originalContent.value
    })
    
    const lineCount = computed(() => {
      return markdownContent.value.split('\n').length
    })
    
    const wordCount = computed(() => {
      return markdownContent.value.replace(/\s+/g, ' ').trim().length
    })
    
    const renderedHtml = computed(() => {
      try {
        return marked(markdownContent.value)
      } catch (error) {
        return `<p style="color: red;">Markdown解析错误: ${error.message}</p>`
      }
    })
    
    // 方法
    const loadFileList = async () => {
      try {
        loadingFiles.value = true
        const data = await getMarkdownList()
        markdownFiles.value = data.files || []
        folderPath.value = data.folder_path || ''
        ElMessage.success(`加载到 ${markdownFiles.value.length} 个文件`)
      } catch (error) {
        ElMessage.error('加载文件列表失败: ' + error.message)
      } finally {
        loadingFiles.value = false
      }
    }

    const loadFileContent = async (filePath) => {
      try {
        loading.value = true
        const data = await loadMarkdownFile(filePath)
        markdownContent.value = data.content || ''
        originalContent.value = markdownContent.value
        currentFilePath.value = filePath
        currentFileName.value = filePath.split('/').pop()
      } catch (error) {
        ElMessage.error('加载文件失败: ' + error.message)
      } finally {
        loading.value = false
      }
    }

    const saveFile = async () => {
      try {
        saving.value = true
        await saveMarkdownFile(markdownContent.value, currentFilePath.value)
        originalContent.value = markdownContent.value
        ElMessage.success('保存成功')
      } catch (error) {
        ElMessage.error('保存失败: ' + error.message)
      } finally {
        saving.value = false
      }
    }

    const insertTemplate = (type) => {
      const textarea = markdownTextarea.value
      if (!textarea) return

      const start = textarea.selectionStart
      const end = textarea.selectionEnd
      const selectedText = markdownContent.value.substring(start, end)

      let insertText = ''
      switch (type) {
        case 'heading': insertText = `# ${selectedText || '标题'}`; break
        case 'bold': insertText = `**${selectedText || '粗体'}**`; break
        case 'italic': insertText = `*${selectedText || '斜体'}*`; break
        case 'code': insertText = `\`${selectedText || '代码'}\``; break
        case 'link': insertText = `[${selectedText || '链接'}](url)`; break
        case 'image': insertText = `![${selectedText || '图片'}](url)`; break
        case 'table': insertText = '| 列1 | 列2 |\n|-----|-----|\n| 内容 | 内容 |'; break
      }

      markdownContent.value = markdownContent.value.substring(0, start) +
                             insertText +
                             markdownContent.value.substring(end)
    }

    const selectFile = (file) => {
      if (hasUnsavedChanges.value) {
        ElMessageBox.confirm('当前有未保存的更改，确定要切换文件吗？', '确认', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          loadFileContent(file.path)
        }).catch(() => {})
      } else {
        loadFileContent(file.path)
      }
    }

    const refreshFileList = () => {
      loadFileList()
    }

    const deleteFile = async (file) => {
      try {
        await ElMessageBox.confirm(`确定要删除文件 "${file.name}" 吗？`, '确认删除', {
          confirmButtonText: '删除',
          cancelButtonText: '取消',
          type: 'warning'
        })

        await deleteMarkdownFile(file.path)

        ElMessage.success('文件删除成功')
        if (file.path === currentFilePath.value) {
          markdownContent.value = ''
          originalContent.value = ''
          currentFilePath.value = ''
          currentFileName.value = ''
        }
        loadFileList()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败: ' + error.message)
        }
      }
    }

    const handleFileAction = (command) => {
      switch (command) {
        case 'new': showNewFileDialog.value = true; break
        case 'export': exportHtml(); break
        case 'settings':
          ElMessage.info('请在系统设置中配置Markdown文件夹路径')
          break
      }
    }

    const createNewFile = async () => {
      if (!newFileForm.value.name) {
        ElMessage.warning('请输入文件名')
        return
      }

      let fileName = newFileForm.value.name
      if (!fileName.endsWith('.md')) {
        fileName += '.md'
      }

      try {
        creating.value = true
        const data = await createMarkdownFile(fileName, newFileForm.value.template)
        showNewFileDialog.value = false
        newFileForm.value = { name: '', template: 'blank' }
        loadFileList()
        // 自动选择新创建的文件
        if (data.file_path) {
          loadFileContent(data.file_path)
        }
        ElMessage.success('创建成功')
      } catch (error) {
        ElMessage.error('创建失败: ' + error.message)
      } finally {
        creating.value = false
      }
    }

    const exportHtml = () => {
      const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Export</title></head><body>${renderedHtml.value}</body></html>`
      const blob = new Blob([html], { type: 'text/html' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'export.html'
      a.click()
      URL.revokeObjectURL(url)
    }

    const copyHtml = () => {
      navigator.clipboard.writeText(renderedHtml.value)
      ElMessage.success('已复制HTML')
    }

    const printPreview = () => {
      window.print()
    }

    const onContentChange = () => {}
    const syncScroll = () => {}
    const syncPreviewScroll = () => {}
    const handleKeydown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault()
        saveFile()
      }
    }
    const togglePreviewMode = () => {}

    onMounted(() => {
      loadFileList()
    })

    return {
      markdownContent, originalContent, currentFilePath, currentFileName,
      folderPath, previewMode, loading, saving, creating, loadingFiles,
      showNewFileDialog, newFileForm, markdownFiles, markdownTextarea,
      previewContainer, hasUnsavedChanges, lineCount, wordCount, renderedHtml,
      loadFileList, loadFileContent, selectFile, refreshFileList, deleteFile,
      saveFile, insertTemplate, handleFileAction, createNewFile,
      exportHtml, copyHtml, printPreview, onContentChange,
      syncScroll, syncPreviewScroll, handleKeydown, togglePreviewMode
    }
  }
}
</script>

<style scoped>
.markdown-editor-container {
  height: 80vh;
  display: flex;
  flex-direction: column;
  background: #fff;
  width: 100%;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
  background: #fafbfc;
}

.toolbar-left {
  display: flex;
  align-items: center;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.file-path-bar {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  font-size: 14px;
  color: #606266;
}

.file-path {
  margin-left: 8px;
  flex: 1;
}

.editor-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 文件侧边栏 */
.file-sidebar {
  width: 280px;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  background: #fafbfc;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
  background: #f5f7fa;
  font-weight: 600;
}

.sidebar-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.folder-path {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background: #f0f2f5;
  border-bottom: 1px solid #e4e7ed;
  font-size: 12px;
  color: #606266;
  gap: 6px;
}

.file-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.file-item:hover {
  background: #f0f2f5;
}

.file-item.active {
  background: #e6f7ff;
  border-right: 3px solid #409eff;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 14px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-actions {
  opacity: 0;
  transition: opacity 0.2s;
}

.file-item:hover .file-actions {
  opacity: 1;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
}

/* 内容区域 */
.content-area {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.content-area.preview-only .editor-panel {
  display: none;
}

.content-area.preview-only .preview-panel {
  width: 100%;
}

.editor-panel,
.preview-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e4e7ed;
}

.preview-panel {
  border-right: none;
}

.editor-header,
.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  font-weight: 600;
}

.editor-stats {
  font-size: 12px;
  color: #909399;
  font-weight: normal;
}

.markdown-textarea {
  flex: 1;
  border: none;
  outline: none;
  padding: 16px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.6;
  resize: none;
  background: #fff;
}

.preview-content {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  background: #fff;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.ml-3 {
  margin-left: 12px;
}

/* Markdown预览样式 */
.preview-content :deep(h1),
.preview-content :deep(h2),
.preview-content :deep(h3),
.preview-content :deep(h4),
.preview-content :deep(h5),
.preview-content :deep(h6) {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}

.preview-content :deep(h1) {
  font-size: 2em;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 10px;
}

.preview-content :deep(h2) {
  font-size: 1.5em;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 8px;
}

.preview-content :deep(code) {
  background: #f6f8fa;
  border-radius: 3px;
  padding: 2px 4px;
  font-size: 85%;
}

.preview-content :deep(pre) {
  background: #f6f8fa;
  border-radius: 6px;
  padding: 16px;
  overflow: auto;
}

.preview-content :deep(blockquote) {
  border-left: 4px solid #dfe2e5;
  padding-left: 16px;
  color: #6a737d;
}

.preview-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
}

.preview-content :deep(th),
.preview-content :deep(td) {
  border: 1px solid #dfe2e5;
  padding: 8px 12px;
  text-align: left;
}

.preview-content :deep(th) {
  background: #f6f8fa;
  font-weight: 600;
}
</style>
