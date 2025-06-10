<template>
    <div class="help-container">
      <h1>帮助中心</h1>
      
      <div class="help-content">
        <div class="row">
          <div class="col-md-3">
            <div class="nav flex-column nav-pills" id="v-pills-tab" role="tablist">
              <button 
                class="nav-link active" 
                id="v-pills-home-tab" 
                data-bs-toggle="pill" 
                data-bs-target="#v-pills-home" 
                type="button" 
                role="tab"
              >
                系统介绍
              </button>
              <button 
                class="nav-link" 
                id="v-pills-profile-tab" 
                data-bs-toggle="pill" 
                data-bs-target="#v-pills-profile" 
                type="button" 
                role="tab"
              >
                快速入门
              </button>
              <button 
                class="nav-link" 
                id="v-pills-messages-tab" 
                data-bs-toggle="pill" 
                data-bs-target="#v-pills-messages" 
                type="button" 
                role="tab"
              >
                常见问题
              </button>
              <button 
                class="nav-link" 
                id="v-pills-settings-tab" 
                data-bs-toggle="pill" 
                data-bs-target="#v-pills-settings" 
                type="button" 
                role="tab"
              >
                联系我们
              </button>
            </div>
          </div>
          <div class="col-md-9">
            <div class="tab-content" id="v-pills-tabContent">
              <div 
                class="tab-pane fade show active" 
                id="v-pills-home" 
                role="tabpanel" 
                aria-labelledby="v-pills-home-tab"
              >
                <h2>系统介绍</h2>
                <p>数据查询系统是一个功能强大的数据管理和查询平台，旨在帮助用户高效地管理和分析数据。</p>
                
                <h3>主要功能</h3>
                <ul>
                  <li><strong>数据查询</strong>：支持多种数据源的查询和分析</li>
                  <li><strong>文件管理</strong>：上传、下载和管理各类文件</li>
                  <li><strong>扩展系统</strong>：通过扩展增强系统功能</li>
                  <li><strong>聊天功能</strong>：实时沟通和协作</li>
                  <li><strong>定时任务</strong>：自动化数据处理和分析</li>
                </ul>
                
                <h3>系统特点</h3>
                <ul>
                  <li>高度可定制化</li>
                  <li>安全可靠</li>
                  <li>易于使用</li>
                  <li>可扩展性强</li>
                </ul>
              </div>
              
              <div 
                class="tab-pane fade" 
                id="v-pills-profile" 
                role="tabpanel" 
                aria-labelledby="v-pills-profile-tab"
              >
                <h2>快速入门</h2>
                
                <h3>1. 注册和登录</h3>
                <p>首先，您需要注册一个账户，然后使用您的用户名和密码登录系统。</p>
                
                <h3>2. 浏览数据</h3>
                <p>登录后，您可以在首页看到系统的主要功能模块。点击相应的模块进入对应的功能页面。</p>
                
                <h3>3. 上传文件</h3>
                <p>在文件管理页面，您可以上传、下载和管理您的文件。</p>
                
                <h3>4. 使用扩展</h3>
                <p>系统支持多种扩展，您可以在扩展管理页面安装和配置这些扩展。</p>
                
                <h3>5. 设置定时任务</h3>
                <p>在定时任务页面，您可以创建和管理自动执行的任务。</p>
              </div>
              
              <div 
                class="tab-pane fade" 
                id="v-pills-messages" 
                role="tabpanel" 
                aria-labelledby="v-pills-messages-tab"
              >
                <h2>常见问题</h2>
                
                <div class="accordion" id="faqAccordion">
                  <div class="accordion-item">
                    <h2 class="accordion-header" id="headingOne">
                      <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseOne">
                        如何重置密码？
                      </button>
                    </h2>
                    <div id="collapseOne" class="accordion-collapse collapse show" data-bs-parent="#faqAccordion">
                      <div class="accordion-body">
                        如果您忘记了密码，可以在登录页面点击"忘记密码"链接，然后按照提示操作。系统将向您的注册邮箱发送重置密码的链接。
                      </div>
                    </div>
                  </div>
                  
                  <div class="accordion-item">
                    <h2 class="accordion-header" id="headingTwo">
                      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseTwo">
                        系统支持哪些文件格式？
                      </button>
                    </h2>
                    <div id="collapseTwo" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
                      <div class="accordion-body">
                        系统支持多种常见文件格式，包括但不限于：PDF、Word、Excel、图片（JPG、PNG、GIF）、音频（MP3、WAV）、视频（MP4、AVI）等。
                      </div>
                    </div>
                  </div>
                  
                  <div class="accordion-item">
                    <h2 class="accordion-header" id="headingThree">
                      <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseThree">
                        如何安装扩展？
                      </button>
                    </h2>
                    <div id="collapseThree" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
                      <div class="accordion-body">
                        在扩展管理页面，点击"安装扩展"按钮，然后选择从文件安装或从URL安装。上传扩展文件或输入扩展URL后，点击"安装"按钮完成安装。
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div 
                class="tab-pane fade" 
                id="v-pills-settings" 
                role="tabpanel" 
                aria-labelledby="v-pills-settings-tab"
              >
                <h2>联系我们</h2>
                
                <p>如果您有任何问题或建议，请通过以下方式联系我们：</p>
                
                <div class="contact-info">
                  <div class="mb-3">
                    <h4>技术支持</h4>
                    <p>邮箱：support@example.com</p>
                    <p>电话：123-456-7890</p>
                  </div>
                  
                  <div class="mb-3">
                    <h4>商务合作</h4>
                    <p>邮箱：business@example.com</p>
                    <p>电话：123-456-7891</p>
                  </div>
                  
                  <div class="mb-3">
                    <h4>反馈建议</h4>
                    <p>邮箱：feedback@example.com</p>
                  </div>
                </div>
                
                <div class="feedback-form">
                  <h3>在线反馈</h3>
                  <form @submit.prevent="submitFeedback">
                    <div class="mb-3">
                      <label for="name" class="form-label">姓名</label>
                      <input type="text" class="form-control" id="name" v-model="feedback.name" required>
                    </div>
                    <div class="mb-3">
                      <label for="email" class="form-label">邮箱</label>
                      <input type="email" class="form-control" id="email" v-model="feedback.email" required>
                    </div>
                    <div class="mb-3">
                      <label for="subject" class="form-label">主题</label>
                      <input type="text" class="form-control" id="subject" v-model="feedback.subject" required>
                    </div>
                    <div class="mb-3">
                      <label for="message" class="form-label">内容</label>
                      <textarea class="form-control" id="message" rows="5" v-model="feedback.message" required></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">提交</button>
                  </form>
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
    name: 'HelpView',
    data() {
      return {
        feedback: {
          name: '',
          email: '',
          subject: '',
          message: ''
        }
      }
    },
    methods: {
      submitFeedback() {
        // 这里可以添加提交反馈的逻辑
        alert('感谢您的反馈！我们将尽快回复。')
        this.feedback = {
          name: '',
          email: '',
          subject: '',
          message: ''
        }
      }
    }
  }
  </script>
  
  <style scoped>
  .help-container {
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
    margin-top: 1.5rem;
    margin-bottom: 1rem;
    color: #3498db;
  }
  
  .help-content {
    margin-top: 2rem;
  }
  
  .nav-pills .nav-link {
    color: #2c3e50;
    border-radius: 4px;
    margin-bottom: 0.5rem;
  }
  
  .nav-pills .nav-link.active {
    background-color: #3498db;
    color: white;
  }
  
  .tab-content {
    padding: 1rem;
    background-color: #f8f9fa;
    border-radius: 4px;
    min-height: 400px;
  }
  
  .accordion-button:not(.collapsed) {
    background-color: #e7f5ff;
    color: #0d6efd;
  }
  
  .contact-info {
    margin-bottom: 2rem;
  }
  
  .feedback-form {
    background-color: #fff;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  </style>