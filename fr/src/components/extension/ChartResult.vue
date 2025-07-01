<template>
    <div class="chart-result">
      <div v-if="!result || loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>
      <div v-else-if="error" class="error-container">
        <el-alert
          title="加载数据失败"
          type="error"
          :description="error"
          show-icon
        />
      </div>
      <div v-else-if="!hasData" class="empty-container">
        <el-empty description="没有数据" />
      </div>
      <div v-else class="chart-container">
        <div ref="chartRef" class="chart-element"></div>
        
        <div class="chart-actions">
          <el-radio-group v-model="chartType" size="small">
            <el-radio-button label="line">折线图</el-radio-button>
            <el-radio-button label="bar">柱状图</el-radio-button>
            <el-radio-button label="pie">饼图</el-radio-button>
          </el-radio-group>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { defineComponent, ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
  import * as echarts from 'echarts/core'
  import { LineChart, BarChart, PieChart } from 'echarts/charts'
  import {
    TitleComponent,
    TooltipComponent,
    LegendComponent,
    GridComponent,
    DatasetComponent,
    TransformComponent
  } from 'echarts/components'
  import { LabelLayout, UniversalTransition } from 'echarts/features'
  import { CanvasRenderer } from 'echarts/renderers'
  
  // 注册必要的组件
  echarts.use([
    TitleComponent,
    TooltipComponent,
    LegendComponent,
    GridComponent,
    DatasetComponent,
    TransformComponent,
    LineChart,
    BarChart,
    PieChart,
    LabelLayout,
    UniversalTransition,
    CanvasRenderer
  ])
  
  export default defineComponent({
    name: 'ChartResult',
    props: {
      result: {
        type: [Object, Array],
        default: () => ({})
      },
      loading: {
        type: Boolean,
        default: false
      },
      error: {
        type: String,
        default: ''
      },
      extension: {
        type: Object,
        default: () => ({})
      }
    },
    setup(props) {
      const chartRef = ref(null)
      const chartInstance = ref(null)
      const chartType = ref('line')
      
      // 计算图表数据
      const chartData = computed(() => {
        if (!props.result) return []
        
        // 如果结果是数组，直接使用
        if (Array.isArray(props.result)) {
          return props.result
        }
        
        // 如果结果是对象，尝试获取data属性
        if (props.result.data && Array.isArray(props.result.data)) {
          return props.result.data
        }
        
        // 如果结果是对象，尝试获取其他常见属性
        if (props.result.rows && Array.isArray(props.result.rows)) {
          return props.result.rows
        }
        
        if (props.result.items && Array.isArray(props.result.items)) {
          return props.result.items
        }
        
        if (props.result.records && Array.isArray(props.result.records)) {
          return props.result.records
        }
        
        return []
      })
      
      // 检查是否有数据
      const hasData = computed(() => chartData.value && chartData.value.length > 0)
      
      // 初始化图表
      const initChart = () => {
        if (chartInstance.value) {
          chartInstance.value.dispose()
        }
        
        if (!chartRef.value) return
        
        chartInstance.value = echarts.init(chartRef.value)
        updateChart()
      }
      
      // 更新图表
      const updateChart = () => {
        if (!chartInstance.value || !hasData.value) return
        
        const option = generateChartOption()
        chartInstance.value.setOption(option)
      }
      
      // 生成图表配置
      const generateChartOption = () => {
        const data = chartData.value
        
        // 尝试找到合适的数值和类别字段
        const firstItem = data[0]
        const keys = Object.keys(firstItem)
        
        // 找到第一个数值字段作为值
        const valueKey = keys.find(key => typeof firstItem[key] === 'number') || keys[1] || keys[0]
        
        // 找到第一个非数值字段作为类别
        const categoryKey = keys.find(key => typeof firstItem[key] !== 'number') || keys[0]
        
        // 准备数据
        const categories = data.map(item => item[categoryKey])
        const values = data.map(item => item[valueKey])
        
        // 根据图表类型生成不同配置
        if (chartType.value === 'pie') {
          return {
            title: {
              text: '数据图表',
              left: 'center'
            },
            tooltip: {
              trigger: 'item',
              formatter: '{a} <br/>{b} : {c} ({d}%)'
            },
            legend: {
              orient: 'vertical',
              left: 'left',
              data: categories
            },
            series: [
              {
                name: valueKey,
                type: 'pie',
                radius: '55%',
                center: ['50%', '60%'],
                data: data.map(item => ({
                  name: item[categoryKey],
                  value: item[valueKey]
                })),
                emphasis: {
                  itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                  }
                }
              }
            ]
          }
        } else {
          // 折线图或柱状图
          return {
            title: {
              text: '数据图表',
              left: 'center'
            },
            tooltip: {
              trigger: 'axis'
            },
            xAxis: {
              type: 'category',
              data: categories,
              axisLabel: {
                rotate: 45,
                interval: 0
              }
            },
            yAxis: {
              type: 'value'
            },
            series: [
              {
                name: valueKey,
                type: chartType.value,
                data: values
              }
            ]
          }
        }
      }
      
      // 监听窗口大小变化
      const handleResize = () => {
        if (chartInstance.value) {
          chartInstance.value.resize()
        }
      }
      
      // 监听数据和图表类型变化
      watch(() => [props.result, chartType.value], () => {
        updateChart()
      }, { deep: true })
      
      // 生命周期钩子
      onMounted(() => {
        initChart()
        window.addEventListener('resize', handleResize)
      })
      
      onBeforeUnmount(() => {
        if (chartInstance.value) {
          chartInstance.value.dispose()
        }
        window.removeEventListener('resize', handleResize)
      })
      
      return {
        chartRef,
        chartType,
        hasData
      }
    }
  })
  </script>
  
  <style scoped>
  .chart-result {
    width: 100%;
  }
  
  .loading-container,
  .error-container,
  .empty-container {
    padding: 20px;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  
  .chart-container {
    margin-top: 10px;
  }
  
  .chart-element {
    width: 100%;
    height: 400px;
  }
  
  .chart-actions {
    margin-top: 15px;
    display: flex;
    justify-content: center;
  }
  </style>