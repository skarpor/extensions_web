import axios from '@/utils/axios' // 或其他 HTTP 客户端


// 登录接口
export const loginApi = async (credentials) => {
  try {
    const response = await axios.post('/api/auth/login', credentials)
    // 如果登录成功，将token存储到localStorage
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token)
    }
    return response.data
  } catch (error) {
    console.error('登录失败:', error.response?.data || error.message)
    throw new Error(error.response?.data?.detail || '登录失败')
  }
}

// 登出接口
export const logoutApi = async () => {
  try {
    await axios.post('/api/auth/logout')
    localStorage.removeItem('token')
  } catch (error) {
    // 即使登出失败也继续执行，确保前端状态清除
    console.error('登出时发生错误:', error)
    // 删除token
    localStorage.removeItem('token')
  }
}

// 刷新 token 接口
export const refreshTokenApi = async (token) => {
  try {
    const response = await axios.post('/api/auth/refresh', { token })
    return {
      newToken: response.data.access_token
    }
  } catch (error) {
    throw new Error('会话已过期，请重新登录')
  }
}

// 获取用户信息接口
export const fetchUserInfo = async () => {
  try {
    const response = await axios.get('/api/auth/me')
    return response.data
  } catch (error) {
    console.error('获取用户信息失败:', error.response?.data || error.message)
    throw new Error('获取用户信息失败')
  }
}

// 注册接口
export const registerApi = async (data) => {
  try {
    const response = await axios.post('/api/auth/register', data)
    return response.data
  } catch (error) {
    console.error('注册失败:', error.response?.data || error.message)
    throw new Error(error.response?.data?.detail || '注册失败')
  }
}

// 更新用户信息接口
export const updateUserInfo = async (data) => {
  try {
    const response = await axios.put('/api/auth/me', data)
    return response.data
  } catch (error) {
    console.error('更新用户信息失败:', error.response?.data || error.message)
    throw new Error('更新用户信息失败')
  }
}

// 更新密码接口
export const updatePassword = async (data) => {
  try {
    const response = await axios.put('/api/auth/me/password', data)
    return response.data
  } catch (error) {
    console.error('更新密码失败:', error.response?.data || error.message)
    throw new Error('更新密码失败')
  }
}

// 获取用户列表接口