<template>
  <div class="permission-management-container">
    <div class="permission-header">
      <h2>权限管理</h2>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="权限列表" name="permissions">
          <div class="table-actions">
            <el-button type="primary" @click="showAddPermissionDialog">
              添加权限
            </el-button>
            <el-input
              v-model="permissionSearch"
              placeholder="搜索权限"
              style="width: 300px"
              clearable
            ></el-input>
          </div>
          <el-table
            :data="filteredPermissions"
            border
            style="width: 100%"
            v-loading="permissionsLoading"
          >
            <el-table-column prop="id" label="ID" width="80"></el-table-column>
            <el-table-column prop="code" label="权限代码" width="180"></el-table-column>
            <el-table-column prop="name" label="权限名称" width="150"></el-table-column>
            <el-table-column prop="url" label="URL"></el-table-column>
            <el-table-column prop="description" label="描述"></el-table-column>
            <el-table-column label="操作" width="180">
              <template #default="scope">
                <template v-if="scope && scope.row">
                  <el-button
                    size="small"
                    type="primary"
                    @click="handleEditPermission(scope.row)"
                  >
                    编辑
                  </el-button>
                  <el-button
                    size="small"
                    type="danger"
                    @click="handleDeletePermission(scope.row)"
                  >
                    删除
                  </el-button>
                </template>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="角色列表" name="roles">
          <div class="table-actions">
            <el-button type="primary" @click="showAddRoleDialog">添加角色</el-button>
            <el-input
              v-model="roleSearch"
              placeholder="搜索角色"
              style="width: 300px"
              clearable
            ></el-input>
          </div>
          <el-table
            :data="filteredRoles"
            border
            style="width: 100%"
            v-loading="rolesLoading"
          >
            <el-table-column prop="id" label="ID" width="80"></el-table-column>
            <el-table-column prop="name" label="角色名称" width="150"></el-table-column>
            <el-table-column prop="description" label="描述"></el-table-column>
            <el-table-column label="权限" width="300">
              <template #default="scope">
                <template v-if="scope && scope.row && scope.row.permissions">
                  <el-tag
                    v-for="permission in scope.row.permissions"
                    :key="permission.id"
                    class="permission-tag"
                    size="small"
                  >
                    {{ permission.name }}
                  </el-tag>
                </template>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180">
              <template #default="scope">
                <template v-if="scope && scope.row">
                  <el-button
                    size="small"
                    type="primary"
                    @click="handleEditRole(scope.row)"
                  >
                    编辑
                  </el-button>
                  <el-button
                    size="small"
                    type="danger"
                    @click="handleDeleteRole(scope.row)"
                  >
                    删除
                  </el-button>
                </template>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="用户角色管理" name="userRoles">
          <div class="table-actions">
            <el-input
              v-model="userSearch"
              placeholder="搜索用户"
              style="width: 300px"
              clearable
            ></el-input>
          </div>
          <el-table
            :data="filteredUsers"
            border
            style="width: 100%"
            v-loading="usersLoading"
          >
            <el-table-column prop="id" label="ID" width="80"></el-table-column>
            <el-table-column prop="username" label="用户名" width="150"></el-table-column>
            <el-table-column prop="nickname" label="昵称" width="150"></el-table-column>
            <el-table-column prop="email" label="邮箱"></el-table-column>
            <el-table-column label="角色" width="300">
              <template #default="scope">
                <template v-if="scope && scope.row && userRolesMap[scope.row.id]">
                  <el-tag
                    v-for="role in userRolesMap[scope.row.id].roles"
                    :key="role.id"
                    class="role-tag"
                    size="small"
                  >
                    {{ role.name }}
                  </el-tag>
                </template>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180">
              <template #default="scope">
                <template v-if="scope && scope.row">
                  <el-button
                    size="small"
                    type="primary"
                    @click="handleAssignRoles(scope.row)"
                  >
                    分配角色
                  </el-button>
                </template>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 添加/编辑权限对话框 -->
    <el-dialog
      v-model="permissionDialogVisible"
      :title="isEditMode ? '编辑权限' : '添加权限'"
      width="500px"
    >
      <el-form
        :model="permissionForm"
        label-width="120px"
        :rules="permissionRules"
        ref="permissionFormRef"
      >
        <el-form-item label="权限代码" prop="code">
          <el-input v-model="permissionForm.code" placeholder="例如: user:create"></el-input>
        </el-form-item>
        <el-form-item label="权限名称" prop="name">
          <el-input v-model="permissionForm.name" placeholder="例如: 创建用户"></el-input>
        </el-form-item>
        <el-form-item label="URL" prop="url">
          <el-input v-model="permissionForm.url" placeholder="例如: /api/users"></el-input>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="permissionForm.description"
            type="textarea"
            placeholder="权限描述"
          ></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="permissionDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitPermission">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 添加/编辑角色对话框 -->
    <el-dialog
      v-model="roleDialogVisible"
      :title="isEditMode ? '编辑角色' : '添加角色'"
      width="500px"
    >
      <el-form
        :model="roleForm"
        label-width="120px"
        :rules="roleRules"
        ref="roleFormRef"
      >
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="roleForm.name" placeholder="例如: admin"></el-input>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="roleForm.description"
            type="textarea"
            placeholder="角色描述"
          ></el-input>
        </el-form-item>
        <el-form-item label="权限" prop="permission_ids">
          <el-select
            v-model="roleForm.permission_ids"
            multiple
            placeholder="请选择权限"
            style="width: 100%"
          >
            <el-option
              v-for="item in permissions"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            >
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="roleDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitRole">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 分配角色对话框 -->
    <el-dialog
      v-model="assignRoleDialogVisible"
      title="分配角色"
      width="500px"
    >
      <div v-if="currentUser">
        <p>为用户 <strong>{{ currentUser.username }}</strong> 分配角色：</p>
        <el-form>
          <el-form-item>
            <el-select
              v-model="selectedRoleIds"
              multiple
              placeholder="请选择角色"
              style="width: 100%"
            >
              <el-option
                v-for="item in roles"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              >
              </el-option>
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="assignRoleDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitAssignRole">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getPermissionsApi,
  createPermissionApi,
  updatePermissionApi,
  deletePermissionApi,
  getRolesApi,
  createRoleApi,
  updateRoleApi,
  deleteRoleApi,
  getUsersApi,
  getUserRolesApi,
  assignUserRolesApi
} from '@/api/auth'

