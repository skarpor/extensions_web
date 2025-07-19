import axios from 'axios'

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




