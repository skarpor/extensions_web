<template>
  <div class="permission-group-management">
    <div class="page-header">
      <h2>权限管理</h2>
      <p class="page-description">管理系统权限分组和权限配置</p>
    </div>

    <el-tabs v-model="activeTab" class="permission-tabs">
      <!-- 权限分组管理 -->
      <el-tab-pane label="权限分组" name="groups">
        <div class="tab-content">
          <div class="toolbar">
            <el-button type="primary" @click="showAddGroupDialog">
              <el-icon><Plus /></el-icon>
              添加分组
            </el-button>
            <el-input
              v-model="groupSearch"
              placeholder="搜索权限分组"
              style="width: 300px"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>

          <div class="permission-groups-grid">
            <div
              v-for="group in filteredGroups"
              :key="group.id"
              class="permission-group-card"
            >
              <div class="group-header">
                <div class="group-info">
                  <el-icon class="group-icon" :size="24">
                    <component :is="group.icon || 'Grid'" />
                  </el-icon>
                  <div>
                    <h3>{{ group.name }}</h3>
                    <p class="group-description">{{ group.description }}</p>
                  </div>
                </div>
                <div class="group-actions">
                  <el-button size="small" @click="handleEditGroup(group)">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-button size="small" type="danger" @click="handleDeleteGroup(group)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
              
              <div class="permissions-list">
                <div class="permissions-header">
                  <span>权限列表 ({{ group.permissions?.length || 0 }})</span>
                  <el-button size="small" text @click="showAddPermissionDialog(group)">
                    <el-icon><Plus /></el-icon>
                    添加权限
                  </el-button>
                </div>
                <div class="permissions-grid">
                  <div
                    v-for="permission in group.permissions"
                    :key="permission.id"
                    class="permission-item"
                  >
                    <div class="permission-info">
                      <span class="permission-code">{{ permission.code }}</span>
                      <span class="permission-name">{{ permission.name }}</span>
                    </div>
                    <div class="permission-actions">
                      <el-button size="small" text @click="handleEditPermission(permission)">
                        <el-icon><Edit /></el-icon>
                      </el-button>
                      <el-button size="small" text type="danger" @click="handleDeletePermission(permission)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 角色管理 -->
      <el-tab-pane label="角色管理" name="roles">
        <div class="tab-content">
          <div class="toolbar">
            <el-button type="primary" @click="showAddRoleDialog">
              <el-icon><Plus /></el-icon>
              添加角色
            </el-button>
            <el-input
              v-model="roleSearch"
              placeholder="搜索角色"
              style="width: 300px"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>

          <div class="roles-grid">
            <div
              v-for="role in filteredRoles"
              :key="role.id"
              class="role-card"
            >
              <div class="role-header">
                <div class="role-info">
                  <el-icon class="role-icon" :size="24">
                    <UserFilled />
                  </el-icon>
                  <div>
                    <h3>{{ role.name }}</h3>
                    <p class="role-description">{{ role.description }}</p>
                  </div>
                </div>
                <div class="role-actions">
                  <el-button size="small" @click="handleEditRole(role)">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-button size="small" type="danger" @click="handleDeleteRole(role)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
              
              <div class="role-permissions">
                <div class="permissions-header">
                  <span>权限配置 ({{ role.permissions?.length || 0 }})</span>
                  <el-button size="small" text @click="handleConfigRolePermissions(role)">
                    <el-icon><Setting /></el-icon>
                    配置权限
                  </el-button>
                </div>
                <div class="permissions-tags">
                  <el-tag
                    v-for="permission in role.permissions?.slice(0, 5)"
                    :key="permission.id"
                    size="small"
                    class="permission-tag"
                  >
                    {{ permission.name }}
                  </el-tag>
                  <el-tag v-if="role.permissions?.length > 5" size="small" type="info">
                    +{{ role.permissions.length - 5 }} 更多
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 用户角色分配 -->
      <el-tab-pane label="用户角色" name="users">
        <div class="tab-content">
          <div class="toolbar">
            <el-input
              v-model="userSearch"
              placeholder="搜索用户"
              style="width: 300px"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>

          <el-table :data="filteredUsers" border v-loading="usersLoading">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="username" label="用户名" width="150" />
            <el-table-column prop="nickname" label="昵称" width="150" />
            <el-table-column prop="email" label="邮箱" />
            <el-table-column label="角色" width="300">
              <template #default="{ row }">
                <div class="user-roles">
                  <el-tag
                    v-for="role in getUserRoles(row.id)"
                    :key="role.id"
                    size="small"
                    class="role-tag"
                  >
                    {{ role.name }}
                  </el-tag>
                  <el-tag v-if="!getUserRoles(row.id)?.length" type="info" size="small">
                    未分配角色
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button size="small" @click="handleAssignRoles(row)">
                  分配角色
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 权限分组对话框 -->
    <el-dialog
      v-model="groupDialogVisible"
      :title="isEditMode ? '编辑权限分组' : '添加权限分组'"
      width="500px"
    >
      <el-form
        :model="groupForm"
        label-width="120px"
        :rules="groupRules"
        ref="groupFormRef"
      >
        <el-form-item label="分组代码" prop="code">
          <el-input v-model="groupForm.code" placeholder="例如: user_management" />
        </el-form-item>
        <el-form-item label="分组名称" prop="name">
          <el-input v-model="groupForm.name" placeholder="例如: 用户管理" />
        </el-form-item>
        <el-form-item label="图标" prop="icon">
          <el-select v-model="groupForm.icon" placeholder="选择图标">
            <el-option label="用户" value="User" />
            <el-option label="设置" value="Setting" />
            <el-option label="文件夹" value="Folder" />
            <el-option label="网格" value="Grid" />
            <el-option label="消息" value="Message" />
            <el-option label="聊天" value="ChatDotRound" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="groupForm.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="groupForm.description"
            type="textarea"
            placeholder="分组描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="groupDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitGroup">确定</el-button>
      </template>
    </el-dialog>

    <!-- 权限对话框 -->
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
          <el-input v-model="permissionForm.code" placeholder="例如: user:create" />
        </el-form-item>
        <el-form-item label="权限名称" prop="name">
          <el-input v-model="permissionForm.name" placeholder="例如: 创建用户" />
        </el-form-item>
        <el-form-item label="所属分组" prop="group_id">
          <el-select v-model="permissionForm.group_id" placeholder="选择分组">
            <el-option
              v-for="group in permissionGroups"
              :key="group.id"
              :label="group.name"
              :value="group.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="URL" prop="url">
          <el-input v-model="permissionForm.url" placeholder="例如: /api/users" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="permissionForm.description"
            type="textarea"
            placeholder="权限描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="permissionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPermission">确定</el-button>
      </template>
    </el-dialog>

    <!-- 角色对话框 -->
    <el-dialog
      v-model="roleDialogVisible"
      :title="isEditMode ? '编辑角色' : '添加角色'"
      width="800px"
    >
      <el-form
        :model="roleForm"
        label-width="120px"
        :rules="roleRules"
        ref="roleFormRef"
      >
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="roleForm.name" placeholder="例如: 管理员" />
        </el-form-item>
        <el-form-item label="角色描述" prop="description">
          <el-input
            v-model="roleForm.description"
            type="textarea"
            placeholder="角色描述"
          />
        </el-form-item>
        <el-form-item label="权限配置" prop="permission_ids">
          <div class="role-permissions-config">
            <div
              v-for="group in permissionGroups"
              :key="group.id"
              class="permission-group-section"
            >
              <div class="group-header-config">
                <el-checkbox
                  :model-value="isGroupAllSelected(group)"
                  :indeterminate="isGroupIndeterminate(group)"
                  @change="handleGroupSelectAll(group, $event)"
                >
                  <el-icon class="group-icon-small">
                    <component :is="group.icon || 'Grid'" />
                  </el-icon>
                  {{ group.name }}
                </el-checkbox>
              </div>
              <div class="permissions-checkboxes">
                <el-checkbox
                  v-for="permission in group.permissions"
                  :key="permission.id"
                  :model-value="roleForm.permission_ids.includes(permission.id)"
                  @change="handlePermissionChange(permission.id, $event)"
                  class="permission-checkbox"
                >
                  <span class="permission-label">
                    <span class="permission-code-small">{{ permission.code }}</span>
                    <span class="permission-name-small">{{ permission.name }}</span>
                  </span>
                </el-checkbox>
              </div>
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRole">确定</el-button>
      </template>
    </el-dialog>

    <!-- 用户角色分配对话框 -->
    <el-dialog
      v-model="assignRoleDialogVisible"
      title="分配用户角色"
      width="500px"
    >
      <div v-if="currentUser" class="user-info">
        <h4>用户信息</h4>
        <p><strong>用户名:</strong> {{ currentUser.username }}</p>
        <p><strong>昵称:</strong> {{ currentUser.nickname }}</p>
        <p><strong>邮箱:</strong> {{ currentUser.email }}</p>
      </div>

      <el-form label-width="120px">
        <el-form-item label="选择角色">
          <el-checkbox-group v-model="selectedRoleIds">
            <div class="roles-selection">
              <el-checkbox
                v-for="role in roles"
                :key="role.id"
                :value="role.id"
                class="role-checkbox"
              >
                <div class="role-info-small">
                  <span class="role-name">{{ role.name }}</span>
                  <span class="role-desc">{{ role.description }}</span>
                </div>
              </el-checkbox>
            </div>
          </el-checkbox-group>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="assignRoleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAssignRoles">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, Edit, Delete, Setting, UserFilled, User, Folder, Grid, Message, ChatDotRound
} from '@element-plus/icons-vue'
import {
  getPermissionGroupsApi,
  createPermissionGroupApi,
  updatePermissionGroupApi,
  deletePermissionGroupApi,
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
const activeTab = ref('groups')

// 权限分组相关
const permissionGroups = ref([])
const groupsLoading = ref(false)
const groupSearch = ref('')
const groupDialogVisible = ref(false)
const isEditMode = ref(false)
const groupFormRef = ref()

const groupForm = reactive({
  id: null,
  code: '',
  name: '',
  description: '',
  sort_order: 0,
  icon: ''
})

const groupRules = {
  code: [
    { required: true, message: '请输入分组代码', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入分组名称', trigger: 'blur' }
  ]
}

// 权限相关
const permissionDialogVisible = ref(false)
const permissionFormRef = ref()
const currentGroup = ref(null)

const permissionForm = reactive({
  id: null,
  code: '',
  name: '',
  url: '',
  description: '',
  group_id: null
})

const permissionRules = {
  code: [
    { required: true, message: '请输入权限代码', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入权限名称', trigger: 'blur' }
  ],
  group_id: [
    { required: true, message: '请选择所属分组', trigger: 'change' }
  ]
}

// 角色相关
const roles = ref([])
const rolesLoading = ref(false)
const roleSearch = ref('')
const roleDialogVisible = ref(false)
const roleFormRef = ref()

const roleForm = reactive({
  id: null,
  name: '',
  description: '',
  permission_ids: []
})

const roleRules = {
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' }
  ]
}

// 用户相关
const users = ref([])
const usersLoading = ref(false)
const userSearch = ref('')
const userRolesMap = ref({})
const assignRoleDialogVisible = ref(false)
const currentUser = ref(null)
const selectedRoleIds = ref([])

// 计算属性
const filteredGroups = computed(() => {
  if (!groupSearch.value) return permissionGroups.value
  return permissionGroups.value.filter(group =>
    group.name.includes(groupSearch.value) ||
    group.code.includes(groupSearch.value) ||
    group.description?.includes(groupSearch.value)
  )
})

const filteredRoles = computed(() => {
  if (!roleSearch.value) return roles.value
  return roles.value.filter(role =>
    role.name.includes(roleSearch.value) ||
    role.description?.includes(roleSearch.value)
  )
})

const filteredUsers = computed(() => {
  if (!userSearch.value) return users.value
  return users.value.filter(user =>
    user.username.includes(userSearch.value) ||
    user.nickname?.includes(userSearch.value) ||
    user.email?.includes(userSearch.value)
  )
})

// 方法
const loadPermissionGroups = async () => {
  groupsLoading.value = true
  try {
    const response = await getPermissionGroupsApi()
    permissionGroups.value = response
  } catch (error) {
    ElMessage.error('加载权限分组失败')
    console.error(error)
  } finally {
    groupsLoading.value = false
  }
}

const loadRoles = async () => {
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

const loadUsers = async () => {
  usersLoading.value = true
  try {
    const response = await getUsersApi()
    users.value = response

    // 加载每个用户的角色
    userRolesMap.value = {}
    for (const user of response) {
      try {
        const userRoles = await getUserRolesApi(user.id)
        userRolesMap.value[user.id] = userRoles
      } catch (error) {
        console.error(`加载用户 ${user.id} 角色失败:`, error)
        userRolesMap.value[user.id] = { roles: [] }
      }
    }
  } catch (error) {
    ElMessage.error('加载用户列表失败')
    console.error(error)
  } finally {
    usersLoading.value = false
  }
}

const getUserRoles = (userId) => {
  return userRolesMap.value[userId]?.roles || []
}

// 权限分组操作
const showAddGroupDialog = () => {
  isEditMode.value = false
  resetGroupForm()
  groupDialogVisible.value = true
}

const handleEditGroup = (group) => {
  isEditMode.value = true
  resetGroupForm()

  groupForm.id = group.id
  groupForm.code = group.code
  groupForm.name = group.name
  groupForm.description = group.description || ''
  groupForm.sort_order = group.sort_order || 0
  groupForm.icon = group.icon || ''

  groupDialogVisible.value = true
}

const handleDeleteGroup = async (group) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除权限分组 "${group.name}" 吗？这将同时删除该分组下的所有权限。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deletePermissionGroupApi(group.id)
    ElMessage.success('删除权限分组成功')
    await loadPermissionGroups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除权限分组失败')
      console.error(error)
    }
  }
}

