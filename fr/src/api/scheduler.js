// 扩展接口
import axios from '@/utils/axios';

// 获取扩展列表
export const getJobs = async () => {
  return await axios.get('/api/scheduler/jobs');
};

// 获取扩展详情
export const runScheJob =async (jobId) => {
  return await axios.post(`/api/scheduler/job/${jobId}/run`);
};

// 创建/安装扩展
export const pauseJob =async (jobId) => {
  return await axios.post(`/api/scheduler/job/${jobId}/pause`)
};

// 更新扩展
export const resumeJob = async (jobId) => {
  return await axios.post(`/api/scheduler/job/${jobId}/resume`);
};

// 删除扩展
export const deleteJob =async (jobId) => {
  return await axios.delete(`/api/scheduler/job/${jobId}`);
};

// 获取扩展配置
export const addJob = async (type,payload) => {
  return await axios.post(`/api/scheduler/jobs/${type}`, payload);
};


// 执行扩展查询
export const getJobDetail = async (id) => {
  return await axios.get(`/api/scheduler/jobs/${id}`);
};

// 执行扩展查询
export const getExtensionMethods = async () => {
  return await axios.get(`/api/scheduler/extensions`);
};

