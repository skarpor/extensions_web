<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>添加定时任务</h2>
      <router-link to="/scheduler" class="btn btn-outline-secondary">
        <i class="fas fa-arrow-left"></i> 返回任务列表
      </router-link>
    </div>

    <div class="card">
      <div class="card-header">
        <ul class="nav nav-tabs card-header-tabs" id="taskTypeTabs" role="tablist">
          <li class="nav-item" role="presentation">
            <button class="nav-link active text-dark" id="cron-tab" data-bs-toggle="tab" data-bs-target="#cron" type="button" role="tab" aria-controls="cron" aria-selected="true">
              <i class="fas fa-clock"></i> Cron定时任务
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button class="nav-link text-dark" id="interval-tab" data-bs-toggle="tab" data-bs-target="#interval" type="button" role="tab" aria-controls="interval" aria-selected="false">
              <i class="fas fa-sync"></i> 间隔任务
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button class="nav-link text-dark" id="date-tab" data-bs-toggle="tab" data-bs-target="#date" type="button" role="tab" aria-controls="date" aria-selected="false">
              <i class="fas fa-calendar-day"></i> 一次性任务
            </button>
          </li>
        </ul>
      </div>
      <div class="card-body">
        <div class="tab-content" id="taskTypeTabContent">
          <!-- Cron任务表单 -->
          <div class="tab-pane fade show active" id="cron" role="tabpanel" aria-labelledby="cron-tab">
            <form id="cronForm" class="needs-validation" @submit.prevent="submitCronForm" novalidate>
              <div class="row mb-3">
                <div class="col-md-6">
                  <label for="cronTaskFunc" class="form-label">任务函数 <span class="text-danger">*</span></label>
                  <select class="form-select" id="cronTaskFunc" v-model="cronForm.task_func" required>
                    <option value="" selected disabled>请选择任务函数</option>
                    <option v-for="method in extensionMethods" :key="method.extension_id" :value="method.extension_id">
                      {{ method.extension_name }}
                    </option>
                  </select>
                  <div class="invalid-feedback">请选择任务函数</div>
                </div>
                <div class="col-md-6">
                  <label for="cronJobId" class="form-label">任务ID (可选)</label>
                  <input type="text" class="form-control" id="cronJobId" v-model="cronForm.job_id" placeholder="留空将自动生成">
                  <small class="form-text text-muted">指定一个唯一标识符，如不指定将自动生成</small>
                </div>
              </div>

              <div class="row mb-3">
                <div class="col-md-2">
                  <label for="cronMinute" class="form-label">分钟</label>
                  <input type="text" class="form-control" id="cronMinute" v-model="cronForm.minute" value="*">
                  <small class="form-text text-muted">0-59，*表示每分钟</small>
                </div>
                <div class="col-md-2">
                  <label for="cronHour" class="form-label">小时</label>
                  <input type="text" class="form-control" id="cronHour" v-model="cronForm.hour" value="*">
                  <small class="form-text text-muted">0-23，*表示每小时</small>
                </div>
                <div class="col-md-2">
                  <label for="cronDay" class="form-label">日期</label>
                  <input type="text" class="form-control" id="cronDay" v-model="cronForm.day" value="*">
                  <small class="form-text text-muted">1-31，*表示每天</small>
                </div>
                <div class="col-md-2">
                  <label for="cronMonth" class="form-label">月份</label>
                  <input type="text" class="form-control" id="cronMonth" v-model="cronForm.month" value="*">
                  <small class="form-text text-muted">1-12，*表示每月</small>
                </div>
                <div class="col-md-2">
                  <label for="cronDayOfWeek" class="form-label">星期</label>
                  <input type="text" class="form-control" id="cronDayOfWeek" v-model="cronForm.day_of_week" value="*">
                  <small class="form-text text-muted">0-6，*表示每天</small>
                </div>
                <div class="col-md-2">
                  <label for="cronSecond" class="form-label">秒</label>
                  <input type="text" class="form-control" id="cronSecond" v-model="cronForm.second" value="0">
                  <small class="form-text text-muted">0-59，默认为0</small>
                </div>
              </div>

              <div class="mb-3">
                <div class="form-text">
                  <strong>Cron表达式参考：</strong><br>
                  <code>* * * * *</code> - 每分钟执行<br>
                  <code>0 * * * *</code> - 每小时整点执行<br>
                  <code>0 9 * * 1-5</code> - 工作日早上9点执行<br>
                  <code>0 0 1 * *</code> - 每月1日零点执行<br>
                  <code>*/5 * * * *</code> - 每5分钟执行一次
                </div>
              </div>

              <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
                <i class="fas fa-plus"></i> 添加Cron任务
              </button>
            </form>
          </div>

          <!-- 间隔任务表单 -->
          <div class="tab-pane fade" id="interval" role="tabpanel" aria-labelledby="interval-tab">
            <form id="intervalForm" class="needs-validation" @submit.prevent="submitIntervalForm" novalidate>
              <div class="row mb-3">
                <div class="col-md-6">
                  <label for="intervalTaskFunc" class="form-label">任务函数 <span class="text-danger">*</span></label>
                  <select class="form-select" id="intervalTaskFunc" v-model="intervalForm.task_func" required>
                    <option value="" selected disabled>请选择任务函数</option>
                    <option v-for="method in extensionMethods" :key="method.extension_id" :value="method.extension_id">
                      {{ method.extension_name }}
                    </option>
                  </select>
                  <div class="invalid-feedback">请选择任务函数</div>
                </div>
                <div class="col-md-6">
                  <label for="intervalJobId" class="form-label">任务ID (可选)</label>
                  <input type="text" class="form-control" id="intervalJobId" v-model="intervalForm.job_id" placeholder="留空将自动生成">
                  <small class="form-text text-muted">指定一个唯一标识符，如不指定将自动生成</small>
                </div>
              </div>

              <div class="row mb-3">
                <div class="col-md-3">
                  <label for="intervalSeconds" class="form-label">秒</label>
                  <input type="number" class="form-control" id="intervalSeconds" v-model="intervalForm.seconds" min="0" value="0">
                </div>
                <div class="col-md-3">
                  <label for="intervalMinutes" class="form-label">分钟</label>
                  <input type="number" class="form-control" id="intervalMinutes" v-model="intervalForm.minutes" min="0" value="0">
                </div>
                <div class="col-md-3">
                  <label for="intervalHours" class="form-label">小时</label>
                  <input type="number" class="form-control" id="intervalHours" v-model="intervalForm.hours" min="0" value="0">
                </div>
                <div class="col-md-3">
                  <label for="intervalDays" class="form-label">天</label>
                  <input type="number" class="form-control" id="intervalDays" v-model="intervalForm.days" min="0" value="0">
                </div>
              </div>

              <div class="mb-3">
                <div class="form-text">
                  <strong>时间间隔参考：</strong><br>
                  必须至少指定一个时间单位（秒、分钟、小时或天）。<br>
                  例如：30秒 = 每30秒执行一次<br>
                  例如：5分钟 = 每5分钟执行一次<br>
                  例如：1天 = 每天执行一次
                </div>
              </div>

              <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
                <i class="fas fa-plus"></i> 添加间隔任务
              </button>
            </form>
          </div>

          <!-- 一次性任务表单 -->
          <div class="tab-pane fade" id="date" role="tabpanel" aria-labelledby="date-tab">
            <form id="dateForm" class="needs-validation" @submit.prevent="submitDateForm" novalidate>
              <div class="row mb-3">
                <div class="col-md-6">
                  <label for="dateTaskFunc" class="form-label">任务函数 <span class="text-danger">*</span></label>
                  <select class="form-select" id="dateTaskFunc" v-model="dateForm.task_func" required>
                    <option value="" selected disabled>请选择任务函数</option>
                    <option v-for="method in extensionMethods" :key="method.extension_id" :value="method.extension_id">
                      {{ method.extension_name }}
                    </option>
                  </select>
                  <div class="invalid-feedback">请选择任务函数</div>
                </div>
                <div class="col-md-6">
                  <label for="dateJobId" class="form-label">任务ID (可选)</label>
                  <input type="text" class="form-control" id="dateJobId" v-model="dateForm.job_id" placeholder="留空将自动生成">
                  <small class="form-text text-muted">指定一个唯一标识符，如不指定将自动生成</small>
                </div>
              </div>

              <div class="mb-3">
                <label for="runDate" class="form-label">执行时间 <span class="text-danger">*</span></label>
                <input type="datetime-local" class="form-control" id="runDate" v-model="dateForm.run_date" required>
                <div class="invalid-feedback">请选择有效的执行时间</div>
                <small class="form-text text-muted">执行时间必须在未来</small>
              </div>

              <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
                <i class="fas fa-plus"></i> 添加一次性任务
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>

