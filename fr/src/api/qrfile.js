// 二维码文件处理API
import axios from '@/utils/axios'
axios.defaults.timeout = 300000 // 超时时间设置为5分钟
// 序列化Excel区域
export const serializeExcel = async (file, region, sheet = '') => {
  const formData = new FormData()
  formData.append('excel_file', file)
  formData.append('region', region)
  if (sheet) {
    formData.append('sheet_name', sheet)
  }
  return await axios.post('/api/qrfile/serialize-excel', formData)
}

// 获取Excel文件的sheet列表
export const getExcelSheets = async (file) => {
  const formData = new FormData()
  formData.append('excel_file', file)
  return await axios.post('/api/qrfile/get-excel-sheets', formData)
}

// 序列化文件
export const serializeFile = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return await axios.post('/api/qrfile/serialize-file', formData,{
    timeout: 300000 // 超时时间设置为5分钟
    })
}

// 生成二维码
export const generateQRCodes = async (sessionId, chunkSize = 1800) => {
  const formData = new FormData()
  formData.append('session_id', sessionId)
  formData.append('chunk_size', chunkSize)
  return await axios.post('/api/qrfile/generate-qrcodes', formData,{
    timeout: 300000 // 超时时间设置为5分钟
    })
}

// 扫描恢复文件
export const scanRestore = async (files) => {
  const formData = new FormData()
  files.forEach(file => {
    formData.append('files', file)
  })
  return await axios.post('/api/qrfile/scan-restore', formData,{
    timeout: 300000 // 超时时间设置为5分钟
    })
}

// 视频扫描恢复
export const scanVideo = async (videoFile) => {
  const formData = new FormData()
  formData.append('video_file', videoFile)
  return await axios.post('/api/qrfile/scan-video', formData,{
    timeout: 300000 // 超时时间设置为5分钟
    })
}

// 获取二维码图片URL
export const getQRCodeUrl =async (sessionId, name) => {
  return await axios.get(
    `/api/qrfile/qrcode/${sessionId}/${name}`)
}

// 获取下载链接
export const getDownloadUrl =async (filename) => {
  return await axios.get(
     `/api/qrfile/download/${filename}`)
}

// 从文本内容恢复文件
export const restoreFromText = async (textData) => {
  return await axios.post('/api/qrfile/restore-from-text', 
    textData
  )
}

// 获取二维码文件列表
export const getQRFiles = async (skip = 0, limit = 10) => {
  return await axios.get(`/api/qrfile/files?skip=${skip}&limit=${limit}`)
}

// 删除二维码文件
export const deleteQRFile = async (fileId) => {
  return await axios.delete(`/api/qrfile/files/${fileId}`)
}

// 获取文件统计信息
export const getFileStats = async () => {
  return await axios.get('/api/qrfile/file-stats')
}

// 清理旧文件（管理员专用）
export const cleanOldFiles = async (days = 30) => {
  return await axios.post('/api/qrfile/clean-old-files', { days })
} 

// 根据session_id获取二维码文件列表
export const getQRFilesBySessionIdApi = async (sessionId) => {
  return await axios.get(`/api/qrfile/files/${sessionId}`)
}

