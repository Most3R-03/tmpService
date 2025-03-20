// 全局变量
let currentClassId = null;
let classes = [];
let devices = [];

// DOM 加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    initPage();
    
    // 添加事件监听器
    document.getElementById('addClassBtn').addEventListener('click', showAddClassModal);
    document.getElementById('saveClassBtn').addEventListener('click', saveClass);
    document.getElementById('saveDeviceBtn').addEventListener('click', saveDevice);
    
    // 导航菜单事件
    document.getElementById('classManagement').addEventListener('click', function(e) {
        e.preventDefault();
        // 实现教室管理功能
        showAddClassModal();
    });
    
    document.getElementById('deviceManagement').addEventListener('click', function(e) {
        e.preventDefault();
        // 实现设备管理功能
        showAddDeviceModal();
    });
});

// 初始化页面
function initPage() {
    // 加载教室列表
    loadClasses();
}

// 加载教室列表
function loadClasses() {
    axios.get('/api/classes')
        .then(function(response) {
            classes = response.data;
            renderClassList();
            
            // 如果有教室，默认选中第一个
            if (classes.length > 0) {
                selectClass(classes[0].class_id);
            } else {
                // 如果没有教室，加载所有设备
                loadDevices('undefined');
            }
        })
        .catch(function(error) {
            console.error('加载教室列表失败:', error);
            showAlert('加载教室列表失败', 'danger');
        });
}

// 渲染教室列表
function renderClassList() {
    const classList = document.getElementById('classList');
    classList.innerHTML = '';
    
    // 添加"所有设备"选项
    const allDevicesItem = document.createElement('a');
    allDevicesItem.href = '#';
    allDevicesItem.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
    allDevicesItem.dataset.id = 'undefined';
    allDevicesItem.innerHTML = `
        <div>
            <i class="bi bi-grid-3x3-gap me-2"></i>所有设备
        </div>
        <span class="badge bg-secondary rounded-pill">全部</span>
    `;
    
    allDevicesItem.addEventListener('click', function(e) {
        if (!e.target.closest('button')) {
            selectClass('undefined');
        }
    });
    
    classList.appendChild(allDevicesItem);
    
    // 添加"未分配设备"选项
    const unassignedItem = document.createElement('a');
    unassignedItem.href = '#';
    unassignedItem.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
    unassignedItem.dataset.id = '0';
    unassignedItem.innerHTML = `
        <div>
            <i class="bi bi-question-circle me-2"></i>未分配设备
        </div>
        <span class="badge bg-warning rounded-pill">未分配</span>
    `;
    
    unassignedItem.addEventListener('click', function(e) {
        if (!e.target.closest('button')) {
            selectClass('0');
        }
    });
    
    classList.appendChild(unassignedItem);
    
    // 添加教室列表
    classes.forEach(function(classroom) {
        const item = document.createElement('a');
        item.href = '#';
        item.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
        item.dataset.id = classroom.class_id;
        item.innerHTML = `
            <div>
                <i class="bi bi-building me-2"></i>${classroom.class_name}
            </div>
            <div>
                <span class="badge bg-primary rounded-pill">${classroom.device_count}台</span>
                <button class="btn btn-sm btn-outline-primary ms-2 edit-class-btn" data-id="${classroom.class_id}">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger ms-1 delete-class-btn" data-id="${classroom.class_id}">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `;
        
        item.addEventListener('click', function(e) {
            if (!e.target.closest('button')) {
                selectClass(classroom.class_id);
            }
        });
        
        classList.appendChild(item);
    });
    
    // 添加编辑和删除按钮的事件监听器
    document.querySelectorAll('.edit-class-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const classId = this.dataset.id;
            showEditClassModal(classId);
        });
    });
    
    document.querySelectorAll('.delete-class-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const classId = this.dataset.id;
            deleteClass(classId);
        });
    });
}

