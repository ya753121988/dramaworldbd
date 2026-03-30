import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

# --- Flask App Handler ---
app = Flask(__name__)
app.secret_key = "dramaworld_ultimate_premium_final_key"

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

# --- Database & Config Fix ---
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
            "help_text": "Join our telegram channel for updates and help.",
            "channel_link": "https://t.me/yourchannel",
            "ads": {"popunder": "", "socialbar": "", "native": "", "banner": "", "header": "", "footer": "", "middle": ""}
        }
        settings_col.insert_one(conf)
    
    # Defaults for all keys to prevent 500 Error
    keys = ["site_name", "logo_url", "help_text", "channel_link", "slider_limit", "ads", "admin_user", "admin_pass"]
    for k in keys:
        if k not in conf:
            if k == "ads": conf[k] = {"popunder": "", "socialbar": "", "native": "", "banner": "", "header": "", "footer": "", "middle": ""}
            elif k == "slider_limit": conf[k] = 5
            else: conf[k] = ""
    return conf

# --- UI Styles (Ultra Premium) ---
CSS = """
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    body { font-family: 'Outfit', sans-serif; background-color: #050811; color: #e2e8f0; margin:0; overflow-x: hidden; }
    .glass { background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.05); }
    .movie-card { transition: 0.4s; border: 1px solid rgba(255,255,255,0.05); border-radius: 1.5rem; overflow: hidden; background: #0f172a; }
    .movie-card:hover { transform: translateY(-10px); border-color: #3b82f6; box-shadow: 0 20px 40px -15px rgba(59, 130, 246, 0.5); }
    .slider-box { position: relative; width: 100%; height: 230px; overflow: hidden; border-radius: 30px; }
    @media(min-width: 768px) { .slider-box { height: 480px; } }
    .slide-img { display: none; width: 100%; height: 100%; object-fit: cover; animation: fade 1.5s ease; }
    .slide-active { display: block; }
    @keyframes fade { from { opacity: 0; } to { opacity: 1; } }
    input, select, textarea { background: #0f172a !important; color: white !important; border: 1px solid #1e293b !important; border-radius: 12px; padding: 12px; outline: none; width: 100%; }
    .sidebar-link { display: flex; align-items: center; gap: 10px; padding: 12px 20px; border-radius: 12px; transition: 0.3s; color: #94a3b8; font-weight: 600; }
    .sidebar-link:hover, .sidebar-link.active { background: #3b82f6; color: white; box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.4); }
    .footer-btn { display: flex; flex-direction: column; align-items: center; justify-content: center; color: #94a3b8; font-size: 11px; font-weight: bold; transition: 0.3s; }
    .footer-btn:hover { color: #3b82f6; }
</style>
"""

# --- COMMON USER COMPONENTS ---
def get_user_nav(conf):
    user_sec = f'<a href="/login" class="bg-blue-600 px-5 py-2 rounded-full text-xs font-bold text-white shadow-lg">LOGIN</a>'
    if 'user_id' in session:
        user_sec = f'<a href="/profile" class="text-blue-400 font-bold flex items-center gap-2"><i class="fa fa-user-circle text-xl"></i> <span class="hidden md:inline">{session["user_name"]}</span></a>'
    
    return f'''
    <nav class="glass sticky top-0 z-50 px-4 md:px-10 py-4 flex justify-between items-center border-b border-white/5">
        <a href="/" class="flex items-center gap-2">
            {"<img src='"+conf['logo_url']+"' class='h-8 md:h-10'>" if conf['logo_url'] else ""}
            <span class="text-xl md:text-2xl font-black text-blue-500 italic uppercase tracking-tighter">{conf['site_name']}</span>
        </a>
        <div class="flex items-center gap-4">
            <form action="/" method="GET" class="hidden md:flex bg-slate-900 rounded-full px-4 py-1 border border-slate-800">
                <input type="text" name="search" placeholder="Search..." class="bg-transparent border-none outline-none text-sm w-48 p-1">
                <button type="submit"><i class="fa fa-search text-slate-500"></i></button>
            </form>
            {user_sec}
        </div>
    </nav>
    '''

