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
              <a href="#" @click.prevent="navigateTo('/')">Home</a>
            </li>
            <template v-for="(part, index) in currentPath.split('/').filter(Boolean)" :key="index">
              <li class="breadcrumb-item">
                <a href="#" @click.prevent="navigateTo(currentPath.split('/').slice(0, index + 2).join('/'))">
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
              <th>类型</th>
              <th>上传者</th>
              <th>大小</th>
              <th>修改日期</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="currentPath" class="file-item">
              <td>
                <a href="#" @click.prevent="navigateUp" v-if="currentPath !== '/'">
                  <i class="bi bi-arrow-up-circle"></i> 上一级
                </a>
              </td>
              <td></td>
              <td></td>
              <td></td>
            </tr>
            <!-- 文件列表,没有就显示文件夹为空，显示一个好看的图片 -->
            <tr v-if="filteredItems.length === 0" class="file-item">
              <td colspan="4" class="text-center">
                <img src="/static/img/default-avatar.png" alt="文件夹为空" class="img-fluid">
              </td>
            </tr>
            <tr v-for="item in filteredItems" :key="item.path" class="file-item">
              <td class="text-truncate" style="max-width: 300px" :title="item.filename"> <!-- 文件名，最长显示10个字符，超过的显示省略号 -->
                <a href="#" @click.prevent="handleItemClick(item)">
                  <i :class="getIconClass(item)"></i> {{ item.filename }}
                </a>
              </td>
              <td>{{ item.filetype }}</td>
              <td>{{ item.owner.username }}</td>
              <td>{{ formatSize(item.filesize) }}</td>
              <td>{{ formatDate(item.updated_at) }}</td>
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
  import { getFileList, uploadFile, createDir, deleteDir, deleteFile, downloadFile } from '@/api/files'
  import Toast from '@/utils/toast'
//使用setup
import { ref } from 'vue'
export default {
    name: 'FileManagerView',
    setup() {
        const toast = Toast
        const currentPath = ref('/')
        return {
            toast,
            currentPath
        }
    },
    data() {
      return {
        loading: false,
        // currentPath: '/',
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
    this.loading = true;
    this.toast.info(`获取(${this.currentPath})文件列表中...`);
    const response = await getFileList(this.currentPath);
    console.log('API响应:', response); // 调试用
    
    // 确保response.data存在且是数组
    if (response && response.data) {
      // 检查返回的数据结构
      if (Array.isArray(response.data)) {
        // 如果直接返回数组
        this.items = response.data;
      } else if (response.data.items && Array.isArray(response.data.items)) {
        // 如果返回的是包含items属性的对象
        this.items = response.data.items;
      } else {
        // 其他数据结构情况
        console.warn('意外的数据结构:', response.data);
        this.items = [];
      }
      //对数据进行排序，文件夹在前面，文件在后面
      this.items.sort((a, b) => {
        if (a.filetype === 'directory' && b.filetype !== 'directory') {
          return -1;
        } else if (a.filetype !== 'directory' && b.filetype === 'directory') {
          return 1;
        }
        return 0;
      });
      this.filteredItems = [...this.items];
    } else {
      this.items = [];
      this.filteredItems = [];
    }
  } catch (error) {
    console.error('获取文件列表失败', error);
    this.items = [];
    this.filteredItems = [];
    // 可以添加用户通知
    this.toast?.error('获取文件列表失败，请稍后重试');
  } finally {
    this.loading = false;
  }
},
      
      navigateTo(path) {
        this.currentPath = path
  this.fetchFiles()
},

navigateUp() {
  const parts = this.currentPath.split('/').filter(Boolean)
  if (parts.length > 0) {
    parts.pop()
    this.currentPath = parts.length ? `/${parts.join('/')}` : '/'
    this.fetchFiles()
  }
},

      
      handleItemClick(item) {
        if (item.filetype == 'directory') {
          this.navigateTo(item.path)
        } else {
          this.downloadItem(item)
        }
      },
      
      
      
      async downloadItem(item) {
        try {
          console.log(item,'item')
          const response = await downloadFile(item.id,item.filepath)
          
          const url = window.URL.createObjectURL(new Blob([response.data]))
          const link = document.createElement('a')
          link.href = url
          
          link.setAttribute('download', item.filename)
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
        } catch (error) {
          console.error('下载文件失败', error)
        }
      },
      
      // 修改 deleteItem 方法
async deleteItem(item) {
  if (!confirm(`确定要删除 ${item.filename} 吗？`)) {
    return
  }
  
  try {
    if (item.filetype == 'directory') {
      await deleteDir(item.path)
    } else {
      await deleteFile(item.id,item.filepath)
    }
    this.toast.success('删除成功')
    this.fetchFiles()
  } catch (error) {
    console.error('删除失败', error)
    this.toast?.error(`删除失败: ${error.response?.data?.detail || error.message}`)
  }
},
      
      // 修改 createFolder 方法
async createFolder() {
  const folderName = prompt('请输入文件夹名称:')
  if (!folderName) return
  // 如果文件夹名称包含/，则提示错误 空格
  if (folderName.includes('\\') || folderName.includes(':') || folderName.includes('*') || folderName.includes('?') || folderName.includes('"') || folderName.includes('<') || folderName.includes('>') || folderName.includes('|') || folderName.includes(' ')) {
    this.toast?.error('文件夹名称不能包含\\:*?"<>|空格')
    return
  }
  try {
    
    

    await createDir(this.currentPath,folderName)
    
    this.toast.success('文件夹创建成功')
    this.fetchFiles()
  } catch (error) {
    console.error('创建文件夹失败', error)
    this.toast?.error(`创建失败: ${error.response?.data?.detail || error.message}`)
  }
},

      
      handleFileSelect(event) {
        this.selectedFiles = Array.from(event.target.files)
      },
      
      // 在 methods 中添加路径处理方法

// 修改 uploadFiles 方法
async uploadFiles() {
  if (!this.selectedFiles.length) return
  
  try {
    this.uploadProgress = 10 // 开始上传
    
    const formData = new FormData()
    this.selectedFiles.forEach(file => {
      formData.append('files', file)
    })
    
    // 规范化当前路径
    const normalizedPath = this.currentPath
    
    // 显示上传进度
    const config = {
      onUploadProgress: progressEvent => {
        this.uploadProgress = Math.round(
          (progressEvent.loaded * 90) / progressEvent.total
        )
      }
    }
    
    await uploadFile(formData, normalizedPath, config)
    this.uploadProgress = 100
    
    this.toast.success('文件上传成功')
    this.showUploadModal = false
    this.selectedFiles = []
    this.uploadProgress = 0
    this.fetchFiles()
  } catch (error) {
    console.error('上传文件失败', error)
    this.toast?.error(`上传失败: ${error.response?.data?.detail || error.message}`)
    this.uploadProgress = 0
  }
},

      
      searchFiles() {
        if (!this.searchQuery) {
          this.filteredItems = [...this.items]
          return
        }
        
        const query = this.searchQuery.toLowerCase()
        this.filteredItems = this.items.filter(item => 
          item.filename.toLowerCase().includes(query)
        )
      },
      
      getIconClass(item) {
        if (item.filetype == 'directory') {
          return 'bi bi-folder'
        }
        const extension = item.filename.split('.').pop().toLowerCase()
        
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
  .progress-bar {
  transition: width 0.3s ease;
}
  </style>