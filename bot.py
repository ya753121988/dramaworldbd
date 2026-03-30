import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

# --- Flask Project Handler ---
app = Flask(__name__)
app.secret_key = "dramaworld_ultra_premium_ultimate_v15"

# --- MongoDB Connection ---
MONGO_URI = "mongodb+srv://freelancermaruf1735:6XaThbuVG2zOUWm4@cluster0.ywwppvf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['dramaworld_db']

# Collections
movies_col = db['movies']
settings_col = db['settings']
categories_col = db['categories']
users_col = db['users']
requests_col = db['requests']
notif_col = db['notifications']

# --- Database & Config Initializer ---
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
            "help_text": "Welcome to DramaWorld BD. Join our telegram channel for more updates and direct help.",
            "channel_link": "https://t.me/yourchannel",
            "ads": {
                "header": "", "middle": "", "footer": "", 
                "native": "", "popunder": "", "socialbar": "", "banner": ""
            }
        }
        settings_col.insert_one(conf)
    
    required_keys = ["site_name", "logo_url", "help_text", "channel_link", "slider_limit", "ads", "admin_user", "admin_pass"]
    for key in required_keys:
        if key not in conf:
            if key == "ads":
                conf["ads"] = {"header": "", "middle": "", "footer": "", "native": "", "popunder": "", "socialbar": "", "banner": ""}
            elif key == "slider_limit": conf[key] = 5
            else: conf[key] = "Not Set"
    return conf

