// 定义Toast组件
const toastEl = document.getElementById('liveToast');
const toast = new bootstrap.Toast(toastEl);

// 显示Toast消息
function showToast(title, message, isSuccess = true) {
    console.log(title, message, isSuccess, 'info')

    const toastTitle = document.getElementById('toastTitle');
    const toastMessage = document.getElementById('toastMessage');
    
    toastTitle.textContent = title;
    toastMessage.textContent = message;
    
    // 设置Toast颜色
    toastEl.className = isSuccess 
        ? 'toast text-white bg-success'
        : 'toast text-white bg-danger';
    
    toast.show();
}
export default showToast