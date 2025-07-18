<template>
  <div class="qrfile-manage-container">
    <div class="page-header">
      <h1>二维码文件管理</h1>
      <p class="subtitle">管理您生成的二维码文件，避免服务器存储空间无限增长</p>
    </div>

    <div class="main-content">
      <!-- 统计信息卡片 -->
      <div class="stats-cards">
        <el-card class="stats-card">
          <template #header>
            <div class="card-header">
              <span>文件数量</span>
            </div>
          </template>
          <div class="stats-value">{{ stats.fileCount || 0 }}</div>
        </el-card>

        <el-card class="stats-card">
          <template #header>
            <div class="card-header">
              <span>存储空间</span>
            </div>
          </template>
          <div class="stats-value">{{ stats.totalSizeHuman || '0 B' }}</div>
        </el-card>

        <el-card v-if="isAdmin" class="stats-card">
          <template #header>
            <div class="card-header">
              <span>用户数</span>
            </div>
          </template>
          <div class="stats-value">{{ stats.userCount || 0 }}</div>
        </el-card>

        <el-card v-if="isAdmin" class="stats-card">
          <template #header>
            <div class="card-header">
              <span>已删除文件</span>
            </div>
          </template>
          <div class="stats-value">{{ stats.deletedCount || 0 }}</div>
        </el-card>
      </div>

      <!-- 操作按钮 -->
      <div class="action-bar">
        <el-button type="primary" @click="refreshFiles">
          <i class="fas fa-sync-alt"></i> 刷新
        </el-button>

        <el-button v-if="isAdmin" type="warning" @click="showCleanDialog = true">
          <i class="fas fa-broom"></i> 清理旧文件
        </el-button>
      </div>

      <!-- 文件列表 -->
      <el-card class="file-list-card">
        <template #header>
          <div class="card-header">
            <span>二维码文件列表</span>
          </div>
        </template>

        <el-table v-loading="loading" :data="files" style="width: 100%" empty-text="暂无二维码文件">
          <el-table-column prop="original_filename" label="原始文件名" min-width="180">
            <template #default="scope">
              <el-tooltip :content="scope.row.original_filename" placement="top">
                <span>{{ scope.row.original_filename || '未命名文件' }}</span>
              </el-tooltip>
            </template>
          </el-table-column>

          <el-table-column prop="mode" label="模式" width="120">
            <template #default="scope">
              <el-tag :type="scope.row.mode === 'region' ? 'success' : 'primary'">
                {{ scope.row.mode === 'region' ? 'Excel区域' : '文件' }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="chunk_count" label="二维码数量" width="120">
            <template #default="scope">
              <el-tag v-if="scope.row.chunk_count > 0" type="info">
                {{ scope.row.chunk_count }}
              </el-tag>
              <el-tag v-else-if="scope.row.has_qr_codes" type="info">有</el-tag>
              <el-tag v-else type="danger">无</el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="scope">
              {{ formatDate(scope.row.created_at) }}
            </template>
          </el-table-column>

          <el-table-column label="操作" width="200" fixed="right">
            <template #default="scope">
              <el-button size="small" type="danger" @click="confirmDelete(scope.row)">
                删除
              </el-button>

              <el-button
                v-if="scope.row.has_qr_codes"
                size="small"
                type="primary"
                @click="viewQRCodes(scope.row)"
              >
                查看二维码
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            :total="total"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 清理旧文件对话框 -->
    <el-dialog v-model="showCleanDialog" title="清理旧文件" width="400px">
      <div class="clean-dialog-content">
        <p>此操作将删除指定天数前创建的所有二维码文件，无法恢复。</p>

        <el-form>
          <el-form-item label="保留天数">
            <el-input-number v-model="cleanDays" :min="1" :max="365" :step="1" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCleanDialog = false">取消</el-button>
          <el-button type="danger" @click="cleanFiles" :loading="cleanLoading">
            确认清理
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 查看二维码对话框 -->
    <el-dialog v-model="showQRDialog" title="查看二维码" width="600px">
      <div v-if="currentFile" class="qr-dialog-content">
        <div class="qr-info">
          <p><strong>文件名:</strong> {{ currentFile.original_filename }}</p>
          <p><strong>创建时间:</strong> {{ formatDate(currentFile.created_at) }}</p>
          <p><strong>二维码数量:</strong> {{ currentFile.chunk_count }}</p>
        </div>

        <div class="qr-images">
          <p>请前往二维码文件工具页面，使用会话ID查看二维码：</p>
          <el-input v-model="currentFile.session_id" readonly>
            <template #append>
              <el-button @click="copySessionId">复制</el-button>
            </template>
          </el-input>

          <div class="qr-action">
            <el-button type="primary" @click="goToQRFileTool"> 前往二维码工具 </el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getQRFiles, deleteQRFile, getFileStats, cleanOldFiles } from '@/api/qrfile'
