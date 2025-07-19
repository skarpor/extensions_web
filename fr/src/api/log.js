// src/api/log.js
import axios from 'axios';

/**
 * 获取日志文件列表
 * @returns {Promise<Array<{name: string, size: string, last_modified: string}>>}
 */
export const getLogFiles = async () => {
  try {
    const response = await axios.get('/api/log/');
    return response.data.map(file => ({
      ...file,
      // 确保返回统一格式的日期
      last_modified: new Date(file.last_modified).toISOString()
    }));
  } catch (error) {
    console.error('获取日志文件列表失败:', error);
    throw new Error(error.response?.data?.detail || '获取日志文件失败');
  }
};

/**
 * 获取日志文件内容（非流式）
 * @param {string} fileName 
 * @param {number} lines 要获取的行数
 * @returns {Promise<{content: string[]}>}
 */
export const getLogContent = async (fileName, lines = 500) => {
  try {
    const response = await axios.get(`/api/log/${fileName}`, {
      params: { lines },
      timeout: 10000 // 10秒超时
    });
    return response.data;
  } catch (error) {
    console.error('获取日志内容失败:', error);
    throw new Error(error.response?.data?.detail || '获取日志内容失败');
  }
};

/**
 * 创建SSE连接以流式获取日志
 * @param {string} fileName 
 * @param {{
 *   onMessage: (data: string) => void,
 *   onError?: (error: Error) => void,
 *   onOpen?: () => void
 * }} callbacks 
 * @returns {() => void} 断开连接的函数
 */
export const createLogStream1 = (fileName, { onMessage, onError, onOpen }) => {
  // 确保文件名经过编码
  const encodedFileName = encodeURIComponent(fileName);
  const eventSource = new EventSource(`/api/log/stream/${encodedFileName}`);

  eventSource.onopen = () => {
    console.log(`SSE连接已建立: ${fileName}`);
    onOpen?.();
  };

  eventSource.onmessage = (event) => {
    console.log(123,event.data)
    if (event.data.startsWith('data: ')) {
      onMessage(event.data.substring(6).trim());
    } else if (event.data.startsWith('event: error')) {
      const error = new Error(event.data.substring(12).trim());
      onError?.(error);
    }
  };

  eventSource.onerror = () => {
    const error = new Error('SSE连接错误');
    onError?.(error);
    eventSource.close();
  };

  // 返回断开连接的函数
  return () => {
    console.log(`关闭SSE连接: ${fileName}`);
    eventSource.close();
  };
};
/**
 * 创建SSE连接以流式获取日志
 * @param {string} fileName 
 * @param {{
*   onMessage: (data: string) => void,
*   onError?: (error: Error) => void,
*   onOpen?: () => void
* }} callbacks 
* @returns {() => void} 断开连接的函数
*/
export const createLogStream = (fileName, { onMessage, onError, onOpen }) => {
 // 确保文件名经过编码
 const encodedFileName = encodeURIComponent(fileName);

 const url = `http://${import.meta.env.VITE_HOST}:${import.meta.env.VITE_PORT}/api/log/stream/${encodedFileName}`;
 
 console.log(`创建SSE连接: ${url}`);
 
 // 创建EventSource连接
 const eventSource = new EventSource(url);

 eventSource.onopen = () => {
   console.log(`SSE连接已建立: ${fileName}`);
   onOpen?.();
 };

 eventSource.onmessage = (event) => {
   try {
     // 直接处理数据，不需要再检查前缀
     const data = event.data;
     console.log(`收到SSE消息:`, data);
     onMessage(data);
   } catch (err) {
     console.error('处理SSE消息时出错:', err);
     onError?.(new Error('处理SSE消息时出错: ' + err.message));
   }
 };

 eventSource.onerror = (event) => {
   console.error('SSE连接错误:', event);
   const error = new Error('SSE连接错误');
   onError?.(error);
   
   // 不要立即关闭，让EventSource自动尝试重连
   if (eventSource.readyState === EventSource.CLOSED) {
     console.log('SSE连接已关闭，将不再自动重连');
   }
 };

 // 返回断开连接的函数
 return () => {
   console.log(`关闭SSE连接: ${fileName}`);
   eventSource.close();
 };
};
/**
 * 下载日志文件
 * @param {string} fileName 
 * @param {string} content 
 */
export const downloadLogFile = (fileName, content) => {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${fileName}_${new Date().toISOString().slice(0, 10)}.log`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

/**
 * 处理日志内容（提取时间戳和级别）
 * @param {string} log 
 * @returns {{
 *   raw: string,
 *   timestamp: string | null,
 *   level: 'error' | 'warn' | 'info' | 'debug' | 'trace' | 'fatal' | null,
 *   content: string
 * }}
 */
export const parseLogEntry = (log) => {
  const result = {
    raw: log,
    timestamp: null,
    level: null,
    content: log
  };

  // 提取时间戳（匹配多种格式）
  const timestampMatch = log.match(/(\[?\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z?\]?)/);
  if (timestampMatch) {
    result.timestamp = timestampMatch[1];
    result.content = log.replace(timestampMatch[0], '').trim();
  }

  // 检测日志级别（不区分大小写）
  const logUpper = log.toUpperCase();
  if (logUpper.includes('ERROR') || logUpper.includes('ERR')) {
    result.level = 'error';
  } else if (logUpper.includes('WARN') || logUpper.includes('WARNING')) {
    result.level = 'warn';
  } else if (logUpper.includes('INFO')) {
    result.level = 'info';
  } else if (logUpper.includes('DEBUG')) {
    result.level = 'debug';
  } else if (logUpper.includes('TRACE')) {
    result.level = 'trace';
  } else if (logUpper.includes('FATAL')) {
    result.level = 'fatal';
  }

  return result;
};

/**
 * 获取日志级别对应的CSS类名
 * @param {string} level 
 * @returns {string}
 */
export const getLogLevelClass = (level) => {
  switch (level) {
    case 'error': return 'log-error';
    case 'warn': return 'log-warn';
    case 'info': return 'log-info';
    case 'debug': return 'log-debug';
    case 'trace': return 'log-trace';
    case 'fatal': return 'log-fatal';
    default: return '';
  }
};

/**
 * 格式化文件大小
 * @param {number} bytes 
 * @returns {string}
 */
export const formatFileSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

/**
 * 格式化日期时间
 * @param {string|Date} date 
 * @returns {string}
 */
export const formatDateTime = (date) => {
  const d = date instanceof Date ? date : new Date(date);
  return d.toLocaleString();
};

// 默认导出所有方法
export default {
  getLogFiles,
  getLogContent,
  createLogStream,
  downloadLogFile,
  parseLogEntry,
  getLogLevelClass,
  formatFileSize,
  formatDateTime
};