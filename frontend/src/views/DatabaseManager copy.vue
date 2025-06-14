<template>
  <div class="database-manager">
    <h1>数据库管理</h1>
    
        <!-- 数据库初始化面板 -->
        <div class="db-init-panel" v-if="!isDbInitialized">
      <div class="cyber-container">
        <div class="cyber-header">
          <h2><i class="fas fa-database"></i> 数据库连接初始化</h2>
          <div class="cyber-line"></div>
        </div>
        
        <div class="cyber-body">
          <div class="cyber-terminal">
            <div class="terminal-header">
              <span class="terminal-dot red"></span>
              <span class="terminal-dot yellow"></span>
              <span class="terminal-dot green"></span>
              <span class="terminal-title">数据库配置终端</span>
            </div>
            <div class="terminal-content">
              <div class="terminal-line">
                <span class="prompt">$</span> 
                <span class="command">选择数据库类型</span>
              </div>
              
              <div class="db-type-selector">
                <div 
                  v-for="type in dbTypes" 
                  :key="type.value" 
                  class="db-type-option" 
                  :class="{ active: dbType === type.value }"
                  @click="selectDbType(type.value)"
                >
                  <i :class="type.icon"></i>
                  <span>{{ type.label }}</span>
                </div>
              </div>
              
              <div class="terminal-line">
                <span class="prompt">$</span> 
                <span class="command">配置数据库路径</span>
              </div>
              
              <div class="db-path-input">
                <input 
                  v-model="dbPath" 
                  type="text" 
                  :placeholder="dbPathPlaceholder" 
                  class="cyber-input"
                />
              </div>
              
              <div class="terminal-status" v-if="initStatus">
                <div class="status-line" :class="initStatus.type">
                  <i :class="initStatus.icon"></i> {{ initStatus.message }}
                </div>
              </div>
            </div>
          </div>
          
          <div class="cyber-actions">
            <button 
              class="cyber-button primary" 
              @click="initializeDatabase" 
              :disabled="initLoading"
            >
              <span class="button-content">
                <i class="fas fa-power-off"></i>
                <span>{{ initLoading ? '初始化中...' : '初始化连接' }}</span>
              </span>
              <span class="button-glitch"></span>
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 初始化加载动画 -->
    <div v-if="initLoading" class="cyber-loading-overlay">
      <div class="cyber-loading">
        <div class="cyber-spinner"></div>
        <div class="cyber-loading-text">数据库初始化中...</div>
        <div class="cyber-loading-progress">
          <div class="progress-bar" :style="{ width: initProgress + '%' }"></div>
        </div>
      </div>
    </div>
    
    <!-- 现有的表格搜索部分，仅在数据库初始化后显示 -->
    <div v-if="isDbInitialized">
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
  </div></div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import Toast from '@/utils/toast';
import databaseApi from '@/api/database';
import DbTableEditor from '../components/DbTableEditor.vue';

