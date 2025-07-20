<template>
  <div class="system-settings">
    <div class="page-header">
      <h2>系统设置</h2>
      <p class="page-description">管理系统配置参数和运行环境</p>
    </div>

    <!-- 系统状态卡片 -->
    <el-card class="status-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon class="header-icon">
            <Monitor />
          </el-icon>
          <span>系统状态</span>
        </div>
      </template>

      <div class="status-grid">
        <div class="status-item">
          <div class="status-label">系统状态</div>
          <div class="status-value">
            <el-tag :type="expiryInfo.expired ? 'danger' : 'success'" size="large">
              {{ expiryInfo.expired ? '已过期' : '正常运行' }}
            </el-tag>
          </div>
        </div>

        <div class="status-item" v-if="!expiryInfo.expired">
          <div class="status-label">剩余天数</div>
          <div class="status-value">
            <span class="days-left">{{ expiryInfo.days_left }}</span> 天
          </div>
        </div>

        <div class="status-item" v-if="configStatus.initialized_at">
          <div class="status-label">初始化时间</div>
          <div class="status-value">
            {{ formatDate(configStatus.initialized_at) }}
          </div>
        </div>

        <div class="status-item" v-if="configStatus.updated_at">
          <div class="status-label">最后更新</div>
          <div class="status-value">
            {{ formatDate(configStatus.updated_at) }}
          </div>
        </div>
      </div>
    </el-card>

    <!-- 设置表单 -->
    <el-card class="settings-card" shadow="hover" v-loading="loading">
      <template #header>
        <div class="card-header">
          <el-icon class="header-icon">
            <Setting />
          </el-icon>
          <span>配置参数</span>
          <div class="header-actions">
            <el-button type="primary" @click="saveSettings" :loading="saving">
              <el-icon>
                <Check />
              </el-icon>
              保存设置
            </el-button>
            <el-button @click="resetSettings">
              <el-icon>
                <RefreshLeft />
              </el-icon>
              重置
            </el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab" class="settings-tabs">
        <!-- 基础配置 -->
        <el-tab-pane label="基础配置" name="basic">
          <div class="settings-section">
            <h3>应用配置</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="应用名称">
                  <el-input v-model="settings.APP_NAME" placeholder="请输入应用名称" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="调试模式">
                  <el-switch v-model="settings.DEBUG" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="项目名称">
                  <el-input v-model="settings.PROJECT_NAME" placeholder="项目名称" readonly />
                  <div class="form-tip">系统内部使用的项目名称，只读</div>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="系统版本">
                  <el-input v-model="settings.VERSION" placeholder="系统版本" readonly />
                  <div class="form-tip">当前系统版本号，只读</div>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="监听地址">
                  <el-input v-model="settings.HOST" placeholder="0.0.0.0" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="监听端口">
                  <el-input-number v-model="settings.PORT" :min="1" :max="65535" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <div class="settings-section">
            <h3>模块配置</h3>
            <el-row :gutter="20">
              <el-col :span="6">
                <el-form-item label="文件模块">
                  <el-switch v-model="settings.FILE_ENABLE" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="聊天">
                  <el-switch v-model="settings.CHAT_ENABLE" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="二维码文件传输">
                  <el-switch v-model="settings.QR_ENABLE" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="定时任务模块">
                  <el-switch v-model="settings.SCHEDULER_ENABLE" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="日志模块">
                  <el-switch v-model="settings.LOG_ENABLE" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="数据库模块">
                  <el-switch v-model="settings.DATABASE_ENABLE" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="帮助文档模块">
                  <el-switch v-model="settings.HELP_ENABLE" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="Markdown文档模块">
                  <el-switch v-model="settings.MARKDOWN_ENABLE" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="弹幕模块">
                  <el-switch v-model="settings.DANMU_ENABLE" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="控制面板模块">
                  <el-switch v-model="settings.DASHBOARD_ENABLE" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
          <div class="settings-section">
            <h3>国际化配置</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="时区">
                  <el-select v-model="settings.TIMEZONE" placeholder="选择时区">
                    <el-option label="Asia/Shanghai" value="Asia/Shanghai" />
                    <el-option label="UTC" value="UTC" />
                    <el-option label="America/New_York" value="America/New_York" />
                    <el-option label="Europe/London" value="Europe/London" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="语言">
                  <el-select v-model="settings.LANGUAGE" placeholder="选择语言">
                    <el-option label="简体中文" value="zh-CN" />
                    <el-option label="English" value="en-US" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <!-- 安全配置 -->
        <el-tab-pane label="安全配置" name="security">
          <div class="settings-section">
            <h3>认证配置</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="令牌过期时间(分钟)">
                  <el-input-number
                    v-model="settings.ACCESS_TOKEN_EXPIRE_MINUTES"
                    :min="1"
                    :max="10080"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="加密算法">
                  <el-select v-model="settings.ALGORITHM" placeholder="选择算法">
                    <el-option label="HS256" value="HS256" />
                    <el-option label="HS384" value="HS384" />
                    <el-option label="HS512" value="HS512" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="系统密钥">
              <div class="secret-key-section">
                <el-tag :type="settings.SECRET_KEY_SET ? 'success' : 'warning'">
                  {{ settings.SECRET_KEY_SET ? '已设置' : '未设置' }}
                </el-tag>
                <el-button type="primary" size="small" @click="showSecretKeyDialog = true">
                  {{ settings.SECRET_KEY_SET ? '更新密钥' : '设置密钥' }}
                </el-button>
              </div>
            </el-form-item>
          </div>
        </el-tab-pane>

        <!-- 数据库配置 -->
        <el-tab-pane label="数据库配置" name="database">
          <div class="settings-section">
            <h3>扩展数据库配置</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="数据库类型">
                  <el-select v-model="settings.EXT_DB_TYPE" placeholder="选择数据库类型" @change="updateDatabaseUrl">
                    <el-option label="SQLite" value="sqlite" />
                    <el-option label="MySQL" value="mysql" />
                    <el-option label="PostgreSQL" value="postgresql" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="数据根目录">
                  <el-input v-model="settings.EXT_DB_DIR" placeholder="扩展数据库目录" @input="updateDatabaseUrl" />
                </el-form-item>
              </el-col>
            </el-row>

            <!-- SQLite 配置 -->
            <div v-if="settings.EXT_DB_TYPE === 'sqlite'">
              <el-row :gutter="20">
                <el-col :span="24">
                  <el-form-item label="数据库文件">
                    <el-input v-model="settings.EXT_DB_FILE" placeholder="数据库文件名 (如: app.db)" @input="updateDatabaseUrl" />
                  </el-form-item>
                </el-col>
              </el-row>
            </div>

            <!-- MySQL/PostgreSQL 配置 -->
            <div v-else>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="主机地址">
                    <el-input v-model="settings.EXT_DB_HOST" placeholder="数据库主机" @input="updateDatabaseUrl" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="端口">
                    <el-input-number v-model="settings.EXT_DB_PORT" :min="1" :max="65535" placeholder="端口号" @change="updateDatabaseUrl" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="数据库名">
                    <el-input v-model="settings.EXT_DB_NAME" placeholder="数据库名称" @input="updateDatabaseUrl" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="用户名">
                    <el-input v-model="settings.EXT_DB_USER" placeholder="数据库用户名" @input="updateDatabaseUrl" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="密码">
                    <el-input v-model="settings.EXT_DB_PASSWORD" type="password" placeholder="数据库密码" show-password @input="updateDatabaseUrl" />
                  </el-form-item>
                </el-col>
              </el-row>
            </div>

            <!-- 生成的连接URL -->
            <el-row :gutter="20">
              <el-col :span="24">
                <el-form-item label="连接URL">
                  <el-input v-model="generatedDbUrl" placeholder="自动生成的数据库连接字符串" readonly>
                    <template #append>
                      <el-button @click="copyDbUrl" type="primary">复制</el-button>
                    </template>
                  </el-input>
                  <div class="form-help-text">
                    根据上述配置自动生成的数据库连接字符串
                  </div>
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <!-- 文件配置 -->
        <el-tab-pane label="文件配置" name="files">
          <div class="settings-section">
            <h3>目录配置</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="数据目录">
                  <el-input v-model="settings.DATA_DIR" placeholder="数据目录" readonly />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="配置目录">
                  <el-input v-model="settings.CONFIG_DIR" placeholder="配置目录" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <div class="settings-section">
            <h3>文件上传</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="上传目录">
                  <el-input v-model="settings.UPLOAD_DIR" placeholder="文件上传目录" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="最大文件大小(MB)">
                  <el-input-number
                    v-model="maxFileSizeMB"
                    :min="1"
                    :max="1024"
                    @change="updateMaxFileSize"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="允许的文件扩展名">
              <el-tag
                v-for="(ext, index) in settings.ALLOWED_EXTENSIONS"
                :key="index"
                closable
                @close="removeExtension(index)"
                class="extension-tag"
              >
                {{ ext }}
              </el-tag>
              <el-input
                v-if="inputVisible"
                ref="inputRef"
                v-model="inputValue"
                size="small"
                @keyup.enter="handleInputConfirm"
                @blur="handleInputConfirm"
                class="extension-input"
              />
              <el-button v-else size="small" @click="showInput">
                <el-icon>
                  <Plus />
                </el-icon>
                添加扩展名
              </el-button>
            </el-form-item>
          </div>

          <div class="settings-section">
            <h3>扩展管理</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="扩展目录">
                  <el-input v-model="settings.EXTENSIONS_DIR" placeholder="扩展存储目录" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="允许上传扩展">
                  <el-switch v-model="settings.ALLOW_EXTENSION_UPLOAD" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <div class="settings-section">
            <h3>Markdown编辑器</h3>
            <el-row :gutter="20">
              <el-col :span="24">
                <el-form-item label="Markdown文件夹路径">
                  <el-input
                    v-model="settings.MARKDOWN_FOLDER_PATH"
                    placeholder="例如: data/docs"
                    clearable
                  >
                    <template #append>
                      <el-button @click="testMarkdownPath">测试路径</el-button>
                    </template>
                  </el-input>
                  <div class="form-tip">
                    设置Markdown文件存储的文件夹路径，编辑器将列出此文件夹下所有.md文件
                  </div>
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <!-- 用户配置 -->
        <el-tab-pane label="用户配置" name="users">
          <div class="settings-section">
            <h3>用户注册</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="允许用户注册">
                  <el-switch v-model="settings.ALLOW_REGISTER" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="默认用户角色">
                  <el-select v-model="settings.DEFAULT_USER_ROLE" placeholder="选择默认角色">
                    <el-option
                      v-for="role in settings.ROLES"
                      :key="role.id"
                      :label="role.name"
                      :value="role.name"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <!-- 用户列表管理 -->
          <div class="settings-section">
            <div class="section-header">
              <h3>用户列表管理</h3>
              <el-button type="primary" @click="showCreateUserDialog" size="small">
                <el-icon><Plus /></el-icon>
                新增用户
              </el-button>
            </div>

            <!-- 搜索和筛选 -->
            <div class="user-filters">
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-input
                    v-model="userSearchKeyword"
                    placeholder="搜索用户名或昵称"
                    @input="searchUsers"
                    clearable
                  >
                    <template #prefix>
                      <el-icon><Search /></el-icon>
                    </template>
                  </el-input>
                </el-col>
                <el-col :span="6">
                  <el-select v-model="userStatusFilter" placeholder="状态筛选" @change="loadUsers">
                    <el-option label="全部" value="" />
                    <el-option label="活跃" value="active" />
                    <el-option label="禁用" value="inactive" />
                  </el-select>
                </el-col>
                <el-col :span="6">
                  <el-button @click="loadUsers" :loading="usersLoading">
                    <el-icon><Refresh /></el-icon>
                    刷新
                  </el-button>
                </el-col>
              </el-row>
            </div>

            <!-- 用户表格 -->
            <el-table
              :data="filteredUsers"
              v-loading="usersLoading"
              class="user-table"
              stripe
              border
            >
              <el-table-column prop="id" label="ID" width="80" />
              <el-table-column label="头像" width="80">
                <template #default="{ row }">
                  <el-avatar :size="40" :src="row.avatar">
                    <el-icon><User /></el-icon>
                  </el-avatar>
                </template>
              </el-table-column>
              <el-table-column prop="username" label="用户名" min-width="120" />
              <el-table-column prop="nickname" label="昵称" min-width="120" />
              <el-table-column prop="email" label="邮箱" min-width="180" />
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.is_active ? 'success' : 'danger'">
                    {{ row.is_active ? '活跃' : '禁用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="超级管理员" width="140">
                <template #default="{ row }">
                  <el-switch
                    v-model="row.is_superuser"
                    @change="toggleSuperuser(row)"
                    :disabled="row.id === currentUser?.id"
                    active-text="是"
                    inactive-text="否"
                    size="small"
                  />
                </template>
              </el-table-column>
              <el-table-column label="最近登录" width="160">
                <template #default="{ row }">
                  {{ formatDate(row.last_login) || '从未登录' }}
                </template>
              </el-table-column>
              <el-table-column label="创建时间" width="160">
                <template #default="{ row }">
                  {{ formatDate(row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column label="更新时间" width="160">
                <template #default="{ row }">
                  {{ formatDate(row.updated_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="200" fixed="right">
                <template #default="{ row }">
                  <el-button size="small" @click="showEditUserDialog(row)">
                    <el-icon><Edit /></el-icon>
                    编辑
                  </el-button>
                  <el-button
                    size="small"
                    type="danger"
                    @click="confirmDeleteUser(row)"
                    :disabled="row.id === currentUser?.id"
                  >
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 分页 -->
            <div class="pagination-wrapper">
              <el-pagination
                v-model:current-page="userPagination.page"
                v-model:page-size="userPagination.size"
                :page-sizes="[10, 20, 50, 100]"
                :total="userPagination.total"
                layout="total, sizes, prev, pager, next, jumper"
                @size-change="loadUsers"
                @current-change="loadUsers"
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- 邮件配置 -->
        <el-tab-pane label="邮件配置" name="email">
          <div class="settings-section">
            <h3>SMTP设置</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="SMTP服务器">
                  <el-input v-model="settings.SMTP_HOST" placeholder="smtp.example.com" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="SMTP端口">
                  <el-input-number v-model="settings.SMTP_PORT" :min="1" :max="65535" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="用户名">
                  <el-input v-model="settings.SMTP_USER" placeholder="邮箱用户名" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="密码">
                  <el-input
                    v-model="settings.SMTP_PASSWORD"
                    type="password"
                    placeholder="邮箱密码"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="启用TLS">
              <el-switch v-model="settings.SMTP_TLS" />
            </el-form-item>
          </div>
        </el-tab-pane>

        <!-- 日志配置 -->
        <el-tab-pane label="日志配置" name="logging">
          <div class="settings-section">
            <h3>日志设置</h3>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="日志级别">
                  <el-select v-model="settings.LOG_LEVEL" placeholder="选择日志级别">
                    <el-option label="DEBUG" value="DEBUG" />
                    <el-option label="INFO" value="INFO" />
                    <el-option label="WARNING" value="WARNING" />
                    <el-option label="ERROR" value="ERROR" />
                    <el-option label="CRITICAL" value="CRITICAL" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="日志文件路径">
                  <el-input v-model="settings.LOG_DIR" placeholder="日志文件存储路径" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <!-- 系统命令 -->
        <el-tab-pane label="系统命令" name="commands">
          <div class="commands-section">
            <!-- 系统信息 -->
            <div class="system-info-card">
              <h3>
                <el-icon>
                  <Monitor />
                </el-icon>
                系统信息
              </h3>
              <div class="system-info-grid">
                <div class="info-item">
                  <span class="info-label">系统:</span>
                  <span class="info-value">{{ systemInfo.platform || systemInfo.os || '未知' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">架构:</span>
                  <span class="info-value">{{ systemInfo.architecture || '未知' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">环境:</span>
                  <span class="info-value">{{ getEnvironmentDisplay(systemInfo) }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Python:</span>
                  <span class="info-value">{{ systemInfo.python_version || '未知' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">解释器:</span>
                  <span class="info-value" :title="systemInfo.python_executable">{{ systemInfo.python_executable || '未知' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">目录:</span>
                  <span class="info-value" :title="systemInfo.current_directory">{{ systemInfo.current_directory || '未知' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">脚本:</span>
                  <span class="info-value">{{ systemInfo.script_path || systemInfo.main_script || 'main.py' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">PID:</span>
                  <span class="info-value">{{ systemInfo.pid || '未知' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">运行:</span>
                  <span class="info-value">{{ formatUptime(systemInfo.uptime) || '未知' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">内存:</span>
                  <span class="info-value">{{ formatMemoryUsage(systemInfo.memory_usage) || '未知' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">CPU:</span>
                  <span class="info-value">{{ formatCpuUsage(systemInfo.cpu_usage) || '未知' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">启动:</span>
                  <span class="info-value">{{ systemInfo.restart_method || '未知' }}</span>
                </div>
              </div>
            </div>

            <!-- 自定义命令 -->
            <div class="custom-commands-card">
              <h3>
                <el-icon>
                  <Edit />
                </el-icon>
                自定义命令
                <el-button
                  type="primary"
                  size="small"
                  @click="addCustomCommand"
                  style="margin-left: 12px"
                >
                  <el-icon>
                    <Plus />
                  </el-icon>
                  添加命令
                </el-button>
              </h3>

              <div class="custom-commands-list">
                <div
                  v-for="(cmd, index) in customCommands"
                  :key="index"
                  class="custom-command-item"
                >
                  <el-input v-model="cmd.name" placeholder="命令名称" size="small" style="width: 120px;" />
                  <el-input v-model="cmd.command" placeholder="输入命令" size="small" style="flex: 1; min-width: 180px;" />
                  <el-input v-model="cmd.description" placeholder="描述（可选）" size="small" style="width: 140px;" />
                  <el-button type="primary" size="small" @click="executeCommand(cmd.command, cmd.name)" :loading="executingCommands.includes(`custom-${index}`)" :disabled="!cmd.command.trim()">
                    <el-icon><CaretRight /></el-icon>执行
                  </el-button>
                  <el-button type="danger" size="small" @click="removeCustomCommand(index)">
                    <el-icon><Delete /></el-icon>删除
                  </el-button>
                </div>
              </div>

              <div class="commands-actions">
                <el-button type="success" @click="saveCustomCommands">
                  <el-icon>
                    <Check />
                  </el-icon>
                  保存命令
                </el-button>
                <el-button @click="loadCustomCommands">
                  <el-icon>
                    <Refresh />
                  </el-icon>
                  重新加载
                </el-button>
                <el-button type="info" @click="checkPythonProcess">
                  <el-icon>
                    <Operation />
                  </el-icon>
                  检查Python进程
                </el-button>
                <el-button type="warning" @click="createRestartScript">
                  <el-icon>
                    <RefreshRight />
                  </el-icon>
                  生成重启脚本
                </el-button>
              </div>

              <el-divider content-position="left">进程管理器控制</el-divider>

              <div style="margin-bottom: 20px">
                <el-button
                  type="primary"
                  @click="processRestart"
                  style="background: #409eff; border-color: #409eff; margin-right: 10px"
                >
                  <el-icon>
                    <Refresh />
                  </el-icon>
                  进程管理器重启
                </el-button>
                <el-button type="warning" @click="processForceRestart" style="margin-right: 10px">
                  <el-icon>
                    <Operation />
                  </el-icon>
                  强制重启
                </el-button>
                <el-button type="danger" @click="processStop" style="margin-right: 10px">
                  <el-icon>
                    <Close />
                  </el-icon>
                  停止服务
                </el-button>
                <el-button type="info" @click="showProcessConfig">
                  <el-icon>
                    <Setting />
                  </el-icon>
                  进程配置
                </el-button>
              </div>
            </div>

            <!-- 命令执行结果 -->
            <div class="command-result-card" v-if="commandResults.length > 0">
              <h3>
                <el-icon>
                  <Document />
                </el-icon>
                执行结果
                <el-button
                  type="danger"
                  size="small"
                  @click="clearResults"
                  style="margin-left: 12px"
                >
                  <el-icon>
                    <Delete />
                  </el-icon>
                  清空结果
                </el-button>
              </h3>

              <div class="results-list">
                <div
                  v-for="(result, index) in commandResults"
                  :key="index"
                  class="result-item"
                  :class="{ 'result-error': result.error }"
                >
                  <div class="result-header">
                    <span class="result-command">{{ result.command }}</span>
                    <span class="result-time">{{ formatTime(result.timestamp) }}</span>
                    <el-tag :type="result.error ? 'danger' : 'success'" size="small">
                      {{ result.error ? '失败' : '成功' }}
                    </el-tag>
                  </div>
                  <div class="result-content">
                    <pre>{{ result.output }}</pre>
                  </div>
                </div>
              </div>
            </div>

            <!-- 帮助信息 -->
            <div class="help-commands-card">
              <h3>
                <el-icon>
                  <Document />
                </el-icon>
                常用命令帮助
              </h3>
              <div class="help-commands-grid">
                <div v-for="cmd in helpCommands" :key="cmd.id" class="help-command-item">
                  <div class="help-info">
                    <div class="help-name">{{ cmd.name }}</div>
                    <div class="help-desc">{{ cmd.description }}</div>
                    <div class="help-text">{{ cmd.help }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 密钥设置对话框 -->
    <el-dialog v-model="showSecretKeyDialog" title="设置系统密钥" width="500px">
      <el-form :model="secretKeyForm" label-width="120px">
        <el-form-item label="新密钥" required>
          <el-input
            v-model="secretKeyForm.secret_key"
            type="password"
            placeholder="请输入至少32位的密钥"
            show-password
          />
          <div class="form-tip">密钥用于JWT令牌签名，请妥善保管。建议使用随机生成的强密钥。</div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="generateSecretKey">
            <el-icon>
              <Refresh />
            </el-icon>
            生成随机密钥
          </el-button>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showSecretKeyDialog = false">取消</el-button>
        <el-button type="primary" @click="updateSecretKey" :loading="updatingKey"> 确定</el-button>
      </template>
    </el-dialog>

    <!-- 进程配置对话框 -->
    <el-dialog
      v-model="processConfigVisible"
      title="进程管理器配置"
      width="800px"
      :before-close="handleProcessConfigClose"
    >
      <el-form :model="processConfig" label-width="120px">
        <el-form-item label="命令">
          <el-input v-model="processConfig.command" placeholder="执行的命令，如: python" />
        </el-form-item>
        <el-form-item label="参数">
          <el-input
            v-model="argsString"
            placeholder="命令参数，用空格分隔，如: main.py --port 8000"
          />
        </el-form-item>
        <el-form-item label="工作目录">
          <el-input v-model="processConfig.cwd" placeholder="工作目录路径" />
        </el-form-item>
        <el-form-item label="检查端口">
          <el-input-number
            v-model="processConfig.check_port"
            :min="1"
            :max="65535"
            placeholder="检查的端口号"
          />
        </el-form-item>
        <el-form-item label="检查URL">
          <el-input
            v-model="processConfig.check_url"
            placeholder="检查的URL，如: http://localhost:8000/"
          />
        </el-form-item>
        <el-form-item label="重启延迟">
          <el-input-number
            v-model="processConfig.restart_delay"
            :min="1"
            :max="60"
            placeholder="重启延迟秒数"
          />
        </el-form-item>
        <el-form-item label="自动重启">
          <el-switch v-model="processConfig.auto_restart" />
        </el-form-item>
        <el-form-item label="最大重启次数">
          <el-input-number
            v-model="processConfig.max_restart_attempts"
            :min="-1"
            placeholder="-1表示无限制"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="processConfigVisible = false">取消</el-button>
          <el-button type="primary" @click="saveProcessConfig">保存配置</el-button>
          <el-button type="success" @click="applyProcessConfig">应用配置</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 用户创建/编辑对话框 -->
    <el-dialog
      v-model="userDialogVisible"
      :title="userDialogMode === 'create' ? '新增用户' : '编辑用户'"
      width="600px"
      :before-close="handleUserDialogClose"
    >
      <el-form
        ref="userFormRef"
        :model="userForm"
        :rules="userFormRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="userForm.username"
            placeholder="请输入用户名"
            :disabled="userDialogMode === 'edit'"
          />
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="userForm.nickname" placeholder="请输入昵称" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="userForm.email"
            placeholder="请输入邮箱"
            type="email"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="userDialogMode === 'create'">
          <el-input
            v-model="userForm.password"
            placeholder="请输入密码"
            type="password"
            show-password
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch
            v-model="userForm.is_active"
            active-text="活跃"
            inactive-text="禁用"
          />
        </el-form-item>
        <el-form-item label="头像URL">
          <el-input v-model="userForm.avatar" placeholder="请输入头像URL（可选）" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="handleUserDialogClose">取消</el-button>
        <el-button type="primary" @click="saveUser" :loading="userSaving">
          {{ userDialogMode === 'create' ? '创建' : '保存' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Monitor,
  Setting,
  Check,
  RefreshLeft,
  Plus,
  Refresh,
  Operation,
  Edit,
  CaretRight,
  Delete,
  Document,
  RefreshRight,
  User,
  Search,
  Close,
} from '@element-plus/icons-vue'
import {
  getSettingsApi,
  updateSettingsApi,
  getExpiryInfoApi,
  updateSecretKeyApi,
  getConfigStatusApi,
  getSystemInfoApi,
  executeCommandApi,
  createRestartScriptApi,
  processRestartApi,
  processForceRestartApi,
  processStopApi,
  getProcessConfigApi,
  updateProcessConfigApi,
} from '@/api/settings'

// 导入用户相关API
import {
  getUsersApi,
  createUserApi,
  updateUserApi,
  deleteUserApi,
  getCurrentUserApi,
  toggleUserSuperuserApi,
} from '@/api/user'
import { getRolesApi } from '@/api/auth'
// 响应式数据
const loading = ref(false)
const saving = ref(false)
const updatingKey = ref(false)
const activeTab = ref('basic')

// 系统状态
const expiryInfo = ref({
  expired: false,
  days_left: 0,
  expiry_date: null,
  initialized_at: null,
})

const configStatus = ref({
  config_file_exists: false,
  config_dir: '',
  initialized_at: null,
  updated_at: null,
  total_config_items: 0,
})

// 系统命令相关数据
const systemInfo = ref({
  os: '',
  python_version: '',
  pid: '',
  uptime: '',
  memory_usage: '',
  cpu_usage: '',
})

const helpCommands = ref([
  {
    id: 'restart-service',
    name: '重启当前服务',
    description: '重启当前Python应用程序',
    help: '推荐使用独立重启脚本，避免API响应中断问题。点击"生成重启脚本"按钮创建脚本。',
  },
  {
    id: 'check-python',
    name: '检查Python版本',
    description: '查看当前Python版本信息',
    help: '检查Python版本：python --version 或 python -V',
  },
  {
    id: 'check-pip',
    name: '检查pip包',
    description: '查看已安装的Python包',
    help: '列出已安装包：pip list 或 pip freeze',
  },
  {
    id: 'disk-usage',
    name: '磁盘使用情况',
    description: '查看磁盘空间使用情况',
    help: 'Windows: wmic logicaldisk get size,freespace,caption\nLinux: df -h',
  },
  {
    id: 'memory-info',
    name: '内存信息',
    description: '查看内存使用情况',
    help: 'Windows: wmic OS get TotalVisibleMemorySize,FreePhysicalMemory\nLinux: free -h',
  },
  {
    id: 'process-list',
    name: '进程列表',
    description: '查看系统进程',
    help: 'Windows: tasklist\nLinux: ps aux',
  },
  {
    id: 'network-status',
    name: '网络状态',
    description: '查看网络连接状态',
    help: 'Windows: netstat -an\nLinux: netstat -tuln',
  },
  {
    id: 'current-dir',
    name: '当前目录',
    description: '查看当前工作目录',
    help: 'Windows: cd\nLinux: pwd',
  },
  {
    id: 'list-files',
    name: '列出文件',
    description: '列出当前目录文件',
    help: 'Windows: dir\nLinux: ls -la',
  },
  {
    id: 'system-info',
    name: '系统信息',
    description: '查看系统详细信息',
    help: 'Windows: systeminfo\nLinux: uname -a',
  },
  {
    id: 'kill-process',
    name: '结束进程',
    description: '结束指定进程',
    help: 'Windows按进程名: TASKKILL /IM 进程名.exe /F\nWindows按PID: TASKKILL /PID 进程ID /F\nLinux: kill -9 进程ID',
  },
  {
    id: 'find-process',
    name: '查找进程',
    description: '查找特定进程',
    help: 'Windows: tasklist | findstr python\nLinux: ps aux | grep python\n\n快速检查: 点击下方的"检查Python进程"按钮',
  },
  {
    id: 'check-port',
    name: '检查端口',
    description: '检查端口占用情况',
    help: 'Windows: netstat -ano | findstr :8000\nLinux: netstat -tuln | grep :8000',
  },
  {
    id: 'environment-vars',
    name: '环境变量',
    description: '查看环境变量',
    help: 'Windows: set\nLinux: env',
  },
])

const customCommands = ref([])
const executingCommands = ref([])
const commandResults = ref([])

// 设置数据
const settings = reactive({
  // 基础配置
  APP_NAME: '',
  PROJECT_NAME: 'Data Query System',
  VERSION: '2.0.0',
  DEBUG: false,
  HOST: '0.0.0.0',
  PORT: 8000,

  // 安全配置
  ACCESS_TOKEN_EXPIRE_MINUTES: 30,
  ALGORITHM: 'HS256',
  SECRET_KEY_SET: false,

  // 数据库配置
  EXT_DB_DIR: 'data/db',
  EXT_DB_TYPE: 'sqlite',
  EXT_DB_FILE: 'app.db',
  EXT_DB_HOST: 'localhost',
  EXT_DB_PORT: 3306,
  EXT_DB_NAME: '',
  EXT_DB_USER: '',
  EXT_DB_PASSWORD: '',
  EXT_DB_CONFIG: {},
  // 目录配置（只读）
  DATA_DIR: 'data',
  CONFIG_DIR: '',

  // 文件配置
  UPLOAD_DIR: 'data/uploads',
  MAX_FILE_SIZE: 104857600,
  ALLOWED_EXTENSIONS: [],

  // 扩展配置
  EXTENSIONS_DIR: 'data/extensions',
  ALLOW_EXTENSION_UPLOAD: true,

  // Markdown编辑器配置
  MARKDOWN_FOLDER_PATH: 'data/docs',

  // 用户配置
  ALLOW_REGISTER: true,
  DEFAULT_USER_ROLE: 'user',

  // 日志配置
  LOG_LEVEL: 'INFO',
  LOG_FILE: 'data/logs/app.log',
  LOG_PATH: '',

  // 邮件配置
  SMTP_HOST: '',
  SMTP_PORT: 587,
  SMTP_USER: '',
  SMTP_PASSWORD: '',
  SMTP_TLS: true,

  // 国际化配置
  TIMEZONE: 'Asia/Shanghai',
  LANGUAGE: 'zh-CN',
})
const roles = ref([])
const dbTypes = ref(['sqlite', 'mysql', 'postgresql', 'mssql'])
const db_url = computed({
  get: () => settings.EXT_DB_CONFIG[settings.EXT_DB_TYPE].db_url,
  set: (value) => {
    settings.MAX_FILE_SIZE = value * 1024 * 1024
  },
})
// 原始设置（用于重置）
const originalSettings = ref({})

// 密钥设置
const showSecretKeyDialog = ref(false)
const secretKeyForm = reactive({
  secret_key: '',
})

// 进程管理器相关
const processConfigVisible = ref(false)
const processConfig = ref({
  command: '',
  args: [],
  cwd: '',
  check_port: 8000,
  check_url: '',
  restart_delay: 3,
  auto_restart: true,
  max_restart_attempts: 10,
})
const argsString = ref('')

// 数据库URL生成
const generatedDbUrl = ref('')

// 用户管理相关数据
const users = ref([])
const filteredUsers = ref([])
const usersLoading = ref(false)
const userSearchKeyword = ref('')
const userStatusFilter = ref('')
const userPagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 用户对话框相关
const userDialogVisible = ref(false)
const userDialogMode = ref('create') // 'create' | 'edit'
const userSaving = ref(false)
const userFormRef = ref()
const currentUser = ref(null)

const userForm = reactive({
  id: null,
  username: '',
  nickname: '',
  email: '',
  password: '',
  is_active: true,
  avatar: ''
})

const userFormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  nickname: [
    { required: true, message: '请输入昵称', trigger: 'blur' },
    { min: 2, max: 50, message: '昵称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 个字符', trigger: 'blur' }
  ]
}

// 文件扩展名输入
const inputVisible = ref(false)
const inputValue = ref('')
const inputRef = ref()

// 计算属性
const maxFileSizeMB = computed({
  get: () => Math.round(settings.MAX_FILE_SIZE / (1024 * 1024)),
  set: (value) => {
    settings.MAX_FILE_SIZE = value * 1024 * 1024
  },
})

// 方法
const loadSettings = async () => {
  loading.value = true
  try {
    const response = await getSettingsApi()
    Object.assign(settings, response.data)
    originalSettings.value = JSON.parse(JSON.stringify(response.data))
    ElMessage.success('设置加载成功')
    const roles = await getRolesApi()
    settings.ROLES = roles
  } catch (error) {
    console.error('加载设置失败:', error)
    ElMessage.error('加载设置失败')
  } finally {
    loading.value = false
  }
}

const loadExpiryInfo = async () => {
  try {
    const response = await getExpiryInfoApi()
    expiryInfo.value = response.data
  } catch (error) {
    console.error('加载过期信息失败:', error)
  }
}

const loadConfigStatus = async () => {
  try {
    const response = await getConfigStatusApi()
    configStatus.value = response.data
  } catch (error) {
    console.error('加载配置状态失败:', error)
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    await updateSettingsApi(settings)
    originalSettings.value = JSON.parse(JSON.stringify(settings))
    ElMessage.success('设置保存成功')

    // 重新加载状态信息
    await loadConfigStatus()
  } catch (error) {
    console.error('保存设置失败:', error)
    ElMessage.error('保存设置失败')
  } finally {
    saving.value = false
  }
}

const resetSettings = () => {
  ElMessageBox.confirm('确定要重置所有设置吗？这将恢复到上次保存的状态。', '确认重置', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      Object.assign(settings, originalSettings.value)
      ElMessage.success('设置已重置')
    })
    .catch(() => {
      // 用户取消
    })
}

const updateMaxFileSize = (value) => {
  settings.MAX_FILE_SIZE = value * 1024 * 1024
}

const removeExtension = (index) => {
  settings.ALLOWED_EXTENSIONS.splice(index, 1)
}

const showInput = () => {
  inputVisible.value = true
  nextTick(() => {
    inputRef.value?.focus()
  })
}

const handleInputConfirm = () => {
  if (inputValue.value) {
    let ext = inputValue.value.trim()
    if (!ext.startsWith('.')) {
      ext = '.' + ext
    }
    if (!settings.ALLOWED_EXTENSIONS.includes(ext)) {
      settings.ALLOWED_EXTENSIONS.push(ext)
    }
  }
  inputVisible.value = false
  inputValue.value = ''
}

const testMarkdownPath = async () => {
  if (!settings.MARKDOWN_FOLDER_PATH) {
    ElMessage.warning('请先输入Markdown文件夹路径')
    return
  }

  try {
    // 这里可以调用API测试文件夹路径是否有效
    ElMessage.success('Markdown文件夹路径测试成功')
  } catch (error) {
    ElMessage.error('Markdown文件夹路径测试失败: ' + error.message)
  }
}

const generateSecretKey = () => {
  // 生成32位随机密钥
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < 64; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  secretKeyForm.secret_key = result
}

const updateSecretKey = async () => {
  if (!secretKeyForm.secret_key || secretKeyForm.secret_key.length < 32) {
    ElMessage.error('密钥长度至少为32位')
    return
  }

  updatingKey.value = true
  try {
    await updateSecretKeyApi(secretKeyForm.secret_key)

    settings.SECRET_KEY_SET = true
    showSecretKeyDialog.value = false
    secretKeyForm.secret_key = ''
    ElMessage.success('密钥更新成功')
  } catch (error) {
    console.error('更新密钥失败:', error)
    ElMessage.error('更新密钥失败')
  } finally {
    updatingKey.value = false
  }
}

// 系统命令相关方法
const loadSystemInfo = async () => {
  try {
    const response = await getSystemInfoApi()
    const data = response.data
    systemInfo.value = data
    updateHelpCommands(data)

    // 自动添加默认重启命令到自定义命令
    if (data.default_restart_commands && data.default_restart_commands.length > 0) {
      addDefaultRestartCommands(data.default_restart_commands)
    }
    console.log('系统信息加载成功:', data)
  } catch (error) {
    console.error('加载系统信息失败:', error)
    ElMessage.error('获取系统信息失败: ' + error.message)
  }
}

const updateHelpCommands = (sysInfo) => {
  // 根据系统信息更新帮助信息
  const pythonExe = sysInfo.python_executable || 'python'
  const currentDir = sysInfo.current_directory || '.'
  const scriptPath = sysInfo.script_path || 'main.py'
  const pid = sysInfo.pid || '0000'
  const envType = sysInfo.environment_type || 'unknown'

  // 更新重启服务帮助信息
  const restartCmd = helpCommands.value.find((cmd) => cmd.id === 'restart-service')
  if (restartCmd) {
    let helpText = `检测到运行环境: ${envType}\n\n`

    if (sysInfo.is_docker) {
      helpText += `Docker环境重启：
docker restart $(hostname)

或使用独立脚本：
bash data/restart_service.sh`
    } else if (sysInfo.is_executable) {
      // 如果是打包的exe文件
      const exeName = scriptPath.split('\\').pop() || 'app.exe'
      helpText += `可执行文件重启：
TASKKILL /IM ${exeName} /F && "${scriptPath}"

推荐使用独立脚本：
data\\restart_service.bat`
    } else {
      // 如果是Python脚本
      const mainScript = sysInfo.main_script || 'app.py'
      const fullScriptPath = `${currentDir}\\${mainScript}`
      helpText += `Python应用重启：
TASKKILL /IM python.exe /F && "${pythonExe}" "${fullScriptPath}"

推荐使用独立脚本：
data\\restart_service.bat`
    }

    helpText += `\n\n注意：系统已自动生成适合当前环境的重启命令，请查看自定义命令部分。`
    restartCmd.help = helpText
  }

  // 更新检查Python版本帮助信息
  const pythonCmd = helpCommands.value.find((cmd) => cmd.id === 'check-python')
  if (pythonCmd) {
    pythonCmd.help = `检查Python版本：
"${pythonExe}" --version
"${pythonExe}" -V

Python路径: ${pythonExe}
是否有Python环境: ${sysInfo.has_python ? '是' : '否'}`
  }
}

const addDefaultRestartCommands = (defaultCommands) => {
  // 检查是否已经添加过默认命令
  const hasDefaultCommands = customCommands.value.some(
    (cmd) => cmd.name && cmd.name.includes('重启服务'),
  )

  if (!hasDefaultCommands && defaultCommands.length > 0) {
    // 添加默认重启命令到自定义命令列表
    defaultCommands.forEach((cmd) => {
      customCommands.value.push({
        name: cmd.name,
        command: cmd.command,
        description: cmd.description,
      })
    })

    // 添加后台重启命令
    customCommands.value.push({
      name: '后台重启服务',
      command: 'data\\restart_service_background.bat',
      description: '使用后台模式重启服务，避免终端窗口问题',
    })

    // 自动保存
    saveCustomCommands()

    ElMessage.success(`已自动添加 ${defaultCommands.length + 1} 个适合当前环境的重启命令`)
  }
}

const executeCommand = async (command, name) => {
  const commandId = `${name}-${Date.now()}`
  executingCommands.value.push(commandId)

  try {
    const response = await executeCommandApi(command, name)
    const result = response.data

    // 添加到结果列表
    commandResults.value.unshift({
      command: `${name}: ${command}`,
      output: result.output || result.error || '命令执行完成',
      error: !result.success,
      timestamp: new Date(),
    })

    if (result.success) {
      ElMessage.success(`命令 "${name}" 执行成功`)
    } else {
      ElMessage.error(`命令 "${name}" 执行失败: ${result.error || '未知错误'}`)
    }

    // 如果是重启命令，刷新系统信息
    if (command.includes('restart') || command.includes('python')) {
      setTimeout(() => {
        loadSystemInfo()
      }, 2000)
    }
  } catch (error) {
    console.error('执行命令失败:', error)
    ElMessage.error(`命令执行失败: ${error.message}`)

    commandResults.value.unshift({
      command: `${name}: ${command}`,
      output: `执行失败: ${error.message}`,
      error: true,
      timestamp: new Date(),
    })
  } finally {
    executingCommands.value = executingCommands.value.filter((id) => id !== commandId)
  }
}

const addCustomCommand = () => {
  customCommands.value.push({
    name: '',
    command: '',
    description: '',
  })
}

const removeCustomCommand = (index) => {
  customCommands.value.splice(index, 1)
}

const saveCustomCommands = async () => {
  try {
    localStorage.setItem('customCommands', JSON.stringify(customCommands.value))
    ElMessage.success('自定义命令保存成功')
  } catch (error) {
    console.error('保存自定义命令失败:', error)
    ElMessage.error('保存失败')
  }
}

const loadCustomCommands = async () => {
  try {
    const saved = localStorage.getItem('customCommands')
    if (saved) {
      customCommands.value = JSON.parse(saved)
    }
  } catch (error) {
    console.error('加载自定义命令失败:', error)
  }
}

const createRestartScript = async () => {
  try {
    const response = await createRestartScriptApi()
    const result = response.data
    ElMessage.success('重启脚本已生成')

    // 添加到结果显示
    commandResults.value.unshift({
      command: '生成重启脚本',
      output: `脚本已创建:\n${result.scripts.join('\n')}\n\n启动命令: ${result.start_command}`,
      error: false,
      timestamp: new Date(),
    })

    // 更新帮助信息
    const restartCmd = helpCommands.value.find((cmd) => cmd.id === 'restart-service')
    if (restartCmd) {
      restartCmd.help = `重启脚本已生成，推荐使用独立脚本重启：

Windows: data\\restart_service.bat
Linux: data/restart_service.sh

或使用命令行：
TASKKILL /IM python.exe /F && "${result.start_command}"

脚本会自动处理进程停止和启动，避免API响应中断问题。`
    }
  } catch (error) {
    console.error('生成重启脚本失败:', error)
    ElMessage.error('生成重启脚本失败: ' + error.message)
  }
}

const checkPythonProcess = async () => {
  try {
    await executeCommand('tasklist | findstr python', '检查Python进程')
  } catch (error) {
    console.error('检查进程失败:', error)
  }
}

const testSimpleRestart = async () => {
  try {
    await executeCommand('data\\simple_restart.bat', '测试简单重启')
    ElMessage.info('重启脚本已执行，请等待几秒钟后检查进程状态')
  } catch (error) {
    console.error('测试重启失败:', error)
  }
}

const testWorkingRestart = async () => {
  try {
    await executeCommand('data\\working_restart.bat', '调试重启')
    ElMessage.info('调试重启脚本已执行，会显示详细的执行过程')
  } catch (error) {
    console.error('调试重启失败:', error)
  }
}

const testBackgroundRestart = async () => {
  try {
    await executeCommand('data\\background_restart.bat', '后台重启')
    ElMessage.info('后台重启脚本已执行，使用PowerShell后台启动')
  } catch (error) {
    console.error('后台重启失败:', error)
  }
}

const runDiagnose = async () => {
  try {
    await executeCommand('data\\diagnose.bat', '系统诊断')
    ElMessage.info('系统诊断已开始，请查看详细的检查结果')
  } catch (error) {
    console.error('系统诊断失败:', error)
  }
}

const runMinimalTest = async () => {
  try {
    await executeCommand('data\\minimal_test.bat', '最小测试')
    ElMessage.info('最小测试已开始，这将在前台启动应用用于调试')
  } catch (error) {
    console.error('最小测试失败:', error)
  }
}

const runStartupDiagnosis = async () => {
  try {
    await executeCommand('data\\startup_diagnosis.bat', '启动诊断')
    ElMessage.info('启动诊断已开始，将全面检查启动环境和依赖')
  } catch (error) {
    console.error('启动诊断失败:', error)
  }
}

const runReliableRestart = async () => {
  try {
    await executeCommand('data\\reliable_restart.bat', '可靠重启')
    ElMessage.info('可靠重启已开始，将尝试多种方式确保启动成功')
  } catch (error) {
    console.error('可靠重启失败:', error)
  }
}

const runWorkingRestart = async () => {
  try {
    await executeCommand('data\\working_restart.bat', '修复重启')
    ElMessage.info('修复重启已开始，使用简单有效的重启方式')
  } catch (error) {
    console.error('修复重启失败:', error)
  }
}

const testStartup = async () => {
  try {
    await executeCommand('data\\test_startup.bat', '测试启动')
    ElMessage.info('测试启动已开始，会在前台运行用于调试')
  } catch (error) {
    console.error('测试启动失败:', error)
  }
}

const basicRestart = async () => {
  try {
    await executeCommand('data\\basic_restart.bat', '基础重启')
    ElMessage.info('基础重启已开始，使用最简单的重启方式')
  } catch (error) {
    console.error('基础重启失败:', error)
  }
}

const backgroundStart = async () => {
  try {
    await executeCommand('data\\background_start.bat', '后台启动')
    ElMessage.info('后台启动已开始，会在新窗口中启动应用')
  } catch (error) {
    console.error('后台启动失败:', error)
  }
}

const finalRestart = async () => {
  try {
    await executeCommand('data\\final_restart.bat', '已测试重启')
    ElMessage.success('已测试的重启脚本执行完成！这个脚本已经验证可以正常工作')
  } catch (error) {
    console.error('已测试重启失败:', error)
  }
}

const testApiRestart = async () => {
  try {
    // 先重新生成脚本
    await createRestartScript()

    // 等待一下
    setTimeout(async () => {
      try {
        await executeCommand('data\\restart_service.bat', '测试API重启')
        ElMessage.success('API生成的重启脚本测试完成')
      } catch (error) {
        console.error('API重启脚本执行失败:', error)
      }
    }, 1000)
  } catch (error) {
    console.error('测试API重启失败:', error)
  }
}

const fixedRestart = async () => {
  try {
    await executeCommand('data\\fixed_restart.bat', '修复版重启')
    ElMessage.success('修复版重启脚本执行完成！这个版本保证能启动成功')
  } catch (error) {
    console.error('修复版重启失败:', error)
  }
}

// 进程管理器方法
const processRestart = async () => {
  try {
    await ElMessageBox.confirm('确定要重启服务吗？这将重启整个应用程序。', '确认重启', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    const response = await processRestartApi()
    ElMessage.success('重启命令已发送给进程管理器')
    console.log('进程管理器重启:', response.data)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('进程管理器重启失败:', error)
      ElMessage.error('进程管理器重启失败: ' + error.message)
    }
  }
}

const processForceRestart = async () => {
  try {
    await ElMessageBox.confirm('确定要强制重启服务吗？这将关闭整个应用程序。', '确认强制重启', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    const response = await processForceRestartApi()
    ElMessage.success('强制重启命令已发送给进程管理器')
    console.log('进程管理器强制重启:', response.data)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('进程管理器强制重启失败:', error)
      ElMessage.error('进程管理器强制重启失败: ' + error.message)
    }
  }
}

const processStop = async () => {
  try {
    await ElMessageBox.confirm('确定要停止服务吗？这将关闭整个应用程序。', '确认停止', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    const response = await processStopApi()
    ElMessage.success('停止命令已发送给进程管理器')
    console.log('进程管理器停止:', response.data)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('进程管理器停止失败:', error)
      ElMessage.error('进程管理器停止失败: ' + error.message)
    }
  }
}

const showProcessConfig = async () => {
  try {
    // 获取当前配置
    const response = await getProcessConfigApi()
    const result = response.data
    if (result.success && result.config) {
      processConfig.value = { ...result.config }
      argsString.value = result.config.args ? result.config.args.join(' ') : ''
    }

    processConfigVisible.value = true
  } catch (error) {
    console.error('获取进程配置失败:', error)
    ElMessage.error('获取进程配置失败: ' + error.message)
  }
}

const handleProcessConfigClose = () => {
  processConfigVisible.value = false
}

const saveProcessConfig = async () => {
  try {
    // 处理参数字符串
    const config = { ...processConfig.value }
    config.args = argsString.value ? argsString.value.split(' ').filter((arg) => arg.trim()) : []

    const response = await updateProcessConfigApi(config)
    ElMessage.success('配置已保存并应用')
    processConfigVisible.value = false
    console.log('进程配置更新:', response.data)
  } catch (error) {
    console.error('保存进程配置失败:', error)
    ElMessage.error('保存进程配置失败: ' + error.message)
  }
}

const applyProcessConfig = async () => {
  try {
    await saveProcessConfig()
    // 重启以应用新配置
    setTimeout(() => {
      processRestart()
    }, 1000)
  } catch (error) {
    console.error('应用进程配置失败:', error)
  }
}

// 数据库URL生成和管理
const updateDatabaseUrl = () => {
  const dbType = settings.value.EXT_DB_TYPE

  if (dbType === 'sqlite') {
    const dbDir = settings.value.EXT_DB_DIR || 'data/db'
    const dbFile = settings.value.EXT_DB_FILE || 'app.db'
    generatedDbUrl.value = `sqlite:///${dbDir}/${dbFile}`
  } else if (dbType === 'mysql') {
    const host = settings.value.EXT_DB_HOST || 'localhost'
    const port = settings.value.EXT_DB_PORT || 3306
    const user = settings.value.EXT_DB_USER || ''
    const password = settings.value.EXT_DB_PASSWORD || ''
    const dbname = settings.value.EXT_DB_NAME || ''

    if (user && password && dbname) {
      generatedDbUrl.value = `mysql://${user}:${password}@${host}:${port}/${dbname}`
    } else {
      generatedDbUrl.value = `mysql://${host}:${port}/${dbname || 'database_name'}`
    }
  } else if (dbType === 'postgresql') {
    const host = settings.value.EXT_DB_HOST || 'localhost'
    const port = settings.value.EXT_DB_PORT || 5432
    const user = settings.value.EXT_DB_USER || ''
    const password = settings.value.EXT_DB_PASSWORD || ''
    const dbname = settings.value.EXT_DB_NAME || ''

    if (user && password && dbname) {
      generatedDbUrl.value = `postgresql://${user}:${password}@${host}:${port}/${dbname}`
    } else {
      generatedDbUrl.value = `postgresql://${host}:${port}/${dbname || 'database_name'}`
    }
  }
}

const copyDbUrl = async () => {
  try {
    await navigator.clipboard.writeText(generatedDbUrl.value)
    ElMessage.success('数据库URL已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败，请手动复制')
  }
}

// 用户管理方法
const loadUsers = async () => {
  try {
    usersLoading.value = true
    const skip = (userPagination.page - 1) * userPagination.size
    const response = await getUsersApi(skip, userPagination.size)
    users.value = response.data
    userPagination.total = response.data.length // 简化处理，实际应该从响应头或响应体获取总数
    filterUsers()
  } catch (error) {
    console.error('加载用户列表失败:', error)
    ElMessage.error('加载用户列表失败: ' + error.message)
  } finally {
    usersLoading.value = false
  }
}

const filterUsers = () => {
  let filtered = [...users.value]

  // 关键词搜索
  if (userSearchKeyword.value) {
    const keyword = userSearchKeyword.value.toLowerCase()
    filtered = filtered.filter(user =>
      user.username.toLowerCase().includes(keyword) ||
      user.nickname.toLowerCase().includes(keyword) ||
      (user.email && user.email.toLowerCase().includes(keyword))
    )
  }

  // 状态筛选
  if (userStatusFilter.value) {
    if (userStatusFilter.value === 'active') {
      filtered = filtered.filter(user => user.is_active)
    } else if (userStatusFilter.value === 'inactive') {
      filtered = filtered.filter(user => !user.is_active)
    }
  }

  filteredUsers.value = filtered
}

const searchUsers = () => {
  filterUsers()
}

const showCreateUserDialog = () => {
  userDialogMode.value = 'create'
  resetUserForm()
  userDialogVisible.value = true
}

const showEditUserDialog = (user) => {
  userDialogMode.value = 'edit'
  Object.assign(userForm, {
    id: user.id,
    username: user.username,
    nickname: user.nickname,
    email: user.email,
    is_active: user.is_active,
    avatar: user.avatar || '',
    password: '' // 编辑时不显示密码
  })
  userDialogVisible.value = true
}

const resetUserForm = () => {
  Object.assign(userForm, {
    id: null,
    username: '',
    nickname: '',
    email: '',
    password: '',
    is_active: true,
    avatar: ''
  })
  if (userFormRef.value) {
    userFormRef.value.clearValidate()
  }
}

const handleUserDialogClose = () => {
  userDialogVisible.value = false
  resetUserForm()
}

const saveUser = async () => {
  try {
    await userFormRef.value.validate()
    userSaving.value = true

    const userData = {
      username: userForm.username,
      nickname: userForm.nickname,
      email: userForm.email,
      is_active: userForm.is_active,
      avatar: userForm.avatar || null
    }

    if (userDialogMode.value === 'create') {
      userData.password = userForm.password
      await createUserApi(userData)
      ElMessage.success('用户创建成功')
    } else {
      await updateUserApi(userForm.id, userData)
      ElMessage.success('用户更新成功')
    }

    userDialogVisible.value = false
    resetUserForm()
    loadUsers()
  } catch (error) {
    console.error('保存用户失败:', error)
    ElMessage.error('保存用户失败: ' + error.message)
  } finally {
    userSaving.value = false
  }
}

const confirmDeleteUser = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await deleteUserApi(user.id)
    ElMessage.success('用户删除成功')
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
      ElMessage.error('删除用户失败: ' + error.message)
    }
  }
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

const toggleSuperuser = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要${user.is_superuser ? '设置' : '取消'} "${user.username}" 的超级管理员权限吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await toggleUserSuperuserApi(user.id, user.is_superuser)
    ElMessage.success(`已${user.is_superuser ? '设置为' : '取消'}超级管理员`)
    loadUsers() // 重新加载用户列表
  } catch (error) {
    if (error !== 'cancel') {
      console.error('修改超级管理员状态失败:', error)
      ElMessage.error('修改超级管理员状态失败: ' + error.message)
      // 恢复开关状态
      user.is_superuser = !user.is_superuser
    } else {
      // 用户取消操作，恢复开关状态
      user.is_superuser = !user.is_superuser
    }
  }
}

const clearResults = () => {
  commandResults.value = []
  ElMessage.success('执行结果已清空')
}

const getEnvironmentDisplay = (sysInfo) => {
  if (!sysInfo) return '未知环境'

  const envType = sysInfo.environment_type || 'unknown'
  const envMap = {
    docker: 'Docker容器',
    windows_service: 'Windows服务',
    systemd_service: 'Systemd服务',
    executable: '可执行文件',
    python_script: 'Python脚本',
    development: '开发环境',
    production: '生产环境',
    unknown: '未知环境',
  }

  let display = envMap[envType] || envType

  // 添加更多环境信息
  if (sysInfo.is_docker) {
    display += ' (Docker)'
  }

  if (sysInfo.is_virtual_env) {
    display += ' (虚拟环境)'
  }

  if (sysInfo.is_conda_env) {
    display += ' (Conda环境)'
  }
  if (sysInfo.is_executable) display += ' (打包)'
  if (!sysInfo.has_python) display += ' (无Python环境)'

  return display
}

// 格式化运行时间
const formatUptime = (uptime) => {
  if (!uptime) return '未知'
  if (typeof uptime === 'string') return uptime

  const seconds = Math.floor(uptime)
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (days > 0) {
    return `${days}天 ${hours}小时 ${minutes}分钟`
  } else if (hours > 0) {
    return `${hours}小时 ${minutes}分钟`
  } else if (minutes > 0) {
    return `${minutes}分钟 ${secs}秒`
  } else {
    return `${secs}秒`
  }
}

// 格式化内存使用
const formatMemoryUsage = (memory) => {
  if (!memory) return '未知'
  if (typeof memory === 'string') return memory

  if (typeof memory === 'object') {
    const used = memory.used || 0
    const total = memory.total || 0
    const percent = total > 0 ? ((used / total) * 100).toFixed(1) : 0

    return `${formatBytes(used)} / ${formatBytes(total)} (${percent}%)`
  }

  return memory.toString()
}

// 格式化CPU使用率
const formatCpuUsage = (cpu) => {
  if (!cpu && cpu !== 0) return '未知'
  if (typeof cpu === 'string') return cpu

  if (typeof cpu === 'object') {
    const process = cpu.process || 0
    const system = cpu.system || 0
    const cores = cpu.cores || 0

    // 如果进程CPU使用率很低，主要显示系统CPU
    if (process < 1) {
      return `系统: ${system.toFixed(1)}% (${cores}核)`
    } else {
      return `进程: ${process.toFixed(1)}% | 系统: ${system.toFixed(1)}% (${cores}核)`
    }
  }

  if (typeof cpu === 'number') {
    return `${cpu.toFixed(1)}%`
  }

  return cpu.toString()
}

// 格式化字节数
const formatBytes = (bytes) => {
  if (!bytes && bytes !== 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatTime = (date) => {
  return new Date(date).toLocaleString('zh-CN')
}


// 生命周期
onMounted(async () => {
  await Promise.all([loadSettings(), loadExpiryInfo(), loadConfigStatus(), loadCustomCommands()])
  // 最后加载系统信息，这样可以更新帮助信息
  await loadSystemInfo()
  // 初始化数据库URL
  updateDatabaseUrl()
  // 加载用户列表
  await loadUsers()
  // 获取当前用户信息
  try {
    const response = await getCurrentUserApi()
    currentUser.value = response.data
  } catch (error) {
    console.error('获取当前用户信息失败:', error)
  }
})
</script>

<style scoped>
.system-settings {
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
  font-size: 28px;
  font-weight: 600;
}

.page-description {
  margin: 0;
  color: #909399;
  font-size: 16px;
}

/* 状态卡片 */
.status-card {
  margin-bottom: 24px;
  border-radius: 12px;
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-icon {
  font-size: 18px;
  color: #409eff;
}

.header-actions {
  margin-left: auto;
  display: flex;
  gap: 12px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.status-item {
  text-align: center;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
}

.status-label {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 8px;
}

.status-value {
  font-size: 18px;
  font-weight: 600;
}

.days-left {
  font-size: 24px;
  font-weight: 700;
  color: #ffd700;
}

/* 设置卡片 */
.settings-card {
  border-radius: 12px;
  overflow: hidden;
}

.settings-tabs {
  margin-top: 20px;
}

.settings-section {
  margin-bottom: 32px;
  padding: 24px;
  background: #fafbfc;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.settings-section h3 {
  margin: 0 0 20px 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
  padding-bottom: 12px;
  border-bottom: 2px solid #409eff;
}

.settings-section .el-form-item {
  margin-bottom: 20px;
}

.settings-section .el-form-item__label {
  font-weight: 500;
  color: #606266;
}

/* 密钥设置 */
.secret-key-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.form-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

/* 扩展名标签 */
.extension-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

.extension-input {
  width: 120px;
  margin-right: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .system-settings {
    padding: 12px;
  }

  .status-grid {
    grid-template-columns: 1fr;
  }

  .header-actions {
    flex-direction: column;
    gap: 8px;
  }

  .settings-section {
    padding: 16px;
  }
}

/* 标签页样式 */
.settings-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
}

.settings-tabs :deep(.el-tabs__nav-wrap) {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 4px;
}

.settings-tabs :deep(.el-tabs__item) {
  border-radius: 6px;
  transition: all 0.3s ease;
}

.settings-tabs :deep(.el-tabs__item.is-active) {
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 表单样式增强 */
.settings-section .el-input,
.settings-section .el-select,
.settings-section .el-input-number {
  width: 100%;
}

.settings-section .el-switch {
  --el-switch-on-color: #409eff;
}

/* 卡片悬停效果 */
.status-card:hover,
.settings-card:hover {
  transform: translateY(-2px);
  transition: all 0.3s ease;
}

/* 按钮样式 */
.header-actions .el-button {
  border-radius: 6px;
  font-weight: 500;
}

.header-actions .el-button--primary {
  background: linear-gradient(135deg, #409eff 0%, #36a3f7 100%);
  border: none;
}

.header-actions .el-button--primary:hover {
  background: linear-gradient(135deg, #36a3f7 0%, #2b8ce6 100%);
}

/* 系统命令样式 */
.commands-section {
  padding: 0;
}

.system-info-card,
.preset-commands-card,
.custom-commands-card,
.command-result-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.system-info-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.system-info-card h3 {
  margin: 0 0 20px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
}

.system-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.info-item {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
  min-height: 80px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
  cursor: default;
}

.info-item:hover {
  background: #f1f3f4;
  border-color: #dee2e6;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.info-label {
  display: block;
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 8px;
  font-weight: 500;
  color: #909399;
}

.info-value {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  word-wrap: break-word;
  word-break: break-all;
  white-space: pre-wrap;
  line-height: 1.5;
  flex: 1;
  display: flex;
  align-items: center;
}

.help-commands-card h3,
.custom-commands-card h3,
.command-result-card h3 {
  margin: 0 0 20px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  color: #2c3e50;
}

.help-commands-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 16px;
}

.help-command-item {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #17a2b8;
}

.help-info {
  width: 100%;
}

.help-name {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 4px;
}

.help-desc {
  font-size: 14px;
  color: #6c757d;
  margin-bottom: 8px;
}

.help-text {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  color: #495057;
  background: rgba(0, 0, 0, 0.05);
  padding: 8px 12px;
  border-radius: 4px;
  white-space: pre-line;
  line-height: 1.4;
}

.command-info {
  flex: 1;
}

.command-name {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 4px;
}

.command-desc {
  font-size: 14px;
  color: #6c757d;
  margin-bottom: 8px;
}

.command-text {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  color: #495057;
  background: rgba(0, 0, 0, 0.05);
  padding: 4px 8px;
  border-radius: 4px;
}

.command-input-wrapper {
  margin-top: 8px;
}

.command-input {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
}

.command-input .el-input__inner {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
}

.command-actions {
  display: flex;
  gap: 8px;
  margin-left: 16px;
}

.custom-commands-list {
  margin-bottom: 20px;
}

.custom-command-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 6px;
  margin-bottom: 6px;
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.custom-command-item:hover {
  background: #f1f3f4;
  border-color: #dee2e6;
}

.form-help-text {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

/* 用户管理样式 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
}

.user-filters {
  margin-bottom: 20px;
}

.user-table {
  margin-bottom: 20px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.commands-actions {
  display: flex;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #e9ecef;
}

.results-list {
  max-height: 400px;
  overflow-y: auto;
}

.result-item {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  border-left: 4px solid #28a745;
}

.result-item.result-error {
  border-left-color: #dc3545;
  background: #fff5f5;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.result-command {
  font-weight: 600;
  color: #2c3e50;
}

.result-time {
  font-size: 12px;
  color: #6c757d;
}

.result-content {
  background: #2c3e50;
  color: #fff;
  border-radius: 4px;
  padding: 12px;
  overflow-x: auto;
}

.result-content pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .system-info-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .info-item {
    padding: 12px;
    min-height: 70px;
  }

  .info-value {
    font-size: 14px;
  }
}

  .help-commands-grid {
    grid-template-columns: 1fr;
  }

  .custom-command-item {
    flex-wrap: wrap;
    gap: 8px;
  }

  .custom-command-item .el-input {
    min-width: 50px;
    flex: 1;
  }

  .custom-command-item .el-button {
    flex-shrink: 0;
  }

  .result-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

</style>
