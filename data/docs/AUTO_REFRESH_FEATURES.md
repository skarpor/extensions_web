# 自动刷新功能说明

## 概述

现代化扩展工作台提供了两种不同的自动刷新功能，让用户可以根据需要选择合适的自动化方式。

## 🔄 自动刷新扩展列表

### 功能说明
定期刷新扩展列表，获取最新的扩展状态和信息。

### 适用场景
- **多人协作环境**：其他用户可能添加、删除或修改扩展
- **扩展开发调试**：开发过程中扩展文件可能发生变化
- **扩展状态监控**：监控扩展的启用/禁用状态变化
- **长时间使用**：确保扩展列表信息始终是最新的

### 配置选项
- **开关**：自动刷新扩展列表
- **间隔**：30-600秒（默认60秒）
- **说明**：定期刷新扩展列表，获取最新的扩展状态

### 刷新内容
```javascript
// 刷新的内容包括：
- 扩展列表
- 扩展状态（启用/禁用）
- 扩展配置信息
- 扩展描述和元数据
```

### 使用建议
- **开发环境**：建议开启，间隔设置为30-60秒
- **生产环境**：可选开启，间隔设置为120-300秒
- **个人使用**：通常不需要开启

## ⚡ 自动重新执行

### 功能说明
定期重新执行当前选中的扩展，获取最新的结果数据。

### 适用场景
- **实时监控**：系统状态、性能指标等需要实时更新的数据
- **数据仪表板**：定期更新图表和统计信息
- **状态检查**：定期检查服务状态、资源使用情况
- **自动化报告**：定期生成最新的报告数据

### 配置选项
- **开关**：自动重新执行
- **间隔**：10-300秒（默认30秒）
- **说明**：定期重新执行当前选中的扩展，获取最新结果
- **限制**：仅对无参数或使用默认参数的扩展有效

### 执行条件
```javascript
// 自动执行的条件：
1. 有选中的扩展
2. 扩展当前没有在执行中
3. 扩展没有查询表单（无需用户输入参数）
4. 或者扩展使用默认参数
```

### 使用建议
- **监控类扩展**：强烈建议开启，间隔10-60秒
- **报告类扩展**：可选开启，间隔60-300秒
- **交互类扩展**：不建议开启（需要用户输入）

## 🎯 使用场景对比

| 场景 | 扩展列表刷新 | 自动重新执行 | 推荐间隔 |
|------|-------------|-------------|----------|
| 系统监控仪表板 | ❌ | ✅ | 30秒 |
| 扩展开发调试 | ✅ | ❌ | 60秒 |
| 多人协作环境 | ✅ | ❌ | 120秒 |
| 实时数据展示 | ❌ | ✅ | 15秒 |
| 定期报告生成 | ❌ | ✅ | 300秒 |
| 个人日常使用 | ❌ | ❌ | - |

## ⚙️ 配置界面

### 设置位置
工作台右上角设置按钮 → 自动刷新配置

### 配置项说明
```
自动刷新扩展列表: [开关]
├── 说明: 定期刷新扩展列表，获取最新的扩展状态
└── 扩展列表刷新间隔: [30-600秒]

自动重新执行: [开关]  
├── 说明: 定期重新执行当前选中的扩展，获取最新结果
├── 重新执行间隔: [10-300秒]
└── 限制: 仅对无参数或使用默认参数的扩展有效
```

### 状态显示
设置对话框底部会显示当前的自动功能状态：
- 🔄 扩展列表自动刷新: 每60秒
- ⚡ 自动重新执行: 每30秒  
- 💤 未启用自动功能

## 🔧 技术实现

