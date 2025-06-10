<template>
  <div class="table-editor">
    <h3>{{ isEdit ? '编辑表结构' : '创建新表' }}</h3>
    
    <div class="table-info mb-4">
      <div class="row">
        <div class="col-md-6">
          <div class="form-group">
            <label>表名</label>
            <input 
              v-model="tableName" 
              class="form-control" 
              placeholder="输入表名" 
              :disabled="isEdit"
            />
          </div>
        </div>
        
        <div class="col-md-6">
          <div class="form-group">
            <label>表描述</label>
            <input v-model="tableDescription" class="form-control" placeholder="表的用途描述" />
          </div>
        </div>
      </div>
    </div>
    
    <h4>字段定义</h4>
    <div class="columns-container">
      <div v-for="(column, index) in columns" :key="index" class="column-row border p-3 mb-3 rounded">
        <!-- 基本属性 -->
        <div class="row mb-3">
          <div class="col-md-3">
            <label>字段名</label>
            <input v-model="column.name" class="form-control" placeholder="字段名" />
          </div>
          
          <div class="col-md-3">
            <label>数据类型</label>
            <select v-model="column.type" class="form-select">
              <option value="integer">整数</option>
              <option value="string">字符串</option>
              <option value="text">文本</option>
              <option value="float">浮点数</option>
              <option value="boolean">布尔值</option>
              <option value="datetime">日期时间</option>
            </select>
          </div>
          
          <div class="col-md-3" v-if="column.type === 'string'">
            <label>长度</label>
            <input v-model.number="column.length" type="number" class="form-control" />
          </div>
          
          <div class="col-md-3" v-if="['integer', 'float'].includes(column.type)">
            <label>精度</label>
            <input v-model.number="column.precision" type="number" class="form-control" />
          </div>
        </div>
        
        <!-- 约束条件 -->
        <div class="row mb-3">
          <div class="col-md-3">
            <div class="form-check">
              <input v-model="column.primary_key" class="form-check-input" type="checkbox" :id="`pk-${index}`">
              <label class="form-check-label" :for="`pk-${index}`">主键</label>
            </div>
          </div>
          
          <div class="col-md-3">
            <div class="form-check">
              <input v-model="column.nullable" class="form-check-input" type="checkbox" :id="`null-${index}`">
              <label class="form-check-label" :for="`null-${index}`">可空</label>
            </div>
          </div>
          
          <div class="col-md-3">
            <div class="form-check">
              <input v-model="column.unique" class="form-check-input" type="checkbox" :id="`unique-${index}`">
              <label class="form-check-label" :for="`unique-${index}`">唯一</label>
            </div>
          </div>
          
          <div class="col-md-3">
            <div class="form-check" v-if="column.type === 'integer' && column.primary_key">
              <input v-model="column.auto_increment" class="form-check-input" type="checkbox" :id="`auto-${index}`">
              <label class="form-check-label" :for="`auto-${index}`">自增</label>
            </div>
          </div>
        </div>
        
        <!-- 高级选项 -->
        <div class="row mb-3">
          <div class="col-md-4">
            <label>默认值</label>
            <input v-model="column.default" class="form-control" placeholder="默认值" />
          </div>
          
          <div class="col-md-4">
            <label>注释</label>
            <input v-model="column.comment" class="form-control" placeholder="字段说明" />
          </div>
          
          <div class="col-md-3 d-flex align-items-end">
            <button class="btn btn-danger" @click="removeColumn(index)">
              <i class="fas fa-trash"></i> 删除字段
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <div class="actions mt-4">
      <button class="btn btn-outline-primary me-2" @click="addColumn">
        <i class="fas fa-plus"></i> 添加字段
      </button>
      
      <button class="btn btn-success" @click="saveTable">
        <i class="fas fa-save"></i> {{ isEdit ? '保存修改' : '创建表' }}
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue';
import { useToast } from 'vue-toastification';
import axios from 'axios';

