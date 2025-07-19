/**
 * 扩展适配器 - 统一处理不同类型扩展的数据格式和显示逻辑
 */

/**
 * 标准化扩展结果数据
 * @param {*} result - 扩展返回的原始结果
 * @param {Object} extension - 扩展信息
 * @returns {Object} 标准化后的结果
 */
export function normalizeExtensionResult(result, extension) {
  // 检查是否是标准格式
  if (result && typeof result === 'object' && result.type && result.data !== undefined) {
    return {
      type: result.type,
      data: result.data,
      meta: result.meta || {},
      extension: extension
    }
  }

  // 根据扩展的render_type进行适配
  const renderType = extension?.render_type || 'text'
  
  return {
    type: renderType,
    data: adaptDataByType(result, renderType),
    meta: extractMetaData(result, renderType),
    extension: extension
  }
}

/**
 * 根据类型适配数据
 * @param {*} data - 原始数据
 * @param {string} type - 数据类型
 * @returns {*} 适配后的数据
 */
function adaptDataByType(data, type) {
  switch (type) {
    case 'html':
      return typeof data === 'string' ? data : JSON.stringify(data, null, 2)
    
    case 'table':
      if (Array.isArray(data)) {
        return data
      } else if (data && typeof data === 'object') {
        // 将对象转换为表格格式
        return Object.entries(data).map(([key, value]) => ({
          键: key,
          值: value
        }))
      }
      return []
    
    case 'text':
      if (typeof data === 'string') {
        return data
      } else if (data && typeof data === 'object') {
        return JSON.stringify(data, null, 2)
      }
      return String(data)
    
    case 'file':
      if (data && typeof data === 'object' && data.file_path) {
        return data
      }
      return {
        filename: 'unknown_file',
        content_type: 'application/octet-stream',
        content: data
      }
    
    case 'chart':
      if (data && typeof data === 'object' && data.chart_data) {
        return data
      }
      // 尝试将数据转换为简单的图表格式
      return convertToChartData(data)
    
    case 'image':
      return data
    
    default:
      return data
  }
}

/**
 * 提取元数据
 * @param {*} data - 原始数据
 * @param {string} type - 数据类型
 * @returns {Object} 元数据
 */
function extractMetaData(data, type) {
  const meta = {
    generated_at: new Date().toISOString(),
    data_type: type,
    original_type: typeof data
  }

  if (Array.isArray(data)) {
    meta.item_count = data.length
  } else if (typeof data === 'string') {
    meta.character_count = data.length
    meta.line_count = data.split('\n').length
  } else if (data && typeof data === 'object') {
    meta.field_count = Object.keys(data).length
  }

  return meta
}

/**
 * 将数据转换为图表格式
 * @param {*} data - 原始数据
 * @returns {Object} 图表配置
 */
function convertToChartData(data) {
  if (Array.isArray(data)) {
    // 数组数据转换为柱状图
    const labels = data.map((_, index) => `项目${index + 1}`)
    const values = data.map(item => {
      if (typeof item === 'number') return item
      if (item && typeof item === 'object') {
        // 尝试找到数值字段
        const numericValue = Object.values(item).find(v => typeof v === 'number')
        return numericValue || 0
      }
      return 0
    })

    return {
      chart_type: 'bar',
      chart_data: {
        labels: labels,
        datasets: [{
          label: '数据',
          data: values,
          backgroundColor: '#4ecdc4',
          borderColor: '#45b7d1',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: '数据可视化'
          }
        },
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }
    }
  } else if (data && typeof data === 'object') {
    // 对象数据转换为饼图
    const entries = Object.entries(data).filter(([_, value]) => typeof value === 'number')
    
    if (entries.length > 0) {
      return {
        chart_type: 'pie',
        chart_data: {
          labels: entries.map(([key]) => key),
          datasets: [{
            data: entries.map(([_, value]) => value),
            backgroundColor: [
              '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57',
              '#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3', '#ff9f43'
            ]
          }]
        },
        options: {
          responsive: true,
          plugins: {
            title: {
              display: true,
              text: '数据分布'
            }
          }
        }
      }
    }
  }

  // 默认返回空图表
  return {
    chart_type: 'bar',
    chart_data: {
      labels: ['无数据'],
      datasets: [{
        label: '数据',
        data: [0],
        backgroundColor: '#e9ecef'
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: '暂无可视化数据'
        }
      }
    }
  }
}