import { useUserStore } from '@/stores/user'
import Toast from '@/utils/toast'
import { ElMessageBox } from 'element-plus'
import { copyText } from '@/utils/utils.js'
export default {
  name: 'QRFileManageView',
  setup() {
    // 路由
    const router = useRouter()

    // 用户信息
    const userStore = useUserStore()
    const isAdmin = ref(userStore.isAdmin)

    // 文件列表状态
    const files = ref([])
    const loading = ref(false)
    const currentPage = ref(1)
    const pageSize = ref(10)
    const total = ref(0)

    // 统计信息
    const stats = reactive({
      fileCount: 0,
      totalSize: 0,
      totalSizeHuman: '0 B',
      userCount: 0,
      deletedCount: 0,
    })

    // 清理旧文件
    const showCleanDialog = ref(false)
    const cleanDays = ref(30)
    const cleanLoading = ref(false)

    // 查看二维码
    const showQRDialog = ref(false)
    const currentFile = ref(null)

    // 加载文件列表
    const loadFiles = async () => {
      try {
        loading.value = true
        const skip = (currentPage.value - 1) * pageSize.value
        const response = await getQRFiles(skip, pageSize.value)

        if (response.data && response.data.success) {
          files.value = response.data.files
          total.value = response.data.total
        } else {
          Toast.error('加载文件列表失败')
        }
      } catch (err) {
        console.error('加载文件列表失败', err)
        Toast.error(`加载文件列表失败: ${err.response?.data?.detail || err.message}`)
      } finally {
        loading.value = false
      }
    }

    // 加载统计信息
    const loadStats = async () => {
      try {
        const response = await getFileStats()

        if (response.data && response.data.success) {
          stats.fileCount = response.data.file_count
          stats.totalSize = response.data.total_size
          stats.totalSizeHuman = response.data.total_size_human

          if (isAdmin.value) {
            stats.userCount = response.data.user_count
            stats.deletedCount = response.data.deleted_count
          }
        }
      } catch (err) {
        console.error('加载统计信息失败', err)
        Toast.error(`加载统计信息失败: ${err.response?.data?.detail || err.message}`)
      }
    }

    // 刷新文件列表
    const refreshFiles = async () => {
      await loadFiles()
      await loadStats()
    }

    // 分页处理
    const handleSizeChange = (size) => {
      pageSize.value = size
      loadFiles()
    }

    const handleCurrentChange = (page) => {
      currentPage.value = page
      loadFiles()
    }

    // 确认删除文件
    const confirmDelete = (file) => {
      ElMessageBox.confirm(
        `确定要删除文件 "${file.original_filename || '未命名文件'}" 吗？此操作不可恢复。`,
        '删除确认',
        {
          confirmButtonText: '删除',
          cancelButtonText: '取消',
          type: 'warning',
        },
      )
        .then(() => {
          deleteFile(file.id)
        })
        .catch(() => {})
    }

    // 删除文件
    const deleteFile = async (fileId) => {
      try {
        const response = await deleteQRFile(fileId)

        if (response.data && response.data.success) {
          Toast.success('文件已成功删除')
          refreshFiles()
        } else {
          Toast.error('删除文件失败')
        }
      } catch (err) {
        console.error('删除文件失败', err)
        Toast.error(`删除文件失败: ${err.response?.data?.detail || err.message}`)
      }
    }

    // 清理旧文件
    const cleanFiles = async () => {
      try {
        cleanLoading.value = true
        const response = await cleanOldFiles(cleanDays.value)

        if (response.data && response.data.success) {
          Toast.success(response.data.message)
          showCleanDialog.value = false
          refreshFiles()
        } else {
          Toast.error('清理旧文件失败')
        }
      } catch (err) {
        console.error('清理旧文件失败', err)
        Toast.error(`清理旧文件失败: ${err.response?.data?.detail || err.message}`)
      } finally {
        cleanLoading.value = false
      }
    }

    // 查看二维码
    const viewQRCodes = (file) => {
      currentFile.value = file
      showQRDialog.value = true
    }

    // 复制会话ID
    const copySessionId = () => {
      if (!currentFile.value) return

      const sessionId = currentFile.value.session_id
      copyText(sessionId)
      // navigator.clipboard
      //   .writeText(sessionId)
      //   .then(() => Toast.success('会话ID已复制到剪贴板'))
      //   .catch(() => Toast.error('复制失败，请手动复制'))
    }

    // 前往二维码工具
    const goToQRFileTool = () => {
      showQRDialog.value = false
      router.push('/qrfile')
    }

    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return ''

      const date = new Date(dateString)
      return date.toLocaleString()
    }

    // 组件挂载时加载数据
    onMounted(() => {
      refreshFiles()
    })

    return {
      // 状态
      files,
      loading,
      currentPage,
      pageSize,
      total,
      stats,
      isAdmin,
      showCleanDialog,
      cleanDays,
      cleanLoading,
      showQRDialog,
      currentFile,

      // 方法
      loadFiles,
      loadStats,
      refreshFiles,
      handleSizeChange,
      handleCurrentChange,
      confirmDelete,
      deleteFile,
      cleanFiles,
      viewQRCodes,
      copySessionId,
      goToQRFileTool,
      formatDate,
    }
  },
}
</script>

<style scoped>
.qrfile-manage-container {
  width: 100%;
  padding: 20px;
  height: 100%;
}

.page-header {
  margin-bottom: 20px;
  text-align: center;
}

.page-header h1 {
  font-size: 28px;
  color: #333;
  margin-bottom: 5px;
}

.subtitle {
  font-size: 16px;
  color: #666;
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-cards {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.stats-card {
  flex: 1;
  min-width: 200px;
}

.stats-value {
  font-size: 24px;
  font-weight: bold;
  text-align: center;
  padding: 10px 0;
}

.action-bar {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.file-list-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.clean-dialog-content {
  margin-bottom: 20px;
}

.qr-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.qr-info {
  margin-bottom: 10px;
}

.qr-images {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.qr-action {
  margin-top: 20px;
  text-align: center;
}

@media (max-width: 768px) {
  .stats-card {
    min-width: 100%;
  }
}
</style>