# --- Global CSS ---
CSS = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;900&display=swap');
    body { font-family: 'Outfit', sans-serif; background-color: #02040a; color: #e2e8f0; margin:0; overflow-x: hidden; }
    .glass { background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.05); }
    .movie-card { transition: 0.4s; border: 1px solid rgba(255,255,255,0.05); border-radius: 1.5rem; overflow: hidden; background: #0f172a; position: relative; }
    .movie-card:hover { transform: translateY(-10px); border-color: #3b82f6; box-shadow: 0 20px 40px -15px rgba(59, 130, 246, 0.5); }
    .slider-box { position: relative; width: 100%; height: 230px; overflow: hidden; border-radius: 30px; border: 1px solid rgba(59, 130, 246, 0.2); }
    @media(min-width: 768px) { .slider-box { height: 480px; } }
    .slide-img { display: none; width: 100%; height: 100%; object-fit: cover; animation: fade 1.5s ease; }
    .slide-active { display: block; }
    @keyframes fade { from { opacity: 0; } to { opacity: 1; } }
    input, select, textarea { background: #0f172a !important; color: white !important; border: 1px solid #1e293b !important; border-radius: 12px; padding: 12px; outline: none; width: 100%; transition: 0.3s; }
    input:focus { border-color: #3b82f6 !important; box-shadow: 0 0 10px rgba(59, 130, 246, 0.3); }
    .sidebar-link { display: flex; align-items: center; gap: 12px; padding: 14px 20px; border-radius: 14px; transition: 0.3s; color: #94a3b8; font-weight: 600; text-decoration: none; }
    .sidebar-link:hover, .sidebar-link.active { background: #3b82f6; color: white; box-shadow: 0 10px 20px -5px rgba(59, 130, 246, 0.4); }
    .footer-nav { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); width: 92%; max-width: 480px; height: 75px; border-radius: 40px; z-index: 1000; border: 1px solid rgba(59, 130, 246, 0.3); display: flex; justify-content: space-around; align-items: center; box-shadow: 0 20px 50px rgba(0,0,0,0.8); }
    .f-item { display: flex; flex-direction: column; align-items: center; color: #94a3b8; font-weight: bold; font-size: 11px; transition: 0.3s; text-decoration: none; }
    .f-item:hover, .f-item.active { color: #3b82f6; }
    .f-item i { font-size: 22px; margin-bottom: 2px; }
    .btn-premium { background: linear-gradient(135deg, #3b82f6, #1e40af); color: white; font-weight: bold; padding: 14px; border-radius: 15px; transition: 0.3s; text-align: center; display: block; text-decoration: none; }
    .btn-premium:hover { transform: scale(1.02); opacity: 0.9; }
</style>
"""

# --- UTILITY HELPERS ---

def get_navbar(conf):
    user_status = '<a href="/login" class="bg-blue-600 px-5 py-2 rounded-full text-xs font-bold text-white shadow-lg text-decoration-none">LOGIN</a>'
    if 'user_id' in session:
        user_status = f'''
        <div class="flex items-center gap-4">
            <a href="/profile" class="text-blue-400 font-bold flex items-center gap-2 text-decoration-none">
                <i class="fa fa-user-circle text-2xl"></i>
                <span class="hidden md:inline">{session.get("user_name")}</span>
            </a>
        </div>
        '''
    return f'''
    <nav class="glass sticky top-0 z-50 px-4 md:px-10 py-4 flex justify-between items-center border-b border-white/5">
        <a href="/" class="flex items-center gap-2 text-decoration-none">
            <img src="{conf['logo_url']}" class="h-8 md:h-11">
            <span class="text-xl md:text-2xl font-black text-blue-500 uppercase italic tracking-tighter">{conf['site_name']}</span>
        </a>
        <div class="flex items-center gap-6">
            <form action="/" method="GET" class="hidden md:flex bg-slate-900 rounded-full px-4 py-1 border border-slate-800">
                <input type="text" name="search" placeholder="Search movies..." class="bg-transparent border-none outline-none text-sm w-48 p-1">
                <button type="submit" class="text-slate-500"><i class="fa fa-search"></i></button>
            </form>
            {user_status}
        </div>
    </nav>
    '''

def get_footer():
    mail_link = ""
    if 'user_id' in session:
        mail_link = '<a href="/mailbox" class="f-item"><i class="fa fa-envelope"></i><span>MAIL 📬</span></a>'
    return f'''
    <div class="h-28"></div>
    <div class="glass footer-nav">
        <a href="/" class="f-item"><i class="fa fa-home"></i><span>HOME 🏠</span></a>
        <a href="/help" class="f-item"><i class="fa fa-question-circle"></i><span>HELP 🆘</span></a>
        <a href="/request" class="f-item"><i class="fa fa-paper-plane"></i><span>REQUEST 🚀</span></a>
        {mail_link}
    </div>
    '''

# --- USER FACING ROUTES (NO WP) ---

@app.route('/')
def index():
    conf = get_config()
    search = request.args.get('search')
    if search:
        movies = list(movies_col.find({"name": {"$regex": search, "$options": "i"}}))
        results_title = f'Search Results for "{search}"'
        slider_movies = []
        grouped_movies = {results_title: movies}
    else:
        all_cats = list(categories_col.find())
        grouped_movies = {}
        for cat in all_cats:
            grouped_movies[cat['name']] = list(movies_col.find({"category": cat['name']}).sort("_id", -1))
        slider_movies = list(movies_col.find().sort("_id", -1).limit(int(conf['slider_limit'])))

    html_content = f"""
    <!DOCTYPE html><html><head>{CSS}<title>{conf['site_name']}</title></head><body>
    {get_navbar(conf)}
    <div class="container mx-auto px-4 py-6">
        <div class="mb-6 text-center"> {{{{ conf.ads.header | safe }}}} </div>
        {{% if slider_movies %}}
        <div class="slider-box mb-12 shadow-2xl">
            {{% for sm in slider_movies %}}
            <a href="/movie/{{{{ sm._id }}}}"><img src="{{{{ sm.poster }}}}" class="slide-img"></a>
            {{% endfor %}}
        </div>
        {{% endif %}}
        <div class="mb-8 text-center"> {{{{ conf.ads.middle | safe }}}} </div>
        {{% for cat_name, ms in grouped_movies.items() %}}
            {{% if ms %}}
            <div class="mb-12">
                <h2 class="text-xl font-bold mb-6 flex items-center gap-3"><span class="w-2 h-8 bg-blue-600 rounded-full shadow-[0_0_15px_#3b82f6]"></span> {{{{ cat_name }}}}</h2>
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
                    {{% for m in ms %}}
                    <div class="movie-card cursor-pointer" onclick="location.href='/movie/{{{{ m._id }}}}'">
                        <img src="{{{{ m.poster }}}}" class="w-full h-64 md:h-80 object-cover">
                        <div class="absolute top-3 left-3 bg-blue-600 text-[10px] font-bold px-3 py-1 rounded-full uppercase border border-white/20">{{{{ m.badge }}}}</div>
                        <div class="p-4 bg-slate-900/90 backdrop-blur-md"><h3 class="font-bold text-sm truncate uppercase italic tracking-tighter">{{{{ m.name }}}}</h3></div>
                    </div>
                    {{% endfor %}}
                </div>
            </div>
            {{% endif %}}
        {{% endfor %}}
        <div class="mt-10 text-center"> {{{{ conf.ads.footer | safe }}}} </div>
        <div class="text-center mt-4"> {{{{ conf.ads.banner | safe }}}} </div>
        <div class="text-center mt-4"> {{{{ conf.ads.native | safe }}}} </div>
    </div>
    {get_footer()}
    <script>
        let sIdx = 0; const slides = document.querySelectorAll('.slide-img');
        if(slides.length > 0){{
            slides[0].classList.add('slide-active');
            setInterval(() => {{
                slides[sIdx].classList.remove('slide-active');
                sIdx = (sIdx + 1) % slides.length;
                slides[sIdx].classList.add('slide-active');
            }}, 5000);
        }}
    </script>
    </body></html>
    """
    return render_template_string(html_content, slider_movies=slider_movies, grouped_movies=grouped_movies, conf=conf)

@app.route('/movie/<id>')
def movie_details(id):
    conf = get_config()
    movie = movies_col.find_one({"_id": ObjectId(id)})
    if not movie: return redirect('/')
    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>{{{{movie.name}}}}</title></head><body>
    {get_navbar(conf)}
    <div class="container mx-auto px-4 py-10">
        <div class="flex flex-col md:flex-row gap-10">
            <div class="w-full md:w-80"><img src="{{{{ movie.poster }}}}" class="w-full rounded-[2.5rem] shadow-2xl border-4 border-slate-900"></div>
            <div class="flex-1">
                <span class="bg-blue-600 px-5 py-1 rounded-full text-xs font-bold uppercase shadow-lg">{{{{ movie.badge }}}}</span>
                <h1 class="text-4xl md:text-5xl font-black mt-4 mb-2 italic tracking-tighter uppercase leading-tight">{{{{ movie.name }}}}</h1>
                <p class="text-blue-500 font-bold mb-8 uppercase text-sm tracking-widest">{{{{ movie.category }}}}</p>
                <div class="glass p-8 rounded-[2rem] border border-blue-500/20 shadow-2xl">
                    <h3 class="text-xl font-bold mb-8 flex items-center gap-3 text-white border-b border-white/5 pb-4">
                        <i class="fa fa-play-circle text-blue-500 text-3xl"></i> DOWNLOAD & WATCH LINKS
                    </h3>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {{% for link in movie.links %}}
                        <a href="{{{{ link.url }}}}" target="_blank" class="btn-premium">📥 {{{{ link.label }}}}</a>
                        {{% endfor %}}
                    </div>
                </div>
                <div class="mt-8 text-center"> {{{{ conf.ads.native | safe }}}} </div>
            </div>
        </div>
    </div>
    {get_footer()}
    </body></html>
    """
    return render_template_string(html, movie=movie, conf=conf)

@app.route('/help')
def help_page():
    conf = get_config()
    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>Support - {conf['site_name']}</title></head><body>
    {get_navbar(conf)}
    <div class="container mx-auto px-4 py-10 text-center">
        <div class="glass p-10 md:p-20 rounded-[3.5rem] max-w-4xl mx-auto shadow-2xl border-t-4 border-blue-600">
            <img src="{conf['logo_url']}" class="h-24 mx-auto mb-8 drop-shadow-2xl">
            <h1 class="text-4xl font-black mb-6 uppercase italic text-blue-500">Need Assistance?</h1>
            <p class="text-slate-400 text-lg mb-12 leading-relaxed"> {{{{ conf.help_text }}}} </p>
            <a href="{conf['channel_link']}" target="_blank" class="bg-blue-600 hover:bg-blue-700 text-white px-12 py-5 rounded-2xl font-bold text-lg shadow-2xl inline-flex items-center gap-3 transition transform hover:scale-105 text-decoration-none">
                <i class="fa fa-paper-plane"></i> JOIN OUR TELEGRAM CHANNEL
            </a>
        </div>
    </div>
    {get_footer()}
    </body></html>
    """
    return render_template_string(html, conf=conf)

# --- USER AUTHENTICATION (NO WP) ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name, user, pw = request.form.get('name'), request.form.get('user'), request.form.get('pass')
        if users_col.find_one({"user": user}):
            flash("Username already exists!")
        else:
            uid = "DW" + str(ObjectId())[-6:].upper()
            users_col.insert_one({"uid": uid, "name": name, "user": user, "pass": pw})
            flash("Registration Successful! Please Login.")
            return redirect('/login')
    
    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>Sign Up</title></head>
    <body class="flex items-center justify-center min-h-screen p-4">
        <form method="POST" class="glass p-10 rounded-[2.5rem] w-full max-md space-y-6 shadow-2xl border-t-4 border-blue-600">
            <h2 class="text-3xl font-black text-center text-blue-500 uppercase italic">Create Account</h2>
            {{% with messages = get_flashed_messages() %}}{{% if messages %}}<p class="text-red-500 text-xs text-center font-bold">{{{{messages[0]}}}}</p>{{% endif %}}{{% endwith %}}
            <input type="text" name="name" placeholder="Full Name" required>
            <input type="text" name="user" placeholder="Username" required>
            <input type="password" name="pass" placeholder="Password" required>
            <button class="bg-blue-600 w-full py-4 rounded-2xl font-bold text-white shadow-xl uppercase">Register</button>
            <p class="text-center text-sm text-slate-400">Already have account? <a href="/login" class="text-blue-500 font-bold">Login</a></p>
        </form>
    </body></html>
    """
    return render_template_string(html)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user, pw = request.form.get('user', '').strip(), request.form.get('pass', '').strip()
        u = users_col.find_one({"user": user, "pass": pw})
        if u:
            session.clear()
            session['user_id'] = str(u['_id'])
            session['user_name'] = u['name']
            return redirect('/')
        flash("Invalid Credentials!")
    
    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>User Login</title></head>
    <body class="flex items-center justify-center min-h-screen p-4">
        <form method="POST" class="glass p-10 rounded-[2.5rem] w-full max-w-md space-y-6 shadow-2xl border-t-4 border-blue-600">
            <h2 class="text-3xl font-black text-center text-blue-500 uppercase italic">User Login</h2>
            {{% with messages = get_flashed_messages() %}}{{% if messages %}}<p class="text-red-500 text-xs text-center font-bold">{{{{messages[0]}}}}</p>{{% endif %}}{{% endwith %}}
            <input type="text" name="user" placeholder="Username" required>
            <input type="password" name="pass" placeholder="Password" required>
            <button class="bg-blue-600 w-full py-4 rounded-2xl font-bold text-white shadow-xl uppercase">Access Account</button>
            <p class="text-center text-xs text-slate-500">New? <a href="/register" class="text-blue-500 font-bold">Sign Up</a></p>
        </form>
    </body></html>
    """
    return render_template_string(html)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- USER SYSTEM: REQUESTS, MAIL, PROFILE ---

@app.route('/request', methods=['GET', 'POST'])
def request_movie():
    if 'user_id' not in session: return redirect('/login')
    conf = get_config()
    if request.method == 'POST':
        requests_col.insert_one({
            "user_id": session['user_id'], "user_name": session['user_name'],
            "movie_name": request.form.get('movie_name'), "email": request.form.get('email'),
            "status": "Pending", "date": datetime.now().strftime("%d %b %Y")
        })
        flash("Request submitted!")
        return redirect('/mailbox')
    
    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>Request</title></head><body>
    {get_navbar(conf)}
    <div class="container mx-auto px-4 py-10">
        <form method="POST" class="glass p-10 rounded-[3rem] max-w-xl mx-auto space-y-6 border-t-4 border-blue-600 shadow-2xl">
            <h2 class="text-3xl font-black text-blue-500 uppercase italic">Request Movie</h2>
            <input type="text" name="movie_name" placeholder="Movie Name" required>
            <input type="email" name="email" placeholder="Your Email" required>
            <button class="bg-blue-600 w-full py-4 rounded-2xl font-bold text-white uppercase">Submit</button>
        </form>
    </div>
    {get_footer()}
    </body></html>
    """
    return render_template_string(html)

@app.route('/mailbox')
def mailbox():
    if 'user_id' not in session: return redirect('/login')
    conf = get_config()
    notifs = list(notif_col.find({"user_id": session['user_id']}).sort("_id", -1))
    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>MailBox</title></head><body>
    {get_navbar(conf)}
    <div class="container mx-auto px-4 py-10 max-w-4xl">
        <h2 class="text-3xl font-black mb-8 text-blue-500 uppercase italic">MailBox (Inbox)</h2>
        <div class="space-y-4">
            {{% for n in notifs %}}
            <div class="glass p-6 rounded-3xl border-l-4 border-blue-600 shadow-xl">
                <p class="text-sm font-semibold text-slate-200">{{{{ n.message }}}}</p>
                <span class="text-[10px] text-slate-600 uppercase">{{{{ n.date }}}}</span>
            </div>
            {{% endfor %}}
        </div>
    </div>
    {get_footer()}
    </body></html>
    """
    return render_template_string(html, notifs=notifs, conf=conf)

@app.route('/profile')
def profile():
    if 'user_id' not in session: return redirect('/login')
    conf = get_config()
    u = users_col.find_one({"_id": ObjectId(session['user_id'])})
    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>Profile</title></head><body>
    {get_navbar(conf)}
    <div class="container mx-auto px-4 py-10 text-center">
        <div class="glass p-12 rounded-[3.5rem] max-w-md mx-auto border-b-4 border-blue-600 shadow-2xl">
            <div class="w-24 h-24 bg-blue-600 rounded-full mx-auto flex items-center justify-center text-4xl font-black mb-6 shadow-xl border-4 border-slate-900">{u['name'][0]}</div>
            <h2 class="text-3xl font-black mb-1 uppercase italic tracking-tighter">{u['name']}</h2>
            <p class="text-blue-500 font-bold text-xs mb-8 uppercase tracking-widest">ID: {u['uid']}</p>
            <a href="/logout" class="block py-4 text-red-500 font-black text-xs uppercase tracking-widest hover:underline">Sign Out</a>
        </div>
    </div>
    {get_footer()}
    </body></html>
    """
    return render_template_string(html)

# --- ADMIN PANEL (URL: /admin/wp) ---

@app.route('/admin/wp/login', methods=['GET', 'POST'])
def admin_login():
    conf = get_config()
    if request.method == 'POST':
        user, pw = request.form.get('user'), request.form.get('pass')
        if user == conf['admin_user'] and pw == conf['admin_pass']:
            session['admin'] = True
            return redirect('/admin/wp')
        flash("Admin Login Failed!")
    
    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>Admin Access</title></head>
    <body class="bg-black flex items-center justify-center min-h-screen">
        <form method="POST" class="glass p-10 rounded-[2.5rem] w-full max-w-md space-y-6 border-t-4 border-blue-500 shadow-2xl">
            <h2 class="text-3xl font-black text-center text-blue-500 uppercase italic">ADMIN WP LOGIN</h2>
            {{% with messages = get_flashed_messages() %}}{{% if messages %}}<p class="text-red-500 text-xs text-center font-bold">{{{{messages[0]}}}}</p>{{% endif %}}{{% endwith %}}
            <input type="text" name="user" placeholder="Admin Username" required>
            <input type="password" name="pass" placeholder="Admin Password" required>
            <button class="bg-blue-600 w-full py-4 rounded-2xl font-bold text-white uppercase shadow-xl">Admin Access</button>
        </form>
    </body></html>
    """
    return render_template_string(html)

@app.route('/admin/wp')
def admin_dash():
    if not session.get('admin'): return redirect('/admin/wp/login')
    search = request.args.get('search', '')
    query = {"name": {"$regex": search, "$options": "i"}} if search else {}
    movies = list(movies_col.find(query).sort("_id", -1))
    
    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>Admin Dashboard</title></head>
    <body class="flex flex-col md:flex-row min-h-screen">
        <div class="w-full md:w-72 bg-[#080c14] border-r border-slate-900 p-8 flex flex-col shadow-2xl h-full sticky top-0">
            <h2 class="text-2xl font-black text-blue-500 uppercase italic mb-10">ADMIN WP</h2>
            <nav class="space-y-2">
                <a href="/admin/wp" class="sidebar-link active"><i class="fa fa-dashboard"></i> Dashboard</a>
                <a href="/admin/wp/requests" class="sidebar-link"><i class="fa fa-paper-plane"></i> User Requests</a>
                <a href="/admin/wp/add" class="sidebar-link"><i class="fa fa-plus-circle"></i> Add Movie</a>
                <a href="/admin/wp/settings" class="sidebar-link"><i class="fa fa-cog"></i> Settings</a>
                <a href="/logout" class="sidebar-link text-red-500 mt-20"><i class="fa fa-sign-out-alt"></i> Logout</a>
            </nav>
        </div>
        <main class="flex-grow p-6 md:p-12">
            <div class="flex flex-col md:flex-row justify-between items-center mb-10 gap-4">
                <h1 class="text-3xl font-black uppercase">Library</h1>
                <form action="/admin/wp" method="GET" class="flex bg-slate-900 rounded-2xl px-5 py-2 border border-slate-800 w-full md:w-96 shadow-lg">
                    <input type="text" name="search" placeholder="Search..." class="bg-transparent border-none p-1 text-sm" value="{search}">
                    <button type="submit" class="text-slate-500"><i class="fa fa-search"></i></button>
                </form>
            </div>
            <div class="glass rounded-[2.5rem] overflow-hidden shadow-2xl">
                <table class="w-full text-left">
                    <thead class="bg-slate-900 text-slate-500 text-xs uppercase font-bold tracking-widest">
                        <tr><th class="p-6">Movie</th><th class="p-6">Category</th><th class="p-6 text-center">Manage</th></tr>
                    </thead>
                    <tbody class="divide-y divide-slate-800">
                        {{% for m in movies %}}
                        <tr class="hover:bg-slate-800/50">
                            <td class="p-6"><span class="font-bold text-sm">{{{{ m.name }}}}</span></td>
                            <td class="p-6 text-xs text-blue-400 font-bold uppercase">{{{{ m.category }}}}</td>
                            <td class="p-6">
                                <div class="flex justify-center gap-4">
                                    <a href="/admin/wp/edit/{{{{ m._id }}}}" class="text-blue-500"><i class="fa fa-edit"></i></a>
                                    <a href="/admin/wp/delete/{{{{ m._id }}}}" class="text-red-500" onclick="return confirm('Delete?')"><i class="fa fa-trash"></i></a>
                                </div>
                            </td>
                        </tr>
                        {{% endfor %}}
                    </tbody>
                </table>
            </div>
        </main>
    </body></html>
    """
    return render_template_string(html, movies=movies)

@app.route('/admin/wp/add', methods=['GET', 'POST'])
def add_movie():
    if not session.get('admin'): return redirect('/admin/wp/login')
    cats = list(categories_col.find())
    if request.method == 'POST':
        labels, urls = request.form.getlist('l_name[]'), request.form.getlist('l_url[]')
        links = [{"label": labels[i], "url": urls[i]} for i in range(len(labels))]
        movies_col.insert_one({
            "name": request.form.get('name'), "poster": request.form.get('poster'),
            "badge": request.form.get('badge'), "category": request.form.get('category'), "links": links
        })
        return redirect('/admin/wp')
    
    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>Add Movie</title></head>
    <body class="flex flex-col md:flex-row min-h-screen">
        <div class="w-full md:w-72 bg-[#080c14] border-r border-slate-900 p-8">
            <h2 class="text-2xl font-black text-blue-500 mb-10 italic">ADMIN WP</h2>
            <nav class="space-y-2"><a href="/admin/wp" class="sidebar-link"><i class="fa fa-dashboard"></i> Dashboard</a></nav>
        </div>
        <main class="flex-grow p-6 md:p-12">
            <div class="max-w-4xl glass p-10 rounded-[3rem] shadow-2xl mx-auto border-t-4 border-blue-600">
                <h2 class="text-3xl font-black mb-10 text-blue-500 uppercase italic">Publish New Movie</h2>
                <form method="POST" class="space-y-6">
                    <input type="text" name="name" required placeholder="Movie Name">
                    <select name="category" required>
                        {{% for c in cats %}}<option value="{{{{ c.name }}}}">{{{{ c.name }}}}</option>{{% endfor %}}
                    </select>
                    <input type="text" name="poster" required placeholder="Poster Image URL">
                    <input type="text" name="badge" placeholder="Badge Info">
                    <div id="btn-box" class="space-y-4"></div>
                    <button type="button" onclick="addL()" class="text-blue-400 font-bold text-xs uppercase underline tracking-widest">+ Add Download Link</button>
                    <button class="bg-blue-600 w-full py-4 rounded-2xl font-black text-white uppercase shadow-xl mt-6">Publish</button>
                </form>
            </div>
        </main>
        <script>
            function addL(){{
                const b = document.getElementById('btn-box');
                const d = document.createElement('div');
                d.className = "flex gap-4 p-4 glass rounded-2xl border border-white/5";
                d.innerHTML = `<input type="text" name="l_name[]" placeholder="Button Label" required><input type="text" name="l_url[]" placeholder="URL" required>`;
                b.appendChild(d);
            }}
            addL();
        </script>
    </body></html>
    """
    return render_template_string(html, cats=cats)

@app.route('/admin/wp/requests', methods=['GET', 'POST'])
def admin_requests():
    if not session.get('admin'): return redirect('/admin/wp/login')
    if request.method == 'POST':
        req_id, status, admin_note = request.form.get('req_id'), request.form.get('status'), request.form.get('admin_note')
        req = requests_col.find_one({"_id": ObjectId(req_id)})
        if req:
            notif_col.insert_one({
                "user_id": req['user_id'],
                "message": f"Your request for '{req['movie_name']}': It has been {status}. Admin Message: {admin_note}",
                "date": datetime.now().strftime("%d %b, %H:%M")
            })
            if status == "Uploaded/Done": requests_col.delete_one({"_id": ObjectId(req_id)})
            else: requests_col.update_one({"_id": ObjectId(req_id)}, {"$set": {"status": status}})
        return redirect('/admin/wp/requests')

    reqs = list(requests_col.find().sort("_id", -1))
    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>User Requests</title></head>
    <body class="flex flex-col md:flex-row min-h-screen">
        <div class="w-full md:w-72 bg-[#080c14] border-r border-slate-900 p-8"><h2 class="text-2xl font-black text-blue-500 mb-10 italic">ADMIN WP</h2><nav class="space-y-2"><a href="/admin/wp" class="sidebar-link"><i class="fa fa-dashboard"></i> Dashboard</a></nav></div>
        <main class="flex-grow p-6 md:p-12">
            <h1 class="text-3xl font-black mb-12 uppercase italic">User Requests Queue</h1>
            {{% for r in reqs %}}
            <div class="glass p-8 rounded-[2.5rem] flex flex-col md:flex-row justify-between items-center gap-8 mb-6 shadow-xl">
                <div class="flex-1">
                    <h3 class="text-2xl font-black text-blue-500 uppercase italic tracking-tighter">{{{{ r.movie_name }}}}</h3>
                    <p class="text-xs text-slate-400 font-bold uppercase tracking-widest">{{{{ r.user_name }}}} | {{{{ r.email }}}}</p>
                    <span class="text-[10px] text-yellow-500 font-bold uppercase">{{{{ r.status }}}} - {{{{ r.date }}}}</span>
                </div>
                <form method="POST" class="flex flex-col md:flex-row gap-2">
                    <input type="hidden" name="req_id" value="{{{{ r._id }}}}">
                    <input type="text" name="admin_note" placeholder="Message to user..." required class="text-xs">
                    <select name="status" class="text-xs"><option>Uploaded/Done</option><option>Rejected</option></select>
                    <button class="bg-blue-600 px-6 py-2 rounded-xl font-bold uppercase text-xs shadow-xl">Update</button>
                </form>
            </div>
            {{% endfor %}}
        </main>
    </body></html>
    """
    return render_template_string(html, reqs=reqs)

@app.route('/admin/wp/settings', methods=['GET', 'POST'])
def admin_settings():
    if not session.get('admin'): return redirect('/admin/wp/login')
    conf = get_config()
    cats = list(categories_col.find())
    
    if request.method == 'POST':
        if 'update_branding' in request.form:
            settings_col.update_one({"type": "config"}, {"$set": {
                "site_name": request.form.get('site_name'), "logo_url": request.form.get('logo_url'),
                "help_text": request.form.get('help_text'), "channel_link": request.form.get('channel_link'),
                "slider_limit": int(request.form.get('slider_limit', 5))
            }})
        elif 'update_profile' in request.form:
            settings_col.update_one({"type": "config"}, {"$set": {
                "admin_user": request.form.get('admin_user'), "admin_pass": request.form.get('admin_pass')
            }})
        elif 'add_cat' in request.form:
            categories_col.insert_one({"name": request.form.get('cat_name')})
        elif 'del_cat' in request.form:
            categories_col.delete_one({"_id": ObjectId(request.form.get('cat_id'))})
        elif 'update_ads' in request.form:
            ads = {k: request.form.get(k) for k in conf['ads'].keys()}
            settings_col.update_one({"type": "config"}, {"$set": {"ads": ads}})
        flash("Configuration Updated!")
        return redirect('/admin/wp/settings')

    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>Settings</title></head>
    <body class="flex flex-col md:flex-row min-h-screen">
        <div class="w-full md:w-72 bg-[#080c14] border-r border-slate-900 p-8"><h2 class="text-2xl font-black text-blue-500 mb-10 italic">ADMIN WP</h2><nav class="space-y-2"><a href="/admin/wp" class="sidebar-link"><i class="fa fa-dashboard"></i> Dashboard</a><a href="/admin/wp/settings" class="sidebar-link active"><i class="fa fa-cog"></i> Settings</a></nav></div>
        <main class="flex-grow p-6 md:p-12 space-y-10">
            <h1 class="text-4xl font-black uppercase italic tracking-tighter">WP Global Configuration</h1>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-10">
                <form method="POST" class="glass p-8 rounded-[3rem] space-y-4 shadow-2xl border-t-4 border-blue-600">
                    <h3 class="text-blue-500 font-black uppercase text-xs">Branding & Social</h3>
                    <input type="text" name="site_name" value="{{{{conf.site_name}}}}" placeholder="Site Name">
                    <input type="text" name="logo_url" value="{{{{conf.logo_url}}}}" placeholder="Logo URL">
                    <textarea name="help_text" rows="3">{{{{conf.help_text}}}}</textarea>
                    <input type="text" name="channel_link" value="{{{{conf.channel_link}}}}" placeholder="Telegram Link">
                    <input type="number" name="slider_limit" value="{{{{conf.slider_limit}}}}" placeholder="Slider Limit">
                    <button name="update_branding" class="bg-blue-600 w-full py-4 rounded-2xl font-bold uppercase">Save Branding</button>
                </form>
                <div class="space-y-10">
                    <div class="glass p-8 rounded-[3rem] shadow-2xl border-t-4 border-green-600">
                        <h3 class="text-green-500 font-black uppercase text-xs mb-4">Genre Manager</h3>
                        <form method="POST" class="flex gap-2"><input type="text" name="cat_name" placeholder="Genre Name" required><button name="add_cat" class="bg-green-600 px-6 rounded-xl font-bold">ADD</button></form>
                        <div class="mt-4 space-y-2">
                            {{% for c in cats %}}<div class="flex justify-between p-3 glass rounded-xl text-sm font-bold">{{{{c.name}}}}<form method="POST" class="inline"><input type="hidden" name="cat_id" value="{{{{c._id}}}}"><button name="del_cat" class="text-red-500"><i class="fa fa-trash"></i></button></form></div>{{% endfor %}}
                        </div>
                    </div>
                </div>
            </div>
            <form method="POST" class="glass p-10 rounded-[3.5rem] shadow-2xl border-t-4 border-yellow-500 space-y-8">
                <h3 class="text-yellow-500 font-black uppercase text-xs italic">Monetization System (WP)</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {{% for k, v in conf.ads.items() %}}<div class="space-y-2"><label class="text-[10px] uppercase font-bold text-slate-500">{{{{k}}}} SLOT</label><textarea name="{{{{k}}}}" rows="4">{{{{v}}}}</textarea></div>{{% endfor %}}
                </div>
                <button name="update_ads" class="bg-yellow-600 w-full py-5 rounded-[2rem] font-black uppercase text-xl shadow-2xl">Update Ad Scripts</button>
            </form>
        </main>
    </body></html>
    """
    return render_template_string(html, conf=conf, cats=cats)

@app.route('/admin/wp/edit/<id>', methods=['GET', 'POST'])
def edit_movie(id):
    if not session.get('admin'): return redirect('/admin/wp/login')
    movie = movies_col.find_one({"_id": ObjectId(id)})
    cats = list(categories_col.find())
    if request.method == 'POST':
        labels, urls = request.form.getlist('l_name[]'), request.form.getlist('l_url[]')
        links = [{"label": labels[i], "url": urls[i]} for i in range(len(labels))]
        movies_col.update_one({"_id": ObjectId(id)}, {"$set": {
            "name": request.form.get('name'), "poster": request.form.get('poster'),
            "badge": request.form.get('badge'), "category": request.form.get('category'), "links": links
        }})
        return redirect('/admin/wp')
    
    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>Edit - {{{{movie.name}}}}</title></head><body class="p-10">
    <div class="max-w-4xl glass p-10 rounded-[3rem] mx-auto shadow-2xl border-t-4 border-blue-600">
        <h2 class="text-2xl font-black mb-8 uppercase italic">Edit Entry (WP)</h2>
        <form method="POST" class="space-y-6">
            <input type="text" name="name" value="{{{{movie.name}}}}" required>
            <input type="text" name="poster" value="{{{{movie.poster}}}}" required>
            <input type="text" name="badge" value="{{{{movie.badge}}}}">
            <select name="category">
                {{% for c in cats %}}<option value="{{{{c.name}}}}" {{% if c.name == movie.category %}}selected{{% endif %}}>{{{{c.name}}}}</option>{{% endfor %}}
            </select>
            <div id="ec" class="space-y-3 pt-6 border-t border-slate-800">
                {{% for l in movie.links %}}<div class="flex gap-3"><input name="l_name[]" value="{{{{l.label}}}}"><input name="l_url[]" value="{{{{l.url}}}}"></div>{{% endfor %}}
            </div>
            <button class="bg-blue-600 w-full py-4 rounded-xl font-bold uppercase shadow-xl mt-6">Update Database</button>
            <a href="/admin/wp" class="block text-center mt-4 text-slate-500 font-bold text-xs uppercase underline">Back to Dashboard</a>
        </form>
    </div>
    </body></html>
    """
    return render_template_string(html, movie=movie, cats=cats)

@app.route('/admin/wp/delete/<id>')
def delete_movie(id):
    if not session.get('admin'): return redirect('/admin/wp/login')
    movies_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin/wp')

@app.errorhandler(404)
def page_not_found(e):
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