USER_FOOTER = '''
<div class="h-28 md:h-32"></div>
<div class="fixed bottom-4 left-1/2 -translate-x-1/2 w-[92%] md:w-[450px] glass h-16 rounded-full flex justify-around items-center px-6 z-50 shadow-2xl border border-blue-500/20">
    <a href="/" class="footer-btn"><i class="fa fa-home text-xl"></i><span>HOME 🏠</span></a>
    <a href="/help" class="footer-btn"><i class="fa fa-question-circle text-xl"></i><span>HELP 🆘</span></a>
    <a href="/request" class="footer-btn"><i class="fa fa-paper-plane text-xl"></i><span>REQUEST 🚀</span></a>
    {% if session.user_id %}
    <a href="/profile" class="footer-btn"><i class="fa fa-envelope text-xl"></i><span>MAIL 📬</span></a>
    {% endif %}
</div>
'''

# --- USER ROUTES ---

@app.route('/')
def index():
    conf = get_config()
    search = request.args.get('search')
    if search:
        movies = list(movies_col.find({"name": {"$regex": search, "$options": "i"}}))
        grouped_movies = {"SEARCH RESULTS": movies}
        slider_movies = []
    else:
        all_cats = list(categories_col.find())
        grouped_movies = {cat['name']: list(movies_col.find({"category": cat['name']}).sort("_id", -1)) for cat in all_cats}
        movies = list(movies_col.find().sort("_id", -1))
        slider_movies = movies[:int(conf['slider_limit'])]
    
    return render_template_string(f"""
    <!DOCTYPE html><html><head><title>{{{{conf.site_name}}}}</title>{CSS}</head>
    <body>
        {get_user_nav(conf)}
        <div class="container mx-auto px-4 py-6">
            <div class="mb-4 text-center overflow-hidden">{{{{ conf.ads.header | safe }}}}</div>
            
            {% if slider_movies and not request.args.get('search') %}
            <div class="slider-box mb-12 shadow-2xl">
                {% for sm in slider_movies %}<a href="/movie/{{{{ sm._id }}}}"><img src="{{{{ sm.poster }}}}" class="slide-img"></a>{% endfor %}
            </div>
            {% endif %}

            <div class="mb-8 text-center overflow-hidden">{{{{ conf.ads.middle | safe }}}}</div>

            {% for cat_name, movies in grouped_movies.items() %}{% if movies %}
            <div class="mb-12">
                <h2 class="text-xl font-bold mb-6 flex items-center gap-3"><span class="w-2 h-8 bg-blue-600 rounded-full shadow-[0_0_15px_#3b82f6]"></span> {{{{ cat_name }}}}</h2>
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
                    {% for m in movies %}
                    <div class="movie-card relative cursor-pointer" onclick="location.href='/movie/{{{{ m._id }}}}'">
                        <img src="{{{{ m.poster }}}}" class="w-full h-64 md:h-80 object-cover">
                        <div class="absolute top-3 left-3 bg-blue-600 text-[10px] font-bold px-3 py-1 rounded-full uppercase border border-white/20">{{{{ m.badge }}}}</div>
                        <div class="p-4 bg-slate-900/80 backdrop-blur-md font-bold text-sm truncate">{{{{ m.name }}}}</div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}{% endfor %}

            <div class="mt-10 text-center overflow-hidden">{{{{ conf.ads.footer | safe }}}}</div>
        </div>
        {USER_FOOTER}
        <script>
            let sIdx = 0; const slides = document.querySelectorAll('.slide-img');
            if(slides.length > 0){{ slides[0].classList.add('slide-active'); setInterval(()=>{{ slides[sIdx].classList.remove('slide-active'); sIdx = (sIdx + 1) % slides.length; slides[sIdx].classList.add('slide-active'); }}, 5000); }}
        </script>
    </body></html>
    """, conf=conf, slider_movies=slider_movies, grouped_movies=grouped_movies)

