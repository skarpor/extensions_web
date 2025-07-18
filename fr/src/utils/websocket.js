/**
 * WebSocket认证工具类
 */

import { ElMessage } from 'element-plus'

export class AuthenticatedWebSocket {
  constructor(url, options = {}) {
    this.url = url
    this.options = {
      reconnectInterval: 3000,
      maxReconnectAttempts: 5,
      authTimeout: 10000,
      ...options
    }
    
    this.websocket = null
    this.authenticated = false
    this.reconnectAttempts = 0
    this.reconnectTimer = null
    this.authTimer = null
    
    // 事件回调
    this.onOpen = null
    this.onMessage = null
    this.onClose = null
    this.onError = null
    this.onAuthSuccess = null
    this.onAuthFailed = null
  }
  
  /**
   * 连接WebSocket
   * @param {string} token - 认证令牌
   */
  async connect(token) {
    if (!token) {
      throw new Error('缺少认证令牌')
    }
    
    this.token = token
    
    try {
      this.websocket = new WebSocket(this.url)
      
      this.websocket.onopen = () => {
        console.log('WebSocket连接已建立，发送认证消息...')
        this.sendAuthMessage()
        
        // 设置认证超时
        this.authTimer = setTimeout(() => {
          if (!this.authenticated) {
            console.error('WebSocket认证超时')
            this.close()
            if (this.onAuthFailed) {
              this.onAuthFailed('认证超时')
            }
          }
        }, this.options.authTimeout)
        
        if (this.onOpen) {
          this.onOpen()
        }
      }
      
      this.websocket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          
          // 处理认证响应
          if (message.type === 'auth_response') {
            this.handleAuthResponse(message)
            return
          }
          
          // 只有认证成功后才处理其他消息
          if (this.authenticated && this.onMessage) {
            this.onMessage(message)
          }
        } catch (error) {
          console.error('解析WebSocket消息失败:', error)
        }
      }
      
      this.websocket.onclose = (event) => {
        console.log('WebSocket连接已关闭:', event.code, event.reason)
        this.authenticated = false
        
        if (this.authTimer) {
          clearTimeout(this.authTimer)
          this.authTimer = null
        }
        
        if (this.onClose) {
          this.onClose(event)
        }
        
        // 自动重连（如果不是主动关闭）
        if (event.code !== 1000 && this.reconnectAttempts < this.options.maxReconnectAttempts) {
          this.scheduleReconnect()
        }
      }
      
