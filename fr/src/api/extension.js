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
  return axios.get(`/api/extensions/${id}/query`);
};

// 执行扩展查询
export const executeExtensionQuery1 = (id, formData) => {
  return axios.post(`/query/${id}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
};
export const executeExtensionQuery = (id, formData = {}) => {
  // 创建一个FormData对象
  const form = new FormData()
  
  // 即使没有数据，也确保表单格式正确
  if (Object.keys(formData).length === 0) {
    // 添加一个空字段确保格式正确
    form.append('_dummy', '')
  } else {
    // 将formData中的数据添加到FormData对象
    Object.keys(formData).forEach(key => {
      const value = formData[key]
      if (value instanceof File) {
        form.append(key, value, value.name)
      } else if (value !== null && value !== undefined) {
        form.append(key, value)
      }
    })
  }
  
  // 发送请求，确保使用正确的content-type
  return axios.post(`/query/${id}`, form, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  }).then(res => res.data)
}
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