<template>
  <div class="user-profile">
    <h1>个人资料</h1>

    <v-card class="mt-4">
      <v-card-title>个人信息</v-card-title>
      <v-card-text>
        <v-form ref="form" v-model="valid" lazy-validation>
          <v-row>
            <!-- 头像，使用图片上传 -->
            <v-col cols="12" md="6">
              <div class="avatar-upload-container">
                <!-- 头像预览 -->
                <v-img
                  v-if="userForm.avatar"
                  :src="userForm.avatar"
                  alt="用户头像"
                  max-width="120"
                  max-height="120"
                  class="avatar-preview"
                  cover
                ></v-img>

                <!-- 默认头像（当avatar为空时） -->
                <div v-else class="default-avatar">
                  <v-icon size="64" color="grey lighten-1">mdi-account-circle</v-icon>
                </div>

                <!-- 上传按钮 -->
                <v-btn small color="primary" class="mt-2" @click="$refs.avatarInput.click()">
                  更换头像
                </v-btn>
                <input
                  ref="avatarInput"
                  type="file"
                  accept="image/*"
                  style="display: none"
                  @change="handleAvatarUpload"
                />
              </div>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="userForm.username"
                label="用户名"
                readonly
                outlined
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="userForm.email"
                label="邮箱"
                outlined
                :rules="emailRules"
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model="userForm.nickname" label="昵称" outlined></v-text-field>
            </v-col>

            <v-col cols="12">
              <v-btn
                color="primary"
                @click="updateProfile"
                :loading="loading"
                :disabled="!valid || !hasChanges"
              >
                保存更改
              </v-btn>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
    </v-card>

    <v-card class="mt-4">
      <v-card-title>修改密码</v-card-title>
      <v-card-text>
        <v-form ref="passwordForm" v-model="passwordValid" lazy-validation>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="passwordForm.current_password"
                label="当前密码"
                type="password"
                outlined
                :rules="[(v) => !!v || '请输入当前密码']"
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="passwordForm.new_password"
                label="新密码"
                type="password"
                outlined
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="passwordForm.confirm_password"
                label="确认新密码"
                type="password"
                outlined
                :rules="[
                  (v) => !!v || '请确认新密码',
                  (v) => v === passwordForm.new_password || '两次输入的密码不一致',
                ]"
              ></v-text-field>
            </v-col>
            <v-col cols="12">
              <v-btn
                color="primary"
                @click="updatePassword"
                :loading="passwordLoading"
                :disabled="!passwordValid"
              >
                更新密码
              </v-btn>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
    </v-card>

    <v-card class="mt-4">
      <v-card-title>账户信息</v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="6">
            <div class="info-item">
              <div class="label">账户状态:</div>
              <div class="value">
                <v-chip :color="userInfo.is_active ? 'success' : 'error'" text-color="white" small>
                  {{ userInfo.is_active ? '已激活' : '未激活' }}
                </v-chip>
              </div>
            </div>
          </v-col>
          <v-col cols="12" md="6">
            <div class="info-item">
              <div class="label">用户角色:</div>
              <div class="value">
                <v-chip
                  v-for="(role, index) in userInfo.roles"
                  :key="index"
                  color="primary"
                  class="mr-2 mb-2"
                  small
                >
                  {{ role.name }}
                </v-chip>
                <span v-if="!userInfo.roles || userInfo.roles.length === 0">无角色</span>
              </div>
            </div>
          </v-col>
          <v-col cols="12">
            <div class="info-item">
              <div class="label">注册时间:</div>
              <div class="value">{{ formatDate(userInfo.created_at) }}</div>
            </div>
          </v-col>
          <v-col cols="12">
            <div class="info-item">
              <div class="label">最后登录:</div>
              <div class="value">{{ formatDate(userInfo.last_login) }}</div>
            </div>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-card class="mt-4" v-if="userInfo.is_superuser">
      <v-card-title>权限信息</v-card-title>
      <v-card-text shadow="hover">
        <div class="value">
          <div
            v-for="(role, index) in userInfo.roles"
            :key="index"
            color="primary"
            class="mr-2 mb-2"
            small
          >
            <div class="permissions-list">
              <v-chip
                v-for="(permission, index) in role.permissions"
                :key="index"
                color="info"
                class="mr-2 mb-2"
                small
              >
                {{ permission.name }}
              </v-chip>
              <span v-if="!role.permissions || role.permissions.length === 0">无特殊权限</span>
            </div>
            <hr />
          </div>
          <span v-if="!userInfo.roles || userInfo.roles.length === 0">无角色</span>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import { fetchUserInfo, updateUserInfo, updatePassword } from '@/api/auth'
