<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>任务详情</h2>
      <router-link to="/scheduler" class="btn btn-outline-secondary">
        <i class="fas fa-arrow-left"></i> 返回任务列表
      </router-link>
    </div>

    <div v-if="job">
      <div class="card mb-4">
        <div class="card-header bg-primary text-white">
          <h5 class="mb-0">
            <i :class="`fas ${getJobIcon(job.type)} me-2`"></i>
            {{ job.job_id }}
            <span :class="`badge ${job.active ? 'bg-success' : 'bg-warning'} ms-2`">
              {{ job.active ? '活跃' : '已暂停' }}
            </span>
          </h5>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-6">
              <h6 class="text-muted">基本信息</h6>
              <table class="table">
                <tbody>
                  <tr>
                    <th style="width: 30%">任务ID</th>
                    <td>{{ job.id }}</td>
                  </tr>
                  <tr>
                    <th>任务类型</th>
                    <td>
                      <span v-if="job.job_type === 'cron'" class="badge bg-primary">Cron定时任务</span>
                      <span v-else-if="job.job_type === 'interval'" class="badge bg-info"
                        >间隔任务</span
                      >
                      <span v-else class="badge bg-warning">一次性任务</span>
                    </td>
                  </tr>
                  <tr>
                    <th>任务函数</th>
                    <td>{{ job.func }}</td>
                  </tr>
                  <tr>
                    <th>状态</th>
                    <td>
                      <span v-if="job.active" class="badge bg-success">活跃</span>
                      <span v-else class="badge bg-warning">已暂停</span>
                    </td>

                  </tr>
                <tr>
                  <th>创建用户</th>
                  <td>{{ job.user?.nickname ||job.user?.username || '未知' }}</td>
                </tr>
                </tbody>
              </table>
            </div>
            <div class="col-md-6">
              <h6 class="text-muted">执行信息</h6>
              <table class="table">
                <tbody>
                  <tr>
                    <th style="width: 30%">下次执行时间</th>
                    <td>{{ job.next_run_time || '暂无计划' }}</td>
                  </tr>
                  <tr v-if="job.type === 'cron'">
                    <th>Cron表达式</th>
                    <td>
                      <code>{{ job.cron_expression }}</code>
                    </td>
                  </tr>
                  <tr v-if="job.type === 'cron'">
                    <th>表达式描述</th>
                    <td>{{ job.cron_description }}</td>
                  </tr>
                  <tr v-else-if="job.type === 'interval'">
                    <th>时间间隔</th>
                    <td>{{ job.interval_description }}</td>
                  </tr>
                  <tr v-else>
                    <th>执行时间</th>
                    <td>{{ job.trigger }}</td>
                  </tr>
                  <tr>
                    <th>创建时间</th>
                    <td>{{ job.created_at }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div v-if="job.last_run_info && job.last_run_info.length">
            <h6 class="text-muted mt-4">最近执行记录</h6>
            <div class="table-responsive">
              <table class="table table-bordered table-hover">
                <thead class="table-light">
                  <tr>
                    <th>执行时间</th>
                    <th>执行结果</th>
                    <th>耗时</th>
                    <th>状态</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="run in job.last_run_info" :key="run.run_time">
                    <td>{{ run.run_time }}</td>
                    <td>
                      <div v-if="run.result" class="text-truncate" style="max-width: 300px">
                        {{ run.result }}
                      </div>
                      <span v-else class="text-muted">无返回值</span>
                    </td>
                    <td>{{ run.duration }}秒</td>
                    <td>
                      <span v-if="run.success" class="badge bg-success">成功</span>
                      <span v-else class="badge bg-danger">失败</span>
                      <button
                        v-if="!run.success"
                        class="btn btn-link text-danger p-0 ms-2"
                        data-bs-toggle="tooltip"
                        data-bs-placement="top"
                        :title="run.error"
                      >
                        <i class="fas fa-exclamation-circle"></i>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div v-else class="alert alert-info mt-4">
            <i class="fas fa-info-circle me-2"></i> 该任务暂无执行记录
          </div>
        </div>
        <div class="card-footer">
          <div class="d-flex gap-2">
            <button v-if="job.active" class="btn btn-warning" @click="pauseJob">
              <i class="fas fa-pause me-1"></i> 暂停任务
            </button>
            <button v-else class="btn btn-success" @click="resumeJob">
              <i class="fas fa-play me-1"></i> 恢复任务
            </button>
            <button class="btn btn-primary" @click="runJob" :disabled="isRunning">
              <i v-if="!isRunning" class="fas fa-bolt me-1"></i>
              <span v-if="!isRunning">立即执行</span>
              <span
                v-if="isRunning"
                class="spinner-border spinner-border-sm"
                role="status"
                aria-hidden="true"
              ></span>
              <span v-if="isRunning"> 执行中...</span>
            </button>
            <button class="btn btn-danger" @click="showDeleteModal">
              <i class="fas fa-trash-alt me-1"></i> 删除任务
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="alert alert-warning">
      <i class="fas fa-exclamation-triangle me-2"></i> 未找到任务信息
    </div>
  </div>

  <!-- 删除确认对话框 -->
  <div
    class="modal fade"
    id="deleteConfirmModal"
    tabindex="-1"
    aria-labelledby="deleteConfirmModalLabel"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="deleteConfirmModalLabel">确认删除</h5>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <p>
            您确定要删除任务 <strong>{{ job?.job_id }}</strong> 吗？
          </p>
          <p class="text-danger">此操作不可逆，删除后任务将无法恢复。</p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
          <button type="button" class="btn btn-danger" @click="deleteJob">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Modal } from 'bootstrap'; // 添加这行
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {runScheduleJobApi, resumeJobApi, pauseJobApi, getJobDetail,deleteJobApi} from '@/api/scheduler.js'
import  Toast from '@/utils/toast.js'

