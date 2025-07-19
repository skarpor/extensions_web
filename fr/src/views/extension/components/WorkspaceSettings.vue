<template>
  <div class="workspace-settings">
    <el-form :model="settings" label-width="120px">
      <!-- 基础设置 -->
      <div class="settings-section">
        <h3>基础设置</h3>
        
        <el-form-item label="自动刷新">
          <el-switch 
            v-model="settings.autoRefresh"
            active-text="开启"
            inactive-text="关闭"
          />
          <div class="form-tip">自动刷新扩展列表和结果</div>
        </el-form-item>

        <el-form-item label="刷新间隔" v-if="settings.autoRefresh">
          <el-input-number
            v-model="settings.refreshInterval"
            :min="5"
            :max="300"
            :step="5"
            controls-position="right"
          />
          <span class="unit">秒</span>
          <div class="form-tip">自动刷新的时间间隔</div>
        </el-form-item>

        <el-form-item label="显示执行时间">
          <el-switch 
            v-model="settings.showExecutionTime"
            active-text="显示"
            inactive-text="隐藏"
          />
          <div class="form-tip">在结果中显示扩展执行时间</div>
        </el-form-item>

        <el-form-item label="启用通知">
          <el-switch 
            v-model="settings.enableNotifications"
            active-text="开启"
            inactive-text="关闭"
          />
          <div class="form-tip">执行完成后显示通知消息</div>
        </el-form-item>
      </div>

      <!-- 显示设置 -->
      <div class="settings-section">
        <h3>显示设置</h3>
        
        <el-form-item label="默认结果视图">
          <el-select v-model="settings.defaultResultView" placeholder="选择默认视图">
            <el-option label="自动适应" value="auto" />
            <el-option label="紧凑模式" value="compact" />
            <el-option label="详细模式" value="detailed" />
            <el-option label="全屏模式" value="fullscreen" />
          </el-select>
          <div class="form-tip">扩展结果的默认显示模式</div>
        </el-form-item>

        <el-form-item label="主题模式">
          <el-radio-group v-model="settings.themeMode">
            <el-radio label="light">浅色主题</el-radio>
            <el-radio label="dark">深色主题</el-radio>
            <el-radio label="auto">跟随系统</el-radio>
          </el-radio-group>
          <div class="form-tip">工作台的主题外观</div>
        </el-form-item>

        <el-form-item label="侧边栏宽度">
          <el-slider
            v-model="settings.sidebarWidth"
            :min="250"
            :max="500"
            :step="10"
            show-input
          />
          <div class="form-tip">扩展列表侧边栏的宽度</div>
        </el-form-item>

        <el-form-item label="结果区域高度">
          <el-slider
            v-model="settings.resultAreaHeight"
            :min="300"
            :max="800"
            :step="50"
            show-input
          />
          <div class="form-tip">结果显示区域的最大高度</div>
        </el-form-item>
      </div>

      <!-- 性能设置 -->
      <div class="settings-section">
        <h3>性能设置</h3>
        
        <el-form-item label="缓存结果">
          <el-switch 
            v-model="settings.cacheResults"
            active-text="开启"
            inactive-text="关闭"
          />
          <div class="form-tip">缓存扩展执行结果以提高性能</div>
        </el-form-item>

        <el-form-item label="缓存时间" v-if="settings.cacheResults">
          <el-input-number
            v-model="settings.cacheTimeout"
            :min="1"
            :max="60"
            controls-position="right"
          />
          <span class="unit">分钟</span>
          <div class="form-tip">结果缓存的有效时间</div>
        </el-form-item>

        <el-form-item label="最大并发数">
          <el-input-number
            v-model="settings.maxConcurrency"
            :min="1"
            :max="10"
            controls-position="right"
          />
          <div class="form-tip">同时执行的扩展数量限制</div>
        </el-form-item>

        <el-form-item label="超时时间">
          <el-input-number
            v-model="settings.executionTimeout"
            :min="10"
            :max="300"
            :step="10"
            controls-position="right"
          />
          <span class="unit">秒</span>
          <div class="form-tip">扩展执行的超时时间</div>
        </el-form-item>
      </div>

      <!-- 安全设置 -->
      <div class="settings-section">
        <h3>安全设置</h3>
        
        <el-form-item label="确认危险操作">
          <el-switch 
            v-model="settings.confirmDangerousActions"
            active-text="开启"
            inactive-text="关闭"
          />
          <div class="form-tip">执行可能有风险的扩展前显示确认对话框</div>
        </el-form-item>

        <el-form-item label="记录执行日志">
          <el-switch 
            v-model="settings.logExecutions"
            active-text="开启"
            inactive-text="关闭"
          />
          <div class="form-tip">记录所有扩展执行的详细日志</div>
        </el-form-item>

        <el-form-item label="允许文件下载">
          <el-switch 
            v-model="settings.allowFileDownloads"
            active-text="允许"
            inactive-text="禁止"
          />
          <div class="form-tip">是否允许扩展生成和下载文件</div>
        </el-form-item>
      </div>

      <!-- 高级设置 -->
      <div class="settings-section">
        <h3>高级设置</h3>
        
        <el-form-item label="调试模式">
          <el-switch 
            v-model="settings.debugMode"
            active-text="开启"
            inactive-text="关闭"
          />
          <div class="form-tip">显示详细的调试信息和错误堆栈</div>
        </el-form-item>

        <el-form-item label="API基础URL">
          <el-input
            v-model="settings.apiBaseUrl"
            placeholder="http://localhost:8000"
          />
          <div class="form-tip">扩展API的基础URL地址</div>
        </el-form-item>

        <el-form-item label="请求超时">
          <el-input-number
            v-model="settings.requestTimeout"
            :min="5"
            :max="120"
            :step="5"
            controls-position="right"
          />
          <span class="unit">秒</span>
          <div class="form-tip">API请求的超时时间</div>
        </el-form-item>

        <el-form-item label="重试次数">
          <el-input-number
            v-model="settings.retryCount"
            :min="0"
            :max="5"
            controls-position="right"
          />
          <div class="form-tip">请求失败时的重试次数</div>
        </el-form-item>
      </div>

      <!-- 操作按钮 -->
      <div class="settings-actions">
        <el-button @click="resetToDefaults">恢复默认</el-button>
        <el-button @click="exportSettings">导出设置</el-button>
        <el-button @click="importSettings">导入设置</el-button>
        <el-button type="primary" @click="saveSettings">保存设置</el-button>
      </div>
    </el-form>

    <!-- 导入设置对话框 -->
    <el-dialog v-model="showImportDialog" title="导入设置" width="500px">
      <el-input
        v-model="importData"
        type="textarea"
        :rows="10"
        placeholder="请粘贴设置JSON数据..."
      />
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" @click="doImportSettings">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'WorkspaceSettings',
  props: {
    modelValue: {
      type: Object,
      required: true
    }
  },
  emits: ['update:modelValue', 'save'],
  setup(props, { emit }) {
    const showImportDialog = ref(false)
    const importData = ref('')

    // 默认设置
    const defaultSettings = {
      // 基础设置
      autoRefresh: false,
      refreshInterval: 30,
      showExecutionTime: true,
      enableNotifications: true,
      
      // 显示设置
      defaultResultView: 'auto',
      themeMode: 'light',
      sidebarWidth: 320,
      resultAreaHeight: 600,
      
      // 性能设置
      cacheResults: true,
      cacheTimeout: 5,
      maxConcurrency: 3,
      executionTimeout: 60,
      
      // 安全设置
      confirmDangerousActions: true,
      logExecutions: true,
      allowFileDownloads: true,
      
      // 高级设置
      debugMode: false,
      apiBaseUrl: 'http://localhost:8000',
      requestTimeout: 30,
      retryCount: 2
    }

    // 响应式设置对象
    const settings = reactive({ ...defaultSettings, ...props.modelValue })

    // 监听设置变化
    watch(settings, (newSettings) => {
      emit('update:modelValue', { ...newSettings })
    }, { deep: true })

    // 方法
    const resetToDefaults = async () => {
      try {
        await ElMessageBox.confirm('确定要恢复所有设置到默认值吗？', '确认重置', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        Object.assign(settings, defaultSettings)
        ElMessage.success('设置已恢复到默认值')
      } catch {
        // 用户取消
      }
    }

    const exportSettings = () => {
      try {
        const settingsJson = JSON.stringify(settings, null, 2)
        const blob = new Blob([settingsJson], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `workspace-settings-${Date.now()}.json`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
        ElMessage.success('设置已导出')
      } catch (error) {
        ElMessage.error('导出失败: ' + error.message)
      }
    }

    const importSettings = () => {
      showImportDialog.value = true
      importData.value = ''
    }

    const doImportSettings = () => {
      try {
        const importedSettings = JSON.parse(importData.value)
        
        // 验证设置格式
        if (typeof importedSettings !== 'object') {
          throw new Error('无效的设置格式')
        }
        
        // 合并设置
        Object.assign(settings, defaultSettings, importedSettings)
        
        showImportDialog.value = false
        ElMessage.success('设置导入成功')
      } catch (error) {
        ElMessage.error('导入失败: ' + error.message)
      }
    }

    const saveSettings = () => {
      emit('save', { ...settings })
    }

    return {
      settings,
      showImportDialog,
      importData,
      resetToDefaults,
      exportSettings,
      importSettings,
      doImportSettings,
      saveSettings
    }
  }
}
</script>

<style scoped>
.workspace-settings {
  max-height: 70vh;
  overflow-y: auto;
  padding: 20px;
}

.settings-section {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e9ecef;
}

.settings-section:last-of-type {
  border-bottom: none;
}

.settings-section h3 {
  margin: 0 0 20px 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 8px;
}

.settings-section h3::before {
  content: '';
  width: 4px;
  height: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 2px;
}

.form-tip {
  font-size: 12px;
  color: #6c757d;
  margin-top: 4px;
  line-height: 1.4;
}

.unit {
  margin-left: 8px;
  color: #6c757d;
  font-size: 14px;
}

.settings-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 24px;
  border-top: 1px solid #e9ecef;
  margin-top: 32px;
}

/* 表单项样式优化 */
.workspace-settings :deep(.el-form-item) {
  margin-bottom: 24px;
}

.workspace-settings :deep(.el-form-item__label) {
  font-weight: 600;
  color: #495057;
}

.workspace-settings :deep(.el-switch) {
  margin-right: 12px;
}

.workspace-settings :deep(.el-slider) {
  margin-right: 20px;
}

.workspace-settings :deep(.el-input-number) {
  width: 120px;
}

.workspace-settings :deep(.el-select) {
  width: 200px;
}

.workspace-settings :deep(.el-radio-group) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .workspace-settings {
    padding: 16px;
  }
  
  .settings-actions {
    flex-direction: column;
  }
  
  .workspace-settings :deep(.el-form-item__label) {
    width: 100px !important;
  }
}
</style>
