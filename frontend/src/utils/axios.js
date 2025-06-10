//axios的配置文件
import axios from 'axios'


// 配置axios
axios.defaults.baseURL = 'http://localhost:8000'
axios.defaults.timeout = 5000

// 添加请求拦截器，从localStorage中获取token
axios.interceptors.request.use(
  function (config) {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  function (error) {
    return Promise.reject(error)
  }
)
export default axios
