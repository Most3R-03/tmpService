from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import pyodbc  # 替换sqlite3为pyodbc
import os
import json
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = 'jiaoshikongzhi_secret_key'  # 用于会话加密

# ODBC数据库连接信息
DSN_NAME = 'jiaoshi'  # 数据库DSN名称

# 登录所需的用户名和密码
USERS = {
    'admin': 'admin123',
    'teacher': 'teacher123'
}

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# 数据库连接函数
def get_db_connection():
    """
    获取数据库连接
    
    Returns:
        conn: 数据库连接对象
    
    MySQL接口说明:
    - 使用ODBC连接到MySQL数据库
    - DSN名称为'jiaoshi'
    - 需要在系统中配置ODBC数据源
    """
    conn = pyodbc.connect(f'DSN={DSN_NAME}')
    return conn

# 初始化数据库
def init_db():
    """
    初始化数据库表结构
    
    MySQL接口说明:
    - 创建classes表: 存储教室信息
    - 创建devices表: 存储设备信息
    - 创建operation_logs表: 存储操作日志
    - 创建data_records表: 存储设备数据记录
    - 所有表使用相同的字符集(utf8mb4)和排序规则(utf8mb4_unicode_ci)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建班级表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS classes (
        class_id INT AUTO_INCREMENT PRIMARY KEY,
        class_name VARCHAR(100) NOT NULL UNIQUE,
        class_room VARCHAR(100),
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    ''')
    
    # 创建设备表 - 确保device_id是VARCHAR(50)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS devices (
        device_id VARCHAR(50) PRIMARY KEY,
        device_name VARCHAR(100) NOT NULL,
        device_type VARCHAR(50) NOT NULL,
        current_status VARCHAR(20) DEFAULT 'OFF',
        class_id INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (class_id) REFERENCES classes (class_id) ON DELETE SET NULL
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    ''')
    
    # 创建操作日志表 - 确保device_id也是VARCHAR(50)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS operation_logs (
        log_id INT AUTO_INCREMENT PRIMARY KEY,
        device_id VARCHAR(50) NOT NULL,
        operation VARCHAR(50) NOT NULL,
        operation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (device_id) REFERENCES devices (device_id) ON DELETE CASCADE
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ENGINE=InnoDB
    ''')
    
    # 创建数据记录表 - 确保device_id也是VARCHAR(50)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS data_records (
        record_id INT AUTO_INCREMENT PRIMARY KEY,
        device_id VARCHAR(50) NOT NULL,
        data_type VARCHAR(50) NOT NULL,
        data_value VARCHAR(100) NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (device_id) REFERENCES devices (device_id) ON DELETE CASCADE
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ENGINE=InnoDB
    ''')
    
    conn.commit()
    conn.close()

# 在应用启动时初始化数据库
try:
    init_db()
except Exception as e:
    print(f"初始化数据库时出错: {str(e)}")
    print("请确保已正确配置'jiaoshi' ODBC数据源")
    print("尝试创建没有外键约束的表...")
    
    # 如果创建带外键约束的表失败，尝试创建没有外键约束的表
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 创建班级表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            class_id INT AUTO_INCREMENT PRIMARY KEY,
            class_name VARCHAR(100) NOT NULL UNIQUE,
            class_room VARCHAR(100),
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        ''')
        
        # 创建设备表 - 没有外键约束
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            device_id VARCHAR(50) PRIMARY KEY,
            device_name VARCHAR(100) NOT NULL,
            device_type VARCHAR(50) NOT NULL,
            current_status VARCHAR(20) DEFAULT 'OFF',
            class_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        ''')
        
        # 创建操作日志表 - 没有外键约束
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS operation_logs (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            device_id VARCHAR(50) NOT NULL,
            operation VARCHAR(50) NOT NULL,
            operation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        ''')
        
        # 创建数据记录表 - 没有外键约束
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_records (
            record_id INT AUTO_INCREMENT PRIMARY KEY,
            device_id VARCHAR(50) NOT NULL,
            data_type VARCHAR(50) NOT NULL,
            data_value VARCHAR(100) NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        ''')
        
        conn.commit()
        conn.close()
        print("成功创建没有外键约束的表")
    except Exception as e2:
        print(f"创建没有外键约束的表也失败: {str(e2)}")

# 路由：首页
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# 路由：日志页面
@app.route('/logs')
@login_required
def logs():
    return render_template('logs.html')

# 路由：获取所有班级
@app.route('/api/classes', methods=['GET'])
@login_required
def get_classes():
    """
    获取所有班级信息
    
    MySQL接口说明:
    - 查询classes表获取所有班级
    - 对每个班级查询关联的设备数量
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM classes')
    classes = cursor.fetchall()
    
    result = []
    for cls in classes:
        # 获取班级中的设备数量
        cursor.execute('SELECT COUNT(*) FROM devices WHERE class_id = ?', (cls[0],))
        device_count = cursor.fetchone()[0]
        
        result.append({
            'class_id': cls[0],
            'class_name': cls[1],
            'class_room': cls[2],
            'description': cls[3],
            'device_count': device_count
        })
    
    conn.close()
    return jsonify(result)

