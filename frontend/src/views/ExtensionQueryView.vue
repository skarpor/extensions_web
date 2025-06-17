<template>
    <div class="extension-query">
      <div class="cyber-header-main">
        <h1><i class="fas fa-plug"></i> 扩展接口查询系统</h1>
        <div class="cyber-line-main"></div>
      </div>
      
      <div id="extensionsList" class="cyber-extensions-list">
        <!-- 加载状态 -->
        <div v-if="loading" class="text-center py-4">
          <div class="cyber-spinner"></div>
          <p>加载扩展列表中...</p>
        </div>
        
        <!-- 无扩展提示 -->
        <div v-else-if="extensions.length === 0" class="cyber-alert info">
          <i class="fas fa-info-circle"></i> 当前没有可用的扩展
        </div>
        
        <!-- 扩展列表 -->
        <div v-else>
          <div v-for="ext in extensions" :key="ext.id" class="cyber-extension-item">
            <div class="cyber-extension-header">
              <h3>{{ ext.name }}</h3>
              <div class="cyber-extension-actions">
                <button class="cyber-button primary" @click="executeQuery(ext)">
                  <span class="button-content">
                    <i class="fas fa-search"></i> 执行查询
                  </span>
                </button>
                <button class="cyber-button secondary" @click="toggleForm(ext.id)">
                  <span class="button-content">
                    <i class="fas fa-eye"></i> {{ formVisible[ext.id] ? '隐藏表单' : '显示表单' }}
                  </span>
                </button>
              </div>
            </div>
            
            <div class="cyber-extension-body">
              <p>{{ ext.description || '无描述信息' }}</p>
              <p><strong>接口端点:</strong> <code>{{ ext.endpoint || '/query/' + ext.id }}</code></p>
              
              <!-- 查询表单 -->
              <div class="cyber-query-form" v-if="formVisible[ext.id]" :id="`form-${ext.id}`">
                <h4>查询参数</h4>
                <div v-if="ext.has_query_form">
                  <div v-if="formLoading[ext.id]" class="text-center py-3">
                    <div class="cyber-spinner small"></div>
                    <p>加载表单中...</p>
                  </div>
                  <div v-else-if="formError[ext.id]" class="cyber-alert danger">
                    <i class="fas fa-exclamation-triangle"></i> {{ formError[ext.id] }}
                  </div>
                  <div v-else v-html="formHtml[ext.id]"></div>
                </div>
                <div v-else>
                  <p>此扩展不需要额外参数</p>
                </div>
              </div>
              
              <!-- 查询结果 -->
              <div class="cyber-result-container" v-if="resultVisible[ext.id]" :id="`result-${ext.id}`">
                <div class="cyber-result-header">
                  <h4>查询结果</h4>
                  <button class="cyber-button small" @click="toggleResult(ext.id)">
                    <span class="button-content">
                      <i class="fas fa-eye-slash"></i> 隐藏结果
                    </span>
                  </button>
                </div>
                
                <div v-if="queryLoading[ext.id]" class="text-center py-3">
                  <div class="cyber-spinner"></div>
                  <p>正在查询数据...</p>
                </div>
                <div v-else-if="queryError[ext.id]" class="cyber-alert danger">
                  <i class="fas fa-exclamation-triangle"></i> {{ queryError[ext.id] }}
                </div>
                <div v-else :id="`result-content-${ext.id}`" class="cyber-result-content">
                  <!-- HTML 结果 -->
                  <div v-if="resultType[ext.id] === 'html'" v-html="queryResult[ext.id]"></div>
                  
                  <!-- 表格结果 -->
                  <div v-else-if="resultType[ext.id] === 'table'">
                    <div v-if="resultMeta[ext.id]" class="cyber-result-meta">
                      <pre>{{ JSON.stringify(resultMeta[ext.id], null, 2) }}</pre>
                    </div>
                    
                    <div class="cyber-table-container" v-if="resultData[ext.id] && resultData[ext.id].length > 0">
                      <table class="cyber-table">
                        <thead>
                          <tr>
                            <th v-for="(_, key) in resultData[ext.id][0]" :key="key">{{ key }}</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="(item, index) in resultData[ext.id]" :key="index">
                            <td v-for="(value, key) in item" :key="key">{{ value }}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                  
                  <!-- 图片结果 -->
                  <div v-else-if="resultType[ext.id] === 'image'">
                    <img :src="queryResult[ext.id]" alt="查询结果" class="cyber-result-image">
                  </div>
                  
                  <!-- 文件结果 -->
                  <div v-else-if="resultType[ext.id] === 'file'">
                    <a :href="queryResult[ext.id]" download class="cyber-download-link">
                      <i class="fas fa-download"></i> 下载文件
                    </a>
                  </div>
                  
                  <!-- 其他结果 -->
                  <div v-else>
                    <pre>{{ queryResult[ext.id] }}</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