      this.websocket.onerror = (error) => {
        console.error('WebSocket错误:', error)
        if (this.onError) {
          this.onError(error)
        }
      }
      
    } catch (error) {
      console.error('WebSocket连接失败:', error)
      throw error
    }
  }
  
  /**
   * 发送认证消息
   */
  sendAuthMessage() {
    const authMessage = {
      type: 'auth',
      token: this.token
    }
    
    this.send(authMessage)
  }
  
  /**
   * 处理认证响应
   */
  handleAuthResponse(message) {
    if (this.authTimer) {
      clearTimeout(this.authTimer)
      this.authTimer = null
    }
    
    if (message.success) {
      this.authenticated = true
      this.reconnectAttempts = 0
      console.log('WebSocket认证成功:', message.user)
      
      if (this.onAuthSuccess) {
        this.onAuthSuccess(message)
      }
    } else {
      this.authenticated = false
      console.error('WebSocket认证失败:', message.error)
      
      if (this.onAuthFailed) {
        this.onAuthFailed(message.error)
      }
      
      this.close()
    }
  }
  
  /**
   * 发送消息
   * @param {object} message - 要发送的消息对象
   */
  send(message) {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      this.websocket.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket未连接，无法发送消息')
    }
  }
  
  /**
   * 发送聊天消息（需要认证）
   * @param {object} messageData - 消息数据
   */
  sendChatMessage(messageData) {
    if (!this.authenticated) {
      console.warn('WebSocket未认证，无法发送聊天消息')
      return
    }
    
    this.send({
      type: 'send_message',
      data: messageData
    })
  }
  
  /**
   * 发送正在输入状态
   * @param {boolean} isTyping - 是否正在输入
   */
  sendTypingStatus(isTyping) {
    if (!this.authenticated) {
      return
    }
    
    this.send({
      type: 'typing',
      data: {
        is_typing: isTyping
      }
    })
  }
  
  /**
   * 编辑消息
   * @param {number} messageId - 消息ID
   * @param {string} content - 新内容
   */
  editMessage(messageId, content) {
    if (!this.authenticated) {
      return
    }
    
    this.send({
      type: 'edit_message',
      data: {
        message_id: messageId,
        content: content
      }
    })
  }
  
  /**
   * 删除消息
   * @param {number} messageId - 消息ID
   */
  deleteMessage(messageId) {
    if (!this.authenticated) {
      return
    }
    
    this.send({
      type: 'delete_message',
      data: {
        message_id: messageId
      }
    })
  }
  
  /**
   * 表情反应
   * @param {number} messageId - 消息ID
   * @param {string} emoji - 表情
   */
  reactToMessage(messageId, emoji) {
    if (!this.authenticated) {
      return
    }
    
    this.send({
      type: 'react_message',
      data: {
        message_id: messageId,
        emoji: emoji
      }
    })
  }
  
  /**
   * 安排重连
   */
  scheduleReconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }
    
    this.reconnectAttempts++
    const delay = this.options.reconnectInterval * this.reconnectAttempts
    
    console.log(`${delay}ms后尝试第${this.reconnectAttempts}次重连...`)
    
    this.reconnectTimer = setTimeout(() => {
      this.connect(this.token).catch(error => {
        console.error('重连失败:', error)
      })
    }, delay)
  }
  
  /**
   * 关闭连接
   */
  close() {
    this.authenticated = false
    
    if (this.authTimer) {
      clearTimeout(this.authTimer)
      this.authTimer = null
    }
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    
    if (this.websocket) {
      this.websocket.close(1000, '主动关闭')
      this.websocket = null
    }
  }
  
  /**
   * 获取连接状态
   */
  getReadyState() {
    return this.websocket ? this.websocket.readyState : WebSocket.CLOSED
  }
  
  /**
   * 是否已连接
   */
  isConnected() {
    return this.websocket && this.websocket.readyState === WebSocket.OPEN
  }
  
  /**
   * 是否已认证
   */
  isAuthenticated() {
    return this.authenticated
  }
}

/**
 * 创建聊天室WebSocket连接
 * @param {number} roomId - 聊天室ID
 * @param {string} token - 认证令牌
 * @param {object} callbacks - 回调函数
 */
export function createChatWebSocket(roomId, token, callbacks = {}) {
  const wsUrl = `ws://${import.meta.env.VITE_HOST}:${import.meta.env.VITE_PORT}/api/modern-chat/ws/${roomId}`
  
  const ws = new AuthenticatedWebSocket(wsUrl, {
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
    authTimeout: 10000
  })
  
  // 设置回调
  ws.onAuthSuccess = callbacks.onAuthSuccess || (() => {
    ElMessage.success('聊天室连接成功')
  })
  
  ws.onAuthFailed = callbacks.onAuthFailed || ((error) => {
    ElMessage.error('聊天室连接失败: ' + error)
  })
  
  ws.onMessage = callbacks.onMessage
  ws.onClose = callbacks.onClose
  ws.onError = callbacks.onError
  
  return ws
}

/**
 * 创建私聊WebSocket连接
 * @param {number} targetUserId - 目标用户ID
 * @param {string} token - 认证令牌
 * @param {object} callbacks - 回调函数
 */
export function createPrivateChatWebSocket(targetUserId, token, callbacks = {}) {
  const wsUrl = `ws://${import.meta.env.VITE_HOST}:${import.meta.env.VITE_PORT}/api/modern-chat/ws/private/${targetUserId}`
  
  const ws = new AuthenticatedWebSocket(wsUrl, {
    reconnectInterval: 3000,
    maxReconnectAttempts: 3,
    authTimeout: 10000
  })
  
  // 设置回调
  ws.onAuthSuccess = callbacks.onAuthSuccess || (() => {
    ElMessage.success('私聊连接成功')
  })
  
  ws.onAuthFailed = callbacks.onAuthFailed || ((error) => {
    ElMessage.error('私聊连接失败: ' + error)
  })
  
  ws.onMessage = callbacks.onMessage
  ws.onClose = callbacks.onClose
  ws.onError = callbacks.onError
  
  return ws
}
