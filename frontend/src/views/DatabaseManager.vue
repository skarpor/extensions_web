<template>
  <div class="database-manager">
    <h1>数据库管理</h1>
    
    <div class="row mb-4">
      <div class="col-md-8">
        <div class="input-group">
          <input 
            v-model="searchQuery" 
            class="form-control" 
            placeholder="搜索表..." 
            @input="filterTables"
          />
          <button class="btn btn-outline-secondary" @click="filterTables">
            <i class="fas fa-search"></i>
          </button>
        </div>
      </div>
      
      <div class="col-md-4 text-end">
        <button 
          class="btn btn-primary" 
          @click="showCreateTableModal"
          v-if="userCan('manage_extension_db')"
        >
          <i class="fas fa-plus"></i> 创建新表
        </button>
      </div>
    </div>
    
    <div v-if="loading" class="text-center my-5">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">加载中...</span>
      </div>
      <p class="mt-2">正在加载数据库表...</p>
    </div>
    
    <div v-else-if="tables.length === 0" class="alert alert-info">
      <i class="fas fa-info-circle me-2"></i> 暂无表，请创建新表
    </div>
    
    <div v-else class="table-responsive">
      <table class="table table-hover">
        <thead class="table-light">
          <tr>
            <th>表名</th>
            <th>描述</th>
            <th>记录数</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="table in filteredTables" :key="table.name">
            <td>{{ table.display_name }}</td>
            <td>{{ table.description || '无描述' }}</td>
            <td>{{ table.record_count || 0 }}</td>
            <td>{{ formatDate(table.created_at) }}</td>
            <td>
              <div class="btn-group">
                <button 
                  class="btn btn-sm btn-outline-primary" 
                  @click="viewTableData(table)"
                  title="查看数据"
                >
                  <i class="fas fa-table"></i>
                </button>
                
                <button 
                  class="btn btn-sm btn-outline-secondary" 
                  @click="viewTableSchema(table)"
                  title="查看结构"
                >
                  <i class="fas fa-code"></i>
                </button>
                
                <button 
                  v-if="userCan('manage_extension_db')"
                  class="btn btn-sm btn-outline-warning" 
                  @click="editTable(table)"
                  title="编辑表"
                >
                  <i class="fas fa-edit"></i>
                </button>
                
                <button 
                  v-if="userCan('manage_extension_db')"
                  class="btn btn-sm btn-outline-danger" 
                  @click="confirmDeleteTable(table)"
                  title="删除表"
                >
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- 创建/编辑表模态框 -->
    <div v-if="showTableEditor" class="modal fade show" style="display: block;">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ editingTable ? '编辑表' : '创建新表' }}</h5>
            <button type="button" class="btn-close" @click="closeTableEditor"></button>
          </div>
          
          <div class="modal-body">
            <div v-if="editingTable">
              <db-table-editor 
                :table-data="editingTable" 
                :is-edit="!!editingTable"
                @saved="handleTableSaved"
                @cancel="closeTableEditor"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 表数据查看模态框 -->
    <div v-if="showTableData" class="modal fade show" style="display: block;">
      <div class="modal-dialog modal-xl modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ currentTable?.display_name }} - 数据</h5>
            <button type="button" class="btn-close" @click="closeTableData"></button>
          </div>
          
          <div class="modal-body">
            <div class="mb-3">
              <div class="input-group">
                <input 
                  v-model="dataSearchQuery" 
                  class="form-control" 
                  placeholder="搜索数据..." 
                  @keyup.enter="searchTableData"
                />
                <button class="btn btn-outline-secondary" @click="searchTableData">
                  <i class="fas fa-search"></i>
                </button>
              </div>
            </div>
            
            <div v-if="loadingTableData" class="text-center my-5">
              <div class="spinner-border" role="status">
                <span class="visually-hidden">加载中...</span>
              </div>
              <p class="mt-2">正在加载数据...</p>
            </div>
            
            <div v-else-if="tableData.length === 0" class="alert alert-info">
              <i class="fas fa-info-circle me-2"></i> 表中没有数据
            </div>
            
            <div v-else class="table-responsive">
              <table class="table table-striped table-bordered">
                <thead class="table-dark">
                  <tr>
                    <th v-for="column in tableColumns" :key="column.name">
                      {{ column.name }}
                    </th>
                    <th v-if="userCan('manage_extension_db')">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, index) in tableData" :key="index">
                    <td v-for="column in tableColumns" :key="column.name">
                      {{ formatCellValue(row[column.name]) }}
                    </td>
                    <td v-if="userCan('manage_extension_db')">
                      <div class="btn-group">
                        <button 
                          class="btn btn-sm btn-outline-warning" 
                          @click="editRecord(row)"
                          title="编辑"
                        >
                          <i class="fas fa-edit"></i>
                        </button>
                        <button 
                          class="btn btn-sm btn-outline-danger" 
                          @click="deleteRecord(row)"
                          title="删除"
                        >
                          <i class="fas fa-trash"></i>
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <!-- 分页控件 -->
            <div class="d-flex justify-content-between align-items-center mt-3">
              <div>
                显示 {{ tableData.length }} 条记录，共 {{ totalRecords }} 条
              </div>
              <nav aria-label="Page navigation">
                <ul class="pagination">
                  <li class="page-item" :class="{ disabled: currentPage === 1 }">
                    <a class="page-link" @click="changePage(1)">首页</a>
                  </li>
                  <li class="page-item" :class="{ disabled: currentPage === 1 }">
                    <a class="page-link" @click="changePage(currentPage - 1)">上一页</a>
                  </li>
                  <li 
                    v-for="page in pageRange" 
                    :key="page" 
                    class="page-item"
                    :class="{ active: currentPage === page }"
                  >
                    <a class="page-link" @click="changePage(page)">{{ page }}</a>
                  </li>
                  <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                    <a class="page-link" @click="changePage(currentPage + 1)">下一页</a>
                  </li>
                  <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                    <a class="page-link" @click="changePage(totalPages)">末页</a>
                  </li>
                </ul>
              </nav>
            </div>
          </div>
          
          <div class="modal-footer">
            <button 
              v-if="userCan('manage_extension_db')"
              class="btn btn-success" 
              @click="showAddRecordForm"
            >
              <i class="fas fa-plus"></i> 添加记录
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 表结构查看模态框 -->
    <div v-if="showSchema" class="modal fade show" style="display: block;">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ currentTable?.display_name }} - 表结构</h5>
            <button type="button" class="btn-close" @click="closeSchema"></button>
          </div>
          
          <div class="modal-body">
            <div v-if="loadingSchema" class="text-center my-5">
              <div class="spinner-border" role="status">
                <span class="visually-hidden">加载中...</span>
              </div>
              <p class="mt-2">正在加载表结构...</p>
            </div>
            
            <div v-else>
              <div class="table-responsive">
                <table class="table table-bordered">
                  <thead class="table-secondary">
                    <tr>
                      <th>字段名</th>
                      <th>类型</th>
                      <th>约束</th>
                      <th>默认值</th>
                      <th>说明</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="column in tableColumns" :key="column.name">
                      <td>{{ column.name }}</td>
                      <td>{{ formatColumnType(column) }}</td>
                      <td>
                        <span v-if="column.primary_key" class="badge bg-primary me-1">主键</span>
                        <span v-if="column.unique" class="badge bg-info me-1">唯一</span>
                        <span v-if="column.nullable" class="badge bg-secondary me-1">可空</span>
                        <span v-if="column.auto_increment" class="badge bg-success me-1">自增</span>
                      </td>
                      <td>{{ column.default || '-' }}</td>
                      <td>{{ column.comment || '-' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              
              <div class="mt-4">
                <h5>SQL 创建语句</h5>
                <pre class="bg-dark text-light p-3 rounded">{{ schemaSQL }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 删除确认模态框 -->
    <div v-if="showDeleteConfirm" class="modal fade show" style="display: block;">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">确认删除</h5>
            <button type="button" class="btn-close" @click="cancelDelete"></button>
          </div>
          
          <div class="modal-body">
            <p>确定要删除表 <strong>{{ tableToDelete?.display_name }}</strong> 吗？</p>
            <div class="alert alert-danger">
              <i class="fas fa-exclamation-triangle me-2"></i> 此操作将删除表及其所有数据，且不可恢复！
            </div>
          </div>
          
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="cancelDelete">取消</button>
            <button class="btn btn-danger" @click="deleteTable">确认删除</button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 遮罩层 -->
    <div v-if="showTableEditor || showTableData || showSchema || showDeleteConfirm" class="modal-backdrop fade show"></div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useToast } from 'vue-toastification';
import axios from 'axios';
import DbTableEditor from '../components/DbTableEditor.vue';

export default {
  name: 'DatabaseManager',
  components: {
    DbTableEditor
  },
  setup() {
    const toast = useToast();
    
    // 表格数据
    const tables = ref([]);
    const loading = ref(true);
    const searchQuery = ref('');
    const filteredTables = ref([]);
    
    // 表编辑
    const showTableEditor = ref(false);
    const editingTable = ref(null);
    
    // 表数据查看
    const showTableData = ref(false);
    const currentTable = ref(null);
    const tableData = ref([]);
    const tableColumns = ref([]);
    const loadingTableData = ref(false);
    const dataSearchQuery = ref('');
    
    // 分页
    const currentPage = ref(1);
    const pageSize = ref(10);
    const totalRecords = ref(0);
    const totalPages = computed(() => Math.ceil(totalRecords.value / pageSize.value));
    const pageRange = computed(() => {
      const range = [];
      const start = Math.max(1, currentPage.value - 2);
      const end = Math.min(totalPages.value, currentPage.value + 2);
      
      for (let i = start; i <= end; i++) {
        range.push(i);
      }
      
      return range;
    });
    
    // 表结构查看
    const showSchema = ref(false);
    const loadingSchema = ref(false);
    const schemaSQL = ref('');
    
    // 删除确认
    const showDeleteConfirm = ref(false);
    const tableToDelete = ref(null);
    
    // 加载表格列表
    const loadTables = async () => {
      try {
        loading.value = true;
        const response = await axios.get('/api/v1/db/tables');
        tables.value = response.data;
        filterTables();
      } catch (error) {
        console.error('加载表格失败:', error);
        toast.error('加载表格失败: ' + (error.response?.data?.detail || error.message));
      } finally {
        loading.value = false;
      }
    };
    
    // 筛选表格
    const filterTables = () => {
      if (!searchQuery.value) {
        filteredTables.value = [...tables.value];
        return;
      }
      
      const query = searchQuery.value.toLowerCase();
      filteredTables.value = tables.value.filter(table => 
        table.display_name.toLowerCase().includes(query) || 
        (table.description && table.description.toLowerCase().includes(query))
      );
    };
    
    // 打开创建表模态框
    const showCreateTableModal = async () => {
      editingTable.value = null;
      showTableEditor.value = true;
    };
    
    // 编辑表
    const editTable = (table) => {
      editingTable.value = table;
      showTableEditor.value = true;
    };
    
    // 关闭表编辑模态框
    const closeTableEditor = () => {
      showTableEditor.value = false;
      editingTable.value = null;
    };
    
    // 表保存完成
    const handleTableSaved = () => {
      closeTableEditor();
      loadTables();
      toast.success('表操作成功');
    };
    
    // 查看表数据
    const viewTableData = async (table) => {
      currentTable.value = table;
      showTableData.value = true;
      dataSearchQuery.value = '';
      await loadTableData(1);
    };
    
    // 加载表数据
    const loadTableData = async (page) => {
      try {
        loadingTableData.value = true;
        currentPage.value = page;
        
        const params = {
          page: page,
          per_page: pageSize.value
        };
        
        if (dataSearchQuery.value) {
          params.search = dataSearchQuery.value;
        }
        
        const [dataResponse, schemaResponse] = await Promise.all([
          axios.get(`/api/v1/db/tables/${currentTable.value.name}/data`, { params }),
          axios.get(`/api/v1/db/tables/${currentTable.value.name}/schema`)
        ]);
        
        tableData.value = dataResponse.data.items;
        totalRecords.value = dataResponse.data.total;
        tableColumns.value = schemaResponse.data.columns;
      } catch (error) {
        console.error('加载表数据失败:', error);
        toast.error('加载表数据失败: ' + (error.response?.data?.detail || error.message));
      } finally {
        loadingTableData.value = false;
      }
    };
    
    // 切换分页
    const changePage = (page) => {
      if (page < 1 || page > totalPages.value) return;
      loadTableData(page);
    };
    
    // 搜索表数据
    const searchTableData = () => {
      loadTableData(1);
    };
    
    // 关闭表数据模态框
    const closeTableData = () => {
      showTableData.value = false;
      currentTable.value = null;
      tableData.value = [];
      tableColumns.value = [];
    };
    
    // 查看表结构
    const viewTableSchema = async (table) => {
      try {
        loadingSchema.value = true;
        currentTable.value = table;
        showSchema.value = true;
        
        const response = await axios.get(`/api/v1/db/tables/${table.name}/schema`);
        tableColumns.value = response.data.columns;
        schemaSQL.value = response.data.sql;
      } catch (error) {
        console.error('加载表结构失败:', error);
        toast.error('加载表结构失败: ' + (error.response?.data?.detail || error.message));
      } finally {
        loadingSchema.value = false;
      }
    };
    
    // 关闭表结构模态框
    const closeSchema = () => {
      showSchema.value = false;
      currentTable.value = null;
      tableColumns.value = [];
      schemaSQL.value = '';
    };
    
    // 确认删除表
    const confirmDeleteTable = (table) => {
      tableToDelete.value = table;
      showDeleteConfirm.value = true;
    };
    
    // 取消删除
    const cancelDelete = () => {
      showDeleteConfirm.value = false;
      tableToDelete.value = null;
    };
    
    // 删除表
    const deleteTable = async () => {
      try {
        await axios.delete(`/api/v1/db/tables/${tableToDelete.value.name}`);
        toast.success(`表 ${tableToDelete.value.display_name} 已删除`);
        showDeleteConfirm.value = false;
        tableToDelete.value = null;
        loadTables();
      } catch (error) {
        console.error('删除表失败:', error);
        toast.error('删除表失败: ' + (error.response?.data?.detail || error.message));
      }
    };
    
    // 编辑记录
    const editRecord = (record) => {
      // 实现编辑记录的逻辑
      toast.info('编辑记录功能待实现');
    };
    
    // 删除记录
    const deleteRecord = async (record) => {
      try {
        // 获取主键字段
        const primaryKey = tableColumns.value.find(col => col.primary_key);
        if (!primaryKey) {
          toast.error('无法确定主键字段');
          return;
        }
        
        const id = record[primaryKey.name];
        await axios.delete(`/api/v1/db/tables/${currentTable.value.name}/data/${id}`);
        toast.success('记录已删除');
        loadTableData(currentPage.value);
      } catch (error) {
        console.error('删除记录失败:', error);
        toast.error('删除记录失败: ' + (error.response?.data?.detail || error.message));
      }
    };
    
    // 添加记录
    const showAddRecordForm = () => {
      // 实现添加记录的逻辑
      toast.info('添加记录功能待实现');
    };
    
    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return '-';
      return new Date(dateString).toLocaleString();
    };
    
    // 格式化单元格值
    const formatCellValue = (value) => {
      if (value === null || value === undefined) return '-';
      if (typeof value === 'boolean') return value ? '是' : '否';
      if (value instanceof Date) return value.toLocaleString();
      if (typeof value === 'object') return JSON.stringify(value);
      return value;
    };
    
    // 格式化列类型
    const formatColumnType = (column) => {
      let type = column.type;
      
      if (column.type === 'string' && column.length) {
        type += `(${column.length})`;
      }
      
      if (['integer', 'float'].includes(column.type) && column.precision) {
        type += `(${column.precision})`;
      }
      
      return type;
    };
    
    // 检查用户权限
    const userCan = (permission) => {
      // 从本地存储获取用户信息
      const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
      return userInfo.permissions?.includes(permission) || false;
    };
    
    onMounted(() => {
      loadTables();
    });
    
    return {
      tables,
      loading,
      searchQuery,
      filteredTables,
      
      showTableEditor,
      editingTable,
      
      showTableData,
      currentTable,
      tableData,
      tableColumns,
      loadingTableData,
      dataSearchQuery,
      
      currentPage,
      totalRecords,
      totalPages,
      pageRange,
      
      showSchema,
      loadingSchema,
      schemaSQL,
      
      showDeleteConfirm,
      tableToDelete,
      
      filterTables,
      showCreateTableModal,
      editTable,
      closeTableEditor,
      handleTableSaved,
      
      viewTableData,
      searchTableData,
      changePage,
      closeTableData,
      
      viewTableSchema,
      closeSchema,
      
      confirmDeleteTable,
      cancelDelete,
      deleteTable,
      
      editRecord,
      deleteRecord,
      showAddRecordForm,
      
      formatDate,
      formatCellValue,
      formatColumnType,
      userCan
    };
  }
};
</script>

<style scoped>
.database-manager {
  padding: 1.5rem;
}

.table td {
  vertical-align: middle;
}

.modal {
  background-color: rgba(0, 0, 0, 0.5);
}

.pagination {
  margin-bottom: 0;
}

.page-link {
  cursor: pointer;
}
</style> 