<template>
    <div class="home">
        <h1>数据查询系统</h1>
        <div class="card-container">
            <div class="card" @click="navigateTo('/extension-query')">
                <h2>扩展查询</h2>
                <p>查询扩展信息</p>
            </div>
            <div class="card" @click="navigateTo('/extensions')">
                <h2>扩展管理</h2>
                <p>管理系统扩展功能</p>
            </div>
            <!-- newauto-->
             <div class="card" @click="navigateTo('/newauto')">
                <h2>新自动</h2>
                <p>新自动功能</p>
             </div>
            <div class="card" @click="navigateTo('/chat')">
                <h2>聊天</h2>
                <p>实时聊天功能，支持群聊和私聊</p>
            </div>
            <div class="card" @click="navigateTo('/files')">
                <h2>文件管理</h2>
                <p>上传、下载和管理文件</p>
            </div>
            <div class="card" @click="navigateTo('/settings')">
                <h2>系统设置</h2>
                <p>配置系统参数和用户权限</p>
            </div>
            <!--dashboard-->
            <div class="card" @click="navigateTo('/dashboard')">
                <h2>控制面板</h2>
                <p>管理系统控制面板</p>
            </div>
            <!-- profile-->
            <div class="card" @click="navigateTo('/profile')">
                <h2>用户信息</h2>
                <p>查看和管理用户信息</p>
            </div>
            <!--权限管理-->
            <div class="card" @click="navigateTo('/permissions')">
                <h2>权限管理</h2>
                <p>管理系统权限</p>
            </div>
            <!--DB -->
            <div class="card" @click="navigateTo('/database')">
                <h2>数据库管理</h2>
                <p>管理系统数据库</p>
            </div>
            <!---->
            <div class="card" @click="navigateTo('/scheduler')">
                <h2>定时器调度</h2>
                <p>管理任务定时器</p>
            </div>
            <div class="card" @click="navigateTo('/log')">
                <h2>日志查询</h2>
                <p>查看系统运行日志</p>
            </div>

        </div>
    </div>
</template>

<script>
    export default {
        name: 'HomeView',
        methods: {
            navigateTo(path) {
                this.$router.push(path)
            }
        }
    }
</script>

<style scoped>
    .home {
        text-align: center;
        padding: 2rem;
    }

    h1 {
        font-size: 2.5rem;
        margin-bottom: 2rem;
        color: #2c3e50;
    }

    .card-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 2rem;
    }

    .card {
        width: 250px;
        padding: 1.5rem;
        border-radius: 8px;
        background-color: #f8f9fa;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        cursor: pointer;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
    }

    h2 {
        font-size: 1.5rem;
        margin-bottom: 1rem;
        color: #3498db;
    }

    p {
        color: #666;
    }
</style>