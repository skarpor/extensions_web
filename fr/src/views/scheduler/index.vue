<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>定时任务管理</h2>
      <router-link to="/scheduler/add" class="btn btn-primary">
        <i class="fas fa-plus"></i> 添加新任务
      </router-link>
    </div>

    <div class="row">
      <div class="col-md-12">
        <div class="card mb-4">
          <div class="card-header">
            <ul class="nav nav-tabs card-header-tabs" id="myTab" role="tablist">
              <li class="nav-item" role="presentation">
                <button class="nav-link active text-dark" id="all-tab" data-bs-toggle="tab" data-bs-target="#all" type="button" role="tab" aria-controls="all" aria-selected="true">
                  所有任务 <span class="badge bg-primary">{{ jobs.length }}</span>
                </button>
              </li>
              <li v-for="(jobList, jobType) in groupedJobs" :key="jobType" class="nav-item" role="presentation">
                <button class="nav-link text-dark" :id="`${jobType}-tab`" data-bs-toggle="tab" :data-bs-target="`#${jobType}`" type="button" role="tab" :aria-controls="jobType" aria-selected="false">
                  {{ taskTypes[jobType] }} <span class="badge bg-secondary">{{ jobList.length }}</span>
                </button>
              </li>
            </ul>
          </div>
          <div class="card-body">
            <div class="tab-content" id="myTabContent">
              <!-- 所有任务 -->
              <div class="tab-pane fade show active" id="all" role="tabpanel" aria-labelledby="all-tab">
                <div v-if="jobs.length" class="table-responsive">
                  <table class="table table-striped table-hover">
                    <thead>
                      <tr>
                        <th>任务ID</th>
                        <th>类型</th>
                        <th>函数</th>
                        <th>下次执行时间</th>
                        <th>操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="job in jobs" :key="job.id">
                        <td>
                          <router-link :to="`/scheduler/job/${job.id}`" class="text-decoration-none partial-content" :title="job.id">
                            {{ job.id }}
                          </router-link>
                        </td>
                        <td>
                          <span v-if="job.trigger.toLowerCase().includes('cron')" class="badge bg-primary">Cron</span>
                          <span v-else-if="job.trigger.toLowerCase().includes('interval')" class="badge bg-success">间隔</span>
                          <span v-else class="badge bg-warning">一次性</span>
                        </td>
                        <td class="partial-content" :title="job.func">{{ job.func }}</td>
                        <td>{{ job.next_run_time || "已暂停" }}</td>
                        <td>
                          <div class="btn-group btn-group-sm" role="group">
                            <router-link :to="`/scheduler/job/${job.id}`" class="btn btn-info" title="详情">
                              <i class="fas fa-info-circle"></i>
                            </router-link>
                            <button class="btn btn-success run-job" :data-job-id="job.id" title="立即执行" @click="runJob(job.id)">
                              <i class="fas fa-play"></i>
                            </button>
                            <button v-if="job.next_run_time" class="btn btn-warning pause-job" :data-job-id="job.id" title="暂停" @click="pauseJob(job.id)">
                              <i class="fas fa-pause"></i>
                            </button>
                            <button v-else class="btn btn-primary resume-job" :data-job-id="job.id" title="恢复" @click="resumeJob(job.id)">
                              <i class="fas fa-play-circle"></i>
                            </button>
                            <button class="btn btn-danger delete-job" :data-job-id="job.id" title="删除" @click="confirmDelete(job.id)">
                              <i class="fas fa-trash"></i>
                            </button>
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-else class="alert alert-info">
                  <i class="fas fa-info-circle"></i> 暂无任务，请点击右上角的"添加新任务"按钮创建一个任务。
                </div>
              </div>

              <!-- 按类型分组的任务 -->
              <div v-for="(jobList, jobType) in groupedJobs" :key="jobType" class="tab-pane fade" :id="jobType" role="tabpanel" :aria-labelledby="`${jobType}-tab`">
                <div v-if="jobList.length" class="table-responsive">
                  <table class="table table-striped table-hover">
                    <thead>
                      <tr>
                        <th>任务ID</th>
                        <th>函数</th>
                        <th>下次执行时间</th>
                        <th>操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="job in jobList" :key="job.id">
                        <td>
                          <router-link :to="`/scheduler/job/${job.id}`" class="text-decoration-none">
                            {{ job.id }}
                          </router-link>
                        </td>
                        <td>{{ job.func }}</td>
                        <td>{{ job.next_run_time || "已暂停" }}</td>
                        <td>
                          <div class="btn-group btn-group-sm" role="group">
                            <router-link :to="`/scheduler/job/${job.id}`" class="btn btn-info" title="详情">
                              <i class="fas fa-info-circle"></i>
                            </router-link>
                            <button class="btn btn-success run-job" :data-job-id="job.id" title="立即执行" @click="runJob(job.id)">
                              <i class="fas fa-play"></i>
                            </button>
                            <button v-if="job.next_run_time" class="btn btn-warning pause-job" :data-job-id="job.id" title="暂停" @click="pauseJob(job.id)">
                              <i class="fas fa-pause"></i>
                            </button>
                            <button v-else class="btn btn-primary resume-job" :data-job-id="job.id" title="恢复" @click="resumeJob(job.id)">
                              <i class="fas fa-play-circle"></i>
                            </button>
                            <button class="btn btn-danger delete-job" :data-job-id="job.id" title="删除" @click="confirmDelete(job.id)">
                              <i class="fas fa-trash"></i>
                            </button>
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-else class="alert alert-info">
                  <i class="fas fa-info-circle"></i> 暂无{{ taskTypes[jobType] }}，请点击右上角的"添加新任务"按钮创建一个任务。
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 快速说明 -->
    <div class="row mt-4">
      <div class="col-md-4">
        <div class="card">
          <div class="card-header bg-primary text-white">
            <i class="fas fa-clock"></i> Cron定时任务
          </div>
          <div class="card-body">
            <p>基于cron表达式的定时任务，可以在特定的时间点执行。</p>
            <p><strong>例如：</strong></p>
            <ul>
              <li><code>* * * * *</code> - 每分钟执行</li>
              <li><code>0 * * * *</code> - 每小时整点执行</li>
              <li><code>0 9 * * 1-5</code> - 工作日早上9点执行</li>
            </ul>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card">
          <div class="card-header bg-success text-white">
            <i class="fas fa-sync"></i> 间隔任务
          </div>
          <div class="card-body">
            <p>按固定时间间隔重复执行的任务。</p>
            <p><strong>例如：</strong></p>
            <ul>
              <li>每30秒执行一次</li>
              <li>每5分钟执行一次</li>
              <li>每天执行一次</li>
            </ul>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card">
          <div class="card-header bg-warning">
            <i class="fas fa-calendar-day"></i> 一次性任务
          </div>
          <div class="card-body">
            <p>在指定的日期和时间执行一次，执行后自动从调度器中移除。</p>
            <p><strong>例如：</strong></p>
            <ul>
              <li>2025-12-31 23:59:59</li>
              <li>明天上午10点</li>
              <li>1小时后</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 确认删除模态框 -->
  <div class="modal fade" id="deleteModal" tabindex="-1" aria-labelledby="deleteModalLabel" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="deleteModalLabel">确认删除</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          确定要删除任务 <span id="deleteJobId" class="fw-bold">{{ jobToDelete }}</span> 吗？此操作不可恢复。
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
import { ref, onMounted } from 'vue';
import {
  getJobs,
  getJobDetail, resumeJobApi, deleteJobApi, pauseJobApi, runScheduleJobApi
} from '@/api/scheduler';
import Toast from '@/utils/toast.js';

