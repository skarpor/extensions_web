import axios from '@/utils/axios.js'

// ==================== 用户管理相关API ====================

/**
 * 获取用户列表
 * @param {number} skip - 跳过的记录数
 * @param {number} limit - 限制返回的记录数
 * @returns {Promise} 用户列表
 */
export const getUsersApi = async (skip = 0, limit = 100) => {
  return await axios.get('/api/users', {
    params: { skip, limit }
  })
}

/**
 * 根据ID获取用户信息
 * @param {number|string} userId - 用户ID，'me'表示当前用户
 * @returns {Promise} 用户信息
 */
export const getUserByIdApi = async (userId) => {
  return await axios.get(`/api/users/${userId}`)
}

/**
 * 获取当前用户信息
 * @returns {Promise} 当前用户信息
 */
export const getCurrentUserApi = async () => {
  return await axios.get('/api/users/me')
}

/**
 * 创建新用户
 * @param {Object} userData - 用户数据
 * @param {string} userData.username - 用户名
 * @param {string} userData.nickname - 昵称
 * @param {string} userData.email - 邮箱
 * @param {string} userData.password - 密码
 * @param {boolean} userData.is_active - 是否活跃
 * @param {string} userData.avatar - 头像URL
 * @returns {Promise} 创建的用户信息
 */
export const createUserApi = async (userData) => {
  return await axios.post('/api/users', userData)
}

/**
 * 更新用户信息
 * @param {number} userId - 用户ID
 * @param {Object} userData - 要更新的用户数据
 * @returns {Promise} 更新后的用户信息
 */
export const updateUserApi = async (userId, userData) => {
  return await axios.put(`/api/users/${userId}`, userData)
}

/**
 * 删除用户（软删除，设置为非活跃状态）
 * @param {number} userId - 用户ID
 * @returns {Promise} 删除结果
 */
export const deleteUserApi = async (userId) => {
  return await axios.delete(`/api/users/${userId}`)
}

/**
 * 更新当前用户信息
 * @param {Object} userData - 要更新的用户数据
 * @returns {Promise} 更新后的用户信息
 */
export const updateCurrentUserApi = async (userData) => {
  return await axios.put('/api/users/me', userData)
}

/**
 * 修改当前用户密码
 * @param {Object} passwordData - 密码数据
 * @param {string} passwordData.current_password - 当前密码
 * @param {string} passwordData.new_password - 新密码
 * @returns {Promise} 修改结果
 */
export const changePasswordApi = async (passwordData) => {
  return await axios.post('/api/users/me/change-password', passwordData)
}

/**
 * 搜索用户
 * @param {string} q - 搜索关键词
 * @param {number} limit - 限制返回数量
 * @returns {Promise} 搜索结果
 */
export const searchUsersApi = async (q, limit = 10) => {
  return await axios.get('/api/users/search/users', {
    params: { q, limit }
  })
}

/**
 * 上传用户头像
 * @param {File} file - 头像文件
 * @returns {Promise} 上传结果
 */
