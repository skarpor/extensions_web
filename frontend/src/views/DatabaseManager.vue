<template>
  <div class="database-manager">
    <div class="cyber-header-main">
      <h1><i class="fas fa-database"></i> 数据库管理系统</h1>
      <div class="cyber-line-main"></div>
    </div>
    
    <!-- 数据库初始化面板 -->
    <div class="db-init-panel" v-if="!isDbInitialized">
      <div class="cyber-container">
        <div class="cyber-header">
          <h2><i class="fas fa-plug"></i> 数据库连接初始化</h2>
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
    
    <!-- 已初始化的数据库管理界面 -->
    <div v-if="isDbInitialized" class="cyber-initialized">
      <div class="cyber-search-panel">
        <div class="cyber-container">
          <div class="cyber-search-content">
            <div class="cyber-search-input">
              <i class="fas fa-search"></i>
              <input 
                v-model="searchQuery" 
                type="text" 
                placeholder="搜索表..." 
                class="cyber-input" 
                @input="filterTables"
              />
            </div>
            
            <button 
              class="cyber-button create" 
              @click="showCreateTableModal"
              v-if="userCan('manage_extension_db')"
            >
              <span class="button-content">
                <i class="fas fa-plus"></i>
                <span>创建新表</span>
              </span>
            </button>
          </div>
        </div>
      </div>
      
      <div v-if="loading" class="cyber-loading-container">
        <div class="cyber-spinner"></div>
        <div class="cyber-loading-text">正在加载数据库表...</div>
      </div>
      
      <div v-else-if="tables.length === 0" class="cyber-empty-state">
        <i class="fas fa-database"></i>
        <p>暂无表，请创建新表</p>
        <button 
          class="cyber-button create" 
          @click="showCreateTableModal"
          v-if="userCan('manage_extension_db')"
        >
          <span class="button-content">
            <i class="fas fa-plus"></i>
            <span>创建新表</span>
          </span>
        </button>
      </div>
      
      <div v-else class="cyber-table-container">
        <table class="cyber-table">
          <thead>
            <tr>
              <th>表名</th>
              <th>描述</th>
              <th>记录数</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="table in filteredTables" :key="table.name" class="cyber-table-row">
              <td>{{ table.display_name }}</td>
              <td>{{ table.description || '无描述' }}</td>
              <td>{{ table.record_count || 0 }}</td>
              <td>{{ formatDate(table.created_at) }}</td>
              <td>
                <div class="cyber-button-group">
                  <button 
                    class="cyber-icon-button view" 
                    @click="viewTableData(table)"
                    title="查看数据"
                  >
                    <i class="fas fa-table"></i>
                  </button>
                  
                  <button 
                    class="cyber-icon-button schema" 
                    @click="viewTableSchema(table)"
                    title="查看结构"
                  >
                    <i class="fas fa-code"></i>
                  </button>
                  
                  <button 
                    v-if="userCan('manage_extension_db')"
                    class="cyber-icon-button edit" 
                    @click="editTable(table)"
                    title="编辑表"
                  >
                    <i class="fas fa-edit"></i>
                  </button>
                  
                  <button 
                    v-if="userCan('manage_extension_db')"
                    class="cyber-icon-button delete" 
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
    </div>
    
    <!-- 创建/编辑表模态框 -->
    <div v-if="showTableEditor" class="cyber-modal">
      <div class="cyber-modal-backdrop" @click="closeTableEditor"></div>
      <div class="cyber-modal-container">
        <div class="cyber-modal-header">
          <h3>{{ editingTable ? '编辑表' : '创建新表' }}</h3>
          <button class="cyber-close-button" @click="closeTableEditor">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="cyber-modal-body">
          <div class="cyber-form">
            <!-- 表基本信息 -->
            <div class="cyber-form-group">
              <label class="cyber-label">表名</label>
              <input 
                v-model="tableForm.name" 
                type="text" 
                class="cyber-input" 
                placeholder="输入表名"
                :disabled="editingTable"
              />
            </div>
            
            <div class="cyber-form-group">
              <label class="cyber-label">显示名称</label>
              <input 
                v-model="tableForm.display_name" 
                type="text" 
                class="cyber-input" 
                placeholder="输入显示名称"
              />
            </div>
            
            <div class="cyber-form-group">
              <label class="cyber-label">描述</label>
              <textarea 
                v-model="tableForm.description" 
                class="cyber-textarea" 
                placeholder="输入表描述"
              ></textarea>
            </div>
            
            <!-- 表字段 -->
            <div class="cyber-form-section">
              <div class="cyber-section-header">
                <h4>表字段</h4>
                <button class="cyber-button small" @click="addColumn">
                  <i class="fas fa-plus"></i> 添加字段
                </button>
              </div>
              
              <div class="cyber-columns-container">
                <div 
                  v-for="(column, index) in tableForm.columns" 
                  :key="index"
                  class="cyber-column-item"
                >
                  <div class="cyber-column-header">
                    <span>字段 #{{ index + 1 }}</span>
                    <button class="cyber-icon-button delete small" @click="removeColumn(index)">
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                  
                  <div class="cyber-column-body">
                    <div class="cyber-form-row">
                      <div class="cyber-form-group">
                        <label class="cyber-label">字段名</label>
                        <input 
                          v-model="column.name" 
                          type="text" 
                          class="cyber-input" 
                          placeholder="字段名"
                        />
                      </div>
                      
                      <div class="cyber-form-group">
                        <label class="cyber-label">类型</label>
                        <select v-model="column.type" class="cyber-select">
                          <option value="integer">整数 (Integer)</option>
                          <option value="string">字符串 (String)</option>
                          <option value="text">文本 (Text)</option>
                          <option value="float">浮点数 (Float)</option>
                          <option value="boolean">布尔值 (Boolean)</option>
                          <option value="datetime">日期时间 (DateTime)</option>
                        </select>
                      </div>
                    </div>
                    
                    <div class="cyber-form-row">
                      <div class="cyber-form-group" v-if="column.type === 'string'">
                        <label class="cyber-label">长度</label>
                        <input 
                          v-model.number="column.length" 
                          type="number" 
                          class="cyber-input" 
                          placeholder="字符长度"
                        />
                      </div>
                      
                      <div class="cyber-form-group">
                        <label class="cyber-label">默认值</label>
                        <input 
                          v-model="column.default" 
                          type="text" 
                          class="cyber-input" 
                          placeholder="默认值"
                        />
                      </div>
                    </div>
                    
                    <div class="cyber-form-row cyber-checkboxes">
                      <div class="cyber-checkbox">
                        <input 
                          :id="'primary_' + index" 
                          type="checkbox" 
                          v-model="column.primary_key"
                          @change="handlePrimaryKeyChange(index)"
                        />
                        <label :for="'primary_' + index">主键</label>
                      </div>
                      
                      <div class="cyber-checkbox">
                        <input 
                          :id="'unique_' + index" 
                          type="checkbox" 
                          v-model="column.unique"
                        />
                        <label :for="'unique_' + index">唯一</label>
                      </div>
                      
                      <div class="cyber-checkbox">
                        <input 
                          :id="'nullable_' + index" 
                          type="checkbox" 
                          v-model="column.nullable"
                          :disabled="column.primary_key"
                        />
                        <label :for="'nullable_' + index">可空</label>
                      </div>
                      
                      <div class="cyber-checkbox" v-if="column.type === 'integer'">
                        <input 
                          :id="'autoincrement_' + index" 
                          type="checkbox" 
                          v-model="column.auto_increment"
                          :disabled="!column.primary_key"
                        />
                        <label :for="'autoincrement_' + index">自增</label>
                      </div>
                    </div>
                    
                    <div class="cyber-form-group">
                      <label class="cyber-label">注释</label>
                      <input 
                        v-model="column.comment" 
                        type="text" 
                        class="cyber-input" 
                        placeholder="字段注释"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="cyber-modal-footer">
          <button class="cyber-button secondary" @click="closeTableEditor">
            <span class="button-content">取消</span>
          </button>
          <button class="cyber-button primary" @click="saveTable">
            <span class="button-content">
              <i class="fas fa-save"></i>
              <span>保存</span>
            </span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- 表数据查看模态框 -->
    <div v-if="showTableData" class="cyber-modal">
      <div class="cyber-modal-backdrop" @click="closeTableData"></div>
      <div class="cyber-modal-container large">
        <div class="cyber-modal-header">
          <h3>{{ currentTable?.display_name }} - 数据</h3>
          <button class="cyber-close-button" @click="closeTableData">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="cyber-modal-body">
          <div class="cyber-search-panel small">
            <div class="cyber-search-input">
              <i class="fas fa-search"></i>
              <input 
                v-model="dataSearchQuery" 
                type="text" 
                placeholder="搜索数据..." 
                class="cyber-input" 
                @keyup.enter="searchTableData"
              />
              <button class="cyber-button small" @click="searchTableData">
                <i class="fas fa-search"></i>
              </button>
            </div>
          </div>
          
          <div v-if="loadingTableData" class="cyber-loading-container">
            <div class="cyber-spinner"></div>
            <div class="cyber-loading-text">正在加载数据...</div>
          </div>
          
          <div v-else-if="tableData.length === 0" class="cyber-empty-state">
            <i class="fas fa-table"></i>
            <p>表中没有数据</p>
          </div>
          
          <div v-else class="cyber-table-container">
            <table class="cyber-table data-table">
              <thead>
                <tr>
                  <th v-for="column in tableColumns" :key="column.name">
                    {{ column.name }}
                  </th>
                  <th v-if="userCan('manage_extension_db')">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, index) in tableData" :key="index" class="cyber-table-row">
                  <td v-for="column in tableColumns" :key="column.name">
                    {{ formatCellValue(row[column.name]) }}
                  </td>
                  <td v-if="userCan('manage_extension_db')">
                    <div class="cyber-button-group">
                      <button 
                        class="cyber-icon-button edit small" 
                        @click="editRecord(row)"
                        title="编辑"
                      >
                        <i class="fas fa-edit"></i>
                      </button>
                      <button 
                        class="cyber-icon-button delete small" 
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
          <div class="cyber-pagination">
            <div class="cyber-pagination-info">
              显示 {{ tableData.length }} 条记录，共 {{ totalRecords }} 条
            </div>
            <div class="cyber-pagination-controls">
              <button 
                class="cyber-pagination-button" 
                :class="{ disabled: currentPage === 1 }"
                @click="changePage(1)"
              >
                <i class="fas fa-angle-double-left"></i>
              </button>
              <button 
                class="cyber-pagination-button" 
                :class="{ disabled: currentPage === 1 }"
                @click="changePage(currentPage - 1)"
              >
                <i class="fas fa-angle-left"></i>
              </button>
              
              <div class="cyber-pagination-pages">
                <button 
                  v-for="page in pageRange" 
                  :key="page"
                  class="cyber-pagination-button" 
                  :class="{ active: currentPage === page }"
                  @click="changePage(page)"
                >
                  {{ page }}
                </button>
              </div>
              
              <button 
                class="cyber-pagination-button" 
                :class="{ disabled: currentPage === totalPages }"
                @click="changePage(currentPage + 1)"
              >
                <i class="fas fa-angle-right"></i>
              </button>
              <button 
                class="cyber-pagination-button" 
                :class="{ disabled: currentPage === totalPages }"
                @click="changePage(totalPages)"
              >
                <i class="fas fa-angle-double-right"></i>
              </button>
            </div>
          </div>
        </div>
        
        <div class="cyber-modal-footer">
          <button 
            v-if="userCan('manage_extension_db')"
            class="cyber-button success" 
            @click="showAddRecordForm"
          >
            <span class="button-content">
              <i class="fas fa-plus"></i>
              <span>添加记录</span>
            </span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- 表结构查看模态框 -->
    <div v-if="showSchema" class="cyber-modal">
      <div class="cyber-modal-backdrop" @click="closeSchema"></div>
      <div class="cyber-modal-container">
        <div class="cyber-modal-header">
          <h3>{{ currentTable?.display_name }} - 表结构</h3>
          <button class="cyber-close-button" @click="closeSchema">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="cyber-modal-body">
          <div v-if="loadingSchema" class="cyber-loading-container">
            <div class="cyber-spinner"></div>
            <div class="cyber-loading-text">正在加载表结构...</div>
          </div>
          
          <div v-else>
            <div class="cyber-table-container">
              <table class="cyber-table">
                <thead>
                  <tr>
                    <th>字段名</th>
                    <th>类型</th>
                    <th>约束</th>
                    <th>默认值</th>
                    <th>说明</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="column in tableColumns" :key="column.name" class="cyber-table-row">
                    <td>{{ column.name }}</td>
                    <td>{{ formatColumnType(column) }}</td>
                    <td>
                      <span v-if="column.primary_key" class="cyber-badge primary">主键</span>
                      <span v-if="column.unique" class="cyber-badge info">唯一</span>
                      <span v-if="column.nullable" class="cyber-badge secondary">可空</span>
                      <span v-if="column.auto_increment" class="cyber-badge success">自增</span>
                    </td>
                    <td>{{ column.default || '-' }}</td>
                    <td>{{ column.comment || '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <div class="cyber-code-block">
              <div class="cyber-code-header">
                <h4>SQL 创建语句</h4>
              </div>
              <pre class="cyber-code">{{ schemaSQL }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 删除确认模态框 -->
    <div v-if="showDeleteConfirm" class="cyber-modal">
      <div class="cyber-modal-backdrop" @click="cancelDelete"></div>
      <div class="cyber-modal-container small">
        <div class="cyber-modal-header">
          <h3>确认删除</h3>
          <button class="cyber-close-button" @click="cancelDelete">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="cyber-modal-body">
          <div class="cyber-confirm-message">
            <p>确定要删除表 <strong>{{ tableToDelete?.display_name }}</strong> 吗？</p>
            <div class="cyber-alert danger">
              <i class="fas fa-exclamation-triangle"></i>
              <span>此操作将删除表及其所有数据，且不可恢复！</span>
            </div>
          </div>
        </div>
        
        <div class="cyber-modal-footer">
          <button class="cyber-button secondary" @click="cancelDelete">
            <span class="button-content">取消</span>
          </button>
          <button class="cyber-button danger" @click="deleteTable">
            <span class="button-content">
              <i class="fas fa-trash"></i>
              <span>确认删除</span>
            </span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- 记录编辑模态框 -->
    <div v-if="showRecordEditor" class="cyber-modal">
      <div class="cyber-modal-backdrop" @click="closeRecordEditor"></div>
      <div class="cyber-modal-container">
        <div class="cyber-modal-header">
          <h3>{{ editingRecord ? '编辑记录' : '添加记录' }}</h3>
          <button class="cyber-close-button" @click="closeRecordEditor">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="cyber-modal-body">
          <div class="cyber-form">
            <div 
              v-for="column in tableColumns" 
              :key="column.name"
              class="cyber-form-group"
              v-show="!column.auto_increment || !editingRecord"
            >
              <label class="cyber-label">{{ column.name }}</label>
              
              <!-- 根据字段类型渲染不同的输入控件 -->
              <input 
                v-if="column.type === 'string' || column.type === 'integer' || column.type === 'float'"
                v-model="recordForm[column.name]"
                :type="column.type === 'integer' || column.type === 'float' ? 'number' : 'text'"
                class="cyber-input"
                :placeholder="column.name"
                :disabled="column.primary_key && editingRecord"
              />
              
              <textarea 
                v-else-if="column.type === 'text'"
                v-model="recordForm[column.name]"
                class="cyber-textarea"
                :placeholder="column.name"
              ></textarea>
              
              <div v-else-if="column.type === 'boolean'" class="cyber-toggle">
                <input 
                  :id="'toggle_' + column.name" 
                  type="checkbox" 
                  v-model="recordForm[column.name]"
                />
                <label :for="'toggle_' + column.name"></label>
              </div>
              
              <input 
                v-else-if="column.type === 'datetime'"
                v-model="recordForm[column.name]"
                type="datetime-local"
                class="cyber-input"
              />
              
              <input 
                v-else
                v-model="recordForm[column.name]"
                type="text"
                class="cyber-input"
                :placeholder="column.name"
              />
            </div>
          </div>
        </div>
        
        <div class="cyber-modal-footer">
          <button class="cyber-button secondary" @click="closeRecordEditor">
            <span class="button-content">取消</span>
          </button>
          <button class="cyber-button primary" @click="saveRecord">
            <span class="button-content">
              <i class="fas fa-save"></i>
              <span>保存</span>
            </span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, reactive } from 'vue';
import Toast from '@/utils/toast';
import databaseApi from '@/api/database';

export default {
  name: 'DatabaseManager',
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
      { value: 'postgres', label: 'PostgreSQL', icon: 'fas fa-database' },
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
    const tableForm = reactive({
      name: '',
      display_name: '',
      description: '',
      columns: []
    });
    
    // 表数据查看
    const showTableData = ref(false);
    const currentTable = ref(null);
    const tableData = ref([]);
    const tableColumns = ref([]);
    const loadingTableData = ref(false);
    const dataSearchQuery = ref('');
    
    // 记录编辑
    const showRecordEditor = ref(false);
    const editingRecord = ref(null);
    const recordForm = reactive({});
    
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
    const showCreateTableModal = () => {
      // 重置表单
      Object.assign(tableForm, {
        name: '',
        display_name: '',
        description: '',
        columns: [createDefaultColumn()]
      });
      
      editingTable.value = null;
      showTableEditor.value = true;
    };
    
    // 创建默认列
    const createDefaultColumn = () => {
      return {
        name: '',
        type: 'integer',
        primary_key: true,
        unique: false,
        nullable: false,
        auto_increment: true,
        default: null,
        comment: '',
        length: null
      };
    };
    
    // 添加列
    const addColumn = () => {
      tableForm.columns.push({
        name: '',
        type: 'string',
        primary_key: false,
        unique: false,
        nullable: true,
        auto_increment: false,
        default: null,
        comment: '',
        length: 255
      });
    };
    
    // 移除列
    const removeColumn = (index) => {
      tableForm.columns.splice(index, 1);
    };
    
    // 处理主键变更
    const handlePrimaryKeyChange = (index) => {
      // 如果设置为主键，则自动设置不可为空
      if (tableForm.columns[index].primary_key) {
        tableForm.columns[index].nullable = false;
        
        // 如果是整数类型，默认设置为自增
        if (tableForm.columns[index].type === 'integer') {
          tableForm.columns[index].auto_increment = true;
        }
        
        // 取消其他列的主键设置（单主键）
        tableForm.columns.forEach((col, i) => {
          if (i !== index && col.primary_key) {
            col.primary_key = false;
            col.auto_increment = false;
          }
        });
      } else {
        // 取消主键时，同时取消自增
        tableForm.columns[index].auto_increment = false;
      }
    };
    
    // 编辑表
    const editTable = async (table) => {
      try {
        // 获取表结构
        const schema = await databaseApi.getTableSchema(table.name);
        
        // 填充表单
        Object.assign(tableForm, {
          name: table.name,
          display_name: table.display_name || table.name,
          description: table.description || '',
          columns: schema.data.columns.map(col => ({
            name: col.name,
            type: col.type,
            primary_key: col.primary_key,
            unique: col.unique,
            nullable: col.nullable,
            auto_increment: col.auto_increment,
            default: col.default,
            comment: col.comment,
            length: col.type === 'string' ? (col.length || 255) : null
          }))
        });
        
        editingTable.value = table;
        showTableEditor.value = true;
      } catch (error) {
        console.error('加载表结构失败:', error);
        toast.error('加载表结构失败: ' + (error.response?.data?.detail || error.message));
      }
    };
    
    // 关闭表编辑模态框
    const closeTableEditor = () => {
      showTableEditor.value = false;
      editingTable.value = null;
    };
    
    // 保存表
    const saveTable = async () => {
      try {
        // 验证表单
        if (!tableForm.name) {
          toast.error('表名不能为空');
          return;
        }
        
        if (tableForm.columns.length === 0) {
          toast.error('表至少需要一个字段');
          return;
        }
        
        // 验证列名
        for (const column of tableForm.columns) {
          if (!column.name) {
            toast.error('字段名不能为空');
            return;
          }
        }
        
        // 验证主键
        if (!tableForm.columns.some(col => col.primary_key)) {
          toast.error('表必须有一个主键');
          return;
        }
        
        // 准备请求数据
        const schema = {
          columns: tableForm.columns,
          description: tableForm.description
        };
        
        if (editingTable.value) {
          // 更新表
          await databaseApi.updateTable(editingTable.value.name, schema);
          toast.success(`表 ${editingTable.value.name} 更新成功`);
        } else {
          // 创建表
          await databaseApi.createTable(tableForm.name, schema);
          toast.success(`表 ${tableForm.name} 创建成功`);
        }
        
        // 关闭模态框并刷新表格
        closeTableEditor();
        loadTables();
      } catch (error) {
        console.error('保存表失败:', error);
        toast.error('保存表失败: ' + (error.response?.data?.detail || error.message));
      }
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
    
    // 显示添加记录表单
    const showAddRecordForm = () => {
      // 重置表单
      const newRecord = {};
      tableColumns.value.forEach(column => {
        newRecord[column.name] = null;
      });
      
      Object.assign(recordForm, newRecord);
      editingRecord.value = null;
      showRecordEditor.value = true;
    };
    
    // 编辑记录
    const editRecord = (record) => {
      // 填充表单
      Object.assign(recordForm, { ...record });
      editingRecord.value = record;
      showRecordEditor.value = true;
    };
    
    // 关闭记录编辑模态框
    const closeRecordEditor = () => {
      showRecordEditor.value = false;
      editingRecord.value = null;
    };
    
    // 保存记录
    const saveRecord = async () => {
      try {
        if (editingRecord.value) {
          // 获取主键字段
          const primaryKey = tableColumns.value.find(col => col.primary_key);
          if (!primaryKey) {
            toast.error('无法确定主键字段');
            return;
          }
          
          const id = recordForm[primaryKey.name];
          await databaseApi.updateRecord(currentTable.value.name, id, recordForm);
          toast.success('记录已更新');
        } else {
          await databaseApi.createRecord(currentTable.value.name, recordForm);
          toast.success('记录已添加');
        }
        
        closeRecordEditor();
        loadTableData(currentPage.value);
      } catch (error) {
        console.error('保存记录失败:', error);
        toast.error('保存记录失败: ' + (error.response?.data?.detail || error.message));
      }
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
        
        if (confirm(`确定要删除这条记录吗？`)) {
          await databaseApi.deleteRecord(currentTable.value.name, id);
          toast.success('记录已删除');
          loadTableData(currentPage.value);
        }
      } catch (error) {
        console.error('删除记录失败:', error);
        toast.error('删除记录失败: ' + (error.response?.data?.detail || error.message));
      }
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
      // 简化处理，实际应用中应该从用户信息中获取权限
      return true;
    };
    
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
    
    onMounted(() => {
      // 检查是否已经初始化
      // checkDbInitialized();
    });

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
      
      // 表格数据
      tables,
      loading,
      searchQuery,
      filteredTables,
      filterTables,
      
      // 表编辑
      showTableEditor,
      editingTable,
      tableForm,
      showCreateTableModal,
      editTable,
      closeTableEditor,
      saveTable,
      addColumn,
      removeColumn,
      handlePrimaryKeyChange,
      
      // 表数据查看
      showTableData,
      currentTable,
      tableData,
      tableColumns,
      loadingTableData,
      dataSearchQuery,
      viewTableData,
      closeTableData,
      searchTableData,
      
      // 分页
      currentPage,
      totalRecords,
      totalPages,
      pageRange,
      changePage,
      
      // 记录编辑
      showRecordEditor,
      editingRecord,
      recordForm,
      showAddRecordForm,
      editRecord,
      closeRecordEditor,
      saveRecord,
      deleteRecord,
      
      // 表结构查看
      showSchema,
      loadingSchema,
      schemaSQL,
      viewTableSchema,
      closeSchema,
      
      // 删除确认
      showDeleteConfirm,
      tableToDelete,
      confirmDeleteTable,
      cancelDelete,
      deleteTable,
      
      // 工具函数
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
  width: 100%;
  min-height: 100%;
  background: linear-gradient(135deg, #0f1631, #171d33);
  color: #e0e0ff;
  font-family: 'Rajdhani', 'Roboto', sans-serif;
  padding: 1.5rem;
  position: relative;
}

/* 主标题样式 */
.cyber-header-main {
  margin-bottom: 2rem;
  position: relative;
}

.cyber-header-main h1 {
  color: #4facfe;
  font-size: 2.5rem;
  font-weight: 600;
  margin: 0;
  padding: 0;
  text-transform: uppercase;
  letter-spacing: 2px;
  display: flex;
  align-items: center;
  text-shadow: 0 0 10px rgba(79, 172, 254, 0.5);
}

.cyber-header-main h1 i {
  margin-right: 1rem;
  font-size: 2rem;
}

.cyber-line-main {
  height: 2px;
  background: linear-gradient(90deg, #4facfe, transparent);
  margin-top: 0.5rem;
  position: relative;
  overflow: hidden;
}

.cyber-line-main::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, #4facfe, transparent);
  animation: cyber-scan 3s linear infinite;
}

@keyframes cyber-scan {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

/* 数据库初始化面板 */
.db-init-panel {
  margin-bottom: 2rem;
}

.cyber-container {
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  border-radius: 10px;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
  border: 1px solid rgba(79, 172, 254, 0.3);
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
  text-transform: uppercase;
  letter-spacing: 1px;
}

.cyber-header h2 i {
  margin-right: 0.75rem;
}

.cyber-line {
  height: 1px;
  background: linear-gradient(90deg, transparent, #4facfe, transparent);
  margin-top: 1rem;
  position: relative;
}

.cyber-body {
  padding: 1.5rem;
}

/* 终端风格 */
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

/* 数据库类型选择器 */
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
  box-shadow: 0 5px 15px rgba(79, 172, 254, 0.2);
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

/* 输入控件 */
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

.cyber-textarea {
  width: 100%;
  background: rgba(30, 30, 63, 0.7);
  border: 1px solid rgba(79, 172, 254, 0.3);
  border-radius: 4px;
  padding: 0.75rem 1rem;
  color: #fff;
  font-family: 'Courier New', monospace;
  min-height: 100px;
  resize: vertical;
  transition: all 0.3s ease;
}

.cyber-textarea:focus {
  outline: none;
  border-color: #4facfe;
  box-shadow: 0 0 10px rgba(79, 172, 254, 0.5);
}

.cyber-select {
  width: 100%;
  background: rgba(30, 30, 63, 0.7);
  border: 1px solid rgba(79, 172, 254, 0.3);
  border-radius: 4px;
  padding: 0.75rem 1rem;
  color: #fff;
  font-family: 'Courier New', monospace;
  transition: all 0.3s ease;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%234facfe' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.7rem center;
  background-size: 1em;
}

.cyber-select:focus {
  outline: none;
  border-color: #4facfe;
  box-shadow: 0 0 10px rgba(79, 172, 254, 0.5);
}

/* 状态显示 */
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

/* 按钮 */
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

.cyber-button.primary::before {
  background: linear-gradient(135deg, #0061ff, #60efff);
}

.cyber-button.secondary::before {
  background: linear-gradient(135deg, #6e7c90, #a1a9b6);
}

.cyber-button.success::before {
  background: linear-gradient(135deg, #00b09b, #96c93d);
}

.cyber-button.danger::before {
  background: linear-gradient(135deg, #ff416c, #ff4b2b);
}

.cyber-button.create::before {
  background: linear-gradient(135deg, #7f00ff, #e100ff);
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

.cyber-button.small {
  padding: 0.5rem 1rem;
  font-size: 0.85rem;
}

/* 图标按钮 */
.cyber-icon-button {
  width: 36px;
  height: 36px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(30, 30, 63, 0.7);
  border: 1px solid rgba(79, 172, 254, 0.3);
  color: #fff;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cyber-icon-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(79, 172, 254, 0.2);
}

.cyber-icon-button.view {
  color: #4facfe;
}

.cyber-icon-button.schema {
  color: #e100ff;
}

.cyber-icon-button.edit {
  color: #ffbd2e;
}

.cyber-icon-button.delete {
  color: #ff5f56;
}

.cyber-icon-button.small {
  width: 28px;
  height: 28px;
  font-size: 0.85rem;
}

.cyber-button-group {
  display: flex;
  gap: 0.5rem;
}

/* 加载动画 */
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
  position: relative;
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

.cyber-loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

/* 已初始化界面 */
.cyber-initialized {
  margin-top: 2rem;
}

.cyber-search-panel {
  margin-bottom: 1.5rem;
}

.cyber-search-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
}

.cyber-search-input {
  flex: 1;
  position: relative;
  max-width: 500px;
}

.cyber-search-input i {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: #4facfe;
}

.cyber-search-input .cyber-input {
  padding-left: 2.5rem;
}

.cyber-search-panel.small {
  margin-bottom: 1rem;
}

.cyber-search-panel.small .cyber-search-input {
  display: flex;
  gap: 0.5rem;
}

.cyber-empty-state {
  text-align: center;
  padding: 3rem;
  background: rgba(30, 30, 63, 0.3);
  border-radius: 8px;
  border: 1px solid rgba(79, 172, 254, 0.3);
}

.cyber-empty-state i {
  font-size: 3rem;
  color: #4facfe;
  margin-bottom: 1rem;
}

.cyber-empty-state p {
  font-size: 1.25rem;
  margin-bottom: 1.5rem;
  color: #a1a9b6;
}

/* 表格 */
.cyber-table-container {
  overflow-x: auto;
  margin-bottom: 1.5rem;
  border-radius: 8px;
  border: 1px solid rgba(79, 172, 254, 0.3);
}

.cyber-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  color: #e0e0ff;
}

.cyber-table thead tr {
  background: linear-gradient(90deg, rgba(79, 172, 254, 0.2), rgba(0, 242, 254, 0.2));
}

.cyber-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #4facfe;
  border-bottom: 1px solid rgba(79, 172, 254, 0.3);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.cyber-table td {
  padding: 1rem;
  border-bottom: 1px solid rgba(79, 172, 254, 0.1);
}

.cyber-table-row {
  transition: all 0.3s ease;
}

.cyber-table-row:hover {
  background: rgba(79, 172, 254, 0.1);
}

.cyber-table-row:last-child td {
  border-bottom: none;
}

.cyber-table.data-table {
  font-family: 'Courier New', monospace;
}

/* 模态框 */
.cyber-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.cyber-modal-backdrop {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(10, 10, 35, 0.8);
  backdrop-filter: blur(5px);
}

.cyber-modal-container {
  position: relative;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  border-radius: 10px;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
  border: 1px solid rgba(79, 172, 254, 0.3);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  z-index: 1;
}

.cyber-modal-container.large {
  max-width: 1200px;
}

.cyber-modal-container.small {
  max-width: 500px;
}

.cyber-modal-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(79, 172, 254, 0.3);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.cyber-modal-header h3 {
  margin: 0;
  color: #4facfe;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.cyber-close-button {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255, 95, 86, 0.2);
  border: 1px solid rgba(255, 95, 86, 0.4);
  color: #ff5f56;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cyber-close-button:hover {
  background: rgba(255, 95, 86, 0.3);
  transform: scale(1.1);
}

.cyber-modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.cyber-modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid rgba(79, 172, 254, 0.3);
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

/* 表单 */
.cyber-form {
  margin-bottom: 1.5rem;
}

.cyber-form-group {
  margin-bottom: 1.5rem;
}

.cyber-label {
  display: block;
  margin-bottom: 0.5rem;
  color: #4facfe;
  font-weight: 600;
}

.cyber-form-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.cyber-form-row .cyber-form-group {
  flex: 1;
  margin-bottom: 0;
}

.cyber-form-section {
  margin-top: 2rem;
  border-top: 1px solid rgba(79, 172, 254, 0.3);
  padding-top: 1.5rem;
}

.cyber-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.cyber-section-header h4 {
  margin: 0;
  color: #4facfe;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.cyber-columns-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.cyber-column-item {
  background: rgba(30, 30, 63, 0.3);
  border: 1px solid rgba(79, 172, 254, 0.3);
  border-radius: 8px;
  overflow: hidden;
}

.cyber-column-header {
  background: rgba(79, 172, 254, 0.1);
  padding: 0.75rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cyber-column-header span {
  font-weight: 600;
  color: #4facfe;
}

.cyber-column-body {
  padding: 1rem;
}

/* 复选框 */
.cyber-checkboxes {
  display: flex;
  gap: 1.5rem;
}

.cyber-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.cyber-checkbox input[type="checkbox"] {
  appearance: none;
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  background: rgba(30, 30, 63, 0.7);
  border: 1px solid rgba(79, 172, 254, 0.3);
  border-radius: 3px;
  cursor: pointer;
  position: relative;
}

.cyber-checkbox input[type="checkbox"]:checked {
  background: #4facfe;
}

.cyber-checkbox input[type="checkbox"]:checked::after {
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #fff;
  font-size: 12px;
}

.cyber-checkbox input[type="checkbox"]:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cyber-checkbox label {
  cursor: pointer;
}

/* 开关 */
.cyber-toggle {
  position: relative;
  display: inline-block;
  width: 60px;
  height: 30px;
}

.cyber-toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.cyber-toggle label {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(30, 30, 63, 0.7);
  border: 1px solid rgba(79, 172, 254, 0.3);
  border-radius: 30px;
  transition: .4s;
}

.cyber-toggle label:before {
  position: absolute;
  content: "";
  height: 22px;
  width: 22px;
  left: 4px;
  bottom: 3px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

.cyber-toggle input:checked + label {
  background-color: #4facfe;
}

.cyber-toggle input:checked + label:before {
  transform: translateX(30px);
}

/* 徽章 */
.cyber-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  margin-right: 0.25rem;
}

.cyber-badge.primary {
  background: rgba(79, 172, 254, 0.2);
  color: #4facfe;
  border: 1px solid rgba(79, 172, 254, 0.4);
}

.cyber-badge.info {
  background: rgba(0, 242, 254, 0.2);
  color: #00f2fe;
  border: 1px solid rgba(0, 242, 254, 0.4);
}

.cyber-badge.secondary {
  background: rgba(161, 169, 182, 0.2);
  color: #a1a9b6;
  border: 1px solid rgba(161, 169, 182, 0.4);
}

.cyber-badge.success {
  background: rgba(39, 201, 63, 0.2);
  color: #27c93f;
  border: 1px solid rgba(39, 201, 63, 0.4);
}

/* 代码块 */
.cyber-code-block {
  margin-top: 1.5rem;
}

.cyber-code-header {
  background: rgba(30, 30, 63, 0.5);
  padding: 0.75rem 1rem;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
  border: 1px solid rgba(79, 172, 254, 0.3);
  border-bottom: none;
}

.cyber-code-header h4 {
  margin: 0;
  color: #4facfe;
  font-size: 1rem;
  font-weight: 600;
}

.cyber-code {
  background: #0a0a23;
  color: #e0e0ff;
  padding: 1rem;
  border-bottom-left-radius: 8px;
  border-bottom-right-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  line-height: 1.5;
  overflow-x: auto;
  border: 1px solid rgba(79, 172, 254, 0.3);
  white-space: pre-wrap;
}

/* 确认消息 */
.cyber-confirm-message {
  text-align: center;
  padding: 1rem;
}

.cyber-confirm-message p {
  font-size: 1.25rem;
  margin-bottom: 1.5rem;
}

.cyber-alert {
  padding: 1rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.cyber-alert.danger {
  background: rgba(255, 95, 86, 0.1);
  border: 1px solid rgba(255, 95, 86, 0.3);
  color: #ff5f56;
}

.cyber-alert i {
  font-size: 1.5rem;
}

/* 分页 */
.cyber-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1.5rem;
}

.cyber-pagination-info {
  color: #a1a9b6;
}

.cyber-pagination-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.cyber-pagination-pages {
  display: flex;
  gap: 0.25rem;
}

.cyber-pagination-button {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(30, 30, 63, 0.7);
  border: 1px solid rgba(79, 172, 254, 0.3);
  color: #fff;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.cyber-pagination-button:hover {
  background: rgba(79, 172, 254, 0.2);
}

.cyber-pagination-button.active {
  background: rgba(79, 172, 254, 0.3);
  border-color: #4facfe;
  color: #4facfe;
}

.cyber-pagination-button.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .cyber-form-row {
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .cyber-checkboxes {
    flex-wrap: wrap;
    gap: 1rem;
  }
  
  .cyber-search-content {
    flex-direction: column;
    gap: 1rem;
  }
  
  .cyber-search-input {
    max-width: 100%;
  }
  
  .cyber-pagination {
    flex-direction: column;
    gap: 1rem;
  }
}

/* 动画效果 */
@keyframes neon-pulse {
  0% {
    box-shadow: 0 0 5px rgba(79, 172, 254, 0.5), 0 0 10px rgba(79, 172, 254, 0.3);
  }
  50% {
    box-shadow: 0 0 10px rgba(79, 172, 254, 0.8), 0 0 20px rgba(79, 172, 254, 0.5);
  }
  100% {
    box-shadow: 0 0 5px rgba(79, 172, 254, 0.5), 0 0 10px rgba(79, 172, 254, 0.3);
  }
}

.cyber-container {
  animation: neon-pulse 3s infinite;
}
</style>