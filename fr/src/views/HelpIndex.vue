<template>
  <div class="help-container">
    <div class="page-header">
      <h1>示例和文档</h1>
      <p>浏览和查看帮助文档和示例代码</p>
    </div>

    <div class="example-filter">
      <h5>帮助说明</h5>
      <p>这里提供了系统的使用手册、开发指南和示例代码，帮助您了解和使用扩展数据查询系统。</p>
      <ul>
        <li><strong>文档</strong> - 开发指南和使用说明，包括如何开发安全的扩展、处理文件上传、参数配置等</li>
        <li><strong>示例扩展</strong> - 可以参考的扩展代码示例，展示了如何实现各种功能</li>
        <li><strong>示例页面</strong> - HTML演示页面，展示了如何设计前端界面</li>
      </ul>
    </div>
    <div v-if="examples.length > 0" class="table-responsive">
      <div class="card">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h5 class="mb-0">示例文件列表</h5>
          <div class="d-flex gap-2">
            <button class="btn btn-sm btn-outline-secondary" @click="refreshExtensions">
              <i class="fas fa-sync-alt"></i> 刷新
            </button>
            <button class="btn btn-sm btn-outline-secondary" @click="openUploadModal">
              <i class="fas fa-upload"></i> 上传
            </button>
          </div>
        </div>
        <div class="card-body">
          <table class="example-table">
            <thead>
              <tr>
                <th>文件名</th>
                <th>类型</th>
                <th>大小</th>
                <th>修改时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="example in examples" :key="example.filename">
                <td>
                  <i class="file-icon fas" :class="example.icon_class"></i>
                  {{ example.filename }}
                </td>
                <td>
                  <span class="file-type" :class="getFileTypeClass(example.type)">
                    {{ example.type }}
                  </span>
                </td>
                <td>{{ example.size_formatted }}</td>
                <td>{{ example.modified_time }}</td>
                <td>
                  <a :href="`/help/${example.filename}`" class="btn btn-sm btn-primary" target="_blank">
                    <i class="fas fa-eye"></i> 查看
                  </a>&ensp;
                  <a href="javascript:void(0)" class="btn btn-sm btn-success" @click="downloadFile(example.filename)">
                    <i class="fas fa-download"></i> 下载
                  </a>&ensp;
                  <a href="javascript:void(0)" class="btn btn-sm btn-danger" @click="deleteFile(example.filename)">
                    <i class="fas fa-trash"></i> 删除
                  </a>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-else class="example-empty">
      <i class="fas fa-folder-open fa-3x mb-3"></i>
      <h3>暂无文件</h3>
      <p>当前没有可用的示例或文档。</p>
      <button class="btn btn-primary" @click="openUploadModal">上传新文件</button>
    </div>

    <!-- Upload Modal -->
    <div class="modal fade" id="uploadModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">上传新示例文件</h5>
          </div>
          <div class="modal-body">
            <form id="uploadForm" enctype="multipart/form-data" @submit.prevent="uploadFile">
              <div class="mb-3">
                <label for="files" class="form-label">选择文件</label>
                <input type="file" class="form-control" id="files" name="files" multiple>
              </div>
              <button type="submit" class="btn btn-primary">上传</button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getFileList, uploadFileAPI, deleteFile, downloadFileApi } from '@/api/help';
import Toast from '@/utils/toast';
export default {
  name: 'ExampleList',
  data() {
    return {
      examples: [],
      uploadModal: null
    };
  },
  mounted() {
    this.loadExamples();
    this.uploadModal = new bootstrap.Modal(document.getElementById('uploadModal'));
  },
  methods: {
    loadExamples() {
      getFileList()
        .then(response => {
          this.examples = response.data.files || [];
          Toast.success('列表已刷新');
        })
        .catch(error => {
          Toast.error(error.response?.data?.detail || '列表刷新失败');
        });
    },
    getFileTypeClass(type) {
      switch(type) {
        case '文档': return 'file-type-doc';
        case '示例扩展': return 'file-type-extension';
        case '示例页面': return 'file-type-page';
        default: return 'file-type-other';
      }
    },
    refreshExtensions() {
      this.loadExamples();
    },
    openUploadModal() {
      this.uploadModal.show();
    },
    uploadFile() {
      const files = document.getElementById('files').files;
      const formData = new FormData();
      
      for (let i = 0; i < files.length; i++) {
        formData.append(`files[${i}]`, files[i]);
      }
        console.log([...formData.entries()]);

      if (files.length === 0) {
        Toast.error("请选择文件");
        return;
      }
      
      uploadFileAPI(formData)
        .then(response => {
          Toast.success(response.data.detail);
          this.uploadModal.hide();
          if (response.data.success_files?.length > 0) {
            Toast.success(`成功上传的文件：${response.data.success_files.join(',')}`);
          }
          if (response.data.failed_files?.length > 0) {
            Toast.error(`失败的上传的文件：${response.data.failed_files.join(',')}`);
          }
          this.loadExamples();
        })
        .catch(error => {
          Toast.error(error.response?.data?.detail || '上传失败');
        });
    },
    deleteFile(filename) {
      if (confirm(`确定删除该文件吗？\n${filename}`)) {
        deleteFile(filename)
          .then(response => {
            Toast.success(response.data.detail);
            this.loadExamples();
          })
          .catch(error => {
            Toast.error(error.response?.data?.detail || '删除失败');
          });
      }
    },
    downloadFile(filename) {
      const a = document.createElement('a');
      a.href = downloadFileApi(filename);
      a.download = filename;
      a.click();
      Toast.success('下载成功');
    }
  }
};
</script>

<style scoped>
.help-container {
  padding: 20px;
  width: 100%;
}

.page-header {
  margin-bottom: 20px;
}
.example-filter {
  margin-bottom: 20px;
  padding: 15px;
  background-color: var(--secondary-color);
  border-radius: 8px;
}

.example-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
}

.example-table th, .example-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.example-table th {
  background-color: var(--secondary-color);
  color: var(--text-color);
  font-weight: bold;
}

.example-table tr:hover {
  background-color: #f5f5f5;
}

.file-icon {
  margin-right: 8px;
  width: 20px;
  text-align: center;
}

.example-empty {
  text-align: center;
  padding: 40px;
  color: #888;
}

.file-type {
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  display: inline-block;
}

.file-type-doc {
  background-color: #e3f2fd;
  color: #0d47a1;
}

.file-type-extension {
  background-color: #e8f5e9;
  color: #1b5e20;
}

.file-type-page {
  background-color: #fff3e0;
  color: #e65100;
}

.file-type-other {
  background-color: #f5f5f5;
  color: #616161;
}
</style>