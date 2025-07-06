<template>
  <div class="qrfile-container">
    <div class="page-header">
      <h1>文件二维码工具</h1>
      <p class="subtitle">将文件或Excel区域转换为二维码，便于离线存储与传输</p>
      <div class="header-actions">
        <router-link to="/qrfile-manage" class="manage-link">
          <el-button type="info" size="large">
            <i class="fas fa-cog"></i> 文件管理
          </el-button>
        </router-link>
      </div>
    </div>
    
    <div class="main-content">
      <!-- 控制面板 -->
      <div class="control-panel">
        <!-- 模式选择 -->
        <div class="panel-section">
          <h3 class="section-title">模式选择</h3>
          <div class="mode-selector">
            <el-radio-group v-model="mode" @change="resetData">
              <el-radio value="region">Excel区域模式</el-radio>
              <el-radio value="file">文件模式</el-radio>
            </el-radio-group>
          </div>
        </div>
        
        <!-- 文件选择区域 -->
        <div class="panel-section">
          <h3 class="section-title">{{ mode === 'region' ? 'Excel文件' : '文件' }}选择</h3>
          <el-upload
            class="file-uploader"
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :file-list="fileList"
            :limit="1"
            :accept="mode === 'region' ? '.xlsx,.xls' : ''"
          >
            <template #trigger>
              <el-button type="primary">选择{{ mode === 'region' ? 'Excel文件' : '文件' }}</el-button>
            </template>
            <template #tip>
              <div class="el-upload__tip">
                {{ mode === 'region' ? '请选择Excel文件(.xlsx,.xls)' : '选择任意类型文件（建议不超过10MB）' }}
              </div>
            </template>
          </el-upload>
        </div>
        
        <!-- Excel区域设置 -->
        <div v-if="mode === 'region'" class="panel-section">
          <h3 class="section-title">Excel区域设置</h3>
          <div class="region-settings">
            <div class="setting-item">
              <span class="setting-label">区域:</span>
              <el-input v-model="regionInput" placeholder="例如: A1:D10"></el-input>
            </div>
            <div class="setting-item">
              <span class="setting-label">Sheet:</span>
              <el-select v-model="selectedSheet" placeholder="选择Sheet" clearable>
                <el-option v-for="sheet in sheetList" :key="sheet" :label="sheet" :value="sheet"></el-option>
              </el-select>
              <div v-if="sheetList.length === 0" class="sheet-tip">
                请先上传Excel文件以加载可用的Sheet
              </div>
            </div>
          </div>
        </div>
        
        <!-- 二维码设置 -->
        <div class="panel-section">
          <h3 class="section-title">二维码设置</h3>
          <div class="setting-item">
            <span class="setting-label">数据块大小:</span>
            <el-select v-model="chunkSize" placeholder="选择数据块大小">
              <el-option label="1200字节" :value="1200"></el-option>
              <el-option label="1500字节" :value="1500"></el-option>
              <el-option label="1800字节" :value="1800"></el-option>
              <el-option label="2000字节" :value="2000"></el-option>
              <el-option label="2500字节" :value="2500"></el-option>
            </el-select>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="panel-section">
          <h3 class="section-title">操作</h3>
          <div class="action-buttons">
            <el-button type="primary" @click="serialize" :disabled="!selectedFile || loading">
              <i class="fas fa-cube"></i> 序列化
            </el-button>
            <el-button type="success" @click="generateQR" :disabled="!serializedData || loading">
              <i class="fas fa-qrcode"></i> 生成二维码
            </el-button>
            <el-button type="info" @click="showScanModal = true">
              <i class="fas fa-search"></i> 扫描恢复
            </el-button>
            <el-button type="warning" @click="saveAllQR" :disabled="!qrImages.length || loading">
              <i class="fas fa-download"></i> 保存二维码
            </el-button>
          </div>
        </div>
        
        <!-- 进度显示 -->
        <div class="panel-section">
          <h3 class="section-title">进度</h3>
          <el-progress :percentage="progress" :status="progressStatus"></el-progress>
          <div class="progress-text">{{ progressText }}</div>
        </div>

        <!-- 输入session,输入框及按钮放置在同一行中
         -->
         <div class="panel-section">
  <h3 class="section-title">输入session</h3>
  <div class="input-group" style="display: flex; gap: 10px;">
    <el-input 
      v-model="sessionInput" 
      placeholder="请输入session"
      style="flex: 1;"
    ></el-input>
    <el-button 
      :disabled="!sessionInput" 
      type="primary" 
      @click="getQRFilesBySessionId"
    >
      获取二维码
    </el-button>
  </div>
