<template>
  <div class="extensions-container">
    <h1>扩展管理</h1>
    
    <div class="actions mb-4">
      <button class="btn btn-primary me-2" @click="openInstallModal">
        <i class="fas fa-plus-circle"></i> 安装扩展
      </button>
      <button class="btn btn-secondary me-2" @click="refreshExtensions">
        <i class="fas fa-sync"></i> 刷新
      </button>
      <RouterLink to="/extension-query" class="btn btn-info">
        <i class="fas fa-search"></i> 扩展查询界面
      </RouterLink>
    </div>
    
    <div class="alert alert-info" v-if="!extensions.length">
      <p>没有已安装的扩展。</p>
    </div>
    
    <div class="extensions-grid" v-else>
      <div 
        v-for="extension in extensions" 
        :key="extension.id" 
        class="extension-card"
        :class="{ disabled: !extension.enabled }"
      >
        <div class="extension-header">
          <h3>{{ extension.name }}</h3>
          <div class="extension-version">{{ extension.version || '1.0' }}</div>
        </div>
        <div class="extension-body">
          <p>{{ extension.description || '暂无描述' }}</p>
          <div class="extension-meta">
            <div class="extension-author">创建者: {{ extension.creator.nickname || '系统' }}</div>
            <div class="extension-updated">更新时间: {{ formatDate(extension.updated_at || extension.created_at) }}</div>
          </div>
          <div class="extension-features">
            <span v-if="extension.has_config_form" class="feature-badge">
              <i class="fas fa-cog"></i> 配置
            </span>
            <span v-if="extension.has_query_form" class="feature-badge">
              <i class="fas fa-search"></i> 查询
            </span>
            <span class="feature-badge" :class="{'active': extension.enabled}">
              <i class="fas fa-power-off"></i> {{ extension.enabled ? '已启用' : '已禁用' }}
            </span>
            <span class="feature-badge" :class="{'active': extension.show_in_home}">
              <i class="fas fa-home"></i> {{ extension.show_in_home ? '首页显示' : '首页隐藏' }}
            </span>
          </div>
        </div>
        <div class="extension-footer">
          <div class="form-check form-switch">
            <input 
              class="form-check-input" 
              type="checkbox" 
              :id="`extension-${extension.id}`" 
              v-model="extension.enabled"
              @change="toggleExtension(extension, 'enabled')"
            >
            <label class="form-check-label" :for="`extension-${extension.id}`">
              {{ extension.enabled ? '启用' : '禁用' }}
            </label>
          </div>
          <div class="form-check form-switch">
            <input 
              class="form-check-input" 
              type="checkbox" 
              :id="`extension-${extension.id}-show-in-home`" 
              v-model="extension.show_in_home"
              @change="toggleExtension(extension, 'show_in_home')"
            >
            <label class="form-check-label" :for="`extension-${extension.id}-show-in-home`">
              {{ extension.show_in_home ? '显示' : '隐藏' }}
            </label>
          </div>
          <div class="extension-actions">
            <button class="btn btn-sm btn-outline-primary" @click="configureExtension(extension)">
              <i class="fas fa-cog"></i>
            </button>
            <!-- <RouterLink :to="`/extensions/${extension.id}`" class="btn btn-sm btn-outline-info">
              <i class="fas fa-info-circle"></i>
            </RouterLink> -->
            <button class="btn btn-sm btn-outline-danger" @click="uninstallExtension(extension)">
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 安装扩展模态框 -->
    <el-dialog
      v-model="showInstallModal"
      title="安装扩展"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="installFormRef"
        :model="installForm"
        :rules="installRules"
        label-width="100px"
        label-position="left"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="名称" prop="name">
              <el-input
                v-model="installForm.name"
                placeholder="输入扩展名称"
                clearable
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="执行模式" prop="executionMode">
              <el-select v-model="installForm.executionMode" placeholder="选择执行模式" style="width: 100%">
                <el-option label="手动" value="manual" />
                <el-option label="自动" value="auto" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="渲染类型" prop="renderType">
              <el-select v-model="installForm.renderType" placeholder="选择渲染类型" style="width: 100%">
                <el-option label="HTML" value="html" />
                <el-option label="表格" value="table" />
                <el-option label="图片" value="image" />
                <el-option label="文件" value="file" />
                <el-option label="文本" value="text" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="首页显示">
              <el-switch
                v-model="installForm.showInHome"
                active-text="显示"
                inactive-text="隐藏"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="描述信息" prop="description">
          <el-input
            v-model="installForm.description"
            type="textarea"
            :rows="3"
            placeholder="输入扩展描述"
            show-word-limit
            maxlength="500"
          />
        </el-form-item>

        <el-form-item label="扩展文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :show-file-list="true"
            :limit="1"
            accept=".py"
            :on-change="handleFileSelect"
            :on-remove="handleFileRemove"
          >
            <template #trigger>
              <el-button type="primary">
                <el-icon><Upload /></el-icon>
                选择文件
              </el-button>
            </template>
            <template #tip>
              <div class="el-upload__tip">
                上传包含 execute_query() 函数的Python文件，文件大小不超过10MB
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item v-if="installProgress > 0">
          <el-progress
            :percentage="installProgress"
            :stroke-width="8"
            :text-inside="true"
            status="success"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showInstallModal = false">取消</el-button>
          <el-button
            type="primary"
            @click="installExtension"
            :disabled="!canInstall"
            :loading="installing"
          >
            <el-icon><Upload /></el-icon>
            安装扩展
          </el-button>
        </div>
      </template>
    </el-dialog>
    
    <!-- 配置扩展模态框 -->
    <el-dialog
      v-model="showConfigModal"
      :title="`配置扩展: ${currentExtension?.name}`"
      width="1000px"
      :close-on-click-modal="false"
      top="5vh"
    >
      <div v-if="configLoading" class="loading-container">
        <el-loading-directive v-loading="true" element-loading-text="加载配置中...">
          <div style="height: 200px;"></div>
        </el-loading-directive>
      </div>

      <el-alert
        v-else-if="configError"
        :title="configError"
        type="error"
        show-icon
        :closable="false"
      />

      <div v-else>
        <el-form
          ref="configFormRef"
          :model="configValues"
          :rules="configRules"
          label-width="120px"
          label-position="left"
        >
          <!-- 基本设置 -->
          <el-card class="config-card" shadow="never">
            <template #header>
              <div class="card-header">
                <el-icon><Setting /></el-icon>
                <span>基本设置</span>
              </div>
            </template>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="名称" prop="name">
                  <el-input v-model="configValues.name" placeholder="扩展名称" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="API端点" prop="endpoint">
                  <el-input v-model="configValues.endpoint" disabled />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="返回值类型" prop="return_type">
                  <el-select v-model="configValues.return_type" style="width: 100%">
                    <el-option label="HTML" value="html" />
                    <el-option label="JSON列表" value="table" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
            <el-form-item label="执行模式" prop="executionMode">
              <el-select v-model="installForm.executionMode" placeholder="选择执行模式" style="width: 100%">
                <el-option label="手动" value="manual" />
                <el-option label="自动" value="auto" />
              </el-select>
            </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="首页显示">
                  <el-switch
                    v-model="configValues.showinindex"
                    active-text="显示"
                    inactive-text="隐藏"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="启用扩展">
                  <el-switch
                    v-model="configValues.enabled"
                    active-text="启用"
                    inactive-text="禁用"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="描述" prop="description">
              <el-input
                v-model="configValues.description"
                type="textarea"
                :rows="3"
                placeholder="扩展描述"
                show-word-limit
                maxlength="500"
              />
            </el-form-item>
          </el-card>

          <!-- 扩展文档 -->
          <el-card v-if="extensionDocumentation" class="config-card" shadow="never">
            <template #header>
              <div class="card-header">
                <el-icon><Document /></el-icon>
                <span>使用说明</span>
              </div>
            </template>

            <el-collapse v-model="activeDocCollapse" accordion>
              <el-collapse-item title="模块说明" name="module">
                <div class="doc-content" v-html="parsedModuleDoc"></div>
              </el-collapse-item>
              <el-collapse-item title="方法说明" name="methods">
                <div class="methods-doc">
                  <el-descriptions :column="1" border>
                    <el-descriptions-item label="execute_query">
                      <div v-html="parsedExecuteQueryDoc"></div>
                    </el-descriptions-item>
                    <el-descriptions-item label="get_config_form">
                      <div v-html="parsedGetConfigFormDoc"></div>
                    </el-descriptions-item>
                    <el-descriptions-item label="get_default_config">
                      <div v-html="parsedGetDefaultConfigDoc"></div>
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </el-collapse-item>
            </el-collapse>
          </el-card>

          <!-- 扩展配置表单 -->
          <el-card v-if="currentExtension?.has_config_form" class="config-card" shadow="never">
            <template #header>
              <div class="card-header">
                <el-icon><Tools /></el-icon>
                <span>扩展设置</span>
              </div>
            </template>

            <!-- 动态渲染扩展配置字段 -->
            <div class="extension-config-form">
              <template v-if="extensionConfigFields && extensionConfigFields.length > 0">
                <el-row :gutter="20" v-for="(row, rowIndex) in configFieldRows" :key="rowIndex">
                  <el-col
                    v-for="field in row"
                    :key="field.name"
                    :span="field.span || 12"
                  >
                    <el-form-item
                      :label="field.label"
                      :prop="`config.${field.name}`"
                      :rules="field.rules"
                    >
                      <!-- 文本输入 -->
                      <el-input
                        v-if="field.type === 'text' || field.type === 'string'"
                        v-model="configValues.config[field.name]"
                        :placeholder="field.placeholder"
                        :disabled="field.disabled"
                        clearable
                      />

                      <!-- 数字输入 -->
                      <el-input-number
                        v-else-if="field.type === 'number' || field.type === 'integer'"
                        v-model="configValues.config[field.name]"
                        :min="field.min"
                        :max="field.max"
                        :step="field.step || 1"
                        :disabled="field.disabled"
                        style="width: 100%"
                      />

                      <!-- 密码输入 -->
                      <el-input
                        v-else-if="field.type === 'password'"
                        v-model="configValues.config[field.name]"
                        type="password"
                        :placeholder="field.placeholder"
                        :disabled="field.disabled"
                        show-password
                        clearable
                      />

                      <!-- 多行文本 -->
                      <el-input
                        v-else-if="field.type === 'textarea'"
                        v-model="configValues.config[field.name]"
                        type="textarea"
                        :rows="field.rows || 3"
                        :placeholder="field.placeholder"
                        :disabled="field.disabled"
                        show-word-limit
                        :maxlength="field.maxlength"
                      />

                      <!-- 选择框 -->
                      <el-select
                        v-else-if="field.type === 'select'"
                        v-model="configValues.config[field.name]"
                        :placeholder="field.placeholder"
                        :disabled="field.disabled"
                        style="width: 100%"
                        clearable
                      >
                        <el-option
                          v-for="option in field.options"
                          :key="option.value"
                          :label="option.label"
                          :value="option.value"
                        />
                      </el-select>

                      <!-- 开关 -->
                      <el-switch
                        v-else-if="field.type === 'boolean' || field.type === 'switch'"
                        v-model="configValues.config[field.name]"
                        :active-text="field.activeText || '启用'"
                        :inactive-text="field.inactiveText || '禁用'"
                        :disabled="field.disabled"
                      />

                      <!-- 日期选择 -->
                      <el-date-picker
                        v-else-if="field.type === 'date'"
                        v-model="configValues.config[field.name]"
                        type="date"
                        :placeholder="field.placeholder"
                        :disabled="field.disabled"
                        style="width: 100%"
                      />

                      <!-- 时间选择 -->
                      <el-time-picker
                        v-else-if="field.type === 'time'"
                        v-model="configValues.config[field.name]"
                        :placeholder="field.placeholder"
                        :disabled="field.disabled"
                        style="width: 100%"
                      />

                      <!-- 默认文本输入 -->
                      <el-input
                        v-else
                        v-model="configValues.config[field.name]"
                        :placeholder="field.placeholder"
                        :disabled="field.disabled"
                        clearable
                      />

                      <!-- 字段描述 -->
                      <div v-if="field.description" class="field-description">
                        {{ field.description }}
                      </div>
                    </el-form-item>
                  </el-col>
                </el-row>
              </template>

              <!-- 如果没有解析到配置字段，显示原始HTML -->
              <div v-else-if="configFormHtml" v-html="configFormHtml"></div>

              <!-- 没有配置表单 -->
              <el-empty v-else description="该扩展没有配置项" />
            </div>
          </el-card>
        </el-form>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showConfigModal = false">取消</el-button>
          <el-button
            type="primary"
            @click="saveConfig"
            :loading="configSaving"
          >
            <el-icon><Check /></el-icon>
            保存配置
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import {
  getExtension,
  getExtensions,
  createExtension,
  updateExtension,
  deleteExtension,
  getExtensionConfig,
  saveExtensionConfig
} from '@/api/extension';
import Toast from '@/utils/toast'
import { marked } from 'marked'  // 正确导入marked
import {
  Upload,
  Setting,
  Document,
  Tools,
  Check
} from '@element-plus/icons-vue'