// 选项卡相关
const activeTab = ref('permissions')

// 权限管理相关
const permissions = ref([])
const permissionsLoading = ref(false)
const permissionSearch = ref('')
const permissionDialogVisible = ref(false)
const isEditMode = ref(false)
const permissionForm = reactive({
  id: null,
  code: '',
  name: '',
  url: '',
  description: ''
})
const permissionFormRef = ref(null)
const permissionRules = {
  code: [{ required: true, message: '请输入权限代码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入权限名称', trigger: 'blur' }]
}

// 角色管理相关
const roles = ref([])
const rolesLoading = ref(false)
const roleSearch = ref('')
const roleDialogVisible = ref(false)
const roleForm = reactive({
  id: null,
  name: '',
  description: '',
  permission_ids: []
})
const roleFormRef = ref(null)
const roleRules = {
  name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }]
}

// 用户角色管理相关
const users = ref([])
const usersLoading = ref(false)
const userSearch = ref('')
const userRolesMap = ref({})
const assignRoleDialogVisible = ref(false)
const currentUser = ref(null)
const selectedRoleIds = ref([])

// 计算属性：根据搜索过滤权限列表
const filteredPermissions = computed(() => {
  if (!permissionSearch.value) return permissions.value
  
  const search = permissionSearch.value.toLowerCase()
  return permissions.value.filter(permission => 
    permission.code.toLowerCase().includes(search) ||
    permission.name.toLowerCase().includes(search) ||
    (permission.description && permission.description.toLowerCase().includes(search))
  )
})

// 计算属性：根据搜索过滤角色列表
const filteredRoles = computed(() => {
  if (!roleSearch.value) return roles.value
  
  const search = roleSearch.value.toLowerCase()
  return roles.value.filter(role => 
    role.name.toLowerCase().includes(search) ||
    (role.description && role.description.toLowerCase().includes(search))
  )
})

