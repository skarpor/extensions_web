//axios的配置文件
import axios from 'axios'
import Toast from '@/utils/toast'
const host=import.meta.env.VITE_HOST
const port=import.meta.env.VITE_PORT
// 配置axios
axios.defaults.baseURL = `http://${host}:${port}`
axios.defaults.timeout = 15000  // 增加超时时间
//axios.defaults.withCredentials = true  // 允许跨域请求发送cookies

// 添加请求拦截器，从localStorage中获取token
axios.interceptors.request.use(
  function (config) {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // 确保Content-Type正确设置
    if (!config.headers['Content-Type'] && config.data) {
      config.headers['Content-Type'] = 'application/json'
    }
    return config
  },
  function (error) {
    return Promise.reject(error)
  }
)

//响应拦截器
axios.interceptors.response.use(
  function (response) {
    if (response.status === 200 || response.status === 201) {
      return response
    } else {
      return Promise.reject(response.data)
    }
  },
  function (error) {
    // 更完善的错误处理
    if (error.response) {
      // 服务器响应了，但状态码不在2xx范围内，401错误并且当前页面不是登录页
      if (error.response.status === 401 && window.location.pathname !== '/login') {
        Toast.error('认证失败，请重新登录')
        localStorage.removeItem('token')
        window.location.href = '/login'
      } else if (error.response.status === 403) {
        Toast.error('权限不足，无法访问该资源')
      } else if (error.response.status === 500) {
        Toast.error('服务器内部错误，请稍后再试')
      } else {
        // 尝试显示详细错误信息
        const errorMsg = error.response.data?.detail || error.response.data?.message || '请求失败'
        Toast.error(errorMsg)
      }
    } else if (error.request) {
      // 请求发出了，但没有收到响应
      Toast.error('无法连接到服务器，请检查网络连接')
    } else {
      // 请求配置错误
      Toast.error('请求配置错误: ' + error.message)
    }
    return Promise.reject(error)
  }
)

export default axios