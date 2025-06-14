// 聊天接口,对于后端接口文件为new_app\api\v1\endpoints\ws.py
import axios from '@/utils/axios'

// 获取聊天室列表
export const getChatRooms = async () => {
  const response = await axios.get('/api/ws/rooms')
  return response.data
}

// 获取聊天室成员列表
export const getChatRoomMembers = async (roomId) => {
  const response = await axios.get(`/api/ws/rooms/${roomId}/members`)
  return response.data
}

// 获取聊天室消息
export const getChatRoomMessages = async (roomId) => {
  const response = await axios.get(`/api/ws/rooms/${roomId}/messages`)
  return response.data
}

// 发送消息
export const sendMessage = async (roomId, message) => {
  const response = await axios.post(`/api/ws/rooms/${roomId}/messages`, { message })
  return response.data
}


// 创建聊天室
export const createChatRoom = async (room) => {
  const response = await axios.post('/api/ws/rooms', room)
  return response.data
}

// 删除聊天室
export const deleteChatRoom = async (roomId) => {
  const response = await axios.delete(`/api/ws/rooms/${roomId}`)
  return response.data
}

// 添加聊天室成员
export const addChatRoomMember = async (roomId, member) => {
  const response = await axios.post(`/api/ws/rooms/${roomId}/members`, member)
  return response.data
}

// 删除聊天室成员
export const removeChatRoomMember = async (roomId, memberId) => {
  const response = await axios.delete(`/api/ws/rooms/${roomId}/members/${memberId}`)
  return response.data
}


//私聊
export const getPrivateMessages = async (userId) => {
  const response = await axios.get(`/api/ws/messages?with_user_id=${userId}`)
  return response.data
}

// 上传图片
export const uploadImage = async (formData) => {
  const response = await axios.post('/api/ws/upload_image', formData)
  return response.data
}

// 编辑聊天室
export const editChatRoom = async (roomId, roomData) => {
  const response = await axios.put(`/api/ws/rooms/${roomId}`, roomData)
  return response.data
}