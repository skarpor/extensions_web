import axios from '@/utils/axios.js'

export const getSettingsApi = async () => {
return await axios.get('/api/system/settings')
}

export const updateSettingsApi = async (settings) => {
  return await axios.put('/api/system/settings', settings)
}



export const rebootApi = async () => {
  return await axios.post('/api/system/reboot')
}



export const getExpiryInfoApi = async () => {
  return await axios.get('/api/system/expiry-info')
}

export const updateSecretKeyApi = async (secretKey) => {
  return await axios.put('/api/system/settings/secret-key', {
    secret_key: secretKey,
  })
}

export const getConfigStatusApi = async () => {
  return await axios.get('/api/system/config-status')
}

export const updateConfigStatusApi = async (configStatus) => {
  return await axios.put('/api/system/config-status', configStatus)
}

// 系统信息相关API
export const getSystemInfoApi = async () => {
  return await axios.get('/api/system/system/info')
}

// 命令执行相关API
export const executeCommandApi = async (command, name) => {
  return await axios.post('/api/system/system/execute-command', {
    command,
    name
  })
}

// 重启脚本相关API
export const createRestartScriptApi = async () => {
  return await axios.post('/api/system/system/create-restart-script')
}

// 进程管理器相关API
export const processRestartApi = async () => {
  return await axios.post('/api/system/system/process-restart')
}

export const processForceRestartApi = async () => {
  return await axios.post('/api/system/system/process-force-restart')
}

export const processStopApi = async () => {
  return await axios.post('/api/system/system/process-stop')
}

export const getProcessConfigApi = async () => {
  return await axios.get('/api/system/system/process-config')
}

export const updateProcessConfigApi = async (config) => {
  return await axios.post('/api/system/system/process-config', config)
}

// 用户管理相关API已移动到 @/api/user.js