@app.route('/movie/<id>')
def movie_details(id):
    conf = get_config()
    movie = movies_col.find_one({"_id": ObjectId(id)})
    if not movie: return redirect('/')
    return render_template_string(f"""
    <!DOCTYPE html><html><head><title>{{{{movie.name}}}} - {{{{conf.site_name}}}}</title>{CSS}</head>
    <body>
        {get_user_nav(conf)}
        <div class="container mx-auto px-4 py-10">
            <div class="flex flex-col md:flex-row gap-10">
                <div class="w-full md:w-80"><img src="{{{{ movie.poster }}}}" class="w-full rounded-[2.5rem] shadow-2xl border-4 border-slate-900"></div>
                <div class="flex-1">
                    <span class="bg-blue-600 px-4 py-1 rounded-full text-xs font-bold uppercase shadow-lg">{{{{ movie.badge }}}}</span>
                    <h1 class="text-4xl font-black mt-4 mb-2 italic tracking-tight">{{{{ movie.name }}}}</h1>
                    <p class="text-blue-500 font-bold mb-8 uppercase text-sm tracking-widest">{{{{ movie.category }}}}</p>
                    <div class="glass p-8 rounded-[2rem] border border-blue-500/20 shadow-2xl">
                        <h3 class="text-xl font-bold mb-8 flex items-center gap-3 text-white border-b border-white/5 pb-4"><i class="fa fa-play-circle text-blue-500 text-3xl"></i> WATCH OR DOWNLOAD LINKS</h3>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            {% for link in movie.links %}
                            <a href="{{{{ link.url }}}}" target="_blank" class="bg-blue-600 hover:bg-blue-700 text-white text-center py-4 rounded-2xl font-bold transition transform hover:scale-105 shadow-xl border border-white/10 uppercase">
                                 {{{{ link.label }}}}
                            </a>
                            {% endfor %}
                        </div>
                    </div>
                    <div class="mt-8 text-center overflow-hidden">{{{{ conf.ads.native | safe }}}}</div>
                </div>
            </div>
        </div>
        {USER_FOOTER}
    </body></html>
    """, movie=movie, conf=conf)

@app.route('/help')
def help_page():
    conf = get_config()
    return render_template_string(f"""
    <!DOCTYPE html><html><head><title>Help Center</title>{CSS}</head>
    <body>
        {get_user_nav(conf)}
        <div class="container mx-auto px-4 py-10 text-center">
            <div class="glass p-10 md:p-20 rounded-[3rem] max-w-3xl mx-auto shadow-2xl border-t-4 border-blue-600">
                {% if conf.logo_url %}<img src="{{{{conf.logo_url}}}}" class="h-24 mx-auto mb-8 drop-shadow-2xl">{% endif %}
                <h1 class="text-4xl font-black mb-6 uppercase italic text-blue-500">Need Help?</h1>
                <p class="text-slate-400 text-lg mb-10 leading-relaxed">{{{{conf.help_text}}}}</p>
                <a href="{{{{conf.channel_link}}}}" target="_blank" class="bg-blue-600 hover:bg-blue-700 text-white px-10 py-5 rounded-2xl font-bold text-lg shadow-2xl inline-flex items-center gap-3 transition">
                    <i class="fa fa-paper-plane"></i> JOIN TELEGRAM CHANNEL
                </a>
            </div>
        </div>
        {USER_FOOTER}
    </body></html>
    """, conf=conf)

# --- AUTH SYSTEM ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name, user, pw = request.form.get('name'), request.form.get('user'), request.form.get('pass')
        if users_col.find_one({"user": user}): flash("Username already exists!")
        else:
            uid = "DW" + str(ObjectId())[-6:].upper()
            users_col.insert_one({"uid": uid, "name": name, "user": user, "pass": pw})
            flash("Registered Successfully! Please Login.")
            return redirect('/login')
    return render_template_string(f"""
    <!DOCTYPE html><html><head><title>Register</title>{CSS}</head>
    <body class="flex items-center justify-center min-h-screen p-4">
        <form method="POST" class="glass p-10 rounded-[2.5rem] w-full max-w-md space-y-6 shadow-2xl border-t-4 border-blue-600">
            <h2 class="text-3xl font-black text-center text-blue-500 uppercase italic">Sign Up</h2>
            <input type="text" name="name" placeholder="Full Name" required>
            <input type="text" name="user" placeholder="Username" required>
            <input type="password" name="pass" placeholder="Password" required>
            <button class="w-full bg-blue-600 py-4 rounded-2xl font-bold text-white shadow-xl">CREATE ACCOUNT</button>
            <p class="text-center text-sm">Already have an account? <a href="/login" class="text-blue-500 font-bold">Login</a></p>
        </form>
    </body></html>
    """)

