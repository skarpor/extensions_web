<template>
  <div class="file-view">
    <div class="doc-header">
      <div>
        <h1 class="doc-title">
          {{ filename }}
          <span class="file-type" :class="fileTypeClass">
            {{ fileType }}
          </span>
        </h1>
        <div class="text-muted mt-2">最后修改时间: {{ modifiedTime }}</div>
      </div>
      <router-link to="/" class="back-btn">
        <i class="fas fa-arrow-left"></i> 返回首页
      </router-link>
    </div>

    <div class="doc-content">
      <div v-if="contentType === 'html' || contentType === 'markdown'" v-html="content"></div>
      <div v-else>
        <pre ref="codeBlock"><code :class="codeClass">{{ content }}</code></pre>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import { viewFile } from '@/api/help';
import Prism from 'prismjs';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-c';
import 'prismjs/components/prism-cpp';
import 'prismjs/components/prism-java';
import 'prismjs/components/prism-kotlin';
import 'prismjs/components/prism-php';
import 'prismjs/components/prism-ruby';
import 'prismjs/components/prism-rust';
import 'prismjs/components/prism-sql';
import 'prismjs/components/prism-swift';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-yaml';
import 'prismjs/themes/prism-okaidia.css';

export default {
  setup() {
    const route = useRoute();
    const filename = route.params.filename;
    const fileType = ref('');
    const modifiedTime = ref('');
    const contentType = ref('');
    const content = ref('');
    const loading = ref(true);
    const codeBlock = ref(null);

    const loadContent = async () => {
      try {
        const response = await viewFile(filename);
        console.log('Received content type:', response.data.content_type);

        content.value = response.data.content;
        contentType.value = response.data.content_type;
        fileType.value = response.data.file_type;
        modifiedTime.value = response.data.modified_time;
      } finally {
        loading.value = false;
      }
    };

    // 修正：使用 .value 访问 ref 值
    const fileTypeClass = computed(() => {
      switch(fileType.value) {
        case '文档': return 'file-type-doc';
        case '示例扩展': return 'file-type-extension';
        case '示例页面': return 'file-type-page';
        default: return 'file-type-other';
      }
    });

    // 修正：使用 .value 访问 ref 值
    const codeClass = computed(() => {
      if (!contentType.value) return '';
      const typeMap = {
        'python': 'language-python',
        'text/x-python': 'language-python',
        // 其他常见类型
        'text/x-c': 'language-c',
        'text/x-c++': 'language-cpp',
        'text/x-java': 'language-java',
        'text/x-kotlin': 'language-kotlin',
        'text/x-php': 'language-php',
        'text/x-ruby': 'language-ruby',
        'text/x-rust': 'language-rust',
        'text/x-sql': 'language-sql',
        'text/x-swift': 'language-swift',
        'text/x-typescript': 'language-typescript',
        'text/x-yaml': 'language-yaml',//
      };
      return typeMap[contentType.value] || '';
    });

    // 添加内容变化监听，触发高亮
    watch([content, codeClass], () => {
      nextTick(() => {
    const codeElements = document.querySelectorAll('code');
    codeElements.forEach(el => {
      el.className = `language-python ${el.className}`;
    });
    Prism.highlightAll();
  });
  //     console.log('当前contentType:', contentType.value);
  //     console.log('计算出的codeClass:', codeClass.value);
  //     nextTick(() => {
  //       console.log('实际DOM类名:', codeBlock.value?.className);
  //   Prism.highlightElement(codeBlock.value);
  //   console.log('已执行高亮');
  // });
  //     if (codeBlock.value) {
  //       Prism.highlightElement(codeBlock.value);
  //     }
    });

    onMounted(() => {
      loadContent();
    });

    return {
      filename,
      fileType,
      modifiedTime,
      contentType,
      content,
      loading,
      fileTypeClass,
      codeClass,
      codeBlock
    };
  }
}
</script>
<style scoped>
.file-view {
  padding: 20px;
  width: 100%;
}

.doc-header {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.doc-title {
  color: var(--primary-color);
  margin: 0;
}

.doc-content {
  padding: 20px;
  line-height: 1.6;
  overflow-x: auto;
}

.doc-content h1, .doc-content h2, .doc-content h3 {
  color: var(--primary-color);
  margin-top: 1.5em;
  margin-bottom: 0.8em;
}

.doc-content h1 {
  font-size: 2rem;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.3em;
}

.doc-content h2 {
  font-size: 1.5rem;
}

.doc-content h3 {
  font-size: 1.2rem;
}

.doc-content code {
  background-color: var(--secondary-color);
  padding: 2px 4px;
  border-radius: 4px;
  font-family: SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 0.9em;
}

.doc-content pre {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 15px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 1.5em 0;
}

.doc-content pre code {
  background-color: transparent;
  padding: 0;
  color: inherit;
}

.doc-content blockquote {
  border-left: 4px solid var(--primary-color);
  padding-left: 15px;
  color: #666;
  margin: 1.5em 0;
}

.doc-content ul, .doc-content ol {
  padding-left: 2em;
}

.doc-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 1.5em 0;
}

.doc-content table th, .doc-content table td {
  border: 1px solid var(--border-color);
  padding: 8px 12px;
  text-align: left;
}

.doc-content table th {
  background-color: var(--secondary-color);
}

.doc-content img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 1.5em auto;
}

.back-btn {
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.back-btn:hover {
  background-color: var(--accent-color);
  transform: translateY(-1px);
  color: white;
  text-decoration: none;
}

.file-type {
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  margin-left: 10px;
  display: inline-block;
}

.file-type-doc {
  background-color: #e3f2fd;
  color: #0d47a1;
}

.file-type-extension {
  background-color: #e8f5e9;
  color: #1b5e20;
}

.file-type-page {
  background-color: #fff3e0;
  color: #e65100;
}

.file-type-other {
  background-color: #f5f5f5;
  color: #616161;
}
</style>