</div>

      </div>
      
      <!-- 二维码预览区域 -->
      <div class="preview-panel">
        <h3 class="panel-title">二维码预览</h3>
        
        <div v-if="loading" class="loading-container">
          <el-skeleton :rows="5" animated />
        </div>
        
        <div v-else-if="!qrImages.length" class="no-qr-container">
          <el-empty description="暂无二维码，请先序列化数据并生成二维码"></el-empty>
        </div>
        
        <div v-else class="qr-content">
          <!-- 导航控制 -->
          <div class="qr-navigation">
            <el-button @click="prevQR" :disabled="currentQRIndex <= 0">
              <i class="fas fa-arrow-left"></i> 上一个
            </el-button>
            <span class="qr-position">{{ currentQRIndex + 1 }}/{{ qrImages.length }}</span>
            <el-button @click="nextQR" :disabled="currentQRIndex >= qrImages.length - 1">
              <i class="fas fa-arrow-right"></i> 下一个
            </el-button>
            <span class="qr-name">{{ qrImages[currentQRIndex]?.name || '' }}</span>
          </div>
          
          <!-- 图片显示 -->
          <div class="qr-image-container">
            <img v-if="qrImages[currentQRIndex]" :src="getQRImageUrl(currentQRIndex)" class="qr-image" />
          </div>
        </div>
      </div>
    </div>
    
    <!-- 扫描恢复模态框 -->
    <el-dialog
      v-model="showScanModal"
      title="扫描二维码恢复"
      width="500px"
      @closed="resetScanData"
    >
      <div class="scan-dialog-content">
        <!-- 扫描模式选择 -->
        <div class="scan-mode-selector">
          <el-radio-group v-model="scanMode" @change="resetScanData">
            <el-radio value="image">图片扫描</el-radio>
            <el-radio value="video">视频扫描</el-radio>
            <el-radio value="text">文本恢复</el-radio>
          </el-radio-group>
        </div>
        
        <!-- 图片扫描 -->
        <div v-if="scanMode === 'image'" class="scan-section">
          <el-upload
            class="scan-uploader"
            action="#"
            :auto-upload="false"
            :on-change="handleScanFileChange"
            :file-list="scanFileList"
            multiple
            :accept="'.png,.jpg,.jpeg'"
          >
            <template #trigger>
              <el-button type="primary">选择二维码图片</el-button>
            </template>
            <template #tip>
              <div class="el-upload__tip">
                支持PNG、JPG格式的二维码图片，可多选
              </div>
            </template>
          </el-upload>
        </div>
        
        <!-- 视频扫描 -->
        <div v-else-if="scanMode === 'video'" class="scan-section">
          <el-upload
            class="scan-uploader"
            action="#"
            :auto-upload="false"
            :on-change="handleScanVideoChange"
            :file-list="scanVideoList"
            :limit="1"
            :accept="'.mp4,.avi,.mov,.mkv,.wmv'"
          >
            <template #trigger>
              <el-button type="primary">选择视频文件</el-button>
            </template>
            <template #tip>
              <div class="el-upload__tip">
                支持MP4、AVI、MOV、MKV、WMV格式的视频文件
                <br>视频中应包含清晰可见的二维码，处理时间可能较长，请耐心等待
              </div>
            </template>
          </el-upload>
          
          <div class="video-tips">
            <el-alert
              title="视频扫描提示"
              type="info"
              description="1. 确保视频中的二维码清晰可见且大小适中
