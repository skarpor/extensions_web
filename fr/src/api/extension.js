// 扩展接口
import axios from '@/utils/axios';

// 获取扩展列表
export const getExtensions = () => {
  return axios.get('/api/extensions');
};

// 获取扩展详情
export const getExtension = (id) => {
  return axios.get(`/api/extensions/${id}`);
};

// 创建/安装扩展
export const createExtension = (formData) => {
  return axios.post('/api/extensions', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
};

// 更新扩展
export const updateExtension = (id, data) => {
  return axios.put(`/api/extensions/${id}`, data);
};

// 删除扩展
export const deleteExtension = (id) => {
  return axios.delete(`/api/extensions/${id}`);
};

// 获取扩展配置
export const getExtensionConfig = (id) => {
  return axios.get(`/api/extensions/${id}/config`);
};

// 保存扩展配置
export const saveExtensionConfig = (id, config) => {
  return axios.post(`/api/extensions/${id}/config`, { config });
};

// 获取扩展查询表单
export const getExtensionQueryForm = (id) => {
  return axios.get(`/api/extensions/${id}/query_form`);
};

// 执行扩展查询
export const executeExtensionQuery = (id, formData) => {
  return axios.post(`/query/${id}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
};

export default {
  getExtensions,
  getExtension,
  createExtension,
  updateExtension,
  deleteExtension,
  getExtensionConfig,
  saveExtensionConfig,
  getExtensionQueryForm,
  executeExtensionQuery
};