<template>
  <div class="email-sender">
    <div class="page-header">
      <h1>
        <el-icon><Message /></el-icon>
        邮件发送
      </h1>
      <p class="page-description">发送邮件和通知消息</p>
    </div>

    <el-tabs v-model="activeTab" class="email-tabs">
      <!-- 普通邮件 -->
      <el-tab-pane label="发送邮件" name="email">
        <el-card class="email-card">
          <template #header>
            <div class="card-header">
              <span>撰写邮件</span>
              <el-button type="primary" @click="sendEmail" :loading="sending">
                <el-icon><Promotion /></el-icon>
                发送邮件
              </el-button>
            </div>
          </template>

          <el-form :model="emailForm" :rules="emailRules" ref="emailFormRef" label-width="100px">
            <el-form-item label="收件人" prop="to_emails" required>
              <el-select
                v-model="emailForm.to_emails"
                multiple
                filterable
                allow-create
                placeholder="输入邮箱地址，按回车添加"
                style="width: 100%"
              >
                <el-option
                  v-for="email in commonEmails"
                  :key="email"
                  :label="email"
                  :value="email"
                />
              </el-select>
              <div class="form-help">支持多个邮箱地址，可以直接输入新邮箱</div>
            </el-form-item>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="抄送" prop="cc_emails">
                  <el-select
                    v-model="emailForm.cc_emails"
                    multiple
                    filterable
                    allow-create
                    placeholder="抄送邮箱（可选）"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="email in commonEmails"
                      :key="email"
                      :label="email"
                      :value="email"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="密送" prop="bcc_emails">
                  <el-select
                    v-model="emailForm.bcc_emails"
                    multiple
                    filterable
                    allow-create
                    placeholder="密送邮箱（可选）"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="email in commonEmails"
                      :key="email"
                      :label="email"
                      :value="email"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="邮件主题" prop="subject" required>
              <el-input
                v-model="emailForm.subject"
                placeholder="请输入邮件主题"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="内容类型" prop="content_type">
              <el-radio-group v-model="emailForm.content_type">
                <el-radio label="plain">纯文本</el-radio>
                <el-radio label="html">HTML格式</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="邮件内容" prop="content" required>
              <el-input
                v-if="emailForm.content_type === 'plain'"
                v-model="emailForm.content"
                type="textarea"
                :rows="10"
                placeholder="请输入邮件内容"
                maxlength="10000"
                show-word-limit
              />
              <div v-else class="html-editor">
                <el-input
                  v-model="emailForm.content"
                  type="textarea"
                  :rows="10"
                  placeholder="请输入HTML格式的邮件内容"
                  maxlength="10000"
                  show-word-limit
                />
                <div class="html-preview" v-if="emailForm.content">
                  <h4>预览效果：</h4>
                  <div class="preview-content" v-html="emailForm.content"></div>
                </div>
              </div>
            </el-form-item>

            <el-form-item label="附件">
              <el-upload
                ref="uploadRef"
                :file-list="attachments"
                :auto-upload="false"
                multiple
                :on-change="handleFileChange"
                :on-remove="handleFileRemove"
                action="#"
              >
                <el-button type="primary">
                  <el-icon><Upload /></el-icon>
                  选择附件
                </el-button>
                <template #tip>
                  <div class="el-upload__tip">
                    支持多个文件，单个文件不超过10MB
                  </div>
                </template>
              </el-upload>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 通知邮件 -->
      <el-tab-pane label="发送通知" name="notification">
        <el-card class="email-card">
          <template #header>
            <div class="card-header">
              <span>发送通知邮件</span>
              <el-button type="success" @click="sendNotification" :loading="sending">
                <el-icon><Bell /></el-icon>
                发送通知
              </el-button>
            </div>
          </template>

          <el-form :model="notificationForm" :rules="notificationRules" ref="notificationFormRef" label-width="100px">
            <el-form-item label="收件人" prop="to_emails" required>
              <el-select
                v-model="notificationForm.to_emails"
                multiple
                filterable
                allow-create
                placeholder="输入邮箱地址，按回车添加"
                style="width: 100%"
              >
                <el-option
                  v-for="email in commonEmails"
                  :key="email"
                  :label="email"
                  :value="email"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="通知标题" prop="title" required>
              <el-input
                v-model="notificationForm.title"
                placeholder="请输入通知标题"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="通知内容" prop="message" required>
              <el-input
                v-model="notificationForm.message"
                type="textarea"
                :rows="8"
                placeholder="请输入通知内容，支持HTML格式"
                maxlength="5000"
                show-word-limit
              />
              <div class="form-help">通知邮件会自动使用美观的HTML模板</div>
            </el-form-item>

            <el-form-item label="预览">
              <div class="notification-preview">
                <h4>{{ notificationForm.title || '通知标题' }}</h4>
                <div class="preview-content" v-html="notificationForm.message || '通知内容'"></div>
              </div>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 邮件配置 -->
      <el-tab-pane label="邮件配置" name="config" v-if="isAdmin">
        <el-card class="email-card">
          <template #header>
            <div class="card-header">
              <span>邮件服务配置</span>
              <div>
                <el-button @click="testConnection" :loading="testing">
                  <el-icon><Connection /></el-icon>
                  测试连接
                </el-button>
                <el-button type="warning" @click="showTestEmailDialog">
                  <el-icon><Message /></el-icon>
                  发送测试邮件
                </el-button>
              </div>
            </div>
          </template>

          <el-descriptions :column="2" border v-loading="configLoading">
            <el-descriptions-item label="SMTP服务器">{{ emailConfig.smtp_host || '未配置' }}</el-descriptions-item>
            <el-descriptions-item label="SMTP端口">{{ emailConfig.smtp_port || '未配置' }}</el-descriptions-item>
            <el-descriptions-item label="SMTP用户">{{ emailConfig.smtp_user || '未配置' }}</el-descriptions-item>
            <el-descriptions-item label="发件人地址">{{ emailConfig.smtp_from || '未配置' }}</el-descriptions-item>
            <el-descriptions-item label="使用TLS">
              <el-tag :type="emailConfig.use_tls ? 'success' : 'danger'">
                {{ emailConfig.use_tls ? '是' : '否' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="使用SSL">
              <el-tag :type="emailConfig.use_ssl ? 'success' : 'danger'">
                {{ emailConfig.use_ssl ? '是' : '否' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="配置状态" :span="2">
              <el-tag :type="emailConfig.is_configured ? 'success' : 'warning'">
                {{ emailConfig.is_configured ? '已配置' : '未完整配置' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>

          <div class="config-help">
            <el-alert
              title="配置说明"
              type="info"
              :closable="false"
              show-icon
            >
              <p>邮件服务配置需要在环境变量中设置：</p>
              <ul>
                <li>SMTP_HOST: SMTP服务器地址</li>
                <li>SMTP_PORT: SMTP端口（通常为587或465）</li>
                <li>SMTP_USER: SMTP用户名</li>
                <li>SMTP_PASSWORD: SMTP密码</li>
                <li>SMTP_FROM: 发件人邮箱地址</li>
              </ul>
            </el-alert>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 测试邮件对话框 -->
    <el-dialog v-model="testEmailDialogVisible" title="发送测试邮件" width="400px">
      <el-form :model="testEmailForm" ref="testEmailFormRef">
        <el-form-item label="测试邮箱" prop="email" required>
          <el-input
            v-model="testEmailForm.email"
            placeholder="请输入测试邮箱地址"
            type="email"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="testEmailDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="sendTestEmail" :loading="testingSend">
          发送测试邮件
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Message,
  Promotion,
  Bell,
  Upload,
  Connection,
  Delete,
  Plus
} from '@element-plus/icons-vue'
import {
  sendEmailApi,
  sendNotificationEmailApi,
  sendEmailWithAttachmentsApi,
  getEmailConfigApi,
  testEmailConnectionApi,
  sendTestEmailApi
} from '@/api/email'
import { useUserStore } from '@/stores/user'

// 用户信息
const userStore = useUserStore()
const isAdmin = computed(() => userStore.user?.is_superuser || false)

// 标签页
const activeTab = ref('email')

// 加载状态
const sending = ref(false)
const testing = ref(false)
const testingSend = ref(false)
const configLoading = ref(false)

// 邮件表单
const emailForm = reactive({
  to_emails: [],
  cc_emails: [],
  bcc_emails: [],
  subject: '',
  content: '',
  content_type: 'plain'
})

// 通知表单
const notificationForm = reactive({
  to_emails: [],
  title: '',
  message: ''
})

// 测试邮件表单
const testEmailForm = reactive({
  email: ''
})

// 邮件配置
const emailConfig = ref({})

// 附件
const attachments = ref([])

// 常用邮箱
const commonEmails = ref([
  'admin@example.com',
  'support@example.com',
  'noreply@example.com'
])

// 对话框
const testEmailDialogVisible = ref(false)

// 表单引用
const emailFormRef = ref()
const notificationFormRef = ref()
const testEmailFormRef = ref()
const uploadRef = ref()

// 表单验证规则
const emailRules = {
  to_emails: [
    { required: true, message: '请选择收件人', trigger: 'change' }
  ],
  subject: [
    { required: true, message: '请输入邮件主题', trigger: 'blur' },
    { min: 1, max: 200, message: '主题长度在 1 到 200 个字符', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '请输入邮件内容', trigger: 'blur' }
  ]
}

const notificationRules = {
  to_emails: [
    { required: true, message: '请选择收件人', trigger: 'change' }
  ],
  title: [
    { required: true, message: '请输入通知标题', trigger: 'blur' },
    { min: 1, max: 200, message: '标题长度在 1 到 200 个字符', trigger: 'blur' }
  ],
  message: [
    { required: true, message: '请输入通知内容', trigger: 'blur' }
  ]
}

// 发送邮件
const sendEmail = async () => {
  try {
    await emailFormRef.value.validate()
    sending.value = true

    if (attachments.value.length > 0) {
      // 发送带附件的邮件
      const emailData = {
        to_emails: emailForm.to_emails.join(','),
        subject: emailForm.subject,
        content: emailForm.content,
        content_type: emailForm.content_type
      }

      const files = attachments.value.map(item => item.raw)
      const response = await sendEmailWithAttachmentsApi(emailData, files)

      if (response.data.success) {
        ElMessage.success('带附件邮件发送成功')
        resetEmailForm()
      } else {
        ElMessage.error(response.data.message || '邮件发送失败')
      }
    } else {
      // 发送普通邮件
      const response = await sendEmailApi({
        to_emails: emailForm.to_emails,
        cc_emails: emailForm.cc_emails.length > 0 ? emailForm.cc_emails : undefined,
        bcc_emails: emailForm.bcc_emails.length > 0 ? emailForm.bcc_emails : undefined,
        subject: emailForm.subject,
        content: emailForm.content,
        content_type: emailForm.content_type
      })

      if (response.data.success) {
        ElMessage.success('邮件发送成功')
        resetEmailForm()
      } else {
        ElMessage.error(response.data.message || '邮件发送失败')
      }
    }
  } catch (error) {
    console.error('发送邮件失败:', error)
    ElMessage.error('发送邮件失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    sending.value = false
  }
}

// 发送通知
const sendNotification = async () => {
  try {
    await notificationFormRef.value.validate()
    sending.value = true

    const response = await sendNotificationEmailApi({
      to_emails: notificationForm.to_emails,
      title: notificationForm.title,
      message: notificationForm.message
    })

    if (response.data.success) {
      ElMessage.success('通知邮件发送成功')
      resetNotificationForm()
    } else {
      ElMessage.error(response.data.message || '通知邮件发送失败')
    }
  } catch (error) {
    console.error('发送通知邮件失败:', error)
    ElMessage.error('发送通知邮件失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    sending.value = false
  }
}

// 重置邮件表单
const resetEmailForm = () => {
  Object.assign(emailForm, {
    to_emails: [],
    cc_emails: [],
    bcc_emails: [],
    subject: '',
    content: '',
    content_type: 'plain'
  })
  attachments.value = []
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

// 重置通知表单
const resetNotificationForm = () => {
  Object.assign(notificationForm, {
    to_emails: [],
    title: '',
    message: ''
  })
}

// 处理文件变化
const handleFileChange = (file, fileList) => {
  attachments.value = fileList
}

// 处理文件移除
const handleFileRemove = (file, fileList) => {
  attachments.value = fileList
}

// 加载邮件配置
const loadEmailConfig = async () => {
  if (!isAdmin.value) return

  try {
    configLoading.value = true
    const response = await getEmailConfigApi()
    emailConfig.value = response.data
  } catch (error) {
    console.error('加载邮件配置失败:', error)
    ElMessage.error('加载邮件配置失败')
  } finally {
    configLoading.value = false
  }
}

// 测试连接
const testConnection = async () => {
  try {
    testing.value = true
    const response = await testEmailConnectionApi()

    if (response.data.success) {
      ElMessage.success('邮件服务器连接测试成功')
    } else {
      ElMessage.error(response.data.message || '邮件服务器连接测试失败')
    }
  } catch (error) {
    console.error('测试邮件连接失败:', error)
    ElMessage.error('测试邮件连接失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    testing.value = false
  }
}

// 显示测试邮件对话框
const showTestEmailDialog = () => {
  testEmailForm.email = userStore.user?.email || ''
  testEmailDialogVisible.value = true
}

// 发送测试邮件
const sendTestEmail = async () => {
  if (!testEmailForm.email) {
    ElMessage.error('请输入测试邮箱地址')
    return
  }

  try {
    testingSend.value = true
    const response = await sendTestEmailApi(testEmailForm.email)

    if (response.data.success) {
      ElMessage.success('测试邮件发送成功')
      testEmailDialogVisible.value = false
    } else {
      ElMessage.error(response.data.message || '测试邮件发送失败')
    }
  } catch (error) {
    console.error('发送测试邮件失败:', error)
    ElMessage.error('发送测试邮件失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    testingSend.value = false
  }
}

// 组件挂载
onMounted(() => {
  loadEmailConfig()
})
</script>

<style scoped>
.email-sender {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
  text-align: center;
}

.page-header h1 {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #2c3e50;
  margin-bottom: 10px;
}

.page-description {
  color: #7f8c8d;
  font-size: 16px;
  margin: 0;
}

.email-tabs {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.email-card {
  border: none;
  box-shadow: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.form-help {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.html-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.html-preview {
  border-top: 1px solid #ebeef5;
  padding: 15px;
  background: #fafafa;
}

.html-preview h4 {
  margin: 0 0 10px 0;
  color: #606266;
  font-size: 14px;
}

.preview-content {
  background: white;
  padding: 15px;
  border-radius: 4px;
  border: 1px solid #ebeef5;
  min-height: 100px;
}

.notification-preview {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 6px;
  border: 1px solid #e9ecef;
  max-width: 600px;
}

.notification-preview h4 {
  color: #2c3e50;
  border-bottom: 2px solid #3498db;
  padding-bottom: 10px;
  margin: 0 0 15px 0;
}

.config-help {
  margin-top: 20px;
}

.config-help ul {
  margin: 10px 0 0 20px;
  padding: 0;
}

.config-help li {
  margin-bottom: 5px;
  color: #606266;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .email-sender {
    padding: 10px;
  }

  .card-header {
    flex-direction: column;
    gap: 10px;
    align-items: stretch;
  }

  .notification-preview {
    max-width: 100%;
  }
}

/* 上传组件样式 */
:deep(.el-upload-list) {
  margin-top: 10px;
}

:deep(.el-upload__tip) {
  margin-top: 5px;
}

/* 标签页样式 */
:deep(.el-tabs__header) {
  margin-bottom: 0;
}

:deep(.el-tabs__content) {
  padding: 20px;
}

/* 描述列表样式 */
:deep(.el-descriptions__body .el-descriptions__table) {
  border-radius: 6px;
}
</style>
