/**
 * Simple-ID Main JavaScript
 * MTV 패턴의 Template 레이어 인터랙션
 */

document.addEventListener('DOMContentLoaded', function() {
    // 알림 메시지 자동 숨김
    initAutoHideAlerts();
    
    // 툴팁 초기화
    initTooltips();
    
    // 폼 검증
    initFormValidation();
    
    // 테이블 정렬
    initTableSort();
    
    // 페이드인 애니메이션
    initFadeInAnimation();
    
    // 클립보드 복사
    initClipboard();
});

/**
 * 알림 메시지 5초 후 자동 숨김
 */
function initAutoHideAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

/**
 * Bootstrap 툴팁 초기화
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * 폼 실시간 검증
 */
function initFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // PIN 코드 입력 (숫자만)
    const pinInputs = document.querySelectorAll('input[name="pin_code"]');
    pinInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9]/g, '').slice(0, 6);
        });
    });
    
    // 전화번호 자동 포맷팅
    const phoneInputs = document.querySelectorAll('input[name="phone_number"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = this.value.replace(/[^0-9]/g, '');
            if (value.length > 3 && value.length <= 7) {
                value = value.slice(0, 3) + '-' + value.slice(3);
            } else if (value.length > 7) {
                value = value.slice(0, 3) + '-' + value.slice(3, 7) + '-' + value.slice(7, 11);
            }
            this.value = value;
        });
    });
}

/**
 * 테이블 정렬 기능
 */
function initTableSort() {
    const sortableTables = document.querySelectorAll('.table-sortable');
    
    sortableTables.forEach(table => {
        const headers = table.querySelectorAll('th[data-sort]');
        
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.innerHTML += ' <i class="fas fa-sort text-muted"></i>';
            
            header.addEventListener('click', function() {
                const column = this.dataset.sort;
                const rows = Array.from(table.querySelectorAll('tbody tr'));
                const sortOrder = this.dataset.order === 'asc' ? 'desc' : 'asc';
                
                // 정렬
                rows.sort((a, b) => {
                    const aValue = a.querySelector(`td[data-${column}]`).textContent;
                    const bValue = b.querySelector(`td[data-${column}]`).textContent;
                    
                    if (sortOrder === 'asc') {
                        return aValue > bValue ? 1 : -1;
                    } else {
                        return aValue < bValue ? 1 : -1;
                    }
                });
                
                // 재정렬된 행 삽입
                const tbody = table.querySelector('tbody');
                rows.forEach(row => tbody.appendChild(row));
                
                // 정렬 순서 업데이트
                this.dataset.order = sortOrder;
                
                // 아이콘 업데이트
                headers.forEach(h => {
                    const icon = h.querySelector('i');
                    icon.className = 'fas fa-sort text-muted';
                });
                const icon = this.querySelector('i');
                icon.className = sortOrder === 'asc' ? 'fas fa-sort-up text-primary' : 'fas fa-sort-down text-primary';
            });
        });
    });
}

/**
 * 페이드인 애니메이션
 */
function initFadeInAnimation() {
    const elements = document.querySelectorAll('.fade-in');
    
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, {
        threshold: 0.1
    });
    
    elements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

/**
 * 클립보드 복사 기능
 */
function initClipboard() {
    window.copyToClipboard = function(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                showToast('클립보드에 복사되었습니다!', 'success');
            }).catch(() => {
                showToast('복사에 실패했습니다.', 'danger');
            });
        } else {
            // Fallback
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            try {
                document.execCommand('copy');
                showToast('클립보드에 복사되었습니다!', 'success');
            } catch (err) {
                showToast('복사에 실패했습니다.', 'danger');
            }
            document.body.removeChild(textarea);
        }
    };
}

/**
 * 토스트 알림 표시
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    const toastElement = toastContainer.lastElementChild;
    const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

/**
 * 토스트 컨테이너 생성
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

/**
 * 확인 대화상자
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

/**
 * 로딩 스피너 표시/숨김
 */
function showLoading(element) {
    const spinner = document.createElement('div');
    spinner.className = 'spinner-border spinner-border-sm ms-2';
    spinner.role = 'status';
    element.appendChild(spinner);
    element.disabled = true;
}

function hideLoading(element) {
    const spinner = element.querySelector('.spinner-border');
    if (spinner) spinner.remove();
    element.disabled = false;
}

/**
 * AJAX 요청 헬퍼
 */
async function fetchJSON(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        showToast('요청 처리 중 오류가 발생했습니다.', 'danger');
        throw error;
    }
}

/**
 * CSRF 토큰 가져오기
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * 날짜 포맷팅
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * 숫자 포맷팅 (천 단위 구분)
 */
function formatNumber(number) {
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Export functions for use in other scripts
window.SimpleID = {
    showToast,
    confirmAction,
    showLoading,
    hideLoading,
    fetchJSON,
    formatDate,
    formatNumber,
    copyToClipboard
};
