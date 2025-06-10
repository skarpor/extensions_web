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

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')