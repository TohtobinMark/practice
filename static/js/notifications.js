// static/js/notifications.js

class NotificationManager {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // Создаем контейнер для уведомлений
        if (!document.querySelector('.toast-container-custom')) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container-custom';
            document.body.appendChild(this.container);
        } else {
            this.container = document.querySelector('.toast-container-custom');
        }
    }

    show(options) {
        const {
            type = 'info',      // success, error, warning, info, confirm
            title = '',
            message = '',
            duration = 5000,    // время отображения в мс
            onConfirm = null,   // для confirm
            onCancel = null     // для confirm
        } = options;

        if (type === 'confirm') {
            this.showConfirmDialog({ title, message, onConfirm, onCancel });
            return;
        }

        const toast = this.createToast({ type, title, message });
        this.container.appendChild(toast);

        // Автоматическое скрытие через duration
        if (duration > 0) {
            setTimeout(() => {
                this.hideToast(toast);
            }, duration);
        }
    }

    createToast({ type, title, message }) {
        const toast = document.createElement('div');
        toast.className = `custom-toast ${type}`;

        const icon = this.getIcon(type);
        const headerBg = this.getHeaderBg(type);

        toast.innerHTML = `
            <div class="toast-header-custom">
                <i class="${icon}"></i>
                <strong>${title}</strong>
                <button class="toast-close">&times;</button>
            </div>
            <div class="toast-body-custom">
                ${message}
            </div>
        `;

        // Кнопка закрытия
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            this.hideToast(toast);
        });

        return toast;
    }

    showConfirmDialog({ title, message, onConfirm, onCancel }) {
        // Создаем модальное окно подтверждения
        const modal = document.createElement('div');
        modal.className = 'custom-modal-overlay';
        modal.innerHTML = `
            <div class="custom-modal">
                <div class="custom-modal-header">
                    <i class="bi bi-question-circle"></i>
                    <strong>${title || 'Подтверждение действия'}</strong>
                </div>
                <div class="custom-modal-body">
                    ${message}
                </div>
                <div class="custom-modal-footer">
                    <button class="btn-modal btn-modal-cancel">Отмена</button>
                    <button class="btn-modal btn-modal-confirm">Подтвердить</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Закрытие при клике на фон
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
                if (onCancel) onCancel();
            }
        });

        // Кнопка подтверждения
        const confirmBtn = modal.querySelector('.btn-modal-confirm');
        confirmBtn.addEventListener('click', () => {
            modal.remove();
            if (onConfirm) onConfirm();
        });

        // Кнопка отмены
        const cancelBtn = modal.querySelector('.btn-modal-cancel');
        cancelBtn.addEventListener('click', () => {
            modal.remove();
            if (onCancel) onCancel();
        });
    }

    hideToast(toast) {
        toast.classList.add('hiding');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 300);
    }

    getIcon(type) {
        const icons = {
            success: 'bi bi-check-circle-fill',
            error: 'bi bi-x-circle-fill',
            warning: 'bi bi-exclamation-triangle-fill',
            info: 'bi bi-info-circle-fill',
            confirm: 'bi bi-question-circle-fill'
        };
        return icons[type] || icons.info;
    }

    getHeaderBg(type) {
        const bg = {
            success: '#d4edda',
            error: '#f8d7da',
            warning: '#fff3cd',
            info: '#d1ecf1'
        };
        return bg[type] || bg.info;
    }

    // Быстрые методы
    success(title, message, duration = 5000) {
        this.show({ type: 'success', title, message, duration });
    }

    error(title, message, duration = 5000) {
        this.show({ type: 'error', title, message, duration });
    }

    warning(title, message, duration = 5000) {
        this.show({ type: 'warning', title, message, duration });
    }

    info(title, message, duration = 5000) {
        this.show({ type: 'info', title, message, duration });
    }

    confirm(title, message, onConfirm, onCancel) {
        this.show({ type: 'confirm', title, message, onConfirm, onCancel });
    }
}

// Инициализация глобального объекта
window.notify = new NotificationManager();