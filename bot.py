import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

# --- Flask App Configuration for Vercel ---
app = Flask(__name__)
app.secret_key = "dramaworld_premium_final_v12"

# --- MongoDB Connection ---
MONGO_URI = "mongodb+srv://freelancermaruf1735:6XaThbuVG2zOUWm4@cluster0.ywwppvf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['dramaworld_db']
movies_col = db['movies']
settings_col = db['settings']
categories_col = db['categories']
users_col = db['users']
requests_col = db['requests']
notif_col = db['notifications']

# --- Config Loader ---
def get_config():
    conf = settings_col.find_one({"type": "config"})
    if not conf:
        conf = {
            "type": "config",
            "site_name": "DRAMA WORLD",
            "logo_url": "https://cdn-icons-png.flaticon.com/512/705/705062.png",
            "admin_user": "admin",
            "admin_pass": "admin123",
            "slider_limit": 5,
            "help_text": "Join our Telegram for updates.",
            "channel_link": "https://t.me/yourchannel",
            "ads": {"header": "", "middle": "", "footer": "", "native": "", "popunder": "", "socialbar": "", "sidebar": ""}
        }
        settings_col.insert_one(conf)
    return conf

# --- Premium UI CSS ---
CSS = """
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    body { font-family: 'Outfit', sans-serif; background: #050811; color: #f1f5f9; margin: 0; }
    .glass { background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.05); }
    .movie-card { transition: 0.4s; border-radius: 1.5rem; overflow: hidden; background: #0f172a; border: 1px solid #1e293b; }
    .movie-card:hover { transform: translateY(-8px); border-color: #3b82f6; box-shadow: 0 20px 40px -20px rgba(59, 130, 246, 0.5); }
    .footer-nav { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); width: 90%; max-width: 450px; height: 70px; border-radius: 35px; z-index: 1000; border: 1px solid rgba(59, 130, 246, 0.2); display: flex; justify-content: space-around; align-items: center; box-shadow: 0 15px 30px rgba(0,0,0,0.5); }
    .f-item { display: flex; flex-direction: column; align-items: center; color: #94a3b8; font-weight: bold; font-size: 10px; transition: 0.3s; text-decoration: none; }
    .f-item:hover, .f-item.active { color: #3b82f6; }
    .f-item i { font-size: 20px; margin-bottom: 2px; }
    input, select, textarea { background: #0f172a !important; color: white !important; border: 1px solid #1e293b !important; border-radius: 12px; padding: 12px; outline: none; width: 100%; }
    .sidebar-link { display: flex; align-items: center; gap: 12px; padding: 14px 20px; border-radius: 14px; transition: 0.3s; color: #94a3b8; font-weight: 600; text-decoration: none; }
    .sidebar-link:hover, .sidebar-link.active { background: #3b82f6; color: white; box-shadow: 0 10px 15px -5px rgba(59, 130, 246, 0.4); }
    .slider-img { display: none; width: 100%; height: 100%; object-fit: cover; animation: fade 1.5s ease; }
    .slide-active { display: block; }
    @keyframes fade { from { opacity: 0; } to { opacity: 1; } }
</style>
"""