export default {
  name: 'DbTableEditor',
  props: {
    tableData: {
      type: Object,
      default: null
    },
    isEdit: {
      type: Boolean,
      default: false
    }
  },
  emits: ['saved', 'cancel'],
  setup(props, { emit }) {
    const toast = useToast();
    
    // 表基本信息
    const tableName = ref(props.tableData?.original_name || '');
    const tableDescription = ref(props.tableData?.description || '');
    
    // 列定义
    const columns = ref([]);
    
    // 初始化列数据
    const initColumns = () => {
      if (props.isEdit && props.tableData?.columns?.length) {
        columns.value = props.tableData.columns.map(col => ({
          name: col.name,
          type: col.type,
          primary_key: col.primary_key,
          nullable: col.nullable,
          unique: col.unique,
          default: col.default,
          comment: col.comment,
          length: col.type === 'string' ? 255 : undefined,
          precision: ['integer', 'float'].includes(col.type) ? undefined : undefined,
          auto_increment: col.primary_key && col.type === 'integer'
        }));
      } else {
        // 默认添加一个ID列
        columns.value = [{
          name: 'id',
          type: 'integer',
          primary_key: true,
          nullable: false,
          unique: true,
          default: null,
          comment: '主键ID',
          auto_increment: true
        }];
      }
    };
    
    // 调用初始化
    initColumns();
    
    // 添加列
    const addColumn = () => {
      columns.value.push({
        name: '',
        type: 'string',
        primary_key: false,
        nullable: true,
        unique: false,
        default: null,
        comment: '',
        length: 255
      });
    };
    
    // 删除列
    const removeColumn = (index) => {
      // 确保至少保留一列
      if (columns.value.length > 1) {
        columns.value.splice(index, 1);
      } else {
        toast.warning('表至少需要一列');
      }
    };
    
    // 保存表
    const saveTable = async () => {
      try {
        // 验证表名
        if (!tableName.value.trim()) {
          toast.error('请输入表名');
          return;
        }
        
        // 验证列名
        for (const col of columns.value) {
          if (!col.name.trim()) {
            toast.error('列名不能为空');
            return;
          }
        }
        
        // 验证主键
        const hasPrimaryKey = columns.value.some(col => col.primary_key);
        if (!hasPrimaryKey) {
          toast.error('表必须至少有一个主键');
          return;
        }
        
        // 准备要提交的列数据
        const columnsData = columns.value.map(col => {
          const data = {
            name: col.name,
            type: col.type,
            primary_key: col.primary_key,
            nullable: col.nullable,
            unique: col.unique,
            comment: col.comment || undefined
          };
          
          // 添加类型特定的属性
          if (col.type === 'string' && col.length) {
            data.length = col.length;
          }
          
          if (col.default !== null && col.default !== undefined && col.default !== '') {
            data.default = col.default;
          }
          
          // 处理自增主键
          if (col.type === 'integer' && col.primary_key && col.auto_increment) {
            data.auto_increment = true;
          }
          
          return data;
        });
        
        if (props.isEdit) {
          // 编辑已有表
          await axios.put(`/api/v1/db/tables/${props.tableData.name}`, {
            columns: columnsData,
            description: tableDescription.value
          });
          
          toast.success('表结构修改成功');
        } else {
          // 创建新表
          await axios.post(`/api/v1/db/tables`, {
            table_name: tableName.value,
            schema: {
              columns: columnsData,
              description: tableDescription.value
            }
          });
          
          toast.success('表创建成功');
        }
        
        emit('saved');
      } catch (error) {
        console.error('保存表失败:', error);
        toast.error(error.response?.data?.detail || '保存表失败');
      }
    };
    
    return {
      tableName,
      tableDescription,
      columns,
      addColumn,
      removeColumn,
      saveTable
    };
  }
};
</script>

<style scoped>
.table-editor {
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.column-row {
  background-color: white;
}
</style> 