2. 视频分辨率建议不低于720p
3. 视频处理可能需要较长时间，请耐心等待
4. 如果视频扫描失败，建议使用图片扫描模式"
              show-icon
              :closable="false"
            ></el-alert>
          </div>
        </div>
        
        <!-- 文本恢复 -->
        <div v-else class="scan-section">
          <div class="text-restore-container">
            <el-alert
              title="文本恢复说明"
              type="info"
              description="请输入或粘贴二维码文本内容，不同二维码的文本内容使用英文分号(;)分隔"
              show-icon
              :closable="false"
              style="margin-bottom: 15px;"
            ></el-alert>
            
            <el-input
              v-model="qrTextContent"
              type="textarea"
              :rows="10"
              placeholder="粘贴二维码文本内容，使用英文分号(;)分隔不同二维码的内容"
            ></el-input>
            
            <div class="text-restore-tips">
              <p>提示：</p>
              <ul>
                <li>确保文本内容完整无误</li>
                <li>每个二维码内容之间使用英文分号(;)分隔</li>
                <li>如果只有一个二维码，不需要添加分号</li>
              </ul>
            </div>
          </div>
        </div>
        
        <div v-if="scanProgress > 0" class="scan-progress">
          <el-progress :percentage="scanProgress"></el-progress>
          <div class="progress-text">{{ scanProgressText }}</div>
        </div>
        
        <div v-if="restoreResult" class="restore-result">
          <el-alert
            :title="restoreResult.success ? '恢复成功' : '恢复失败'"
            :type="restoreResult.success ? 'success' : 'error'"
            :description="restoreResult.message"
            show-icon
          ></el-alert>
          
          <div v-if="restoreResult.success" class="download-section">
            <el-button type="primary" @click="downloadRestoredFile">
              <i class="fas fa-download"></i> 下载恢复的文件
            </el-button>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showScanModal = false">取消</el-button>
          <el-button type="primary" @click="startScanRestore" 
                    :disabled="(scanMode === 'image' && !scanFiles.length) || 
                              (scanMode === 'video' && !scanVideo) || 
                              (scanMode === 'text' && !qrTextContent) || 
                              scanLoading">
            开始恢复
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { serializeExcel, serializeFile, generateQRCodes, scanRestore, scanVideo as scanVideoApi, getQRCodeUrl, getExcelSheets, restoreFromText, getQRFilesBySessionIdApi } from '@/api/qrfile'
import Toast from '@/utils/toast'