# --- USER LAYOUT ---
def get_layout(content, active="home"):
    conf = get_config()
    user_sec = f'<a href="/login" class="bg-blue-600 px-5 py-2 rounded-full text-xs font-bold text-white shadow-lg">LOGIN</a>'
    if 'user_id' in session:
        user_sec = f'<a href="/profile" class="text-blue-400 font-bold flex items-center gap-2 text-decoration-none"><i class="fa fa-user-circle text-xl"></i> <span class="hidden md:inline">{session["user_name"]}</span></a>'
    
    mail_btn = f'<a href="/mail" class="f-item {"active" if active=="mail" else ""}"><i class="fa fa-envelope"></i><span>MAIL 📬</span></a>' if 'user_id' in session else ""

    return f"""
    <!DOCTYPE html><html><head><title>{conf['site_name']}</title>{CSS}</head><body>
        <nav class="glass sticky top-0 z-50 px-4 md:px-10 py-4 flex justify-between items-center border-b border-white/5">
            <a href="/" class="flex items-center gap-2 text-decoration-none">
                <img src="{conf['logo_url']}" class="h-8 md:h-10">
                <span class="text-xl md:text-2xl font-black text-blue-500 uppercase italic">{conf['site_name']}</span>
            </a>
            <div class="flex items-center gap-4">
                <form action="/" method="GET" class="hidden md:flex bg-slate-900 rounded-full px-4 py-1 border border-slate-800">
                    <input type="text" name="search" placeholder="Search..." class="bg-transparent border-none outline-none text-sm w-40 p-1">
                    <button type="submit"><i class="fa fa-search text-slate-500"></i></button>
                </form>
                {user_sec}
            </div>
        </nav>
        <div class="container mx-auto px-4 py-6">{content}</div>
        <div class="h-28"></div>
        <div class="glass footer-nav">
            <a href="/" class="f-item {"active" if active=="home" else ""}"><i class="fa fa-home"></i><span>HOME 🏠</span></a>
            <a href="/help" class="f-item {"active" if active=="help" else ""}"><i class="fa fa-question-circle"></i><span>HELP 🆘</span></a>
            <a href="/request" class="f-item {"active" if active=="request" else ""}"><i class="fa fa-paper-plane"></i><span>REQUEST 🚀</span></a>
            {mail_btn}
        </div>
    </body></html>
    """

# --- USER ROUTES ---

@app.route('/')
def index():
    conf = get_config()
    search = request.args.get('search')
    content = ""
    if search:
        movies = list(movies_col.find({"name": {"$regex": search, "$options": "i"}}))
        content += f'<h2 class="text-xl font-bold mb-6">Search Results for "{search}"</h2>'
        content += '<div class="grid grid-cols-2 md:grid-cols-6 gap-6">'
        for m in movies:
            content += f'<div class="movie-card cursor-pointer" onclick="location.href=\'/movie/{m["_id"]}\'"><img src="{m["poster"]}" class="w-full h-64 object-cover"><div class="p-3 text-sm font-bold truncate uppercase">{m["name"]}</div></div>'
        content += '</div>'
    else:
        slider_movies = list(movies_col.find().sort("_id", -1).limit(int(conf['slider_limit'])))
        content += '<div class="relative h-60 md:h-[450px] rounded-[2rem] overflow-hidden mb-12 shadow-2xl">'
        for i, sm in enumerate(slider_movies):
            active_class = "slide-active" if i == 0 else ""
            content += f'<img src="{sm["poster"]}" class="slider-img {active_class}">'
        content += '</div><script>let sIdx=0; const slides=document.querySelectorAll(".slider-img"); setInterval(()=>{slides[sIdx].classList.remove("slide-active"); sIdx=(sIdx+1)%slides.length; slides[sIdx].classList.add("slide-active");}, 5000);</script>'
        
        all_cats = list(categories_col.find())
        for cat in all_cats:
            ms = list(movies_col.find({"category": cat['name']}).sort("_id", -1))
            if ms:
                content += f'<h2 class="text-xl font-bold mb-6 flex items-center gap-3 mt-10"><span class="w-2 h-7 bg-blue-600 rounded-full"></span> {cat["name"]}</h2>'
                content += '<div class="grid grid-cols-2 md:grid-cols-6 gap-6">'
                for m in ms:
                    content += f'<div class="movie-card cursor-pointer" onclick="location.href=\'/movie/{m["_id"]}\'"><img src="{m["poster"]}" class="w-full h-64 object-cover"><div class="p-3 text-sm font-bold truncate uppercase italic">{m["name"]}</div></div>'
                content += '</div>'
    return get_layout(content, "home")

@app.route('/movie/<id>')
def movie_details(id):
    movie = movies_col.find_one({"_id": ObjectId(id)})
    if not movie: return redirect('/')
    links_html = "".join([f'<a href="{l["url"]}" target="_blank" class="bg-blue-600 text-white text-center py-4 rounded-2xl font-bold text-decoration-none shadow-xl">📥 {l["label"]}</a>' for l in movie['links']])
    content = f"""
    <div class="flex flex-col md:flex-row gap-10 py-10">
        <div class="w-full md:w-80"><img src="{movie['poster']}" class="w-full rounded-[2.5rem] shadow-2xl"></div>
        <div class="flex-1">
            <span class="bg-blue-600 px-4 py-1 rounded-full text-xs font-bold uppercase">{movie['badge']}</span>
            <h1 class="text-4xl font-black mt-4 mb-2 italic tracking-tighter uppercase">{movie['name']}</h1>
            <p class="text-blue-500 font-bold mb-8 uppercase text-sm tracking-widest">{movie['category']}</p>
            <div class="glass p-8 rounded-[2rem] border border-blue-500/20">
                <h3 class="text-xl font-bold mb-6 text-white border-b border-white/5 pb-4">DOWNLOAD LINKS</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">{links_html}</div>
            </div>
        </div>
    </div>
    """
    return get_layout(content, "home")