</template>

<script>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { addJob,getExtensionMethods } from '@/api/scheduler.js';
import  Toast  from '@/utils/toast.js';

export default {
  setup() {
    const router = useRouter();
    const extensionMethods = ref([]);
    const isSubmitting = ref(false);

    const cronForm = ref({
      task_func: '',
      job_id: '',
      minute: '*',
      hour: '*',
      day: '*',
      month: '*',
      day_of_week: '*',
      second: '0'
    });

    const intervalForm = ref({
      task_func: '',
      job_id: '',
      seconds: 0,
      minutes: 0,
      hours: 0,
      days: 0
    });

    const dateForm = ref({
      task_func: '',
      job_id: '',
      run_date: ''
    });


    const fetchExtensionMethods = async () => {
      try {
        const response = await getExtensionMethods();
        extensionMethods.value = response.data.extension_methods;
      } catch (error) {
        console.error('Error fetching extension methods:', error);
        Toast.error('获取失败', '获取扩展方法时发生错误', false);
      }
    };

    const submitCronForm = async () => {
      const form = document.getElementById('cronForm');
      if (!form.checkValidity()) {
        form.classList.add('was-validated');
        Toast.error('验证失败', '请检查表单数据', false);
        return;
      }

      isSubmitting.value = true;
      try {
        const response = await addJob('cron',cronForm.value);
        Toast.success('添加成功', response.data.detail);
        setTimeout(() => {
          router.push('/scheduler');
        }, 1500);
      } catch (error) {
        Toast.error('添加失败', error.response?.data?.message || '添加任务时发生错误', false);
      } finally {
        isSubmitting.value = false;
      }
    };

    const submitIntervalForm = async () => {
      const form = document.getElementById('intervalForm');
      if (!form.checkValidity()) {
        form.classList.add('was-validated');
        Toast.error('验证失败', '请检查表单数据', false);
        return;
      }

      // 检查是否至少指定了一个时间间隔
      const { seconds, minutes, hours, days } = intervalForm.value;
      if (seconds === 0 && minutes === 0 && hours === 0 && days === 0) {
        Toast.error('验证失败', '必须至少指定一个时间间隔（秒、分钟、小时或天）', false);
        return;
      }

      isSubmitting.value = true;
      try {
        const response = await addJob('interval', intervalForm.value);
        Toast.success('添加成功', response.data.message);
        setTimeout(() => {
          router.push('/scheduler');
        }, 1500);
      } catch (error) {
        Toast.error('添加失败', error.response?.data?.message || '添加任务时发生错误', false);
      } finally {
        isSubmitting.value = false;
      }
    };

    const submitDateForm = async () => {
      const form = document.getElementById('dateForm');
      if (!form.checkValidity()) {
        form.classList.add('was-validated');
        Toast.error('验证失败', '请检查表单数据', false);
        return;
      }

      // 检查执行时间是否在未来
      const runDate = new Date(dateForm.value.run_date);
      const now = new Date();
      if (runDate <= now) {
        Toast.error('验证失败', '执行时间必须在未来', false);
        return;
      }

      isSubmitting.value = true;
      try {
        const formattedDate = runDate.toISOString().replace('T', ' ').substr(0, 19);
        const payload = {
          ...dateForm.value,
          run_date: formattedDate
        };
        const response = await addJob('date', payload);
        Toast.success('添加成功', response.data.message);
        setTimeout(() => {
          router.push('/scheduler');
        }, 1500);
      } catch (error) {
        Toast.error('添加失败', error.response?.data?.message || '添加任务时发生错误', false);
      } finally {
        isSubmitting.value = false;
      }
    };

    onMounted(() => {
      fetchExtensionMethods();

      // 设置默认的执行时间为1小时后
      const now = new Date();
      now.setHours(now.getHours() + 1);
      dateForm.value.run_date = now.toISOString().slice(0, 16);
    });

    return {
      extensionMethods,
      cronForm,
      intervalForm,
      dateForm,
      isSubmitting,
      submitCronForm,
      submitIntervalForm,
      submitDateForm
    };
  }
};
</script>

<style scoped>
.text-dark {
  color: #6c757d !important;
}
</style>