@app.route('/login', methods=['GET', 'POST'])
def login():
    conf = get_config()
    if request.method == 'POST':
        user, pw = request.form.get('user'), request.form.get('pass')
        if user == conf['admin_user'] and pw == conf['admin_pass']:
            session['admin'] = True; return redirect('/admin')
        u = users_col.find_one({"user": user, "pass": pw})
        if u:
            session['user_id'] = str(u['_id']); session['user_name'] = u['name']
            return redirect('/')
        flash("Invalid Credentials!")
    return render_template_string(f"""
    <!DOCTYPE html><html><head><title>Login</title>{CSS}</head>
    <body class="flex items-center justify-center min-h-screen p-4">
        <form method="POST" class="glass p-10 rounded-[2.5rem] w-full max-w-md space-y-6 shadow-2xl border-t-4 border-blue-600">
            <h2 class="text-3xl font-black text-center text-blue-500 uppercase italic">Login</h2>
            {% with messages = get_flashed_messages() %}{% if messages %}<p class="text-red-500 text-xs text-center font-bold">{{{{messages[0]}}}}</p>{% endif %}{% endwith %}
            <input type="text" name="user" placeholder="Username" required>
            <input type="password" name="pass" placeholder="Password" required>
            <button class="w-full bg-blue-600 py-4 rounded-2xl font-bold text-white shadow-xl">LOG IN</button>
            <p class="text-center text-sm text-slate-400">New user? <a href="/register" class="text-blue-500 font-bold">Sign Up</a></p>
        </form>
    </body></html>
    """)

@app.route('/logout')
def logout():
    session.clear(); return redirect('/')

# --- REQUEST & PROFILE SYSTEM ---

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
        flash("Request submitted successfully!"); return redirect('/profile')
    return render_template_string(f"""
    <!DOCTYPE html><html><head><title>Request Movie</title>{CSS}</head>
    <body>
        {get_user_nav(conf)}
        <div class="container mx-auto px-4 py-10">
            <form method="POST" class="glass p-10 rounded-[3rem] max-w-xl mx-auto space-y-6 border-t-4 border-blue-600 shadow-2xl">
                <h2 class="text-3xl font-black text-blue-500 uppercase italic">Request Movie 🚀</h2>
                <div class="space-y-1"><label class="text-xs font-bold text-slate-500 uppercase">Movie Name</label><input type="text" name="movie_name" required></div>
                <div class="space-y-1"><label class="text-xs font-bold text-slate-500 uppercase">Your Name</label><input type="text" value="{{{{session.user_name}}}}" readonly></div>
                <div class="space-y-1"><label class="text-xs font-bold text-slate-500 uppercase">Your Email</label><input type="email" name="email" required></div>
                <button class="w-full bg-blue-600 py-4 rounded-2xl font-bold text-white shadow-xl">SEND REQUEST</button>
            </form>
        </div>
        {USER_FOOTER}
    </body></html>
    """, conf=conf)

@app.route('/profile')
def profile():
    if 'user_id' not in session: return redirect('/login')
    conf = get_config()
    u = users_col.find_one({"_id": ObjectId(session['user_id'])})
    notifs = list(notif_col.find({"user_id": session['user_id']}).sort("_id", -1))
    return render_template_string(f"""
    <!DOCTYPE html><html><head><title>Profile</title>{CSS}</head>
    <body>
        {get_user_nav(conf)}
        <div class="container mx-auto px-4 py-10">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-10">
                <div class="md:col-span-1 glass p-10 rounded-[3rem] text-center border-b-4 border-blue-600 h-fit">
                    <div class="w-24 h-24 bg-blue-600 rounded-full mx-auto flex items-center justify-center text-4xl font-black mb-4">{{{{ u.name[0] }}}}</div>
                    <h2 class="text-2xl font-black">{{{{ u.name }}}}</h2>
                    <p class="text-blue-500 font-bold text-xs mt-2 uppercase tracking-widest">USER ID: {{{{ u.uid }}}}</p>
                    <a href="/logout" class="block mt-10 text-red-500 font-bold hover:underline">LOGOUT</a>
                </div>
                <div class="md:col-span-2 glass p-8 rounded-[2.5rem] border border-white/5">
                    <h3 class="text-xl font-black mb-6 text-blue-500 flex items-center gap-3 uppercase"><i class="fa fa-envelope"></i> Notifications (MailBox)</h3>
                    <div class="space-y-4">
                        {% if not notifs %}<p class="text-slate-500 italic text-sm">No new notifications.</p>{% endif %}
                        {% for n in notifs %}
                        <div class="p-5 bg-slate-900 rounded-2xl border-l-4 border-blue-600">
                            <p class="text-sm font-semibold mb-2 leading-relaxed text-slate-200">{{{{ n.message }}}}</p>
                            <p class="text-[10px] text-slate-500 font-bold uppercase">{{{{ n.date }}}}</p>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
        {USER_FOOTER}
    </body></html>
    """, u=u, notifs=notifs, conf=conf)

