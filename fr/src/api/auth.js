import axios from '@/utils/axios' // 或其他 HTTP 客户端
import toast from '@/utils/toast'

// 登录接口
export const loginApi = async (credentials) => {
  try {
    const response = await axios.post('/api/auth/login-json', credentials)
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
    toast.error('登出时发生错误:', error)
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
    toast.error('获取用户信息失败:', error.response?.data || error.message)
    throw new Error('获取用户信息失败')
  }
}

// 注册接口
export const registerApi = async (data) => {
  try {
     return await axios.post('/api/auth/register', data)
  } catch (error) {
    toast.error(error.response?.data || error.detail)
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
export const getUsersApi = async () => {
  try {
    const response = await axios.get('/api/auth/users')
    return response.data
  } catch (error) {
    console.error('获取用户列表失败:', error.response?.data || error.message)
    throw new Error('获取用户列表失败')
  }
}

// 以下是新增的权限管理相关API

// 获取所有权限
export const getPermissionsApi = async () => {
  try {
    const response = await axios.get('/api/auth/permissions/all')
    return response.data
  } catch (error) {
    console.error('获取权限列表失败:', error.response?.data || error.message)
    throw new Error('获取权限列表失败')
  }
}

// 权限分组管理接口
export const getPermissionGroupsApi = async () => {
  try {
    const response = await axios.get('/api/auth/permission-groups')
    return response.data
  } catch (error) {
    console.error('获取权限分组失败:', error)
    throw error
  }
}

export const createPermissionGroupApi = async (groupData) => {
  try {
    const response = await axios.post('/api/auth/permission-groups', groupData)
    return response.data
  } catch (error) {
    console.error('创建权限分组失败:', error)
    throw error
  }
}

export const updatePermissionGroupApi = async (groupId, groupData) => {
  try {
    const response = await axios.put(`/api/auth/permission-groups/${groupId}`, groupData)
    return response.data
  } catch (error) {
    console.error('更新权限分组失败:', error)
    throw error
  }
}

export const deletePermissionGroupApi = async (groupId) => {
  try {
    const response = await axios.delete(`/api/auth/permission-groups/${groupId}`)
    return response.data
  } catch (error) {
    console.error('删除权限分组失败:', error)
    throw error
  }
}
// 获取用户权限
export const getUserPermissionsApi = async () => {
  try {
    const response = await axios.get('/api/auth/permissions')
    return response.data
  } catch (error) {
    console.error('获取用户权限失败:', error.response?.data || error.message)
    throw new Error('获取用户权限失败')
  }
}

// 获取权限列表
export const getPermissionsApi1 = async () => {
  try {
    const response = await axios.get('/api/auth/permissions/list')
    return response.data
  } catch (error) {
    console.error('获取权限列表失败:', error.response?.data || error.message)
    throw new Error('获取权限列表失败')
  }
}
// 创建权限
export const createPermissionApi = async (data) => {
  try {
    const response = await axios.post('/api/auth/permissions', data)
    return response.data
  } catch (error) {
    console.error('创建权限失败:', error.response?.data || error.message)
    throw new Error(error.response?.data?.detail || '创建权限失败')
  }
}

// 更新权限
export const updatePermissionApi = async (id, data) => {
  try {
    const response = await axios.put(`/api/auth/permissions/${id}`, data)
    return response.data
  } catch (error) {
    console.error('更新权限失败:', error.response?.data || error.message)
    throw new Error(error.response?.data?.detail || '更新权限失败')
  }
}

// 删除权限
export const deletePermissionApi = async (id) => {
  try {
    const response = await axios.delete(`/api/auth/permissions/${id}`)
    return response.data
  } catch (error) {
    console.error('删除权限失败:', error.response?.data || error.message)
    throw new Error(error.response?.data?.detail || '删除权限失败')
  }
}

// 获取所有角色
export const getRolesApi = async () => {
  try {
    const response = await axios.get('/api/auth/roles')
    return response.data
  } catch (error) {
    console.error('获取角色列表失败:', error.response?.data || error.message)
    throw new Error('获取角色列表失败')
  }
}

// 创建角色
export const createRoleApi = async (data) => {
  try {
    const response = await axios.post('/api/auth/roles', data)
    return response.data
  } catch (error) {
    console.error('创建角色失败:', error.response?.data || error.message)
    throw new Error(error.response?.data?.detail || '创建角色失败')
  }
}

// 更新角色
export const updateRoleApi = async (id, data) => {
  try {
    const response = await axios.put(`/api/auth/roles/${id}`, data)
    return response.data
  } catch (error) {
    console.error('更新角色失败:', error.response?.data || error.message)
    throw new Error(error.response?.data?.detail || '更新角色失败')
  }
}

// 删除角色
export const deleteRoleApi = async (id) => {
  try {
    const response = await axios.delete(`/api/auth/roles/${id}`)
    return response.data
  } catch (error) {
    console.error('删除角色失败:', error.response?.data || error.message)
    throw new Error(error.response?.data?.detail || '删除角色失败')
  }
}

// 获取用户角色
export const getUserRolesApi = async (userId) => {
  try {
    const response = await axios.get(`/api/auth/users/${userId}/roles`)
    return response.data
  } catch (error) {
    console.error('获取用户角色失败:', error.response?.data || error.message)
    throw new Error('获取用户角色失败')
  }
}

// 为用户分配角色
export const assignUserRolesApi = async (data) => {
  try {
    const response = await axios.post('/api/auth/users/assign-roles', data)
    return response.data
  } catch (error) {
    console.error('分配用户角色失败:', error.response?.data || error.message)
    throw new Error(error.response?.data?.detail || '分配用户角色失败')
  }
}