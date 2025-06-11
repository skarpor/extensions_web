import axios from '@/utils/axios' // 或其他 HTTP 客户端


// 登录接口
export const loginApi = async (credentials) => {
  try {
    const response = await axios.post('/api/auth/login', credentials)
    return {
      user: response.data.user,
      token: response.data.access_token
    }
  } catch (error) {
    // 可以根据后端返回的错误码进行更精细的错误处理
    if (error.response) {
      throw new Error(error.response.data.message || '登录失败')
    } else {
      throw new Error('网络错误，请稍后重试')
    }
  }
}

// 登出接口
export const logoutApi = async () => {
  try {
    await axios.post('/auth/logout')
  } catch (error) {
    // 即使登出失败也继续执行，确保前端状态清除
    console.error('登出时发生错误:', error)
  }
}

// 刷新 token 接口
export const refreshTokenApi = async (token) => {
  try {
    const response = await axios.post('/api/auth/refresh', { token })
    return {
      newToken: response.data.token
    }
  } catch (error) {
    throw new Error('会话已过期，请重新登录')
  }
}

// 获取用户信息接口
export const fetchUserInfo = async (token) => {
  try {
    const response = await axios.get('/api/auth/me', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    return response.data.user
  } catch (error) {
    throw new Error('获取用户信息失败')
  }
}