// 计算属性：根据搜索过滤用户列表
const filteredUsers = computed(() => {
  if (!userSearch.value) return users.value
  
  const search = userSearch.value.toLowerCase()
  return users.value.filter(user => 
    user.username.toLowerCase().includes(search) ||
    (user.nickname && user.nickname.toLowerCase().includes(search)) ||
    (user.email && user.email.toLowerCase().includes(search))
  )
})

// 生命周期钩子
onMounted(async () => {
  await loadPermissions()
  await loadRoles()
  await loadUsers()
})

// 加载权限列表
async function loadPermissions() {
  permissionsLoading.value = true
  try {
    const response = await getPermissionsApi()
    permissions.value = response
  } catch (error) {
    ElMessage.error('加载权限列表失败')
    console.error(error)
  } finally {
    permissionsLoading.value = false
  }
}

// 加载角色列表
async function loadRoles() {
  rolesLoading.value = true
  try {
    const response = await getRolesApi()
    roles.value = response
  } catch (error) {
    ElMessage.error('加载角色列表失败')
    console.error(error)
  } finally {
    rolesLoading.value = false
  }
}

// 加载用户列表及其角色
async function loadUsers() {
  usersLoading.value = true
  try {
    const response = await getUsersApi()
    users.value = response
    
    // 先清空现有的角色映射
    userRolesMap.value = {}
    
    // 单独处理角色获取错误，不影响整体用户列表加载
    if (users.value && users.value.length > 0) {
      ElMessage.info('正在加载用户角色信息...')
      let successCount = 0
      
      for (const user of users.value) {
        try {
          const userRoles = await getUserRolesApi(user.id)
          if (userRoles) {
            userRolesMap.value[user.id] = userRoles
            successCount++
          }
        } catch (error) {
          console.error(`获取用户 ${user.id} 的角色失败:`, error)
          // 创建一个空的角色列表，防止界面报错
          userRolesMap.value[user.id] = { roles: [] }
        }
      }
      
      if (successCount === 0 && users.value.length > 0) {
        ElMessage.warning('无法获取用户角色信息，请检查后端API或网络连接')
      } else if (successCount < users.value.length) {
        ElMessage.warning(`部分用户(${users.value.length - successCount}/${users.value.length})的角色信息加载失败`)
      }
    }
  } catch (error) {
    ElMessage.error('加载用户列表失败')
    console.error(error)
  } finally {
    usersLoading.value = false
  }
}

// 显示添加权限对话框
function showAddPermissionDialog() {
  isEditMode.value = false
  resetPermissionForm()
  permissionDialogVisible.value = true
}

// 处理编辑权限
function handleEditPermission(permission) {
  isEditMode.value = true
  resetPermissionForm()
  
  // 填充表单
  permissionForm.id = permission.id
  permissionForm.code = permission.code
  permissionForm.name = permission.name
  permissionForm.url = permission.url || ''
  permissionForm.description = permission.description || ''
  
  permissionDialogVisible.value = true
}

// 处理删除权限
function handleDeletePermission(permission) {
  ElMessageBox.confirm(
    `确定要删除权限 "${permission.name}" 吗？`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deletePermissionApi(permission.id)
      ElMessage.success('删除权限成功')
      await loadPermissions()
      await loadRoles()  // 重新加载角色，因为角色中的权限可能已更新
    } catch (error) {
      ElMessage.error('删除权限失败')
      console.error(error)
    }
  }).catch(() => {
    // 用户取消删除，不做任何操作
  })
}

// 提交权限表单
async function submitPermission() {
  if (!permissionFormRef.value) return
  
  await permissionFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    try {
      if (isEditMode.value) {
        await updatePermissionApi(permissionForm.id, {
          code: permissionForm.code,
          name: permissionForm.name,
          url: permissionForm.url,
          description: permissionForm.description
        })
        ElMessage.success('更新权限成功')
      } else {
        await createPermissionApi({
          code: permissionForm.code,
          name: permissionForm.name,
          url: permissionForm.url,
          description: permissionForm.description
        })
        ElMessage.success('添加权限成功')
      }
      
      permissionDialogVisible.value = false
      await loadPermissions()
    } catch (error) {
      ElMessage.error(isEditMode.value ? '更新权限失败' : '添加权限失败')
      console.error(error)
    }
  })
}