export const uploadAvatarApi = async (file) => {
  const formData = new FormData()
  formData.append('file', file)

  return await axios.post('/api/users/me/avatar', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取用户权限列表
 * @param {number} userId - 用户ID
 * @returns {Promise} 用户权限列表
 */
export const getUserPermissionsApi = async (userId) => {
  return await axios.get(`/api/users/${userId}/permissions`)
}

/**
 * 更新用户权限
 * @param {number} userId - 用户ID
 * @param {Array} permissions - 权限列表
 * @returns {Promise} 更新结果
 */
export const updateUserPermissionsApi = async (userId, permissions) => {
  return await axios.put(`/api/users/${userId}/permissions`, { permissions })
}

/**
 * 启用/禁用用户
 * @param {number} userId - 用户ID
 * @param {boolean} isActive - 是否启用
 * @returns {Promise} 操作结果
 */
export const toggleUserStatusApi = async (userId, isActive) => {
  return await axios.patch(`/api/users/${userId}/status`, { is_active: isActive })
}

/**
 * 修改用户超级管理员状态
 * @param {number} userId - 用户ID
 * @param {boolean} isSuperuser - 是否为超级管理员
 * @returns {Promise} 操作结果
 */
export const toggleUserSuperuserApi = async (userId, isSuperuser) => {
  return await axios.patch(`/api/users/${userId}/superuser`, null, {
    params: { is_superuser: isSuperuser }
  })
}

/**
 * 重置用户密码（管理员功能）
 * @param {number} userId - 用户ID
 * @param {string} newPassword - 新密码
 * @returns {Promise} 重置结果
 */
export const resetUserPasswordApi = async (userId, newPassword) => {
  return await axios.post(`/api/users/${userId}/reset-password`, {
    new_password: newPassword
  })
}

/**
 * 获取用户统计信息
 * @returns {Promise} 用户统计数据
 */
export const getUserStatsApi = async () => {
  return await axios.get('/api/users/stats')
}

/**
 * 批量操作用户
 * @param {Object} batchData - 批量操作数据
 * @param {Array} batchData.user_ids - 用户ID列表
 * @param {string} batchData.action - 操作类型 ('activate', 'deactivate', 'delete')
 * @returns {Promise} 批量操作结果
 */
export const batchUserOperationApi = async (batchData) => {
  return await axios.post('/api/users/batch-operation', batchData)
}

// ==================== 用户角色相关API ====================

/**
 * 获取用户角色列表
 * @returns {Promise} 角色列表
 */
export const getUserRolesApi = async () => {
  return await axios.get('/api/users/roles')
}

/**
 * 分配角色给用户
 * @param {number} userId - 用户ID
 * @param {Array} roleIds - 角色ID列表
 * @returns {Promise} 分配结果
 */
export const assignUserRolesApi = async (userId, roleIds) => {
  return await axios.post(`/api/users/${userId}/roles`, { role_ids: roleIds })
}

/**
 * 移除用户角色
 * @param {number} userId - 用户ID
 * @param {number} roleId - 角色ID
 * @returns {Promise} 移除结果
 */
export const removeUserRoleApi = async (userId, roleId) => {
  return await axios.delete(`/api/users/${userId}/roles/${roleId}`)
}

// ==================== 用户偏好设置相关API ====================

/**
 * 获取用户偏好设置
 * @returns {Promise} 用户偏好设置
 */
export const getUserPreferencesApi = async () => {
  return await axios.get('/api/users/me/preferences')
}

/**
 * 更新用户偏好设置
 * @param {Object} preferences - 偏好设置数据
 * @returns {Promise} 更新结果
 */
export const updateUserPreferencesApi = async (preferences) => {
  return await axios.put('/api/users/me/preferences', preferences)
}

/**
 * 重置用户偏好设置为默认值
 * @returns {Promise} 重置结果
 */
export const resetUserPreferencesApi = async () => {
  return await axios.post('/api/users/me/preferences/reset')
}

// 默认导出所有API函数
export default {
  // 基础用户管理
  getUsersApi,
  getUserByIdApi,
  getCurrentUserApi,
  createUserApi,
  updateUserApi,
  deleteUserApi,
  updateCurrentUserApi,
  changePasswordApi,
  searchUsersApi,
  uploadAvatarApi,

  // 权限管理
  getUserPermissionsApi,
  updateUserPermissionsApi,

  // 状态管理
  toggleUserStatusApi,
  resetUserPasswordApi,

  // 统计信息
  getUserStatsApi,

  // 批量操作
  batchUserOperationApi,

  // 角色管理
  getUserRolesApi,
  assignUserRolesApi,
  removeUserRoleApi,

  // 偏好设置
  getUserPreferencesApi,
  updateUserPreferencesApi,
  resetUserPreferencesApi
}