const resetGroupForm = () => {
  groupForm.id = null
  groupForm.code = ''
  groupForm.name = ''
  groupForm.description = ''
  groupForm.sort_order = 0
  groupForm.icon = ''
  if (groupFormRef.value) {
    groupFormRef.value.resetFields()
  }
}

const submitGroup = async () => {
  if (!groupFormRef.value) return

  await groupFormRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      if (isEditMode.value) {
        await updatePermissionGroupApi(groupForm.id, {
          code: groupForm.code,
          name: groupForm.name,
          description: groupForm.description,
          sort_order: groupForm.sort_order,
          icon: groupForm.icon
        })
        ElMessage.success('更新权限分组成功')
      } else {
        await createPermissionGroupApi({
          code: groupForm.code,
          name: groupForm.name,
          description: groupForm.description,
          sort_order: groupForm.sort_order,
          icon: groupForm.icon
        })
        ElMessage.success('添加权限分组成功')
      }

      groupDialogVisible.value = false
      await loadPermissionGroups()
    } catch (error) {
      ElMessage.error(isEditMode.value ? '更新权限分组失败' : '添加权限分组失败')
      console.error(error)
    }
  })
}

// 权限操作
const showAddPermissionDialog = (group) => {
  isEditMode.value = false
  currentGroup.value = group
  resetPermissionForm()
  permissionForm.group_id = group.id
  permissionDialogVisible.value = true
}