# --- ADMIN PANEL ---

@app.route('/admin')
def admin_dash():
    if not session.get('admin'): return redirect('/login')
    search = request.args.get('search', '')
    query = {"name": {"$regex": search, "$options": "i"}} if search else {}
    movies = list(movies_col.find(query).sort("_id", -1))
    
    return render_template_string(f"""
    <!DOCTYPE html><html><head><title>Admin Dash</title>{CSS}</head>
    <body class="flex flex-col md:flex-row min-h-screen">
        <div class="w-full md:w-72 bg-[#080c14] border-r border-slate-900 p-8 flex flex-col shadow-2xl">
            <h2 class="text-2xl font-black text-blue-500 mb-10 italic">CONTROL PANEL</h2>
            <nav class="space-y-2 flex-grow">
                <a href="/admin" class="sidebar-link active"><i class="fa fa-dashboard"></i> Dashboard</a>
                <a href="/admin/requests" class="sidebar-link"><i class="fa fa-paper-plane"></i> Requests</a>
                <a href="/admin/add" class="sidebar-link"><i class="fa fa-plus-circle"></i> Add Movie</a>
                <a href="/admin/settings" class="sidebar-link"><i class="fa fa-cog"></i> Settings & Ads</a>
                <a href="/logout" class="sidebar-link text-red-500 mt-10">Logout</a>
            </nav>
        </div>
        <main class="flex-grow p-6 md:p-12">
            <div class="flex flex-col md:flex-row justify-between items-center mb-10 gap-4">
                <h1 class="text-3xl font-black uppercase">Manage Movies</h1>
                <form class="flex bg-slate-900 rounded-2xl px-4 py-2 border border-slate-800 w-full md:w-80">
                    <input type="text" name="search" placeholder="Search movies..." class="bg-transparent border-none text-sm p-1" value="{search}">
                    <button type="submit"><i class="fa fa-search text-slate-500"></i></button>
                </form>
            </div>
            <div class="glass rounded-[2rem] overflow-hidden">
                <table class="w-full text-left">
                    <thead class="bg-slate-900 text-slate-500 text-xs uppercase font-bold tracking-widest"><tr class="border-b border-white/5"><th class="p-6">Movie</th><th class="p-6">Category</th><th class="p-6 text-center">Action</th></tr></thead>
                    <tbody class="divide-y divide-slate-800">
                        {{% for m in movies %}}
                        <tr class="hover:bg-slate-800/50 transition">
                            <td class="p-6 flex items-center gap-4">
                                <img src="{{{{ m.poster }}}}" class="w-10 h-14 rounded-lg object-cover">
                                <span class="font-bold text-sm">{{{{ m.name }}}}</span>
                            </td>
                            <td class="p-6 text-xs text-blue-400 font-bold uppercase">{{{{ m.category }}}}</td>
                            <td class="p-6">
                                <div class="flex justify-center gap-4">
                                    <a href="/admin/edit/{{{{ m._id }}}}" class="text-blue-500 text-xl"><i class="fa fa-edit"></i></a>
                                    <a href="/admin/delete/{{{{ m._id }}}}" class="text-red-500 text-xl" onclick="return confirm('Delete?')"><i class="fa fa-trash"></i></a>
                                </div>
                            </td>
                        </tr>
                        {{% endfor %}}
                    </tbody>
                </table>
            </div>
        </main>
    </body></html>
    """, movies=movies)