@app.route('/help')
def help_page():
    conf = get_config()
    content = f"""
    <div class="text-center py-10">
        <div class="glass p-10 md:p-20 rounded-[3rem] max-w-3xl mx-auto shadow-2xl border-t-4 border-blue-600">
            <img src="{conf['logo_url']}" class="h-20 mx-auto mb-8">
            <h1 class="text-4xl font-black mb-6 text-blue-500 uppercase italic">Support</h1>
            <p class="text-slate-400 text-lg mb-10 leading-relaxed">{conf['help_text']}</p>
            <a href="{conf['channel_link']}" target="_blank" class="bg-blue-600 px-10 py-5 rounded-2xl font-bold text-lg text-decoration-none text-white shadow-2xl inline-block">JOIN TELEGRAM CHANNEL</a>
        </div>
    </div>
    """
    return get_layout(content, "help")

@app.route('/request', methods=['GET', 'POST'])
def request_movie():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST':
        requests_col.insert_one({"user_id": session['user_id'], "user_name": session['user_name'], "movie_name": request.form.get('movie_name'), "email": request.form.get('email'), "status": "Pending", "date": datetime.now().strftime("%d %b %Y")})
        flash("Request Sent!")
        return redirect('/profile')
    content = f"""
    <form method="POST" class="glass p-10 rounded-[3rem] max-w-xl mx-auto space-y-6 border-t-4 border-blue-600 shadow-2xl mt-10">
        <h2 class="text-3xl font-black text-blue-500 uppercase italic">Request Movie 🚀</h2>
        <input name="movie_name" placeholder="Movie/Drama Name" required>
        <input value="{session['user_name']}" readonly>
        <input name="email" placeholder="Contact Email" required>
        <button class="bg-blue-600 w-full py-4 rounded-2xl font-bold text-white shadow-xl">SUBMIT REQUEST</button>
    </form>
    """
    return get_layout(content, "request")

@app.route('/mail')
def mailbox():
    if 'user_id' not in session: return redirect('/login')
    notifs = list(notif_col.find({"user_id": session['user_id']}).sort("_id", -1))
    content = '<h2 class="text-2xl font-black mb-8 text-blue-500 uppercase italic">📬 MailBox</h2><div class="space-y-4">'
    for n in notifs:
        content += f'<div class="glass p-6 rounded-2xl border-l-4 border-blue-600"><p class="text-sm font-semibold mb-2">{n["message"]}</p><p class="text-[10px] text-slate-500 uppercase">{n["date"]}</p></div>'
    if not notifs: content += '<p class="text-slate-500">No new mail.</p>'
    content += '</div>'
    return get_layout(content, "mail")

@app.route('/profile')
def profile():
    if 'user_id' not in session: return redirect('/login')
    u = users_col.find_one({"_id": ObjectId(session['user_id'])})
    content = f"""
    <div class="text-center py-10">
        <div class="glass p-12 rounded-[3rem] max-w-md mx-auto border-b-4 border-blue-600 shadow-2xl">
            <div class="w-20 h-20 bg-blue-600 rounded-full mx-auto flex items-center justify-center text-3xl font-black mb-4">{u['name'][0]}</div>
            <h2 class="text-2xl font-black">{u['name']}</h2>
            <p class="text-blue-500 font-bold text-xs mt-2 uppercase tracking-widest">ID: {u['uid']}</p>
            <a href="/logout" class="block mt-10 text-red-500 font-bold text-decoration-none">LOGOUT</a>
        </div>
    </div>
    """
    return get_layout(content, "home")

# --- ADMIN PANEL ---