const handleEditPermission = (permission) => {
  isEditMode.value = true
  resetPermissionForm()

  permissionForm.id = permission.id
  permissionForm.code = permission.code
  permissionForm.name = permission.name
  permissionForm.url = permission.url || ''
  permissionForm.description = permission.description || ''
  permissionForm.group_id = permission.group_id

  permissionDialogVisible.value = true
}

const handleDeletePermission = async (permission) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除权限 "${permission.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deletePermissionApi(permission.id)
    ElMessage.success('删除权限成功')
    await loadPermissionGroups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除权限失败')
      console.error(error)
    }
  }
}

const resetPermissionForm = () => {
  permissionForm.id = null
  permissionForm.code = ''
  permissionForm.name = ''
  permissionForm.url = ''
  permissionForm.description = ''
  permissionForm.group_id = null
  if (permissionFormRef.value) {
    permissionFormRef.value.resetFields()
  }
}

const submitPermission = async () => {
  if (!permissionFormRef.value) return

  await permissionFormRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      if (isEditMode.value) {
        await updatePermissionApi(permissionForm.id, {
          code: permissionForm.code,
          name: permissionForm.name,
          url: permissionForm.url,
          description: permissionForm.description,
          group_id: permissionForm.group_id
        })
        ElMessage.success('更新权限成功')
      } else {
        await createPermissionApi({
          code: permissionForm.code,
          name: permissionForm.name,
          url: permissionForm.url,
          description: permissionForm.description,
          group_id: permissionForm.group_id
        })
        ElMessage.success('添加权限成功')
      }

      permissionDialogVisible.value = false
      await loadPermissionGroups()
    } catch (error) {
      ElMessage.error(isEditMode.value ? '更新权限失败' : '添加权限失败')
      console.error(error)
    }
  })
}

