<template>
  <div class="modern-chat">
    <!-- 聊天室列表侧边栏 -->
    <div class="chat-sidebar" :class="{ 'mobile-hidden': !showSidebar }">
      <div class="sidebar-header">
        <h3>聊天室</h3>
        <div class="header-actions">
          <el-button type="primary" size="small" @click="showCreateRoomDialog = true">
            <el-icon><Plus /></el-icon>
            创建
          </el-button>
          <el-button type="success" size="small" @click="showPrivateChatDialog = true">
            <el-icon><ChatDotRound /></el-icon>
            私聊
          </el-button>
          <el-button type="warning" size="small" @click="showJoinRoomDialog = true">
            <el-icon><Search /></el-icon>
            加入
          </el-button>
        </div>
      </div>
      
      <div class="room-search">
        <el-input
          v-model="searchQuery"
          placeholder="搜索聊天室..."
          prefix-icon="Search"
          size="small"
        />
      </div>
      
      <div class="room-list">
        <div
          v-for="room in filteredRooms"
          :key="room.id"
          class="room-item"
          :class="{ active: currentRoom?.id === room.id }"
          @click="selectRoom(room)"
          @contextmenu.prevent.stop="showRoomContextMenu($event, room)"
        >
          <div class="room-avatar" :class="getRoomAvatarClass(room)">
            <img v-if="room.avatar" :src="room.avatar" :alt="room.name" />
            <div v-else class="default-avatar">
              {{ room.name.charAt(0).toUpperCase() }}
            </div>
            <!-- 聊天室类型标识 -->
            <div class="room-type-badge" :class="getRoomTypeBadgeClass(room)">
              <el-icon class="type-icon">
                <ChatDotRound v-if="room.room_type === 'public'" />
                <Lock v-else-if="room.room_type === 'group'" />
                <Message v-else-if="room.room_type === 'private'" />
                <Promotion v-else />
              </el-icon>
            </div>
            <span v-if="room.unread_count > 0" class="unread-badge">
              {{ room.unread_count > 99 ? '99+' : room.unread_count }}
            </span>
          </div>
          
          <div class="room-info">
            <div class="room-name-container">
              <span class="room-name" :class="getRoomNameClass(room)">{{ room.name }}</span>
              <span class="room-type-text" :class="getRoomTypeTextClass(room)">
                {{ getRoomTypeText(room) }}
              </span>
            </div>
            <div class="room-last-message">
              <template v-if="room.last_message">
                <span class="message-sender">{{ room.last_message.sender?.username }}:</span>
                <span class="message-content">{{ room.last_message.content }}</span>
              </template>
              <span v-else class="no-message">暂无消息</span>
            </div>
          </div>
          
          <div class="room-meta">
            <div class="room-time">
              {{ formatTime(room.last_message_at) }}
            </div>
            <div class="room-type">
              <el-tag size="small" :type="getRoomTypeColor(room.room_type)">
                {{ getRoomTypeName(room.room_type) }}
              </el-tag>
            </div>


          </div>
        </div>
      </div>
    </div>
    
    <!-- 主聊天区域 -->
    <div class="chat-main">
      <!-- 移动端顶部栏 -->
      <div class="mobile-header" v-if="isMobile">
        <el-button @click="showSidebar = !showSidebar" text>
          <el-icon><Menu /></el-icon>
        </el-button>
        <span v-if="currentRoom">{{ currentRoom.name }}</span>
      </div>
      
      <!-- 聊天头部 -->
      <div class="chat-header" v-if="currentRoom">
        <div class="room-info">
          <div class="room-avatar">
            <img v-if="currentRoom.avatar" :src="currentRoom.avatar" :alt="currentRoom.name" />
            <div v-else class="default-avatar">
              {{ currentRoom.name.charAt(0).toUpperCase() }}
            </div>
          </div>
          <div class="room-details">
            <h3 class="clickable-room-name" @click="showRoomInfoDialog = true">
              {{ currentRoom.name }}
              <el-icon class="room-info-icon"><InfoFilled /></el-icon>
            </h3>
            <p>{{ currentRoom.member_count }} 名成员 · {{ onlineCount }} 人在线</p>
          </div>
        </div>
        
        <div class="header-actions">
          <el-button @click="showRoomInfo = true" text>
            <el-icon><InfoFilled /></el-icon>
          </el-button>
          <el-button @click="showMemberList = true" text>
            <el-icon><User /></el-icon>
          </el-button>
        </div>
      </div>
      
      <!-- 消息区域 -->
      <div class="chat-messages" ref="messagesContainer" v-if="currentRoom">
        <!-- 置顶消息区域 -->
        <div v-if="pinnedMessagesInRoom.length > 0" class="pinned-messages-area">
          <div class="pinned-header">
            <el-icon><Star /></el-icon>
            <span>置顶消息 ({{ pinnedMessagesInRoom.length }})</span>
            <el-button
              text
              size="small"
              @click="showPinnedMessages = !showPinnedMessages"
            >
              {{ showPinnedMessages ? '收起' : '展开' }}
            </el-button>
          </div>
          <div v-if="showPinnedMessages" class="pinned-messages-list">
            <div
              v-for="pinnedMsg in pinnedMessagesInRoom"
              :key="pinnedMsg.id"
              class="pinned-message-item"
            >
              <div class="pinned-message-content">
                <span class="sender-name">{{ pinnedMsg.sender.nickname || pinnedMsg.sender.username }}:</span>
                <span class="message-text">{{ pinnedMsg.content }}</span>
              </div>
              <div class="pinned-message-actions">
                <el-button
                  text
                  size="small"
                  @click="scrollToMessage(pinnedMsg.id)"
                >
                  定位
                </el-button>
                <el-button
                  v-if="canManageRoom(currentRoom)"
                  text
                  size="small"
                  type="danger"
                  @click="togglePinMessage(pinnedMsg)"
                >
                  取消置顶
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 固定置顶消息条 -->
        <div
          v-if="currentPinnedMessage"
          class="fixed-pinned-message"
          @click="scrollToMessage(currentPinnedMessage.id)"
        >
          <div class="pinned-message-indicator">
            <el-icon class="pin-icon"><Star /></el-icon>
            <span class="pinned-label">置顶消息</span>
          </div>
          <div class="pinned-message-preview">
            <span class="pinned-sender">{{ currentPinnedMessage.sender.nickname || currentPinnedMessage.sender.username }}:</span>
            <span class="pinned-content">{{ truncateText(currentPinnedMessage.content, 50) }}</span>
          </div>
          <div class="pinned-message-actions">
            <el-button
              text
              size="small"
              @click.stop="scrollToMessage(currentPinnedMessage.id)"
            >
              <el-icon><Search /></el-icon>
            </el-button>
            <el-button
              v-if="canManageRoom(currentRoom)"
              text
              size="small"
              type="danger"
              @click.stop="togglePinMessage(currentPinnedMessage)"
            >
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </div>

        <div class="messages-list">
          <template v-for="message in messages" :key="message.id">
            <!-- 系统消息 -->
            <div
              v-if="message.message_type === 'system'"
              :data-message-id="message.id"
              class="system-message-container"
            >
              <div class="message-system" :class="getSystemMessageClass(message.system_data?.type)">
                <el-icon>
                  <component :is="getSystemMessageIcon(message.system_data?.type)" />
                </el-icon>
                <span class="system-text">{{ message.content }}</span>

                <!-- 加入申请系统消息的操作按钮 -->
                <div
                  v-if="message.system_data?.type === 'join_request' && canManageRoom(currentRoom)"
                  class="system-actions"
                >
                  <el-button
                    type="success"
                    size="small"
                    @click="approveJoinRequest(message.system_data)"
                    :loading="processingRequest"
                  >
                    同意
                  </el-button>
                  <el-button
                    type="danger"
                    size="small"
                    @click="rejectJoinRequest(message.system_data)"
                    :loading="processingRequest"
                  >
                    拒绝
                  </el-button>
                </div>

                <!-- 置顶消息的操作按钮 -->
                <div
                  v-if="message.system_data?.type === 'message_pinned' && message.system_data?.pinned_message_id"
                  class="system-actions"
                >
                  <el-button
                    type="primary"
                    size="small"
                    @click="scrollToMessage(message.system_data.pinned_message_id)"
                  >
                    查看消息
                  </el-button>
                </div>

                <!-- 角色变更消息的用户信息 -->
                <div
                  v-if="['admin_promoted', 'admin_demoted', 'owner_transferred'].includes(message.system_data?.type)"
                  class="system-user-info"
                >
                  <el-tag
                    :type="getTagType(message.system_data?.new_role)"
                    size="small"
                  >
                    {{ getRoleDisplayName(message.system_data?.new_role) }}
                  </el-tag>
                </div>
              </div>
            </div>

            <!-- 普通消息 -->
            <div
              v-else
              :data-message-id="message.id"
              class="message-item"
              :class="{
                'own-message': message.sender.id === userStore.user?.id,
                'pinned-message': message.is_pinned
              }"
              @contextmenu.prevent.stop="showMessageContextMenu($event, message)"
            >
            <div class="message-avatar">
              <img v-if="message.sender.avatar" :src="message.sender.avatar" :alt="message.sender.username" />
              <div v-else class="default-avatar">
                {{ message.sender.username.charAt(0).toUpperCase() }}
              </div>
            </div>
            
            <div class="message-content">
              <div class="message-header">
                <span class="sender-name">{{ message.sender.nickname || message.sender.username }}</span>
                <span class="message-time">{{ formatMessageTime(message.created_at) }}</span>
                <el-tag v-if="message.is_edited" size="small" type="info">已编辑</el-tag>
              </div>
              
              <!-- 回复消息 -->
              <div v-if="message.reply_to" class="reply-message">
                <div class="reply-content">
                  <span class="reply-sender">{{ message.reply_to.sender.username }}</span>
                  <span class="reply-text">{{ message.reply_to.content }}</span>
                </div>
              </div>
              
              <!-- 消息内容 -->
              <div v-if="!message.is_deleted">
                <!-- 文本消息 -->
                <div v-if="message.message_type === 'text'" class="message-text">
                  {{ message.content }}
                </div>

                <!-- 图片消息 -->
                <div v-else-if="message.message_type === 'image'" class="message-image">
                  <img
                    :src="message.file_url"
                    :alt="message.file_name"
                    @click="previewImage(message.file_url)"
                    class="chat-image"
                  />
                  <div class="image-info">
                    <span class="image-name">{{ message.file_name }}</span>
                    <span class="image-size">{{ formatFileSize(message.file_size) }}</span>
                  </div>
                </div>

                <!-- 文件消息 -->
                <div v-else-if="message.message_type === 'file'" class="message-file">
                  <div class="file-icon">
                    <el-icon><Document /></el-icon>
                  </div>
                  <div class="file-info">
                    <div class="file-name">{{ message.file_name }}</div>
                    <div class="file-size">{{ formatFileSize(message.file_size) }}</div>
                  </div>
                  <el-button
                    type="primary"
                    size="small"
                    @click="downloadFile(message.file_url, message.file_name)"
                  >
                    下载
                  </el-button>
                </div>



                <!-- 其他类型消息 -->
                <div v-else class="message-text">
                  {{ message.content }}
                </div>
              </div>

              <!-- 已删除消息 -->
              <div class="message-deleted" v-else>
                <el-icon><Delete /></el-icon>
                此消息已被删除
              </div>
              
              <!-- 消息操作 -->
              <div class="message-actions" v-if="!message.is_deleted">
                <el-button @click="replyToMessage(message)" text size="small" title="回复">
                  <el-icon><ChatDotRound /></el-icon>
                </el-button>
                <el-button @click="reactToMessage(message)" text size="small" title="表情反应">
                  <el-icon><Star /></el-icon>
                </el-button>
                <el-button
                  v-if="message.sender.id === userStore.user?.id"
                  @click="editMessage(message)"
                  text
                  size="small"
                  title="编辑"
                >
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button
                  v-if="message.sender.id === userStore.user?.id"
                  @click="deleteMessage(message)"
                  text
                  size="small"
                  type="danger"
                  title="删除"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
                <el-button @click="copyMessage(message)" text size="small" title="复制">
                  <el-icon><DocumentCopy /></el-icon>
                </el-button>
              </div>
              
              <!-- 表情反应 -->
              <div v-if="message.reactions && message.reactions.length > 0" class="message-reactions">
                <span
                  v-for="reaction in message.reactions"
                  :key="reaction.emoji"
                  class="reaction-item"
                  :class="{ 'user-reacted': reaction.user_reacted }"
                  @click="toggleReaction(message, reaction.emoji)"
                >
                  {{ reaction.emoji }} {{ reaction.count }}
                </span>
              </div>
            </div>
          </div>
          </template>
        </div>
        
        <!-- 正在输入提示 -->
        <div v-if="typingUsers.length > 0" class="typing-indicator">
          <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <span class="typing-text">
            {{ getTypingText() }}
          </span>
        </div>
      </div>
      
      <!-- 消息输入区域 -->
      <div class="chat-input" v-if="currentRoom">
        <!-- 回复预览 -->
        <div v-if="replyingTo" class="reply-preview">
          <div class="reply-info">
            <span>回复 {{ replyingTo.sender.username }}</span>
            <span class="reply-content">{{ replyingTo.content }}</span>
          </div>
          <el-button @click="cancelReply" text size="small">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        
        <!-- 编辑提示 -->
        <div v-if="editingMessage" class="edit-preview">
          <div class="edit-info">
            <span>编辑消息</span>
            <span class="edit-content">{{ editingMessage.content }}</span>
          </div>
          <el-button @click="cancelEdit" text size="small">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>

        <!-- 输入框 -->
        <div class="input-area">
          <el-input
            v-model="messageInput"
            type="textarea"
            :rows="3"
            :placeholder="editingMessage ? '编辑消息...' : '输入消息...'"
            @keydown.enter.exact="sendMessage"
            @keydown.enter.shift.exact.prevent="messageInput += '\n'"
            @keydown.esc="cancelEdit"
            @input="handleTyping"
            resize="none"
          />

          <div class="input-actions">
            <div class="left-actions">
              <el-button @click="showEmojiPicker = !showEmojiPicker" text>
                <el-icon><Star /></el-icon>
              </el-button>

              <!-- 图片上传 -->
              <el-upload
                :show-file-list="false"
                :before-upload="handleImageUpload"
                accept="image/*"
                :disabled="uploading"
                multiple
                :limit="9"
              >
                <el-button text :loading="uploading">
                  <el-icon><Picture /></el-icon>
                </el-button>
              </el-upload>

              <!-- 文件上传 -->
              <el-upload
                :show-file-list="false"
                :before-upload="handleFileUpload"
                accept=".pdf,.doc,.docx,.txt,.zip,.rar"
                :disabled="uploading"
              >
                <el-button text :loading="uploading">
                  <el-icon><Paperclip /></el-icon>
                </el-button>
              </el-upload>
            </div>

            <el-button
              type="primary"
              @click="sendMessage"
              :disabled="!messageInput.trim()"
            >
              <el-icon><Promotion /></el-icon>
              {{ editingMessage ? '保存' : '发送' }}
            </el-button>
          </div>

          <!-- 上传进度 -->
          <div v-if="uploading" class="upload-progress">
            <el-progress :percentage="uploadProgress" :show-text="false" />
            <span>上传中... {{ uploadProgress }}%</span>
          </div>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-else class="empty-state">
        <el-empty description="选择一个聊天室开始聊天" />
      </div>
    </div>
    
    <!-- 创建聊天室对话框 -->
    <el-dialog v-model="showCreateRoomDialog" title="创建聊天室" width="800px">
      <el-form :model="newRoom" label-width="100px">
        <el-form-item label="聊天室名称" required>
          <el-input v-model="newRoom.name" placeholder="请输入聊天室名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newRoom.description" type="textarea" placeholder="聊天室描述（可选）" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="newRoom.room_type" placeholder="选择聊天室类型" @change="onRoomTypeChange">
            <el-option label="🌍 公开聊天室 - 所有人都可以查看和聊天" value="public" />
            <el-option label="🔒 私密聊天室 - 只有受邀成员可以聊天" value="group" />
            <el-option label="📢 频道 - 只有管理员可以发言" value="channel" />
          </el-select>
          <div class="room-type-description">
            <p v-if="newRoom.room_type === 'public'" class="type-desc public-desc">
              <el-icon><ChatDotRound /></el-icon>
              <strong>公开聊天室：</strong>所有用户都可以查看和参与聊天，无需邀请。适合开放讨论、社区交流等场景。
            </p>
            <p v-if="newRoom.room_type === 'group'" class="type-desc group-desc">
              <el-icon><Lock /></el-icon>
              <strong>私密聊天室：</strong>只有受邀请的成员才能查看和聊天。适合团队内部讨论、私人群组等场景。
            </p>
            <p v-if="newRoom.room_type === 'channel'" class="type-desc channel-desc">
              <el-icon><Promotion /></el-icon>
              <strong>频道：</strong>只有管理员和创建者可以发言，其他成员只能查看。适合公告发布、新闻推送等场景。
            </p>
          </div>
        </el-form-item>
        <el-form-item label="最大成员">
          <el-input-number v-model="newRoom.max_members" :min="2" :max="10000" />
        </el-form-item>

        <!-- 私密聊天室高级设置 -->
        <div v-if="newRoom.room_type === 'group'" class="advanced-settings">
          <h4>私密聊天室设置</h4>

          <el-form-item label="搜索设置">
            <el-switch
              v-model="newRoom.allow_search"
              active-text="允许被搜索"
              inactive-text="不允许搜索"
            />
            <div class="setting-description">
              <small>开启后，其他用户可以通过搜索找到此聊天室并申请加入</small>
            </div>
          </el-form-item>

          <el-form-item label="邀请码">
            <el-switch
              v-model="newRoom.enable_invite_code"
              active-text="启用邀请码"
              inactive-text="禁用邀请码"
            />
            <div class="setting-description">
              <small>开启后，用户可以通过邀请码直接加入聊天室</small>
            </div>
          </el-form-item>
        </div>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateRoomDialog = false">取消</el-button>
        <el-button type="primary" @click="createRoom" :loading="creating">创建</el-button>
      </template>
    </el-dialog>

    <!-- 开始私聊对话框 -->
    <el-dialog v-model="showPrivateChatDialog" title="开始私聊" width="400px">
      <div class="private-chat-form">
        <el-form label-width="80px">
          <el-form-item label="选择用户">
            <el-select
              v-model="selectedUserId"
              placeholder="请选择要私聊的用户"
              style="width: 100%"
              filterable
              remote
              :remote-method="searchUsers"
              :loading="searchingUsers"
            >
              <el-option
                v-for="user in availableUsers"
                :key="user.id"
                :label="`${user.username} (${user.nickname || '无昵称'})`"
                :value="user.id"
              >
                <div class="user-option">
                  <span class="user-name">{{ user.username }}</span>
                  <span class="user-nickname">{{ user.nickname || '无昵称' }}</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item label="快速选择">
            <div class="quick-users">
              <el-tag
                v-for="user in recentUsers"
                :key="user.id"
                @click="selectedUserId = user.id"
                class="user-tag"
                :class="{ active: selectedUserId === user.id }"
              >
                {{ user.username }}
              </el-tag>
            </div>
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="showPrivateChatDialog = false">取消</el-button>
        <el-button type="primary" @click="startPrivateChat" :disabled="!selectedUserId">
          开始私聊
        </el-button>
      </template>
    </el-dialog>

    <!-- 加入聊天室对话框 -->
    <el-dialog v-model="showJoinRoomDialog" title="加入聊天室" width="500px">
      <div class="join-room-content">
        <el-tabs v-model="joinRoomTab" class="join-room-tabs">
          <!-- 搜索聊天室 -->
          <el-tab-pane label="搜索聊天室" name="search">
            <div class="search-room-section">
              <el-input
                v-model="roomSearchQuery"
                placeholder="搜索聊天室名称..."
                prefix-icon="Search"
                @input="searchRooms"
                clearable
              />

              <div class="search-results" v-if="roomSearchResults.length > 0">
                <div
                  v-for="room in roomSearchResults"
                  :key="room.id"
                  class="room-search-item"
                  @click="selectRoomToJoin(room)"
                >
                  <div class="room-avatar" :class="getRoomAvatarClass(room)">
                    <div class="default-avatar">
                      {{ room.name.charAt(0).toUpperCase() }}
                    </div>
                    <div class="room-type-badge" :class="getRoomTypeBadgeClass(room)">
                      <el-icon class="type-icon">
                        <ChatDotRound v-if="room.room_type === 'public'" />
                        <Lock v-else-if="room.room_type === 'group'" />
                        <Message v-else-if="room.room_type === 'private'" />
                        <Promotion v-else />
                      </el-icon>
                    </div>
                  </div>

                  <div class="room-info">
                    <div class="room-name-container">
                      <span class="room-name">{{ room.name }}</span>
                      <span class="room-type-text" :class="getRoomTypeTextClass(room)">
                        {{ getRoomTypeText(room) }}
                      </span>
                    </div>
                    <div class="room-description">{{ room.description || '暂无描述' }}</div>
                    <div class="room-stats">
                      <span>{{ room.member_count }} 成员</span>
                    </div>
                  </div>

                  <div class="join-action">
                    <el-button
                      v-if="room.room_type === 'public'"
                      type="primary"
                      size="small"
                      @click.stop="joinPublicRoom(room)"
                    >
                      直接加入
                    </el-button>
                    <el-button
                      v-else
                      type="warning"
                      size="small"
                      @click.stop="showJoinPrivateRoomDialog(room)"
                    >
                      申请加入
                    </el-button>
                  </div>
                </div>
              </div>

              <div v-else-if="roomSearchQuery && !searchingRooms" class="no-results">
                <el-empty description="未找到相关聊天室" />
              </div>
            </div>
          </el-tab-pane>

          <!-- 邀请码加入 -->
          <el-tab-pane label="邀请码加入" name="invite">
            <div class="invite-code-section">
              <el-form :model="inviteCodeForm" label-width="80px">
                <el-form-item label="邀请码">
                  <el-input
                    v-model="inviteCodeForm.code"
                    placeholder="请输入邀请码"
                    clearable
                  />
                </el-form-item>
              </el-form>

              <div class="invite-code-actions">
                <el-button @click="showJoinRoomDialog = false">取消</el-button>
                <el-button
                  type="primary"
                  @click="joinByInviteCode"
                  :loading="joiningByInvite"
                  :disabled="!inviteCodeForm.code.trim()"
                >
                  加入
                </el-button>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>

    <!-- 申请加入私密聊天室对话框 -->
    <el-dialog v-model="showJoinPrivateDialog" title="申请加入私密聊天室" width="400px">
      <div v-if="selectedRoomToJoin" class="join-private-content">
        <div class="room-info-display">
          <div class="room-avatar" :class="getRoomAvatarClass(selectedRoomToJoin)">
            <div class="default-avatar">
              {{ selectedRoomToJoin.name.charAt(0).toUpperCase() }}
            </div>
          </div>
          <div class="room-details">
            <h4>{{ selectedRoomToJoin.name }}</h4>
            <p>{{ selectedRoomToJoin.description || '暂无描述' }}</p>
            <span class="room-type-text" :class="getRoomTypeTextClass(selectedRoomToJoin)">
              {{ getRoomTypeText(selectedRoomToJoin) }}
            </span>
          </div>
        </div>

        <el-form :model="joinRequestForm" label-width="80px">
          <el-form-item label="申请消息">
            <el-input
              v-model="joinRequestForm.message"
              type="textarea"
              :rows="3"
              placeholder="请输入申请理由（可选）"
              maxlength="200"
              show-word-limit
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="showJoinPrivateDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="submitJoinRequest"
          :loading="submittingRequest"
        >
          发送申请
        </el-button>
      </template>
    </el-dialog>

    <!-- 聊天室信息对话框 -->
    <el-dialog v-model="showRoomInfoDialog" title="聊天室信息" width="500px">
      <div v-if="currentRoom" class="room-info-dialog">
        <!-- 基本信息 -->
        <div class="room-basic-info">
          <div class="room-avatar large" :class="getRoomAvatarClass(currentRoom)">
            <img v-if="currentRoom.avatar" :src="currentRoom.avatar" :alt="currentRoom.name" />
            <div v-else class="default-avatar">
              {{ currentRoom.name.charAt(0).toUpperCase() }}
            </div>
            <div class="room-type-badge" :class="getRoomTypeBadgeClass(currentRoom)">
              <el-icon class="type-icon">
                <ChatDotRound v-if="currentRoom.room_type === 'public'" />
                <Lock v-else-if="currentRoom.room_type === 'group'" />
                <Message v-else-if="currentRoom.room_type === 'private'" />
                <Promotion v-else />
              </el-icon>
            </div>
          </div>

          <div class="room-info-text">
            <h3>{{ currentRoom.name }}</h3>
            <p class="room-description">{{ currentRoom.description || '暂无描述' }}</p>
            <div class="room-meta">
              <span class="room-type-text" :class="getRoomTypeTextClass(currentRoom)">
                {{ getRoomTypeText(currentRoom) }}
              </span>
              <span class="room-stats">{{ currentRoom.member_count }} 名成员</span>
            </div>
          </div>
        </div>

        <!-- 功能区域 -->
        <div class="room-actions">
          <!-- 邀请码功能（仅私密聊天室显示） -->
          <div v-if="currentRoom.room_type === 'group'" class="action-section">
            <h4>邀请码</h4>
            <div v-if="roomInviteCode" class="invite-code-section">
              <div class="invite-code-display">
                <el-input
                  :value="roomInviteCode.invite_code"
                  readonly
                  class="invite-code-input"
                >
                  <template #append>
                    <el-button @click="copyInviteCode" type="primary">复制</el-button>
                  </template>
                </el-input>
              </div>
              <div class="invite-code-info">
                <span v-if="roomInviteCode.expires_at" class="expire-time">
                  过期时间: {{ formatDateTime(roomInviteCode.expires_at) }}
                </span>
                <span v-if="roomInviteCode.is_expired" class="expired-tag">已过期</span>
              </div>
              <div class="invite-code-actions">
                <el-button @click="refreshInviteCode" :loading="refreshingCode" size="small">
                  刷新邀请码
                </el-button>
              </div>
            </div>
            <div v-else class="no-invite-code">
              <p>暂无邀请码</p>
              <el-button @click="generateInviteCode" :loading="generatingCode" type="primary" size="small">
                生成邀请码
              </el-button>
            </div>
          </div>

          <!-- 申请加入功能（非成员显示） -->
          <div v-if="!isCurrentRoomMember && currentRoom.room_type === 'group'" class="action-section">
            <h4>申请加入</h4>
            <el-form :model="joinRequestForm" label-width="80px">
              <el-form-item label="申请消息">
                <el-input
                  v-model="joinRequestForm.message"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入申请理由（可选）"
                  maxlength="200"
                  show-word-limit
                />
              </el-form-item>
            </el-form>
            <el-button
              @click="submitJoinRequestFromInfo"
              :loading="submittingRequest"
              type="primary"
            >
              发送申请
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 聊天室信息侧边栏 -->
    <el-drawer v-model="showRoomInfo" title="聊天室信息" size="400px">
      <div v-if="currentRoom" class="room-info-content">
        <div class="room-header">
          <div class="room-avatar large">
            <img v-if="currentRoom.avatar" :src="currentRoom.avatar" :alt="currentRoom.name" />
            <div v-else class="default-avatar">
              {{ currentRoom.name.charAt(0).toUpperCase() }}
            </div>
          </div>
          <h3>{{ currentRoom.name }}</h3>
          <p>{{ currentRoom.description || '暂无描述' }}</p>
        </div>
        
        <div class="room-stats">
          <div class="stat-item">
            <span class="label">成员数量</span>
            <span class="value">{{ currentRoom.member_count }}</span>
          </div>
          <div class="stat-item">
            <span class="label">创建时间</span>
            <span class="value">{{ formatDate(currentRoom.created_at) }}</span>
          </div>
          <div class="stat-item">
            <span class="label">类型</span>
            <span class="value">{{ getRoomTypeName(currentRoom.room_type) }}</span>
          </div>
        </div>
      </div>
    </el-drawer>
    
    <!-- 成员列表侧边栏 -->
    <el-drawer v-model="showMemberList" title="成员列表" size="400px">
      <div class="member-list">
        <div
          v-for="member in currentRoom?.members || []"
          :key="member.id"
          class="member-item"
        >
          <div class="member-avatar">
            <img v-if="member.avatar" :src="member.avatar" :alt="member.username" />
            <div v-else class="default-avatar">
              {{ member.username.charAt(0).toUpperCase() }}
            </div>
            <div class="online-indicator" :class="{ online: member.is_online }"></div>
          </div>
          
          <div class="member-info">
            <div class="member-name">{{ member.nickname || member.username }}</div>
            <div class="member-role">{{ getRoleName(member.role) }}</div>
          </div>
          
          <div class="member-actions">
            <el-tag v-if="member.role === 'admin'" type="warning" size="small">管理员</el-tag>
            <el-tag v-if="member.is_muted" type="danger" size="small">已静音</el-tag>
          </div>
        </div>
      </div>
    </el-drawer>

    <!-- 表情选择器 -->
    <el-dialog v-model="showEmojiPicker" title="选择表情" width="40%" :show-close="false">
      <div class="emoji-picker">
        <div class="emoji-categories">
          <el-button
            v-for="category in emojiCategories"
            :key="category.name"
            @click="selectedEmojiCategory = category.name"
            :type="selectedEmojiCategory === category.name ? 'primary' : ''"
            text
          >
            {{ category.icon }}
          </el-button>
        </div>

        <div class="emoji-grid">
          <span
            v-for="emoji in currentEmojis"
            :key="emoji"
            class="emoji-item"
            @click="selectEmoji(emoji)"
          >
            {{ emoji }}
          </span>
        </div>
      </div>

      <template #footer>
        <el-button @click="showEmojiPicker = false">取消</el-button>
      </template>
    </el-dialog>


  </div>

  <!-- 聊天室右键菜单 -->
  <div
    v-if="roomContextMenu.visible"
    class="context-menu"
    :style="{ left: roomContextMenu.x + 'px', top: roomContextMenu.y + 'px' }"
    @click.stop
    @contextmenu.prevent
  >
    <div class="context-menu-item" @click="selectRoom(roomContextMenu.room)">
      <el-icon><ChatDotRound /></el-icon>
      <span>打开聊天室</span>
    </div>

    <div class="context-menu-item" @click="togglePinRoom(roomContextMenu.room)">
      <el-icon><Star /></el-icon>
      <span>{{ pinnedRooms.has(roomContextMenu.room?.id) ? '取消置顶' : '置顶聊天室' }}</span>
    </div>

    <div v-if="canManageRoom(roomContextMenu.room)" class="context-menu-divider"></div>

    <div
      v-if="canManageRoom(roomContextMenu.room) && roomContextMenu.room?.room_type !== 'private'"
      class="context-menu-item"
      @click="editRoom(roomContextMenu.room)"
    >
      <el-icon><Edit /></el-icon>
      <span>编辑聊天室</span>
    </div>

