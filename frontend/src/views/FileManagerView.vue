<template>
    <div class="file-manager">
      <h1>文件管理</h1>
      
      <div class="actions mb-4">
        <button class="btn btn-primary me-2" @click="showUploadModal = true">
          <i class="bi bi-upload"></i> 上传文件
        </button>
        <button class="btn btn-secondary me-2" @click="createFolder">
          <i class="bi bi-folder-plus"></i> 新建文件夹
        </button>
        <div class="search-box">
          <input 
            type="text" 
            class="form-control" 
            placeholder="搜索文件..." 
            v-model="searchQuery"
            @input="searchFiles"
          />
        </div>
      </div>
      
      <div class="breadcrumb-container mb-3">
        <nav aria-label="breadcrumb">
          <ol class="breadcrumb">
            <li class="breadcrumb-item">
              <a href="#" @click.prevent="navigateTo('')">根目录</a>
            </li>
            <template v-for="(part, index) in currentPath.split('/').filter(Boolean)" :key="index">
              <li class="breadcrumb-item">
                <a href="#" @click.prevent="navigateTo(currentPath.split('/').slice(0, index + 1).join('/'))">
                  {{ part }}
                </a>
              </li>
            </template>
          </ol>
        </nav>
      </div>
      
      <div class="file-list">
        <table class="table">
          <thead>
            <tr>
              <th>名称</th>
              <th>大小</th>
              <th>修改日期</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="currentPath" class="file-item">
              <td>
                <a href="#" @click.prevent="navigateUp">
                  <i class="bi bi-arrow-up-circle"></i> 上一级
                </a>
              </td>
              <td></td>
              <td></td>
              <td></td>
            </tr>
            <tr v-for="item in filteredItems" :key="item.path" class="file-item">
              <td>
                <a href="#" @click.prevent="handleItemClick(item)">
                  <i :class="getIconClass(item)"></i> {{ item.name }}
                </a>
              </td>
              <td>{{ formatSize(item.size) }}</td>
              <td>{{ formatDate(item.modified) }}</td>
              <td>
                <div class="btn-group">
                  <button class="btn btn-sm btn-outline-secondary" @click="downloadItem(item)" v-if="!item.is_dir">
                    <i class="bi bi-download"></i>
                  </button>
                  <button class="btn btn-sm btn-outline-danger" @click="deleteItem(item)">
                    <i class="bi bi-trash"></i>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- 上传文件模态框 -->
      <div class="modal" v-if="showUploadModal">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">上传文件</h5>
              <button type="button" class="btn-close" @click="showUploadModal = false"></button>
            </div>
            <div class="modal-body">
              <div class="mb-3">
                <label for="fileInput" class="form-label">选择文件</label>
                <input 
                  type="file" 
                  id="fileInput" 
                  class="form-control" 
                  @change="handleFileSelect" 
                  multiple
                />
              </div>
              <div class="upload-progress" v-if="uploadProgress > 0">
                <div class="progress">
                  <div 
                    class="progress-bar" 
                    role="progressbar" 
                    :style="{ width: uploadProgress + '%' }" 
                    :aria-valuenow="uploadProgress" 
                    aria-valuemin="0" 
                    aria-valuemax="100"
                  >
                    {{ uploadProgress }}%
                  </div>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="showUploadModal = false">取消</button>
              <button type="button" class="btn btn-primary" @click="uploadFiles" :disabled="!selectedFiles.length">
                上传
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import axios from '@/utils/axios'
  
  export default {
    name: 'FileManagerView',
    data() {
      return {
        currentPath: '',
        items: [],
        searchQuery: '',
        filteredItems: [],
        showUploadModal: false,
        selectedFiles: [],
        uploadProgress: 0
      }
    },
    created() {
      this.fetchFiles()
    },
    methods: {
      async fetchFiles() {
        try {
          const response = await axios.get(`/api/files/?path=${encodeURIComponent(this.currentPath)}`)
          this.items = response.data.items
          this.filteredItems = [...this.items]
        } catch (error) {
          console.error('获取文件列表失败', error)
        }
      },
      
      navigateTo(path) {
        this.currentPath = path
        this.fetchFiles()
      },
      
      navigateUp() {
        const parts = this.currentPath.split('/').filter(Boolean)
        parts.pop()
        this.currentPath = parts.join('/')
        this.fetchFiles()
      },
      
      handleItemClick(item) {
        if (item.is_dir) {
          this.navigateTo(item.path)
        } else {
          this.previewFile(item)
        }
      },
      
      previewFile(item) {
        window.open(`/api/files/download?path=${encodeURIComponent(item.path)}`, '_blank')
      },
      
      async downloadItem(item) {
        try {
          const response = await axios.get(`/api/files/download?path=${encodeURIComponent(item.path)}`, {
            responseType: 'blob'
          })
          
          const url = window.URL.createObjectURL(new Blob([response.data]))
          const link = document.createElement('a')
          link.href = url
          link.setAttribute('download', item.name)
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
        } catch (error) {
          console.error('下载文件失败', error)
        }
      },
      
      async deleteItem(item) {
        if (!confirm(`确定要删除 ${item.name} 吗？`)) {
          return
        }
        
        try {
          await axios.delete(`/api/files/delete?path=${encodeURIComponent(item.path)}`)
          this.fetchFiles()
        } catch (error) {
          console.error('删除文件失败', error)
        }
      },
      
      async createFolder() {
        const folderName = prompt('请输入文件夹名称:')
        if (!folderName) return
        
        try {
          await axios.post('/api/files/create_folder', {
            path: this.currentPath,
            name: folderName
          })
          this.fetchFiles()
        } catch (error) {
          console.error('创建文件夹失败', error)
        }
      },
      
      handleFileSelect(event) {
        this.selectedFiles = Array.from(event.target.files)
      },
      
      async uploadFiles() {
        if (!this.selectedFiles.length) return
        
        const formData = new FormData()
        this.selectedFiles.forEach(file => {
          formData.append('files', file)
        })
        formData.append('path', this.currentPath)
        
        try {
          await axios.post('/api/files/upload', formData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            },
            onUploadProgress: (progressEvent) => {
              this.uploadProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            }
          })
          
          this.showUploadModal = false
          this.selectedFiles = []
          this.uploadProgress = 0
          this.fetchFiles()
        } catch (error) {
          console.error('上传文件失败', error)
        }
      },
      
      searchFiles() {
        if (!this.searchQuery) {
          this.filteredItems = [...this.items]
          return
        }
        
        const query = this.searchQuery.toLowerCase()
        this.filteredItems = this.items.filter(item => 
          item.name.toLowerCase().includes(query)
        )
      },
      
      getIconClass(item) {
        if (item.is_dir) {
          return 'bi bi-folder'
        }
        
        const extension = item.name.split('.').pop().toLowerCase()
        
        switch (extension) {
          case 'pdf':
            return 'bi bi-file-earmark-pdf'
          case 'doc':
          case 'docx':
            return 'bi bi-file-earmark-word'
          case 'xls':
          case 'xlsx':
            return 'bi bi-file-earmark-excel'
          case 'ppt':
          case 'pptx':
            return 'bi bi-file-earmark-ppt'
          case 'jpg':
          case 'jpeg':
          case 'png':
          case 'gif':
            return 'bi bi-file-earmark-image'
          case 'mp3':
          case 'wav':
            return 'bi bi-file-earmark-music'
          case 'mp4':
          case 'avi':
          case 'mov':
            return 'bi bi-file-earmark-play'
          case 'zip':
          case 'rar':
          case '7z':
            return 'bi bi-file-earmark-zip'
          case 'txt':
            return 'bi bi-file-earmark-text'
          default:
            return 'bi bi-file-earmark'
        }
      },
      
      formatSize(bytes) {
        if (!bytes) return '-'
        
        const units = ['B', 'KB', 'MB', 'GB', 'TB']
        let size = bytes
        let unitIndex = 0
        
        while (size >= 1024 && unitIndex < units.length - 1) {
          size /= 1024
          unitIndex++
        }
        
        return `${size.toFixed(1)} ${units[unitIndex]}`
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
  .file-manager {
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
  
  .actions {
    display: flex;
    align-items: center;
    margin-bottom: 1.5rem;
  }
  
  .search-box {
    flex: 1;
    max-width: 300px;
    margin-left: auto;
  }
  
  .file-list {
    display: flex;
    border-radius: 4px;
    overflow: hidden;
  }
  
  .file-item td {
    vertical-align: middle;
  }
  
  .file-item a {
    display: flex;
    align-items: center;
    color: #2c3e50;
    text-decoration: none;
  }
  
  .file-item a:hover {
    color: #3498db;
  }
  
  .file-item i {
    margin-right: 0.5rem;
    font-size: 1.25rem;
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
  
  .upload-progress {
    margin-top: 1rem;
  }
  
  .progress {
    height: 10px;
    border-radius: 5px;
    overflow: hidden;
  }
  </style>