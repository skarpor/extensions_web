import axios from '@/utils/axios'

// ==================== 邮件相关API ====================

/**
 * 发送邮件
 * @param {Object} emailData - 邮件数据
 * @param {Array} emailData.to_emails - 收件人邮箱列表
 * @param {string} emailData.subject - 邮件主题
 * @param {string} emailData.content - 邮件内容
 * @param {string} emailData.content_type - 内容类型 ('plain' 或 'html')
 * @param {Array} emailData.cc_emails - 抄送邮箱列表（可选）
 * @param {Array} emailData.bcc_emails - 密送邮箱列表（可选）
 * @returns {Promise} 发送结果
 */
export const sendEmailApi = async (emailData) => {
  return await axios.post('/api/email/send', emailData)
}

/**
 * 发送通知邮件
 * @param {Object} notificationData - 通知数据
 * @param {Array} notificationData.to_emails - 收件人邮箱列表
 * @param {string} notificationData.title - 通知标题
 * @param {string} notificationData.message - 通知消息
 * @returns {Promise} 发送结果
 */
export const sendNotificationEmailApi = async (notificationData) => {
  return await axios.post('/api/email/send-notification', notificationData)
}

/**
 * 发送带附件的邮件
 * @param {Object} emailData - 邮件数据
 * @param {string} emailData.to_emails - 收件人邮箱（逗号分隔）
 * @param {string} emailData.subject - 邮件主题
 * @param {string} emailData.content - 邮件内容
 * @param {string} emailData.content_type - 内容类型
 * @param {Array} files - 附件文件列表
 * @returns {Promise} 发送结果
 */
export const sendEmailWithAttachmentsApi = async (emailData, files) => {
  const formData = new FormData()
  
  // 添加邮件数据
  formData.append('to_emails', emailData.to_emails)
  formData.append('subject', emailData.subject)
  formData.append('content', emailData.content)
  formData.append('content_type', emailData.content_type || 'plain')
  
  // 添加附件
  files.forEach(file => {
    formData.append('files', file)
  })
  
  return await axios.post('/api/email/send-with-attachments', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取邮件配置信息（仅超级管理员）
 * @returns {Promise} 邮件配置信息
 */
export const getEmailConfigApi = async () => {
  return await axios.get('/api/email/config')
}

/**
 * 测试邮件服务器连接（仅超级管理员）
 * @returns {Promise} 测试结果
 */
export const testEmailConnectionApi = async () => {
  return await axios.post('/api/email/test-connection')
}

/**
 * 发送测试邮件（仅超级管理员）
 * @param {string} testEmail - 测试邮箱地址
 * @returns {Promise} 发送结果
 */
export const sendTestEmailApi = async (testEmail) => {
  return await axios.post('/api/email/send-test', null, {
    params: { test_email: testEmail }
  })
}

// 默认导出所有API函数
export default {
  sendEmailApi,
  sendNotificationEmailApi,
  sendEmailWithAttachmentsApi,
  getEmailConfigApi,
  testEmailConnectionApi,
  sendTestEmailApi
}
