//dashboard
import axios from '@/utils/axios'

// 获取dashboard数据
export const getDashboardData = async () => {
  const response = await axios.get('/api/dashboard/stats')
  return response.data
}

// 获取系统信息
export const getSystemInfo = async () => {
  const response = await axios.get('/api/dashboard/system')
  return response.data
}

// 最近活动
export const getRecentActivity = async () => {
  const response = await axios.get('/api/dashboard/activity')
  return response.data
}