export default {
  name: 'ExtensionsView',
  components: {
    Upload,
    Setting,
    Document,
    Tools,
    Check
  },
  data() {
    return {
      extensions: [],
      showInstallModal: false,
      showConfigModal: false,
      extensionFile: null,
      installProgress: 0,
      installing: false,
      currentExtension: null,
      configValues: {},
      configLoading: false,
      configSaving: false,
      configError: null,
      configFormHtml: null,
      extensionDocumentation: null,
      config: null,
      activeDocCollapse: 'module',
      extensionConfigFields: [], // 解析后的配置字段

      // Element Plus 表单数据
      installForm: {
        name: '',
        description: '',
        executionMode: 'manual',
        renderType: 'html',
        showInHome: true,
        file: null
      },

      // 表单验证规则
      installRules: {
        name: [
          { required: true, message: '请输入扩展名称', trigger: 'blur' },
          { min: 2, max: 50, message: '名称长度在 2 到 50 个字符', trigger: 'blur' }
        ],
        executionMode: [
          { required: true, message: '请选择执行模式', trigger: 'change' }
        ],
        renderType: [
          { required: true, message: '请选择渲染类型', trigger: 'change' }
        ],
        file: [
          { required: true, message: '请选择扩展文件', trigger: 'change' }
        ]
      },

      configRules: {
        name: [
          { required: true, message: '请输入扩展名称', trigger: 'blur' }
        ],
        endpoint: [
          { required: true, message: 'API端点不能为空', trigger: 'blur' }
        ]
      }
    }
  },
  computed: {
    compiledMarkdown(markdownContent) {
      return marked(markdownContent);
    },

    canInstall() {
      return this.installForm.file && this.installForm.name
    },

    // 将配置字段按行分组，实现响应式布局
    configFieldRows() {
      if (!this.extensionConfigFields || this.extensionConfigFields.length === 0) {
        return []
      }

      const rows = []
      let currentRow = []
      let currentRowSpan = 0

      for (const field of this.extensionConfigFields) {
        const fieldSpan = field.span || 12

        // 如果当前行放不下这个字段，开始新行
        if (currentRowSpan + fieldSpan > 24) {
          if (currentRow.length > 0) {
            rows.push(currentRow)
          }
          currentRow = [field]
          currentRowSpan = fieldSpan
        } else {
          currentRow.push(field)
          currentRowSpan += fieldSpan
        }
      }

      // 添加最后一行
      if (currentRow.length > 0) {
        rows.push(currentRow)
      }

      return rows
    },
    parsedModuleDoc() {
      return this.extensionDocumentation?.module ? 
        this.compiledMarkdown(this.extensionDocumentation.module) : 
        "无说明"
    },
    parsedExecuteQueryDoc() {
      return this.extensionDocumentation?.functions?.execute_query ? 
        this.compiledMarkdown(this.extensionDocumentation.functions.execute_query) : 
        "无方法说明"
    },
    parsedGetConfigFormDoc() {
      return this.extensionDocumentation?.functions?.get_config_form ? 
        this.compiledMarkdown(this.extensionDocumentation.functions.get_config_form) : 
        "无方法说明"
    },
    parsedGetDefaultConfigDoc() {
      return this.extensionDocumentation?.functions?.get_default_config ? 
        this.compiledMarkdown(this.extensionDocumentation.functions.get_default_config) : 
        "无方法说明"
    }
  },
  created() {
    this.fetchExtensions()
  },
  methods: {
    async fetchExtensions() {
      try {
        const response = await getExtensions()
        this.extensions = response.data
      } catch (error) {
        console.error('获取扩展列表失败', error)
        Toast.error('获取扩展列表失败: ' + (error.response?.data?.detail || error.message))
      }
    },
    
    refreshExtensions() {
      this.fetchExtensions()
    },
    
    handleFileSelect(file) {
      this.installForm.file = file.raw
    },

    handleFileRemove() {
      this.installForm.file = null
    },

    async installExtension() {
      // 验证表单
      if (!this.$refs.installFormRef) return

      try {
        await this.$refs.installFormRef.validate()
      } catch (error) {
        return
      }

      if (!this.installForm.file) {
        this.$message.error('请选择扩展文件')
        return
      }

      try {
        this.installing = true
        this.installProgress = 10

        const formData = new FormData()
        formData.append('file', this.installForm.file)
        formData.append('name', this.installForm.name)
        formData.append('description', this.installForm.description)
        formData.append('execution_mode', this.installForm.executionMode)
        formData.append('render_type', this.installForm.renderType)
        formData.append('show_in_home', this.installForm.showInHome)

        this.installProgress = 50

        await createExtension(formData)

        this.installProgress = 100

        this.$message.success('扩展安装成功')
        this.showInstallModal = false
        this.resetInstallForm()
        this.fetchExtensions()
      } catch (error) {
        console.error('安装扩展失败', error)
        this.$message.error('安装扩展失败: ' + (error.response?.data?.detail || error.message))
      } finally {
        this.installing = false
        this.installProgress = 0
      }
    },

    openInstallModal() {
      this.resetInstallForm()
      this.showInstallModal = true
    },

    resetInstallForm() {
      this.installForm = {
        name: '',
        description: '',
        executionMode: 'manual',
        renderType: 'html',
        showInHome: true,
        file: null
      }
      this.installProgress = 0
      if (this.$refs.uploadRef) {
        this.$refs.uploadRef.clearFiles()
      }
      if (this.$refs.installFormRef) {
        this.$refs.installFormRef.resetFields()
      }
    },
    
    async toggleExtension(extension, field) {
      try {
        await updateExtension(extension.id, {
          [field]: extension[field]
        })
        Toast.success(`扩展已${extension[field] ? '启用' : '禁用'}`)
      } catch (error) {
        console.error('切换扩展状态失败', error)
        extension[field] = !extension[field] // 恢复状态
        Toast.error('切换扩展状态失败: ' + (error.response?.data?.detail || error.message))
      }
    },
    async renderTemplate(template, context){
      return template.replace(/\{\{\s*(.*?)\s*\}\}/g, (match, p1) => {
        const path = p1.split('.');
        let result = context;
        for (const key of path) {
          result = result?.[key];
          if (result === undefined) return ""; // 找不到则返回原模板
        }
        return result ?? match;
      });
    },
    async configureExtension(extension) {
      this.currentExtension = extension
      this.configLoading = true
      this.configError = null
      this.showConfigModal = true
      this.configValues = {}
      this.configFormHtml = null
      this.extensionDocumentation = null
      
      try {
        // 获取扩展详情
        const response = await getExtension(extension.id)
        const extensionData = response.data
        
        // 设置基本配置值
        this.configValues = {
          id: extensionData.id,
          name: extensionData.name,
          description: extensionData.description || '',
          endpoint: extensionData.entry_point,
          return_type: extensionData.render_type || 'html',
          showinindex: extensionData.show_in_home || false,
          enabled: extensionData.enabled || false,
          config: {} // 初始化config对象
        }
        
        // 获取文档信息
        this.extensionDocumentation = extensionData.documentation
        
        // 如果有配置表单，获取配置表单
        if (extensionData.has_config_form) {
          try {
            const configResponse = await getExtensionConfig(extension.id)
            let configFormHtml = configResponse.data.config_form
            const configData = configResponse.data.config || {}
            this.config = configData
            // 处理配置表单中的变量
            if (configData) {
              // 替换所有的 {{config.xxx}} 为实际的配置值
              // configFormHtml = this.replaceConfigVariables(configFormHtml, configData)
              configFormHtml =await this.renderTemplate(configFormHtml, { config: this.config })
            }
            console.log(this.config)
            console.log(configFormHtml)
            this.configFormHtml = configFormHtml

            // 解析配置表单HTML，提取字段信息
            this.parseConfigFields(configFormHtml, configData)
          } catch (error) {
            console.error('获取配置表单失败', error)
            this.configFormHtml = `
              <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                加载扩展配置表单失败: ${error.message}
              </div>
            `
          }
        }
      } catch (error) {
        console.error('获取扩展配置失败', error)
        this.configError = '获取扩展配置失败: ' + (error.response?.data?.detail || error.message)
      } finally {
        this.configLoading = false
      }
    },
    
    async saveConfig() {
      if (!this.currentExtension) return

      // 验证表单
      if (this.$refs.configFormRef) {
        try {
          await this.$refs.configFormRef.validate()
        } catch (error) {
          return
        }
      }

      try {
        this.configSaving = true

        // 准备保存的数据
        const data = {
          id: this.configValues.id,
          name: this.configValues.name,
          description: this.configValues.description,
          endpoint: this.configValues.endpoint,
          return_type: this.configValues.return_type,
          showinindex: this.configValues.showinindex,
          enabled: this.configValues.enabled
        }

        // 添加扩展配置数据
        if (this.configValues.config && Object.keys(this.configValues.config).length > 0) {
          data.config = this.configValues.config
        }

        // console.log('保存配置数据:', data)

        await updateExtension(this.currentExtension.id, data)

        this.$message.success('配置保存成功')
        this.showConfigModal = false
        this.resetConfigModal()
        this.fetchExtensions()
      } catch (error) {
        console.error('保存扩展配置失败', error)
        this.$message.error('保存扩展配置失败: ' + (error.response?.data?.detail || error.message))
      } finally {
        this.configSaving = false
      }
    },
    resetConfigModal() {
      this.currentExtension = null
      this.configValues = {}
      this.configFormHtml = null
      this.extensionDocumentation = null
      this.configError = null
      this.activeDocCollapse = 'module'
      this.extensionConfigFields = []
    },

    // 解析配置表单HTML，提取字段信息
    parseConfigFields(configFormHtml, configData) {
      this.extensionConfigFields = []

      if (!configFormHtml) return

      try {
        // 创建临时DOM元素来解析HTML
        const tempDiv = document.createElement('div')
        tempDiv.innerHTML = configFormHtml

        // 查找所有表单字段
        const inputs = tempDiv.querySelectorAll('input, select, textarea')
        const fields = []

        inputs.forEach(input => {
          const field = this.extractFieldInfo(input, configData)
          if (field) {
            fields.push(field)
          }
        })

        this.extensionConfigFields = fields

        // 初始化配置值
        if (!this.configValues.config) {
          this.configValues.config = {}
        }

        // 设置配置值，优先使用后端返回的配置数据
        fields.forEach(field => {
          // 优先使用后端配置数据，其次使用默认值
          const configValue = configData[field.name] !== undefined ? configData[field.name] : field.defaultValue
          this.configValues.config[field.name] = configValue || ''
        })

        console.log('解析到的配置字段:', fields)
        console.log('设置的配置值:', this.configValues.config)
      } catch (error) {
        console.error('解析配置字段失败:', error)
      }
    },

    // 从HTML元素提取字段信息
    extractFieldInfo(element, configData) {
      const name = element.name || element.id
      if (!name || !name.startsWith('config.')) return null

      const fieldName = name.replace('config.', '')
      const label = this.getFieldLabel(element)
      const type = this.getFieldType(element)

      const field = {
        name: fieldName,
        label: label || fieldName,
        type: type,
        placeholder: element.placeholder || '',
        disabled: element.disabled || false,
        required: element.required || false,
        defaultValue: configData[fieldName] || element.value || '',
        span: this.getFieldSpan(type)
      }

      // 添加特定类型的属性
      if (type === 'number' || type === 'integer') {
        field.min = element.min ? parseInt(element.min) : undefined
        field.max = element.max ? parseInt(element.max) : undefined
        field.step = element.step ? parseFloat(element.step) : 1
      }

      if (type === 'textarea') {
        field.rows = element.rows || 3
        field.maxlength = element.maxLength || undefined
      }

      if (type === 'select') {
        field.options = this.getSelectOptions(element)
      }

      if (type === 'boolean' || type === 'switch') {
        field.activeText = element.getAttribute('data-active-text') || '启用'
        field.inactiveText = element.getAttribute('data-inactive-text') || '禁用'
      }

      // 添加描述信息
      const description = this.getFieldDescription(element)
      if (description) {
        field.description = description
      }

      // 添加验证规则
      field.rules = this.getFieldRules(field)

      return field
    },

    // 获取字段标签
    getFieldLabel(element) {
      // 查找关联的label
      const id = element.id
      if (id) {
        const label = document.querySelector(`label[for="${id}"]`)
        if (label) return label.textContent.trim()
      }

      // 查找父级的label
      const parent = element.closest('.form-group, .field-group, .el-form-item')
      if (parent) {
        const label = parent.querySelector('label')
        if (label) return label.textContent.trim()
      }

      return element.getAttribute('data-label') || ''
    },

    // 获取字段类型
    getFieldType(element) {
      const tagName = element.tagName.toLowerCase()

      if (tagName === 'select') return 'select'
      if (tagName === 'textarea') return 'textarea'

      if (tagName === 'input') {
        const type = element.type.toLowerCase()
        if (type === 'checkbox') return 'boolean'
        if (type === 'number') return 'number'
        if (type === 'password') return 'password'
        if (type === 'date') return 'date'
        if (type === 'time') return 'time'
        return 'text'
      }

      return 'text'
    },

    // 获取字段占用的列数
    getFieldSpan(type) {
      switch (type) {
        case 'textarea':
          return 24 // 全宽
        case 'boolean':
        case 'switch':
          return 8  // 1/3宽
        default:
          return 12 // 半宽
      }
    },

    // 获取选择框选项
    getSelectOptions(selectElement) {
      const options = []
      const optionElements = selectElement.querySelectorAll('option')

      optionElements.forEach(option => {
        if (option.value) {
          options.push({
            label: option.textContent.trim(),
            value: option.value
          })
        }
      })

      return options
    },

    // 获取字段描述
    getFieldDescription(element) {
      // 查找help文本
      const helpText = element.getAttribute('data-help') ||
                     element.getAttribute('title') ||
                     element.getAttribute('data-description')

      if (helpText) return helpText

      // 查找相邻的help元素
      const parent = element.closest('.form-group, .field-group')
      if (parent) {
        const help = parent.querySelector('.help-text, .form-text, .field-help')
        if (help) return help.textContent.trim()
      }

      return ''
    },

    // 获取字段验证规则
    getFieldRules(field) {
      const rules = []

      if (field.required) {
        rules.push({
          required: true,
          message: `请输入${field.label}`,
          trigger: field.type === 'select' ? 'change' : 'blur'
        })
      }

      if (field.type === 'number' || field.type === 'integer') {
        rules.push({
          type: 'number',
          message: `${field.label}必须是数字`,
          trigger: 'blur'
        })
      }

      return rules
    },
    
    async uninstallExtension(extension) {
      if (!confirm(`确定要卸载扩展 ${extension.name} 吗？这将删除所有相关数据。`)) {
        return
      }
      
      try {
        await deleteExtension(extension.id)
        Toast.success('扩展已卸载')
        this.fetchExtensions()
      } catch (error) {
        console.error('卸载扩展失败', error)
        Toast.error('卸载扩展失败: ' + (error.response?.data?.detail || error.message))
      }
    },
    
    formatDate(timestamp) {
      if (!timestamp) return '-'
      
      const date = new Date(timestamp)
      return date.toLocaleString()
    },
    
    // HTML 转义辅助函数
    escapeHtml(unsafe) {
      return unsafe?.toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;") || ''
    },
    replaceConfigVariables(html, configData) {
      if (!html) return '';
      
      return html.replace(/\{\{(config\.([\w\.]+))\}\}/g, (match, p1, p2) => {
        try {
          // 处理嵌套路径，例如 config.api.key
          const path = p2.split('.');
          let value = configData;
          
          for (const key of path) {
            if (value === undefined || value === null) {
              return match; // 如果中间路径不存在，保留原始模板变量
            }
            value = value[key];
          }
          
          // 如果找到值，则返回值；否则返回原始模板变量
          return value !== undefined ? value : match;
        } catch (error) {
          console.error('替换配置变量失败:', error, match);
          return match; // 发生错误时保留原始模板变量
        }
      });
    }
  }
}
</script>

