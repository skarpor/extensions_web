import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// 导入Bootstrap和FontAwesome
import 'bootstrap/dist/css/bootstrap.min.css'
import '../static/js/bootstrap.bundle.min.js'
import '@fortawesome/fontawesome-free/css/all.min.css'

// import './assets/main.css'
//cors
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import vuetify from './plugins/vuetify'
const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(Toast, {
    position: 'top-left',
    timeout: 3000,
    closeOnClick: true,
    pauseOnFocusLoss: true,
    pauseOnHover: true,
    draggable: true,
    draggablePercent: 0.6,
  })
app.use(vuetify)
app.mount('#app')