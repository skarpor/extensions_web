<template>
  <div id="danmu-container" ref="danmuContainer">
    <!-- 弹幕元素会动态添加到这里 -->
    
    <!-- 控制面板 -->
    <div id="control-panel">
      <input 
        type="text" 
        id="danmu-input" 
        v-model="inputText"
        @keypress="handleKeyPress"
        placeholder="输入弹幕内容..."
        ref="danmuInput"
      >
      <button
        id="send-btn"
        @click="sendDanmu"
        :disabled="!inputText.trim() || !isConnected"
      >
        {{ isConnected ? '发送' : '连接中...' }}
      </button>
      <button
        id="test-btn"
        @click="testDanmu"
        style="margin-left: 10px; padding: 8px 16px; background-color: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;"
      >
        测试弹幕
      </button>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { useToast } from 'vue-toastification'

export default {
  name: 'Danmu',
  setup() {
    const toast = useToast()
    const danmuContainer = ref(null)
    const danmuInput = ref(null)
    const inputText = ref('')
    const isConnected = ref(false)
    
    let danmuSocket = null
    let heartbeatTimer = null

    // WebSocket连接初始化
    const initWebSocket = async () => {
      if (danmuSocket && danmuSocket.readyState === WebSocket.OPEN) {
        return
      }

      try {
        // 获取当前域名和协议
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const host = window.location.host
        const wsUrl = `${protocol}//localhost:8000/api/danmu/ws`
        console.log('Connecting to WebSocket:', wsUrl)
        
        danmuSocket = new WebSocket(wsUrl)

        danmuSocket.onopen = () => {
          console.log("弹幕WebSocket连接已建立")
          isConnected.value = true
          sendHeartbeat()
        }

        danmuSocket.onmessage = async (event) => {
          if (event.data === "ping") {
            return
          }

          try {
            const danmu = JSON.parse(event.data)
            await createDanmu(danmu.text, danmu.color)
          } catch (error) {
            console.error('解析弹幕数据失败:', error)
          }
        }

        danmuSocket.onclose = () => {
          console.log("弹幕连接关闭，5秒后重连...")
          isConnected.value = false
          clearTimeout(heartbeatTimer)
          setTimeout(initWebSocket, 5000)
        }

        danmuSocket.onerror = (error) => {
          console.error("弹幕WebSocket错误:", error)
          isConnected.value = false
        }
      } catch (error) {
        console.error('WebSocket连接失败:', error)
        isConnected.value = false
        setTimeout(initWebSocket, 5000)
      }
    }

    // 心跳保持
    const sendHeartbeat = () => {
      if (danmuSocket && danmuSocket.readyState === WebSocket.OPEN) {
        danmuSocket.send("ping")
        heartbeatTimer = setTimeout(sendHeartbeat, 25000) // 25秒一次心跳
      }
    }

    // 随机生成Y轴位置
    const getRandomY = () => {
      return Math.floor(Math.random() * (window.innerHeight - 30))
    }

    // 创建弹幕元素
    const createDanmu = async (text, color) => {
      // 确保组件已经挂载
      await nextTick()

      if (!danmuContainer.value) {
        console.error('danmuContainer is null, component may not be mounted yet')
        return
      }

      const danmu = document.createElement('div')
      danmu.className = 'danmu'
      danmu.textContent = text
      danmu.style.color = color
      danmu.style.left = `${window.innerWidth}px`
      danmu.style.top = `${getRandomY()}px`

      danmuContainer.value.appendChild(danmu)

      // 弹幕动画
      const duration = 10000 // 10秒
      const startTime = Date.now()

      const animate = () => {
        const elapsed = Date.now() - startTime
        const progress = elapsed / duration

        if (progress >= 1) {
          if (danmu.parentNode) {
            danmu.parentNode.removeChild(danmu)
          }
          return
        }

        const x = window.innerWidth - (window.innerWidth + danmu.offsetWidth) * progress
        danmu.style.left = `${x}px`
        requestAnimationFrame(animate)
      }

      requestAnimationFrame(animate)
    }

    // 发送弹幕
    const sendDanmu = async () => {
      const text = inputText.value.trim()
      if (!text) return

      if (!danmuSocket || danmuSocket.readyState !== WebSocket.OPEN) {
        toast.error("弹幕连接未就绪")
        await initWebSocket()
        return
      }

      const color = "#" + Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0')

      try {
        const response = await fetch('/send_danmu', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text: text,
            color: color
          })
        })

        if (!response.ok) {
          throw new Error(`HTTP错误! 状态码: ${response.status}`)
        }

        inputText.value = ''
        toast.success('弹幕发送成功')
      } catch (error) {
        console.error('发送失败:', error)
        toast.error('发送弹幕失败')
      }
    }

    // 测试弹幕功能
    const testDanmu = async () => {
      const testTexts = ['测试弹幕1', '测试弹幕2', 'Hello World!', '这是一个测试']
      const testColors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff']

      const randomText = testTexts[Math.floor(Math.random() * testTexts.length)]
      const randomColor = testColors[Math.floor(Math.random() * testColors.length)]

      console.log('Creating test danmu:', randomText, randomColor)
      await createDanmu(randomText, randomColor)
    }

    // 处理键盘事件
    const handleKeyPress = (e) => {
      if (e.key === 'Enter') {
        sendDanmu()
      }
    }

    onMounted(async () => {
      // 确保DOM已经渲染
      await nextTick()

      // 检查容器是否正确挂载
      if (!danmuContainer.value) {
        console.error('danmuContainer failed to mount')
        return
      }

      console.log('danmuContainer mounted successfully:', danmuContainer.value)

      // 初始化WebSocket
      initWebSocket()

      // 聚焦输入框
      if (danmuInput.value) {
        danmuInput.value.focus()
      }
    })

    onUnmounted(() => {
      if (danmuSocket) {
        danmuSocket.close()
      }
      if (heartbeatTimer) {
        clearTimeout(heartbeatTimer)
      }
    })

    return {
      danmuContainer,
      danmuInput,
      inputText,
      isConnected,
      sendDanmu,
      testDanmu,
      handleKeyPress
    }
  }
}
</script>

<style scoped>
#danmu-container {
  position: relative;
  width: 100vw;
  height: 100vh;
  background-color: #000;
  overflow: hidden;
}

:deep(.danmu) {
  position: absolute;
  white-space: nowrap;
  font-size: 24px;
  font-weight: bold;
  text-shadow: 1px 1px 2px #000;
  pointer-events: none;
  z-index: 1;
}

#control-panel {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 10px;
  z-index: 100;
}

#danmu-input {
  width: 300px;
  padding: 8px;
  border-radius: 4px;
  border: none;
  outline: none;
}

#send-btn {
  padding: 8px 16px;
  background-color: #ff5500;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

#send-btn:hover:not(:disabled) {
  background-color: #ff7733;
}

#send-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

/* 全屏样式 */
body {
  margin: 0;
  padding: 0;
  font-family: Arial, sans-serif;
  background-color: #000;
  overflow: hidden;
}
</style>

<style>
/* 全局样式，确保页面全屏 */
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  overflow: hidden;
}

#app {
  height: 100vh;
}
</style>