# 路由：获取班级信息
@app.route('/api/classes/<int:class_id>', methods=['GET'])
@login_required
def get_class(class_id):
    """
    获取特定班级信息
    
    MySQL接口说明:
    - 根据class_id查询classes表
    - 获取该班级关联的设备数量
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM classes WHERE class_id = ?', (class_id,))
    cls = cursor.fetchone()
    
    if cls is None:
        conn.close()
        return jsonify({'error': '班级不存在'}), 404
    
    # 获取班级中的设备数量
    cursor.execute('SELECT COUNT(*) FROM devices WHERE class_id = ?', (class_id,))
    device_count = cursor.fetchone()[0]
    conn.close()
    
    result = {
        'class_id': cls[0],
        'class_name': cls[1],
        'class_room': cls[2],
        'description': cls[3],
        'device_count': device_count
    }
    
    return jsonify(result)

# 路由：添加班级
@app.route('/api/classes', methods=['POST'])
@login_required
def add_class():
    """
    添加新班级
    
    MySQL接口说明:
    - 向classes表插入新记录
    - 返回新插入记录的class_id
    - 自动设置created_at和update_time字段
    """
    data = request.json
    
    if not data or 'class_name' not in data:
        return jsonify({'error': '班级名称不能为空'}), 400
    
    class_name = data['class_name']
    class_room = data.get('class_room', '')
    description = data.get('description', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 获取当前时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 插入新班级记录，显式指定update_time字段
        cursor.execute('INSERT INTO classes (class_name, class_room, description, update_time) VALUES (?, ?, ?, ?)',
                    (class_name, class_room, description, current_time))
        conn.commit()
        
        # 获取新添加的班级ID
        cursor.execute('SELECT LAST_INSERT_ID()')
        class_id = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({'class_id': class_id, 'message': '班级添加成功'}), 201
    except Exception as e:
        conn.close()
        # 检查是否是唯一约束错误
        if 'Duplicate entry' in str(e):
            return jsonify({'error': '班级名称已存在'}), 400
        return jsonify({'error': str(e)}), 500

# 路由：更新班级
@app.route('/api/classes/<int:class_id>', methods=['PUT'])
@login_required
def update_class(class_id):
    """
    更新班级信息
    
    MySQL接口说明:
    - 根据class_id更新classes表中的记录
    - 支持部分字段更新
    - update_time字段会自动更新为当前时间
    """
    data = request.json
    
    if not data:
        return jsonify({'error': '数据不能为空'}), 400
    
    class_name = data.get('class_name')
    class_room = data.get('class_room')
    description = data.get('description')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 检查班级是否存在
        cursor.execute('SELECT * FROM classes WHERE class_id = ?', (class_id,))
        cls = cursor.fetchone()
        if cls is None:
            conn.close()
            return jsonify({'error': '班级不存在'}), 404
        
        # 更新班级信息，不需要手动更新update_time字段，它会自动更新
        if class_name:
            cursor.execute('UPDATE classes SET class_name = ? WHERE class_id = ?',
                        (class_name, class_id))
        if class_room is not None:
            cursor.execute('UPDATE classes SET class_room = ? WHERE class_id = ?',
                        (class_room, class_id))
        if description is not None:
            cursor.execute('UPDATE classes SET description = ? WHERE class_id = ?',
                        (description, class_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': '班级更新成功'})
    except Exception as e:
        conn.close()
        # 检查是否是唯一约束错误
        if 'Duplicate entry' in str(e):
            return jsonify({'error': '班级名称已存在'}), 400
        return jsonify({'error': str(e)}), 500

# 路由：删除班级
@app.route('/api/classes/<int:class_id>', methods=['DELETE'])
@login_required
def delete_class(class_id):
    """
    删除班级
    
    MySQL接口说明:
    - 先将该班级关联的设备的class_id设为NULL
    - 然后删除classes表中的记录
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查班级是否存在
    cursor.execute('SELECT * FROM classes WHERE class_id = ?', (class_id,))
    cls = cursor.fetchone()
    if cls is None:
        conn.close()
        return jsonify({'error': '班级不存在'}), 404
    
    try:
        # 将该班级的设备的class_id设为NULL
        cursor.execute('UPDATE devices SET class_id = NULL WHERE class_id = ?', (class_id,))
        
        # 删除班级
        cursor.execute('DELETE FROM classes WHERE class_id = ?', (class_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': '班级删除成功'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# 路由：获取班级的设备
@app.route('/api/classes/<int:class_id>/devices', methods=['GET'])
@login_required
def get_class_devices(class_id):
    """
    获取班级关联的设备
    
    MySQL接口说明:
    - 根据class_id查询devices表
    - 关联classes表获取班级名称
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查班级是否存在
    if class_id > 0:
        cursor.execute('SELECT * FROM classes WHERE class_id = ?', (class_id,))
        cls = cursor.fetchone()
        if cls is None:
            conn.close()
            return jsonify({'error': '班级不存在'}), 404
        
        cursor.execute('''
            SELECT d.*, c.class_name 
            FROM devices d 
            LEFT JOIN classes c ON d.class_id = c.class_id 
            WHERE d.class_id = ?
        ''', (class_id,))
        devices = cursor.fetchall()
    else:
        # 如果class_id为0或undefined，返回所有未分配班级的设备
        cursor.execute('''
            SELECT d.*, c.class_name 
            FROM devices d 
            LEFT JOIN classes c ON d.class_id = c.class_id
            WHERE d.class_id IS NULL
        ''')
        devices = cursor.fetchall()
    
    conn.close()
    
    result = []
    for device in devices:
        result.append({
            'device_id': device[0],
            'device_name': device[1],
            'device_type': device[2],
            'current_status': device[3],
            'class_id': device[4],
            'class_name': device[6] if len(device) > 6 and device[6] else ''
        })
    
    return jsonify(result)

# 路由：获取未分配班级的设备
@app.route('/api/classes/undefined/devices', methods=['GET'])
@login_required
def get_unassigned_devices():
    """
    获取未分配班级的设备
    
    MySQL接口说明:
    - 查询devices表中class_id为NULL的设备
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT d.*, c.class_name 
        FROM devices d 
        LEFT JOIN classes c ON d.class_id = c.class_id
        WHERE d.class_id IS NULL
    ''')
    devices = cursor.fetchall()
    
    conn.close()
    
    result = []
    for device in devices:
        result.append({
            'device_id': device[0],
            'device_name': device[1],
            'device_type': device[2],
            'current_status': device[3],
            'class_id': device[4],
            'class_name': device[6] if len(device) > 6 and device[6] else ''
        })
    
    return jsonify(result)

# 路由：获取所有设备
@app.route('/api/devices', methods=['GET'])
@login_required
def get_devices():
    """
    获取所有设备
    
    MySQL接口说明:
    - 查询devices表获取所有设备
    - 关联classes表获取班级名称
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.*, c.class_name 
        FROM devices d 
        LEFT JOIN classes c ON d.class_id = c.class_id
    ''')
    devices = cursor.fetchall()
    conn.close()
    
    result = []
    for device in devices:
        result.append({
            'device_id': device[0],
            'device_name': device[1],
            'device_type': device[2],
            'current_status': device[3],
            'class_id': device[4],
            'class_name': device[6] if len(device) > 6 and device[6] else ''
        })
    
    return jsonify(result)

# 路由：获取设备信息
@app.route('/api/devices/<device_id>', methods=['GET'])
@login_required
def get_device(device_id):
    """
    获取特定设备信息
    
    MySQL接口说明:
    - 根据device_id查询devices表
    - 关联classes表获取班级名称
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.*, c.class_name 
        FROM devices d 
        LEFT JOIN classes c ON d.class_id = c.class_id 
        WHERE d.device_id = ?
    ''', (device_id,))
    device = cursor.fetchone()
    
    if device is None:
        conn.close()
        return jsonify({'error': '设备不存在'}), 404
    
    conn.close()
    
    result = {
        'device_id': device[0],
        'device_name': device[1],
        'device_type': device[2],
        'current_status': device[3],
        'class_id': device[4],
        'class_name': device[6] if len(device) > 6 and device[6] else ''
    }
    
    return jsonify(result)

# 路由：添加设备
@app.route('/api/devices', methods=['POST'])
@login_required
def add_device():
    """
    添加新设备
    
    MySQL接口说明:
    - 向devices表插入新记录
    - 支持设置设备所属班级
    - 显式设置created_at和update_time字段
    """
    data = request.json
    
    if not data or 'device_id' not in data or 'device_name' not in data or 'device_type' not in data:
        return jsonify({'error': '设备ID、名称和类型不能为空'}), 400
    
    device_id = data['device_id']
    device_name = data['device_name']
    device_type = data['device_type']
    current_status = data.get('current_status', 'OFF')
    class_id = data.get('class_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 检查设备ID是否已存在
        cursor.execute('SELECT * FROM devices WHERE device_id = ?', (device_id,))
        device = cursor.fetchone()
        if device:
            conn.close()
            return jsonify({'error': '设备ID已存在'}), 400
        
        # 如果指定了班级ID，检查班级是否存在
        if class_id:
            cursor.execute('SELECT * FROM classes WHERE class_id = ?', (class_id,))
            cls = cursor.fetchone()
            if cls is None:
                conn.close()
                return jsonify({'error': '指定的班级不存在'}), 400
        
        # 获取当前时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 插入新设备记录，显式指定update_time字段
        cursor.execute('''
            INSERT INTO devices (device_id, device_name, device_type, current_status, class_id, update_time) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (device_id, device_name, device_type, current_status, class_id, current_time))
        conn.commit()
        conn.close()
        
        return jsonify({'message': '设备添加成功'}), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# 路由：更新设备
@app.route('/api/devices/<device_id>', methods=['PUT'])
@login_required
def update_device(device_id):
    """
    更新设备信息
    
    MySQL接口说明:
    - 根据device_id更新devices表中的记录
    - 支持部分字段更新
    - update_time字段会自动更新为当前时间
    """
    data = request.json
    
    if not data:
        return jsonify({'error': '数据不能为空'}), 400
    
    device_name = data.get('device_name')
    device_type = data.get('device_type')
    current_status = data.get('current_status')
    class_id = data.get('class_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 检查设备是否存在
        cursor.execute('SELECT * FROM devices WHERE device_id = ?', (device_id,))
        device = cursor.fetchone()
        if device is None:
            conn.close()
            return jsonify({'error': '设备不存在'}), 404
        
        # 如果指定了班级ID，检查班级是否存在
        if class_id is not None:
            # 将class_id转换为整数或None
            try:
                if class_id == '' or class_id == 'undefined' or class_id == 'null' or class_id == 0:
                    class_id = None
                else:
                    class_id = int(class_id)
                    # 如果class_id > 0，检查班级是否存在
                    if class_id > 0:
                        cursor.execute('SELECT * FROM classes WHERE class_id = ?', (class_id,))
                        cls = cursor.fetchone()
                        if cls is None:
                            conn.close()
                            return jsonify({'error': '指定的班级不存在'}), 400
            except (ValueError, TypeError):
                conn.close()
                return jsonify({'error': '班级ID格式不正确'}), 400
        
        # 更新设备信息，不需要手动更新update_time字段，它会自动更新
        if device_name:
            cursor.execute('UPDATE devices SET device_name = ? WHERE device_id = ?',
                        (device_name, device_id))
        if device_type:
            cursor.execute('UPDATE devices SET device_type = ? WHERE device_id = ?',
                        (device_type, device_id))
        if current_status:
            cursor.execute('UPDATE devices SET current_status = ? WHERE device_id = ?',
                        (current_status, device_id))
        if class_id is not None:
            cursor.execute('UPDATE devices SET class_id = ? WHERE device_id = ?',
                        (class_id, device_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': '设备更新成功'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# 路由：删除设备
@app.route('/api/devices/<device_id>', methods=['DELETE'])
@login_required
def delete_device(device_id):
    """
    删除设备
    
    MySQL接口说明:
    - 先删除设备关联的操作日志和数据记录
    - 然后删除devices表中的记录
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查设备是否存在
    cursor.execute('SELECT * FROM devices WHERE device_id = ?', (device_id,))
    device = cursor.fetchone()
    if device is None:
        conn.close()
        return jsonify({'error': '设备不存在'}), 404
    
    try:
        # 删除设备相关的操作日志
        cursor.execute('DELETE FROM operation_logs WHERE device_id = ?', (device_id,))
        
        # 删除设备相关的数据记录
        cursor.execute('DELETE FROM data_records WHERE device_id = ?', (device_id,))
        
        # 删除设备
        cursor.execute('DELETE FROM devices WHERE device_id = ?', (device_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': '设备删除成功'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# 路由：连接设备
@app.route('/api/devices/<device_id>/connect', methods=['POST'])
@login_required
def connect_device(device_id):
    """
    连接设备
    
    MySQL接口说明:
    - 记录操作日志到operation_logs表
    - 更新devices表中设备状态
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查设备是否存在
    cursor.execute('SELECT * FROM devices WHERE device_id = ?', (device_id,))
    device = cursor.fetchone()
    if device is None:
        conn.close()
        return jsonify({'error': '设备不存在'}), 404
    
    try:
        # 记录操作日志 - 使用正确的列名
        cursor.execute('INSERT INTO operation_logs (device_id, operation) VALUES (?, ?)',
                    (device_id, '连接设备'))
        
        # 更新设备状态
        cursor.execute('UPDATE devices SET current_status = ? WHERE device_id = ?',
                    ('ON', device_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': '设备连接成功'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# 路由：断开设备
@app.route('/api/devices/<device_id>/disconnect', methods=['POST'])
@login_required
def disconnect_device(device_id):
    """
    断开设备连接
    
    MySQL接口说明:
    - 记录操作日志到operation_logs表
    - 更新devices表中设备状态
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查设备是否存在
    cursor.execute('SELECT * FROM devices WHERE device_id = ?', (device_id,))
    device = cursor.fetchone()
    if device is None:
        conn.close()
        return jsonify({'error': '设备不存在'}), 404
    
    try:
        # 记录操作日志 - 使用正确的列名
        cursor.execute('INSERT INTO operation_logs (device_id, operation) VALUES (?, ?)',
                    (device_id, '断开设备'))
        
        # 更新设备状态
        cursor.execute('UPDATE devices SET current_status = ? WHERE device_id = ?',
                    ('OFF', device_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': '设备断开成功'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# 路由：开启设备
@app.route('/api/devices/<device_id>/turn-on', methods=['POST'])
@login_required
def turn_on_device(device_id):
    """
    开启设备
    
    MySQL接口说明:
    - 记录操作日志到operation_logs表
    - 更新devices表中设备状态
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查设备是否存在
    cursor.execute('SELECT * FROM devices WHERE device_id = ?', (device_id,))
    device = cursor.fetchone()
    if device is None:
        conn.close()
        return jsonify({'error': '设备不存在'}), 404
    
    try:
        # 获取当前时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 记录操作日志 - 使用正确的列名
        cursor.execute('INSERT INTO operation_logs (device_id, operation) VALUES (?, ?)',
                    (device_id, '开启设备'))
        
        # 更新设备状态
        cursor.execute('UPDATE devices SET current_status = ? WHERE device_id = ?',
                    ('ON', device_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': '设备开启成功'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# 路由：关闭设备
@app.route('/api/devices/<device_id>/turn-off', methods=['POST'])
@login_required
def turn_off_device(device_id):
    """
    关闭设备
    
    MySQL接口说明:
    - 记录操作日志到operation_logs表
    - 更新devices表中设备状态
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查设备是否存在
    cursor.execute('SELECT * FROM devices WHERE device_id = ?', (device_id,))
    device = cursor.fetchone()
    if device is None:
        conn.close()
        return jsonify({'error': '设备不存在'}), 404
    
    try:
        # 记录操作日志 - 使用正确的列名
        cursor.execute('INSERT INTO operation_logs (device_id, operation) VALUES (?, ?)',
                    (device_id, '关闭设备'))
        
        # 更新设备状态
        cursor.execute('UPDATE devices SET current_status = ? WHERE device_id = ?',
                    ('OFF', device_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': '设备关闭成功'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# 路由：获取设备数据
@app.route('/api/devices/<device_id>/data', methods=['GET'])
@login_required
def get_device_data(device_id):
    """
    获取设备数据
    
    MySQL接口说明:
    - 查询devices表获取设备信息
    - 模拟生成设备数据
    - 记录数据到data_records表
    - 查询历史数据记录
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查设备是否存在
    cursor.execute('SELECT * FROM devices WHERE device_id = ?', (device_id,))
    device = cursor.fetchone()
    if device is None:
        conn.close()
        return jsonify({'error': '设备不存在'}), 404
    
    # 获取设备类型
    device_type = device[2]  # device_type在第3列
    
    # 模拟设备数据
    data = {}
    
    if '灯' in device_type or '照明' in device_type:
        data = {
            '状态': 'ON',
            '亮度': f"{datetime.now().second % 100}%",
            '功率': f"{10 + datetime.now().second % 40}W"
        }
    elif '空调' in device_type or '温控' in device_type:
        data = {
            '状态': 'ON',
            '温度': f"{16 + datetime.now().second % 14}°C",
            '模式': '制冷',
            '风速': '中速'
        }
    elif '投影' in device_type or '显示' in device_type:
        data = {
            '状态': 'ON',
            '信号源': 'HDMI',
            '亮度': f"{datetime.now().second % 100}%",
            '对比度': f"{datetime.now().second % 100}%"
        }
    else:
        data = {
            '状态': 'ON',
            '运行时间': f"{1 + datetime.now().hour % 24}小时"
        }
    
    # 记录数据
    try:
        # 获取当前时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for key, value in data.items():
            cursor.execute('''
                INSERT INTO data_records (device_id, data_type, data_value, update_time) 
                VALUES (?, ?, ?, ?)
            ''', (device_id, key, value, current_time))
        
        conn.commit()
    except Exception as e:
        print(f"记录数据时出错: {str(e)}")
    
    # 获取历史数据记录
    cursor.execute('''
        SELECT * FROM data_records 
        WHERE device_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 10
    ''', (device_id,))
    records = cursor.fetchall()
    
    conn.close()
    
    history = []
    for record in records:
        history.append({
            'data_type': record[2],  # data_type在第3列
            'data_value': record[3],  # data_value在第4列
            'timestamp': record[4]    # timestamp在第5列
        })
    
    return jsonify({
        'current_data': data,
        'history': history
    })

# 路由：分配设备到班级
@app.route('/api/classes/<int:class_id>/assign-devices', methods=['POST'])
@login_required
def assign_devices_to_class(class_id):
    """
    分配设备到班级
    
    MySQL接口说明:
    - 将指定班级的所有设备的class_id设为NULL
    - 然后为选中的设备设置新的class_id
    """
    data = request.json
    
    if not data or 'device_ids' not in data:
        return jsonify({'error': '设备ID列表不能为空'}), 400
    
    device_ids = data['device_ids']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 处理class_id
    try:
        # 如果class_id为0或负数，表示未分配班级
        if class_id <= 0:
            class_id = None
        else:
            # 检查班级是否存在
            cursor.execute('SELECT * FROM classes WHERE class_id = ?', (class_id,))
            cls = cursor.fetchone()
            if cls is None:
                conn.close()
                return jsonify({'error': '班级不存在'}), 404
    except (ValueError, TypeError):
        conn.close()
        return jsonify({'error': '班级ID格式不正确'}), 400
    
    try:
        # 开始事务 - 使用连接对象的方法
        conn.autocommit = False
        
        # 如果class_id不为None，先将该班级的所有设备的class_id设为NULL
        if class_id is not None:
            cursor.execute('UPDATE devices SET class_id = NULL WHERE class_id = ?', (class_id,))
        
        # 然后为选中的设备设置班级ID
        for device_id in device_ids:
            # 检查设备是否存在
            cursor.execute('SELECT * FROM devices WHERE device_id = ?', (device_id,))
            device = cursor.fetchone()
            if device:
                cursor.execute('UPDATE devices SET class_id = ? WHERE device_id = ?',
                            (class_id, device_id))
        
        # 提交事务
        conn.commit()
        conn.close()
        
        return jsonify({'message': '设备分配成功'})
    except Exception as e:
        # 回滚事务
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 500

# API：获取操作日志
@app.route('/api/logs', methods=['GET'])
@login_required
def get_logs():
    """
    获取操作日志
    
    MySQL接口说明:
    - 查询operation_logs表获取日志记录
    - 支持分页和筛选
    - 关联devices表获取设备名称
    - 使用BINARY关键字确保字符集排序规则一致
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    device_id = request.args.get('device_id', '')
    operation = request.args.get('operation', '')
    date = request.args.get('date', '')
    
    # 构建查询条件
    query = 'SELECT l.log_id, l.device_id, d.device_name, l.operation, l.operation_time FROM operation_logs l LEFT JOIN devices d ON BINARY l.device_id = BINARY d.device_id WHERE 1=1'
    params = []
    
    if device_id:
        query += ' AND BINARY l.device_id = ?'
        params.append(device_id)
    
    if operation:
        query += ' AND l.operation = ?'
        params.append(operation)
    
    if date:
        query += ' AND DATE(l.operation_time) = ?'
        params.append(date)
    
    # 计算总记录数
    count_query = query.replace('SELECT l.log_id, l.device_id, d.device_name, l.operation, l.operation_time', 'SELECT COUNT(*)')
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]
    
    # 添加排序和分页
    query += ' ORDER BY l.operation_time DESC LIMIT ? OFFSET ?'
    params.append(page_size)
    params.append((page - 1) * page_size)
    
    # 执行查询
    cursor.execute(query, params)
    logs = cursor.fetchall()
    
    # 计算总页数
    total_pages = (total_count + page_size - 1) // page_size
    
    # 构建结果
    result = {
        'logs': [],
        'total_count': total_count,
        'total_pages': total_pages,
        'current_page': page
    }
    
    for log in logs:
        result['logs'].append({
            'log_id': log[0],
            'device_id': log[1],
            'device_name': log[2],
            'operation': log[3],
            'operation_time': log[4]
        })
    
    conn.close()
    return jsonify(result)

# API：清空操作日志
@app.route('/api/logs', methods=['DELETE'])
@login_required
def clear_logs():
    """
    清空操作日志
    
    MySQL接口说明:
    - 删除operation_logs表中的所有记录
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM operation_logs')
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'All logs have been cleared'})

# API：获取日志详情
@app.route('/api/logs/<int:log_id>', methods=['GET'])
@login_required
def get_log_detail(log_id):
    """
    获取日志详情
    
    MySQL接口说明:
    - 根据log_id查询operation_logs表
    - 关联devices表获取设备名称
    - 使用BINARY关键字确保字符集排序规则一致
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT l.*, d.device_name FROM operation_logs l LEFT JOIN devices d ON BINARY l.device_id = BINARY d.device_id WHERE l.log_id = ?', 
                  (log_id,))
    log = cursor.fetchone()
    conn.close()
    
    if not log:
        return jsonify({'error': 'Log not found'}), 404
    
    return jsonify({
        'log_id': log[0],
        'device_id': log[1],
        'device_name': log[5],  # device_name在第6列
        'operation': log[2],
        'operation_time': log[3]
    })

# 路由：登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in USERS and USERS[username] == password:
            session['username'] = username
            
            # 实现"记住我"功能
            if 'remember' in request.form:
                # 设置会话的持久时间为30天
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)
            
            return redirect(url_for('index'))
        else:
            error = '用户名或密码错误'
    
    return render_template('login.html', error=error)

# 路由：登出
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True) 