<!--    <div-->
<!--      v-if="canManageRoom(roomContextMenu.room)"-->
<!--      class="context-menu-item"-->
<!--      @click="editRoom(roomContextMenu.room)"-->
<!--    >-->
<!--      <el-icon><Edit /></el-icon>-->
<!--      <span>编辑聊天室</span>-->
<!--    </div>-->

    <div
      v-if="canManageRoom(roomContextMenu.room) && roomContextMenu.room?.room_type === 'group'"
      class="context-menu-item"
      @click="showRoomSettings(roomContextMenu.room)">
      <el-icon><Setting /></el-icon>
      <span>聊天室设置</span>
    </div>

    <div
      v-if="canManageRoom(roomContextMenu.room) && roomContextMenu.room?.room_type !== 'private'"
      class="context-menu-item"
      @click="showMemberManagement(roomContextMenu.room)"
    >
      <el-icon><User /></el-icon>
      <span>成员管理</span>
    </div>

    <div
      v-if="canManageRoom(roomContextMenu.room)"
      class="context-menu-item danger"
      @click="deleteRoom(roomContextMenu.room)"
    >
      <el-icon><Delete /></el-icon>
      <span>{{ roomContextMenu.room?.room_type === 'private' ? '删除私聊' : '删除聊天室' }}</span>
    </div>

    <div class="context-menu-divider"></div>

    <div class="context-menu-item" @click="markRoomAsRead(roomContextMenu.room)">
      <el-icon><Check /></el-icon>
      <span>标记为已读</span>
    </div>

    <div class="context-menu-item" @click="toggleRoomMute(roomContextMenu.room)">
      <el-icon><Bell /></el-icon>
      <span>{{ roomContextMenu.room?.is_muted ? '取消静音' : '静音通知' }}</span>
    </div>

    <div class="context-menu-divider"></div>

    <div
      class="context-menu-item danger"
      @click="leaveRoom(roomContextMenu.room)"
    >
      <el-icon><Close /></el-icon>
      <span>{{ isRoomCreator(roomContextMenu.room) ? '解散群聊' : '退出群聊' }}</span>
    </div>
  </div>

  <!-- 消息右键菜单 -->
  <div
    v-if="messageContextMenu.show"
    class="context-menu"
    :style="{ left: messageContextMenu.x + 'px', top: messageContextMenu.y + 'px' }"
    @click.stop
    @contextmenu.prevent
  >
    <div class="context-menu-item" @click="replyToMessage(messageContextMenu.message)">
      <el-icon><ChatLineRound /></el-icon>
      <span>回复</span>
    </div>

    <div class="context-menu-item" @click="copyMessage(messageContextMenu.message)">
      <el-icon><CopyDocument /></el-icon>
      <span>复制</span>
    </div>

    <div class="context-menu-item" @click="reactToMessage(messageContextMenu.message)">
      <el-icon><Star /></el-icon>
      <span>表情反应</span>
    </div>

    <div
      v-if="canManageRoom(currentRoom)"
      class="context-menu-item"
      @click="togglePinMessage(messageContextMenu.message)"
    >
      <el-icon><Star /></el-icon>
      <span>{{ messageContextMenu.message?.is_pinned ? '取消置顶' : '置顶消息' }}</span>
    </div>

    <div v-if="canEditMessage(messageContextMenu.message)" class="context-menu-divider"></div>

    <div
      v-if="canEditMessage(messageContextMenu.message)"
      class="context-menu-item"
      @click="editMessage(messageContextMenu.message)"
    >
      <el-icon><Edit /></el-icon>
      <span>编辑</span>
    </div>

    <div
      v-if="canDeleteMessage(messageContextMenu.message)"
      class="context-menu-item danger"
      @click="deleteMessage(messageContextMenu.message)"
    >
      <el-icon><Delete /></el-icon>
      <span>删除</span>
    </div>
  </div>

  <!-- 成员管理对话框 -->
  <el-dialog
    v-model="showMemberManagementDialog"
    title="成员管理"
    width="600px"
    :close-on-click-modal="false"
  >
    <div class="member-management">
      <div class="member-stats">
        <el-statistic title="总成员数" :value="roomMembers.length" />
        <el-statistic title="在线成员" :value="onlineMembers" />
      </div>

      <div class="member-search">
        <el-input
          v-model="memberSearchQuery"
          placeholder="搜索成员..."
          prefix-icon="Search"
          clearable
        />
        <el-button
          v-if="canManageRoom(currentRoom)"
          type="primary"
          @click="showInviteUserDialog = true"
          style="margin-left: 12px;"
        >
          <el-icon><Plus /></el-icon>
          邀请用户
        </el-button>
      </div>

      <div class="member-list">
        <div
          v-for="member in filteredMembers"
          :key="member.user_id"
          class="member-item"
        >
          <div class="member-info">
            <el-avatar :size="40" :src="member.avatar">
              {{ member.nickname?.[0] || member.username[0] }}
            </el-avatar>
            <div class="member-details">
              <div class="member-name">
                {{ member.nickname || member.username }}
                <el-tag v-if="member.role === 'creator'" type="danger" size="small">创建者</el-tag>
                <el-tag v-else-if="member.role === 'admin'" type="warning" size="small">管理员</el-tag>
              </div>
              <div class="member-meta">
                <span class="join-time">{{ formatDateTime(member.joined_at) }} 加入</span>
                <el-tag v-if="member.is_muted" type="info" size="small">已禁言</el-tag>
              </div>
            </div>
          </div>

          <div class="member-actions" v-if="canManageRoom(currentRoom) && member.role !== 'creator'">
            <el-dropdown trigger="click">
              <el-button text>
                <el-icon><More /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                    v-if="member.user_id !== userStore.user?.id"
                    @click="kickMember(member)"
                  >
                    <el-icon><Delete /></el-icon>
                    踢出聊天室
                  </el-dropdown-item>
                  <el-dropdown-item @click="toggleMuteMember(member)">
                    <el-icon><Bell /></el-icon>
                    {{ member.is_muted ? '取消禁言' : '禁言' }}
                  </el-dropdown-item>
                  <el-dropdown-item
                    v-if="member.role !== 'admin' && member.user_id !== userStore.user?.id && isRoomCreator(currentRoom)"
                    @click="promoteToAdmin(member)"
                  >
                    <el-icon><Star /></el-icon>
                    设为管理员
                  </el-dropdown-item>
                  <el-dropdown-item
                    v-if="member.role === 'admin' && member.user_id !== userStore.user?.id && isRoomCreator(currentRoom)"
                    @click="demoteFromAdmin(member)"
                  >
                    <el-icon><User /></el-icon>
                    取消管理员
                  </el-dropdown-item>
                  <el-dropdown-item
                    v-if="member.role !== 'creator' && member.user_id !== userStore.user?.id && isRoomCreator(currentRoom)"
                    @click="transferOwnership(member)"
                  >
                    <el-icon><Crown /></el-icon>
                    转让群主
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="showMemberManagementDialog = false">关闭</el-button>
    </template>
  </el-dialog>

  <!-- 邀请用户对话框 -->
  <el-dialog
    v-model="showInviteUserDialog"
    title="邀请用户"
    width="500px"
    :close-on-click-modal="false"
  >
    <div class="invite-user-content">
      <el-form :model="inviteUserForm" label-width="80px">
        <el-form-item label="搜索用户">
          <el-input
            v-model="userSearchQuery"
            placeholder="输入用户名或昵称搜索..."
            @input="searchUsersForInvite"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="搜索结果" v-if="searchedUsers.length > 0">
          <div class="user-search-results">
            <div
              v-for="user in searchedUsers"
              :key="user.id"
              class="user-search-item"
              @click="selectUserToInvite(user)"
            >
              <el-avatar :size="32" :src="user.avatar">
                {{ user.nickname?.[0] || user.username[0] }}
              </el-avatar>
              <div class="user-info">
                <div class="user-name">{{ user.nickname || user.username }}</div>
                <div class="user-username">@{{ user.username }}</div>
              </div>
              <el-button size="small" type="primary">选择</el-button>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="选中用户" v-if="inviteUserForm.selectedUser">
          <div class="selected-user">
            <el-avatar :size="40" :src="inviteUserForm.selectedUser.avatar">
              {{ inviteUserForm.selectedUser.nickname?.[0] || inviteUserForm.selectedUser.username[0] }}
            </el-avatar>
            <div class="user-info">
              <div class="user-name">{{ inviteUserForm.selectedUser.nickname || inviteUserForm.selectedUser.username }}</div>
              <div class="user-username">@{{ inviteUserForm.selectedUser.username }}</div>
            </div>
            <el-button size="small" @click="inviteUserForm.selectedUser = null">取消选择</el-button>
          </div>
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <el-button @click="showInviteUserDialog = false">取消</el-button>
      <el-button
        type="primary"
        @click="inviteUser"
        :disabled="!inviteUserForm.selectedUser"
        :loading="invitingUser"
      >
        邀请
      </el-button>
    </template>
  </el-dialog>

  <!-- 退出聊天室对话框 -->
  <el-dialog
    v-model="showLeaveRoomDialog"
    title="退出聊天室"
    width="400px"
    :close-on-click-modal="false"
  >
    <div class="leave-room-content">
      <el-icon class="warning-icon"><WarningFilled /></el-icon>
      <p v-if="isRoomCreator(currentRoom)">
        您是群主，退出后聊天室将被解散，所有消息和数据将被删除。
      </p>
      <p v-else>
        确定要退出聊天室吗？
      </p>
    </div>

    <template #footer>
      <el-button @click="showLeaveRoomDialog = false">取消</el-button>
      <el-button
        type="danger"
        @click="confirmLeaveRoom"
        :loading="leavingRoom"
      >
        {{ isRoomCreator(currentRoom) ? '解散群聊' : '退出群聊' }}
      </el-button>
    </template>
  </el-dialog>

  <!-- 编辑聊天室对话框 -->
  <el-dialog
    v-model="showEditRoomDialog"
    title="编辑聊天室"
    width="600px"
    :close-on-click-modal="false"
  >
    <el-form :model="editRoomForm" label-width="100px" v-if="editRoomForm">
      <el-form-item label="聊天室名称">
        <el-input v-model="editRoomForm.name" placeholder="请输入聊天室名称" />
      </el-form-item>

      <el-form-item label="聊天室描述">
        <el-input
          v-model="editRoomForm.description"
          type="textarea"
          :rows="3"
          placeholder="请输入聊天室描述"
        />
      </el-form-item>

      <el-form-item label="最大成员数">
        <el-input-number v-model="editRoomForm.max_members" :min="2" :max="10000" />
      </el-form-item>

      <div v-if="editRoomForm.room_type === 'group'" class="advanced-settings">
        <h4>高级设置</h4>

        <el-form-item label="搜索设置">
          <el-switch
            v-model="editRoomForm.allow_search"
            active-text="允许被搜索"
            inactive-text="不允许搜索"
          />
        </el-form-item>

        <el-form-item label="邀请码">
          <el-switch
            v-model="editRoomForm.enable_invite_code"
            active-text="启用邀请码"
            inactive-text="禁用邀请码"
          />
        </el-form-item>

        <el-form-item label="成员邀请">
          <el-switch
            v-model="editRoomForm.allow_member_invite"
            active-text="允许成员邀请"
            inactive-text="仅管理员邀请"
          />
        </el-form-item>

        <el-form-item label="聊天室状态">
          <el-switch
            v-model="editRoomForm.is_active"
            active-text="活跃"
            inactive-text="已归档"
          />
        </el-form-item>
      </div>
    </el-form>

    <template #footer>
      <el-button @click="showEditRoomDialog = false">取消</el-button>
      <el-button
        type="primary"
        @click="updateRoom"
        :loading="updatingRoom"
      >
        保存
      </el-button>
    </template>
  </el-dialog>

  <!-- 聊天室高级设置对话框 -->
  <el-dialog
    v-model="showRoomSettingsDialog"
    title="聊天室高级设置"
    width="700px"
    :close-on-click-modal="false"
  >
    <el-form :model="roomSettingsForm" label-width="120px" v-if="roomSettingsForm">
      <el-tabs>
        <el-tab-pane label="统计信息" name="statistics">
          <div class="room-statistics" v-if="roomStatistics">
            <el-row :gutter="20">
              <el-col :span="6">
                <el-statistic title="总消息数" :value="roomStatistics.total_messages" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="今日消息" :value="roomStatistics.today_messages" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="总成员数" :value="roomStatistics.total_members" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="活跃成员" :value="roomStatistics.active_members" />
              </el-col>
            </el-row>

            <el-row :gutter="20" style="margin-top: 20px;">
              <el-col :span="6">
                <el-statistic title="置顶消息" :value="roomStatistics.pinned_messages" />
              </el-col>
              <el-col :span="18">
                <div class="top-users">
                  <h4>最活跃用户</h4>
                  <div v-for="user in roomStatistics.top_users" :key="user.user_id" class="top-user-item">
                    <span class="user-name">{{ user.nickname || user.username }}</span>
                    <span class="message-count">{{ user.message_count }} 条消息</span>
                  </div>
                </div>
              </el-col>
            </el-row>

            <el-row style="margin-top: 20px;">
              <el-col :span="24">
                <div class="room-info">
                  <p><strong>创建时间：</strong>{{ formatDateTime(roomStatistics.created_at) }}</p>
                  <p v-if="roomStatistics.last_message_at">
                    <strong>最后消息：</strong>{{ formatDateTime(roomStatistics.last_message_at) }}
                  </p>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <el-tab-pane label="基本设置" name="basic">
          <el-form-item label="聊天室名称">
            <el-input v-model="roomSettingsForm.name" placeholder="请输入聊天室名称" />
          </el-form-item>

          <el-form-item label="聊天室描述">
            <el-input
              v-model="roomSettingsForm.description"
              type="textarea"
              :rows="3"
              placeholder="请输入聊天室描述"
            />
          </el-form-item>

          <el-form-item label="最大成员数">
            <el-input-number v-model="roomSettingsForm.max_members" :min="2" :max="10000" />
          </el-form-item>

          <el-form-item label="聊天室状态">
            <el-switch
              v-model="roomSettingsForm.is_active"
              active-text="活跃"
              inactive-text="已归档"
            />
          </el-form-item>
        </el-tab-pane>

        <el-tab-pane label="权限设置" name="permissions">
          <el-form-item label="搜索设置">
            <el-switch
              v-model="roomSettingsForm.allow_search"
              active-text="允许被搜索"
              inactive-text="不允许搜索"
            />
          </el-form-item>

          <el-form-item label="邀请码">
            <el-switch
              v-model="roomSettingsForm.enable_invite_code"
              active-text="启用邀请码"
              inactive-text="禁用邀请码"
            />
          </el-form-item>

          <el-form-item label="成员邀请">
            <el-switch
              v-model="roomSettingsForm.allow_member_invite"
              active-text="允许成员邀请"
              inactive-text="仅管理员邀请"
            />
          </el-form-item>

          <el-form-item label="文件上传">
            <el-switch
              v-model="roomSettingsForm.allow_file_upload"
              active-text="允许上传文件"
              inactive-text="禁止上传文件"
            />
          </el-form-item>

          <el-form-item label="文件大小限制" v-if="roomSettingsForm.allow_file_upload">
            <el-input-number
              v-model="roomSettingsForm.max_file_size"
              :min="1"
              :max="100"
              :step="1"
            />
            <span style="margin-left: 8px;">MB</span>
          </el-form-item>
        </el-tab-pane>

        <el-tab-pane label="消息设置" name="messages">
          <el-form-item label="自动删除消息">
            <el-switch
              v-model="roomSettingsForm.auto_delete_messages"
              active-text="启用自动删除"
              inactive-text="永久保存"
            />
          </el-form-item>

          <el-form-item label="消息保留天数" v-if="roomSettingsForm.auto_delete_messages">
            <el-input-number
              v-model="roomSettingsForm.message_retention_days"
              :min="1"
              :max="365"
              :step="1"
            />
            <span style="margin-left: 8px;">天</span>
          </el-form-item>

          <el-form-item label="欢迎消息">
            <el-input
              v-model="roomSettingsForm.welcome_message"
              type="textarea"
              :rows="3"
              placeholder="新成员加入时显示的欢迎消息"
            />
          </el-form-item>

          <el-form-item label="聊天室规则">
            <el-input
              v-model="roomSettingsForm.rules"
              type="textarea"
              :rows="4"
              placeholder="聊天室规则和说明"
            />
          </el-form-item>
        </el-tab-pane>
      </el-tabs>
    </el-form>

    <template #footer>
      <el-button @click="showRoomSettingsDialog = false">取消</el-button>
      <el-button
        type="primary"
        @click="updateRoomSettings"
        :loading="updatingRoomSettings"
      >
        保存设置
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, Menu, InfoFilled, User, Delete, Document, ChatDotRound,
  Star, Edit, Close, Paperclip, Promotion, DocumentCopy, More, Bell,
  Picture, Check, ChatLineRound, CopyDocument, Lock, Message, Setting,
   WarningFilled
} from '@element-plus/icons-vue' //Crown,
import { useUserStore } from '@/stores/user'
import axios from '@/utils/axios'

