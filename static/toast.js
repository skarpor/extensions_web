// 这是一个需要被导入后，可以直接使用的函数
// 导入后，直接使用showToast函数即可

async function showToast (message, type = 'danger', delay = 3000){
    // 获取或创建容器
    // 如果容器不存在，则创建一个
    
    // 如果容器存在，则清空容器

    let container = document.getElementById('toast-container');
    if (!container) {
        let html = `
        <div id="toast-container" class="position-fixed top-0 end-0 p-3" style="z-index: 9999">
          <div id="toast-template" class="toast align-items-center text-white" role="alert" aria-live="assertive" aria-atomic="true" style="display: none; min-width: 250px;">
            <div class="d-flex">
              <div class="toast-body"></div>
              <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
          </div>
        </div>
        `;
        document.body.insertAdjacentHTML('beforeend', html);
        container = document.getElementById('toast-container');
    }


// 克隆模板
    const template = document.getElementById('toast-template');
    const toast = template.cloneNode(true);
    toast.id = '';
    toast.style.display = '';
    toast.classList.add(`bg-${type}`);

    // 设置消息内容
    toast.querySelector('.toast-body').textContent = message;

    // 添加到容器
    container.appendChild(toast);

    // 初始化Bootstrap Toast（即使不使用它的显示/隐藏逻辑）
    const bsToast = new bootstrap.Toast(toast, { autohide: false });

    // 显示toast
    toast.classList.add('show');

    // 自动隐藏
    const hideToast = () => {
      toast.classList.add('hiding');
      setTimeout(() => {
        bsToast.dispose();
        toast.remove();
      }, 300);
    };

    const timeoutId = setTimeout(hideToast, delay);

    // 点击关闭按钮
    toast.querySelector('[data-bs-dismiss="toast"]').addEventListener('click', () => {
      clearTimeout(timeoutId);
      hideToast();
    });

    return {
      hide: () => {
        clearTimeout(timeoutId);
        hideToast();
      }
    };
  }



