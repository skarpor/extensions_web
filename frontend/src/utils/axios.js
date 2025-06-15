//axios的配置文件
import axios from 'axios'
import Toast from '@/utils/toast'

// 配置axios
axios.defaults.baseURL = 'http://192.168.2.75:8000'
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

//响应拦截器，
// HTTPException(
//   status_code=status.HTTP_401_UNAUTHORIZED,
//   detail="用户名或密码错误",
//   headers={"WWW-Authenticate": "Bearer"},
// ),会触发哪个拦截器

axios.interceptors.response.use(
  function (response) {
    if (response.status === 200) {
      return response
    } else {
      return Promise.reject(response.data)
    }
  },
  function (error) {
    Toast.error(error.response.data.detail)
    if (error.response.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default axios