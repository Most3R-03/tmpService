// 全局变量
let logs = [];
let currentPage = 1;
let pageSize = 10;
let totalPages = 1;
let filters = {
    device_id: '',
    operation: '',
    date: ''
};

// DOM 加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    initPage();
    
    // 添加事件监听器
    document.getElementById('searchBtn').addEventListener('click', applyFilters);
    document.getElementById('resetBtn').addEventListener('click', resetFilters);
    document.getElementById('clearLogsBtn').addEventListener('click', clearLogs);
    
    // 导航菜单事件
    document.getElementById('classManagement').addEventListener('click', function(e) {
        e.preventDefault();
        window.location.href = '/';
    });
    
    document.getElementById('deviceManagement').addEventListener('click', function(e) {
        e.preventDefault();
        window.location.href = '/';
    });
});

// 初始化页面
function initPage() {
    // 加载设备列表用于筛选
    loadDevices();
    
    // 加载日志数据
    loadLogs();
}

// 加载设备列表
function loadDevices() {
    axios.get('/api/devices')
        .then(function(response) {
            const devices = response.data;
            const deviceFilter = document.getElementById('deviceFilter');
            
            // 清空现有选项（保留"所有设备"选项）
            deviceFilter.innerHTML = '<option value="">所有设备</option>';
            
            devices.forEach(function(device) {
                const option = document.createElement('option');
                option.value = device.device_id;
                option.textContent = device.device_name;
                deviceFilter.appendChild(option);
            });
        })
        .catch(function(error) {
            console.error('加载设备列表失败:', error);
            showAlert('加载设备列表失败', 'danger');
        });
}

// 加载日志数据
function loadLogs() {
    // 构建查询参数
    let params = {
        page: currentPage,
        page_size: pageSize
    };
    
    // 添加筛选条件
    if (filters.device_id) {
        params.device_id = filters.device_id;
    }
    if (filters.operation) {
        params.operation = filters.operation;
    }
    if (filters.date) {
        params.date = filters.date;
    }
    
    axios.get('/api/logs', { params: params })
        .then(function(response) {
            logs = response.data.logs;
            totalPages = response.data.total_pages;
            
            // 更新总记录数
            document.getElementById('totalLogs').textContent = response.data.total_count;
            
            // 渲染日志表格
            renderLogsTable();
            
            // 渲染分页
            renderPagination();
        })
        .catch(function(error) {
            console.error('加载日志数据失败:', error);
            showAlert('加载日志数据失败: ' + (error.response?.data?.error || error.message), 'danger');
        });
}

// 渲染日志表格
function renderLogsTable() {
    const tableBody = document.getElementById('logsTableBody');
    tableBody.innerHTML = '';
    
    if (logs.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="5" class="text-center">暂无日志记录</td>';
        tableBody.appendChild(row);
        return;
    }
    
    logs.forEach(function(log) {
        const row = document.createElement('tr');
        
        // 格式化时间
        const date = new Date(log.operation_time);
        const formattedDate = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`;
        
        // 操作类型中文显示
        let operationText = log.operation;
        
        row.innerHTML = `
            <td>${log.log_id}</td>
            <td>${log.device_name || log.device_id}</td>
            <td>${operationText}</td>
            <td>${formattedDate}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary view-log-btn" data-id="${log.log_id}">
                    <i class="bi bi-eye"></i> 查看
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // 添加查看详情按钮的事件监听器
    document.querySelectorAll('.view-log-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const logId = this.dataset.id;
            showLogDetail(logId);
        });
    });
}

// 渲染分页
function renderPagination() {
    const pagination = document.getElementById('logsPagination');
    pagination.innerHTML = '';
    
    // 上一页按钮
    const prevItem = document.createElement('li');
    prevItem.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    prevItem.innerHTML = `<a class="page-link" href="#" aria-label="Previous"><span aria-hidden="true">&laquo;</span></a>`;
    prevItem.addEventListener('click', function(e) {
        e.preventDefault();
        if (currentPage > 1) {
            currentPage--;
            loadLogs();
        }
    });
    pagination.appendChild(prevItem);
    
    // 页码按钮
    for (let i = 1; i <= totalPages; i++) {
        const pageItem = document.createElement('li');
        pageItem.className = `page-item ${i === currentPage ? 'active' : ''}`;
        pageItem.innerHTML = `<a class="page-link" href="#">${i}</a>`;
        pageItem.addEventListener('click', function(e) {
            e.preventDefault();
            currentPage = i;
            loadLogs();
        });
        pagination.appendChild(pageItem);
    }
    
    // 下一页按钮
    const nextItem = document.createElement('li');
    nextItem.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    nextItem.innerHTML = `<a class="page-link" href="#" aria-label="Next"><span aria-hidden="true">&raquo;</span></a>`;
    nextItem.addEventListener('click', function(e) {
        e.preventDefault();
        if (currentPage < totalPages) {
            currentPage++;
            loadLogs();
        }
    });
    pagination.appendChild(nextItem);
}

// 应用筛选条件
function applyFilters() {
    filters.device_id = document.getElementById('deviceFilter').value;
    filters.operation = document.getElementById('operationFilter').value;
    filters.date = document.getElementById('dateFilter').value;
    
    // 重置到第一页
    currentPage = 1;
    
    // 重新加载数据
    loadLogs();
}

// 重置筛选条件
function resetFilters() {
    document.getElementById('deviceFilter').value = '';
    document.getElementById('operationFilter').value = '';
    document.getElementById('dateFilter').value = '';
    
    filters = {
        device_id: '',
        operation: '',
        date: ''
    };
    
    // 重置到第一页
    currentPage = 1;
    
    // 重新加载数据
    loadLogs();
}

// 清空日志
function clearLogs() {
    if (!confirm('确定要清空所有日志记录吗？此操作不可恢复！')) {
        return;
    }
    
    axios.delete('/api/logs')
        .then(function(response) {
            // 重新加载数据
            loadLogs();
            showAlert('日志已清空', 'success');
        })
        .catch(function(error) {
            console.error('清空日志失败:', error);
            showAlert('清空日志失败: ' + (error.response?.data?.error || error.message), 'danger');
        });
}

// 显示日志详情
function showLogDetail(logId) {
    axios.get(`/api/logs/${logId}`)
        .then(function(response) {
            const log = response.data;
            
            // 格式化时间
            const date = new Date(log.operation_time);
            const formattedDate = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`;
            
            // 填充模态框内容
            document.getElementById('modalDeviceName').textContent = log.device_name || log.device_id;
            document.getElementById('modalOperation').textContent = log.operation;
            document.getElementById('modalTime').textContent = formattedDate;
            
            // 构建详细信息
            const details = {
                '日志ID': log.log_id,
                '设备ID': log.device_id,
                '设备名称': log.device_name || '未知',
                '操作类型': log.operation,
                '操作时间': formattedDate
            };
            
            document.getElementById('modalDetails').textContent = JSON.stringify(details, null, 2);
            
            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('logDetailModal'));
            modal.show();
        })
        .catch(function(error) {
            console.error('获取日志详情失败:', error);
            showAlert('获取日志详情失败: ' + (error.response?.data?.error || error.message), 'danger');
        });
}

// 显示提示信息
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertDiv.style.zIndex = 1050;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // 3秒后自动关闭
    setTimeout(function() {
        alertDiv.classList.remove('show');
        setTimeout(function() {
            alertDiv.remove();
        }, 150);
    }, 3000);
} 