def admin_layout(content, active="dash"):
    return f"""
    <!DOCTYPE html><html><head><title>Admin Panel</title>{CSS}</head>
    <body class="flex flex-col md:flex-row min-h-screen">
        <div class="w-full md:w-72 bg-[#080c14] border-r border-white/5 p-8 flex flex-col shadow-2xl">
            <h2 class="text-2xl font-black text-blue-500 mb-10 italic uppercase">Admin</h2>
            <nav class="space-y-2 flex-grow">
                <a href="/admin" class="sidebar-link {"active" if active=="dash" else ""}"><i class="fa fa-dashboard"></i> Dashboard</a>
                <a href="/admin/requests" class="sidebar-link {"active" if active=="req" else ""}"><i class="fa fa-paper-plane"></i> User Requests</a>
                <a href="/admin/add" class="sidebar-link {"active" if active=="add" else ""}"><i class="fa fa-plus-circle"></i> Add Movie</a>
                <a href="/admin/settings" class="sidebar-link {"active" if active=="settings" else ""}"><i class="fa fa-cog"></i> Settings</a>
                <a href="/logout" class="sidebar-link text-red-500 mt-10">Logout</a>
            </nav>
        </div>
        <main class="flex-grow p-6 md:p-12">{content}</main>
    </body></html>
    """

@app.route('/admin')
def admin_dash():
    if not session.get('admin'): return redirect('/login')
    search = request.args.get('search', '')
    query = {"name": {"$regex": search, "$options": "i"}} if search else {}
    movies = list(movies_col.find(query).sort("_id", -1))
    table_rows = "".join([f"<tr class='border-b border-slate-800'><td class='p-4 flex items-center gap-3'><img src='{m['poster']}' class='w-10 h-14 object-cover rounded-lg'> {m['name']}</td><td class='p-4 text-blue-400 font-bold uppercase text-xs'>{m['category']}</td><td class='p-4 text-center'><a href='/admin/edit/{m['_id']}' class='text-blue-500 mx-2'><i class='fa fa-edit'></i></a><a href='/admin/delete/{m['_id']}' class='text-red-500 mx-2' onclick='return confirm(\"Del?\")'><i class='fa fa-trash'></i></a></td></tr>" for m in movies])
    content = f"""
    <div class="flex flex-col md:flex-row justify-between items-center mb-10 gap-4">
        <h1 class="text-3xl font-black uppercase tracking-tighter">Movies</h1>
        <form class="flex bg-slate-900 rounded-xl px-4 py-1 border border-slate-800 w-full md:w-80">
            <input name="search" placeholder="Search movies..." class="bg-transparent border-none text-sm p-1" value="{search}">
            <button type="submit"><i class="fa fa-search text-slate-500"></i></button>
        </form>
    </div>
    <div class="glass rounded-3xl overflow-hidden"><table class="w-full text-left"><thead class="bg-slate-900 text-xs text-slate-500 uppercase tracking-widest"><tr><th class="p-4">Movie</th><th class="p-4">Category</th><th class="p-4 text-center">Action</th></tr></thead><tbody>{table_rows}</tbody></table></div>
    """
    return admin_layout(content, "dash")

