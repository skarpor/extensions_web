import axios from '@/utils/axios';

export const getFileList = async () => {
    return await axios.get('/api/help/list');
};

export const viewFile = async (filename) => {
    return await axios.get(`/api/help/view/${filename}`);
};

export const uploadFileAPI = async (file) => {
    return await axios.post('/api/help/upload', file);
};

export const deleteFile = async (filename) => {
    return await axios.delete(`/api/help/delete/${filename}`);
};

export const downloadFileApi = async (filename) => {
    return await axios.get(`/api/help/download/${filename}`);
};