@app.route('/admin/requests', methods=['GET', 'POST'])
def admin_requests():
    if not session.get('admin'): return redirect('/login')
    if request.method == 'POST':
        rid, status, text = request.form.get('rid'), request.form.get('status'), request.form.get('admin_text')
        req = requests_col.find_one({"_id": ObjectId(rid)})
        if req:
            notif_col.insert_one({
                "user_id": req['user_id'],
                "message": f"Update on '{req['movie_name']}': {status}. Admin Note: {text}",
                "date": datetime.now().strftime("%d %b, %H:%M")
            })
            if status == "Uploaded/Done": requests_col.delete_one({"_id": ObjectId(rid)})
            else: requests_col.update_one({"_id": ObjectId(rid)}, {"$set": {"status": status}})
        return redirect('/admin/requests')

    reqs = list(requests_col.find().sort("_id", -1))
    return render_template_string(f"""
    <!DOCTYPE html><html><head><title>Requests</title>{CSS}</head>
    <body class="flex flex-col md:flex-row min-h-screen">
        <div class="w-full md:w-72 bg-[#080c14] border-r border-slate-900 p-8 flex flex-col shadow-2xl">
            <h2 class="text-2xl font-black text-blue-500 mb-10 italic">ADMIN</h2>
            <nav class="space-y-2 flex-grow">
                <a href="/admin" class="sidebar-link"><i class="fa fa-dashboard"></i> Dashboard</a>
                <a href="/admin/requests" class="sidebar-link active"><i class="fa fa-paper-plane"></i> Requests</a>
                <a href="/admin/add" class="sidebar-link"><i class="fa fa-plus-circle"></i> Add Movie</a>
                <a href="/admin/settings" class="sidebar-link"><i class="fa fa-cog"></i> Settings & Ads</a>
                <a href="/logout" class="sidebar-link text-red-500 mt-10">Logout</a>
            </nav>
        </div>
        <main class="flex-grow p-6 md:p-12 space-y-6">
            <h1 class="text-3xl font-black">User Requests</h1>
            {{% for r in reqs %}}
            <div class="glass p-8 rounded-[2.5rem] flex flex-col md:flex-row justify-between items-center gap-6">
                <div class="flex-1">
                    <h3 class="text-xl font-bold text-blue-500 uppercase">{{{{ r.movie_name }}}}</h3>
                    <p class="text-xs text-slate-400 font-bold mt-1">Requested by: {{{{ r.user_name }}}} | {{{{ r.date }}}}</p>
                    <span class="inline-block mt-3 px-3 py-1 bg-yellow-500/10 text-yellow-500 text-[10px] font-bold rounded-full uppercase">{{{{ r.status }}}}</span>
                </div>
                <form method="POST" class="flex flex-col md:flex-row gap-2 w-full md:w-auto">
                    <input type="hidden" name="rid" value="{{{{ r._id }}}}">
                    <input type="text" name="admin_text" placeholder="Admin Reply..." required class="text-xs">
                    <select name="status" class="text-xs"><option>Uploaded/Done</option><option>Rejected</option></select>
                    <button class="bg-blue-600 px-6 py-3 rounded-xl font-bold text-xs uppercase">Reply</button>
                </form>
            </div>
            {{% endfor %}}
        </main>
    </body></html>
    """, reqs=reqs)