export default {
  setup() {
    const route = useRoute()
    const router = useRouter()
    const job = ref(null)
    const isRunning = ref(false)
    const deleteModal = ref(null)

    const getJobIcon = (type) => {
      switch (type) {
        case 'cron':
          return 'fa-clock'
        case 'interval':
          return 'fa-sync'
        default:
          return 'fa-calendar-day'
      }
    }

    const fetchJobDetails = async () => {
      try {
        const response = await getJobDetail(route.params.id)
        job.value = response.data
      } catch (error) {
        console.error('Error fetching job details:', error)
        Toast.error('获取失败', '获取任务详情时发生错误', false)
      }
    }


    const pauseJob = async () => {
      try {
        const response = await pauseJobApi(job.value.id)
        Toast.success('操作成功', '任务已暂停')
        setTimeout(() => {
          fetchJobDetails()
        }, 1000)
      } catch (error) {
        Toast.error('操作失败', error.response?.data?.detail || '暂停任务失败', false)
      }
    }

    const resumeJob = async () => {
      try {
        const response = await resumeJobApi(job.value.id)
        Toast.success('操作成功', '任务已恢复')
        setTimeout(() => {
          fetchJobDetails()
        }, 1000)
      } catch (error) {
        Toast.error('操作失败', error.response?.data?.detail || '恢复任务失败', false)
      }
    }

    const runJob = async () => {
      isRunning.value = true
      try {
        const response = await runScheduleJobApi(job.value.id)
        Toast.success('操作成功', '任务已执行')
        setTimeout(() => {
          fetchJobDetails()
        }, 1000)
      } catch (error) {
        Toast.error('操作失败', error.response?.data?.detail || '执行任务失败', false)
      } finally {
        isRunning.value = false
      }
    }

    const showDeleteModal = () => {
      deleteModal.value = new Modal(document.getElementById('deleteConfirmModal'))
      deleteModal.value.show()
    }

    const deleteJob = async () => {
      try {
        const response = await deleteJobApi(job.value.id)
        Toast.success('操作成功', '任务已删除')
        deleteModal.value.hide()
        setTimeout(() => {
          router.push('/scheduler')
        }, 1000)
      } catch (error) {
        Toast.error('操作失败', error.response?.data?.detail || '删除任务失败', false)
      }
    }

    onMounted(() => {
      fetchJobDetails()

      // Initialize tooltips
      const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]'),
      )
      tooltipTriggerList.forEach((tooltipTriggerEl) => {
        new Tooltip(tooltipTriggerEl)
      })
    })

    return {
      job,
      isRunning,
      getJobIcon,
      pauseJob,
      resumeJob,
      runJob,
      showDeleteModal,
      deleteJob,
    }
  },
}
</script>