@app.route('/admin/requests', methods=['GET', 'POST'])
def admin_requests():
    if not session.get('admin'): return redirect('/login')
    if request.method == 'POST':
        rid, status, admin_text = request.form.get('rid'), request.form.get('status'), request.form.get('admin_text')
        req = requests_col.find_one({"_id": ObjectId(rid)})
        if req:
            notif_col.insert_one({"user_id": req['user_id'], "message": f"Update on '{req['movie_name']}': {status}. Note: {admin_text}", "date": datetime.now().strftime("%d %b, %H:%M")})
            if status == "Uploaded/Done": requests_col.delete_one({"_id": ObjectId(rid)})
            else: requests_col.update_one({"_id": ObjectId(rid)}, {"$set": {"status": status}})
        return redirect('/admin/requests')
    reqs = list(requests_col.find().sort("_id", -1))
    req_html = ""
    for r in reqs:
        req_html += f"""
        <div class="glass p-6 rounded-3xl flex flex-col md:flex-row justify-between items-center gap-6 mb-4">
            <div><h3 class="text-xl font-bold text-blue-500 uppercase">{r['movie_name']}</h3><p class="text-xs text-slate-400">By: {r['user_name']} | Status: {r['status']}</p></div>
            <form method="POST" class="flex gap-2"><input type="hidden" name="rid" value="{r['_id']}"><input name="admin_text" placeholder="Admin Reply..." required class="text-xs w-48"><select name="status" class="text-xs w-32"><option>Uploaded/Done</option><option>Rejected</option></select><button class="bg-blue-600 px-6 py-2 rounded-xl font-bold text-xs uppercase">Reply</button></form>
        </div>"""
    return admin_layout(f'<h1 class="text-3xl font-black mb-10 uppercase">User Requests</h1>{req_html}', "req")

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not session.get('admin'): return redirect('/login')
    conf = get_config(); cats = list(categories_col.find())
    if request.method == 'POST':
        if 'update_branding' in request.form:
            settings_col.update_one({"type": "config"}, {"$set": {"site_name": request.form.get('site_name'), "logo_url": request.form.get('logo_url'), "help_text": request.form.get('help_text'), "channel_link": request.form.get('channel_link'), "slider_limit": int(request.form.get('slider_limit', 5))}})
        elif 'add_cat' in request.form: categories_col.insert_one({"name": request.form.get('cat_name')})
        elif 'del_cat' in request.form: categories_col.delete_one({"_id": ObjectId(request.form.get('cat_id'))})
        return redirect('/admin/settings')
    cat_rows = "".join([f"<div class='flex justify-between bg-slate-900 p-3 rounded-xl mb-2'><span>{c['name']}</span><form method='POST' class='inline'><input type='hidden' name='cat_id' value='{c['_id']}'><button name='del_cat' class='text-red-500'><i class='fa fa-trash'></i></button></form></div>" for c in cats])
    content = f"""
    <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
        <form method="POST" class="glass p-8 rounded-[2.5rem] space-y-4"><h3 class="text-blue-500 font-bold uppercase text-xs border-b border-white/5 pb-2">Site Settings</h3>
            <input name="site_name" value="{conf['site_name']}" placeholder="Site Name"><input name="logo_url" value="{conf['logo_url']}" placeholder="Logo URL">
            <textarea name="help_text" rows="3">{conf['help_text']}</textarea><input name="channel_link" value="{conf['channel_link']}" placeholder="Telegram Link">
            <input type="number" name="slider_limit" value="{conf['slider_limit']}"><button name="update_branding" class="bg-blue-600 w-full py-4 rounded-xl font-bold uppercase">Save Branding</button>
        </form>
        <form method="POST" class="glass p-8 rounded-[2.5rem] space-y-4"><h3 class="text-green-500 font-bold uppercase text-xs border-b border-white/5 pb-2">Categories</h3>
            <div class="flex gap-2"><input name="cat_name" placeholder="New category"><button name="add_cat" class="bg-green-600 px-6 rounded-xl font-bold">ADD</button></div>
            <div class="max-h-48 overflow-y-auto">{cat_rows}</div>
        </form>
    </div>"""
    return admin_layout(content, "settings")

@app.route('/admin/add', methods=['GET', 'POST'])
def admin_add():
    if not session.get('admin'): return redirect('/login')
    cats = list(categories_col.find())
    if request.method == 'POST':
        labels, urls = request.form.getlist('l_name[]'), request.form.getlist('l_url[]')
        links = [{"label": labels[i], "url": urls[i]} for i in range(len(labels))]
        movies_col.insert_one({"name": request.form.get('name'), "poster": request.form.get('poster'), "badge": request.form.get('badge'), "category": request.form.get('category'), "links": links})
        return redirect('/admin')
    cat_options = "".join([f"<option>{c['name']}</option>" for c in cats])
    content = f"""
    <form method="POST" class="glass p-10 rounded-[3rem] max-w-4xl mx-auto space-y-6 shadow-2xl">
        <h2 class="text-2xl font-black text-blue-500 uppercase italic">Publish Movie</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4"><input name="name" placeholder="Movie Name" required><select name="category">{cat_options}</select></div>
        <input name="poster" placeholder="Poster URL" required><input name="badge" placeholder="Badge (e.g. 1080p)">
        <div id="lc" class="space-y-3 pt-6 border-t border-slate-800"><label class="text-xs font-bold text-blue-500 uppercase">Links</label></div>
        <button type="button" onclick="addL()" class="text-blue-400 font-bold text-xs uppercase hover:underline">+ Add Link</button>
        <button class="bg-blue-600 w-full py-4 rounded-2xl font-bold uppercase">Publish Now</button>
    </form>
    <script>function addL(){{ let d=document.createElement('div'); d.className='flex gap-4'; d.innerHTML='<input name="l_name[]" placeholder="Label" required><input name="l_url[]" placeholder="URL" required>'; document.getElementById('lc').appendChild(d); }} addL();</script>
    """
    return admin_layout(content, "add")

