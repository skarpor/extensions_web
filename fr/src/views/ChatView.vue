<template>
    <div class="chat-container">
      <div class="chat-sidebar">
        <div class="chat-rooms">
          <h3>聊天室</h3>
          <button class="btn btn-sm btn-primary" @click="showCreateRoomModal = true">
            创建聊天室
          </button>
          <ContextMenu 
            ref="contextMenu"
            :items="menuItems"
            @select="handleMenuSelect"
          />
          <div class="room-list">
            <div 
              v-for="room in rooms" 
              :key="room.id" 
              class="room-item right-click-area" 
              :class="{ active: currentRoom && currentRoom.id === room.id }"
              @click="selectRoom(room)"
              @contextmenu.prevent="showContextMenu($event, room)"
              >
                <div class="room-name">{{ room.name }}</div>
                <div class="room-desc">{{ room.description }}</div>
            </div>
          </div>
          
        </div>
        <div class="online-users">
          <h3>在线用户</h3>
          <div class="user-list">
            <div 
              v-for="user in onlineUsers" 
              :key="user.id" 
              class="user-item"
              @click="startPrivateChat(user)"
            >
              <div class="user-avatar">
                <img :src="user.avatar || '/static/img/default-avatar.png'" alt="avatar">
                <span class="status-indicator online"></span>
              </div>
              <div class="user-info">
                <div class="user-name">{{ user.nickname || user.username }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="chat-main">
        <div class="chat-header">
          <h2>{{ chatTitle }}</h2>
          <div class="chat-actions" v-if="currentRoom">
            <button class="btn btn-sm btn-outline-primary" @click="showRoomMembers">
              成员 ({{ currentRoom.member_count || 0 }})
            </button>
          </div>
        </div>
        
        <div class="chat-messages" ref="messagesContainer">
          <div v-if="!currentRoom && !currentPrivateUser" class="no-chat-selected">
            <p>请选择一个聊天室或用户开始聊天</p>
          </div>
          <template v-else>
            <div 
              v-for="message in messages" 
              :key="message.id" 
              class="message-item"
              :class="{ 'message-mine': message.sender_id === currentUser.id }"
            >
              <div class="message-avatar">
                <img :src="message.avatar || '/static/img/default-avatar.png'" alt="avatar">
              </div>
              <div class="message-content">
                <div class="message-header">
                  <span class="message-sender">{{ message.nickname || message.username }}</span>
                  <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                </div>
                <div class="message-body">
                  <div v-if="message.message_type === 'text'">{{ message.message }}</div>
                  <div v-else-if="message.message_type === 'image'" class="message-image">
                    <img :src="message.message" alt="image" @click="viewImage(message.message)">
                  </div>
                </div>
              </div>
            </div>
            <div v-if="isTyping" class="typing-indicator">
              <span>{{ typingUser }} 正在输入...</span>
            </div>
          </template>
        </div>
        
        <div class="chat-input" v-if="currentRoom || currentPrivateUser">
          <div class="input-actions">
            <button class="btn btn-sm btn-outline-secondary" @click="showEmojiPicker = !showEmojiPicker">
              😊
            </button>
            <label class="btn btn-sm btn-outline-secondary">
              <input type="file" accept="image/*" @change="handleImageUpload" class="d-none">
              <i class="bi bi-image"></i> 图片
            </label>
          </div>
          <div class="emoji-picker" v-if="showEmojiPicker">
            <div class="emoji-list">
              <span 
                v-for="emoji in emojis" 
                :key="emoji" 
                class="emoji-item"
                @click="insertEmoji(emoji)"
              >
                {{ emoji }}
              </span>
            </div>
          </div>
          <div class="input-container">
            <textarea 
              v-model="newMessage" 
              class="form-control" 
              placeholder="输入消息..." 
              @keydown.enter.prevent="sendMessage"
              @input="handleTyping"
            ></textarea>
            <button class="btn btn-primary send-btn" @click="sendMessage" :disabled="!newMessage.trim()">
              发送
            </button>
          </div>
        </div>
      </div>
      
      <!-- 创建聊天室模态框 -->
      <div class="modal" v-if="showCreateRoomModal">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">创建聊天室</h5>
              <button type="button" class="btn-close" @click="showCreateRoomModal = false"></button>
            </div>
            <div class="modal-body">
              <form @submit.prevent="createRoom">
                <div class="form-group">
                  <label for="roomName">聊天室名称</label>
                  <input 
                    type="text" 
                    id="roomName" 
                    v-model="newRoom.name" 
                    class="form-control" 
                    required
                  >
                </div>
                <div class="form-group">
                  <label for="roomDesc">描述</label>
                  <textarea 
                    id="roomDesc" 
                    v-model="newRoom.description" 
                    class="form-control"
                  ></textarea>
                </div>
                <div class="form-check">
                  <input 
                    type="checkbox" 
                    id="isPrivate" 
                    v-model="newRoom.is_private" 
                    class="form-check-input"
                  >
                  <label for="isPrivate" class="form-check-label">私有聊天室</label>
                </div>
                <div class="modal-footer">
                  <button type="button" class="btn btn-secondary" @click="showCreateRoomModal = false">取消</button>
                  <button type="submit" class="btn btn-primary">创建</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 编辑聊天室模态框 -->
      <div class="modal" v-if="showEditRoomModal">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">编辑聊天室</h5>
              <button type="button" class="btn-close" @click="showEditRoomModal = false"></button>
            </div>
            <div class="modal-body">
              <form @submit.prevent="editRoom">
                <div class="form-group">
                  <label for="roomName">聊天室名称</label>
                  <input 
                    type="text" 
                    id="roomName" 
                    v-model="newRoom.name" 
                    class="form-control" 
                    required
                  >
                </div>
                <div class="form-group">
                  <label for="roomDesc">描述</label>
                  <textarea 
                    id="roomDesc" 
                    v-model="newRoom.description" 
                    class="form-control"
                  ></textarea>
                </div>
                <div class="form-check">
                  <input 
                    type="checkbox" 
                    id="isPrivate" 
                    v-model="newRoom.is_private" 
                    class="form-check-input"
                  >
                  <label for="isPrivate" class="form-check-label">私有聊天室</label>
                </div>
                <div class="modal-footer">
                  <button type="button" class="btn btn-secondary" @click="showEditRoomModal = false">取消</button>
                  <button type="submit" class="btn btn-primary">保存</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
      <!-- 查看图片模态框 -->
      <div class="modal" v-if="imagePreview">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <button type="button" class="btn-close" @click="imagePreview = null"><i class="fa fa-close"></i></button>
            </div>
            <div class="modal-body text-center">
              <img :src="imagePreview" class="img-fluid" alt="preview">
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  //import { ref } from 'vue'
  import axios from '@/utils/axios'
  import ContextMenu from './ContextMenu.vue'
  import { useUserStore } from '@/stores/user'
  import Toast from '@/utils/toast'
  import { getChatRooms, 
    getChatRoomMembers, 
    getChatRoomMessages, 
    sendMessage, 
    createChatRoom, 
    deleteChatRoom, 
    addChatRoomMember, 
    removeChatRoomMember, 
    editChatRoom,
    getPrivateMessages,
    uploadImage } from '@/api/ws_chat'
  //const contextMenu = ref(null)
  export default {
    name: 'ChatView',
    data() {
      return {
        menuItems:[],
        currentUser: {},
        rooms: [],
        onlineUsers: [],
        currentRoom: null,
        currentPrivateUser: null,
        messages: [],
        newMessage: '',
        ws: null,
        isConnected: false,
        isTyping: false,
        typingUser: '',
        typingTimeout: null,
        lastTypingTime: 0,
        showCreateRoomModal: false,
        showEditRoomModal: false,
        showEmojiPicker: false,
        imagePreview: null,
        newRoom: {
          name: '',
          description: '',
          is_private: false
        },
        emojis: ['😊', '😂', '❤️', '👍', '🎉', '🔥', '😎', '🤔', '😢', '😡']
      }
    },
    components: {
      ContextMenu
    }
    ,
    computed: {
      chatTitle() {
        if (this.currentRoom) {
          return this.currentRoom.name
        } else if (this.currentPrivateUser) {
          return this.currentPrivateUser.nickname || this.currentPrivateUser.username
        }
        return '聊天'
      }
    },
    async created() {
      try {
        // 获取当前用户信息
        const userResponse = await axios.get('/api/auth/me')
        this.currentUser = userResponse.data
        
        // 获取聊天室列表
        await this.fetchRooms()
        
        // 连接WebSocket
        this.connectWebSocket()
      } catch (error) {
        console.error('初始化聊天失败', error)
        Toast.error('初始化聊天失败')
      }
    },
    beforeUnmount() {
      // 断开WebSocket连接
      if (this.ws) {
        this.ws.close()
      }
      
      // 清除定时器
      if (this.typingTimeout) {
        clearTimeout(this.typingTimeout)
      }
    },
    methods: {
      // 右键菜单
      showContextMenu(e, room) {
        // 存储当前右键的房间
        this.currentRoomContext = room;
        
        // 根据房间类型动态设置菜单项
        this.menuItems = this.getRoomMenuItems(room.is_private);
        
        // 显示菜单
        if (this.$refs.contextMenu?.showMenu) {
          this.$refs.contextMenu.showMenu(e.clientX, e.clientY);
        } else {
          console.error('ContextMenu 引用或方法不可用');
        }
      },
      getRoomMenuItems(roomType) {
        const baseItems = [
          { label: '编辑', action: 'edit' },          
          { label: '删除', action: 'delete' }
        ];
        
        if (roomType) {
          return [
            ...baseItems, 
            { label: '邀请', action: 'invite' },          
            { label: '删除', action: 'remove' },
          ];
        }
        return baseItems;
      },

      handleMenuSelect(item) {
        if (!this.currentRoomContext) return;
        
        console.log(`在房间 ${this.currentRoomContext.id} 执行:`, item.action);
        switch(item.action) {
          case 'delete':
            this.deleteRoom(this.currentRoomContext);
            break;
          case 'edit':
            // 编辑逻辑，弹出模态框
            this.newRoom = this.currentRoomContext
            this.showEditRoomModal = true
            break;
          case 'invite':
            this.inviteMembers(this.currentRoomContext);
            break;
          case 'remove':
            this.removeMembers(this.currentRoomContext);
            break;
          // 其他操作...
        }
      },
      async deleteRoom(room) {
        // 删除逻辑
        // 二次确认
        if (confirm(`确定要删除这个聊天室吗？${room.name}`)) {
          // 删除逻辑
          try {
            await deleteChatRoom(room.id)
            Toast.success(`删除聊天室成功`)
            // 刷新聊天室列表
            await this.fetchRooms()
          } catch (error) {
            Toast.error(`删除聊天室失败`)
          }
        }
      },
      async editRoom(room) {
        // 发送编辑请求
        try {
          console.log('编辑聊天室', room.id, this.newRoom)
          await editChatRoom(this.newRoom.id, this.newRoom)
          Toast.success(`编辑聊天室成功`)
        } catch (error) {
          Toast.error(`编辑聊天室失败`)
        }
      },
      inviteMembers(room) {
        // 邀请成员逻辑
      },
      removeMembers(room) {
        // 删除成员逻辑
      },

      connectWebSocket() {
        // 创建WebSocket连接
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const wsUrl = `${protocol}//localhost:8000/api/ws/chat/${this.currentUser.username}`
        
        this.ws = new WebSocket(wsUrl)
        
        // WebSocket事件处理
        this.ws.onopen = this.handleSocketOpen
        this.ws.onmessage = this.handleSocketMessage
        this.ws.onclose = this.handleSocketClose
        this.ws.onerror = this.handleSocketError
      },
      
      handleSocketOpen() {
        Toast.success('WebSocket连接已建立')
        this.isConnected = true
        
        // 发送用户信息
        this.sendToSocket({
          type: 'user_info',
          nickname: this.currentUser.nickname
        })
      },
      
      handleSocketMessage(event) {
        try {
          const data = JSON.parse(event.data)
          
          
          switch (data.type) {
            case 'chat':
              this.handleChatMessage(data)
              break
            case 'users_list':
              this.handleUsersList(data)
              break
            case 'typing':
              this.handleTypingStatus(data)
              break
            case 'user_join':
              this.handleUserJoin(data)
              break
            case 'user_leave':
              this.handleUserLeave(data)
              break
            case 'members_list':
              this.handleMembersList(data)
              break
            case 'system':
              Toast.success(`系统消息, ${data.message}`)
              break
          }
        } catch (error) {
          console.error('处理消息失败', error)
        }
      },
      
      handleSocketClose(event) {
        console.log('WebSocket连接已关闭', event.code, event.reason)
        this.isConnected = false
        
        // 尝试重新连接
        setTimeout(() => {
          if (!this.isConnected) {
            this.connectWebSocket()
          }
        }, 3000)
      },
      
      handleSocketError(error) {
        console.error('WebSocket错误', error)
      },
      
      sendToSocket(data) {
        if (this.isConnected && this.ws) {
          console.log("发送消息：",JSON.stringify(data));
        
          this.ws.send(JSON.stringify(data))
          
        } else {
          console.error('WebSocket未连接')
        }
      },
      
      async fetchRooms() {
        try {
          const data = await getChatRooms()
          Toast.success(`获取聊天室成功`)
          this.rooms = data.rooms
        } catch (error) {
          
          console.error('获取聊天室失败', error)
        }
      },
      
      async selectRoom(room) {
        this.currentRoom = room
        this.currentPrivateUser = null
        
        // 加入聊天室
        this.sendToSocket({
          type: 'join_room',
          room_id: room.id
        })
        
        // 获取聊天室成员
        this.sendToSocket({
          type: 'get_members',
          room_id: room.id
        })
        
        // 获取历史消息
        try {
          const response = await getChatRoomMessages(room.id)
          this.messages = response.messages
          this.scrollToBottom()
        } catch (error) {
          console.error('获取历史消息失败', error)
        }
      },
      
      startPrivateChat(user) {
        if (user.id === this.currentUser.id) {
          return // 不能和自己聊天
        }
        
        this.currentPrivateUser = user
        this.currentRoom = null
        
        // 获取历史消息
        this.fetchPrivateMessages(user.id)
      },
      
      async fetchPrivateMessages(userId) {
        try {
          const response = await getPrivateMessages(userId)
          this.messages = response.messages
          this.scrollToBottom()
        } catch (error) {
          console.error('获取私聊消息失败', error)
        }
      },
      
      sendMessage() {
        if (!this.newMessage.trim()) return
        
        const messageData = {
          type: 'chat',
          message_type: 'text',
          message: this.newMessage
        }
        
        if (this.currentRoom) {
          messageData.room_id = this.currentRoom.id
        } else if (this.currentPrivateUser) {
          messageData.receiver_id = this.currentPrivateUser.id
        } else {
          return
        }
        
        this.sendToSocket(messageData)
        this.newMessage = ''
      },
      
      handleChatMessage(data) {
        // 检查消息是否属于当前聊天
        if (
          (this.currentRoom && data.room_id === this.currentRoom.id) ||
          (this.currentPrivateUser && 
           ((data.sender_id === this.currentPrivateUser.id && data.receiver_id === this.currentUser.id) ||
            (data.sender_id === this.currentUser.id && data.receiver_id === this.currentPrivateUser.id)))
        ) {
          this.messages.push(data)
          this.scrollToBottom()
        }
      },
      
      handleUsersList(data) {
        this.onlineUsers = data.users.filter(user => user.id !== this.currentUser.id)
      },
      
      handleTypingStatus(data) {
        if (
          (this.currentRoom && data.room_id === this.currentRoom.id && data.sender_id !== this.currentUser.id) ||
          (this.currentPrivateUser && data.sender_id === this.currentPrivateUser.id)
        ) {
          if (data.isTyping) {
            this.isTyping = true
            this.typingUser = data.nickname || data.username
            
            // 3秒后清除typing状态
            if (this.typingTimeout) {
              clearTimeout(this.typingTimeout)
            }
            
            this.typingTimeout = setTimeout(() => {
              this.isTyping = false
            }, 3000)
          } else {
            this.isTyping = false
          }
        }
      },
      
      handleTyping() {
        const now = Date.now()
        
        // 限制发送频率，至少2秒发送一次
        if (now - this.lastTypingTime > 2000) {
          this.lastTypingTime = now
          
          const typingData = {
            type: 'typing',
            isTyping: true
          }
          
          if (this.currentRoom) {
            typingData.room_id = this.currentRoom.id
          } else if (this.currentPrivateUser) {
            typingData.receiver_id = this.currentPrivateUser.id
          } else {
            return
          }
          
          this.sendToSocket(typingData)
          
          // 2秒后发送停止输入状态
          setTimeout(() => {
            typingData.isTyping = false
            this.sendToSocket(typingData)
          }, 2000)
        }
      },
      
      handleUserJoin(data) {
        console.log('用户加入', data.nickname, data.username,this.currentRoom.id)
        if (this.currentRoom && data.room_id === this.currentRoom.id) {
          // 添加系统消息
          this.messages.push({
            id: Date.now(),
            type: 'system',
            message: `${data.nickname || data.username} 加入了聊天室`,
            timestamp: data.timestamp
          })
          
          this.scrollToBottom()
        }else{
          console.log('用户加入11', data.nickname, data.username,this.currentRoom.id)
        }
      },
      
      handleUserLeave(data) {
        console.log('用户离开', data.nickname, data.username,this.currentRoom.id)
        if (this.currentRoom && data.room_id === this.currentRoom.id) {
          // 添加系统消息
          this.messages.push({
            id: Date.now(),
            type: 'system',
            message: `${data.nickname || data.username} 离开了聊天室`,
            timestamp: data.timestamp
          })
          
          this.scrollToBottom()
        }
      },
      
      handleMembersList(data) {
        console.log('聊天室成员', data.members)
        // 这里可以更新成员列表UI，修改成员数量
        this.currentRoom.member_count=data.members.length
      },
      
      async createRoom() {
        try {
          const data = await createChatRoom(this.newRoom)
          this.showCreateRoomModal = false
          this.newRoom = { name: '', description: '', is_private: false }
          
          // 刷新聊天室列表
          await this.fetchRooms()
          
          // 选择新创建的聊天室
          const newRoomId = data.room.id
          const newRoom = this.rooms.find(r => r.id === newRoomId)
          if (newRoom) {
            this.selectRoom(newRoom)
          }
        } catch (error) {
          console.error('创建聊天室失败', error)
        }
      },
      
      showRoomMembers() {
        if (this.currentRoom) {
          this.sendToSocket({
            type: 'get_members',
            room_id: this.currentRoom.id
          })
        }
      },
      
      async handleImageUpload(event) {
        const file = event.target.files[0]
        if (!file) return
        
        // 检查文件类型
        if (!file.type.startsWith('image/')) {
          Toast.error('只能上传图片文件')
          return
        }
        
        // 检查文件大小（最大5MB）
        if (file.size > 5 * 1024 * 1024) {
          Toast.error('图片大小不能超过5MB')
          return
        }
        
        try {
          const formData = new FormData()
          formData.append('image', file)
          
          const data = await uploadImage(formData)
          const imageUrl = data.image_url
          
          // 发送图片消息
          const messageData = {
            type: 'chat',
            message_type: 'image',
            message: imageUrl
          }
          
          if (this.currentRoom) {
            messageData.room_id = this.currentRoom.id
          } else if (this.currentPrivateUser) {
            messageData.receiver_id = this.currentPrivateUser.id
          } else {
            return
          }
          
          this.sendToSocket(messageData)
        } catch (error) {
          console.error('上传图片失败', error)
          Toast.error('上传图片失败')
        }
      },
      
      insertEmoji(emoji) {
        this.newMessage += emoji
        this.showEmojiPicker = false
      },
      
      viewImage(imageUrl) {
        this.imagePreview = imageUrl
      },
      
      scrollToBottom() {
        this.$nextTick(() => {
          const container = this.$refs.messagesContainer
          if (container) {
            container.scrollTop = container.scrollHeight
          }
        })
      },
      
      formatTime(timestamp) {
        if (!timestamp) return ''
        
        const date = new Date(timestamp)
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    }
  }
  </script>
  
  <style scoped>
  .chat-container {
    display: flex;
    /** 设置最大宽度 */
    width: 100%;

    height: calc(100vh - 200px);
    min-height: 500px;
    background-color: #f8f9fa;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  }
  
  .chat-sidebar {
    width: 280px;
    display: flex;
    flex-direction: column;
    background-color: #fff;
    border-right: 1px solid #e9ecef;
  }
  
  .chat-rooms {
    flex: 1;
    padding: 1rem;
    border-bottom: 1px solid #e9ecef;
    overflow-y: auto;
  }
  
  .online-users {
    flex: 1;
    padding: 1rem;
    overflow-y: auto;
  }
  
  h3 {
    font-size: 1rem;
    margin-bottom: 1rem;
    color: #6c757d;
  }
  
  .room-list, .user-list {
    margin-bottom: 1rem;
  }
  
  .room-item, .user-item {
    padding: 0.75rem;
    border-radius: 4px;
    margin-bottom: 0.5rem;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .room-item:hover, .user-item:hover {
    background-color: #f1f3f5;
  }
  
  .room-item.active {
    background-color: #e9ecef;
  }
  
  .room-name {
    font-weight: 500;
    margin-bottom: 0.25rem;
  }
  
  .room-desc {
    font-size: 0.875rem;
    color: #6c757d;
  }
  
  .user-item {
    display: flex;
    align-items: center;
  }
  
  .user-avatar {
    position: relative;
    margin-right: 0.75rem;
  }
  
  .user-avatar img {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    object-fit: cover;
  }
  
  .status-indicator {
    position: absolute;
    bottom: 0;
    right: 0;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    border: 2px solid #fff;
  }
  
  .status-indicator.online {
    background-color: #28a745;
  }
  
  .user-info {
    flex: 1;
  }
  
  .user-name {
    font-weight: 500;
  }
  
  .chat-main {
    flex: 1;
    display: flex;
    flex-direction: column;
  }
  
  .chat-header {
    padding: 1rem;
    border-bottom: 1px solid #e9ecef;
    background-color: #fff;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .chat-header h2 {
    margin: 0;
    font-size: 1.25rem;
  }
  
  .chat-messages {
    flex: 1;
    padding: 1rem;
    overflow-y: auto;
    background-color: #f8f9fa;
  }
  
  .no-chat-selected {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    color: #6c757d;
  }
  
  .message-item {
    display: flex;
    margin-bottom: 1rem;
    max-width: 80%;
  }
  
  .message-mine {
    margin-left: auto;
    flex-direction: row-reverse;
  }
  
  .message-avatar {
    margin-right: 0.75rem;
    margin-left: 0.75rem;
  }
  
  .message-avatar img {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    object-fit: cover;
  }
  
  .message-content {
    background-color: #fff;
    padding: 0.75rem;
    border-radius: 8px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  }
  
  .message-mine .message-content {
    background-color: #dcf8c6;
  }
  
  .message-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }
  
  .message-sender {
    font-weight: 500;
    font-size: 0.875rem;
  }
  
  .message-time {
    font-size: 0.75rem;
    color: #6c757d;
  }
  
  .message-body {
    word-break: break-word;
  }
  
  .message-image img {
    max-width: 100%;
    max-height: 300px;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .typing-indicator {
    font-size: 0.875rem;
    color: #6c757d;
    margin-bottom: 0.5rem;
    font-style: italic;
  }
  
  .chat-input {
    padding: 1rem;
    background-color: #fff;
    border-top: 1px solid #e9ecef;
  }
  
  .input-actions {
    display: flex;
    margin-bottom: 0.5rem;
  }
  
  .input-actions button, .input-actions label {
    margin-right: 0.5rem;
    cursor: pointer;
  }
  
  .emoji-picker {
    background-color: #fff;
    border: 1px solid #e9ecef;
    border-radius: 4px;
    padding: 0.5rem;
    margin-bottom: 0.5rem;
    max-height: 100px;
    overflow-y: auto;
  }
  
  .emoji-list {
    display: flex;
    flex-wrap: wrap;
  }
  
  .emoji-item {
    font-size: 1.5rem;
    padding: 0.25rem;
    cursor: pointer;
  }
  
  .input-container {
    display: flex;
  }
  
  .input-container textarea {
    flex: 1;
    resize: none;
    height: 60px;
  }
  
  .send-btn {
    margin-left: 0.5rem;
    align-self: flex-end;
  }
  
  .modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }
  
  .modal-dialog {
    width: 100%;
    max-width: 500px;
    margin: 1.75rem auto;
  }
  
  .modal-content {
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid #e9ecef;
  }
  
  .modal-title {
    margin: 0;
  }
  
  .btn-close {
    background: transparent;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
  }
  
  .modal-body {
    padding: 1rem;
  }
  
  .modal-footer {
    padding: 1rem;
    border-top: 1px solid #e9ecef;
    display: flex;
    justify-content: flex-end;
  }
  
  .form-group {
    margin-bottom: 1rem;
  }
  
  .form-check {
    display: flex;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .form-check-input {
    margin-right: 0.5rem;
  }

  </style>