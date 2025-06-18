<template>
    <div class="settings-container">
      <h1>系统设置</h1>
      
      <div class="settings-nav">
        <ul class="nav nav-tabs">
          <li class="nav-item">
            <a 
              class="nav-link" 
              :class="{ active: activeTab === 'general' }" 
              href="#"
              @click.prevent="activeTab = 'general'"
            >
              常规设置
            </a>
          </li>
          <li class="nav-item">
            <a 
              class="nav-link" 
              :class="{ active: activeTab === 'users' }" 
              href="#"
              @click.prevent="activeTab = 'users'"
            >
              用户管理
            </a>
          </li>
          <li class="nav-item">
            <a 
              class="nav-link" 
              :class="{ active: activeTab === 'permissions' }" 
              href="#"
              @click.prevent="activeTab = 'permissions'"
            >
              权限设置
            </a>
          </li>
          <li class="nav-item">
            <a 
              class="nav-link" 
              :class="{ active: activeTab === 'scheduler' }" 
              href="#"
              @click.prevent="activeTab = 'scheduler'"
            >
              定时任务
            </a>
          </li>
        </ul>
      </div>
      
      <div class="settings-content mt-4">
        <!-- 常规设置 -->
        <div v-if="activeTab === 'general'">
          <h2>常规设置</h2>
          <form @submit.prevent="saveGeneralSettings">
            <div class="row mb-4">
              <div class="col-md-6">
                <div class="card">
                  <div class="card-header">
                    系统功能
                  </div>
                  <div class="card-body">
                    <div class="form-check form-switch mb-3">
                      <input 
                        class="form-check-input" 
                        type="checkbox" 
                        id="enableChat" 
                        v-model="generalSettings.enable_chat"
                      >
                      <label class="form-check-label" for="enableChat">启用聊天功能</label>
                    </div>
                    <div class="form-check form-switch mb-3">
                      <input 
                        class="form-check-input" 
                        type="checkbox" 
                        id="enableExtensions" 
                        v-model="generalSettings.enable_extensions"
                      >
                      <label class="form-check-label" for="enableExtensions">启用扩展管理</label>
                    </div>
                    <div class="form-check form-switch mb-3">
                      <input 
                        class="form-check-input" 
                        type="checkbox" 
                        id="enableLogs" 
                        v-model="generalSettings.enable_logs"
                      >
                      <label class="form-check-label" for="enableLogs">启用日志管理</label>
                    </div>
                    <div class="form-check form-switch mb-3">
                      <input 
                        class="form-check-input" 
                        type="checkbox" 
                        id="enableFiles" 
                        v-model="generalSettings.enable_files"
                      >
                      <label class="form-check-label" for="enableFiles">启用文件管理</label>
                    </div>
                  </div>
                </div>
              </div>
              <div class="col-md-6">
                <div class="card">
                  <div class="card-header">
                    系统信息
                  </div>
                  <div class="card-body">
                    <div class="mb-3">
                      <label for="systemName" class="form-label">系统名称</label>
                      <input 
                        type="text" 
                        class="form-control" 
                        id="systemName" 
                        v-model="generalSettings.system_name"
                      >
                    </div>
                    <div class="mb-3">
                      <label for="adminEmail" class="form-label">管理员邮箱</label>
                      <input 
                        type="email" 
                        class="form-control" 
                        id="adminEmail" 
                        v-model="generalSettings.admin_email"
                      >
                    </div>
                    <div class="mb-3">
                      <label for="maxUploadSize" class="form-label">最大上传大小 (MB)</label>
                      <input 
                        type="number" 
                        class="form-control" 
                        id="maxUploadSize" 
                        v-model.number="generalSettings.max_upload_size"
                        min="1"
                      >
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="d-flex justify-content-end">
              <button type="submit" class="btn btn-primary" :disabled="savingGeneral">
                {{ savingGeneral ? '保存中...' : '保存设置' }}
              </button>
            </div>
          </form>
        </div>
        
        <!-- 用户管理 -->
        <div v-if="activeTab === 'users'">
          <div class="d-flex justify-content-between align-items-center mb-4">
            <h2>用户管理</h2>
            <button class="btn btn-primary" @click="showCreateUserModal = true">
              <i class="bi bi-person-plus"></i> 添加用户
            </button>
          </div>
          
          <div class="table-responsive">
            <table class="table table-striped">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>用户名</th>
                  <th>昵称</th>
                  <th>邮箱</th>
                  <th>角色</th>
                  <th>最后登录</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in users" :key="user.id">
                  <td>{{ user.id }}</td>
                  <td>{{ user.username }}</td>
                  <td>{{ user.nickname }}</td>
                  <td>{{ user.email }}</td>
                  <td>
                    <span class="badge" :class="getRoleBadgeClass(user.role)">
                      {{ user.role }}
                    </span>
                  </td>
                  <td>{{ formatDate(user.last_login) }}</td>
                  <td>
                    <div class="btn-group btn-group-sm">
                      <button class="btn btn-outline-primary" @click="editUser(user)">
                        <i class="bi bi-pencil"></i>
                      </button>
                      <button 
                        class="btn btn-outline-danger" 
                        @click="deleteUser(user)" 
                        :disabled="user.id === currentUser.id"
                      >
                        <i class="bi bi-trash"></i>
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- 权限设置 -->
        <div v-if="activeTab === 'permissions'">
          <h2>权限设置</h2>
          <div class="alert alert-info">
            <p>在此页面配置不同角色的权限。</p>
          </div>
          
          <div class="card mb-4">
            <div class="card-header">
              <ul class="nav nav-tabs card-header-tabs">
                <li class="nav-item" v-for="role in roles" :key="role">
                  <a 
                    class="nav-link" 
                    :class="{ active: activeRole === role }" 
                    href="#"
                    @click.prevent="activeRole = role"
                  >
                    {{ role }}
                  </a>
                </li>
              </ul>
            </div>
            <div class="card-body">
              <div v-if="loadingPermissions" class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                  <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">加载权限...</p>
              </div>
              <div v-else>
                <div v-for="(perms, resource) in permissions" :key="resource" class="mb-4">
                  <h4>{{ resource }}</h4>
                  <div class="form-check mb-2" v-for="(enabled, action) in perms" :key="action">
                    <input 
                      class="form-check-input" 
                      type="checkbox" 
                      :id="`perm-${resource}-${action}`" 
                      v-model="permissions[resource][action]"
                    >
                    <label class="form-check-label" :for="`perm-${resource}-${action}`">
                      {{ action }}
                    </label>
                  </div>
                </div>
                
                <div class="d-flex justify-content-end mt-4">
                  <button class="btn btn-primary" @click="savePermissions" :disabled="savingPermissions">
                    {{ savingPermissions ? '保存中...' : '保存权限' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 定时任务 -->
        <div v-if="activeTab === 'scheduler'">
          <h2>定时任务</h2>
          <div class="alert alert-info">
            <p>在此页面管理系统定时任务。</p>
          </div>
          
          <div class="card mb-4">
            <div class="card-header">
              <div class="d-flex justify-content-between align-items-center">
                <span>任务列表</span>
                <button class="btn btn-sm btn-primary" @click="showCreateTaskModal = true">
                  <i class="bi bi-plus-circle"></i> 添加任务
                </button>
              </div>
            </div>
            <div class="card-body">
              <div v-if="loadingTasks" class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                  <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">加载任务...</p>
              </div>
              <div v-else-if="!tasks.length" class="text-center py-4">
                <p>没有定时任务。</p>
              </div>
              <div v-else>
                <div class="table-responsive">
                  <table class="table table-striped">
                    <thead>
                      <tr>
                        <th>名称</th>
                        <th>函数</th>
                        <th>计划</th>
                        <th>状态</th>
                        <th>上次运行</th>
                        <th>操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="task in tasks" :key="task.id">
                        <td>{{ task.name }}</td>
                        <td>{{ task.func_path }}</td>
                        <td>{{ task.schedule }}</td>
                        <td>
                          <span class="badge" :class="task.enabled ? 'bg-success' : 'bg-secondary'">
                            {{ task.enabled ? '启用' : '禁用' }}
                          </span>
                        </td>
                        <td>{{ formatDate(task.last_run) }}</td>
                        <td>
                          <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" @click="editTask(task)">
                              <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-outline-secondary" @click="runTask(task)">
                              <i class="bi bi-play"></i>
                            </button>
                            <button class="btn btn-outline-danger" @click="deleteTask(task)">
                              <i class="bi bi-trash"></i>
                            </button>
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 创建用户模态框 -->
      <div class="modal" v-if="showCreateUserModal">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">{{ editingUser ? '编辑用户' : '创建用户' }}</h5>
              <button type="button" class="btn-close" @click="closeUserModal"></button>
            </div>
            <div class="modal-body">
              <form @submit.prevent="saveUser">
                <div class="mb-3">
                  <label for="username" class="form-label">用户名</label>
                  <input 
                    type="text" 
                    class="form-control" 
                    id="username" 
                    v-model="userForm.username" 
                    required
                    :disabled="editingUser"
                  >
                </div>
                <div class="mb-3">
                  <label for="nickname" class="form-label">昵称</label>
                  <input 
                    type="text" 
                    class="form-control" 
                    id="nickname" 
                    v-model="userForm.nickname"
                  >
                </div>
                <div class="mb-3">
                  <label for="email" class="form-label">邮箱</label>
                  <input 
                    type="email" 
                    class="form-control" 
                    id="email" 
                    v-model="userForm.email"
                  >
                </div>
                <div class="mb-3">
                  <label for="password" class="form-label">
                    {{ editingUser ? '密码 (留空不修改)' : '密码' }}
                  </label>
                  <input 
                    type="password" 
                    class="form-control" 
                    id="password" 
                    v-model="userForm.password"
                    :required="!editingUser"
                  >
                </div>
                <div class="mb-3">
                  <label for="role" class="form-label">角色</label>
                  <select class="form-select" id="role" v-model="userForm.role" required>
                    <option v-for="role in roles" :key="role" :value="role">{{ role }}</option>
                  </select>
                </div>
                <div class="modal-footer">
                  <button type="button" class="btn btn-secondary" @click="closeUserModal">取消</button>
                  <button type="submit" class="btn btn-primary" :disabled="savingUser">
                    {{ savingUser ? '保存中...' : '保存' }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 创建任务模态框 -->
      <div class="modal" v-if="showCreateTaskModal">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">{{ editingTask ? '编辑任务' : '创建任务' }}</h5>
              <button type="button" class="btn-close" @click="closeTaskModal"></button>
            </div>
            <div class="modal-body">
              <form @submit.prevent="saveTask">
                <div class="mb-3">
                  <label for="taskName" class="form-label">任务名称</label>
                  <input 
                    type="text" 
                    class="form-control" 
                    id="taskName" 
                    v-model="taskForm.name" 
                    required
                  >
                </div>
                <div class="mb-3">
                  <label for="taskFunc" class="form-label">函数路径</label>
                  <input 
                    type="text" 
                    class="form-control" 
                    id="taskFunc" 
                    v-model="taskForm.func_path"
                    required
                  >
                  <small class="form-text text-muted">例如: app.tasks.my_task.run_task</small>
                </div>
                <div class="mb-3">
                  <label for="taskSchedule" class="form-label">计划</label>
                  <input 
                    type="text" 
                    class="form-control" 
                    id="taskSchedule" 
                    v-model="taskForm.schedule"
                    required
                  >
                  <small class="form-text text-muted">Cron表达式，例如: */5 * * * * (每5分钟)</small>
                </div>
                <div class="form-check mb-3">
                  <input 
                    class="form-check-input" 
                    type="checkbox" 
                    id="taskEnabled" 
                    v-model="taskForm.enabled"
                  >
                  <label class="form-check-label" for="taskEnabled">启用任务</label>
                </div>
                <div class="modal-footer">
                  <button type="button" class="btn btn-secondary" @click="closeTaskModal">取消</button>
                  <button type="submit" class="btn btn-primary" :disabled="savingTask">
                    {{ savingTask ? '保存中...' : '保存' }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import axios from '@/utils/axios'
  
  export default {
    name: 'SettingsView',
    data() {
      return {
        activeTab: 'general',
        activeRole: 'admin',
        roles: ['admin', 'manager', 'user', 'readonly'],
        
        // 常规设置
        generalSettings: {
          enable_chat: true,
          enable_extensions: true,
          enable_logs: true,
          enable_files: true,
          system_name: '数据查询系统',
          admin_email: '',
          max_upload_size: 10
        },
        savingGeneral: false,
        
        // 用户管理
        users: [],
        currentUser: {},
        showCreateUserModal: false,
        editingUser: null,
        userForm: {
          username: '',
          nickname: '',
          email: '',
          password: '',
          role: 'user'
        },
        savingUser: false,
        
        // 权限设置
        permissions: {},
        loadingPermissions: false,
        savingPermissions: false,
        
        // 定时任务
        tasks: [],
        loadingTasks: false,
        showCreateTaskModal: false,
        editingTask: null,
        taskForm: {
          name: '',
          func_path: '',
          schedule: '',
          enabled: true
        },
        savingTask: false
      }
    },
    created() {
      this.fetchCurrentUser()
      this.fetchGeneralSettings()
      
      if (this.$route.hash) {
        const tab = this.$route.hash.substring(1)
        if (['general', 'users', 'permissions', 'scheduler'].includes(tab)) {
          this.activeTab = tab
        }
      }
      
      this.$watch('activeTab', (newValue) => {
        this.$router.replace({ hash: `#${newValue}` })
        
        if (newValue === 'users' && !this.users.length) {
          this.fetchUsers()
        } else if (newValue === 'permissions') {
          this.fetchPermissions()
        } else if (newValue === 'scheduler' && !this.tasks.length) {
          this.fetchTasks()
        }
      })
      
      this.$watch('activeRole', () => {
        this.fetchPermissions()
      })
    },
    methods: {
      async fetchCurrentUser() {
        try {
          const response = await axios.get('/api/auth/current-user')
          this.currentUser = response.data
        } catch (error) {
          console.error('获取当前用户失败', error)
        }
      },
      
      async fetchGeneralSettings() {
        try {
          const response = await axios.get('/api/settings/general')
          this.generalSettings = response.data
        } catch (error) {
          console.error('获取常规设置失败', error)
        }
      },
      
      async saveGeneralSettings() {
        this.savingGeneral = true
        
        try {
          await axios.post('/api/settings/general', this.generalSettings)
          alert('设置保存成功')
        } catch (error) {
          console.error('保存设置失败', error)
          alert('保存设置失败: ' + (error.response?.data?.detail || error.message))
        } finally {
          this.savingGeneral = false
        }
      },
      
      async fetchUsers() {
        try {
          const response = await axios.get('/api/users')
          this.users = response.data
        } catch (error) {
          console.error('获取用户列表失败', error)
        }
      },
      
      editUser(user) {
        this.editingUser = user
        this.userForm = {
          username: user.username,
          nickname: user.nickname || '',
          email: user.email || '',
          password: '',
          role: user.role
        }
        this.showCreateUserModal = true
      },
      
      closeUserModal() {
        this.showCreateUserModal = false
        this.editingUser = null
        this.userForm = {
          username: '',
          nickname: '',
          email: '',
          password: '',
          role: 'user'
        }
      },
      
      async saveUser() {
        this.savingUser = true
        
        try {
          if (this.editingUser) {
            // 更新用户
            await axios.put(`/api/users/${this.editingUser.id}`, this.userForm)
          } else {
            // 创建用户
            await axios.post('/api/users', this.userForm)
          }
          
          this.closeUserModal()
          this.fetchUsers()
        } catch (error) {
          console.error('保存用户失败', error)
          alert('保存用户失败: ' + (error.response?.data?.detail || error.message))
        } finally {
          this.savingUser = false
        }
      },
      
      async deleteUser(user) {
        if (!confirm(`确定要删除用户 ${user.username} 吗？`)) {
          return
        }
        
        try {
          await axios.delete(`/api/users/${user.id}`)
          this.fetchUsers()
        } catch (error) {
          console.error('删除用户失败', error)
          alert('删除用户失败: ' + (error.response?.data?.detail || error.message))
        }
      },
      
      async fetchPermissions() {
        this.loadingPermissions = true
        
        try {
          const response = await axios.get(`/api/settings/permissions/${this.activeRole}`)
          this.permissions = response.data.permissions
        } catch (error) {
          console.error('获取权限失败', error)
        } finally {
          this.loadingPermissions = false
        }
      },
      
      async savePermissions() {
        this.savingPermissions = true
        
        try {
          await axios.post(`/api/settings/permissions/${this.activeRole}`, {
            permissions: this.permissions
          })
          alert('权限保存成功')
        } catch (error) {
          console.error('保存权限失败', error)
          alert('保存权限失败: ' + (error.response?.data?.detail || error.message))
        } finally {
          this.savingPermissions = false
        }
      },
      
      async fetchTasks() {
        this.loadingTasks = true
        
        try {
          const response = await axios.get('/api/scheduler/tasks')
          this.tasks = response.data.tasks
        } catch (error) {
          console.error('获取任务列表失败', error)
        } finally {
          this.loadingTasks = false
        }
      },
      
      editTask(task) {
        this.editingTask = task
        this.taskForm = {
          name: task.name,
          func_path: task.func_path,
          schedule: task.schedule,
          enabled: task.enabled
        }
        this.showCreateTaskModal = true
      },
      
      closeTaskModal() {
        this.showCreateTaskModal = false
        this.editingTask = null
        this.taskForm = {
          name: '',
          func_path: '',
          schedule: '',
          enabled: true
        }
      },
      
      async saveTask() {
        this.savingTask = true
        
        try {
          if (this.editingTask) {
            // 更新任务
            await axios.put(`/api/scheduler/tasks/${this.editingTask.id}`, this.taskForm)
          } else {
            // 创建任务
            await axios.post('/api/scheduler/tasks', this.taskForm)
          }
          
          this.closeTaskModal()
          this.fetchTasks()
        } catch (error) {
          console.error('保存任务失败', error)
          alert('保存任务失败: ' + (error.response?.data?.detail || error.message))
        } finally {
          this.savingTask = false
        }
      },
      
      async deleteTask(task) {
        if (!confirm(`确定要删除任务 ${task.name} 吗？`)) {
          return
        }
        
        try {
          await axios.delete(`/api/scheduler/tasks/${task.id}`)
          this.fetchTasks()
        } catch (error) {
          console.error('删除任务失败', error)
          alert('删除任务失败: ' + (error.response?.data?.detail || error.message))
        }
      },
      
      async runTask(task) {
        try {
          await axios.post(`/api/scheduler/tasks/${task.id}/run`)
          alert(`任务 ${task.name} 已执行`)
        } catch (error) {
          console.error('执行任务失败', error)
          alert('执行任务失败: ' + (error.response?.data?.detail || error.message))
        }
      },
      
      getRoleBadgeClass(role) {
        switch (role) {
          case 'admin':
            return 'bg-danger'
          case 'manager':
            return 'bg-warning'
          case 'user':
            return 'bg-primary'
          case 'readonly':
            return 'bg-secondary'
          default:
            return 'bg-info'
        }
      },
      
      formatDate(timestamp) {
        if (!timestamp) return '-'
        
        const date = new Date(timestamp)
        return date.toLocaleString()
      }
    }
  }
  </script>
  
  <style scoped>
  .settings-container {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    padding: 2rem;
  }
  
  h1 {
    margin-bottom: 2rem;
    color: #2c3e50;
  }
  
  h2 {
    margin-bottom: 1.5rem;
    color: #2c3e50;
  }
  
  .settings-nav {
    margin-bottom: 2rem;
  }
  
  .card {
    margin-bottom: 1.5rem;
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
  </style>