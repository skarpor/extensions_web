import {ElMessage} from "element-plus";

export const copyText = (text) => {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text)
    ElMessage.success('消息已复制到剪贴板')
  } else {
    // 兼容旧浏览器
    const textArea = document.createElement('textarea')
    textArea.value = text
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    ElMessage.success('消息已复制到剪贴板')
  }
}
