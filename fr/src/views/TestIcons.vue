<template>
  <div class="test-icons">
    <h2>Element Plus 图标测试</h2>
    
    <div class="icon-grid">
      <div class="icon-item">
        <el-icon><Refresh /></el-icon>
        <span>Refresh</span>
      </div>
      
      <div class="icon-item">
        <el-icon><Document /></el-icon>
        <span>Document</span>
      </div>
      
      <div class="icon-item">
        <el-icon><List /></el-icon>
        <span>List</span>
      </div>
      
      <div class="icon-item">
        <el-icon><EditPen /></el-icon>
        <span>EditPen</span>
      </div>
      
      <div class="icon-item">
        <el-icon><Link /></el-icon>
        <span>Link</span>
      </div>
      
      <div class="icon-item">
        <el-icon><Picture /></el-icon>
        <span>Picture</span>
      </div>
      
      <div class="icon-item">
        <el-icon><Grid /></el-icon>
        <span>Grid</span>
      </div>
      
      <div class="icon-item">
        <el-icon><Folder /></el-icon>
        <span>Folder</span>
      </div>
      
      <div class="icon-item">
        <el-icon><Delete /></el-icon>
        <span>Delete</span>
      </div>
      
      <div class="icon-item">
        <el-icon><Plus /></el-icon>
        <span>Plus</span>
      </div>
    </div>
    
    <div class="test-buttons">
      <el-button @click="$router.push('/markdown')">
        <el-icon><EditPen /></el-icon>
        前往 Markdown 编辑器
      </el-button>
    </div>
  </div>
</template>

<script>
import { 
  Refresh, 
  Document, 
  List,
  EditPen,
  Link, 
  Picture,
  Grid,
  Folder,
  Delete,
  Plus
} from '@element-plus/icons-vue'

export default {
  name: 'TestIcons',
  components: {
    Refresh,
    Document,
    List,
    EditPen,
    Link,
    Picture,
    Grid,
    Folder,
    Delete,
    Plus
  }
}
</script>

<style scoped>
.test-icons {
  padding: 20px;
}

.icon-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.icon-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 15px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #fafbfc;
}

.icon-item .el-icon {
  font-size: 24px;
  margin-bottom: 8px;
  color: #409eff;
}

.icon-item span {
  font-size: 12px;
  color: #606266;
}

.test-buttons {
  margin-top: 30px;
  text-align: center;
}
</style>