// 重置权限表单
function resetPermissionForm() {
  permissionForm.id = null
  permissionForm.code = ''
  permissionForm.name = ''
  permissionForm.url = ''
  permissionForm.description = ''
  if (permissionFormRef.value) {
    permissionFormRef.value.resetFields()
  }
}

// 显示添加角色对话框
function showAddRoleDialog() {
  isEditMode.value = false
  resetRoleForm()
  roleDialogVisible.value = true
}

// 处理编辑角色
function handleEditRole(role) {
  isEditMode.value = true
  resetRoleForm()
  
  // 填充表单
  roleForm.id = role.id
  roleForm.name = role.name
  roleForm.description = role.description || ''
  roleForm.permission_ids = role.permissions.map(p => p.id)
  
  roleDialogVisible.value = true
}

// 处理删除角色
function handleDeleteRole(role) {
  ElMessageBox.confirm(
    `确定要删除角色 "${role.name}" 吗？`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteRoleApi(role.id)
      ElMessage.success('删除角色成功')
      await loadRoles()
      await loadUsers()  // 重新加载用户，因为用户的角色可能已更新
    } catch (error) {
      ElMessage.error('删除角色失败')
      console.error(error)
    }
  }).catch(() => {
    // 用户取消删除，不做任何操作
  })
}

// 提交角色表单
async function submitRole() {
  if (!roleFormRef.value) return
  
  await roleFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    try {
      if (isEditMode.value) {
        await updateRoleApi(roleForm.id, {
          name: roleForm.name,
          description: roleForm.description,
          permission_ids: roleForm.permission_ids
        })
        ElMessage.success('更新角色成功')
      } else {
        await createRoleApi({
          name: roleForm.name,
          description: roleForm.description,
          permission_ids: roleForm.permission_ids
        })
        ElMessage.success('添加角色成功')
      }
      
      roleDialogVisible.value = false
      await loadRoles()
    } catch (error) {
      ElMessage.error(isEditMode.value ? '更新角色失败' : '添加角色失败')
      console.error(error)
    }
  })
}

// 重置角色表单
function resetRoleForm() {
  roleForm.id = null
  roleForm.name = ''
  roleForm.description = ''
  roleForm.permission_ids = []
  if (roleFormRef.value) {
    roleFormRef.value.resetFields()
  }
}

// 处理分配角色
function handleAssignRoles(user) {
  currentUser.value = user
  
  // 从用户角色映射中获取角色，如果不存在则使用空数组
  const userRoles = userRolesMap.value[user.id]
  selectedRoleIds.value = userRoles?.roles?.map(r => r.id) || []
  
  // 提示用户当前状态
  if (!userRoles || !userRoles.roles || userRoles.roles.length === 0) {
    ElMessage.info('未获取到该用户的角色信息，将为其分配新角色')
  }
  
  assignRoleDialogVisible.value = true
}

// 提交分配角色
async function submitAssignRole() {
  if (!currentUser.value) return
  
  try {
    ElMessage.info('正在为用户分配角色...')
    
    await assignUserRolesApi({
      user_id: currentUser.value.id,
      role_ids: selectedRoleIds.value
    })
    
    ElMessage.success('分配角色成功')
    assignRoleDialogVisible.value = false
    
    // 更新本地角色信息
    userRolesMap.value[currentUser.value.id] = {
      ...currentUser.value,
      roles: roles.value.filter(role => selectedRoleIds.value.includes(role.id))
    }
  } catch (error) {
    ElMessage.error('分配角色失败: ' + (error.message || '未知错误'))
    console.error('分配角色失败:', error)
  }
}
</script>

<style scoped>
.permission-management-container {
  padding: 20px;
  width: 100%;
}

.permission-header {
  margin-bottom: 20px;
}

.table-actions {
  margin-bottom: 15px;
  display: flex;
  justify-content: space-between;
}

.permission-tag,
.role-tag {
  margin-right: 5px;
  margin-bottom: 5px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style> 