import { 
  getExtensions, 
  getExtensionQueryForm, 
  executeExtensionQuery 
} from '@/api/extension';
import Toast from '@/utils/toast';
  
  export default {
    name: 'ExtensionQueryView',
    data() {
      return {
        extensions: [],
        loading: true,
        
        // 表单状态
        formVisible: {},
        formLoading: {},
        formError: {},
        formHtml: {},
        
        // 结果状态
        resultVisible: {},
        queryLoading: {},
        queryError: {},
        queryResult: {},
        resultType: {},
        resultMeta: {},
        resultData: {}
      }
    },
    mounted() {
      this.loadExtensions()
    },
    methods: {
      // 加载可用的扩展列表
      async loadExtensions() {
        try {
          this.loading = true
          const response = await getExtensions()
          // 过滤出已启用且应该在首页显示的扩展
          this.extensions = response.data.filter(ext => ext.enabled && ext.show_in_home)
          
          // 初始化状态对象
          this.extensions.forEach(ext => {
            this.formVisible[ext.id] = false
            this.formLoading[ext.id] = false
            this.formError[ext.id] = null
            this.formHtml[ext.id] = null
            
            this.resultVisible[ext.id] = false
            this.queryLoading[ext.id] = false
            this.queryError[ext.id] = null
            this.queryResult[ext.id] = null
            this.resultType[ext.id] = null
            this.resultMeta[ext.id] = null
            this.resultData[ext.id] = null
          })
        } catch (error) {
          console.error('加载扩展列表失败:', error)
          Toast.error('加载扩展列表失败: ' + (error.response?.data?.detail || error.message))
        } finally {
          this.loading = false
        }
      },
      
      // 切换表单显示状态
      async toggleForm(extId) {
        this.formVisible[extId] = !this.formVisible[extId]
        
        // 如果显示表单且还没有加载过表单内容
        if (this.formVisible[extId] && !this.formHtml[extId] && this.extensions.find(ext => ext.id === extId).has_query_form) {
          await this.loadQueryForm(extId)
        }
      },
      
      // 加载查询表单
      async loadQueryForm(extId) {
        try {
          this.formLoading[extId] = true
          this.formError[extId] = null
          
          const response = await getExtensionQueryForm(extId)
          this.formHtml[extId] = response.data
        } catch (error) {
          console.error('加载查询表单失败:', error)
          this.formError[extId] = '加载表单失败: ' + (error.response?.data?.detail || error.message)
        } finally {
          this.formLoading[extId] = false
        }
      },
      
      // 切换结果显示状态
      toggleResult(extId) {
        this.resultVisible[extId] = !this.resultVisible[extId]
      },
      
      // 执行查询
      async executeQuery(ext) {
  const extId = ext.id;
  
  try {
    this.queryLoading[extId] = true;
    this.queryError[extId] = null;
    this.resultVisible[extId] = true;
    
    // 收集表单数据
    const formData = new FormData();
    const formElement = document.getElementById(`form-${extId}`);
    
    if (formElement) {
      // 处理文件上传
      const fileInputs = formElement.querySelectorAll('input[type="file"]');
      fileInputs.forEach(fileInput => {
        if (fileInput.files[0]) {
          formData.append(fileInput.name, fileInput.files[0]);
        }
      });
      
      // 处理其他输入
      const inputs = formElement.querySelectorAll('input, select, textarea');
      inputs.forEach(input => {
        if (input.name && input.style.display !== 'none' && input.type !== 'file' && input.type !== 'button' && input.type !== 'submit') {
          if (input.type === 'checkbox') {
            formData.append(input.name, input.checked);
          } else {
            formData.append(input.name, input.value);
          }
        }
      });
    }
    
    // 发送查询请求
    const response = await executeExtensionQuery(extId, formData);
    
    // 获取扩展配置信息
    const configResponse = await getExtension(extId);
    const returnType = configResponse.data.render_type || 'text';
    
    // 处理返回结果
    if (response.data && response.data.data) {
      this.resultType[extId] = returnType;
      
      if (returnType === 'html') {
        this.queryResult[extId] = response.data.data;
      } else if (returnType === 'table') {
        this.resultMeta[extId] = response.data.meta;
        this.resultData[extId] = response.data.data;
      } else if (returnType === 'image') {
        if (response.data.data.startsWith('data:image')) {
          this.queryResult[extId] = response.data.data;
        } else {
          this.queryResult[extId] = `data:image/png;base64,${response.data.data}`;
        }
      } else if (returnType === 'file') {
        if (response.data.data.startsWith('data:application/octet-stream')) {
          const blob = new Blob([response.data.data], { type: 'application/octet-stream' });
          this.queryResult[extId] = URL.createObjectURL(blob);
        } else if (response.data.data.startsWith('http')) {
          this.queryResult[extId] = response.data.data;
        } else {
          this.queryError[extId] = `返回值类型错误: ${returnType}`;
        }
      } else {
        this.queryResult[extId] = response.data.data;
      }
    } else {
      this.resultType[extId] = 'text';
      this.queryResult[extId] = JSON.stringify(response.data, null, 2);
    }
  } catch (error) {
    console.error('执行查询失败:', error);
    this.queryError[extId] = '查询失败: ' + (error.response?.data?.detail || error.message);
  } finally {
    this.queryLoading[extId] = false;
  }
}
    }
  }
  </script>
  
  <style scoped>
  .extension-query {
    width: 100%;
    /*max-width: 1200px;*/
    margin: 0 auto;
    padding: 20px;
  }
  
  /* 主标题样式 */
  .cyber-header-main {
    margin-bottom: 2rem;
    position: relative;
  }
  
  .cyber-header-main h1 {
    color: #4facfe;
    font-size: 2.5rem;
    font-weight: 600;
    margin: 0;
    padding: 0;
    text-transform: uppercase;
    letter-spacing: 2px;
    display: flex;
    align-items: center;
    text-shadow: 0 0 10px rgba(79, 172, 254, 0.5);
  }
  
  .cyber-header-main h1 i {
    margin-right: 1rem;
    font-size: 2rem;
  }
  
  .cyber-line-main {
    height: 2px;
    background: linear-gradient(90deg, #4facfe, transparent);
    margin-top: 0.5rem;
    position: relative;
    overflow: hidden;
  }
  
  .cyber-line-main::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, #4facfe, transparent);
    animation: cyber-scan 3s linear infinite;
  }
  
  @keyframes cyber-scan {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(100%);
    }
  }
  
  /* 扩展列表 */
  .cyber-extensions-list {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  /* 扩展项 */
  .cyber-extension-item {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border-radius: 10px;
    box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
    border: 1px solid rgba(79, 172, 254, 0.3);
    overflow: hidden;
    position: relative;
    animation: neon-pulse 3s infinite;
  }
  
  .cyber-extension-item::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, #00f2fe, #4facfe, #00f2fe);
    animation: scanline 2s linear infinite;
  }
  
  @keyframes scanline {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(100%);
    }
  }
  
  /* 扩展头部 */
  .cyber-extension-header {
    padding: 1.5rem;
    color: #4facfe;
    border-bottom: 1px solid rgba(79, 172, 254, 0.3);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .cyber-extension-header h3 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
  }
  
  .cyber-extension-actions {
    display: flex;
    gap: 0.5rem;
  }
  
  /* 扩展内容 */
  .cyber-extension-body {
    padding: 1.5rem;
    color: #e0e0ff;
  }
  
  /* 查询表单 */
  .cyber-query-form {
    margin-top: 1.5rem;
    padding: 1.5rem;
    background: rgba(30, 30, 63, 0.5);
    border-radius: 8px;
    border: 1px solid rgba(79, 172, 254, 0.3);
  }
  
  .cyber-query-form h4 {
    margin-top: 0;
    margin-bottom: 1rem;
    color: #4facfe;
    font-weight: 600;
  }
  
  /* 结果容器 */
  .cyber-result-container {
    margin-top: 1.5rem;
    border-radius: 8px;
    border: 1px solid rgba(79, 172, 254, 0.3);
    overflow: hidden;
  }
  
  .cyber-result-header {
    background: rgba(79, 172, 254, 0.1);
    padding: 1rem 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .cyber-result-header h4 {
    margin: 0;
    color: #4facfe;
    font-weight: 600;
  }
  
  .cyber-result-content {
    padding: 1.5rem;
    background: rgba(30, 30, 63, 0.3);
  }
  
  /* 表格 */
  .cyber-table-container {
    overflow-x: auto;
    margin-top: 1rem;
  }
  
  .cyber-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    color: #e0e0ff;
  }
  
  .cyber-table thead tr {
    background: linear-gradient(90deg, rgba(79, 172, 254, 0.2), rgba(0, 242, 254, 0.2));
  }
  
  .cyber-table th {
    padding: 1rem;
    text-align: left;
    font-weight: 600;
    color: #4facfe;
    border-bottom: 1px solid rgba(79, 172, 254, 0.3);
  }
  
  .cyber-table td {
    padding: 1rem;
    border-bottom: 1px solid rgba(79, 172, 254, 0.1);
  }
  
  /* 按钮 */
  .cyber-button {
    background: none;
    border: none;
    position: relative;
    padding: 0.75rem 1.5rem;
    color: #fff;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    cursor: pointer;
    overflow: hidden;
    transition: all 0.3s ease;
  }
  
  .cyber-button::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, #0061ff, #60efff);
    opacity: 0.8;
    z-index: -2;
  }
  
  .cyber-button.primary::before {
    background: linear-gradient(135deg, #0061ff, #60efff);
  }
  
  .cyber-button.secondary::before {
    background: linear-gradient(135deg, #6e7c90, #a1a9b6);
  }
  
  .cyber-button::after {
    content: '';
    position: absolute;
    top: 2px;
    left: 2px;
    right: 2px;
    bottom: 2px;
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    z-index: -1;
  }
  
  .cyber-button .button-content {
    position: relative;
    z-index: 1;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .cyber-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0, 97, 255, 0.4);
  }
  
  .cyber-button:active {
    transform: translateY(0);
  }
  
  .cyber-button.small {
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
  }
  
  /* 加载动画 */
  .cyber-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid transparent;
    border-top-color: #4facfe;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
  }
  
  .cyber-spinner.small {
    width: 20px;
    height: 20px;
    border-width: 2px;
  }
  
  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
  
  /* 警告框 */
  .cyber-alert {
    padding: 1rem 1.5rem;
    border-radius: 8px;
    margin: 1rem 0;
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .cyber-alert i {
    font-size: 1.5rem;
  }
  
  .cyber-alert.info {
    background: rgba(79, 172, 254, 0.1);
    border: 1px solid rgba(79, 172, 254, 0.3);
    color: #4facfe;
  }
  
  .cyber-alert.danger {
    background: rgba(255, 95, 86, 0.1);
    border: 1px solid rgba(255, 95, 86, 0.3);
    color: #ff5f56;
  }
  
  /* 结果图片 */
  .cyber-result-image {
    max-width: 100%;
    border-radius: 8px;
    border: 1px solid rgba(79, 172, 254, 0.3);
  }
  
  /* 下载链接 */
  .cyber-download-link {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: rgba(79, 172, 254, 0.1);
    border: 1px solid rgba(79, 172, 254, 0.3);
    border-radius: 8px;
    color: #4facfe;
    text-decoration: none;
    transition: all 0.3s ease;
  }
  
  .cyber-download-link:hover {
    background: rgba(79, 172, 254, 0.2);
    transform: translateY(-2px);
  }
  
  /* 结果元数据 */
  .cyber-result-meta {
    margin-bottom: 1rem;
    padding: 1rem;
    background: rgba(30, 30, 63, 0.5);
    border-radius: 8px;
    border: 1px solid rgba(79, 172, 254, 0.3);
  }
  
  .cyber-result-meta pre {
    margin: 0;
    color: #a1a9b6;
    font-family: 'Courier New', monospace;
    white-space: pre-wrap;
  }
  
  /* 动画效果 */
  @keyframes neon-pulse {
    0% {
      box-shadow: 0 0 5px rgba(79, 172, 254, 0.5), 0 0 10px rgba(79, 172, 254, 0.3);
    }
    50% {
      box-shadow: 0 0 10px rgba(79, 172, 254, 0.8), 0 0 20px rgba(79, 172, 254, 0.5);
    }
    100% {
      box-shadow: 0 0 5px rgba(79, 172, 254, 0.5), 0 0 10px rgba(79, 172, 254, 0.3);
    }
  }
  
  /* 响应式设计 */
  @media (max-width: 768px) {
    .cyber-extension-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }
    
    .cyber-extension-actions {
      width: 100%;
      justify-content: space-between;
    }
    
    .cyber-result-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }
  }
  </style>