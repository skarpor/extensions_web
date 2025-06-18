// 文件API
import axios from '@/utils/axios';

export const uploadFile = async (formData, path, config) => {
    return await axios.post(`/api/files/upload/${path}`, formData)
  }
  
  
// 获取文件列表
export const getFileList = (path) => {
    return axios.get(`/api/files?path=${path}`);
};



// 创建目录
export const createDir = (path,name) => {
    return axios.post(`/api/files/mkdir/${name}?path=${path}`)
  }



// 删除目录
export const deleteDir = (path) => {
    return axios.delete(`/api/files/dir?path=${path}`);
};



// 下载文件
export const downloadFile = (fileId,path) => {
    // 下载文件,path放在请求体中
    const data = {
        path: path
    }
    return axios.get(`/api/files/download/${fileId}`,{responseType: 'blob',params: data});
};



// 删除文件
export const deleteFile = (fileId,path) => {
    return axios.delete(`/api/files/file/${fileId}?path=${path}`);
};