<style scoped>
.extensions-container {
  width: 100%;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 2rem;
}

/* Element Plus 对话框样式优化 */
.config-card {
  margin-bottom: 20px;
}

.config-card .card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #409eff;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.doc-content {
  background-color: #f5f7fa;
  padding: 16px;
  border-radius: 6px;
  border-left: 4px solid #409eff;
}

.methods-doc {
  margin-top: 10px;
}

.extension-config-form {
  max-height: 400px;
  overflow-y: auto;
  padding: 10px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  background-color: #fafafa;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.field-description {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

h1 {
  margin-bottom: 2rem;
  color: #2c3e50;
}

.extensions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.extension-card {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.extension-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.extension-card.disabled {
  opacity: 0.6;
}

.extension-header {
  padding: 1rem;
  background-color: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.extension-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #2c3e50;
}

.extension-version {
  font-size: 0.875rem;
  color: #6c757d;
  background-color: #e9ecef;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.extension-body {
  padding: 1rem;
}

.extension-body p {
  margin-bottom: 1rem;
}

.extension-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.875rem;
  color: #6c757d;
  margin-bottom: 1rem;
}

.extension-features {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.feature-badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  background-color: #e9ecef;
  color: #6c757d;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.feature-badge.active {
  background-color: #28a745;
  color: white;
}

.extension-footer {
  padding: 1rem;
  border-top: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.extension-actions {
  display: flex;
  gap: 0.5rem;
}

.modal {
  position: fixed;
  top: 5%;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-dialog {
  width: 100%;
  max-width: 500px;
  margin: 1.75rem auto;
}

.modal-dialog.modal-lg {
  max-width: 800px;
}

.modal-content {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e9ecef;
}

.modal-title {
  margin: 0;
}

.btn-close {
  background: transparent;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
}

.modal-body {
  padding: 1rem;
}

.modal-footer {
  padding: 1rem;
  border-top: 1px solid #e9ecef;
  display: flex;
  justify-content: flex-end;
}

.install-progress {
  margin-top: 1rem;
}

.progress {
  height: 10px;
  border-radius: 5px;
  overflow: hidden;
}
</style>