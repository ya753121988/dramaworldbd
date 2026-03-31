import os
import base64
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

# --- Flask Project Handler ---
app = Flask(__name__)
app.secret_key = "dramaworld_ultra_premium_ultimate_v15"

# --- MongoDB Connection ---
# কানেকশন হ্যাং হওয়া রোধ করতে timeout যোগ করা হয়েছে
MONGO_URI = "mongodb+srv://akash:arafat@cluster0.dpg7qid.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
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
            "admin_user": "", 
            "admin_pass": "", 
            "slider_limit": 5,
            "slider_height_desktop": "480px",
            "slider_height_mobile": "230px",
            "home_poster_height": "320px", 
            "help_text": "Welcome to DramaWorld BD. Join our telegram channel for more updates and direct help.",
            "channel_link": "https://t.me/yourchannel",
            "ads": {
                "header": "", "middle": "", "footer": "", 
                "native": "", "popunder": "", "socialbar": "", "banner": ""
            }
        }
        settings_col.insert_one(conf)
    
    required_keys = ["site_name", "logo_url", "help_text", "channel_link", "slider_limit", "ads", "admin_user", "admin_pass", "home_poster_height", "slider_height_desktop", "slider_height_mobile"]
    for key in required_keys:
        if key not in conf:
            if key == "ads":
                conf["ads"] = {"header": "", "middle": "", "footer": "", "native": "", "popunder": "", "socialbar": "", "banner": ""}
            elif key == "slider_limit": conf[key] = 5
            elif key == "home_poster_height": conf[key] = "320px"
            elif key == "slider_height_desktop": conf[key] = "480px"
            elif key == "slider_height_mobile": conf[key] = "230px"
            elif key == "admin_user" or key == "admin_pass": conf[key] = ""
            else: conf[key] = "Not Set"
    return conf

# --- Helper Function for Image Processing ---
def process_media(req, file_key, url_key):
    file = req.files.get(file_key)
    if file and file.filename != '':
        encoded_string = base64.b64encode(file.read()).decode('utf-8')
        return f"data:{file.content_type};base64,{encoded_string}"
    return req.form.get(url_key)