// 响应式数据
const userStore = useUserStore()
const isMobile = ref(window.innerWidth < 768)
const showSidebar = ref(!isMobile.value)

// 聊天室相关
const rooms = ref([])
const currentRoom = ref(null)
const searchQuery = ref('')
const showCreateRoomDialog = ref(false)
const showPrivateChatDialog = ref(false)
const showJoinRoomDialog = ref(false)
const showJoinPrivateDialog = ref(false)
const showRoomInfoDialog = ref(false)
const creating = ref(false)

// 加入聊天室相关
const joinRoomTab = ref('search')
const roomSearchQuery = ref('')
const roomSearchResults = ref([])
const searchingRooms = ref(false)
const selectedRoomToJoin = ref(null)

// 邀请码加入
const inviteCodeForm = reactive({
  code: ''
})
const joiningByInvite = ref(false)

// 申请加入
const joinRequestForm = reactive({
  message: ''
})
const submittingRequest = ref(false)
const processingRequest = ref(false)

// 聊天室信息
const roomInviteCode = ref(null)
const refreshingCode = ref(false)
const generatingCode = ref(false)
const isCurrentRoomMember = computed(() => {
  if (!currentRoom.value || !userStore.user) return false
  // 这里可以根据实际情况判断用户是否是当前聊天室成员
  return true // 暂时返回true，实际应该检查成员列表
})

// 置顶功能
const pinnedRooms = ref(new Set())
const pinnedMessagesInRoom = ref([])
const showPinnedMessages = ref(true)

// 当前聊天室的置顶消息（最新的一条）
const currentPinnedMessage = computed(() => {
  if (!currentRoom.value) return null

  // 从当前消息列表中找到置顶的消息
  const pinnedMessages = messages.value.filter(msg => msg.is_pinned)

  // 返回最新置顶的消息
  if (pinnedMessages.length > 0) {
    return pinnedMessages.sort((a, b) => new Date(b.pinned_at || b.created_at) - new Date(a.pinned_at || a.created_at))[0]
  }

  return null
})

// 成员管理
const showMemberManagementDialog = ref(false)
const roomMembers = ref([])
const memberSearchQuery = ref('')
const onlineMembers = computed(() => {
  // 这里可以根据实际在线状态计算
  return roomMembers.value.length
})

// 邀请用户
const showInviteUserDialog = ref(false)
const inviteUserForm = reactive({
  selectedUser: null
})
const userSearchQuery = ref('')
const searchedUsers = ref([])
const invitingUser = ref(false)

// 退出聊天室
const showLeaveRoomDialog = ref(false)
const leavingRoom = ref(false)

// 编辑聊天室
const showEditRoomDialog = ref(false)
const editRoomForm = ref(null)
const updatingRoom = ref(false)

// 聊天室设置
const showRoomSettingsDialog = ref(false)
const roomSettingsForm = ref(null)
const updatingRoomSettings = ref(false)
const roomStatistics = ref(null)

const filteredMembers = computed(() => {
  if (!memberSearchQuery.value.trim()) {
    return roomMembers.value
  }

  const query = memberSearchQuery.value.toLowerCase()
  return roomMembers.value.filter(member =>
    (member.nickname || member.username).toLowerCase().includes(query) ||
    member.username.toLowerCase().includes(query)
  )
})

