import os
import time
import shutil
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from PIL import Image

app = Flask(__name__)
app.secret_key = 'wxHm_secure_key_2026'

# --- 配置中心 ---
UPLOAD_BASE = 'uploads'
ADMIN_PASSWORD = 'admin123'  # 请在此处修改你的管理密码
EXPIRE_DAYS = 7             

if not os.path.exists(UPLOAD_BASE):
    os.makedirs(UPLOAD_BASE)

def get_active_qr(group_name):
    """获取最新且有效的图片文件名"""
    group_path = os.path.join(UPLOAD_BASE, group_name)
    if not os.path.exists(group_path): return None
    files = [f for f in os.listdir(group_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    if not files: return None
    
    files.sort(key=lambda x: os.path.getmtime(os.path.join(group_path, x)), reverse=True)
    
    now = time.time()
    active_file = None
    for filename in files:
        path = os.path.join(group_path, filename)
        if (now - os.path.getmtime(path)) / (24 * 3600) < EXPIRE_DAYS:
            if not active_file: active_file = filename
        else:
            try: os.remove(path)
            except: pass
    return active_file

# --- 路由：用户扫码页 ---
@app.route('/group/<group_name>')
def group_page(group_name):
    qr_file = get_active_qr(group_name)
    
    # 构造公网绝对路径 (wsrv.nl 需要绝对 URL 才能抓取)
    # request.host_url 会获取如 http://example.com/
    base_url = request.host_url.rstrip('/') 
    raw_img_url = f"{base_url}/uploads/{group_name}/{qr_file}"
    
    # 拼接 wsrv.nl 处理链接 (&we=1 转WebP, &v=随机数防缓存)
    wsrv_url = f"https://wsrv.nl/?url={raw_img_url}&we=1&v={int(time.time())}"
    
    return render_template('index.html', 
                           group_name=group_name, 
                           qr_file=qr_file, 
                           wsrv_url=wsrv_url)

# --- 路由：管理后台 ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    existing_groups = [d for d in os.listdir(UPLOAD_BASE) if os.path.isdir(os.path.join(UPLOAD_BASE, d))]
    existing_groups.sort()
    
    if request.method == 'POST':
        pwd = request.form.get('password')
        group_input = request.form.get('group_name', '').strip()
        file = request.files.get('file')
        
        if pwd != ADMIN_PASSWORD:
            flash("密码错误！")
            return redirect(url_for('admin'))
        
        if group_input and file:
            group_dir = os.path.join(UPLOAD_BASE, group_input)
            if not os.path.exists(group_dir): os.makedirs(group_dir)
            
            try:
                img = Image.open(file)
                if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                new_filename = f"qr_{int(time.time())}.webp"
                img.save(os.path.join(group_dir, new_filename), "WEBP", quality=80)
                flash(f"群组【{group_input}】更新成功 (已优化为WebP)")
            except Exception as e:
                flash(f"上传失败: {str(e)}")
            return redirect(url_for('admin'))
            
    return render_template('admin.html', groups=existing_groups)

# --- 路由：更名与删除 ---
@app.route('/admin/rename', methods=['POST'])
def rename_group():
    pwd = request.form.get('password')
    old_name = request.form.get('old_name')
    new_name = request.form.get('new_name', '').strip()
    if pwd == ADMIN_PASSWORD and old_name and new_name:
        old_path, new_path = os.path.join(UPLOAD_BASE, old_name), os.path.join(UPLOAD_BASE, new_name)
        if not os.path.exists(new_path):
            os.rename(old_path, new_path)
            flash("重命名成功")
    return redirect(url_for('admin'))

@app.route('/admin/delete/<group_name>', methods=['POST'])
def delete_group(group_name):
    pwd = request.form.get('password')
    if pwd == ADMIN_PASSWORD:
        shutil.rmtree(os.path.join(UPLOAD_BASE, group_name))
        flash("群组已删除")
    return redirect(url_for('admin'))

@app.route('/uploads/<group_name>/<filename>')
def serve_qr(group_name, filename):
    return send_from_directory(os.path.join(UPLOAD_BASE, group_name), filename)

@app.route('/')
def home():
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8092)