// 角色操作
const showAddRoleDialog = () => {
  isEditMode.value = false
  resetRoleForm()
  roleDialogVisible.value = true
}

const handleEditRole = (role) => {
  isEditMode.value = true
  resetRoleForm()

  roleForm.id = role.id
  roleForm.name = role.name
  roleForm.description = role.description || ''
  roleForm.permission_ids = role.permissions?.map(p => p.id) || []

  roleDialogVisible.value = true
}

const handleDeleteRole = async (role) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除角色 "${role.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteRoleApi(role.id)
    ElMessage.success('删除角色成功')
    await loadRoles()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除角色失败')
      console.error(error)
    }
  }
}

const handleConfigRolePermissions = (role) => {
  handleEditRole(role)
}

const resetRoleForm = () => {
  roleForm.id = null
  roleForm.name = ''
  roleForm.description = ''
  roleForm.permission_ids = []
  if (roleFormRef.value) {
    roleFormRef.value.resetFields()
  }
}

const submitRole = async () => {
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

// 权限选择相关方法
const isGroupAllSelected = (group) => {
  if (!group.permissions || group.permissions.length === 0) return false
  return group.permissions.every(p => roleForm.permission_ids.includes(p.id))
}

const isGroupIndeterminate = (group) => {
  if (!group.permissions || group.permissions.length === 0) return false
  const selectedCount = group.permissions.filter(p => roleForm.permission_ids.includes(p.id)).length
  return selectedCount > 0 && selectedCount < group.permissions.length
}

const handleGroupSelectAll = (group, checked) => {
  if (checked) {
    // 添加该分组下的所有权限
    group.permissions.forEach(permission => {
      if (!roleForm.permission_ids.includes(permission.id)) {
        roleForm.permission_ids.push(permission.id)
      }
    })
  } else {
    // 移除该分组下的所有权限
    group.permissions.forEach(permission => {
      const index = roleForm.permission_ids.indexOf(permission.id)
      if (index > -1) {
        roleForm.permission_ids.splice(index, 1)
      }
    })
  }
}

const handlePermissionChange = (permissionId, checked) => {
  if (checked) {
    if (!roleForm.permission_ids.includes(permissionId)) {
      roleForm.permission_ids.push(permissionId)
    }
  } else {
    const index = roleForm.permission_ids.indexOf(permissionId)
    if (index > -1) {
      roleForm.permission_ids.splice(index, 1)
    }
  }
}

// 用户角色分配
const handleAssignRoles = (user) => {
  currentUser.value = user
  const userRoles = userRolesMap.value[user.id]
  selectedRoleIds.value = userRoles?.roles?.map(r => r.id) || []
  assignRoleDialogVisible.value = true
}

const submitAssignRoles = async () => {
  try {
    await assignUserRolesApi({
      user_id: currentUser.value.id,
      role_ids: selectedRoleIds.value
    })
    ElMessage.success('分配角色成功')
    assignRoleDialogVisible.value = false
    await loadUsers()
  } catch (error) {
    ElMessage.error('分配角色失败')
    console.error(error)
  }
}

// 初始化
onMounted(() => {
  loadPermissionGroups()
  loadRoles()
  loadUsers()
})
</script>

<style scoped>
.permission-group-management {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
  width: 100%;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.page-description {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.permission-tabs {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.tab-content {
  padding: 20px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

/* 权限分组网格 */
.permission-groups-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.permission-group-card {
  background: white;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  overflow: hidden;
  transition: all 0.3s ease;
}

.permission-group-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f0f2f5;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.group-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.group-icon {
  color: white;
}

.group-info h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
}

.group-description {
  margin: 0;
  font-size: 12px;
  opacity: 0.9;
}

.group-actions {
  display: flex;
  gap: 8px;
}

.group-actions .el-button {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
}

.group-actions .el-button:hover {
  background: rgba(255, 255, 255, 0.3);
}

.permissions-list {
  padding: 16px;
}

.permissions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #606266;
}

.permissions-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.permission-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
  transition: all 0.2s ease;
}

.permission-item:hover {
  background: #e3f2fd;
  border-color: #2196f3;
}

.permission-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.permission-code {
  font-size: 12px;
  color: #2196f3;
  font-family: 'Monaco', 'Menlo', monospace;
  font-weight: 600;
}

.permission-name {
  font-size: 13px;
  color: #606266;
}

.permission-actions {
  display: flex;
  gap: 4px;
}

/* 角色网格 */
.roles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.role-card {
  background: white;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  overflow: hidden;
  transition: all 0.3s ease;
}

.role-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.role-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f0f2f5;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.role-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.role-icon {
  color: white;
}

.role-info h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
}

.role-description {
  margin: 0;
  font-size: 12px;
  opacity: 0.9;
}

.role-actions {
  display: flex;
  gap: 8px;
}

.role-actions .el-button {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
}

.role-actions .el-button:hover {
  background: rgba(255, 255, 255, 0.3);
}

.role-permissions {
  padding: 16px;;
}

.permissions-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.permission-tag {
  font-size: 12px;
}

/* 用户角色 */
.user-roles {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.role-tag {
  font-size: 12px;
}

/* 角色权限配置 */
.role-permissions-config {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 16px;
  width: 100%;
}

.permission-group-section {
  margin-bottom: 20px;
}

.permission-group-section:last-child {
  margin-bottom: 0;
}

.group-header-config {
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f2f5;
}

.group-header-config .el-checkbox {
  font-weight: 600;
  color: #303133;
}

.group-icon-small {
  margin-right: 6px;
  color: #409eff;
}

.permissions-checkboxes {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 8px;
  margin-left: 24px;
}

.permission-checkbox {
  margin: 0;
}

.permission-label {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.permission-code-small {
  font-size: 11px;
  color: #2196f3;
  font-family: 'Monaco', 'Menlo', monospace;
  font-weight: 600;
}

.permission-name-small {
  font-size: 12px;
  color: #606266;
}

/* 用户角色分配 */
.user-info {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.user-info h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.user-info p {
  margin: 4px 0;
  font-size: 14px;
  color: #606266;
}

.roles-selection {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.role-checkbox {
  margin: 0;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.role-checkbox:hover {
  background: #f8f9fa;
  border-color: #409eff;
}

.role-info-small {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.role-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.role-desc {
  font-size: 12px;
  color: #909399;
}

/* 响应式 */
@media (max-width: 768px) {
  .permission-groups-grid,
  .roles-grid {
    grid-template-columns: 1fr;
  }

  .toolbar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .permissions-checkboxes {
    grid-template-columns: 1fr;
  }
}
</style>
