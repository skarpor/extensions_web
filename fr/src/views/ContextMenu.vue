<template>
    <div 
      v-if="visible" 
      class="context-menu" 
      :style="{ left: `${position.x}px`, top: `${position.y}px` }"
      @click.stop
    >
      <div 
        v-for="(item, index) in items" 
        :key="index" 
        class="context-menu-item" 
        @click="handleClick(item)"
      >
        {{ item.label }}
      </div>
    </div>
  </template>
  
  <script>
  export default {
    props: {
      items: {
        type: Array,
        required: true
      }
    },
    data() {
      return {
        visible: false,
        position: { x: 0, y: 0 }
      }
    },
    methods: {
    showMenu(x, y) {
        // 检查右边界
        const viewportWidth = window.innerWidth;
        const menuWidth = 200; // 假设菜单宽度
        if (x + menuWidth > viewportWidth) {
            x = viewportWidth - menuWidth;
        }
        
        // 检查下边界
        const viewportHeight = window.innerHeight;
        const menuHeight = this.items.length * 40; // 假设每项高度40px
        if (y + menuHeight > viewportHeight) {
            y = viewportHeight - menuHeight;
        }
        
        this.position = { x, y };
        this.visible = true;
        document.addEventListener('click', this.closeMenu)
    },
      closeMenu() {
        this.visible = false
        document.removeEventListener('click', this.closeMenu)
      },
      handleClick(item) {
        this.$emit('select', item)
        this.closeMenu()
      }
    }
  }
  </script>
  
  <style scoped>
  .context-menu {
    position: fixed;
    background: white;
    border: 1px solid #ccc;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    z-index: 1000;
    min-width: 120px;
  }
  
  .context-menu-item {
    padding: 8px 12px;
    cursor: pointer;
  }
  
  .context-menu-item:hover {
    background-color: #f0f0f0;
  }
  </style>