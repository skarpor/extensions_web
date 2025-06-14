//数据库管理API
import axios from '@/utils/axios'

//获取所有表
export const getTables = async () => {
    try {
        const response = await axios.get('/api/db/tables')
        return response
    } catch (error) {
        console.error('获取表列表失败:', error)
        throw error
    }
}

//获取表结构
export const getTableSchema = async (tableName) => {
    try {
        const response = await axios.get(`/api/db/tables/${tableName}/schema`)
        return response
    } catch (error) {
        console.error('获取表结构失败:', error)
        throw error
    }
}

//创建表
export const createTable = async (tableName, tableSchema) => {
    try {
        const response = await axios.post('/api/db/tables', {
            name: tableName,
            schema: tableSchema
        })
        return response
    } catch (error) {
        console.error('创建表失败:', error)
        throw error
    }
}

//更新表
export const updateTable = async (tableName, tableSchema) => {
    try {
        const response = await axios.put(`/api/db/tables/${tableName}`, {
            schema: tableSchema
        })
        return response
    } catch (error) {
        console.error('更新表失败:', error)
        throw error
    }
}

//删除表
export const deleteTable = async (tableName) => {
    try {
        const response = await axios.delete(`/api/db/tables/${tableName}`)
        return response
    } catch (error) {
        console.error('删除表失败:', error)
        throw error
    }
}

//获取表数据
export const getTableData = async (tableName, params = {}) => {
    try {
        const response = await axios.get(`/api/db/tables/${tableName}/data`, { params })
        return response
    } catch (error) {
        console.error('获取表数据失败:', error)
        throw error
    }
}

//创建表记录
export const createRecord = async (tableName, recordData) => {
    try {
        const response = await axios.post(`/api/db/tables/${tableName}/data`, {
            data: recordData
        })
        return response
    } catch (error) {
        console.error('创建记录失败:', error)
        throw error
    }
}

//获取表记录
export const getRecord = async (tableName, recordId) => {
    try {
        const response = await axios.get(`/api/db/tables/${tableName}/data/${recordId}`)
        return response
    } catch (error) {
        console.error('获取记录失败:', error)
        throw error
    }
}

//更新表记录
export const updateRecord = async (tableName, recordId, recordData) => {
    try {
        const response = await axios.put(`/api/db/tables/${tableName}/data/${recordId}`, {
            data: recordData
        })
        return response
    } catch (error) {
        console.error('更新记录失败:', error)
        throw error
    }
}

//删除表记录
export const deleteRecord = async (tableName, recordId) => {
    try {
        const response = await axios.delete(`/api/db/tables/${tableName}/data/${recordId}`)
        return response
    } catch (error) {
        console.error('删除记录失败:', error)
        throw error
    }
}

//导出表数据
export const exportTableData = async (tableName, format = 'json') => {
    try {
        const response = await axios.get(`/api/db/tables/${tableName}/export`, {
            params: { format }
        })
        return response
    } catch (error) {
        console.error('导出表数据失败:', error)
        throw error
    }
}

//执行自定义查询
export const executeCustomQuery = async (tableName, query) => {
    try {
        const response = await axios.post(`/api/db/tables/${tableName}/query`, {
            query
        })
        return response
    } catch (error) {
        console.error('执行自定义查询失败:', error)
        throw error
    }
}

//批量插入数据
export const bulkInsertData = async (tableName, data) => {
    try {
        const response = await axios.post(`/api/db/tables/${tableName}/bulk`, {
            data
        })
        return response
    } catch (error) {
        console.error('批量插入数据失败:', error)
        throw error
    }
}

//初始化数据库连接
export const initializeDatabase = async (dbType, dbPath = null) => {
    try {
        const params = { db_type: dbType }
        if (dbPath) {
            params.db_path = dbPath
        }
        const response = await axios.post('/api/db/initialize', null, { params })
        return response
    } catch (error) {
        console.error('初始化数据库失败:', error)
        throw error
    }
}

//导入表数据
export const importTableData = async (tableName, file) => {
    try {
        const formData = new FormData()
        formData.append('file', file)
        const response = await axios.post(`/api/db/tables/${tableName}/import`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })
        return response
    } catch (error) {
        console.error('导入表数据失败:', error)
        throw error
    }
}

// 默认导出所有API
export default {
    getTables,
    getTableSchema,
    createTable,
    updateTable,
    deleteTable,
    getTableData,
    createRecord,
    getRecord,
    updateRecord,
    deleteRecord,
    exportTableData,
    executeCustomQuery,
    bulkInsertData,
    initializeDatabase,
    importTableData
}