export default {
    props: ['activeTab'], // 添加这行
    setup(props) {
	const xx=props.activeTab; // 可以访问 props.activeTab
	const jobs = ref([]);
    const groupedJobs = ref({});
    const taskTypes = ref({});
    const jobToDelete = ref(null);

    const fetchJobs = async () => {
      try {
        const response = await getJobs();
        jobs.value = response.data|| [];

        const grouped = {
          cron: [],
          interval: [],
          date: []
        };
        jobs.value.forEach(job => {
          if (job.trigger && job.trigger.toLowerCase().includes('cron')) {
            grouped.cron.push(job);
          } else if (job.trigger && job.trigger.toLowerCase().includes('interval')) {
            grouped.interval.push(job);
          } else {
            grouped.date.push(job);
          }
        });
        groupedJobs.value = {};
        taskTypes.value = response.data.task_types;
      } catch (error) {
        console.error('Error fetching jobs:', error);
        Toast.error('获取失败', '获取任务列表时发生错误', false);
      }
    };


    const runJob = async (jobId) => {
      try {
        const response = await runScheduleJobApi(jobId);
        Toast.success('执行成功', response.data.message);
      } catch (error) {
        Toast.error('执行失败', error.response?.data?.message || '请求执行任务时发生错误', false);
      }
    };

    const pauseJob = async (jobId) => {
      try {
        const response = await pauseJobApi(jobId);
        Toast.success('暂停成功', response.data.message);
        setTimeout(() => {
          fetchJobs();
        }, 1000);
      } catch (error) {
        Toast.error('暂停失败', error.response?.data?.message || '请求暂停任务时发生错误', false);
      }
    };

    const resumeJob = async (jobId) => {
      try {
        const response = await resumeJobApi(jobId);
        Toast.success('恢复成功', response.data.message);
        setTimeout(() => {
          fetchJobs();
        }, 1000);
      } catch (error) {
        Toast.error('恢复失败', error.response?.data?.message || '请求恢复任务时发生错误', false);
      }
    };

    const confirmDelete = (jobId) => {
      jobToDelete.value = jobId;
      const deleteModal = new Modal(document.getElementById('deleteModal'));
      deleteModal.show();
    };

    const deleteJob = async () => {
      if (!jobToDelete.value) return;

      try {
        const response = await deleteJobApi(jobToDelete.value);
        Toast.success('删除成功', response.data.message);
        const deleteModal = Modal.getInstance(document.getElementById('deleteModal'));
        deleteModal.hide();
        setTimeout(() => {
          fetchJobs();
        }, 1000);
      } catch (error) {
        Toast.error('删除失败', error.response?.data?.message || '请求删除任务时发生错误', false);
      }
    };

    onMounted(() => {
      fetchJobs();
    });

    return {
      jobs,
      groupedJobs,
      taskTypes,
      jobToDelete,
      runJob,
      pauseJob,
      resumeJob,
      confirmDelete,
      deleteJob
    };
  }
};
</script>

<style scoped>
.text-dark {
  color: #6c757d !important;
}
</style>