@app.route('/admin/add', methods=['GET', 'POST'])
def add_movie():
    if not session.get('admin'): return redirect('/login')
    cats = list(categories_col.find())
    if request.method == 'POST':
        labels, urls = request.form.getlist('l_name[]'), request.form.getlist('l_url[]')
        links = [{"label": labels[i], "url": urls[i]} for i in range(len(labels))]
        movies_col.insert_one({
            "name": request.form.get('name'), "poster": request.form.get('poster'),
            "badge": request.form.get('badge'), "category": request.form.get('category'), "links": links
        })
        return redirect('/admin')
    
    return render_template_string(f"""
    <!DOCTYPE html><html><head><title>Add Movie</title>{CSS}</head>
    <body class="flex flex-col md:flex-row min-h-screen">
        <div class="w-full md:w-72 bg-[#080c14] border-r border-slate-900 p-8 shadow-2xl">
            <h2 class="text-2xl font-black text-blue-500 mb-10 italic text-center">ADMIN</h2>
            <nav class="space-y-2">
                <a href="/admin" class="sidebar-link"><i class="fa fa-dashboard"></i> Dashboard</a>
                <a href="/admin/requests" class="sidebar-link"><i class="fa fa-paper-plane"></i> Requests</a>
                <a href="/admin/add" class="sidebar-link active"><i class="fa fa-plus-circle"></i> Add Movie</a>
                <a href="/admin/settings" class="sidebar-link"><i class="fa fa-cog"></i> Settings & Ads</a>
                <a href="/logout" class="sidebar-link text-red-500 mt-10">Logout</a>
            </nav>
        </div>
        <main class="flex-grow p-6 md:p-12">
            <form method="POST" class="glass p-10 rounded-[3rem] max-w-4xl mx-auto space-y-6 shadow-2xl">
                <h2 class="text-2xl font-black text-blue-500 uppercase">Publish Movie</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <input type="text" name="name" placeholder="Movie Name" required>
                    <select name="category" required>
                        {{% for c in cats %}}<option value="{{{{ c.name }}}}">{{{{ c.name }}}}</option>{{% endfor %}}
                    </select>
                </div>
                <input type="text" name="poster" placeholder="Poster Image URL" required>
                <input type="text" name="badge" placeholder="Badge (e.g. 1080p | Dual Audio)">
                <div id="btn-container" class="space-y-3 pt-6 border-t border-slate-800">
                    <label class="block text-xs font-bold text-blue-500 uppercase tracking-widest">Download Link Management</label>
                </div>
                <button type="button" onclick="addL()" class="text-blue-400 font-bold text-xs uppercase hover:underline">+ Add Link Button</button>
                <button class="w-full bg-blue-600 py-4 rounded-2xl font-bold shadow-xl uppercase">Publish Now</button>
            </form>
        </main>
        <script>function addL(){{ const d = document.createElement('div'); d.className = "flex gap-4"; d.innerHTML = `<input type="text" name="l_name[]" placeholder="Label" required><input type="text" name="l_url[]" placeholder="URL" required>`; document.getElementById('btn-container').appendChild(d); }} addL();</script>
    </body></html>
    """, cats=cats)

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not session.get('admin'): return redirect('/login')
    conf = get_config(); cats = list(categories_col.find())
    if request.method == 'POST':
        if 'update_branding' in request.form:
            settings_col.update_one({"type": "config"}, {"$set": {
                "site_name": request.form.get('site_name'), "logo_url": request.form.get('logo_url'),
                "help_text": request.form.get('help_text'), "channel_link": request.form.get('channel_link'),
                "slider_limit": int(request.form.get('slider_limit', 5))
            }})
        elif 'update_profile' in request.form:
            settings_col.update_one({"type": "config"}, {"$set": {"admin_user": request.form.get('admin_user'), "admin_pass": request.form.get('admin_pass')}})
        elif 'add_cat' in request.form: categories_col.insert_one({"name": request.form.get('cat_name')})
        elif 'del_cat' in request.form: categories_col.delete_one({"_id": ObjectId(request.form.get('cat_id'))})
        elif 'update_ads' in request.form:
            ads = {k: request.form.get(k) for k in conf['ads'].keys()}
            settings_col.update_one({"type": "config"}, {"$set": {"ads": ads}})
        return redirect('/admin/settings')

    return render_template_string(f"""
    <!DOCTYPE html><html><head><title>Admin Settings</title>{CSS}</head>
    <body class="flex flex-col md:flex-row min-h-screen">
        <div class="w-full md:w-72 bg-[#080c14] border-r border-slate-900 p-8 flex flex-col shadow-2xl">
            <h2 class="text-2xl font-black text-blue-500 mb-10 italic">SETTINGS</h2>
            <nav class="space-y-2">
                <a href="/admin" class="sidebar-link"><i class="fa fa-dashboard"></i> Dashboard</a>
                <a href="/admin/requests" class="sidebar-link"><i class="fa fa-paper-plane"></i> Requests</a>
                <a href="/admin/add" class="sidebar-link"><i class="fa fa-plus-circle"></i> Add Movie</a>
                <a href="/admin/settings" class="sidebar-link active"><i class="fa fa-cog"></i> Settings & Ads</a>
                <a href="/logout" class="sidebar-link text-red-500 mt-10">Logout</a>
            </nav>
        </div>
        <main class="flex-grow p-6 md:p-12 space-y-10">
            <h1 class="text-3xl font-black uppercase tracking-tighter">System Configuration</h1>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-10">
                <form method="POST" class="glass p-8 rounded-[2.5rem] space-y-4 shadow-2xl">
                    <h3 class="text-blue-500 font-bold uppercase text-xs italic border-b border-white/5 pb-3">Site Branding & Identity</h3>
                    <input type="text" name="site_name" value="{{{{conf.site_name}}}}" placeholder="Site Name">
                    <input type="text" name="logo_url" value="{{{{conf.logo_url}}}}" placeholder="Logo Image URL">
                    <textarea name="help_text" rows="3" placeholder="Help Text">{{{{conf.help_text}}}}</textarea>
                    <input type="text" name="channel_link" value="{{{{conf.channel_link}}}}" placeholder="Channel/Social Link">
                    <input type="number" name="slider_limit" value="{{{{conf.slider_limit}}}}" placeholder="Slider Limit">
                    <button name="update_branding" class="w-full bg-blue-600 py-4 rounded-xl font-bold uppercase">Save Branding</button>
                </form>
                <div class="space-y-10">
                    <form method="POST" class="glass p-8 rounded-[2.5rem] space-y-4 shadow-2xl">
                        <h3 class="text-green-500 font-bold uppercase text-xs italic border-b border-white/5 pb-3">Category Manager</h3>
                        <div class="flex gap-2"><input type="text" name="cat_name" placeholder="New Cat Name"><button name="add_cat" class="bg-green-600 px-6 rounded-xl font-bold uppercase text-xs">ADD</button></div>
                        <div class="max-h-48 overflow-y-auto space-y-2 pt-2">
                            {{% for c in cats %}}<div class="flex justify-between items-center bg-slate-900 p-3 rounded-xl border border-slate-800"><span>{{{{c.name}}}}</span><form method="POST" class="inline"><input type="hidden" name="cat_id" value="{{{{c._id}}}}"><button name="del_cat" class="text-red-500" onclick="return confirm('Delete?')"><i class="fa fa-trash"></i></button></form></div>{{% endfor %}}
                        </div>
                    </form>
                    <form method="POST" class="glass p-8 rounded-[2.5rem] space-y-4 shadow-2xl">
                        <h3 class="text-red-500 font-bold uppercase text-xs italic border-b border-white/5 pb-3">Admin Access Security</h3>
                        <input type="text" name="admin_user" value="{{{{conf.admin_user}}}}">
                        <input type="text" name="admin_pass" value="{{{{conf.admin_pass}}}}">
                        <button name="update_profile" class="w-full bg-red-600 py-4 rounded-xl font-bold uppercase">Update Security</button>
                    </form>
                </div>
            </div>
            <form method="POST" class="glass p-8 rounded-[2.5rem] space-y-6 shadow-2xl border-t-4 border-yellow-500">
                <h3 class="text-yellow-500 font-bold uppercase text-xs italic border-b border-white/5 pb-3">Monetization & Ad Management (7 SLOTS)</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {{% for k, v in conf.ads.items() %}}
                    <div class="space-y-1"><label class="text-[10px] uppercase font-bold text-slate-500 tracking-widest">{{{{k}}}} Code</label><textarea name="{{{{k}}}}" rows="3">{{{{v}}}}</textarea></div>
                    {{% endfor %}}
                </div>
                <button name="update_ads" class="bg-blue-600 px-12 py-4 rounded-xl font-bold uppercase shadow-2xl">UPDATE SYSTEM ADS</button>
            </form>
        </main>
    </body></html>
    """, conf=conf, cats=cats)

