<template>
  <div class="extension-detail">
    <div class="header">
      <h1>{{ extension.name || '扩展详情' }}</h1>
      <div class="actions">
        <v-btn
          v-if="extension.enabled"
          color="error"
          @click="toggleExtension(false)"
          :loading="loading"
        >
          禁用
        </v-btn>
        <v-btn
          v-else
          color="success"
          @click="toggleExtension(true)"
          :loading="loading"
        >
          启用
        </v-btn>
        <v-btn color="primary" @click="runExtension" :loading="loading" :disabled="!extension.enabled">
          运行
        </v-btn>
        <v-btn color="warning" @click="showEditDialog" :loading="loading">
          编辑
        </v-btn>
        <v-btn color="error" @click="showDeleteDialog" :loading="loading">
          删除
        </v-btn>
      </div>
    </div>

    <v-card class="mt-4">
      <v-card-title>基本信息</v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="6">
            <div class="info-item">
              <div class="label">ID:</div>
              <div class="value">{{ extension.id }}</div>
            </div>
          </v-col>
          <v-col cols="12" md="6">
            <div class="info-item">
              <div class="label">状态:</div>
              <div class="value">
                <v-chip
                  :color="extension.enabled ? 'success' : 'error'"
                  text-color="white"
                  small
                >
                  {{ extension.enabled ? '已启用' : '已禁用' }}
                </v-chip>
              </div>
            </div>
          </v-col>
          <v-col cols="12" md="6">
            <div class="info-item">
              <div class="label">版本:</div>
              <div class="value">{{ extension.version }}</div>
            </div>
          </v-col>
          <v-col cols="12" md="6">
            <div class="info-item">
              <div class="label">创建者:</div>
              <div class="value">{{ extension.creator?.username || '未知' }}</div>
            </div>
          </v-col>
          <v-col cols="12">
            <div class="info-item">
              <div class="label">描述:</div>
              <div class="value description">{{ extension.description || '无描述' }}</div>
            </div>
          </v-col>
          <v-col cols="12">
            <div class="info-item">
              <div class="label">入口点:</div>
              <div class="value">{{ extension.entry_point }}</div>
            </div>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-card class="mt-4">
      <v-card-title>配置信息</v-card-title>
      <v-card-text>
        <pre v-if="extension.config">{{ formatConfig(extension.config) }}</pre>
        <p v-else>无配置信息</p>
      </v-card-text>
    </v-card>

    <v-card class="mt-4" v-if="extension.requirements">
      <v-card-title>依赖项</v-card-title>
      <v-card-text>
        <pre>{{ extension.requirements }}</pre>
      </v-card-text>
    </v-card>

    <!-- 编辑扩展对话框 -->
    <v-dialog v-model="editDialog" max-width="600px">
      <v-card>
        <v-card-title>编辑扩展</v-card-title>
        <v-card-text>
          <v-form ref="form" v-model="valid">
            <v-text-field
              v-model="editForm.name"
              label="名称"
              required
              :rules="[v => !!v || '名称不能为空']"
            ></v-text-field>
            <v-text-field
              v-model="editForm.version"
              label="版本"
              required
              :rules="[v => !!v || '版本不能为空']"
            ></v-text-field>
            <v-textarea
              v-model="editForm.description"
              label="描述"
              rows="3"
            ></v-textarea>
            <v-switch
              v-model="editForm.enabled"
              label="启用"
              color="success"
            ></v-switch>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="blue darken-1" text @click="editDialog = false">取消</v-btn>
          <v-btn color="blue darken-1" text @click="updateExtension" :disabled="!valid" :loading="loading">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除确认对话框 -->
    <v-dialog v-model="deleteDialog" max-width="400px">
      <v-card>
        <v-card-title class="headline">确认删除</v-card-title>
        <v-card-text>
          确定要删除扩展 <strong>{{ extension.name }}</strong> 吗？此操作不可逆。
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="blue darken-1" text @click="deleteDialog = false">取消</v-btn>
          <v-btn color="red darken-1" text @click="deleteExtension" :loading="loading">删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 运行结果对话框 -->
    <v-dialog v-model="resultDialog" max-width="800px">
      <v-card>
        <v-card-title>运行结果</v-card-title>
        <v-card-text>
          <pre>{{ JSON.stringify(runResult, null, 2) }}</pre>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" text @click="resultDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import axios from '@/utils/axios'

