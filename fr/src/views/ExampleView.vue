<template>
    <div class="example-container">
      <h1>帮助文档</h1>
      
      <div class="alert alert-info">
        <p>本页面提供了系统的使用示例和教程，帮助您更好地使用数据查询系统。</p>
      </div>
      
      <div class="row">
        <div class="col-md-3">
          <div class="list-group">
            <a 
              href="#basic" 
              class="list-group-item list-group-item-action active"
              @click.prevent="activeSection = 'basic'"
              :class="{ active: activeSection === 'basic' }"
            >
              基础教程
            </a>
            <a 
              href="#advanced" 
              class="list-group-item list-group-item-action"
              @click.prevent="activeSection = 'advanced'"
              :class="{ active: activeSection === 'advanced' }"
            >
              高级功能
            </a>
            <a 
              href="#api" 
              class="list-group-item list-group-item-action"
              @click.prevent="activeSection = 'api'"
              :class="{ active: activeSection === 'api' }"
            >
              API文档
            </a>
            <a 
              href="#examples" 
              class="list-group-item list-group-item-action"
              @click.prevent="activeSection = 'examples'"
              :class="{ active: activeSection === 'examples' }"
            >
              使用示例
            </a>
          </div>
        </div>
        
        <div class="col-md-9">
          <div v-if="activeSection === 'basic'" class="section">
            <h2>基础教程</h2>
            
            <div class="card mb-4">
              <div class="card-header">
                <h3>1. 系统登录</h3>
              </div>
              <div class="card-body">
                <p>访问系统首页，点击右上角的"登录"按钮，输入您的用户名和密码进行登录。如果您还没有账号，可以点击"注册"按钮创建一个新账号。</p>
                <img src="/static/img/example/login.png" alt="登录示例" class="img-fluid mb-3">
              </div>
            </div>
            
            <div class="card mb-4">
              <div class="card-header">
                <h3>2. 文件管理</h3>
              </div>
              <div class="card-body">
                <p>在文件管理页面，您可以：</p>
                <ul>
                  <li>上传文件：点击"上传文件"按钮，选择要上传的文件</li>
                  <li>创建文件夹：点击"新建文件夹"按钮，输入文件夹名称</li>
                  <li>下载文件：点击文件旁边的下载图标</li>
                  <li>删除文件：点击文件旁边的删除图标</li>
                </ul>
                <img src="/static/img/example/file-manager.png" alt="文件管理示例" class="img-fluid mb-3">
              </div>
            </div>
            
            <div class="card mb-4">
              <div class="card-header">
                <h3>3. 聊天功能</h3>
              </div>
              <div class="card-body">
                <p>在聊天页面，您可以：</p>
                <ul>
                  <li>创建聊天室：点击"创建聊天室"按钮</li>
                  <li>加入聊天室：点击左侧的聊天室列表</li>
                  <li>发送消息：在底部输入框中输入消息，按回车键或点击发送按钮</li>
                  <li>发送图片：点击图片图标，选择要发送的图片</li>
                </ul>
                <img src="/static/img/example/chat.png" alt="聊天示例" class="img-fluid mb-3">
              </div>
            </div>
          </div>
          
          <div v-if="activeSection === 'advanced'" class="section">
            <h2>高级功能</h2>
            
            <div class="card mb-4">
              <div class="card-header">
                <h3>1. 扩展管理</h3>
              </div>
              <div class="card-body">
                <p>扩展管理功能允许您安装、配置和管理系统扩展，以增强系统功能。</p>
                <h4>安装扩展</h4>
                <ol>
                  <li>进入扩展管理页面</li>
                  <li>点击"安装扩展"按钮</li>
                  <li>选择从文件安装或从URL安装</li>
                  <li>上传扩展文件或输入扩展URL</li>
                  <li>点击"安装"按钮完成安装</li>
                </ol>
                
                <h4>配置扩展</h4>
                <ol>
                  <li>在扩展卡片上点击配置图标</li>
                  <li>根据扩展要求填写配置信息</li>
                  <li>点击"保存"按钮保存配置</li>
                </ol>
                
                <h4>启用/禁用扩展</h4>
                <p>在扩展卡片上切换开关即可启用或禁用扩展。</p>
              </div>
            </div>
            
            <div class="card mb-4">
              <div class="card-header">
                <h3>2. 定时任务</h3>
              </div>
              <div class="card-body">
                <p>定时任务功能允许您创建自动执行的任务，以便定期处理数据或执行其他操作。</p>
                <h4>创建定时任务</h4>
                <ol>
                  <li>进入定时任务页面</li>
                  <li>点击"添加任务"按钮</li>
                  <li>填写任务名称、函数路径和计划（Cron表达式）</li>
                  <li>点击"保存"按钮创建任务</li>
                </ol>
                
                <h4>Cron表达式示例</h4>
                <ul>
                  <li><code>*/5 * * * *</code>：每5分钟执行一次</li>
                  <li><code>0 * * * *</code>：每小时整点执行</li>
                  <li><code>0 0 * * *</code>：每天午夜执行</li>
                  <li><code>0 0 * * 0</code>：每周日午夜执行</li>
                  <li><code>0 0 1 * *</code>：每月1日午夜执行</li>
                </ul>
              </div>
            </div>
          </div>
          
          <div v-if="activeSection === 'api'" class="section">
            <h2>API文档</h2>
            
            <div class="alert alert-primary">
              <p>系统提供了丰富的API接口，您可以通过这些接口与系统进行交互。</p>
            </div>
            
            <div class="card mb-4">
              <div class="card-header">
                <h3>认证API</h3>
              </div>
              <div class="card-body">
                <h4>登录</h4>
                <pre><code>POST /api/auth/login
  Content-Type: application/json
  
  {
    "username": "your_username",
    "password": "your_password"
  }</code></pre>
                
                <h4>注册</h4>
                <pre><code>POST /api/auth/register
  Content-Type: application/json
  
  {
    "username": "new_username",
    "password": "new_password",
    "email": "user@example.com"
  }</code></pre>
                
                <h4>获取当前用户</h4>
                <pre><code>GET /api/auth/current-user
  Authorization: Bearer your_token</code></pre>
              </div>
            </div>
            
            <div class="card mb-4">
              <div class="card-header">
                <h3>文件API</h3>
              </div>
              <div class="card-body">
                <h4>获取文件列表</h4>
                <pre><code>GET /api/files/list?path=your_path
  Authorization: Bearer your_token</code></pre>
                
                <h4>上传文件</h4>
                <pre><code>POST /api/files/upload
  Authorization: Bearer your_token
  Content-Type: multipart/form-data
  
  files: [file1, file2, ...]
  path: "your_path"</code></pre>
                
                <h4>下载文件</h4>
                <pre><code>GET /api/files/download?path=your_file_path
  Authorization: Bearer your_token</code></pre>
              </div>
            </div>
          </div>
          
          <div v-if="activeSection === 'examples'" class="section">
            <h2>使用示例</h2>
            
            <div class="card mb-4">
              <div class="card-header">
                <h3>示例1：数据导入与分析</h3>
              </div>
              <div class="card-body">
                <p>本示例演示如何导入CSV数据并进行简单分析。</p>
                
                <h4>步骤1：上传CSV文件</h4>
                <p>首先，在文件管理页面上传一个CSV文件。</p>
                
                <h4>步骤2：使用数据分析扩展</h4>
                <p>安装并配置数据分析扩展，指定CSV文件路径。</p>
                
                <h4>步骤3：查看分析结果</h4>
                <p>在扩展的结果页面查看数据分析结果，包括统计信息和图表。</p>
                
                <div class="example-images">
                  <img src="/static/img/example/example1-1.png" alt="上传CSV" class="img-fluid mb-2">
                  <img src="/static/img/example/example1-2.png" alt="配置扩展" class="img-fluid mb-2">
                  <img src="/static/img/example/example1-3.png" alt="分析结果" class="img-fluid mb-2">
                </div>
              </div>
            </div>
            
            <div class="card mb-4">
              <div class="card-header">
                <h3>示例2：定时数据备份</h3>
              </div>
              <div class="card-body">
                <p>本示例演示如何设置定时任务，自动备份重要数据。</p>
                
                <h4>步骤1：创建备份脚本</h4>
                <p>编写一个Python脚本，用于备份数据。</p>
                
                <h4>步骤2：设置定时任务</h4>
                <p>在定时任务页面创建一个新任务，指定备份脚本路径和执行计划。</p>
                
                <h4>步骤3：查看备份结果</h4>
                <p>在文件管理页面查看生成的备份文件。</p>
                
                <div class="example-images">
                  <img src="/static/img/example/example2-1.png" alt="备份脚本" class="img-fluid mb-2">
                  <img src="/static/img/example/example2-2.png" alt="设置任务" class="img-fluid mb-2">
                  <img src="/static/img/example/example2-3.png" alt="备份结果" class="img-fluid mb-2">
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'ExampleView',
    data() {
      return {
        activeSection: 'basic'
      }
    }
  }
  </script>
  
  <style scoped>
  .example-container {
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
  
  h3 {
    color: #3498db;
  }
  
  h4 {
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
    color: #2c3e50;
  }
  
  .section {
    padding: 1rem;
    background-color: #f8f9fa;
    border-radius: 4px;
    min-height: 400px;
  }
  
  .card {
    margin-bottom: 1.5rem;
  }
  
  .card-header {
    background-color: #f1f8ff;
  }
  
  .card-header h3 {
    margin: 0;
    font-size: 1.25rem;
  }
  
  pre {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 4px;
    overflow-x: auto;
  }
  
  code {
    color: #e83e8c;
  }
  
  .example-images {
    margin-top: 1.5rem;
  }
  
  .example-images img {
    border: 1px solid #dee2e6;
    border-radius: 4px;
    max-width: 100%;
  }
  
  .list-group-item.active {
    background-color: #3498db;
    border-color: #3498db;
  }
  </style>