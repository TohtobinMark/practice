// static/js/custom.js
// Общие функции для всего сайта

// Функция для отображения toast-уведомлений
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        createToastContainer();
    }

    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    document.getElementById('toast-container').innerHTML += toastHTML;
    const toastElement = new bootstrap.Toast(document.getElementById(toastId));
    toastElement.show();

    // Удаляем toast после скрытия
    document.getElementById(toastId).addEventListener('hidden.bs.toast', function () {
        this.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    container.style.zIndex = '1055';
    document.body.appendChild(container);
}

// Функция для подтверждения действий
function confirmAction(message, callback) {
    if (confirm(message)) {
        if (typeof callback === 'function') {
            callback();
        }
        return true;
    }
    return false;
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Автоматическое скрытие alert через 5 секунд
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Добавляем обработчики для всех ссылок с подтверждением
    document.querySelectorAll('a[data-confirm]').forEach(link => {
        link.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirmAction(message)) {
                e.preventDefault();
            }
        });
    });
});