// 私聊相关
const selectedUserId = ref(null)
const availableUsers = ref([])
const recentUsers = ref([])
const searchingUsers = ref(false)

// 消息相关
const messages = ref([])
const messageInput = ref('')
const replyingTo = ref(null)
const editingMessage = ref(null)
const typingUsers = ref([])
const messagesContainer = ref(null)
const selectedMessageForReaction = ref(null)

// 文件上传相关
const uploading = ref(false)
const uploadProgress = ref(0)

// 侧边栏
const showRoomInfo = ref(false)
const showMemberList = ref(false)
const showEmojiPicker = ref(false)

// 表情选择器
const selectedEmojiCategory = ref('smileys')
const emojiCategories = ref([
  { name: 'smileys', icon: '😀', emojis: ['😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣', '😊', '😇', '🙂', '🙃', '😉', '😌', '😍', '🥰', '😘', '😗', '😙', '😚', '😋', '😛', '😝', '😜', '🤪', '🤨', '🧐', '🤓', '😎', '🤩', '🥳'] },
  { name: 'gestures', icon: '👍', emojis: ['👍', '👎', '👌', '🤌', '🤏', '✌️', '🤞', '🤟', '🤘', '🤙', '👈', '👉', '👆', '🖕', '👇', '☝️', '👋', '🤚', '🖐️', '✋', '🖖', '👏', '🙌', '🤲', '🤝', '🙏'] },
  { name: 'hearts', icon: '❤️', emojis: ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔', '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟'] },
  { name: 'animals', icon: '🐶', emojis: ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯', '🦁', '🐮', '🐷', '🐽', '🐸', '🐵', '🙈', '🙉', '🙊', '🐒', '🐔', '🐧', '🐦', '🐤', '🐣', '🐥', '🦆', '🦅', '🦉', '🦇'] }
])

// WebSocket
let websocket = null
let globalWebSocket = null
let typingTimer = null
const onlineCount = ref(0)
const isGlobalConnected = ref(false)

// 聊天室右键菜单
const roomContextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  room: null
})

// 消息右键菜单
const messageContextMenu = reactive({
  show: false,
  x: 0,
  y: 0,
  message: null
})

// 新聊天室表单
const newRoom = reactive({
  name: '',
  description: '',
  room_type: 'public',
  is_public: true,
  max_members: 500,
  allow_search: false,  // 默认不允许搜索
  enable_invite_code: true,  // 默认启用邀请码
  allow_member_invite: true,
  allow_member_modify_info: false,
  message_history_visible: true
})

// 计算属性
const filteredRooms = computed(() => {
  if (!searchQuery.value) return rooms.value
  return rooms.value.filter(room =>
    room.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const currentEmojis = computed(() => {
  const category = emojiCategories.value.find(cat => cat.name === selectedEmojiCategory.value)
  return category ? category.emojis : []
})

// 方法
const loadRooms = async () => {
  try {
    const response = await axios.get('/api/modern-chat/rooms')
    rooms.value = response.data
  } catch (error) {
    console.error('加载聊天室失败:', error)
    ElMessage.error('加载聊天室失败')
  }
}

const selectRoom = async (room) => {
  if (currentRoom.value?.id === room.id) return

  // 断开之前的WebSocket连接
  if (websocket) {
    websocket.close()
    websocket = null
  }

  currentRoom.value = room
  messages.value = []

  // 清除未读消息计数
  const roomIndex = rooms.value.findIndex(r => r.id === room.id)
  if (roomIndex !== -1) {
    rooms.value[roomIndex].unread_count = 0
  }

  // 加载聊天室详情
  await loadRoomDetails(room.id)

  // 加载消息和置顶消息
  await Promise.all([
    loadMessages(room.id),
    loadPinnedMessages()
  ])

  // 确保用户已登录
  if (userStore.isLoggedIn) {
    // 标记消息为已读
    markMessagesAsRead(room.id)
  } else {
    ElMessage.error('请先登录')
    return
  }

  // 移动端自动隐藏侧边栏
  if (isMobile.value) {
    showSidebar.value = false
  }
}

const loadRoomDetails = async (roomId) => {
  try {
    const response = await axios.get(`/api/modern-chat/rooms/${roomId}`)
    currentRoom.value = response.data
  } catch (error) {
    console.error('加载聊天室详情失败:', error)
  }
}

const loadMessages = async (roomId) => {
  try {
    const response = await axios.get(`/api/modern-chat/rooms/${roomId}/messages`)
    messages.value = response.data.messages

    // 滚动到底部
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('加载消息失败:', error)
    ElMessage.error('加载消息失败')
  }
}

const connectGlobalWebSocket = () => {
  // 如果已经有连接，先关闭
  if (globalWebSocket) {
    globalWebSocket.close()
    globalWebSocket = null
  }

  // 获取token
  let token = localStorage.getItem('access_token') ||
              localStorage.getItem('token') ||
              sessionStorage.getItem('access_token') ||
              sessionStorage.getItem('token')

  if (!token) {
    console.error('未找到认证token，无法建立全局WebSocket连接')
    return
  }

  try {
    // 建立全局WebSocket连接
    const wsUrl = `ws://${import.meta.env.VITE_HOST}:${import.meta.env.VITE_PORT}/api/global-ws`
    globalWebSocket = new WebSocket(wsUrl)

    globalWebSocket.onopen = () => {
      console.log('全局WebSocket连接已建立')

      // 发送认证消息
      globalWebSocket.send(JSON.stringify({
        type: 'auth',
        token: token
      }))
    }

    globalWebSocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        handleGlobalWebSocketMessage(message)
      } catch (error) {
        console.error('解析全局WebSocket消息失败:', error)
      }
    }

    globalWebSocket.onclose = (event) => {
      console.log('全局WebSocket连接已关闭', event.code, event.reason)
      isGlobalConnected.value = false

      // 如果不是主动关闭且用户仍然登录，尝试重连
      if (event.code !== 1000 && userStore.isLoggedIn && !event.wasClean) {
        setTimeout(() => {
          console.log('尝试重连全局WebSocket...')
          connectGlobalWebSocket()
        }, 3000)
      }
    }

    globalWebSocket.onerror = (error) => {
      console.error('全局WebSocket错误:', error)
      isGlobalConnected.value = false
    }
  } catch (error) {
    console.error('创建全局WebSocket连接失败:', error)
  }
}

const handleGlobalWebSocketMessage = (message) => {
  console.log('收到全局WebSocket消息:', message)

  switch (message.type) {
    case 'auth_response':
      if (message.data.success) {
        console.log('全局WebSocket认证成功')
        isGlobalConnected.value = true
        ElMessage.success('聊天系统连接成功')
      } else {
        console.error('全局WebSocket认证失败:', message.data.message)
        ElMessage.error('聊天系统连接失败')
      }
      break

    case 'room_created':
      handleRoomCreated(message.data)
      break

    case 'room_deleted':
      handleRoomDeleted(message.data)
      break

    case 'room_updated':
      handleRoomUpdated(message.data)
      break

    case 'private_room_created':
      handlePrivateRoomCreated(message.data)
      break

    case 'new_message':
      handleNewMessage(message.data)
      break

    case 'message_reaction':
      handleMessageReaction(message.data)
      break

    case 'system_notification':
      handleSystemNotification(message.data)
      break

    case 'user_online':
    case 'user_offline':
      handleUserStatusChange(message.data)
      break

    case 'error':
      console.error('全局WebSocket错误:', message.data.message)
      ElMessage.error(message.data.message)
      break

    default:
      console.log('未处理的全局WebSocket消息类型:', message.type)
  }
}





const sendMessage = async () => {
  if (!messageInput.value.trim() || !currentRoom.value) return

  try {
    if (editingMessage.value) {
      // 编辑消息 - 这里可以添加编辑消息的API调用
      ElMessage.info('编辑消息功能待实现')
      editingMessage.value = null
    } else {
      // 发送新消息
      const messageData = {
        content: messageInput.value.trim(),
        message_type: 'text',
        reply_to_id: replyingTo.value?.id
      }

      const response = await axios.post(
        `/api/modern-chat/rooms/${currentRoom.value.id}/messages`,
        messageData
      )

      if (response.data) {
        console.log('消息发送成功')

        // 立即将消息添加到当前聊天室的消息列表中，提供即时反馈
        const newMessage = {
          id: response.data.id,
          content: response.data.content,
          message_type: response.data.message_type,
          sender: {
            id: userStore.user.id,
            username: userStore.user.username,
            nickname: userStore.user.nickname,
            avatar: userStore.user.avatar
          },
          file_url: response.data.file_url,
          file_name: response.data.file_name,
          file_size: response.data.file_size,
          created_at: response.data.created_at,
          reply_to_id: response.data.reply_to_id,
          is_edited: false,
          is_deleted: false,
          is_pinned: false,
          edit_count: 0,
          read_count: 0,
          reactions: []
        }

        messages.value.push(newMessage)

        // 滚动到底部
        nextTick(() => {
          scrollToBottom()
        })

        // 更新聊天室列表中的最后消息
        const roomIndex = rooms.value.findIndex(r => r.id === currentRoom.value.id)
        if (roomIndex !== -1) {
          rooms.value[roomIndex].last_message = {
            content: newMessage.content,
            sender: newMessage.sender,
            created_at: newMessage.created_at
          }
          rooms.value[roomIndex].last_message_at = newMessage.created_at
        }
      }
    }

    messageInput.value = ''
    replyingTo.value = null

    // 停止输入状态
    sendTypingStatus(false)
  } catch (error) {
    console.error('发送消息失败:', error)
    if (error.response) {
      // 服务器返回了错误响应
      const status = error.response.status
      const message = error.response.data?.detail || error.response.data?.message || '发送消息失败'

      if (status === 403) {
        ElMessage.error('权限不足：' + message)
      } else if (status === 422) {
        ElMessage.error('数据验证失败：' + message)
      } else {
        ElMessage.error('发送消息失败：' + message)
      }
    } else if (error.request) {
      // 请求发送了但没有收到响应
      ElMessage.error('网络错误，请检查连接')
    } else {
      // 其他错误
      ElMessage.error('发送消息失败：' + error.message)
    }
  }
}

const handleTyping = () => {
  // 暂时禁用输入状态功能
  // TODO: 实现全局WebSocket的输入状态功能
}

const sendTypingStatus = (isTyping) => {
  // 暂时禁用输入状态功能，因为我们使用全局WebSocket
  // TODO: 实现全局WebSocket的输入状态功能
  console.log('输入状态:', isTyping)
}

const replyToMessage = (message) => {
  replyingTo.value = message
}

const cancelReply = () => {
  replyingTo.value = null
}

const cancelEdit = () => {
  editingMessage.value = null
  messageInput.value = ''
}





const selectEmoji = (emoji) => {
  if (selectedMessageForReaction.value) {
    toggleReaction(selectedMessageForReaction.value, emoji)
    selectedMessageForReaction.value = null
  } else {
    // 在输入框中插入表情
    messageInput.value += emoji
  }
  showEmojiPicker.value = false
}

const handleMessageReaction = (data) => {
  const { message_id, user_id, emoji, action } = data

  // 找到对应的消息
  const message = messages.value.find(m => m.id === message_id)
  if (!message) return

  // 初始化reactions数组
  if (!message.reactions) {
    message.reactions = []
  }

  // 查找现有的表情反应
  let reaction = message.reactions.find(r => r.emoji === emoji)

  if (action === 'added') {
    if (reaction) {
      // 增加计数
      reaction.count++
      if (user_id === userStore.user?.id) {
        reaction.user_reacted = true
      }
    } else {
      // 创建新的表情反应
      message.reactions.push({
        emoji: emoji,
        count: 1,
        user_reacted: user_id === userStore.user?.id
      })
    }
  } else if (action === 'removed') {
    if (reaction) {
      reaction.count--
      if (user_id === userStore.user?.id) {
        reaction.user_reacted = false
      }

      // 如果计数为0，移除这个表情反应
      if (reaction.count <= 0) {
        const index = message.reactions.indexOf(reaction)
        message.reactions.splice(index, 1)
      }
    }
  }
}

const handleRoomCreated = (data) => {
  const { room } = data

  // 检查是否已经存在这个聊天室
  const existingRoom = rooms.value.find(r => r.id === room.id)
  if (existingRoom) {
    return
  }

  // 添加新聊天室到列表
  const newRoom = {
    id: room.id,
    name: room.name,
    room_type: room.room_type,
    avatar: null,
    member_count: 1,
    last_message: null,
    last_message_at: null,
    unread_count: 0,
    is_muted: false,
    creator: room.creator
  }

  rooms.value.unshift(newRoom)

  // 显示通知
  ElNotification({
    title: '新聊天室',
    message: `${room.creator.username} 创建了新的${room.room_type === 'group' ? '群聊' : '频道'}: ${room.name}`,
    type: 'info',
    duration: 3000,
    position: 'top-right'
  })
}

const handleRoomDeleted = (data) => {
  const { room_id, room_name, deleted_by } = data

  // 从聊天室列表中移除
  const index = rooms.value.findIndex(r => r.id === room_id)
  if (index !== -1) {
    rooms.value.splice(index, 1)
  }

  // 如果删除的是当前聊天室，清空当前选择
  if (currentRoom.value?.id === room_id) {
    currentRoom.value = null
    messages.value = []
    if (websocket) {
      websocket.close()
      websocket = null
    }
  }

  // 显示通知
  ElNotification({
    title: '聊天室已删除',
    message: `${deleted_by.username} 删除了聊天室: ${room_name}`,
    type: 'warning',
    duration: 3000,
    position: 'top-right'
  })
}

const handleRoomUpdated = (data) => {
  const { room_id, last_message, last_message_at } = data

  // 找到对应的聊天室并更新
  const room = rooms.value.find(r => r.id === room_id)
  if (room) {
    // 更新最后消息信息
    room.last_message = last_message
    room.last_message_at = last_message_at

    // 如果当前用户不在这个聊天室中，增加未读计数
    if (currentRoom.value?.id !== room_id) {
      room.unread_count = (room.unread_count || 0) + 1
    }

    // 将有新消息的聊天室移到列表顶部
    const index = rooms.value.findIndex(r => r.id === room_id)
    if (index > 0) {
      rooms.value.splice(index, 1)
      rooms.value.unshift(room)
    }
  }
}

const handlePrivateRoomCreated = (data) => {
  const { room } = data

  // 检查是否已经存在这个聊天室
  const existingRoom = rooms.value.find(r => r.id === room.id)
  if (existingRoom) {
    return
  }

  // 添加新私聊聊天室到列表
  const newRoom = {
    id: room.id,
    name: room.name,
    room_type: room.room_type,
    avatar: room.avatar,
    member_count: 2,
    last_message: null,
    last_message_at: null,
    unread_count: 0,
    is_muted: false,
    creator: room.creator
  }

  rooms.value.unshift(newRoom)

  // 显示通知
  ElNotification({
    title: '新私聊',
    message: `${room.creator.username} 发起了与您的私聊`,
    type: 'info',
    duration: 5000,
    position: 'top-right',
    onClick: () => {
      // 点击通知时自动打开私聊
      selectRoom(newRoom)
    }
  })
}

const handleNewMessage = (data) => {
  // console.log('收到新消息:', data)
  // console.log('当前聊天室:', currentRoom.value?.id)

  // 如果是当前聊天室的消息，添加到消息列表
  if (currentRoom.value && data.room_id === currentRoom.value.id) {
    // console.log('添加消息到当前聊天室')

    // 检查消息是否已经存在（避免重复添加）
    const existingMessage = messages.value.find(m => m.id === data.id)
    if (existingMessage) {
      // console.log('消息已存在，跳过添加')
      return
    }

    const newMessage = {
      id: data.id,
      content: data.content,
      message_type: data.message_type,
      sender: data.sender,
      file_url: data.file_url,
      file_name: data.file_name,
      file_size: data.file_size,
      created_at: data.created_at,
      reply_to_id: data.reply_to_id,
      is_edited: false,
      is_deleted: false,
      is_pinned: false,
      edit_count: 0,
      read_count: 0,
      reactions: []
    }

    messages.value.push(newMessage)
    // console.log('消息列表长度:', messages.value.length)

    // 滚动到底部
    nextTick(() => {
      scrollToBottom()
    })
  } else {
    // console.log('消息不属于当前聊天室，忽略')
  }

  // 更新聊天室列表中的最后消息
  const roomIndex = rooms.value.findIndex(r => r.id === data.room_id)
  if (roomIndex !== -1) {
    rooms.value[roomIndex].last_message = {
      content: data.content,
      sender: data.sender,
      created_at: data.created_at
    }
    rooms.value[roomIndex].last_message_at = data.created_at

    // 如果不是当前聊天室，增加未读计数
    if (currentRoom.value?.id !== data.room_id) {
      rooms.value[roomIndex].unread_count = (rooms.value[roomIndex].unread_count || 0) + 1
    }
  }
}

// 处理消息表情反应
const handleMessageReaction1 = (data) => {
  console.log('收到表情反应:', data)

  // 如果是当前聊天室的消息，更新表情反应
  if (currentRoom.value && data.room_id === currentRoom.value.id) {
    const messageIndex = messages.value.findIndex(m => m.id === data.message_id)
    if (messageIndex !== -1) {
      // 重新加载消息的表情反应
      loadMessageReactions(data.message_id)
    }
  }
}

// 处理系统通知
const handleSystemNotification = (data) => {
  console.log('收到系统通知:', data)

  // 如果是加入申请通知，显示在聊天室中
  if (data.type === 'join_request') {
    // 创建系统消息
    const systemMessage = {
      id: `system_${Date.now()}`,
      content: data.message,
      message_type: 'system',
      sender: {
        id: 0,
        username: 'System',
        nickname: '系统',
        avatar: null
      },
      created_at: new Date().toISOString(),
      is_system: true,
      system_data: {
        type: 'join_request',
        user_id: data.user_id,
        username: data.username,
        room_id: data.room_id
      }
    }

    // 如果是当前聊天室，添加到消息列表
    if (currentRoom.value && data.room_id === currentRoom.value.id) {
      messages.value.push(systemMessage)
      nextTick(() => {
        scrollToBottom()
      })
    }

    // 显示通知
    ElMessage.info(data.message)
  }
}

const handleUserStatusChange = (data) => {
  // 更新用户在线状态
  console.log(`用户 ${data.user_id} ${data.is_online ? '上线' : '下线'}`)

  // 可以在这里更新聊天室成员的在线状态显示
  // 如果需要显示在线用户列表，可以在这里处理
}

// 聊天室右键菜单相关方法
const showRoomContextMenu = (event, room) => {
  console.log('显示聊天室右键菜单:', room.name, event.clientX, event.clientY)

  // 确保隐藏其他菜单
  hideMessageContextMenu()

  roomContextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    room: room
  }
  console.log('右键菜单状态:', roomContextMenu.value)

  // 添加一个延迟来确保DOM更新
  nextTick(() => {
    const menu = document.querySelector('.context-menu')
    if (menu) {
      console.log('右键菜单DOM元素:', menu)
      console.log('菜单位置:', menu.style.left, menu.style.top)
      console.log('菜单可见性:', menu.style.display, menu.offsetWidth, menu.offsetHeight)
    } else {
      console.log('未找到右键菜单DOM元素')
    }
  })
}