/**
 * 获取扩展类型的显示配置
 * @param {string} type - 扩展类型
 * @returns {Object} 显示配置
 */
export function getTypeDisplayConfig(type) {
  const configs = {
    html: {
      icon: 'Document',
      label: 'HTML页面',
      color: 'primary',
      description: '渲染HTML内容',
      features: ['直接渲染', '样式支持', '交互元素']
    },
    table: {
      icon: 'Grid',
      label: '数据表格',
      color: 'success',
      description: '表格化数据展示',
      features: ['排序', '分页', '导出', '搜索']
    },
    text: {
      icon: 'Memo',
      label: '文本报告',
      color: 'info',
      description: '纯文本内容',
      features: ['复制', '搜索', '全屏', '统计']
    },
    file: {
      icon: 'Files',
      label: '文件下载',
      color: 'warning',
      description: '生成文件供下载',
      features: ['下载', '预览', '格式转换']
    },
    chart: {
      icon: 'TrendCharts',
      label: '交互图表',
      color: 'danger',
      description: '数据可视化图表',
      features: ['多种图表', '交互', '导出', '数据表格']
    },
    image: {
      icon: 'Picture',
      label: '图片图表',
      color: 'purple',
      description: '图片格式的可视化',
      features: ['缩放', '下载', '全屏']
    }
  }

  return configs[type] || {
    icon: 'Operation',
    label: '未知类型',
    color: 'info',
    description: '未知的扩展类型',
    features: []
  }
}

/**
 * 验证扩展结果格式
 * @param {*} result - 扩展结果
 * @returns {Object} 验证结果
 */
export function validateExtensionResult(result) {
  const validation = {
    valid: true,
    errors: [],
    warnings: []
  }

  if (!result) {
    validation.valid = false
    validation.errors.push('结果为空')
    return validation
  }

  if (typeof result !== 'object') {
    validation.warnings.push('结果不是对象格式，将进行自动适配')
    return validation
  }

  if (!result.type) {
    validation.warnings.push('缺少type字段，将根据扩展配置推断')
  }

  if (result.data === undefined) {
    validation.warnings.push('缺少data字段，将使用整个结果作为数据')
  }

  // 根据类型验证数据格式
  if (result.type && result.data !== undefined) {
    switch (result.type) {
      case 'table':
        if (!Array.isArray(result.data)) {
          validation.errors.push('table类型的data字段必须是数组')
          validation.valid = false
        }
        break
      case 'chart':
        if (!result.data.chart_data && !result.data.chart_type) {
          validation.warnings.push('chart类型缺少chart_data或chart_type字段')
        }
        break
      case 'file':
        if (!result.data.filename && !result.data.file_path) {
          validation.warnings.push('file类型缺少filename或file_path字段')
        }
        break
    }
  }

  return validation
}

/**
 * 格式化扩展执行时间
 * @param {number} startTime - 开始时间戳
 * @param {number} endTime - 结束时间戳
 * @returns {string} 格式化的执行时间
 */
export function formatExecutionTime(startTime, endTime) {
  const duration = endTime - startTime
  
  if (duration < 1000) {
    return `${duration}ms`
  } else if (duration < 60000) {
    return `${(duration / 1000).toFixed(1)}s`
  } else {
    const minutes = Math.floor(duration / 60000)
    const seconds = Math.floor((duration % 60000) / 1000)
    return `${minutes}m ${seconds}s`
  }
}