export default {
  name: 'QRFileView',
  setup() {
    // 基本状态
    const mode = ref('region')
    const fileList = ref([])
    const selectedFile = ref(null)
    const loading = ref(false)
    const progress = ref(0)
    const progressText = ref('就绪')
    const progressStatus = ref('')
    const sessionInput = ref('')
    // Excel区域模式相关
    const regionInput = ref('A1:D10')
    const selectedSheet = ref('')
    const sheetList = ref([])
    
    // 二维码设置
    const chunkSize = ref(1800)
    
    // 序列化数据
    const serializedData = ref(null)
    
    // 二维码图片
    const qrImages = ref([])
    const currentQRIndex = ref(0)
    
    // 扫描恢复相关
    const showScanModal = ref(false)
    const scanMode = ref('image')
    const scanFileList = ref([])
    const scanFiles = ref([])
    const scanVideoList = ref([])
    const scanVideo = ref(null)
    const scanLoading = ref(false)
    const scanProgress = ref(0)
    const scanProgressText = ref('')
    const restoreResult = ref(null)
    const qrTextContent = ref('')
    
    // 计算属性
    const computedProgressStatus = computed(() => {
      if (progress.value === 100) return 'success'
      if (progress.value === 0) return ''
      return 'exception'
    })
    
    // 方法
    
    // 更新进度
    const updateProgress =async (value, message = '') => {
      progress.value = value
      if (message) progressText.value = message
    }
    
    // 文件变更处理
    const handleFileChange = async (file) => {
      fileList.value = [file]
      selectedFile.value = file.raw
      
      // 如果是Excel文件，加载sheet列表
      if (mode.value === 'region' && selectedFile.value) {
        loadSheetList(selectedFile.value)
      }
    }
    
    // 加载Excel的sheet列表 - 使用后端API
    const loadSheetList = async (file) => {
      try {
        loading.value = true
        updateProgress(10, '加载Excel表...')
        
        const response = await getExcelSheets(file)
        if (response.data && response.data.success && response.data.sheets) {
          sheetList.value = response.data.sheets
          if (sheetList.value.length > 0) {
            selectedSheet.value = sheetList.value[0]
          }
        } else {
          // 如果API调用成功但没有返回sheets
          sheetList.value = ['Sheet1']
          selectedSheet.value = 'Sheet1'
        }
      } catch (err) {
        console.error('加载Excel表失败', err)
        Toast.error('加载Excel表失败，使用默认Sheet')
        sheetList.value = ['Sheet1']
        selectedSheet.value = 'Sheet1'
      } finally {
        loading.value = false
        updateProgress(0, '就绪')
      }
    }
    
    // 序列化数据
    const serialize = async () => {
      if (!selectedFile.value) {
        Toast.warning('请先选择文件')
        return
      }
      
      if (mode.value === 'region' && (!regionInput.value || !regionInput.value.includes(':'))) {
        Toast.warning('请输入有效的Excel区域，例如A1:D10')
        return
      }
      
      try {
        loading.value = true
        updateProgress(10, '开始序列化...')
        
        let response
        if (mode.value === 'region') {
          response = await serializeExcel(selectedFile.value, regionInput.value, selectedSheet.value)
        } else {
          response = await serializeFile(selectedFile.value)
        }
        
        serializedData.value = response.data
        updateProgress(100, '序列化成功')
        Toast.success(`${mode.value === 'region' ? 'Excel区域' : '文件'}序列化成功！数据大小: ${serializedData.value.data_size} 字节`)
      } catch (err) {
        console.error('序列化失败', err)
        updateProgress(0, '序列化失败')
        Toast.error(`序列化失败: ${err.response?.data?.detail || err.message}`)
      } finally {
        loading.value = false
        setTimeout(() => {
          updateProgress(0, '就绪')
        }, 3000)
      }
    }
    
    // 生成二维码
    const generateQR = async () => {
      if (!serializedData.value || !serializedData.value.session_id) {
        Toast.warning('请先序列化数据')
        return
      }
      
      try {
        loading.value = true
        updateProgress(10, '开始生成二维码...')
        
        const response = await generateQRCodes(serializedData.value.session_id, chunkSize.value)
        
        qrImages.value = response.data.qr_images.map(img => ({
          name: img.name,
          path: img.path,
          url: getQRCodeUrl(serializedData.value.session_id, img.name)
        }))
        
        currentQRIndex.value = 0
        updateProgress(100, '二维码生成成功')
        Toast.success(`生成了 ${qrImages.value.length} 个二维码`)
      } catch (err) {
        console.error('生成二维码失败', err)
        updateProgress(0, '生成二维码失败')
        Toast.error(`生成二维码失败: ${err.response?.data?.detail || err.message}`)
      } finally {
        loading.value = false
        setTimeout(() => {
          updateProgress(0, '就绪')
        }, 3000)
      }
    }
    
    // 获取二维码图片URL
    const getQRImageUrl = (index) => {
      if (index < 0 || index >= qrImages.value.length) return ''
      return qrImages.value[index].url
    }
    
    // 上一个二维码
    const prevQR = () => {
      if (currentQRIndex.value > 0) {
        currentQRIndex.value--
      }
    }
    
    // 下一个二维码
    const nextQR = () => {
      if (currentQRIndex.value < qrImages.value.length - 1) {
        currentQRIndex.value++
      }
    }
    
    // 保存所有二维码
    const saveAllQR = () => {
      if (!qrImages.value.length) {
        Toast.warning('没有可保存的二维码')
        return
      }
      
      qrImages.value.forEach((img, index) => {
        const link = document.createElement('a')
        link.href = img.url
        link.download = img.name
        link.target = '_blank'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        
        // 稍微延迟以避免浏览器下载管理器过载
        setTimeout(() => {}, 300 * index)
      })
      
      Toast.success(`已启动 ${qrImages.value.length} 个二维码图片的下载`)
    }
    
    // 处理扫描文件选择
    const handleScanFileChange = (file) => {
      scanFileList.value.push(file)
      scanFiles.value.push(file.raw)
    }
    
    // 处理视频文件选择
    const handleScanVideoChange = (file) => {
      scanVideoList.value = [file]
      scanVideo.value = file.raw
    }
    
    // 开始扫描恢复
    const startScanRestore = async () => {
      if (scanMode.value === 'image' && !scanFiles.value.length) {
        Toast.warning('请先选择二维码图片')
        return
      }
      
      if (scanMode.value === 'video' && !scanVideo.value) {
        Toast.warning('请先选择视频文件')
        return
      }
      
      if (scanMode.value === 'text' && !qrTextContent.value.trim()) {
        Toast.warning('请输入二维码文本内容')
        return
      }
      
      try {
        scanLoading.value = true
        scanProgress.value = 10
        scanProgressText.value = scanMode.value === 'image' ? '开始扫描图片...' : 
                               scanMode.value === 'video' ? '开始处理视频，这可能需要一些时间...' :
                               '开始处理文本内容...'
        
        let response
        
        // 如果是视频模式，显示额外的提示和进度模拟
        if (scanMode.value === 'video') {
          Toast.info('视频处理可能需要较长时间，请耐心等待')
          
          // 模拟进度更新，因为后端处理时无法实时获取进度
          let progressInterval = setInterval(() => {
            if (scanProgress.value < 90) {
              scanProgress.value += 5
              if (scanProgress.value < 30) {
                scanProgressText.value = '正在读取视频帧...'
              } else if (scanProgress.value < 60) {
                scanProgressText.value = '正在分析视频中的二维码...'
              } else {
                scanProgressText.value = '正在处理识别结果...'
              }
            }
          }, 3000)
          
          try {
            response = await scanVideoApi(scanVideo.value)
            clearInterval(progressInterval)
          } catch (err) {
            clearInterval(progressInterval)
            throw err
          }
        } else if (scanMode.value === 'text') {
          // 文本恢复模式
          scanProgressText.value = '处理文本内容...'
          scanProgress.value = 30
          
          // 处理文本内容，确保格式正确
          const textContent = qrTextContent.value.trim()
          console.log('提交文本恢复，文本长度:', textContent.length)
          
          // 处理文本内容
          try {
            response = await restoreFromText(textContent)
            console.log('文本恢复响应:', response)
          } catch (err) {
            console.error('文本恢复请求失败:', err)
            throw err
          }
          
          scanProgressText.value = '恢复文件...'
          scanProgress.value = 70
        } else {
          // 图片模式处理
          response = await scanRestore(scanFiles.value)
        }
        
        scanProgress.value = 100
        scanProgressText.value = '恢复成功'
        
        restoreResult.value = {
          success: true,
          message: `文件已成功恢复: ${response.data.filename}`,
          downloadPath: response.data.download_path,
          filename: response.data.filename
        }
        
        Toast.success(`${scanMode.value === 'image' ? '图片' : scanMode.value === 'video' ? '视频' : '文本'}扫描恢复成功`)
      } catch (err) {
        console.error('扫描恢复失败', err)
        scanProgress.value = 0
        scanProgressText.value = '扫描恢复失败'
        
        // 提取错误信息
        let errorMsg = '未知错误'
        if (err.response?.data?.detail) {
          errorMsg = err.response.data.detail
        } else if (err.message) {
          errorMsg = err.message
        }
        
        restoreResult.value = {
          success: false,
          message: `恢复失败: ${errorMsg}`
        }
        
        // 针对特定错误提供更多帮助
        if (errorMsg.includes('未找到二维码')) {
          restoreResult.value.message += '\n\n请确保视频中包含清晰可见的二维码，或尝试使用图片扫描模式。'
        } else if (errorMsg.includes('无法打开视频')) {
          restoreResult.value.message += '\n\n请检查视频文件格式是否受支持，或尝试转换为MP4格式。'
        } else if (scanMode.value === 'text' && (errorMsg.includes('数据不完整') || errorMsg.includes('合并文本数据失败'))) {
          restoreResult.value.message += '\n\n请检查文本内容是否完整，确保正确使用分号分隔不同二维码的内容。'
        }
        
        Toast.error(`扫描恢复失败: ${errorMsg}`)
      } finally {
        scanLoading.value = false
      }
    }
    
    // 下载恢复的文件
    const downloadRestoredFile = () => {
      if (!restoreResult.value || !restoreResult.value.success) return
      
      window.open(restoreResult.value.downloadPath, '_blank')
    }
    
    // 重置扫描数据
    const resetScanData = () => {
      scanFileList.value = []
      scanFiles.value = []
      scanVideoList.value = []
      scanVideo.value = null
      scanProgress.value = 0
      scanProgressText.value = ''
      restoreResult.value = null
      qrTextContent.value = ''
      sessionInput.value = ''
    }
    
    const getQRFilesBySessionId =async()=>{
        // 如果session_id为空，则提示
        if (!sessionInput.value) {
            Toast.warning('请输入session_id')
            return
        }
        // 根据输入框的session_id 获取
        try{
            const response = await getQRFilesBySessionIdApi(sessionInput.value)
            console.log(response)
            // 获取文件列表
            const files = response.data.files
            console.log(files)
            // 渲染到页面，显示二维码图片
        qrImages.value = files.map(file =>({
          name: file,
          path: file,
          url: getQRCodeUrl(sessionInput.value, file)
        }))
        currentQRIndex.value = 0

        Toast.success(`获取了 ${qrImages.value.length} 个二维码`)

        }catch(err){
            console.error('获取文件列表失败', err)
            Toast.error('获取文件列表失败')
        }
    }


    // 重置所有数据
    const resetData = () => {
      fileList.value = []
      selectedFile.value = null
      serializedData.value = null
      qrImages.value = []
      currentQRIndex.value = 0
      progress.value = 0
      progressText.value = '就绪'
    }
    
    // 监视模式变化
    watch(mode, () => {
      resetData()
    })
    
    return {
      // 基本状态
      mode,
      fileList,
      selectedFile,
      loading,
      progress,
      progressText,
      progressStatus,
      sessionInput,
      // Excel区域模式相关
      regionInput,
      selectedSheet,
      sheetList,
      
      // 二维码设置
      chunkSize,
      
      // 序列化数据
      serializedData,
      
      // 二维码图片
      qrImages,
      currentQRIndex,
      
      // 扫描恢复相关
      showScanModal,
      scanMode,
      scanFileList,
      scanFiles,
      scanVideoList,
      scanVideo,
      scanLoading,
      scanProgress,
      scanProgressText,
      restoreResult,
      qrTextContent,
      
      // 方法
      handleFileChange,
      serialize,
      generateQR,
      getQRImageUrl,
      prevQR,
      nextQR,
      saveAllQR,
      handleScanFileChange,
      handleScanVideoChange,
      startScanRestore,
      downloadRestoredFile,
      resetScanData,
      resetData,
      getQRFilesBySessionId
    }
  }
}
</script>