const hideRoomContextMenu = () => {
  roomContextMenu.value.visible = false
}

// 消息右键菜单相关方法
const showMessageContextMenu = (event, message) => {
  console.log('显示消息右键菜单:', message.content.substring(0, 20), event.clientX, event.clientY)

  // 确保隐藏其他菜单
  hideRoomContextMenu()

  messageContextMenu.show = true
  messageContextMenu.x = event.clientX
  messageContextMenu.y = event.clientY
  messageContextMenu.message = message

  console.log('消息右键菜单状态:', messageContextMenu)

  // 添加一个延迟来确保DOM更新
  nextTick(() => {
    const menu = document.querySelector('.context-menu')
    if (menu) {
      console.log('消息右键菜单DOM元素:', menu)
    } else {
      console.error('消息右键菜单DOM元素未找到')
    }
  })
}

const hideMessageContextMenu = () => {
  messageContextMenu.show = false
}

const hideAllContextMenus = () => {
  hideRoomContextMenu()
  hideMessageContextMenu()
}

// 消息操作函数
const copyMessage = (message) => {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(message.content)
    ElMessage.success('消息已复制到剪贴板')
  } else {
    // 兼容旧浏览器
    const textArea = document.createElement('textarea')
    textArea.value = message.content
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    ElMessage.success('消息已复制到剪贴板')
  }
  hideMessageContextMenu()
}

const canEditMessage = (message) => {
  // 只有消息发送者可以编辑消息
  return message.sender.id === userStore.user?.id && !message.is_deleted
}

const canDeleteMessage = (message) => {
  // 消息发送者或管理员可以删除消息
  return (message.sender.id === userStore.user?.id || userStore.user?.is_admin) && !message.is_deleted
}

// // 添加缺失的函数
// const reactToMessage = (message) => {
//   // 表情反应功能待实现
//   ElMessage.info('表情反应功能待实现')
//   hideMessageContextMenu()
// }

const hideContextMenu = () => {
  // 兼容旧的函数名
  hideMessageContextMenu()
}

const markRoomAsRead = async (room) => {
  if (!room) return

  try {
    await markMessagesAsRead(room.id)
    // 清除未读计数
    const roomIndex = rooms.value.findIndex(r => r.id === room.id)
    if (roomIndex !== -1) {
      rooms.value[roomIndex].unread_count = 0
    }
    ElMessage.success('已标记为已读')
  } catch (error) {
    console.error('标记已读失败:', error)
    ElMessage.error('标记已读失败')
  } finally {
    hideRoomContextMenu()
  }
}

const toggleRoomMute = async (room) => {
  if (!room) return

  try {
    // 这里可以添加静音/取消静音的API调用
    const roomIndex = rooms.value.findIndex(r => r.id === room.id)
    if (roomIndex !== -1) {
      rooms.value[roomIndex].is_muted = !rooms.value[roomIndex].is_muted
    }

    ElMessage.success(room.is_muted ? '已取消静音' : '已静音')
  } catch (error) {
    console.error('切换静音状态失败:', error)
    ElMessage.error('操作失败')
  } finally {
    hideRoomContextMenu()
  }
}

const markMessagesAsRead = async (roomId) => {
  try {
    await axios.post(`/api/modern-chat/rooms/${roomId}/mark-read`)
  } catch (error) {
    console.error('标记消息已读失败:', error)
  }
}

// 图片上传处理
const handleImageUpload = async (file) => {
  if (!currentRoom.value) {
    ElMessage.error('请先选择聊天室')
    return false
  }

  // 验证文件类型
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('只支持 JPG、PNG、GIF、WebP 格式的图片')
    return false
  }

  // 验证文件大小 (10MB)
  const maxSize = 10 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('图片大小不能超过 10MB')
    return false
  }

  try {
    uploading.value = true

    // 创建FormData
    const formData = new FormData()
    formData.append('file', file)

    // 上传图片
    const response = await axios.post('/api/modern-chat/upload-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    if (response.data.success) {
      // 发送图片消息
      await sendImageMessage(response.data.url, file.name, file.size)
      ElMessage.success('图片发送成功')
    } else {
      ElMessage.error('图片上传失败')
    }
  } catch (error) {
    console.error('图片上传失败:', error)
    ElMessage.error('图片上传失败')
  } finally {
    uploading.value = false
  }

  return false // 阻止默认上传行为
}

// 发送图片消息
const sendImageMessage = async (imageUrl, fileName, fileSize) => {
  if (!currentRoom.value) return

  try {
    const messageData = {
      content: `[图片] ${fileName}`,
      message_type: 'image',
      file_url: imageUrl,
      file_name: fileName,
      file_size: fileSize
    }

    const response = await axios.post(
      `/api/modern-chat/rooms/${currentRoom.value.id}/messages`,
      messageData
    )

    if (response.data) {
      // 消息会通过WebSocket实时推送，这里不需要手动添加到列表
      console.log('图片消息发送成功')
    }
  } catch (error) {
    console.error('发送图片消息失败:', error)
    ElMessage.error('发送图片消息失败')
  }
}

// 工具函数
const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const previewImage = (imageUrl) => {
  // 创建图片预览对话框
  const dialog = document.createElement('div')
  dialog.className = 'image-preview-dialog'
  dialog.innerHTML = `
    <div class="image-preview-overlay" onclick="this.parentElement.remove()">
      <div class="image-preview-container">
        <img src="${imageUrl}" alt="图片预览" />
        <button class="image-preview-close" onclick="this.closest('.image-preview-dialog').remove()">
          <i class="el-icon-close"></i>
        </button>
      </div>
    </div>
  `

  document.body.appendChild(dialog)
}

const downloadFile = (fileUrl, fileName) => {
  const link = document.createElement('a')
  link.href = fileUrl
  link.download = fileName
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// 聊天室类型相关方法
const getRoomAvatarClass = (room) => {
  return {
    'public-room': room.room_type === 'public',
    'group-room': room.room_type === 'group',
    'private-room': room.room_type === 'private',
    'channel-room': room.room_type === 'channel'
  }
}

const getRoomTypeBadgeClass = (room) => {
  return {
    'public-badge': room.room_type === 'public',
    'group-badge': room.room_type === 'group',
    'private-badge': room.room_type === 'private',
    'channel-badge': room.room_type === 'channel'
  }
}

const getRoomNameClass = (room) => {
  return {
    'public-name': room.room_type === 'public',
    'group-name': room.room_type === 'group',
    'private-name': room.room_type === 'private',
    'channel-name': room.room_type === 'channel'
  }
}

const getRoomTypeTextClass = (room) => {
  return {
    'public-text': room.room_type === 'public',
    'group-text': room.room_type === 'group',
    'private-text': room.room_type === 'private',
    'channel-text': room.room_type === 'channel'
  }
}

const getRoomTypeText = (room) => {
  switch (room.room_type) {
    case 'public':
      return '公开'
    case 'group':
      return '私密'
    case 'private':
      return '私聊'
    case 'channel':
      return '频道'
    default:
      return ''
  }
}

const editMessage = (message) => {
  // 设置编辑状态
  editingMessage.value = message
  messageInput.value = message.content

  // 滚动到输入框
  nextTick(() => {
    const inputElement = document.querySelector('.input-area textarea')
    if (inputElement) {
      inputElement.focus()
      inputElement.setSelectionRange(inputElement.value.length, inputElement.value.length)
    }
  })
}

const deleteMessage = async (message) => {
  try {
    await ElMessageBox.confirm('确定要删除这条消息吗？', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })

    if (websocket && websocket.isAuthenticated()) {
      websocket.deleteMessage(message.id)
    }
  } catch {
    // 用户取消
  }
}

const reactToMessage = (message) => {
  showEmojiPicker.value = true
  selectedMessageForReaction.value = message
  hideMessageContextMenu()
}

const toggleReaction = async (message, emoji) => {
  if (!message || !emoji) return

  try {
    await axios.post(`/api/modern-chat/messages/${message.id}/reactions`, {
      emoji: emoji
    })

    // 本地更新会通过WebSocket通知处理
  } catch (error) {
    console.error('表情反应失败:', error)
    ElMessage.error('表情反应失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 加载消息的表情反应
const loadMessageReactions = async (messageId) => {
  try {
    const response = await axios.get(`/api/modern-chat/messages/${messageId}/reactions`)
    const reactions = response.data

    // 更新消息的表情反应
    const messageIndex = messages.value.findIndex(m => m.id === messageId)
    if (messageIndex !== -1) {
      messages.value[messageIndex].reactions = reactions
    }
  } catch (error) {
    console.error('加载表情反应失败:', error)
  }
}

// ==================== 系统消息辅助函数 ====================

// 获取系统消息图标
const getSystemMessageIcon = (type) => {
  const iconMap = {
    // 加入申请相关
    'join_request': 'User',
    'join_request_approved': 'Check',
    'join_request_rejected': 'Close',

    // 成员管理
    'member_joined': 'User',
    'member_left': 'User',
    'member_kicked': 'WarningFilled',
    'member_invited': 'User',

    // 权限变更
    'role_changed': 'Crown',
    'admin_promoted': 'Crown',
    'admin_demoted': 'Crown',
    'owner_transferred': 'Crown',

    // 聊天室设置
    'room_name_changed': 'Edit',
    'room_description_changed': 'Edit',
    'room_rules_changed': 'Document',
    'room_settings_changed': 'Setting',

    // 消息管理
    'message_pinned': 'Star',
    'message_unpinned': 'Star',
    'message_deleted_by_admin': 'Delete',

    // 文件分享
    'file_uploaded': 'Document',
    'file_shared': 'Document'
  }

  return iconMap[type] || 'InfoFilled'
}

// 获取系统消息样式类
const getSystemMessageClass = (type) => {
  const classMap = {
    // 加入申请相关
    'join_request': 'system-join-request',
    'join_request_approved': 'system-success',
    'join_request_rejected': 'system-danger',

    // 成员管理
    'member_joined': 'system-success',
    'member_left': 'system-warning',
    'member_kicked': 'system-danger',
    'member_invited': 'system-info',

    // 权限变更
    'role_changed': 'system-crown',
    'admin_promoted': 'system-crown',
    'admin_demoted': 'system-crown',
    'owner_transferred': 'system-crown',

    // 聊天室设置
    'room_name_changed': 'system-info',
    'room_description_changed': 'system-info',
    'room_rules_changed': 'system-info',
    'room_settings_changed': 'system-info',

    // 消息管理
    'message_pinned': 'system-pin',
    'message_unpinned': 'system-pin',
    'message_deleted_by_admin': 'system-danger',

    // 文件分享
    'file_uploaded': 'system-file',
    'file_shared': 'system-file'
  }

  return classMap[type] || 'system-default'
}

// 获取角色标签类型
const getTagType = (role) => {
  const typeMap = {
    'creator': 'danger',
    'admin': 'warning',
    'member': 'info'
  }
  return typeMap[role] || 'info'
}

// 获取角色显示名称
const getRoleDisplayName = (role) => {
  const nameMap = {
    'creator': '群主',
    'admin': '管理员',
    'member': '普通成员'
  }
  return nameMap[role] || role
}

// 滚动到指定消息
const scrollToMessage1 = (messageId) => {
  const messageElement = document.querySelector(`[data-message-id="${messageId}"]`)
  if (messageElement) {
    messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
    // 高亮显示消息
    messageElement.classList.add('message-highlight')
    setTimeout(() => {
      messageElement.classList.remove('message-highlight')
    }, 2000)
  } else {
    ElMessage.warning('消息不在当前页面，请尝试加载更多历史消息')
  }
}

const handleFileUpload = async (file) => {
  if (!currentRoom.value) {
    ElMessage.error('请先选择聊天室')
    return false
  }

  // 检查文件大小 (10MB限制)
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过10MB')
    return false
  }

  // 检查文件类型
  const allowedTypes = ['image/', 'video/', 'audio/', 'application/pdf', 'text/', 'application/msword', 'application/vnd.openxmlformats']
  const isAllowed = allowedTypes.some(type => file.type.startsWith(type))

  if (!isAllowed) {
    ElMessage.error('不支持的文件类型')
    return false
  }

  try {
    uploading.value = true

    // 创建FormData
    const formData = new FormData()
    formData.append('files', file)

    // 上传文件到聊天目录
    const uploadPath = `chat/${currentRoom.value.id}/${new Date().getFullYear()}/${new Date().getMonth() + 1}`
    const response = await axios.post(`/api/files/upload/${uploadPath}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
      }
    })

    if (response.data && response.data.length > 0) {
      const uploadedFile = response.data[0]
      // 发送文件消息
      const messageData = {
        type: 'send_message',
        data: {
          content: `[文件] ${file.name}`,
          message_type: file.type.startsWith('image/') ? 'image' : 'file',
          file_url: uploadedFile.download_url,
          file_name: file.name,
          file_size: file.size
        }
      }

      if (websocket && websocket.isAuthenticated()) {
        websocket.sendChatMessage({
          content: `[文件] ${file.name}`,
          message_type: file.type.startsWith('image/') ? 'image' : 'file',
          file_url: uploadedFile.download_url,
          file_name: file.name,
          file_size: file.size
        })
      }

      ElMessage.success('文件上传成功')
    }
  } catch (error) {
    console.error('文件上传失败:', error)
    ElMessage.error('文件上传失败')
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }

  return false
}

const createRoom = async () => {
  if (!newRoom.name.trim()) {
    ElMessage.error('请输入聊天室名称')
    return
  }

  creating.value = true

  try {
    const response = await axios.post('/api/modern-chat/rooms', newRoom)
    rooms.value.unshift(response.data)
    showCreateRoomDialog.value = false

    // 重置表单
    Object.assign(newRoom, {
      name: '',
      description: '',
      room_type: 'group',
      is_public: true,
      max_members: 500,
      allow_member_invite: true,
      allow_member_modify_info: false,
      message_history_visible: true,
      allow_search: false,  // 默认不允许搜索
      enable_invite_code: true  // 默认启用邀请码
    })

    ElMessage.success('聊天室创建成功')

    // 自动选择新创建的聊天室
    selectRoom(response.data)
  } catch (error) {
    console.error('创建聊天室失败:', error)
    ElMessage.error('创建聊天室失败')
  } finally {
    creating.value = false
  }
}



const manageMembers = (room) => {
  // TODO: 实现成员管理功能
  ElMessage.info('成员管理功能开发中')
}

const canManageRoom = (room) => {
  if (!userStore.user) return false

  // 私聊聊天室：任何成员都可以管理（主要是删除）
  if (room.room_type === 'private') {
    return true // 假设当前用户能看到的私聊都是自己参与的
  }

  // 检查是否是创建者
  if (room.creator?.id === userStore.user.id) return true

  // 检查是否是系统管理员
  if (userStore.user.is_superuser) return true

  // 检查是否有admin角色
  if (userStore.user.roles && userStore.user.roles.some(r => r.name === 'admin')) return true

  return false
}

// 检查是否是群主
const isRoomCreator = (room) => {
  if (!room || !userStore.user) return false
  return room.created_by === userStore.user.id || room.creator?.id === userStore.user.id
}

const onRoomTypeChange = (type) => {
  // 根据聊天室类型调整默认设置
  if (type === 'channel') {
    // 频道默认设置
    newRoom.allow_member_invite = false
    newRoom.allow_member_modify_info = false
    newRoom.is_public = true
    newRoom.allow_search = false
  } else if (type === 'group') {
    // 群聊默认设置
    newRoom.allow_member_invite = true
    newRoom.allow_member_modify_info = false
    newRoom.is_public = false
    newRoom.allow_search = true  // 私密聊天室默认允许搜索
  } else if (type === 'public') {
    // 公开聊天室默认设置
    newRoom.allow_member_invite = true
    newRoom.allow_member_modify_info = false
    newRoom.is_public = true
    newRoom.allow_search = false  // 公开聊天室不需要搜索
  }
}

const deleteRoom = async (room) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除聊天室"${room.name}"吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await axios.delete(`/api/modern-chat/rooms/${room.id}`)

    ElMessage.success('聊天室删除成功')

    // 如果删除的是当前聊天室，清空当前选择
    if (currentRoom.value?.id === room.id) {
      currentRoom.value = null
      messages.value = []
      if (websocket) {
        websocket.close()
        websocket = null
      }
    }

    // 从列表中移除
    const index = rooms.value.findIndex(r => r.id === room.id)
    if (index !== -1) {
      rooms.value.splice(index, 1)
    }

  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除聊天室失败:', error)
      ElMessage.error('删除聊天室失败')
    }
  }
}

// 私聊相关方法
const searchUsers = async (query) => {
  if (!query) {
    availableUsers.value = []
    return
  }

  try {
    searchingUsers.value = true
    const response = await axios.get('/api/users/search/users', {
      params: { q: query, limit: 10 }
    })

    // 过滤掉当前用户
    availableUsers.value = response.data.filter(user => user.id !== userStore.user?.id)
  } catch (error) {
    console.error('搜索用户失败:', error)
    ElMessage.error('搜索用户失败')
  } finally {
    searchingUsers.value = false
  }
}

const loadRecentUsers = async () => {
  try {
    // 获取最近聊天的用户
    const response = await axios.get('/api/users/contacts/recent')
    recentUsers.value = response.data.filter(user => user.id !== userStore.user?.id)
  } catch (error) {
    console.error('加载最近联系人失败:', error)
  }
}

const startPrivateChat = async () => {
  if (!selectedUserId.value) {
    ElMessage.error('请选择要私聊的用户')
    return
  }

  try {
    // 查找或创建私聊聊天室
    const response = await axios.post('/api/modern-chat/private-rooms', {
      target_user_id: selectedUserId.value
    })

    const privateRoom = response.data

    // 添加到聊天室列表（如果不存在）
    const existingRoom = rooms.value.find(r => r.id === privateRoom.id)
    if (!existingRoom) {
      rooms.value.unshift(privateRoom)
    }

    // 选择这个聊天室（私聊使用普通聊天室WebSocket）
    await selectRoom(privateRoom)

    // 关闭对话框
    showPrivateChatDialog.value = false
    selectedUserId.value = null

    ElMessage.success('私聊已开始')

  } catch (error) {
    console.error('开始私聊失败:', error)
    ElMessage.error('开始私聊失败: ' + (error.response?.data?.detail || error.message))
  }
}

const updateUserOnlineStatus = (userId, isOnline) => {
  if (currentRoom.value?.members) {
    const member = currentRoom.value.members.find(m => m.id === userId)
    if (member) {
      member.is_online = isOnline
    }
  }

  // 更新在线人数
  updateOnlineCount()
}

const updateOnlineCount = () => {
  if (currentRoom.value?.members) {
    onlineCount.value = currentRoom.value.members.filter(m => m.is_online).length
  }
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const getTypingText = () => {
  if (typingUsers.value.length === 0) return ''
  if (typingUsers.value.length === 1) {
    return `${typingUsers.value[0].username} 正在输入...`
  }
  if (typingUsers.value.length === 2) {
    return `${typingUsers.value[0].username} 和 ${typingUsers.value[1].username} 正在输入...`
  }
  return `${typingUsers.value.length} 人正在输入...`
}

const formatTime = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`

  return date.toLocaleDateString()
}

const formatMessageTime = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date

  // 如果是今天
  if (diff < 24 * 60 * 60 * 1000 && date.getDate() === now.getDate()) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
  }

  // 如果是昨天
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (date.getDate() === yesterday.getDate()) {
    return '昨天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
  }

  // 如果是本周内
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    return weekdays[date.getDay()] + ' ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
  }

  // 如果是今年
  if (date.getFullYear() === now.getFullYear()) {
    return (date.getMonth() + 1) + '月' + date.getDate() + '日 ' +
           date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
  }

  // 其他年份
  return date.getFullYear() + '年' + (date.getMonth() + 1) + '月' + date.getDate() + '日 ' +
         date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
}

// 搜索聊天室
const searchRooms = async () => {
  if (!roomSearchQuery.value.trim()) {
    roomSearchResults.value = []
    return
  }

  try {
    searchingRooms.value = true
    const response = await axios.get(`/api/modern-chat/search-rooms?q=${encodeURIComponent(roomSearchQuery.value)}`)
    roomSearchResults.value = response.data || []
    console.log('搜索结果:', roomSearchResults.value)
  } catch (error) {
    console.error('搜索聊天室失败:', error)
    ElMessage.error('搜索失败: ' + (error.response?.data?.detail || error.message))
    roomSearchResults.value = []
  } finally {
    searchingRooms.value = false
  }
}

// 选择要加入的聊天室
const selectRoomToJoin = (room) => {
  selectedRoomToJoin.value = room
  console.log('选择聊天室:', room.name)
}

// 显示私密聊天室加入对话框
const showJoinPrivateRoomDialog = (room) => {
  selectedRoomToJoin.value = room
  joinRequestForm.message = ''
  showJoinRoomDialog.value = false
  showJoinPrivateDialog.value = true
}

// 直接加入公开聊天室（虽然公开聊天室不会出现在搜索结果中，但保留此方法）
const joinPublicRoom = async (room) => {
  try {
    // 公开聊天室可以直接加入，通过发送消息自动加入
    ElMessage.success(`已加入公开聊天室 ${room.name}`)
    showJoinRoomDialog.value = false

    // 重新加载聊天室列表
    await loadRooms()

    // 选择新加入的聊天室
    const roomInList = rooms.value.find(r => r.id === room.id)
    if (roomInList) {
      selectRoom(roomInList)
    }
  } catch (error) {
    console.error('加入公开聊天室失败:', error)
    ElMessage.error('加入聊天室失败')
  }
}

// 提交加入申请
const submitJoinRequest = async () => {
  if (!selectedRoomToJoin.value) return

  try {
    submittingRequest.value = true

    const response = await axios.post(`/api/modern-chat/rooms/${selectedRoomToJoin.value.id}/join-request`, {
      room_id: selectedRoomToJoin.value.id,
      message: joinRequestForm.message
    })

    if (response.data) {
      ElMessage.success(response.data.message || '申请已发送')
      showJoinPrivateDialog.value = false
      joinRequestForm.message = ''
      selectedRoomToJoin.value = null
    }
  } catch (error) {
    console.error('发送加入申请失败:', error)
    if (error.response?.status === 429) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('发送申请失败: ' + (error.response?.data?.detail || error.message))
    }
  } finally {
    submittingRequest.value = false
  }
}