export default {
  name: 'ExtensionDetail',
  data() {
    return {
      extension: {},
      loading: false,
      editDialog: false,
      deleteDialog: false,
      resultDialog: false,
      valid: true,
      runResult: null,
      editForm: {
        name: '',
        version: '',
        description: '',
        enabled: false
      }
    }
  },
  async created() {
    await this.fetchExtensionDetail()
  },
  methods: {
    async fetchExtensionDetail() {
      try {
        this.loading = true
        const response = await axios.get(`/api/v1/extensions/${this.$route.params.id}`)
        this.extension = response.data
        this.loading = false
      } catch (error) {
        console.error('获取扩展详情失败', error)
        this.$toast.error('获取扩展详情失败')
        this.loading = false
      }
    },
    showEditDialog() {
      this.editForm = {
        name: this.extension.name,
        version: this.extension.version,
        description: this.extension.description,
        enabled: this.extension.enabled
      }
      this.editDialog = true
    },
    showDeleteDialog() {
      this.deleteDialog = true
    },
    async updateExtension() {
      try {
        this.loading = true
        await axios.put(`/api/v1/extensions/${this.extension.id}`, this.editForm)
        this.$toast.success('更新成功')
        this.editDialog = false
        await this.fetchExtensionDetail()
      } catch (error) {
        console.error('更新扩展失败', error)
        this.$toast.error('更新扩展失败')
      } finally {
        this.loading = false
      }
    },
    async deleteExtension() {
      try {
        this.loading = true
        await axios.delete(`/api/v1/extensions/${this.extension.id}`)
        this.$toast.success('删除成功')
        this.deleteDialog = false
        this.$router.push('/extensions')
      } catch (error) {
        console.error('删除扩展失败', error)
        this.$toast.error('删除扩展失败')
      } finally {
        this.loading = false
      }
    },
    async toggleExtension(enabled) {
      try {
        this.loading = true
        await axios.put(`/api/v1/extensions/${this.extension.id}`, {
          enabled
        })
        this.$toast.success(`${enabled ? '启用' : '禁用'}成功`)
        await this.fetchExtensionDetail()
      } catch (error) {
        console.error(`${enabled ? '启用' : '禁用'}扩展失败`, error)
        this.$toast.error(`${enabled ? '启用' : '禁用'}扩展失败`)
      } finally {
        this.loading = false
      }
    },
    async runExtension() {
      try {
        this.loading = true
        const response = await axios.post(`/api/v1/extensions/${this.extension.id}/run`)
        this.runResult = response.data.result
        this.resultDialog = true
      } catch (error) {
        console.error('运行扩展失败', error)
        this.$toast.error('运行扩展失败')
      } finally {
        this.loading = false
      }
    },
    formatConfig(config) {
      try {
        if (typeof config === 'string') {
          return JSON.stringify(JSON.parse(config), null, 2)
        } else {
          return JSON.stringify(config, null, 2)
        }
      } catch (e) {
        return config
      }
    }
  }
}
</script>

<style scoped>
.extension-detail {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.actions {
  display: flex;
  gap: 10px;
}

.info-item {
  margin-bottom: 15px;
  display: flex;
}

.label {
  font-weight: bold;
  width: 100px;
  flex-shrink: 0;
}

.value {
  flex-grow: 1;
}

.description {
  white-space: pre-line;
}

pre {
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
}
</style> 