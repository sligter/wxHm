import os
import time
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'some_secret_key'  # 用于 session 和 flash 消息

# 配置
UPLOAD_FOLDER = 'uploads'
QR_FILENAME = 'current_group.png'
ADMIN_PASSWORD = 'admin123'  # 设置你的管理密码
EXPIRE_DAYS = 7

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 确保上传目录存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_qr_status():
    """检查二维码是否存在及其是否过期"""
    path = os.path.join(app.config['UPLOAD_FOLDER'], QR_FILENAME)
    if not os.path.exists(path):
        return None, False
    
    # 获取文件最后修改时间
    file_time = os.path.getmtime(path)
    days_passed = (time.time() - file_time) / (24 * 3600)
    
    if days_passed > EXPIRE_DAYS:
        # 如果超过7天，自动删除
        os.remove(path)
        return None, False
    
    return QR_FILENAME, True

# --- 前端展示页面 ---
@app.route('/')
def index():
    qr_file, is_valid = get_qr_status()
    return render_template('index.html', qr_file=qr_file, is_valid=is_valid)

# --- 管理上传页面 ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        file = request.files.get('file')
        
        if password != ADMIN_PASSWORD:
            flash("密码错误！")
            return redirect(url_for('admin'))
        
        if file and file.filename != '':
            filename = secure_filename(QR_FILENAME)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash("群二维码上传成功！")
            return redirect(url_for('index'))
            
    return render_template('admin.html')

# 服务静态文件
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8092, debug=True)