import Toast from '@/utils/toast'

export default {
  name: 'UserProfile',
  data() {
    return {
      userInfo: {},
      userForm: {
        username: '',
        email: '',
        nickname: '',
      },
      originalUserForm: {},
      loading: false,
      valid: true,
      emailRules: [
        (v) => !!v || '邮箱不能为空',
        (v) => /.+@.+\..+/.test(v) || '请输入有效的邮箱地址',
      ],
      passwordForm: {
        current_password: '',
        new_password: '',
        confirm_password: '',
      },
      passwordValid: true,
      passwordLoading: false,
      passwordRules: [
        (v) => !!v || '密码不能为空',
        (v) => (v && v.length >= 8) || '密码长度至少为8个字符',
      ],
    }
  },
  computed: {
    hasChanges() {
      return JSON.stringify(this.userForm) !== JSON.stringify(this.originalUserForm)
    },
  },
  async created() {
    await this.fetchUserProfile()
  },
  beforeUnmount() {
    //if (this.userForm.avatar.startsWith('blob:')) {
    //  URL.revokeObjectURL(this.userForm.avatar);
    //}
  },
  methods: {
    handleAvatarUpload(event) {
      const file = event.target.files[0]
      if (!file) return

      // 预览图片（临时URL）
      this.userForm.avatar = URL.createObjectURL(file)
      //设置预览图片大小，width:100px,height:100px

      // 实际处理上传逻辑
      // this.uploadAvatar(file);
    },

    async fetchUserProfile() {
      try {
        this.loading = true
        const response = await fetchUserInfo()
        this.userInfo = response

        // 设置表单数据
        this.userForm = {
          username: this.userInfo.username,
          email: this.userInfo.email,
          nickname: this.userInfo.nickname || '',
        }

        // 保存原始表单数据用于比较
        this.originalUserForm = { ...this.userForm }

        this.loading = false
      } catch (error) {
        console.error('获取用户资料失败', error)
        Toast.error('获取用户资料失败')
        this.loading = false
      }
    },
    async updateProfile() {
      if (!this.$refs.form.validate()) return

      try {
        this.loading = true
        await updateUserInfo(this.userForm)
        Toast.success('个人资料更新成功')

        // 更新原始表单数据
        this.originalUserForm = { ...this.userForm }

        // 刷新用户资料
        await this.fetchUserProfile()
      } catch (error) {
        console.error('更新个人资料失败', error)
        Toast.error('更新个人资料失败')
      } finally {
        this.loading = false
      }
    },
    async updatePassword() {
      if (!this.$refs.passwordForm.validate()) return

      try {
        this.passwordLoading = true
        await updatePassword(this.passwordForm)

        Toast.success('密码更新成功')

        // 清空密码表单
        this.passwordForm = {
          current_password: '',
          new_password: '',
          confirm_password: '',
        }

        // 重置表单验证
        this.$refs.passwordForm.resetValidation()
      } catch (error) {
        console.error('更新密码失败', error)
        Toast.error(error.response?.data?.detail || '更新密码失败')
      } finally {
        this.passwordLoading = false
      }
    },
    formatDate(dateString) {
      if (!dateString) return '未知'

      const date = new Date(dateString)
      return new Intl.DateTimeFormat('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }).format(date)
    },
  },
}
</script>

<style scoped>
.user-profile {
  padding: 20px;
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
}

.info-item {
  margin-bottom: 15px;
  display: flex;
}

.label {
  font-weight: bold;
  width: 120px;
  flex-shrink: 0;
}

.value {
  flex-grow: 1;
}

.permissions-list {
  display: flex;
  flex-wrap: wrap;
}

.avatar-upload-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.avatar-preview {
  border-radius: 50%;
  border: 3px solid #eee;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.avatar-preview:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.default-avatar {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed #ddd;
}
</style>