export default {
  name: 'DatabaseManager',
  components: {
    DbTableEditor
  },
  setup() {
    const toast = Toast;
        // 数据库初始化相关
        const isDbInitialized = ref(false);
    const initLoading = ref(false);
    const initProgress = ref(0);
    const dbType = ref('sqlite');
    const dbPath = ref('new_app/data/app.db');
    const initStatus = ref(null);
    // 数据库类型选项
    const dbTypes = [
      { value: 'sqlite', label: 'SQLite', icon: 'fas fa-file-alt' },
      { value: 'postgres', label: 'PostgreSQL', icon: 'fas fa-elephant' },
      { value: 'mysql', label: 'MySQL', icon: 'fas fa-database' }
    ];
    
    // 根据选择的数据库类型设置路径占位符
    const dbPathPlaceholder = computed(() => {
      if (dbType.value === 'sqlite') {
        return '数据库文件路径 (例如: new_app/data/app.db)';
      } else {
        return '数据库名称 (可选)';
      }
    });
    
    // 选择数据库类型
    const selectDbType = (type) => {
      dbType.value = type;
      // 重置路径
      if (type === 'sqlite') {
        dbPath.value = 'new_app/data/app.db';
      } else {
        dbPath.value = '';
      }
    };
    
    // 初始化数据库连接
    const initializeDatabase = async () => {
      try {
        initLoading.value = true;
        initStatus.value = { type: 'info', icon: 'fas fa-info-circle', message: '正在连接数据库...' };
        
        // 模拟进度
        const progressInterval = setInterval(() => {
          if (initProgress.value < 90) {
            initProgress.value += Math.floor(Math.random() * 10) + 1;
          }
        }, 200);
        
        // 调用API初始化数据库
        const response = await databaseApi.initializeDatabase(dbType.value, dbPath.value);
        
        // 完成进度
        clearInterval(progressInterval);
        initProgress.value = 100;
        
        // 更新状态
        initStatus.value = { type: 'success', icon: 'fas fa-check-circle', message: '数据库连接成功!' };
        toast.success('数据库初始化成功');
        
        // 延迟后加载表格
        setTimeout(() => {
          isDbInitialized.value = true;
          loadTables();
        }, 1000);
      } catch (error) {
        console.error('初始化数据库失败:', error);
        initStatus.value = { type: 'error', icon: 'fas fa-exclamation-circle', message: '连接失败: ' + (error.response?.data?.detail || error.message) };
        toast.error('初始化数据库失败: ' + (error.response?.data?.detail || error.message));
        initProgress.value = 0;
      } finally {
        initLoading.value = false;
      }
    };

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
        const response = await databaseApi.getTables();
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
          databaseApi.getTableData(currentTable.value.name, params),
          databaseApi.getTableSchema(currentTable.value.name)
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
        
        const response = await databaseApi.getTableSchema(table.name);
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
        await databaseApi.deleteTable(tableToDelete.value.name);
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
        await databaseApi.deleteRecord(currentTable.value.name, id);
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
      return true;
      // 从本地存储获取用户信息
      const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
      return userInfo.permissions?.includes(permission) || false;
    };
    
    onMounted(() => {
      // 检查是否已经初始化
      checkDbInitialized();
    });
        // 检查数据库是否已初始化
        const checkDbInitialized = async () => {
      try {
        // 尝试获取表列表，如果成功则说明数据库已初始化
        const response = await databaseApi.getTables();
        if (response && response.data) {
          isDbInitialized.value = true;
          tables.value = response.data;
          filterTables();
        }
      } catch (error) {
        console.log('数据库未初始化或连接失败', error);
        isDbInitialized.value = false;
      } finally {
        loading.value = false;
      }
    };

    return {
            // 数据库初始化相关
            isDbInitialized,
      initLoading,
      initProgress,
      dbType,
      dbPath,
      dbTypes,
      dbPathPlaceholder,
      initStatus,
      selectDbType,
      initializeDatabase,
      
      
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
  display: flex;
  flex-direction: column;
  width: 100%;
  padding: 1.5rem;
}
/* 科技感十足的数据库初始化面板样式 */
.db-init-panel {
  margin-bottom: 2rem;
}

.cyber-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  border-radius: 10px;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
  border: 1px solid rgba(255, 255, 255, 0.18);
  overflow: hidden;
  position: relative;
}

.cyber-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #00f2fe, #4facfe, #00f2fe);
  animation: scanline 2s linear infinite;
}

@keyframes scanline {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.cyber-header {
  padding: 1.5rem;
  color: #4facfe;
  border-bottom: 1px solid rgba(79, 172, 254, 0.3);
  position: relative;
}

.cyber-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  display: flex;
  align-items: center;
}

.cyber-header h2 i {
  margin-right: 0.5rem;
}

.cyber-line {
  height: 1px;
  background: linear-gradient(90deg, transparent, #4facfe, transparent);
  margin-top: 1rem;
}

.cyber-body {
  padding: 1.5rem;
}

.cyber-terminal {
  background: #0a0a23;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
}

.terminal-header {
  background: #1e1e3f;
  padding: 0.5rem 1rem;
  display: flex;
  align-items: center;
}

.terminal-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 6px;
}