@app.route('/admin/edit/<id>', methods=['GET', 'POST'])
def edit_movie(id):
    if not session.get('admin'): return redirect('/login')
    movie = movies_col.find_one({"_id": ObjectId(id)})
    cats = list(categories_col.find())
    if request.method == 'POST':
        labels, urls = request.form.getlist('l_name[]'), request.form.getlist('l_url[]')
        links = [{"label": labels[i], "url": urls[i]} for i in range(len(labels))]
        movies_col.update_one({"_id": ObjectId(id)}, {"$set": {
            "name": request.form.get('name'), "poster": request.form.get('poster'),
            "badge": request.form.get('badge'), "category": request.form.get('category'), "links": links
        }})
        return redirect('/admin')
    return render_template_string(f"<!DOCTYPE html><html><head><title>Edit Movie</title>{CSS}</head><body class='p-10'>{get_user_nav(get_config())}<form method='POST' class='glass p-10 max-w-2xl mx-auto space-y-4 rounded-3xl'><h2 class='text-2xl font-black text-blue-500'>EDIT: {{{{movie.name}}}}</h2><input type='text' name='name' value='{{{{movie.name}}}}'><input type='text' name='poster' value='{{{{movie.poster}}}}'><select name='category'>{{% for c in cats %}}<option {{% if c.name == movie.category %}}selected{{% endif %}}>{{{{c.name}}}}</option>{{% endfor %}}</select><div id='ec' class='space-y-2'>{{% for l in movie.links %}}<div class='flex gap-2'><input name='l_name[]' value='{{{{l.label}}}}'><input name='l_url[]' value='{{{{l.url}}}}'></div>{{% endfor %}}</div><button class='bg-blue-600 p-4 rounded-xl w-full font-bold uppercase'>Save Edit</button></form></body></html>", movie=movie, cats=cats)

@app.route('/admin/delete/<id>')
def delete_movie(id):
    if not session.get('admin'): return redirect('/login')
    movies_col.delete_one({"_id": ObjectId(id)}); return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