// 通过邀请码加入
const joinByInviteCode = async () => {
  if (!inviteCodeForm.code.trim()) return

  try {
    joiningByInvite.value = true

    const response = await axios.post('/api/modern-chat/rooms/join-by-invite', {
      invite_code: inviteCodeForm.code.trim()
    })

    if (response.data) {
      ElMessage.success(response.data.message || '成功加入聊天室')
      showJoinRoomDialog.value = false
      inviteCodeForm.code = ''

      // 重新加载聊天室列表
      await loadRooms()

      // 选择新加入的聊天室
      if (response.data.room_id) {
        const roomInList = rooms.value.find(r => r.id === response.data.room_id)
        if (roomInList) {
          selectRoom(roomInList)
        }
      }
    }
  } catch (error) {
    console.error('通过邀请码加入失败:', error)
    ElMessage.error('加入失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    joiningByInvite.value = false
  }
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('zh-CN')
}

const getRoomTypeColor = (type) => {
  switch (type) {
    case 'private': return 'danger'
    case 'group': return 'primary'
    case 'channel': return 'warning'
    default: return 'info'
  }
}

const getRoomTypeName = (type) => {
  switch (type) {
    case 'private': return '私聊'
    case 'group': return '群聊'
    case 'channel': return '频道'
    default: return '未知'
  }
}

const getRoleName = (role) => {
  switch (role) {
    case 'admin': return '管理员'
    case 'member': return '成员'
    default: return '未知'
  }
}

const handleResize = () => {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value) {
    showSidebar.value = true
  }
}

// 聊天室信息相关方法
const loadRoomInviteCode = async () => {
  if (!currentRoom.value || currentRoom.value.room_type !== 'group') return

  try {
    const response = await axios.get(`/api/modern-chat/rooms/${currentRoom.value.id}/invite-code`)
    roomInviteCode.value = response.data
  } catch (error) {
    console.error('获取邀请码失败:', error)
    roomInviteCode.value = null
  }
}

const generateInviteCode = async () => {
  if (!currentRoom.value) return

  try {
    generatingCode.value = true
    const response = await axios.post(`/api/modern-chat/rooms/${currentRoom.value.id}/refresh-invite-code`)
    roomInviteCode.value = response.data
    ElMessage.success('邀请码生成成功')
  } catch (error) {
    console.error('生成邀请码失败:', error)
    ElMessage.error('生成邀请码失败')
  } finally {
    generatingCode.value = false
  }
}

const refreshInviteCode = async () => {
  if (!currentRoom.value) return

  try {
    refreshingCode.value = true
    const response = await axios.post(`/api/modern-chat/rooms/${currentRoom.value.id}/refresh-invite-code`)
    roomInviteCode.value = response.data
    ElMessage.success('邀请码刷新成功')
  } catch (error) {
    console.error('刷新邀请码失败:', error)
    ElMessage.error('刷新邀请码失败')
  } finally {
    refreshingCode.value = false
  }
}