// 选择教室
function selectClass(classId) {
    currentClassId = classId;
    
    // 更新UI选中状态
    document.querySelectorAll('#classList .list-group-item').forEach(item => {
        if (item.dataset.id == classId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    
    // 设置标题
    if (classId === 'undefined') {
        document.getElementById('currentClassTitle').textContent = '所有设备';
    } else if (classId === '0') {
        document.getElementById('currentClassTitle').textContent = '未分配设备';
    } else {
        // 获取教室信息
        const classroom = classes.find(c => c.class_id == classId);
        if (classroom) {
            document.getElementById('currentClassTitle').textContent = `${classroom.class_name} - 设备控制面板`;
        }
    }
    
    // 加载该教室的设备
    loadDevices(classId);
}

// 加载设备
function loadDevices(classId) {
    let url = '';
    if (classId === 'undefined') {
        url = '/api/devices';
    } else {
        url = `/api/classes/${classId}/devices`;
    }
    
    axios.get(url)
        .then(function(response) {
            devices = response.data;
            renderDevicePanel();
        })
        .catch(function(error) {
            console.error('加载设备列表失败:', error);
            showAlert('加载设备列表失败', 'danger');
        });
}

// 渲染设备面板
function renderDevicePanel() {
    const devicePanel = document.getElementById('devicePanel');
    devicePanel.innerHTML = '';
    
    if (devices.length === 0) {
        devicePanel.innerHTML = '<div class="col-12 text-center py-5"><h4>暂无设备</h4><button class="btn btn-primary mt-3" id="addDeviceBtn">添加设备</button></div>';
        document.getElementById('addDeviceBtn').addEventListener('click', function() {
            showAddDeviceModal(currentClassId);
        });
        return;
    }
    
    devices.forEach(function(device) {
        const deviceCard = document.createElement('div');
        deviceCard.className = 'col-md-4 col-sm-6';
        
        // 设备图标
        let deviceIcon = '';
        switch(device.device_type) {
            case 'projector':
                deviceIcon = '<i class="bi bi-projector device-icon device-projector"></i>';
                break;
            case 'computer':
                deviceIcon = '<i class="bi bi-pc-display device-icon device-computer"></i>';
                break;
            case 'airConditioner':
                deviceIcon = '<i class="bi bi-thermometer-half device-icon device-airConditioner"></i>';
                break;
            case 'light':
                deviceIcon = '<i class="bi bi-lightbulb device-icon device-light"></i>';
                break;
            default:
                deviceIcon = '<i class="bi bi-gear device-icon device-other"></i>';
        }
        
        // 设备状态
        const isConnected = device.current_status === 'ON';
        
        deviceCard.innerHTML = `
            <div class="card device-card">
                <div class="card-body text-center">
                    <div class="device-status ${isConnected ? 'status-on' : 'status-off'}"></div>
                    ${deviceIcon}
                    <h5 class="card-title">${device.device_name}</h5>
                    <p class="card-text text-muted">${device.device_type}</p>
                    <p class="card-text text-muted">${device.class_name || '未分配'}</p>
                    <div class="d-grid gap-2">
                        <button class="btn ${isConnected ? 'btn-danger' : 'btn-success'} btn-control power-btn" 
                                data-id="${device.device_id}">
                            ${isConnected ? '关闭设备' : '开启设备'}
                        </button>
                        <div class="btn-group mt-2">
                            <button class="btn btn-outline-primary edit-device-btn" data-id="${device.device_id}">
                                <i class="bi bi-pencil"></i> 编辑
                            </button>
                            <button class="btn btn-outline-danger delete-device-btn" data-id="${device.device_id}">
                                <i class="bi bi-trash"></i> 删除
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        devicePanel.appendChild(deviceCard);
    });
    
    // 添加"添加设备"按钮
    const addDeviceDiv = document.createElement('div');
    addDeviceDiv.className = 'col-md-4 col-sm-6';
    addDeviceDiv.innerHTML = `
        <div class="card device-card h-100">
            <div class="card-body text-center d-flex flex-column justify-content-center align-items-center">
                <i class="bi bi-plus-circle device-icon"></i>
                <h5 class="card-title">添加新设备</h5>
                <button class="btn btn-primary btn-control" id="addDeviceBtn">添加设备</button>
            </div>
        </div>
    `;
    devicePanel.appendChild(addDeviceDiv);
    
    // 添加事件监听器
    document.getElementById('addDeviceBtn').addEventListener('click', function() {
        showAddDeviceModal(currentClassId);
    });
    
    // 开/关设备
    document.querySelectorAll('.power-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const deviceId = this.dataset.id;
            const device = devices.find(d => d.device_id == deviceId);
            
            if (device.current_status === 'ON') {
                turnOffDevice(deviceId);
            } else {
                turnOnDevice(deviceId);
            }
        });
    });
    
    // 编辑设备
    document.querySelectorAll('.edit-device-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const deviceId = this.dataset.id;
            showEditDeviceModal(deviceId);
        });
    });
    
    // 删除设备
    document.querySelectorAll('.delete-device-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const deviceId = this.dataset.id;
            deleteDevice(deviceId);
        });
    });
}

// 显示添加教室模态框
function showAddClassModal() {
    document.getElementById('classModalTitle').textContent = '添加教室';
    document.getElementById('classForm').reset();
    document.getElementById('classId').value = '';
    
    const classModal = new bootstrap.Modal(document.getElementById('classModal'));
    classModal.show();
}

// 显示编辑教室模态框
function showEditClassModal(classId) {
    document.getElementById('classModalTitle').textContent = '编辑教室';
    
    // 获取教室信息
    axios.get(`/api/classes/${classId}`)
        .then(function(response) {
            const classroom = response.data;
            
            document.getElementById('classId').value = classroom.class_id;
            document.getElementById('className').value = classroom.class_name;
            document.getElementById('classLocation').value = classroom.class_room || '';
            document.getElementById('classCapacity').value = classroom.description || '';
            
            const classModal = new bootstrap.Modal(document.getElementById('classModal'));
            classModal.show();
        })
        .catch(function(error) {
            console.error('获取教室信息失败:', error);
            showAlert('获取教室信息失败', 'danger');
        });
}

// 保存教室
function saveClass() {
    const classId = document.getElementById('classId').value;
    const className = document.getElementById('className').value;
    const classRoom = document.getElementById('classLocation').value;
    const description = document.getElementById('classCapacity').value;
    
    if (!className) {
        showAlert('教室名称不能为空', 'warning');
        return;
    }
    
    const classData = {
        class_name: className,
        class_room: classRoom,
        description: description
    };
    
    if (classId) {
        // 更新教室
        axios.put(`/api/classes/${classId}`, classData)
            .then(function(response) {
                bootstrap.Modal.getInstance(document.getElementById('classModal')).hide();
                showAlert('教室更新成功', 'success');
                loadClasses();
            })
            .catch(function(error) {
                console.error('更新教室失败:', error);
                showAlert('更新教室失败: ' + (error.response?.data?.error || error.message), 'danger');
            });
    } else {
        // 添加教室
        axios.post('/api/classes', classData)
            .then(function(response) {
                bootstrap.Modal.getInstance(document.getElementById('classModal')).hide();
                showAlert('教室添加成功', 'success');
                loadClasses();
            })
            .catch(function(error) {
                console.error('添加教室失败:', error);
                showAlert('添加教室失败: ' + (error.response?.data?.error || error.message), 'danger');
            });
    }
}

// 删除教室
function deleteClass(classId) {
    if (confirm('确定要删除这个教室吗？该教室的所有设备将被移除关联。')) {
        axios.delete(`/api/classes/${classId}`)
            .then(function(response) {
                showAlert('教室删除成功', 'success');
                loadClasses();
            })
            .catch(function(error) {
                console.error('删除教室失败:', error);
                showAlert('删除教室失败: ' + (error.response?.data?.error || error.message), 'danger');
            });
    }
}

// 显示添加设备模态框
function showAddDeviceModal(classId = null) {
    document.getElementById('deviceModalTitle').textContent = '添加设备';
    document.getElementById('deviceForm').reset();
    document.getElementById('deviceId').value = '';
    
    // 加载教室选项
    loadClassOptions(classId);
    
    const deviceModal = new bootstrap.Modal(document.getElementById('deviceModal'));
    deviceModal.show();
}

// 加载教室选项
function loadClassOptions(selectedClassId = null) {
    const classSelect = document.getElementById('classSelect');
    classSelect.innerHTML = '<option value="">未分配</option>';
    
    classes.forEach(function(classroom) {
        const option = document.createElement('option');
        option.value = classroom.class_id;
        option.textContent = classroom.class_name;
        
        if (selectedClassId && selectedClassId == classroom.class_id) {
            option.selected = true;
        }
        
        classSelect.appendChild(option);
    });
}

// 显示编辑设备模态框
function showEditDeviceModal(deviceId) {
    document.getElementById('deviceModalTitle').textContent = '编辑设备';
    
    // 获取设备信息
    axios.get(`/api/devices/${deviceId}`)
        .then(function(response) {
            const device = response.data;
            
            document.getElementById('deviceId').value = device.device_id;
            document.getElementById('deviceName').value = device.device_name;
            document.getElementById('deviceType').value = device.device_type;
            document.getElementById('deviceIP').value = device.device_id;
            
            // 加载教室选项
            loadClassOptions(device.class_id);
            
            const deviceModal = new bootstrap.Modal(document.getElementById('deviceModal'));
            deviceModal.show();
        })
        .catch(function(error) {
            console.error('获取设备信息失败:', error);
            showAlert('获取设备信息失败', 'danger');
        });
}

// 保存设备
function saveDevice() {
    const deviceId = document.getElementById('deviceId').value;
    const deviceName = document.getElementById('deviceName').value;
    const deviceType = document.getElementById('deviceType').value;
    const deviceIP = document.getElementById('deviceIP').value;
    const classId = document.getElementById('classSelect').value;
    
    if (!deviceName || !deviceType || !deviceIP) {
        showAlert('设备信息不完整', 'warning');
        return;
    }
    
    const deviceData = {
        device_name: deviceName,
        device_type: deviceType,
        class_id: classId || null
    };
    
    if (deviceId) {
        // 更新设备
        axios.put(`/api/devices/${deviceId}`, deviceData)
            .then(function(response) {
                bootstrap.Modal.getInstance(document.getElementById('deviceModal')).hide();
                showAlert('设备更新成功', 'success');
                loadDevices(currentClassId);
            })
            .catch(function(error) {
                console.error('更新设备失败:', error);
                showAlert('更新设备失败: ' + (error.response?.data?.error || error.message), 'danger');
            });
    } else {
        // 添加设备
        deviceData.device_id = deviceIP;
        
        axios.post('/api/devices', deviceData)
            .then(function(response) {
                bootstrap.Modal.getInstance(document.getElementById('deviceModal')).hide();
                showAlert('设备添加成功', 'success');
                loadDevices(currentClassId);
            })
            .catch(function(error) {
                console.error('添加设备失败:', error);
                showAlert('添加设备失败: ' + (error.response?.data?.error || error.message), 'danger');
            });
    }
}

// 删除设备
function deleteDevice(deviceId) {
    if (confirm('确定要删除这个设备吗？')) {
        axios.delete(`/api/devices/${deviceId}`)
            .then(function(response) {
                showAlert('设备删除成功', 'success');
                loadDevices(currentClassId);
            })
            .catch(function(error) {
                console.error('删除设备失败:', error);
                showAlert('删除设备失败: ' + (error.response?.data?.error || error.message), 'danger');
            });
    }
}

// 开启设备
function turnOnDevice(deviceId) {
    axios.post(`/api/devices/${deviceId}/turn-on`)
        .then(function(response) {
            showAlert('设备已开启', 'success');
            loadDevices(currentClassId);
        })
        .catch(function(error) {
            console.error('开启设备失败:', error);
            showAlert('开启设备失败: ' + (error.response?.data?.error || error.message), 'danger');
        });
}

// 关闭设备
function turnOffDevice(deviceId) {
    axios.post(`/api/devices/${deviceId}/turn-off`)
        .then(function(response) {
            showAlert('设备已关闭', 'success');
            loadDevices(currentClassId);
        })
        .catch(function(error) {
            console.error('关闭设备失败:', error);
            showAlert('关闭设备失败: ' + (error.response?.data?.error || error.message), 'danger');
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