# --- Global CSS & Responsive Meta ---
CSS = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;900&display=swap');
    body { font-family: 'Outfit', sans-serif; background-color: #02040a; color: #e2e8f0; margin:0; overflow-x: hidden; scroll-behavior: smooth; }
    .glass { background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.05); }
    .movie-card { transition: 0.4s; border: 1px solid rgba(255,255,255,0.05); border-radius: 1.5rem; overflow: hidden; background: #0f172a; position: relative; cursor: pointer; }
    .movie-card:hover { transform: translateY(-10px); border-color: #3b82f6; box-shadow: 0 20px 40px -15px rgba(59, 130, 246, 0.5); }
    
    .full-poster { width: 100%; height: auto; object-fit: contain; border-radius: 2rem; }
    .card-thumb { width: 100%; object-fit: cover; transition: opacity 0.5s; }
    
    #global-loader { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(2, 4, 10, 0.8); z-index: 9999; justify-content: center; align-items: center; backdrop-filter: blur(5px); }
    .spinner { width: 50px; height: 50px; border: 5px solid #1e293b; border-top: 5px solid #3b82f6; border-radius: 50%; animation: spin 1s linear infinite; }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

    .slider-box { position: relative; width: 100%; overflow: hidden; border-radius: 30px; border: 1px solid rgba(59, 130, 246, 0.2); }
    .slide-img { display: none; width: 100%; height: 100%; object-fit: cover; animation: fade 1.5s ease; }
    .slide-active { display: block; }
    @keyframes fade { from { opacity: 0; } to { opacity: 1; } }
    
    input, select, textarea { background: #0f172a !important; color: white !important; border: 1px solid #1e293b !important; border-radius: 12px; padding: 12px; outline: none; width: 100%; transition: 0.3s; }
    input:focus { border-color: #3b82f6 !important; box-shadow: 0 0 10px rgba(59, 130, 246, 0.3); }
    
    .progress-container { display: none; width: 100%; background: #0f172a; border-radius: 10px; margin-top: 10px; overflow: hidden; border: 1px solid #1e293b; }
    .progress-bar { width: 0%; height: 12px; background: linear-gradient(90deg, #3b82f6, #06b6d4); transition: width 0.2s; }

    .sidebar-link { display: flex; align-items: center; gap: 12px; padding: 14px 20px; border-radius: 14px; transition: 0.3s; color: #94a3b8; font-weight: 600; text-decoration: none; }
    .sidebar-link:hover, .sidebar-link.active { background: #3b82f6; color: white; box-shadow: 0 10px 20px -5px rgba(59, 130, 246, 0.4); }
    .footer-nav { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); width: 92%; max-width: 480px; height: 75px; border-radius: 40px; z-index: 1000; border: 1px solid rgba(59, 130, 246, 0.3); display: flex; justify-content: space-around; align-items: center; box-shadow: 0 20px 50px rgba(0,0,0,0.8); }
    .f-item { display: flex; flex-direction: column; align-items: center; color: #94a3b8; font-weight: bold; font-size: 11px; transition: 0.3s; text-decoration: none; }
    .f-item:hover, .f-item.active { color: #3b82f6; }
    .f-item i { font-size: 22px; margin-bottom: 2px; }
    .btn-premium { background: linear-gradient(135deg, #3b82f6, #1e40af); color: white; font-weight: bold; padding: 14px; border-radius: 15px; transition: 0.3s; text-align: center; display: block; text-decoration: none; }
    .btn-premium:hover { transform: scale(1.02); opacity: 0.9; }

    /* TikTok App Styles Integration */
    .tiktok-app-container { width: 100%; display: flex; justify-content: center; padding: 20px 0; background-color: #000; }
    .tiktok-wrapper { position: relative; width: 500px; height: 800px; overflow-y: scroll; scroll-snap-type: y mandatory; scrollbar-width: none; border: 4px solid #9333ea; border-radius: 15px; background: #000; }
    .tiktok-wrapper::-webkit-scrollbar { display: none; }
    .video-slide { width: 100%; height: 800px; scroll-snap-align: start; scroll-snap-stop: always; position: relative; background: #000; }
    .video-slide iframe { width: 100%; height: 100%; border: none; }
    .logo-overlay-app { position: absolute; top: 25px; left: 20px; width: 80px; z-index: 20; pointer-events: none; }
    .ep-tag-app { position: absolute; top: 25px; right: 20px; background: #9333ea; color: white; padding: 12px 20px; border-radius: 10px; font-weight: bold; z-index: 20; box-shadow: 0 0 15px rgba(0,0,0,0.5); white-space: nowrap; font-size: 16px; min-width: 110px; text-align: center; }
    @media (max-width: 600px) {
        .tiktok-wrapper { width: 100vw; height: 90vh; border: none; border-radius: 0; }
        .video-slide { height: 90vh; }
        .logo-overlay-app { width: 65px; top: 20px; }
        .ep-tag-app { padding: 10px 15px; font-size: 14px; min-width: 90px; top: 20px; }
    }
</style>
<div id="global-loader"><div class="text-center"><div class="spinner mx-auto mb-4"></div><p class="text-blue-500 font-bold animate-pulse">LOADING...</p></div></div>
<script>
    function showGlobalLoader() { document.getElementById('global-loader').style.display = 'flex'; }
    window.onpageshow = function(event) { if (event.persisted) { document.getElementById('global-loader').style.display = 'none'; } };
</script>
"""

# --- UTILITY: USER NAV ---
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
        <a href="/" onclick="showGlobalLoader()" class="flex items-center gap-2 text-decoration-none">
            <img src="{conf['logo_url']}" class="h-8 md:h-11" loading="lazy">
            <span class="text-xl md:text-2xl font-black text-blue-500 uppercase italic tracking-tighter">{conf['site_name']}</span>
        </a>
        <div class="flex items-center gap-6">
            <form action="/" method="GET" class="hidden md:flex bg-slate-900 rounded-full px-4 py-1 border border-slate-800">
                <input type="text" name="search" placeholder="Search movies..." class="bg-transparent border-none outline-none text-sm w-48 p-1">
                <button type="submit" onclick="showGlobalLoader()" class="text-slate-500"><i class="fa fa-search"></i></button>
            </form>
            {user_status}
        </div>
    </nav>
    '''

# --- UTILITY: FOOTER ---
def get_footer():
    mail_link = ""
    if 'user_id' in session:
        mail_link = f'<a href="/mailbox" onclick="showGlobalLoader()" class="f-item"><i class="fa fa-envelope"></i><span>MAIL 📬</span></a>'
    
    return f'''
    <div class="h-28"></div>
    <div class="glass footer-nav">
        <a href="/" onclick="showGlobalLoader()" class="f-item"><i class="fa fa-home"></i><span>HOME 🏠</span></a>
        <a href="/help" onclick="showGlobalLoader()" class="f-item"><i class="fa fa-question-circle"></i><span>HELP 🆘</span></a>
        <a href="/request" onclick="showGlobalLoader()" class="f-item"><i class="fa fa-paper-plane"></i><span>REQUEST 🚀</span></a>
        {mail_link}
    </div>
    '''

# --- USER PANEL ROUTES ---

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

    # Python f-string conflict fix with double curly braces
    html_content = f"""
    <!DOCTYPE html><html><head>{CSS}
    <style>
        .slider-box {{ height: {conf['slider_height_mobile']}; }}
        @media(min-width: 768px) {{ .slider-box {{ height: {conf['slider_height_desktop']}; }} }}
    </style>
    <title>{conf['site_name']}</title></head><body>
    {get_navbar(conf)}
    <div class="container mx-auto px-4 py-6">
        
        <!-- Search Bar Option Start -->
        <div class="mb-10 max-w-2xl mx-auto">
            <form action="/" method="GET" class="relative group" onsubmit="showGlobalLoader()">
                <input type="text" name="search" placeholder="Search Your Favorite Drama..." 
                       class="w-full bg-slate-900/50 border-2 border-slate-800 py-4 px-6 rounded-2xl text-white focus:border-blue-600 transition-all duration-300 shadow-2xl"
                       value="{{{{ request.args.get('search', '') }}}}">
                <button type="submit" class="absolute right-3 top-1/2 -translate-y-1/2 bg-blue-600 hover:bg-blue-700 p-2.5 rounded-xl transition-colors shadow-lg">
                    <i class="fa fa-search text-white"></i>
                </button>
            </form>
            {{% if request.args.get('search') %}}
                <div class="text-center mt-4">
                    <a href="/" onclick="showGlobalLoader()" class="text-xs font-bold text-blue-500 uppercase tracking-widest hover:text-white transition"><i class="fa fa-times-circle"></i> Clear Search</a>
                </div>
            {{% endif %}}
        </div>
        <!-- Search Bar Option End -->

        <div class="mb-6 text-center"> {{{{ conf.ads.header | safe }}}} </div>

        {{% if slider_movies %}}
        <div class="slider-box mb-12 shadow-2xl">
            {{% for sm in slider_movies %}}
            <a href="/movie/{{{{ sm._id }}}}" onclick="showGlobalLoader()">
                <img src="{{{{ sm.thumbnail if sm.thumbnail else sm.poster }}}}" class="slide-img" loading="lazy">
            </a>
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
                    <div class="movie-card" onclick="showGlobalLoader(); location.href='/movie/{{{{ m._id }}}}'">
                        <img src="{{{{ m.poster }}}}" class="card-thumb" style="height: {{{{ conf.home_poster_height }}}}" loading="lazy">
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
            <div class="w-full md:w-[450px]">
                <img src="{{{{ movie.thumbnail if movie.thumbnail else movie.poster }}}}" class="full-poster shadow-2xl border-4 border-slate-900" loading="lazy">
            </div>
            <div class="flex-1">
                <span class="bg-blue-600 px-5 py-1 rounded-full text-xs font-bold uppercase shadow-lg">{{{{ movie.badge }}}}</span>
                <h1 class="text-4xl md:text-5xl font-black mt-4 mb-2 italic tracking-tighter uppercase leading-tight">{{{{ movie.name }}}}</h1>
                <p class="text-blue-500 font-bold mb-8 uppercase text-sm tracking-widest">{{{{ movie.category }}}}</p>
                
                <div class="glass p-8 rounded-[2rem] border border-blue-500/20 shadow-2xl">
                    <h3 class="text-xl font-bold mb-8 flex items-center gap-3 text-white border-b border-white/5 pb-4">
                        <i class="fa fa-play-circle text-blue-500 text-3xl"></i> DOWNLOAD & WATCH LINKS
                    </h3>
                    
                    <!-- Vertical TikTok Player Button -->
                    <a href="/play-vertical/{{{{ movie._id }}}}" class="btn-premium !bg-purple-600 mb-6 block w-full !py-5 shadow-purple-500/20 font-black">
                         🔥 WATCH IN VERTICAL PLAYER (SWIPE MODE)
                    </a>

                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {{% for link in movie.links %}}
                        <a href="{{{{ link.url }}}}" target="_blank" class="btn-premium">
                             📥 {{{{ link.label }}}}
                        </a>
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

# --- NEW: VERTICAL PLAYER ROUTE ---
@app.route('/play-vertical/<id>')
def play_vertical(id):
    conf = get_config()
    movie = movies_col.find_one({"_id": ObjectId(id)})
    if not movie: return redirect('/')
    
    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>Swipe Player - {{{{ movie.name }}}}</title></head>
    <body style="background:#000; overflow:hidden;">
    <div class="fixed top-6 left-6 z-50">
        <a href="/movie/{{{{ movie._id }}}}" class="bg-white/10 p-3 rounded-full text-white backdrop-blur-md border border-white/20 shadow-xl"><i class="fa fa-arrow-left"></i></a>
    </div>

    <div class="tiktok-app-container">
      <div class="tiktok-wrapper" id="videoContainer">
        {{% for link in movie.links %}}
        <div class="video-slide" data-url="{{{{ link.url }}}}">
          <img src="{{{{ conf.logo_url }}}}" class="logo-overlay-app">
          <div class="ep-tag-app">{{{{ link.label }}}}</div>
          <iframe class="video-frame" src="" scrolling="no" allow="autoplay; encrypted-media" allowfullscreen></iframe>
        </div>
        {{% endfor %}}
      </div>
    </div>

    <script>
      const slides = document.querySelectorAll('.video-slide');
      const container = document.getElementById('videoContainer');
      const observerOptions = {{ root: container, threshold: 0.7 }};

      const observer = new IntersectionObserver((entries) => {{
        entries.forEach(entry => {{
          const iframe = entry.target.querySelector('iframe');
          const videoUrl = entry.target.getAttribute('data-url');
          if (entry.isIntersecting) {{
            if (iframe.src !== videoUrl) iframe.src = videoUrl;
          }} else {{
            iframe.src = ""; // Fast loading fix: Stop video when not in view
          }}
        }});
      }}, observerOptions);
      slides.forEach(slide => observer.observe(slide));
    </script>
    </body></html>
    """
    return render_template_string(html, movie=movie, conf=conf)

# --- HELP PAGE ---
@app.route('/help')
def help_page():
    conf = get_config()
    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>Support - {conf['site_name']}</title></head><body>
    {get_navbar(conf)}
    <div class="container mx-auto px-4 py-10 text-center">
        <div class="glass p-10 md:p-20 rounded-[3.5rem] max-w-4xl mx-auto shadow-2xl border-t-4 border-blue-600">
            <img src="{conf['logo_url']}" class="h-24 mx-auto mb-8 drop-shadow-2xl" loading="lazy">
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

# --- AUTH SYSTEM ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name, user, pw = request.form.get('name'), request.form.get('user'), request.form.get('pass')
        if users_col.find_one({"user": user}):
            flash("Username already exists! Try another.")
        else:
            uid = "DW" + str(ObjectId())[-6:].upper()
            users_col.insert_one({"uid": uid, "name": name, "user": user, "pass": pw})
            flash("Registration Successful! Please Login.")
            return redirect('/login')
    
    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>Sign Up</title></head>
    <body class="flex items-center justify-center min-h-screen p-4">
        <form method="POST" onsubmit="showGlobalLoader()" class="glass p-10 rounded-[2.5rem] w-full max-w-md space-y-6 shadow-2xl border-t-4 border-blue-600">
            <h2 class="text-3xl font-black text-center text-blue-500 uppercase italic">Create Account</h2>
            {{% with messages = get_flashed_messages() %}}{{% if messages %}}<p class="text-red-500 text-xs text-center font-bold">{{{{messages[0]}}}}</p>{{% endif %}}{{% endwith %}}
            <input type="text" name="name" placeholder="Your Full Name" required>
            <input type="text" name="user" placeholder="Create Username" required>
            <input type="password" name="pass" placeholder="Password" required>
            <button class="bg-blue-600 w-full py-4 rounded-2xl font-bold text-white shadow-xl uppercase">Register Now</button>
            <p class="text-center text-sm text-slate-400">Already have an account? <a href="/login" class="text-blue-500 font-bold">Login</a></p>
        </form>
    </body></html>
    """
    return render_template_string(html)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('user', '').strip()
        pw = request.form.get('pass', '').strip()
        u = users_col.find_one({"user": user, "pass": pw})
        if u:
            session.clear()
            session['user_id'] = str(u['_id'])
            session['user_name'] = u['name']
            return redirect('/')
        flash("Invalid Username or Password!")

    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>Login</title></head>
    <body class="flex items-center justify-center min-h-screen p-4">
        <form method="POST" onsubmit="showGlobalLoader()" class="glass p-10 rounded-[2.5rem] w-full max-w-md space-y-6 shadow-2xl border-t-4 border-blue-600">
            <h2 class="text-3xl font-black text-center text-blue-500 uppercase italic">User Login</h2>
            {{% with messages = get_flashed_messages() %}}{{% if messages %}}<p class="text-red-500 text-xs text-center font-bold">{{{{messages[0]}}}}</p>{{% endif %}}{{% endwith %}}
            <input type="text" name="user" placeholder="Username" required>
            <input type="password" name="pass" placeholder="Password" required>
            <button class="bg-blue-600 w-full py-4 rounded-2xl font-bold text-white shadow-xl uppercase tracking-widest">Access Account</button>
            <div class="flex justify-between text-xs text-slate-500 px-2">
                <span>New User? <a href="/register" class="text-blue-500 font-bold">Sign Up</a></span>
                <a href="/" class="hover:text-white">Back to Home</a>
            </div>
        </form>
    </body></html>
    """
    return render_template_string(html)

@app.route('/admin/wp', methods=['GET', 'POST'])
def admin_login():
    conf = get_config()
    is_setup = not conf.get('admin_user') or not conf.get('admin_pass')

    if request.method == 'POST':
        user = request.form.get('user', '').strip()
        pw = request.form.get('pass', '').strip()
        if is_setup:
            settings_col.update_one({"type": "config"}, {"$set": {"admin_user": user, "admin_pass": pw}})
            flash("Admin Credentials Set Successfully! Now Login.")
            return redirect('/admin/wp')
        if user == conf['admin_user'] and pw == conf['admin_pass']:
            session.clear()
            session['admin'] = True
            return redirect('/admin')
        flash("Incorrect Admin Credentials!")

    title = "Admin Setup" if is_setup else "Admin Login"
    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>{title}</title></head>
    <body class="flex items-center justify-center min-h-screen bg-[#05070a]">
        <form method="POST" onsubmit="showGlobalLoader()" class="glass p-12 rounded-[3rem] w-full max-w-md space-y-6 border-b-4 border-blue-600">
            <div class="text-center"><i class="fa fa-user-shield text-5xl text-blue-500 mb-4"></i></div>
            <h2 class="text-2xl font-black text-center text-white uppercase italic tracking-widest">{title}</h2>
            {{% if is_setup %}}<p class="text-[10px] text-yellow-500 text-center font-bold uppercase">Configure your admin credentials first.</p>{{% endif %}}
            {{% with messages = get_flashed_messages() %}}{{% if messages %}}<p class="text-red-500 text-xs text-center font-bold">{{{{messages[0]}}}}</p>{{% endif %}}{{% endwith %}}
            <input type="text" name="user" placeholder="Username" required>
            <input type="password" name="pass" placeholder="Password" required>
            <button class="bg-blue-600 w-full py-4 rounded-xl font-black text-white shadow-2xl uppercase">Submit</button>
        </form>
    </body></html>
    """
    return render_template_string(html, is_setup=is_setup)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- REQUESTS & MAIL ---

@app.route('/request', methods=['GET', 'POST'])
def request_movie():
    if 'user_id' not in session: 
        flash("Please login to request a movie!")
        return redirect('/login')
    conf = get_config()
    if request.method == 'POST':
        requests_col.insert_one({
            "user_id": session['user_id'],
            "user_name": session['user_name'],
            "movie_name": request.form.get('movie_name'),
            "email": request.form.get('email'),
            "status": "Pending",
            "date": datetime.now().strftime("%d %b %Y")
        })
        flash("Request submitted successfully!")
        return redirect('/mailbox')

    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>Request Movie</title></head><body>
    {get_navbar(conf)}
    <div class="container mx-auto px-4 py-10">
        <form method="POST" onsubmit="showGlobalLoader()" class="glass p-10 rounded-[3rem] max-w-xl mx-auto space-y-6 border-t-4 border-blue-600 shadow-2xl">
            <h2 class="text-3xl font-black text-blue-500 uppercase italic">Request Movie 🚀</h2>
            <p class="text-xs text-slate-500 mb-6 uppercase font-bold">Provide drama details and we will upload it for you.</p>
            <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 uppercase px-1">Movie/Drama Name</label>
                <input type="text" name="movie_name" placeholder="Enter full name" required>
            </div>
            <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 uppercase px-1">Your Name</label>
                <input type="text" value="{session['user_name']}" readonly class="opacity-50">
            </div>
            <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 uppercase px-1">Contact Email</label>
                <input type="email" name="email" placeholder="Your active email" required>
            </div>
            <button class="bg-blue-600 w-full py-4 rounded-2xl font-bold text-white shadow-xl uppercase tracking-widest">Submit Request</button>
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
        <h2 class="text-3xl font-black mb-8 text-blue-500 uppercase italic flex items-center gap-4">
            <i class="fa fa-envelope-open-text"></i> MailBox (Inbox)
        </h2>
        <div class="space-y-4">
            {{% if not notifs %}}
                <div class="glass p-10 rounded-3xl text-center text-slate-500 italic">No notifications or mail found yet.</div>
            {{% endif %}}
            {{% for n in notifs %}}
            <div class="glass p-6 rounded-3xl border-l-4 border-blue-600 shadow-xl">
                <div class="flex justify-between items-start mb-2">
                    <span class="text-blue-500 font-black text-xs uppercase tracking-widest">Notification</span>
                    <span class="text-[10px] text-slate-600 uppercase font-bold">{{{{ n.date }}}}</span>
                </div>
                <p class="text-sm font-semibold leading-relaxed text-slate-200">{{{{ n.message }}}}</p>
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
            <div class="w-24 h-24 bg-blue-600 rounded-full mx-auto flex items-center justify-center text-4xl font-black mb-6 shadow-xl border-4 border-slate-900">
                {u['name'][0] if u else 'U'}
            </div>
            <h2 class="text-3xl font-black mb-1 uppercase tracking-tighter italic">{u['name'] if u else 'User'}</h2>
            <p class="text-blue-500 font-bold text-xs mb-8 uppercase tracking-widest">Member ID: {u['uid'] if u else 'N/A'}</p>
            <div class="space-y-3">
                <a href="/mailbox" onclick="showGlobalLoader()" class="btn-premium flex items-center justify-center gap-2"><i class="fa fa-envelope"></i> My MailBox</a>
                <a href="/logout" onclick="showGlobalLoader()" class="block py-4 text-red-500 font-black text-xs uppercase tracking-widest hover:underline">Sign Out Account</a>
            </div>
        </div>
    </div>
    {get_footer()}
    </body></html>
    """
    return render_template_string(html)

# --- ADMIN PANEL ---

@app.route('/admin')
def admin_dash():
    if not session.get('admin'): return redirect('/admin/wp')
    search = request.args.get('search', '')
    query = {"name": {"$regex": search, "$options": "i"}} if search else {}
    movies = list(movies_col.find(query).sort("_id", -1))
    
    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>Admin Dashboard</title></head>
    <body class="flex flex-col md:flex-row min-h-screen">
        <div class="w-full md:w-72 bg-[#080c14] border-r border-slate-900 p-8 flex flex-col shadow-2xl h-full sticky top-0">
            <div class="mb-12"><h2 class="text-2xl font-black text-blue-500 uppercase italic">Admin Panel</h2><p class="text-[10px] text-slate-500 font-bold uppercase tracking-widest">DramaWorld Control</p></div>
            <nav class="space-y-2 flex-grow">
                <a href="/admin" class="sidebar-link active"><i class="fa fa-dashboard"></i> Dashboard</a>
                <a href="/admin/requests" class="sidebar-link"><i class="fa fa-paper-plane"></i> User Requests</a>
                <a href="/admin/add" class="sidebar-link"><i class="fa fa-plus-circle"></i> Add New Movie</a>
                <a href="/admin/settings" class="sidebar-link"><i class="fa fa-cog"></i> Site Settings</a>
                <a href="/logout" class="sidebar-link text-red-500 mt-20"><i class="fa fa-sign-out-alt"></i> Logout System</a>
            </nav>
        </div>
        <main class="flex-grow p-6 md:p-12">
            <div class="flex flex-col md:flex-row justify-between items-center mb-10 gap-4">
                <h1 class="text-3xl font-black uppercase tracking-tighter">Movie Library</h1>
                <form action="/admin" method="GET" class="flex bg-slate-900 rounded-2xl px-5 py-2 border border-slate-800 w-full md:w-96 shadow-lg">
                    <input type="text" name="search" placeholder="Search in library..." class="bg-transparent border-none p-1 text-sm" value="{search}">
                    <button type="submit" class="text-slate-500"><i class="fa fa-search"></i></button>
                </form>
            </div>
            <div class="glass rounded-[2.5rem] overflow-hidden shadow-2xl">
                <table class="w-full text-left border-collapse">
                    <thead class="bg-slate-900 text-slate-500 text-xs uppercase font-bold tracking-widest">
                        <tr class="border-b border-white/5"><th class="p-6">Movie Information</th><th class="p-6">Category</th><th class="p-6 text-center">Manage</th></tr>
                    </thead>
                    <tbody class="divide-y divide-slate-800">
                        {{% for m in movies %}}
                        <tr class="hover:bg-slate-800/50 transition">
                            <td class="p-6 flex items-center gap-4">
                                <img src="{{{{ m.thumbnail if m.thumbnail else m.poster }}}}" class="w-12 h-16 rounded-xl object-cover shadow-lg border border-white/5" loading="lazy">
                                <span class="font-bold text-sm text-slate-200">{{{{ m.name }}}}</span>
                            </td>
                            <td class="p-6 text-xs text-blue-400 font-bold uppercase tracking-widest">{{{{ m.category }}}}</td>
                            <td class="p-6">
                                <div class="flex justify-center gap-4">
                                    <a href="/admin/edit/{{{{ m._id }}}}" class="p-3 bg-blue-500/10 text-blue-500 rounded-xl hover:bg-blue-500 hover:text-white transition shadow-md"><i class="fa fa-edit"></i></a>
                                    <a href="/admin/delete/{{{{ m._id }}}}" class="p-3 bg-red-500/10 text-red-500 rounded-xl hover:bg-red-500 hover:text-white transition shadow-md" onclick="return confirm('Delete this movie from library?')"><i class="fa fa-trash"></i></a>
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

@app.route('/admin/requests', methods=['GET', 'POST'])
def admin_requests():
    if not session.get('admin'): return redirect('/admin/wp')
    if request.method == 'POST':
        req_id = request.form.get('req_id')
        status = request.form.get('status')
        admin_note = request.form.get('admin_note')
        req = requests_col.find_one({"_id": ObjectId(req_id)})
        if req:
            notif_col.insert_one({
                "user_id": req['user_id'],
                "message": f"Regarding your request '{req['movie_name']}': It has been {status}. Admin Message: {admin_note}",
                "date": datetime.now().strftime("%d %b, %H:%M")
            })
            if status == "Uploaded/Done":
                requests_col.delete_one({"_id": ObjectId(req_id)})
            else:
                requests_col.update_one({"_id": ObjectId(req_id)}, {"$set": {"status": status}})
        flash("Updated successfully!")
        return redirect('/admin/requests')

    reqs = list(requests_col.find().sort("_id", -1))
    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>User Requests</title></head>
    <body class="flex flex-col md:flex-row min-h-screen">
        <div class="w-full md:w-72 bg-[#080c14] border-r border-slate-900 p-8 flex flex-col shadow-2xl h-full sticky top-0">
            <h2 class="text-2xl font-black text-blue-500 mb-10 italic">ADMIN</h2>
            <nav class="space-y-2">
                <a href="/admin" class="sidebar-link"><i class="fa fa-dashboard"></i> Dashboard</a>
                <a href="/admin/requests" class="sidebar-link active"><i class="fa fa-paper-plane"></i> User Requests</a>
                <a href="/admin/add" class="sidebar-link"><i class="fa fa-plus-circle"></i> Add Movie</a>
                <a href="/admin/settings" class="sidebar-link"><i class="fa fa-cog"></i> Settings</a>
                <a href="/logout" class="sidebar-link text-red-500 mt-20">Logout</a>
            </nav>
        </div>
        <main class="flex-grow p-6 md:p-12">
            <h1 class="text-3xl font-black mb-12 uppercase tracking-tighter italic">Movie Requests Queue</h1>
            <div class="grid grid-cols-1 gap-6">
                {{% for r in reqs %}}
                <div class="glass p-8 rounded-[2.5rem] flex flex-col md:flex-row justify-between items-center gap-8 shadow-xl">
                    <div class="flex-1">
                        <h3 class="text-2xl font-black text-blue-500 uppercase italic tracking-tighter">{{{{ r.movie_name }}}}</h3>
                        <p class="text-xs text-slate-400 font-bold mt-2 uppercase tracking-widest">Requester: {{{{ r.user_name }}}} | {{{{ r.email }}}}</p>
                        <div class="mt-4 flex items-center gap-2">
                            <span class="px-3 py-1 bg-yellow-500/10 text-yellow-500 text-[10px] font-bold rounded-full border border-yellow-500/20 uppercase tracking-widest">{{{{ r.status }}}}</span>
                            <span class="text-[10px] text-slate-600 font-bold uppercase">{{{{ r.date }}}}</span>
                        </div>
                    </div>
                    <form method="POST" class="flex flex-col md:flex-row gap-2 w-full md:w-auto">
                        <input type="hidden" name="req_id" value="{{{{ r._id }}}}">
                        <input type="text" name="admin_note" placeholder="Note to user..." required class="text-xs w-full md:w-56">
                        <select name="status" class="text-xs w-full md:w-36">
                            <option>Uploaded/Done</option>
                            <option>Rejected</option>
                        </select>
                        <button class="bg-blue-600 px-8 py-3 rounded-xl font-bold text-xs uppercase tracking-widest shadow-xl">Update</button>
                    </form>
                </div>
                {{% endfor %}}
            </div>
        </main>
    </body></html>
    """
    return render_template_string(html, reqs=reqs)

@app.route('/admin/add', methods=['GET', 'POST'])
def add_movie():
    if not session.get('admin'): return redirect('/admin/wp')
    cats = list(categories_col.find())
    if request.method == 'POST':
        poster_val = process_media(request, 'poster_file', 'poster')
        thumb_val = process_media(request, 'thumb_file', 'thumbnail')
        
        labels, urls = request.form.getlist('l_name[]'), request.form.getlist('l_url[]')
        links = [{"label": labels[i], "url": urls[i]} for i in range(len(labels)) if labels[i] and urls[i]]
        movies_col.insert_one({
            "name": request.form.get('name'), 
            "poster": poster_val,
            "thumbnail": thumb_val,
            "badge": request.form.get('badge'), 
            "category": request.form.get('category'), 
            "links": links
        })
        return redirect('/admin')
    
    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>Publish Movie</title></head>
    <body class="flex flex-col md:flex-row min-h-screen">
        <div class="w-full md:w-72 bg-[#080c14] border-r border-slate-900 p-8 flex flex-col shadow-2xl h-full sticky top-0">
            <h2 class="text-2xl font-black text-blue-500 mb-10 uppercase italic">ADMIN</h2>
            <nav class="space-y-2 flex-grow">
                <a href="/admin" class="sidebar-link"><i class="fa fa-dashboard"></i> Dashboard</a>
                <a href="/admin/requests" class="sidebar-link"><i class="fa fa-paper-plane"></i> User Requests</a>
                <a href="/admin/add" class="sidebar-link active"><i class="fa fa-plus-circle"></i> Add Movie</a>
                <a href="/admin/settings" class="sidebar-link"><i class="fa fa-cog"></i> Settings</a>
            </nav>
        </div>
        <main class="flex-grow p-6 md:p-12">
            <div class="max-w-4xl glass p-10 rounded-[3rem] shadow-2xl mx-auto border-t-4 border-blue-600">
                <h2 class="text-3xl font-black mb-10 text-blue-500 uppercase italic tracking-tighter">Publish New Movie</h2>
                
                <!-- Upload Progress Section -->
                <div id="upload-status" class="progress-container mb-6">
                    <div class="flex justify-between px-4 py-2 text-[10px] font-bold text-blue-400 uppercase tracking-widest">
                        <span id="progress-text">Uploading: 0%</span>
                        <span id="progress-percent">0%</span>
                    </div>
                    <div class="progress-bar" id="progress-bar"></div>
                </div>

                <form id="upload-form" method="POST" enctype="multipart/form-data" class="space-y-8">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div class="space-y-1"><label class="text-xs font-bold text-slate-500 uppercase px-1">Movie Full Name</label><input type="text" name="name" required placeholder="e.g. Kingdom S01 Dual Audio"></div>
                        <div class="space-y-1"><label class="text-xs font-bold text-slate-500 uppercase px-1">Select Category</label>
                            <select name="category" required>
                                {{% for c in cats %}}<option value="{{{{ c.name }}}}">{{{{ c.name }}}}</option>{{% endfor %}}
                            </select>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div class="space-y-4">
                            <h4 class="text-xs font-bold text-blue-500 uppercase">1. MOVIE POSTER (Home View)</h4>
                            <input type="text" name="poster" placeholder="Poster URL">
                            <input type="file" name="poster_file" accept="image/*" class="text-xs">
                        </div>
                        <div class="space-y-4">
                            <h4 class="text-xs font-bold text-green-500 uppercase">2. THUMBNAIL (Detail & Slider)</h4>
                            <input type="text" name="thumbnail" placeholder="Thumbnail URL">
                            <input type="file" name="thumb_file" accept="image/*" class="text-xs">
                        </div>
                    </div>

                    <div class="space-y-1"><label class="text-xs font-bold text-slate-500 uppercase px-1">Badge Info</label><input type="text" name="badge" placeholder="e.g. 1080p Dual Audio"></div>
                    
                    <div id="btn-box" class="space-y-4 pt-6 border-t border-slate-800">
                        <h4 class="text-blue-500 font-black uppercase text-xs tracking-widest flex items-center gap-2 mb-4"><i class="fa fa-link"></i> Download/Watch Link Management</h4>
                    </div>

                    <div class="mt-6 p-4 border border-blue-500/20 bg-blue-500/5 rounded-2xl">
                        <h4 class="text-blue-500 font-black uppercase text-[10px] mb-2 tracking-widest">Multi Link Adder (Bulk)</h4>
                        <textarea id="multi-link-area" rows="4" class="text-xs" placeholder="Format: Label - URL (one per line)"></textarea>
                        <button type="button" onclick="processMultiLinks()" class="mt-2 bg-blue-600/20 text-blue-400 border border-blue-500/30 px-4 py-2 rounded-xl text-[10px] font-bold uppercase hover:bg-blue-600 hover:text-white transition">Process Multi Links</button>
                    </div>

                    <button type="button" onclick="addL()" class="text-blue-400 font-bold text-xs uppercase hover:underline tracking-widest">+ Add Single Link Button</button>
                    
                    <div class="pt-8 flex gap-4">
                        <button type="submit" class="bg-blue-600 flex-1 py-4 rounded-2xl font-black text-white shadow-xl uppercase tracking-widest">Publish to Site</button>
                        <a href="/admin" class="bg-slate-800 px-12 py-4 rounded-2xl font-bold text-white shadow-lg uppercase text-xs flex items-center text-decoration-none">Cancel</a>
                    </div>
                </form>
            </div>
        </main>
        <script>
            function addL(label = '', url = ''){{
                const b = document.getElementById('btn-box');
                const d = document.createElement('div');
                d.className = "flex gap-4 p-4 glass rounded-2xl border border-white/5 relative group animate-fade-in";
                d.innerHTML = `
                    <input type="text" name="l_name[]" placeholder="Button Label" required class="text-sm" value="${{label}}">
                    <input type="text" name="l_url[]" placeholder="Destination URL" required class="text-sm" value="${{url}}">
                    <button type="button" onclick="this.parentElement.remove()" class="text-red-500 p-2 hover:bg-red-500/10 rounded-lg"><i class="fa fa-times"></i></button>
                `;
                b.appendChild(d);
            }}

            function processMultiLinks() {{
                const area = document.getElementById('multi-link-area');
                const lines = area.value.split('\\n');
                lines.forEach(line => {{
                    if(line.includes('-')){{
                        const parts = line.split('-');
                        const label = parts[0].trim();
                        const url = parts.slice(1).join('-').trim();
                        if(label && url) addL(label, url);
                    }}
                }});
                area.value = '';
            }}
            
            const uploadForm = document.getElementById('upload-form');
            if(uploadForm) {{
                uploadForm.onsubmit = function(e) {{
                    e.preventDefault();
                    const formData = new FormData(uploadForm);
                    const xhr = new XMLHttpRequest();
                    
                    document.getElementById('upload-status').style.display = 'block';
                    showGlobalLoader();

                    xhr.upload.addEventListener('progress', function(e) {{
                        if (e.lengthComputable) {{
                            const percent = Math.round((e.loaded / e.total) * 100);
                            document.getElementById('progress-bar').style.width = percent + '%';
                            document.getElementById('progress-percent').innerText = percent + '%';
                            document.getElementById('progress-text').innerText = 'Uploading: ' + percent + '%';
                        }}
                    }});

                    xhr.onreadystatechange = function() {{
                        if (xhr.readyState == 4 && xhr.status == 200) {{
                            window.location.href = '/admin';
                        }}
                    }};

                    xhr.open('POST', '/admin/add', true);
                    xhr.send(formData);
                }};
            }}

            addL();
        </script>
    </body></html>
    """
    return render_template_string(html, cats=cats)

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not session.get('admin'): return redirect('/admin/wp')
    conf = get_config()
    cats = list(categories_col.find())
    
    if request.method == 'POST':
        if 'update_branding' in request.form:
            settings_col.update_one({"type": "config"}, {"$set": {
                "site_name": request.form.get('site_name'),
                "logo_url": request.form.get('logo_url'),
                "help_text": request.form.get('help_text'),
                "channel_link": request.form.get('channel_link'),
                "slider_limit": int(request.form.get('slider_limit', 5)),
                "slider_height_desktop": request.form.get('slider_height_desktop', '480px'),
                "slider_height_mobile": request.form.get('slider_height_mobile', '230px'),
                "home_poster_height": request.form.get('home_poster_height', '320px')
            }})
        elif 'update_profile' in request.form:
            settings_col.update_one({"type": "config"}, {"$set": {
                "admin_user": request.form.get('admin_user'),
                "admin_pass": request.form.get('admin_pass')
            }})
        elif 'add_cat' in request.form:
            categories_col.insert_one({"name": request.form.get('cat_name')})
        elif 'del_cat' in request.form:
            categories_col.delete_one({"_id": ObjectId(request.form.get('cat_id'))})
        elif 'update_ads' in request.form:
            ads = {k: request.form.get(k) for k in conf['ads'].keys()}
            settings_col.update_one({"type": "config"}, {"$set": {"ads": ads}})
            
        flash("System Configuration Updated!")
        return redirect('/admin/settings')

    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>System Settings</title></head>
    <body class="flex flex-col md:flex-row min-h-screen">
        <div class="w-full md:w-72 bg-[#080c14] border-r border-slate-900 p-8 flex flex-col shadow-2xl h-full sticky top-0">
            <h2 class="text-2xl font-black text-blue-500 mb-10 italic uppercase">System</h2>
            <nav class="space-y-2">
                <a href="/admin" class="sidebar-link"><i class="fa fa-dashboard"></i> Dashboard</a>
                <a href="/admin/requests" class="sidebar-link"><i class="fa fa-paper-plane"></i> User Requests</a>
                <a href="/admin/add" class="sidebar-link"><i class="fa fa-plus-circle"></i> Add Movie</a>
                <a href="/admin/settings" class="sidebar-link active"><i class="fa fa-cog"></i> Site Settings</a>
            </nav>
        </div>
        <main class="flex-grow p-6 md:p-12 space-y-10">
            <h1 class="text-4xl font-black uppercase tracking-tighter italic">Global Configuration</h1>
            
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-10">
                <form method="POST" onsubmit="showGlobalLoader()" class="glass p-8 rounded-[3rem] space-y-4 shadow-2xl border-t-4 border-blue-600">
                    <h3 class="text-blue-500 font-black uppercase text-xs tracking-widest border-b border-slate-800 pb-3">Branding & Social</h3>
                    <div class="space-y-1"><label class="text-[10px] uppercase font-bold text-slate-500">Site Display Name</label><input type="text" name="site_name" value="{{{{conf.site_name}}}}"></div>
                    <div class="space-y-1"><label class="text-[10px] uppercase font-bold text-slate-500">Logo Image URL</label><input type="text" name="logo_url" value="{{{{conf.logo_url}}}}"></div>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="space-y-1"><label class="text-[10px] uppercase font-bold text-slate-500">Slider (Desktop)</label><input type="text" name="slider_height_desktop" value="{{{{conf.slider_height_desktop}}}}"></div>
                        <div class="space-y-1"><label class="text-[10px] uppercase font-bold text-slate-500">Slider (Mobile)</label><input type="text" name="slider_height_mobile" value="{{{{conf.slider_height_mobile}}}}"></div>
                    </div>
                    <div class="space-y-1"><label class="text-[10px] uppercase font-bold text-slate-500">Home Poster Height</label><input type="text" name="home_poster_height" value="{{{{conf.home_poster_height}}}}"></div>
                    <div class="space-y-1"><label class="text-[10px] uppercase font-bold text-slate-500">Help Text</label><textarea name="help_text" rows="3">{{{{conf.help_text}}}}</textarea></div>
                    <div class="space-y-1"><label class="text-[10px] uppercase font-bold text-slate-500">Telegram Link</label><input type="text" name="channel_link" value="{{{{conf.channel_link}}}}"></div>
                    <button name="update_branding" class="bg-blue-600 w-full py-4 rounded-2xl font-bold uppercase tracking-widest mt-4">Save Identity</button>
                </form>

                <div class="space-y-10">
                    <div class="glass p-8 rounded-[3rem] space-y-6 shadow-2xl border-t-4 border-green-600">
                        <h3 class="text-green-500 font-black uppercase text-xs tracking-widest border-b border-slate-800 pb-3">Genre Manager</h3>
                        <form method="POST" class="flex gap-2"><input type="text" name="cat_name" placeholder="New Genre" required><button name="add_cat" class="bg-green-600 px-6 rounded-xl font-black text-white">ADD</button></form>
                        <div class="max-h-56 overflow-y-auto space-y-2 p-2">
                            {{% for c in cats %}}
                            <div class="flex justify-between items-center bg-slate-900/50 p-4 rounded-2xl border border-white/5">
                                <span class="font-bold text-sm tracking-wide">{{{{c.name}}}}</span>
                                <form method="POST" class="inline">
                                    <input type="hidden" name="cat_id" value="{{{{c._id}}}}">
                                    <button name="del_cat" class="text-red-500 hover:text-white transition" onclick="return confirm('Delete category?')"><i class="fa fa-trash"></i></button>
                                </form>
                            </div>
                            {{% endfor %}}
                        </div>
                    </div>
                    <form method="POST" onsubmit="showGlobalLoader()" class="glass p-8 rounded-[3rem] space-y-4 shadow-2xl border-t-4 border-red-600">
                        <h3 class="text-red-500 font-black uppercase text-xs tracking-widest border-b border-slate-800 pb-3">Security Access</h3>
                        <div class="space-y-1"><label class="text-[10px] uppercase font-bold text-slate-500">Admin Username</label><input type="text" name="admin_user" value="{{{{conf.admin_user}}}}"></div>
                        <div class="space-y-1"><label class="text-[10px] uppercase font-bold text-slate-500">Admin Password</label><input type="text" name="admin_pass" value="{{{{conf.admin_pass}}}}"></div>
                        <button name="update_profile" class="bg-red-600 w-full py-4 rounded-xl font-bold uppercase tracking-widest text-xs">Update Security</button>
                    </form>
                </div>
            </div>

            <form method="POST" onsubmit="showGlobalLoader()" class="glass p-10 rounded-[3.5rem] space-y-8 shadow-2xl border-t-4 border-yellow-500">
                <h3 class="text-yellow-500 font-black uppercase text-xs tracking-widest border-b border-slate-800 pb-3 italic">Monetization Scripts</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {{% for k, v in conf.ads.items() %}}
                    <div class="space-y-2">
                        <label class="text-[11px] uppercase font-bold text-slate-500 tracking-widest flex items-center gap-2"><i class="fa fa-code"></i> {{{{k | upper}}}} SLOT</label>
                        <textarea name="{{{{k}}}}" rows="4" placeholder="Paste ad code...">{{{{v}}}}</textarea>
                    </div>
                    {{% endfor %}}
                </div>
                <button name="update_ads" class="bg-yellow-600 w-full py-5 rounded-[2rem] font-black uppercase tracking-tighter text-xl shadow-2xl">🚀 Update Ad System</button>
            </form>
        </main>
    </body></html>
    """
    return render_template_string(html, conf=conf, cats=cats)

@app.route('/admin/edit/<id>', methods=['GET', 'POST'])
def edit_movie(id):
    if not session.get('admin'): return redirect('/admin/wp')
    movie = movies_col.find_one({"_id": ObjectId(id)})
    cats = list(categories_col.find())
    if request.method == 'POST':
        poster_val = process_media(request, 'poster_file', 'poster')
        thumb_val = process_media(request, 'thumb_file', 'thumbnail')
        
        if not poster_val: poster_val = movie.get('poster')
        if not thumb_val: thumb_val = movie.get('thumbnail')

        labels, urls = request.form.getlist('l_name[]'), request.form.getlist('l_url[]')
        links = [{"label": labels[i], "url": urls[i]} for i in range(len(labels)) if labels[i] and urls[i]]
        movies_col.update_one({"_id": ObjectId(id)}, {"$set": {
            "name": request.form.get('name'), 
            "poster": poster_val,
            "thumbnail": thumb_val,
            "badge": request.form.get('badge'), 
            "category": request.form.get('category'), 
            "links": links
        }})
        return redirect('/admin')
    
    html = f"""
    <!DOCTYPE html><html><head>{CSS}<title>Edit - {{{{movie.name}}}}</title></head><body class="p-10">
    <div class="max-w-4xl glass p-10 rounded-[3rem] mx-auto shadow-2xl border-t-4 border-blue-600">
        <h2 class="text-2xl font-black mb-8 uppercase italic">Edit Movie Entry</h2>
        
        <div id="upload-status" class="progress-container mb-6">
            <div class="flex justify-between px-4 py-2 text-[10px] font-bold text-blue-400 uppercase tracking-widest">
                <span id="progress-text">Updating: 0%</span>
                <span id="progress-percent">0%</span>
            </div>
            <div class="progress-bar" id="progress-bar"></div>
        </div>

        <form id="edit-form" method="POST" enctype="multipart/form-data" class="space-y-6">
            <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 uppercase px-1">Movie Name</label>
                <input type="text" name="name" value="{{{{movie.name}}}}" required>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8 border-y border-slate-800 py-6">
                <div class="space-y-4">
                    <h4 class="text-xs font-bold text-blue-500">POSTER</h4>
                    <input type="text" name="poster" placeholder="URL" value="{{{{movie.poster if movie.poster.startswith('http') else ''}}}}">
                    <input type="file" name="poster_file" accept="image/*" class="text-xs">
                </div>
                <div class="space-y-4">
                    <h4 class="text-xs font-bold text-green-500">THUMBNAIL</h4>
                    <input type="text" name="thumbnail" placeholder="URL" value="{{{{movie.thumbnail if movie.thumbnail and movie.thumbnail.startswith('http') else ''}}}}">
                    <input type="file" name="thumb_file" accept="image/*" class="text-xs">
                </div>
            </div>

            <div class="space-y-1"><label class="text-xs font-bold text-slate-500 uppercase px-1">Badge</label><input type="text" name="badge" value="{{{{movie.badge}}}}"></div>
            <div class="space-y-1"><label class="text-xs font-bold text-slate-500 uppercase px-1">Category</label>
                <select name="category">
                    {{% for c in cats %}}<option value="{{{{c.name}}}}" {{% if c.name == movie.category %}}selected{{% endif %}}>{{{{c.name}}}}</option>{{% endfor %}}
                </select>
            </div>

            <div id="btn-box" class="space-y-3 pt-6 border-t border-slate-800">
                <h4 class="text-blue-500 font-black uppercase text-xs tracking-widest mb-4">Manage Links</h4>
                {{% for l in movie.links %}}
                <div class="flex gap-3 relative group">
                    <input name="l_name[]" value="{{{{l.label}}}}" placeholder="Label" class="l-name-field">
                    <input name="l_url[]" value="{{{{l.url}}}}" placeholder="URL" class="l-url-field">
                    <button type="button" onclick="this.parentElement.remove()" class="text-red-500"><i class="fa fa-times"></i></button>
                </div>
                {{% endfor %}}
            </div>

            <div class="mt-6 p-4 border border-blue-500/20 bg-blue-500/5 rounded-2xl">
                <button type="button" onclick="loadToTextarea()" class="text-[10px] text-slate-400 hover:text-blue-400 font-bold uppercase transition mb-2">Sync Links to Area</button>
                <textarea id="multi-link-area" rows="4" class="text-xs" placeholder="Label - URL"></textarea>
                <button type="button" onclick="processMultiLinks()" class="mt-2 bg-blue-600/20 text-blue-400 border border-blue-500/30 px-4 py-2 rounded-xl text-[10px] font-bold uppercase hover:bg-blue-600 hover:text-white transition">Process</button>
            </div>

            <button type="button" onclick="addL()" class="text-blue-400 font-bold text-xs uppercase hover:underline tracking-widest mt-2">+ Add More Link</button>
            <button type="submit" class="bg-blue-600 w-full py-4 rounded-xl font-bold uppercase tracking-widest mt-6">Update Database</button>
            <a href="/admin" class="block text-center mt-4 text-slate-500 font-bold text-xs uppercase">Discard Changes</a>
        </form>
    </div>
    <script>
        function addL(label = '', url = ''){{
            const b = document.getElementById('btn-box');
            const d = document.createElement('div');
            d.className = "flex gap-3 p-2 glass rounded-xl border border-white/5 mt-2 relative group";
            d.innerHTML = `
                <input type="text" name="l_name[]" placeholder="Label" required class="text-sm w-full l-name-field" value="${{label}}">
                <input type="text" name="l_url[]" placeholder="URL" required class="text-sm w-full l-url-field" value="${{url}}">
                <button type="button" onclick="this.parentElement.remove()" class="text-red-500 p-2"><i class="fa fa-times"></i></button>
            `;
            b.appendChild(d);
        }}

        function processMultiLinks() {{
            const area = document.getElementById('multi-link-area');
            const lines = area.value.split('\\n');
            lines.forEach(line => {{
                if(line.includes('-')){{
                    const parts = line.split('-');
                    const label = parts[0].trim();
                    const url = parts.slice(1).join('-').trim();
                    if(label && url) addL(label, url);
                }}
            }});
            area.value = '';
        }}

        function loadToTextarea() {{
            const names = document.querySelectorAll('.l-name-field');
            const urls = document.querySelectorAll('.l-url-field');
            let content = "";
            for(let i=0; i<names.length; i++){{
                if(names[i].value && urls[i].value) content += names[i].value + " - " + urls[i].value + "\\n";
            }}
            document.getElementById('multi-link-area').value = content.trim();
        }}
        
        const editForm = document.getElementById('edit-form');
        if(editForm) {{
            editForm.onsubmit = function(e) {{
                e.preventDefault();
                const formData = new FormData(editForm);
                const xhr = new XMLHttpRequest();
                document.getElementById('upload-status').style.display = 'block';
                showGlobalLoader();
                xhr.upload.addEventListener('progress', function(e) {{
                    if (e.lengthComputable) {{
                        const percent = Math.round((e.loaded / e.total) * 100);
                        document.getElementById('progress-bar').style.width = percent + '%';
                        document.getElementById('progress-percent').innerText = percent + '%';
                        document.getElementById('progress-text').innerText = 'Updating: ' + percent + '%';
                    }}
                }});
                xhr.onreadystatechange = function() {{
                    if (xhr.readyState == 4 && xhr.status == 200) window.location.href = '/admin';
                }};
                xhr.open('POST', '/admin/edit/{id}', true);
                xhr.send(formData);
            }};
        }}
    </script>
    </body></html>
    """
    return render_template_string(html, movie=movie, cats=cats)

@app.route('/admin/delete/<id>')
def delete_movie(id):
    if not session.get('admin'): return redirect('/admin/wp')
    movies_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

@app.errorhandler(404)
def page_not_found(e):
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