const copyInviteCode = async () => {
  if (!roomInviteCode.value?.invite_code) return

  try {
    await navigator.clipboard.writeText(roomInviteCode.value.invite_code)
    ElMessage.success('邀请码已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
}

const submitJoinRequestFromInfo = async () => {
  if (!currentRoom.value) return

  try {
    submittingRequest.value = true

    const response = await axios.post(`/api/modern-chat/rooms/${currentRoom.value.id}/join-request`, {
      room_id: currentRoom.value.id,
      message: joinRequestForm.message
    })

    if (response.data) {
      ElMessage.success(response.data.message || '申请已发送')
      showRoomInfoDialog.value = false
      joinRequestForm.message = ''
    }
  } catch (error) {
    console.error('发送加入申请失败:', error)
    if (error.response?.status === 429) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('发送申请失败: ' + (error.response?.data?.detail || error.message))
    }
  } finally {
    submittingRequest.value = false
  }
}

const formatDateTime = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 聊天室设置
const showRoomSettings = async (room) => {
  if (!room) return

  // 显示聊天室高级设置
  showRoomSettingsDialog.value = true
  roomSettingsForm.value = {
    id: room.id,
    name: room.name,
    description: room.description,
    room_type: room.room_type,
    max_members: room.max_members,
    allow_search: room.allow_search,
    enable_invite_code: room.enable_invite_code,
    allow_member_invite: room.allow_member_invite,
    is_active: room.is_active,
    auto_delete_messages: room.auto_delete_messages || false,
    message_retention_days: room.message_retention_days || 30,
    allow_file_upload: room.allow_file_upload !== false,
    max_file_size: room.max_file_size || 10,
    welcome_message: room.welcome_message || '',
    rules: room.rules || ''
  }

  // 加载统计信息
  await loadRoomStatistics(room.id)

  hideAllContextMenus()
}

// 加载聊天室统计信息
const loadRoomStatistics = async (roomId) => {
  try {
    const response = await axios.get(`/api/modern-chat/rooms/${roomId}/statistics`)
    roomStatistics.value = response.data
  } catch (error) {
    console.error('加载统计信息失败:', error)
    roomStatistics.value = null
  }
}

// 置顶功能
const togglePinRoom = (room) => {
  if (!room) return

  if (pinnedRooms.value.has(room.id)) {
    pinnedRooms.value.delete(room.id)
    ElMessage.success(`已取消置顶 ${room.name}`)
  } else {
    pinnedRooms.value.add(room.id)
    ElMessage.success(`已置顶 ${room.name}`)
  }

  // 保存到本地存储
  localStorage.setItem('pinnedRooms', JSON.stringify([...pinnedRooms.value]))

  // 重新排序聊天室列表
  sortRoomsByPin()
  hideAllContextMenus()
}

const togglePinMessage = async (message) => {
  if (!message || !currentRoom.value) return

  try {
    if (message.is_pinned) {
      // 取消置顶
      await axios.delete(`/api/modern-chat/rooms/${currentRoom.value.id}/messages/${message.id}/pin`)
      message.is_pinned = false
      message.pinned_by = null
      message.pinned_at = null
      ElMessage.success('已取消置顶消息')
    } else {
      // 置顶消息
      await axios.post(`/api/modern-chat/rooms/${currentRoom.value.id}/messages/${message.id}/pin`)
      message.is_pinned = true
      message.pinned_by = userStore.user.id
      message.pinned_at = new Date().toISOString()
      ElMessage.success('已置顶消息')
    }

    hideAllContextMenus()
  } catch (error) {
    console.error('置顶操作失败:', error)
    ElMessage.error('操作失败: ' + (error.response?.data?.detail || error.message))
  }
}

const sortRoomsByPin = () => {
  rooms.value.sort((a, b) => {
    const aPinned = pinnedRooms.value.has(a.id)
    const bPinned = pinnedRooms.value.has(b.id)

    if (aPinned && !bPinned) return -1
    if (!aPinned && bPinned) return 1

    // 如果都置顶或都不置顶，按最后消息时间排序
    const aTime = new Date(a.last_message_at || a.created_at).getTime()
    const bTime = new Date(b.last_message_at || b.created_at).getTime()
    return bTime - aTime
  })
}

// 加载置顶数据
const loadPinnedData = () => {
  try {
    const savedPinnedRooms = localStorage.getItem('pinnedRooms')
    if (savedPinnedRooms) {
      pinnedRooms.value = new Set(JSON.parse(savedPinnedRooms))
    }
  } catch (error) {
    console.error('加载置顶数据失败:', error)
  }
}

// 加载置顶消息
const loadPinnedMessages = async () => {
  if (!currentRoom.value) return

  try {
    const response = await axios.get(`/api/modern-chat/rooms/${currentRoom.value.id}/pinned-messages`)
    pinnedMessagesInRoom.value = response.data || []
  } catch (error) {
    console.error('加载置顶消息失败:', error)
    pinnedMessagesInRoom.value = []
  }
}

// 文本截断工具函数
const truncateText = (text, maxLength) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// 滚动到指定消息
const scrollToMessage = (messageId) => {
  const messageElement = document.querySelector(`[data-message-id="${messageId}"]`)
  if (messageElement) {
    messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
    // 高亮显示消息
    messageElement.classList.add('highlight-message')
    setTimeout(() => {
      messageElement.classList.remove('highlight-message')
    }, 2000)
  } else {
    ElMessage.info('消息不在当前页面，请尝试加载更多历史消息')
  }
}

// 成员管理功能
const showMemberManagement = async (room) => {
  if (!room) return

  try {
    const response = await axios.get(`/api/modern-chat/rooms/${room.id}/members`)
    roomMembers.value = response.data || []
    showMemberManagementDialog.value = true
    memberSearchQuery.value = ''
  } catch (error) {
    console.error('加载成员列表失败:', error)
    ElMessage.error('加载成员列表失败')
  }

  hideAllContextMenus()
}

const kickMember = async (member) => {
  if (!currentRoom.value || !member) return

  try {
    await ElMessageBox.confirm(
      `确定要踢出成员 ${member.nickname || member.username} 吗？`,
      '确认踢出',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await axios.post(`/api/modern-chat/rooms/${currentRoom.value.id}/members/${member.user_id}/kick`)

    // 从列表中移除成员
    const index = roomMembers.value.findIndex(m => m.user_id === member.user_id)
    if (index !== -1) {
      roomMembers.value.splice(index, 1)
    }

    ElMessage.success(`已踢出 ${member.nickname || member.username}`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('踢出成员失败:', error)
      ElMessage.error('踢出成员失败: ' + (error.response?.data?.detail || error.message))
    }
  }
}

const toggleMuteMember = async (member) => {
  if (!currentRoom.value || !member) return

  try {
    const action = member.is_muted ? '取消禁言' : '禁言'
    await ElMessageBox.confirm(
      `确定要${action}成员 ${member.nickname || member.username} 吗？`,
      `确认${action}`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await axios.post(`/api/modern-chat/rooms/${currentRoom.value.id}/members/${member.user_id}/mute`, {
      is_muted: !member.is_muted,
      reason: member.is_muted ? '' : '违反聊天室规则'
    })

    // 更新本地状态
    member.is_muted = !member.is_muted

    ElMessage.success(`已${action} ${member.nickname || member.username}`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('禁言操作失败:', error)
      ElMessage.error('操作失败: ' + (error.response?.data?.detail || error.message))
    }
  }
}

const promoteToAdmin = async (member) => {
  if (!currentRoom.value || !member) return

  try {
    await ElMessageBox.confirm(
      `确定要将 ${member.nickname || member.username} 设为管理员吗？`,
      '确认设置管理员',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await axios.post(`/api/modern-chat/rooms/${currentRoom.value.id}/members/${member.user_id}/role`, {
      role: 'admin'
    })

    // 更新本地状态
    member.role = 'admin'

    ElMessage.success(`已将 ${member.nickname || member.username} 设为管理员`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('设置管理员失败:', error)
      ElMessage.error('操作失败: ' + (error.response?.data?.detail || error.message))
    }
  }
}

const demoteFromAdmin = async (member) => {
  if (!currentRoom.value || !member) return

  try {
    await ElMessageBox.confirm(
      `确定要取消 ${member.nickname || member.username} 的管理员身份吗？`,
      '确认取消管理员',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await axios.post(`/api/modern-chat/rooms/${currentRoom.value.id}/members/${member.user_id}/role`, {
      role: 'member'
    })

    // 更新本地状态
    member.role = 'member'

    ElMessage.success(`已取消 ${member.nickname || member.username} 的管理员身份`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消管理员失败:', error)
      ElMessage.error('操作失败: ' + (error.response?.data?.detail || error.message))
    }
  }
}

const transferOwnership = async (member) => {
  if (!currentRoom.value || !member) return

  try {
    await ElMessageBox.confirm(
      `确定要将群主身份转让给 ${member.nickname || member.username} 吗？转让后您将成为管理员。`,
      '确认转让群主',
      {
        confirmButtonText: '确定转让',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await axios.post(`/api/modern-chat/rooms/${currentRoom.value.id}/transfer-ownership`, {
      new_owner_id: member.user_id
    })

    // 更新本地状态
    currentRoom.value.created_by = member.user_id
    member.role = 'creator'

    // 找到当前用户并更新角色
    const currentUserMember = roomMembers.value.find(m => m.user_id === userStore.user.id)
    if (currentUserMember) {
      currentUserMember.role = 'admin'
    }

    ElMessage.success(`已将群主身份转让给 ${member.nickname || member.username}`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('转让群主失败:', error)
      ElMessage.error('操作失败: ' + (error.response?.data?.detail || error.message))
    }
  }
}

// 搜索用户（用于邀请功能）
const searchUsersForInvite = async () => {
  if (!userSearchQuery.value.trim()) {
    searchedUsers.value = []
    return
  }

  try {
    // 使用现有的searchUsers方法，但传入查询参数
    await searchUsers(userSearchQuery.value)
    // 过滤掉已经是成员的用户
    const memberIds = new Set(roomMembers.value.map(m => m.user_id))
    searchedUsers.value = availableUsers.value.filter(user => !memberIds.has(user.id))
  } catch (error) {
    console.error('搜索用户失败:', error)
    searchedUsers.value = []
  }
}

// 选择要邀请的用户
const selectUserToInvite = (user) => {
  inviteUserForm.selectedUser = user
  userSearchQuery.value = ''
  searchedUsers.value = []
}

// 邀请用户
const inviteUser = async () => {
  if (!currentRoom.value || !inviteUserForm.selectedUser) return

  try {
    invitingUser.value = true

    await axios.post(`/api/modern-chat/rooms/${currentRoom.value.id}/members/invite`, {
      user_id: inviteUserForm.selectedUser.id
    })

    // 重新加载成员列表
    await showMemberManagement(currentRoom.value)

    ElMessage.success(`已邀请 ${inviteUserForm.selectedUser.nickname || inviteUserForm.selectedUser.username} 加入聊天室`)

    // 重置表单
    inviteUserForm.selectedUser = null
    showInviteUserDialog.value = false
  } catch (error) {
    console.error('邀请用户失败:', error)
    ElMessage.error('邀请失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    invitingUser.value = false
  }
}

// 退出聊天室
const leaveRoom = (room) => {
  if (!room) return

  currentRoom.value = room
  showLeaveRoomDialog.value = true
  hideAllContextMenus()
}

// 确认退出聊天室
const confirmLeaveRoom = async () => {
  if (!currentRoom.value) return

  try {
    leavingRoom.value = true

    await axios.post(`/api/modern-chat/rooms/${currentRoom.value.id}/leave`)

    // 从聊天室列表中移除
    const index = rooms.value.findIndex(r => r.id === currentRoom.value.id)
    if (index !== -1) {
      rooms.value.splice(index, 1)
    }

    // 如果当前显示的是这个聊天室，清空显示
    if (currentRoom.value) {
      currentRoom.value = null
      messages.value = []
    }

    ElMessage.success(isRoomCreator(currentRoom.value) ? '群聊已解散' : '已退出群聊')
    showLeaveRoomDialog.value = false
  } catch (error) {
    console.error('退出聊天室失败:', error)
    ElMessage.error('操作失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    leavingRoom.value = false
  }
}

// 编辑聊天室
const editRoom = (room) => {
  if (!room) return

  // 复制聊天室数据到编辑表单
  editRoomForm.value = {
    id: room.id,
    name: room.name,
    description: room.description,
    room_type: room.room_type,
    max_members: room.max_members,
    allow_search: room.allow_search,
    enable_invite_code: room.enable_invite_code,
    allow_member_invite: room.allow_member_invite,
    is_active: room.is_active
  }

  showEditRoomDialog.value = true
  hideAllContextMenus()
}

const updateRoom = async () => {
  if (!editRoomForm.value) return

  try {
    updatingRoom.value = true

    const updateData = {
      name: editRoomForm.value.name,
      description: editRoomForm.value.description,
      max_members: editRoomForm.value.max_members,
      allow_search: editRoomForm.value.allow_search,
      enable_invite_code: editRoomForm.value.enable_invite_code,
      allow_member_invite: editRoomForm.value.allow_member_invite,
      is_active: editRoomForm.value.is_active
    }

    await axios.put(`/api/modern-chat/rooms/${editRoomForm.value.id}`, updateData)

    // 更新本地聊天室数据
    const roomIndex = rooms.value.findIndex(r => r.id === editRoomForm.value.id)
    if (roomIndex !== -1) {
      Object.assign(rooms.value[roomIndex], updateData)
    }

    // 如果是当前聊天室，也更新当前聊天室数据
    if (currentRoom.value && currentRoom.value.id === editRoomForm.value.id) {
      Object.assign(currentRoom.value, updateData)
    }

    ElMessage.success('聊天室信息已更新')
    showEditRoomDialog.value = false
  } catch (error) {
    console.error('更新聊天室失败:', error)
    ElMessage.error('更新失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    updatingRoom.value = false
  }
}

// 更新聊天室设置
const updateRoomSettings = async () => {
  if (!roomSettingsForm.value) return

  try {
    updatingRoomSettings.value = true

    const updateData = {
      name: roomSettingsForm.value.name,
      description: roomSettingsForm.value.description,
      max_members: roomSettingsForm.value.max_members,
      allow_search: roomSettingsForm.value.allow_search,
      enable_invite_code: roomSettingsForm.value.enable_invite_code,
      allow_member_invite: roomSettingsForm.value.allow_member_invite,
      is_active: roomSettingsForm.value.is_active,
      auto_delete_messages: roomSettingsForm.value.auto_delete_messages,
      message_retention_days: roomSettingsForm.value.message_retention_days,
      allow_file_upload: roomSettingsForm.value.allow_file_upload,
      max_file_size: roomSettingsForm.value.max_file_size,
      welcome_message: roomSettingsForm.value.welcome_message,
      rules: roomSettingsForm.value.rules
    }

    await axios.put(`/api/modern-chat/rooms/${roomSettingsForm.value.id}`, updateData)

    // 更新本地聊天室数据
    const roomIndex = rooms.value.findIndex(r => r.id === roomSettingsForm.value.id)
    if (roomIndex !== -1) {
      Object.assign(rooms.value[roomIndex], updateData)
    }

    // 如果是当前聊天室，也更新当前聊天室数据
    if (currentRoom.value && currentRoom.value.id === roomSettingsForm.value.id) {
      Object.assign(currentRoom.value, updateData)
    }

    ElMessage.success('聊天室设置已更新')
    showRoomSettingsDialog.value = false
  } catch (error) {
    console.error('更新聊天室设置失败:', error)
    ElMessage.error('更新失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    updatingRoomSettings.value = false
  }
}

// 处理加入申请
const approveJoinRequest = async (systemData) => {
  if (!systemData || !currentRoom.value) return

  try {
    processingRequest.value = true

    const response = await axios.post(`/api/modern-chat/join-requests/${systemData.user_id}/process`, {
      room_id: currentRoom.value.id,
      action: 'approve',
      message: '申请已通过'
    })

    if (response.data) {
      ElMessage.success('已同意加入申请')
      // 重新加载聊天室成员列表
      await loadRoomMembers()
    }
  } catch (error) {
    console.error('处理加入申请失败:', error)
    ElMessage.error('处理申请失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    processingRequest.value = false
  }
}

const rejectJoinRequest = async (systemData) => {
  if (!systemData || !currentRoom.value) return

  try {
    processingRequest.value = true

    const response = await axios.post(`/api/modern-chat/join-requests/${systemData.user_id}/process`, {
      room_id: currentRoom.value.id,
      action: 'reject',
      message: '申请已拒绝'
    })

    if (response.data) {
      ElMessage.success('已拒绝加入申请')
    }
  } catch (error) {
    console.error('处理加入申请失败:', error)
    ElMessage.error('处理申请失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    processingRequest.value = false
  }
}

// 加载聊天室成员列表
const loadRoomMembers = async () => {
  if (!currentRoom.value) return

  try {
    const response = await axios.get(`/api/modern-chat/rooms/${currentRoom.value.id}/members`)
    // 这里可以更新成员列表，如果有的话
    console.log('聊天室成员:', response.data)
  } catch (error) {
    console.error('加载成员列表失败:', error)
  }
}

// 监听聊天室信息对话框的显示，自动加载邀请码
watch(showRoomInfoDialog, (newVal) => {
  if (newVal && currentRoom.value?.room_type === 'group') {
    loadRoomInviteCode()
  }
})

// 生命周期
onMounted(async () => {
  await loadRooms()
  await loadRecentUsers()
  loadPinnedData()

  // 如果用户已登录，建立全局WebSocket连接
  if (userStore.isLoggedIn) {
    connectGlobalWebSocket()
  }

  window.addEventListener('resize', handleResize)
  document.addEventListener('click', hideAllContextMenus)
  document.addEventListener('contextmenu', hideAllContextMenus)
})

// 监听用户登录状态变化
watch(() => userStore.isLoggedIn, (isLoggedIn) => {
  if (isLoggedIn) {
    // 用户登录时连接全局WebSocket
    connectGlobalWebSocket()
  } else {
    // 用户登出时断开全局WebSocket
    if (globalWebSocket) {
      globalWebSocket.close()
      globalWebSocket = null
      isGlobalConnected.value = false
    }
  }
})

onUnmounted(() => {
  if (websocket) {
    websocket.close()
  }
  if (globalWebSocket) {
    globalWebSocket.close()
  }
  if (typingTimer) {
    clearTimeout(typingTimer)
  }
  window.removeEventListener('resize', handleResize)
  document.removeEventListener('click', hideAllContextMenus)
  document.removeEventListener('contextmenu', hideAllContextMenus)
})

// 监听当前聊天室变化
watch(currentRoom, (newRoom) => {
  if (newRoom?.members) {
    // 初始化在线人数
    updateOnlineCount()

    // 设置当前用户为在线状态
    const currentUser = newRoom.members.find(m => m.id === userStore.user?.id)
    if (currentUser) {
      currentUser.is_online = true
      updateOnlineCount()
    }
  }
}, { immediate: true })
</script>

<style scoped>
.modern-chat {
  width: 100%;
  display: flex;

  height: 90vh;
  background: #f5f7fa;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* 聊天室侧边栏 */
.chat-sidebar {
  width: 320px;
  background: white;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}

.chat-sidebar.mobile-hidden {
  transform: translateX(-100%);
  position: absolute;
  z-index: 1000;
  height: 100vh;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h3 {
  margin: 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.room-search {
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
}

.room-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.room-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-left: 3px solid transparent;
}

.room-item:hover {
  background: #f5f7fa;
}

.room-item.active {
  background: #ecf5ff;
  border-left-color: #409eff;
}

.room-avatar {
  position: relative;
  margin-right: 12px;
}

.room-avatar img,
.room-avatar .default-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
}

.default-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 18px;
}

/* 不同类型聊天室的头像样式 */
.room-avatar.public-room .default-avatar {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.room-avatar.group-room .default-avatar {
  background: linear-gradient(135deg, #e6a23c, #f0a020);
}

.room-avatar.private-room .default-avatar {
  background: linear-gradient(135deg, #f56c6c, #f78989);
}

.room-avatar.channel-room .default-avatar {
  background: linear-gradient(135deg, #909399, #b1b3b8);
}

/* 聊天室类型标识 */
.room-type-badge {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.room-type-badge .type-icon {
  font-size: 8px;
  color: white;
}

.room-type-badge.public-badge {
  background: #67c23a;
}

.room-type-badge.group-badge {
  background: #e6a23c;
}

.room-type-badge.private-badge {
  background: #f56c6c;
}

.room-type-badge.channel-badge {
  background: #909399;
}

.unread-badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background: #f56c6c;
  color: white;
  border-radius: 10px;
  padding: 2px 6px;
  font-size: 12px;
  min-width: 18px;
  text-align: center;
}

.room-info {
  flex: 1;
  min-width: 0;
}

.room-name-container {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.room-name {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.room-type-text {
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 8px;
  font-weight: 500;
  white-space: nowrap;
}

/* 不同类型的文本样式 */
.room-type-text.public-text {
  background: #f0f9ff;
  color: #67c23a;
  border: 1px solid #c2e7b0;
}

.room-type-text.group-text {
  background: #fdf6ec;
  color: #e6a23c;
  border: 1px solid #f5dab1;
}

.room-type-text.private-text {
  background: #fef0f0;
  color: #f56c6c;
  border: 1px solid #fbc4c4;
}

.room-type-text.channel-text {
  background: #f4f4f5;
  color: #909399;
  border: 1px solid #d3d4d6;
}

/* 创建聊天室对话框样式 */
.room-type-description {
  margin-top: 8px;
}

.type-desc {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 0;
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.4;
}

.type-desc.public-desc {
  background: #f0f9ff;
  border: 1px solid #c2e7b0;
  color: #67c23a;
}

.type-desc.group-desc {
  background: #fdf6ec;
  border: 1px solid #f5dab1;
  color: #e6a23c;
}

.type-desc.channel-desc {
  background: #f4f4f5;
  border: 1px solid #d3d4d6;
  color: #909399;
}

.type-desc .el-icon {
  margin-top: 2px;
  font-size: 14px;
}

.type-desc strong {
  color: inherit;
}

.room-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.room-last-message {
  color: #909399;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.room-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  position: relative;
}

.room-manage-dropdown {
  opacity: 0.7;
  transition: opacity 0.2s ease;
  position: absolute;
  top: 8px;
  right: 8px;
}

.room-item:hover .room-manage-dropdown {
  opacity: 1;
}

.room-item {
  position: relative;
}

.room-manage-btn {
  padding: 4px;
  min-height: auto;
  color: #909399;
}

.room-manage-btn:hover {
  color: #409eff;
  background: rgba(64, 158, 255, 0.1);
}

.room-time {
  color: #c0c4cc;
  font-size: 12px;
}

/* 主聊天区域 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  width: 100%;
}

.mobile-header {
  display: none;
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  align-items: center;
  gap: 12px;
  background: white;
}

.chat-header {
  padding: 16px 24px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
}

.chat-header .room-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-header .room-avatar img,
.chat-header .room-avatar .default-avatar {
  width: 40px;
  height: 40px;
}

.room-details h3 {
  margin: 0 0 4px 0;
  color: #303133;
  font-size: 16px;
}

.room-details p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.header-actions .el-button {
  padding: 8px 12px;
}

/* 消息区域 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
  background: #fafbfc;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
}

.message-item {
  display: flex;
  gap: 12px;
  max-width: 70%;
}

.message-item.own-message {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-item.own-message .message-content {
  background: #67c23a; /*#b6ffda 绿色#409eff */
  color: white;
}

.message-avatar img,
.message-avatar .default-avatar {
  width: 36px;
  height: 36px;
}

.message-content {
  background: white;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  max-width: 100%;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.sender-name {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.message-time {
  color: #c0c4cc;
  font-size: 12px;
}

.reply-message {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  padding: 8px 12px;
  margin-bottom: 8px;
  border-left: 3px solid #409eff;
}

.reply-sender {
  font-weight: 600;
  color: #409eff;
  font-size: 12px;
}

.reply-text {
  color: #606266;
  font-size: 12px;
  margin-left: 8px;
}

.message-text {
  line-height: 1.5;
  word-wrap: break-word;
}

.message-deleted {
  color: #c0c4cc;
  font-style: italic;
  display: flex;
  align-items: center;
  gap: 4px;
}

.message-file {
  margin-top: 8px;
}

.message-actions {
  display: flex;
  gap: 4px;
  margin-top: 8px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.message-item:hover .message-actions {
  opacity: 1;
}

.message-reactions {
  display: flex;
  gap: 4px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.reaction-item {
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  padding: 2px 8px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.reaction-item:hover {
  background: #ecf5ff;
  border-color: #409eff;
}

.reaction-item.user-reacted {
  background: #409eff;
  color: white;
  border-color: #409eff;
}

/* 正在输入提示 */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  color: #909399;
  font-size: 14px;
}

.typing-dots {
  display: flex;
  gap: 2px;
}

.typing-dots span {
  width: 4px;
  height: 4px;
  background: #909399;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* 消息输入区域 */
.chat-input {
  border-top: 1px solid #e4e7ed;
  background: white;
}

.edit-preview {
  padding: 12px 24px;
  background: #fff7e6;
  border-bottom: 1px solid #ffd591;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.edit-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.edit-content {
  color: #909399;
  font-size: 14px;
}

.reply-preview {
  padding: 12px 24px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.reply-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.reply-content {
  color: #909399;
  font-size: 14px;
}

.input-area {
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.left-actions {
  display: flex;
  gap: 8px;
}

.upload-progress {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #909399;
}

/* 空状态 */
.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 聊天室信息 */
.room-info-content {
  padding: 24px;
}

.room-header {
  text-align: center;
  margin-bottom: 32px;
}

.room-avatar.large img,
.room-avatar.large .default-avatar {
  width: 80px;
  height: 80px;
  margin: 0 auto 16px;
}

.room-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.stat-item .label {
  color: #909399;
}

.stat-item .value {
  font-weight: 600;
  color: #303133;
}

/* 成员列表 */
.member-list {
  padding: 16px;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.member-avatar {
  position: relative;
}

.member-avatar img,
.member-avatar .default-avatar {
  width: 40px;
  height: 40px;
}

.online-indicator {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #c0c4cc;
  border: 2px solid white;
}

.online-indicator.online {
  background: #67c23a;
}

.member-info {
  flex: 1;
}

.member-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.member-role {
  color: #909399;
  font-size: 14px;
}

.member-actions {
  display: flex;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-sidebar {
    width: 100%;
    position: fixed;
    z-index: 1000;
  }

  .mobile-header {
    display: flex;
  }

  .chat-messages {
    padding: 12px 16px;
  }

  .message-item {
    max-width: 85%;
  }

  .input-area {
    padding: 12px 16px;
  }

  .chat-header {
    padding: 12px 16px;
  }
}

/* 滚动条样式 */
.room-list::-webkit-scrollbar,
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.room-list::-webkit-scrollbar-track,
.chat-messages::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.room-list::-webkit-scrollbar-thumb,
.chat-messages::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}

.room-list::-webkit-scrollbar-thumb:hover,
.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #909399;
}

/* 表情选择器 */
.emoji-picker {
  max-height: 400px;
}

.emoji-categories {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.emoji-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.emoji-item {
  font-size: 24px;
  padding: 8px;
  text-align: center;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.emoji-item:hover {
  background: #f5f7fa;
  transform: scale(1.2);
}

/* 右键菜单 */
.context-menu {
  position: fixed !important;
  background: white !important;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 9999999 !important;
  min-width: 150px;
  padding: 4px 0;
  user-select: none;
  pointer-events: auto !important;
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  cursor: pointer;
  transition: background 0.2s ease;
  font-size: 14px;
}

.context-menu-item:hover {
  background: #f5f7fa;
}

.context-menu-item.danger {
  color: #f56c6c;
}

.context-menu-item.danger:hover {
  background: #fef0f0;
}

.context-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 99998;
  background: transparent;
}

/* 消息操作按钮增强 */
.message-actions .el-button {
  opacity: 0.7;
  transition: all 0.2s ease;
}

.message-actions .el-button:hover {
  opacity: 1;
  transform: scale(1.1);
}

/* 文件消息样式 */
.message-file {
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 12px;
  margin-top: 8px;
}

.message-file .el-link {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

/* 图片消息样式 */
.message-image {
  margin-top: 8px;
  border-radius: 8px;
  overflow: hidden;
  max-width: 300px;
}

.message-image img {
  width: 100%;
  height: auto;
  display: block;
}

/* 动画效果 */
@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-item {
  animation: messageSlideIn 0.3s ease;
}

/* 编辑状态样式 */
.message-item.editing .message-content {
  border: 2px solid #409eff;
  background: #ecf5ff;
}

/* 提及样式 */
.mention {
  color: #409eff;
  background: #ecf5ff;
  padding: 2px 4px;
  border-radius: 4px;
  font-weight: 500;
}

/* 链接样式 */
.message-link {
  color: #409eff;
  text-decoration: underline;
  cursor: pointer;
}

.message-link:hover {
  color: #66b1ff;
}

/* 私聊对话框样式 */
.private-chat-form {
  padding: 10px 0;
}

.user-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-name {
  font-weight: 500;
  color: #303133;
}

.user-nickname {
  font-size: 12px;
  color: #909399;
}

.quick-users {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.user-tag {
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-tag:hover {
  background: #ecf5ff;
  border-color: #409eff;
}

.user-tag.active {
  background: #409eff;
  color: white;
  border-color: #409eff;
}

/* 聊天室类型描述样式 */
.room-type-description {
  margin-top: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #409eff;
}

.type-desc {
  margin: 0;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 14px;
  line-height: 1.5;
  color: #606266;
}

.type-desc .el-icon {
  margin-top: 2px;
  color: #409eff;
}

.type-desc strong {
  color: #303133;
}

/* 群聊和频道的不同颜色 */
.room-type-description[data-type="group"] {
  border-left-color: #67c23a;
}

.room-type-description[data-type="group"] .el-icon {
  color: #67c23a;
}

.room-type-description[data-type="channel"] {
  border-left-color: #e6a23c;
}

.room-type-description[data-type="channel"] .el-icon {
  color: #e6a23c;
}

/* 聊天室最后消息样式 */
.room-last-message {
  display: flex;
  align-items: center;
  gap: 4px;
  overflow: hidden;
}

.message-sender {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
}

.message-content {
  font-size: 12px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.no-message {
  font-size: 12px;
  color: #c0c4cc;
  font-style: italic;
}

/* 聊天室信息对话框样式 */
.clickable-room-name {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: color 0.2s ease;
}

.clickable-room-name:hover {
  color: #409eff;
}

.room-info-icon {
  font-size: 14px;
  opacity: 0.7;
}

.room-info-dialog {
  padding: 16px 0;
}

.room-basic-info {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.room-avatar.large {
  width: 60px;
  height: 60px;
  position: relative;
}

.room-avatar.large .default-avatar {
  font-size: 24px;
}

.room-info-text h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
}

.room-description {
  color: #606266;
  margin: 0 0 12px 0;
  line-height: 1.4;
}

.room-meta {
  display: flex;
  gap: 12px;
  align-items: center;
}

.room-stats {
  color: #909399;
  font-size: 13px;
}

.room-actions {
  space-y: 24px;
}

.action-section {
  margin-bottom: 24px;
}

.action-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.invite-code-section {
  space-y: 12px;
}

.invite-code-display {
  margin-bottom: 8px;
}

.invite-code-input {
  font-family: 'Courier New', monospace;
}

.invite-code-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #909399;
  margin-bottom: 12px;
}

.expired-tag {
  color: #f56c6c;
  font-weight: 500;
}

.invite-code-actions {
  text-align: right;
}

.no-invite-code {
  text-align: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 6px;
}

.no-invite-code p {
  margin: 0 0 12px 0;
  color: #909399;
}

/* 创建聊天室高级设置样式 */
.advanced-settings {
  margin-top: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.advanced-settings h4 {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
  color: #495057;
}

.setting-description {
  margin-top: 4px;
}

.setting-description small {
  color: #6c757d;
  font-size: 12px;
  line-height: 1.4;
}

/* 加入聊天室页面样式 */
.join-room-content {
  padding: 16px 0;
}

.join-room-tabs .el-tabs__content {
  padding-top: 16px;
}

.search-room-section {
  space-y: 16px;
}

.search-results {
  margin-top: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.room-search-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.room-search-item:hover {
  border-color: #409eff;
  background: #f0f9ff;
}

.room-search-item .room-avatar {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
}

.room-search-item .room-info {
  flex: 1;
  min-width: 0;
}

.room-search-item .room-name {
  font-weight: 500;
  font-size: 14px;
  margin-bottom: 4px;
}

.room-search-item .room-description {
  color: #606266;
  font-size: 12px;
  margin-bottom: 4px;
  line-height: 1.4;
}

.room-search-item .room-stats {
  color: #909399;
  font-size: 11px;
}

.room-search-item .join-action {
  flex-shrink: 0;
}

.no-results {
  text-align: center;
  padding: 40px 20px;
}

.invite-code-section {
  padding: 16px;
}

.invite-code-actions {
  text-align: right;
  margin-top: 16px;
}

/* 系统消息容器样式 */
.system-message-container {
  display: flex;
  justify-content: center;
  margin: 16px 0;
  padding: 0 20px;
}

/* 系统消息样式 */
.message-system {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 20px;
  color: #0369a1;
  font-size: 13px;
  max-width: 80%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

/* 不同类型系统消息的样式 */
.message-system.system-success {
  background: #f0f9f0;
  border-color: #86efac;
  color: #166534;
}

.message-system.system-warning {
  background: #fffbeb;
  border-color: #fbbf24;
  color: #92400e;
}

.message-system.system-danger {
  background: #fef2f2;
  border-color: #fca5a5;
  color: #991b1b;
}

.message-system.system-crown {
  background: #fef3c7;
  border-color: #fbbf24;
  color: #92400e;
}

.message-system.system-pin {
  background: #f3e8ff;
  border-color: #c4b5fd;
  color: #7c3aed;
}

.message-system.system-file {
  background: #ecfdf5;
  border-color: #86efac;
  color: #166534;
}

.message-system.system-join-request {
  background: #fff7ed;
  border-color: #fdba74;
  color: #ea580c;
}

.message-system .system-text {
  flex: 1;
}

.message-system .system-actions {
  display: flex;
  gap: 8px;
  margin-left: 12px;
}

.system-user-info {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
}

/* 固定置顶消息条 */
.fixed-pinned-message {
  position: sticky;
  top: 0;
  z-index: 100;
  background: linear-gradient(135deg, #fef3c7 0%, #fbbf24 100%);
  border: 1px solid #f59e0b;
  border-radius: 8px;
  margin: 8px 12px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.2);
}

.fixed-pinned-message:hover {
  background: linear-gradient(135deg, #fde68a 0%, #f59e0b 100%);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
  transform: translateY(-1px);
}

.pinned-message-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #92400e;
  font-weight: 600;
  font-size: 13px;
  flex-shrink: 0;
}

.pin-icon {
  color: #f59e0b;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.pinned-message-preview {
  flex: 1;
  min-width: 0;
  color: #92400e;
  font-size: 14px;
}

.pinned-sender {
  font-weight: 600;
  margin-right: 6px;
}

.pinned-content {
  color: #78350f;
  word-break: break-word;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pinned-message-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.pinned-message-actions .el-button {
  color: #92400e;
  border: none;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  padding: 4px 8px;
  height: auto;
}

.pinned-message-actions .el-button:hover {
  background: rgba(255, 255, 255, 0.5);
  color: #78350f;
}

/* 消息高亮动画 */
.message-highlight {
  background: #fef3c7 !important;
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(251, 191, 36, 0.3) !important;
}

.message-highlight .message-system {
  background: #fef3c7 !important;
  border-color: #fbbf24 !important;
}

.message-system .system-actions .el-button {
  padding: 4px 8px;
  font-size: 12px;
  height: auto;
}

/* 置顶消息区域样式 */
.pinned-messages-area {
  background: #fff9e6;
  border: 1px solid #ffd666;
  border-radius: 8px;
  margin: 12px;
  overflow: hidden;
}

.pinned-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #fff2cc;
  border-bottom: 1px solid #ffd666;
  font-size: 13px;
  font-weight: 500;
  color: #d48806;
}

.pinned-header .el-icon {
  color: #faad14;
}

.pinned-messages-list {
  max-height: 200px;
  overflow-y: auto;
}

.pinned-message-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid #fff7e6;
}

.pinned-message-item:last-child {
  border-bottom: none;
}

.pinned-message-content {
  flex: 1;
  min-width: 0;
}

.pinned-message-content .sender-name {
  font-weight: 500;
  color: #1890ff;
  margin-right: 4px;
}

.pinned-message-content .message-text {
  color: #595959;
  word-break: break-word;
}

.pinned-message-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.pinned-message-actions .el-button {
  padding: 2px 6px;
  font-size: 11px;
  height: auto;
}

/* 消息高亮效果 */
.highlight-message {
  background: #fff2cc !important;
  border: 2px solid #faad14 !important;
  border-radius: 6px;
  animation: highlight-pulse 2s ease-in-out;
}

@keyframes highlight-pulse {
  0%, 100% {
    background: #fff2cc;
  }
  50% {
    background: #ffd666;
  }
}

/* 成员管理样式 */
.member-management {
  padding: 16px 0;
}

.member-stats {
  display: flex;
  gap: 32px;
  margin-bottom: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.member-search {
  margin-bottom: 16px;
}

.member-list {
  max-height: 400px;
  overflow-y: auto;
}

.member-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  margin-bottom: 8px;
  transition: all 0.2s ease;
}

.member-item:hover {
  border-color: #409eff;
  background: #f0f9ff;
}

.member-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.member-details {
  flex: 1;
  min-width: 0;
}

.member-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  margin-bottom: 4px;
}

.member-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #909399;
}

.member-actions {
  flex-shrink: 0;
}

.join-time {
  color: #909399;
}

/* 置顶消息样式 */
.pinned-message {
  border-left: 3px solid #faad14 !important;
  background: #fff9e6 !important;
}

/* 邀请用户对话框样式 */
.invite-user-content {
  padding: 16px 0;
}

.user-search-results {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.user-search-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.user-search-item:hover {
  background: #f8f9fa;
}

.user-search-item:last-child {
  border-bottom: none;
}

.user-search-item .user-info {
  flex: 1;
  min-width: 0;
}

.user-search-item .user-name {
  font-weight: 500;
  margin-bottom: 2px;
}

.user-search-item .user-username {
  font-size: 12px;
  color: #909399;
}

.selected-user {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f0f9ff;
  border: 1px solid #409eff;
  border-radius: 6px;
}

.selected-user .user-info {
  flex: 1;
  min-width: 0;
}

/* 退出聊天室对话框样式 */
.leave-room-content {
  text-align: center;
  padding: 20px 0;
}

.leave-room-content .warning-icon {
  font-size: 48px;
  color: #f56c6c;
  margin-bottom: 16px;
}

.leave-room-content p {
  font-size: 14px;
  color: #606266;
  margin: 0;
  line-height: 1.5;
}

/* 右键菜单危险选项样式 */
.context-menu-item.danger {
  color: #f56c6c;
}

.context-menu-item.danger:hover {
  background: #fef0f0;
  color: #f56c6c;
}

/* 聊天室统计信息样式 */
.room-statistics {
  padding: 20px 0;
}

.room-statistics .el-statistic {
  text-align: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.top-users {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.top-users h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 500;
}

.top-user-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}

.top-user-item:last-child {
  border-bottom: none;
}

.top-user-item .user-name {
  font-weight: 500;
  color: #409eff;
}

.top-user-item .message-count {
  color: #909399;
  font-size: 12px;
}

.room-info {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.room-info p {
  margin: 8px 0;
  color: #606266;
  font-size: 14px;
}

.room-info strong {
  color: #303133;
}

/* 消息类型样式 */
.message-image {
  margin: 8px 0;
}

.chat-image {
  max-width: 300px;
  max-height: 200px;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s;
  display: block;
}

.chat-image:hover {
  transform: scale(1.02);
}

.image-info {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
  display: flex;
  justify-content: space-between;
}

.message-file {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  margin: 8px 0;
}

.file-icon {
  font-size: 24px;
  color: #409eff;
}

.file-info {
  flex: 1;
}

.file-name {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.file-size {
  font-size: 12px;
  color: #909399;
}

.message-system {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f0f9ff;
  border: 1px solid #b3d8ff;
  border-radius: 6px;
  color: #409eff;
  font-size: 13px;
  margin: 8px 0;
}

/* 图片预览对话框 */
.image-preview-dialog {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 10000;
}

.image-preview-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.image-preview-container {
  position: relative;
  max-width: 90%;
  max-height: 90%;
  cursor: default;
}

.image-preview-container img {
  max-width: 100%;
  max-height: 100%;
  border-radius: 8px;
}

.image-preview-close {
  position: absolute;
  top: -40px;
  right: 0;
  background: rgba(255, 255, 255, 0.9);
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.image-preview-close:hover {
  background: white;
}
</style>