.terminal-dot.red {
  background: #ff5f56;
}

.terminal-dot.yellow {
  background: #ffbd2e;
}

.terminal-dot.green {
  background: #27c93f;
}

.terminal-title {
  margin-left: 1rem;
  color: #ddd;
  font-size: 0.85rem;
}

.terminal-content {
  padding: 1rem;
  color: #eee;
  font-family: 'Courier New', monospace;
}

.terminal-line {
  margin-bottom: 1rem;
  display: flex;
}

.prompt {
  color: #4facfe;
  margin-right: 0.5rem;
}

.command {
  color: #fff;
}

.db-type-selector {
  display: flex;
  gap: 1rem;
  margin: 1rem 0 1.5rem;
  flex-wrap: wrap;
}

.db-type-option {
  background: rgba(79, 172, 254, 0.1);
  border: 1px solid rgba(79, 172, 254, 0.3);
  border-radius: 6px;
  padding: 0.75rem 1.25rem;
  color: #ddd;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.db-type-option:hover {
  background: rgba(79, 172, 254, 0.2);
  transform: translateY(-2px);
}

.db-type-option.active {
  background: rgba(79, 172, 254, 0.3);
  border-color: #4facfe;
  color: #fff;
  box-shadow: 0 0 15px rgba(79, 172, 254, 0.5);
}

.db-path-input {
  margin: 1rem 0 1.5rem;
}

.cyber-input {
  width: 100%;
  background: rgba(30, 30, 63, 0.7);
  border: 1px solid rgba(79, 172, 254, 0.3);
  border-radius: 4px;
  padding: 0.75rem 1rem;
  color: #fff;
  font-family: 'Courier New', monospace;
  transition: all 0.3s ease;
}

.cyber-input:focus {
  outline: none;
  border-color: #4facfe;
  box-shadow: 0 0 10px rgba(79, 172, 254, 0.5);
}

.terminal-status {
  margin-top: 1rem;
  padding: 0.75rem;
  border-radius: 4px;
}

.status-line {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-line.info {
  color: #4facfe;
}

.status-line.success {
  color: #27c93f;
}

.status-line.error {
  color: #ff5f56;
}

.cyber-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.cyber-button {
  background: none;
  border: none;
  position: relative;
  padding: 0.75rem 1.5rem;
  color: #fff;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s ease;
}

.cyber-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #0061ff, #60efff);
  opacity: 0.8;
  z-index: -2;
}

.cyber-button::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  right: 2px;
  bottom: 2px;
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  z-index: -1;
}

.cyber-button .button-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.cyber-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 97, 255, 0.4);
}

.cyber-button:active {
  transform: translateY(0);
}

.button-glitch {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  transform: translateX(-100%);
}

.cyber-button:hover .button-glitch {
  animation: glitch 1s linear;
}

@keyframes glitch {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.cyber-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cyber-loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(10, 10, 35, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.cyber-loading {
  text-align: center;
  color: #fff;
}

.cyber-spinner {
  width: 60px;
  height: 60px;
  border: 3px solid transparent;
  border-top-color: #4facfe;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

.cyber-spinner::before {
  content: '';
  position: absolute;
  top: 5px;
  left: 5px;
  right: 5px;
  bottom: 5px;
  border: 3px solid transparent;
  border-top-color: #00f2fe;
  border-radius: 50%;
  animation: spin 2s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.cyber-loading-text {
  font-size: 1.25rem;
  margin-bottom: 1rem;
  text-shadow: 0 0 10px rgba(79, 172, 254, 0.7);
}

.cyber-loading-progress {
  width: 300px;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #00f2fe, #4facfe);
  transition: width 0.3s ease;
  box-shadow: 0 0 10px rgba(79, 172, 254, 0.7);
}

/* 现有样式保持不变 */
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