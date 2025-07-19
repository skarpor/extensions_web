import axios from "@/utils/axios";

/**
 * Markdown文件管理API
 */

/**
 * 获取Markdown文件列表
 * @returns {Promise} 文件列表数据
 */
export const getMarkdownList = async () => {
    try {
        const response = await axios.get('/api/markdown/list');
        return response.data;
    } catch (error) {
        console.error('获取文件列表失败:', error);
        throw error;
    }
};

/**
 * 加载指定Markdown文件内容
 * @param {string} filePath - 文件路径
 * @returns {Promise} 文件内容数据
 */
export const loadMarkdownFile = async (filePath) => {
    try {
        const response = await axios.post('/api/markdown/load', {
            file_path: filePath
        });
        return response.data;
    } catch (error) {
        console.error('加载文件失败:', error);
        throw error;
    }
};

/**
 * 保存Markdown文件内容
 * @param {string} content - 文件内容
 * @param {string} filePath - 文件路径
 * @returns {Promise} 保存结果
 */
export const saveMarkdownFile = async (content, filePath) => {
    try {
        const response = await axios.post('/api/markdown/save', {
            content: content,
            file_path: filePath
        });
        return response.data;
    } catch (error) {
        console.error('保存文件失败:', error);
        throw error;
    }
};

/**
 * 创建新的Markdown文件
 * @param {string} fileName - 文件名
 * @param {string} template - 模板类型 (blank, readme, api, project)
 * @returns {Promise} 创建结果
 */
export const createMarkdownFile = async (fileName, template = 'blank') => {
    try {
        const response = await axios.post('/api/markdown/create', {
            file_name: fileName,
            template: template
        });
        return response.data;
    } catch (error) {
        console.error('创建文件失败:', error);
        throw error;
    }
};

/**
 * 删除Markdown文件
 * @param {string} filePath - 文件路径
 * @returns {Promise} 删除结果
 */
export const deleteMarkdownFile = async (filePath) => {
    try {
        const response = await axios.delete('/api/markdown/delete', {
            data: { file_path: filePath }
        });
        return response.data;
    } catch (error) {
        console.error('删除文件失败:', error);
        throw error;
    }
};