### 定时器管理
```javascript
// 定时器变量
const extensionRefreshTimer = ref(null)
const autoExecuteTimer = ref(null)

// 启动定时器
const startTimers = () => {
  stopTimers() // 先清除现有定时器
  
  if (workspaceSettings.autoRefreshExtensions) {
    extensionRefreshTimer.value = setInterval(() => {
      refreshExtensions()
    }, workspaceSettings.extensionRefreshInterval * 1000)
  }
  
  if (workspaceSettings.autoReExecute) {
    autoExecuteTimer.value = setInterval(() => {
      autoReExecuteExtension()
    }, workspaceSettings.reExecuteInterval * 1000)
  }
}

// 停止定时器
const stopTimers = () => {
  if (extensionRefreshTimer.value) {
    clearInterval(extensionRefreshTimer.value)
    extensionRefreshTimer.value = null
  }
  if (autoExecuteTimer.value) {
    clearInterval(autoExecuteTimer.value)
    autoExecuteTimer.value = null
  }
}
```

### 自动执行逻辑
```javascript
const autoReExecuteExtension = async () => {
  // 检查执行条件
  if (!selectedExtension.value || executing.value) {
    return
  }

  // 只对无查询表单的扩展自动执行
  if (selectedExtension.value.has_query_form) {
    console.log('跳过自动执行：扩展需要查询参数')
    return
  }

  try {
    await executeExtension()
    if (workspaceSettings.enableNotifications) {
      ElMessage.success(`${selectedExtension.value.name} 自动执行完成`)
    }
  } catch (error) {
    console.error('自动执行失败:', error)
  }
}
```

### 生命周期管理
```javascript
// 组件挂载时启动定时器
onMounted(() => {
  loadSettings()
  refreshExtensions()
  startTimers()
})

// 组件销毁时清理定时器
onUnmounted(() => {
  stopTimers()
  // 清理其他资源...
})

// 设置变更时重新启动定时器
const saveSettings = (newSettings) => {
  Object.assign(workspaceSettings, newSettings)
  saveSettingsToStorage()
  startTimers() // 重新启动定时器
  ElMessage.success('设置已保存')
}
```

## 📊 性能考虑

### 资源使用
- **扩展列表刷新**：轻量级操作，网络请求较小
- **自动重新执行**：取决于扩展复杂度，可能消耗较多资源

### 优化建议
1. **合理设置间隔**：避免过于频繁的刷新
2. **按需启用**：只在必要时启用自动功能
3. **监控性能**：注意观察系统资源使用情况
4. **错误处理**：自动执行失败不会影响手动操作

## 🎯 最佳实践

### 推荐配置
```javascript
// 开发环境
{
  autoRefreshExtensions: true,
  extensionRefreshInterval: 60,
  autoReExecute: false,
  reExecuteInterval: 30
}

// 监控环境  
{
  autoRefreshExtensions: false,
  extensionRefreshInterval: 120,
  autoReExecute: true,
  reExecuteInterval: 30
}

// 生产环境
{
  autoRefreshExtensions: false,
  extensionRefreshInterval: 300,
  autoReExecute: true,
  reExecuteInterval: 60
}
```

### 使用技巧
1. **监控类扩展**：开启自动重新执行，关闭扩展列表刷新
2. **开发调试**：开启扩展列表刷新，关闭自动重新执行
3. **演示展示**：开启自动重新执行，设置较短间隔
4. **日常使用**：根据需要选择性开启

## 🔍 故障排除

### 常见问题
1. **自动执行不工作**
   - 检查扩展是否有查询表单
   - 确认扩展没有在执行中
   - 查看控制台日志

2. **扩展列表不更新**
   - 检查网络连接
   - 确认后端服务正常
   - 查看浏览器开发者工具

3. **性能问题**
   - 适当增加刷新间隔
   - 关闭不必要的自动功能
   - 检查扩展执行效率

### 调试方法
```javascript
// 在浏览器控制台查看日志
console.log('自动刷新扩展列表')
console.log('自动重新执行扩展: ' + extensionName)
console.log('跳过自动执行：扩展需要查询参数')
```

通过合理配置和使用这两种自动刷新功能，可以大大提升扩展工作台的使用体验和工作效率！
