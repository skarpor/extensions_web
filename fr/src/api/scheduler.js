// 定时器
import axios from '@/utils/axios';

// 获取定时器列表
export const getJobs = async () => {
  return await axios.get('/api/scheduler/jobs');
};

// 运行定时器
export const runScheduleJobApi =async (jobId) => {
  return await axios.post(`/api/scheduler/job/${jobId}/run`);
};

// 暂停定时器
export const pauseJobApi =async (jobId) => {
  return await axios.post(`/api/scheduler/job/${jobId}/pause`)
};

// 恢复定时器
export const resumeJobApi = async (jobId) => {
  return await axios.post(`/api/scheduler/job/${jobId}/resume`);
};

// 删除定时器
export const deleteJobApi =async (jobId) => {
  return await axios.delete(`/api/scheduler/job/${jobId}`);
};

// 添加定时器
export const addJob = async (type,payload) => {
  return await axios.post(`/api/scheduler/jobs/${type}`, payload);
};


// 获取定时器详情
export const getJobDetail = async (id) => {
  return await axios.get(`/api/scheduler/job/${id}`);
};

// 获取扩展方法
export const getExtensionMethods = async () => {
  return await axios.get(`/api/scheduler/extensions`);
};

