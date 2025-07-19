<template>
  <div class="avatar-test-container">
    <h2>头像显示测试</h2>
    
    <!-- 测试不同的头像显示方式 -->
    <div class="test-section">
      <h3>1. 使用v-img组件（固定尺寸）</h3>
      <v-img
        :src="testAvatarUrl"
        alt="测试头像"
        width="120"
        height="120"
        class="test-avatar-1"
      ></v-img>
      <p>尺寸: 120x120px</p>
    </div>
    
    <div class="test-section">
      <h3>2. 使用v-img组件（max尺寸）</h3>
      <v-img
        :src="testAvatarUrl"
        alt="测试头像"
        max-width="120"
        max-height="120"
        class="test-avatar-2"
      ></v-img>
      <p>最大尺寸: 120x120px</p>
    </div>
    
    <div class="test-section">
      <h3>3. 使用普通img标签</h3>
      <img
        :src="testAvatarUrl"
        alt="测试头像"
        class="test-avatar-3"
      />
      <p>CSS控制尺寸</p>
    </div>
    
    <div class="test-section">
      <h3>4. 使用div背景图</h3>
      <div
        class="test-avatar-4"
        :style="{ backgroundImage: `url(${testAvatarUrl})` }"
      ></div>
      <p>背景图方式</p>
    </div>
    
    <!-- 测试数据URL -->
    <div class="test-section">
      <h3>5. 测试Data URL</h3>
      <v-img
        :src="dataUrl"
        alt="Data URL头像"
        width="120"
        height="120"
        class="test-avatar-5"
      ></v-img>
      <p>Data URL方式</p>
    </div>
    
    <!-- 控制面板 -->
    <div class="control-panel">
      <h3>控制面板</h3>
      <v-text-field
        v-model="testAvatarUrl"
        label="头像URL"
        outlined
        dense
      ></v-text-field>
      
      <v-btn @click="generateDataUrl" color="primary" class="mr-2">
        生成测试Data URL
      </v-btn>
      
      <v-btn @click="testFileUpload" color="secondary">
        测试文件上传
      </v-btn>
      
      <input
        ref="fileInput"
        type="file"
        accept="image/*"
        style="display: none"
        @change="handleFileUpload"
      />
    </div>
    
    <!-- 调试信息 -->
    <div class="debug-info">
      <h3>调试信息</h3>
      <pre>{{ debugInfo }}</pre>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AvatarTest',
  data() {
    return {
      testAvatarUrl: 'https://via.placeholder.com/120x120/4CAF50/FFFFFF?text=Test',
      dataUrl: '',
      debugInfo: {}
    }
  },
  mounted() {
    this.updateDebugInfo()
  },
  methods: {
    generateDataUrl() {
      // 创建一个简单的canvas图像作为data URL
      const canvas = document.createElement('canvas')
      canvas.width = 120
      canvas.height = 120
      const ctx = canvas.getContext('2d')
      
      // 绘制一个简单的头像
      ctx.fillStyle = '#4CAF50'
      ctx.fillRect(0, 0, 120, 120)
      ctx.fillStyle = '#FFFFFF'
      ctx.font = '20px Arial'
      ctx.textAlign = 'center'
      ctx.fillText('DATA', 60, 70)
      
      this.dataUrl = canvas.toDataURL()
      this.updateDebugInfo()
    },
    
    testFileUpload() {
      this.$refs.fileInput.click()
    },
    
    handleFileUpload(event) {
      const file = event.target.files[0]
      if (!file) return
      
      const reader = new FileReader()
      reader.onload = (e) => {
        this.dataUrl = e.target.result
        this.updateDebugInfo()
      }
      reader.readAsDataURL(file)
    },
    
    updateDebugInfo() {
      this.debugInfo = {
        testAvatarUrl: this.testAvatarUrl,
        dataUrlLength: this.dataUrl.length,
        dataUrlPreview: this.dataUrl.substring(0, 100) + '...',
        timestamp: new Date().toLocaleString()
      }
    }
  },
  watch: {
    testAvatarUrl() {
      this.updateDebugInfo()
    }
  }
}
</script>

<style scoped>
.avatar-test-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.test-section {
  margin: 20px 0;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.test-avatar-1,
.test-avatar-2,
.test-avatar-5 {
  border-radius: 50%;
  border: 3px solid #eee;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.test-avatar-3 {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  border: 3px solid #eee;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  object-fit: cover;
}

.test-avatar-4 {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  border: 3px solid #eee;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

.control-panel {
  margin: 30px 0;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
}

.debug-info {
  margin: 20px 0;
  padding: 15px;
  background: #f0f0f0;
  border-radius: 8px;
  font-family: monospace;
}

.debug-info pre {
  margin: 0;
  white-space: pre-wrap;
}
</style>