@app.route('/admin/edit/<id>', methods=['GET', 'POST'])
def admin_edit(id):
    if not session.get('admin'): return redirect('/login')
    movie = movies_col.find_one({"_id": ObjectId(id)})
    if request.method == 'POST':
        labels, urls = request.form.getlist('l_name[]'), request.form.getlist('l_url[]')
        links = [{"label": labels[i], "url": urls[i]} for i in range(len(labels))]
        movies_col.update_one({"_id": ObjectId(id)}, {"$set": {"name": request.form.get('name'), "poster": request.form.get('poster'), "badge": request.form.get('badge'), "category": request.form.get('category'), "links": links}})
        return redirect('/admin')
    links_html = "".join([f"<div class='flex gap-2 mb-2'><input name='l_name[]' value='{l['label']}'><input name='l_url[]' value='{l['url']}'></div>" for l in movie['links']])
    content = f"""<form method="POST" class="glass p-10 max-w-2xl mx-auto space-y-4 rounded-[2rem]"><h2 class="text-xl font-bold uppercase">Edit: {movie['name']}</h2><input name="name" value="{movie['name']}"><input name="poster" value="{movie['poster']}"><input name="category" value="{movie['category']}"><div id="ec">{links_html}</div><button class="bg-blue-600 w-full py-4 rounded-xl font-bold uppercase">Save Edit</button></form>"""
    return admin_layout(content, "dash")

@app.route('/admin/delete/<id>')
def admin_del(id):
    if not session.get('admin'): return redirect('/login')
    movies_col.delete_one({"_id": ObjectId(id)}); return redirect('/admin')

# --- AUTH ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name, user, pw = request.form.get('name'), request.form.get('user'), request.form.get('pass')
        if not users_col.find_one({"user": user}):
            users_col.insert_one({"uid": "DW"+str(ObjectId())[-6:].upper(), "name": name, "user": user, "pass": pw})
            flash("Success! Please Login."); return redirect('/login')
        flash("Username exists!")
    return render_template_string(f"<!DOCTYPE html><html><head>{CSS}</head><body class='flex items-center justify-center min-h-screen p-4'><form method='POST' class='glass p-10 rounded-[2.5rem] w-full max-w-md space-y-4 border-t-4 border-blue-600'><h2 class='text-2xl font-black text-center text-blue-500 uppercase'>Register</h2><input name='name' placeholder='Full Name' required><input name='user' placeholder='Username' required><input type='password' name='pass' placeholder='Password' required><button class='bg-blue-600 w-full py-4 rounded-xl font-bold text-white'>SIGN UP</button><p class='text-center text-xs'>Have account? <a href='/login' class='text-blue-500'>Login</a></p></form></body></html>")

@app.route('/login', methods=['GET', 'POST'])
def login():
    conf = get_config()
    if request.method == 'POST':
        user, pw = request.form.get('user'), request.form.get('pass')
        if user == conf['admin_user'] and pw == conf['admin_pass']: session['admin'] = True; return redirect('/admin')
        u = users_col.find_one({"user": user, "pass": pw})
        if u: session['user_id'] = str(u['_id']); session['user_name'] = u['name']; return redirect('/')
        flash("Invalid!")
    return render_template_string(f"<!DOCTYPE html><html><head>{CSS}</head><body class='flex items-center justify-center min-h-screen p-4'><form method='POST' class='glass p-10 rounded-[2.5rem] w-full max-w-md space-y-6 border-t-4 border-blue-600'><h2 class='text-2xl font-black text-center text-blue-500 uppercase'>Login</h2><input name='user' placeholder='Username' required><input type='password' name='pass' placeholder='Password' required><button class='bg-blue-600 w-full py-4 rounded-xl font-bold text-white shadow-xl'>LOG IN</button><p class='text-center text-sm'>New? <a href='/register' class='text-blue-500'>Register</a></p></form></body></html>")

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

# --- Entry Point for Vercel ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)