<style scoped>
.qrfile-container {
  width: 100%;
  padding: 20px;
  height: 100%;
}

.page-header {
  margin-bottom: 20px;
  text-align: center;
  position: relative;
}

.header-actions {
  position: absolute;
  top: 0;
  right: 0;
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
  gap: 20px;
  height: calc(100% - 80px);
}

.control-panel {
  flex: 0 0 350px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 20px;
  overflow-y: auto;
}

.preview-panel {
  flex: 1;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.panel-title, .section-title {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 18px;
  color: #333;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}

.panel-section {
  margin-bottom: 20px;
}

.setting-item {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
}

.setting-label {
  width: 90px;
  margin-right: 10px;
}

.mode-selector {
  margin-bottom: 15px;
}

.file-uploader {
  width: 100%;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.action-buttons .el-button {
  flex: 1 0 45%;
}

.progress-text {
  margin-top: 8px;
  font-size: 14px;
  color: #606266;
  text-align: center;
}

.sheet-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.qr-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.qr-navigation {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.qr-position {
  margin: 0 15px;
  font-weight: bold;
}

.qr-name {
  margin-left: 15px;
  color: #606266;
}

.qr-image-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background-color: #f7f7f7;
  border-radius: 4px;
}

.qr-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.loading-container, .no-qr-container {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
}

.scan-uploader {
  width: 100%;
  margin-bottom: 20px;
}

.scan-progress {
  margin: 20px 0;
}

.restore-result {
  margin-top: 20px;
}

.download-section {
  margin-top: 15px;
  text-align: center;
}

.scan-mode-selector {
  margin-bottom: 20px;
  text-align: center;
}

.scan-section {
  margin-bottom: 20px;
}

.video-tips {
  margin-top: 10px;
  text-align: center;
}

.text-restore-container {
  margin-bottom: 20px;
}

.text-restore-tips {
  margin-top: 10px;
  text-align: left;
}

@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
  }
  
  .control-panel {
    flex: initial;
    width: 100%;
  }
  .qr-image-container {
    margin: 20px 0;
  }
}
</style>