import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

# --- Flask App Handler ---
app = Flask(__name__)
app.secret_key = "dramaworld_premium_ultra_fix_v20"

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

# --- Config Loader (Error Proof) ---
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
            "help_text": "Join our telegram channel for help.",
            "channel_link": "https://t.me/yourchannel",
            "ads": {"header": "", "middle": "", "footer": "", "native": "", "popunder": "", "socialbar": "", "banner": ""}
        }
        settings_col.insert_one(conf)
    
    # Nested key safety check
    if "ads" not in conf:
        conf["ads"] = {"header": "", "middle": "", "footer": "", "native": "", "popunder": "", "socialbar": "", "banner": ""}
    
    # Ensure every single ad slot exists
    ad_slots = ["header", "middle", "footer", "native", "popunder", "socialbar", "banner"]
    for slot in ad_slots:
        if slot not in conf["ads"]:
            conf["ads"][slot] = ""
            
    return conf

# --- UI Styles (Ultra Premium CSS) ---
CSS = """
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;900&display=swap');
    body { font-family: 'Outfit', sans-serif; background-color: #02040a; color: #e2e8f0; margin:0; }
    .glass { background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.05); }
    .movie-card { transition: 0.4s; border: 1px solid rgba(255,255,255,0.05); border-radius: 1.5rem; overflow: hidden; background: #0f172a; }
    .movie-card:hover { transform: translateY(-10px); border-color: #3b82f6; box-shadow: 0 20px 40px -15px rgba(59, 130, 246, 0.5); }
    .slider-box { position: relative; width: 100%; height: 230px; overflow: hidden; border-radius: 30px; }
    @media(min-width: 768px) { .slider-box { height: 480px; } }
    .slide-img { display: none; width: 100%; height: 100%; object-fit: cover; animation: fade 1.5s ease; }
    .slide-active { display: block; }
    @keyframes fade { from { opacity: 0; } to { opacity: 1; } }
    input, select, textarea { background: #0f172a !important; color: white !important; border: 1px solid #1e293b !important; border-radius: 12px; padding: 12px; outline: none; width: 100%; }
    .footer-nav { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); width: 92%; max-width: 450px; height: 70px; border-radius: 35px; z-index: 1000; border: 1px solid rgba(59, 130, 246, 0.3); display: flex; justify-content: space-around; align-items: center; box-shadow: 0 20px 50px rgba(0,0,0,0.8); }
    .f-item { display: flex; flex-direction: column; align-items: center; color: #94a3b8; font-weight: bold; font-size: 11px; transition: 0.3s; text-decoration: none; }
    .f-item:hover, .f-item.active { color: #3b82f6; }
    .f-item i { font-size: 22px; margin-bottom: 2px; }
    .sidebar-link { display: flex; align-items: center; gap: 10px; padding: 14px 20px; border-radius: 14px; transition: 0.3s; color: #94a3b8; font-weight: 600; text-decoration: none; }
    .sidebar-link:hover, .sidebar-link.active { background: #3b82f6; color: white; }
</style>
"""

# --- USER NAV & FOOTER COMPONENT ---
def get_user_header(conf):
    user_area = '<a href="/login" class="bg-blue-600 px-5 py-2 rounded-full text-xs font-bold text-white shadow-lg text-decoration-none">LOGIN</a>'
    if 'user_id' in session:
        user_area = '<a href="/profile" class="text-blue-400 font-bold flex items-center gap-2 text-decoration-none"><i class="fa fa-user-circle text-2xl"></i> <span class="hidden md:inline">' + session.get("user_name") + '</span></a>'
    
    return """
    <nav class="glass sticky top-0 z-50 px-4 md:px-10 py-4 flex justify-between items-center border-b border-white/5">
        <a href="/" class="flex items-center gap-2 text-decoration-none">
            <img src='""" + conf['logo_url'] + """' class="h-8 md:h-11">
            <span class="text-xl md:text-2xl font-black text-blue-500 uppercase italic tracking-tighter">""" + conf['site_name'] + """</span>
        </a>
        <div class="flex items-center gap-6">
            <form action="/" method="GET" class="hidden md:flex bg-slate-900 rounded-full px-4 py-1 border border-slate-800">
                <input type="text" name="search" placeholder="Search..." class="bg-transparent border-none outline-none text-sm w-48 p-1">
                <button type="submit" class="text-slate-500"><i class="fa fa-search"></i></button>
            </form>
            """ + user_area + """
        </div>
    </nav>
    """

def get_user_footer():
    mail_link = ""
    if 'user_id' in session:
        mail_link = '<a href="/mail" class="f-item"><i class="fa fa-envelope"></i><span>MAIL 📬</span></a>'
    
    return """
    <div class="h-28"></div>
    <div class="glass footer-nav">
        <a href="/" class="f-item"><i class="fa fa-home"></i><span>HOME 🏠</span></a>
        <a href="/help" class="f-item"><i class="fa fa-question-circle"></i><span>HELP 🆘</span></a>
        <a href="/request" class="f-item"><i class="fa fa-paper-plane"></i><span>REQUEST 🚀</span></a>
        """ + mail_link + """
    </div>
    """

# --- USER PANEL ROUTES ---

@app.route('/')
def index():
    conf = get_config()
    search = request.args.get('search')
    
    if search:
        movies = list(movies_col.find({"name": {"$regex": search, "$options": "i"}}))
        grouped_movies = {"Search Results": movies}
        slider_movies = []
    else:
        all_cats = list(categories_col.find())
        grouped_movies = {cat['name']: list(movies_col.find({"category": cat['name']}).sort("_id", -1)) for cat in all_cats}
        slider_movies = list(movies_col.find().sort("_id", -1).limit(int(conf['slider_limit'])))

    html = CSS + conf['ads']['popunder'] + conf['ads']['socialbar'] + get_user_header(conf) + """
    <div class="container mx-auto px-4 py-6">
        <div class="mb-6 text-center">""" + conf['ads']['header'] + """</div>
        
        {% if slider_movies and not request.args.get('search') %}
        <div class="slider-box mb-12 shadow-2xl">
            {% for sm in slider_movies %}
            <a href="/movie/{{ sm._id }}"><img src="{{ sm.poster }}" class="slide-img"></a>
            {% endfor %}
        </div>
        {% endif %}

        <div class="mb-8 text-center">""" + conf['ads']['middle'] + """</div>

        {% for cat_name, ms in grouped_movies.items() %}
            {% if ms %}
            <div class="mb-12">
                <h2 class="text-xl font-bold mb-6 flex items-center gap-3"><span class="w-2 h-8 bg-blue-600 rounded-full shadow-[0_0_15px_#3b82f6]"></span> {{ cat_name }}</h2>
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
                    {% for m in ms %}
                    <div class="movie-card relative cursor-pointer" onclick="location.href='/movie/{{ m._id }}'">
                        <img src="{{ m.poster }}" class="w-full h-64 md:h-80 object-cover">
                        <div class="absolute top-3 left-3 bg-blue-600 text-[10px] font-bold px-3 py-1 rounded-full uppercase border border-white/20">{{ m.badge }}</div>
                        <div class="p-4 bg-slate-900/90 backdrop-blur-md"><h3 class="font-bold text-sm truncate uppercase italic tracking-tighter">{{ m.name }}</h3></div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
        {% endfor %}

        <div class="mt-10 text-center">""" + conf['ads']['footer'] + """</div>
        <div class="text-center mt-4">""" + conf['ads']['native'] + """</div>
    </div>
    """ + get_user_footer() + """
    <script>
        let sIdx = 0; const slides = document.querySelectorAll('.slide-img');
        if(slides.length > 0){
            slides[0].classList.add('slide-active');
            setInterval(() => {
                slides[sIdx].classList.remove('slide-active');
                sIdx = (sIdx + 1) % slides.length;
                slides[sIdx].classList.add('slide-active');
            }, 5000);
        }
    </script>
    """
    return render_template_string(html, slider_movies=slider_movies, grouped_movies=grouped_movies, conf=conf)

@app.route('/movie/<id>')
def movie_details(id):
    conf = get_config()
    movie = movies_col.find_one({"_id": ObjectId(id)})
    if not movie: return redirect('/')
    
    html = CSS + get_user_header(conf) + """
    <div class="container mx-auto px-4 py-10">
        <div class="flex flex-col md:flex-row gap-10">
            <div class="w-full md:w-80"><img src="{{ movie.poster }}" class="w-full rounded-[2.5rem] shadow-2xl border-4 border-slate-900"></div>
            <div class="flex-1">
                <span class="bg-blue-600 px-5 py-1 rounded-full text-xs font-bold uppercase shadow-lg">{{ movie.badge }}</span>
                <h1 class="text-4xl md:text-5xl font-black mt-4 mb-2 italic tracking-tighter uppercase leading-tight">{{ movie.name }}</h1>
                <p class="text-blue-500 font-bold mb-8 uppercase text-sm tracking-widest">{{ movie.category }}</p>
                
                <div class="glass p-8 rounded-[2rem] border border-blue-500/20 shadow-2xl">
                    <h3 class="text-xl font-bold mb-8 flex items-center gap-3 text-white border-b border-white/5 pb-4">
                        <i class="fa fa-play-circle text-blue-500 text-3xl"></i> WATCH OR DOWNLOAD LINKS
                    </h3>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {% for link in movie.links %}
                        <a href="{{ link.url }}" target="_blank" class="bg-blue-600 hover:bg-blue-700 text-white text-center py-4 rounded-2xl font-bold transition shadow-xl border border-white/10 uppercase text-decoration-none">
                             📥 {{ link.label }}
                        </a>
                        {% endfor %}
                    </div>
                </div>
                <div class="mt-8 text-center">""" + conf['ads']['native'] + """</div>
            </div>
        </div>
    </div>
    """ + get_user_footer()
    return render_template_string(html, movie=movie, conf=conf)

@app.route('/help')
def help_page():
    conf = get_config()
    html = CSS + get_user_header(conf) + """
    <div class="container mx-auto px-4 py-10 text-center">
        <div class="glass p-10 md:p-20 rounded-[3.5rem] max-w-4xl mx-auto shadow-2xl border-t-4 border-blue-600">
            <img src="{{conf.logo_url}}" class="h-24 mx-auto mb-8 drop-shadow-2xl">
            <h1 class="text-4xl font-black mb-6 uppercase italic text-blue-500">Need Help?</h1>
            <p class="text-slate-400 text-lg mb-12 leading-relaxed">{{conf.help_text}}</p>
            <a href="{{conf.channel_link}}" target="_blank" class="bg-blue-600 hover:bg-blue-700 text-white px-12 py-5 rounded-2xl font-bold text-lg shadow-2xl inline-flex items-center gap-3 transition text-decoration-none">
                <i class="fa fa-paper-plane"></i> JOIN OUR CHANNEL
            </a>
        </div>
    </div>
    """ + get_user_footer()
    return render_template_string(html, conf=conf)

# --- AUTH SYSTEM ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name, user, pw = request.form.get('name'), request.form.get('user'), request.form.get('pass')
        if not users_col.find_one({"user": user}):
            uid = "DW" + str(ObjectId())[-6:].upper()
            users_col.insert_one({"uid": uid, "name": name, "user": user, "pass": pw})
            flash("Success! Please Login.")
            return redirect('/login')
        flash("Username exists!")
    
    html = CSS + """
    <body class="flex items-center justify-center min-h-screen p-4">
        <form method="POST" class="glass p-10 rounded-[2.5rem] w-full max-w-md space-y-6 shadow-2xl border-t-4 border-blue-600">
            <h2 class="text-3xl font-black text-center text-blue-500 uppercase italic">Register</h2>
            {% with msgs = get_flashed_messages() %}{% if msgs %}<p class="text-red-500 text-xs text-center font-bold">{{msgs[0]}}</p>{% endif %}{% endwith %}
            <input type="text" name="name" placeholder="Full Name" required>
            <input type="text" name="user" placeholder="Username" required>
            <input type="password" name="pass" placeholder="Password" required>
            <button class="bg-blue-600 w-full py-4 rounded-2xl font-bold text-white shadow-xl uppercase">Sign Up</button>
            <p class="text-center text-sm">Already have an account? <a href="/login" class="text-blue-500 font-bold">Login</a></p>
        </form>
    </body>
    """
    return render_template_string(html)

@app.route('/login', methods=['GET', 'POST'])
def login():
    conf = get_config()
    if request.method == 'POST':
        user, pw = request.form.get('user'), request.form.get('pass')
        if user == conf['admin_user'] and pw == conf['admin_pass']:
            session['admin'] = True
            return redirect('/admin')
        u = users_col.find_one({"user": user, "pass": pw})
        if u:
            session['user_id'] = str(u['_id'])
            session['user_name'] = u['name']
            return redirect('/')
        flash("Invalid Credentials!")

    html = CSS + """
    <body class="flex items-center justify-center min-h-screen p-4">
        <form method="POST" class="glass p-10 rounded-[2.5rem] w-full max-w-md space-y-6 shadow-2xl border-t-4 border-blue-600">
            <h2 class="text-3xl font-black text-center text-blue-500 uppercase italic">Login</h2>
            {% with msgs = get_flashed_messages() %}{% if msgs %}<p class="text-red-500 text-xs text-center font-bold">{{msgs[0]}}</p>{% endif %}{% endwith %}
            <input type="text" name="user" placeholder="Username" required>
            <input type="password" name="pass" placeholder="Password" required>
            <button class="bg-blue-600 w-full py-4 rounded-2xl font-bold text-white shadow-xl uppercase">Access Account</button>
            <p class="text-center text-sm text-slate-400">New User? <a href="/register" class="text-blue-500 font-bold">Sign Up</a></p>
        </form>
    </body>
    """
    return render_template_string(html)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- REQUEST & MAIL ---

@app.route('/request', methods=['GET', 'POST'])
def request_movie():
    if 'user_id' not in session: return redirect('/login')
    conf = get_config()
    if request.method == 'POST':
        requests_col.insert_one({"user_id": session['user_id'], "user_name": session['user_name'], "movie_name": request.form.get('movie_name'), "email": request.form.get('email'), "status": "Pending", "date": datetime.now().strftime("%d %b %Y")})
        flash("Submitted!")
        return redirect('/profile')
    
    html = CSS + get_user_header(conf) + """
    <div class="container mx-auto px-4 py-10">
        <form method="POST" class="glass p-10 rounded-[3rem] max-w-xl mx-auto space-y-6 border-t-4 border-blue-600 shadow-2xl">
            <h2 class="text-3xl font-black text-blue-500 uppercase italic">Request Movie 🚀</h2>
            <input name="movie_name" placeholder="Movie Full Name" required>
            <input value='""" + session['user_name'] + """' readonly class="opacity-50">
            <input name="email" placeholder="Your Email" required>
            <button class="bg-blue-600 w-full py-4 rounded-2xl font-bold text-white shadow-xl">SUBMIT</button>
        </form>
    </div>
    """ + get_user_footer()
    return render_template_string(html)

@app.route('/mail')
def user_mail():
    if 'user_id' not in session: return redirect('/login')
    conf = get_config()
    notifs = list(notif_col.find({"user_id": session['user_id']}).sort("_id", -1))
    html = CSS + get_user_header(conf) + """
    <div class="container mx-auto px-4 py-10 max-w-4xl">
        <h2 class="text-2xl font-black mb-8 text-blue-500 uppercase italic">📬 MailBox</h2>
        <div class="space-y-4">
            {% for n in notifs %}
            <div class="glass p-6 rounded-3xl border-l-4 border-blue-600 shadow-xl">
                <p class="text-sm font-semibold mb-2 leading-relaxed">{{n.message}}</p>
                <p class="text-[10px] text-slate-500 uppercase font-bold">{{n.date}}</p>
            </div>
            {% else %}
                <p class="text-slate-500 italic">No notifications found.</p>
            {% endfor %}
        </div>
    </div>
    """ + get_user_footer()
    return render_template_string(html, notifs=notifs)

@app.route('/profile')
def profile():
    if 'user_id' not in session: return redirect('/login')
    conf = get_config()
    u = users_col.find_one({"_id": ObjectId(session['user_id'])})
    html = CSS + get_user_header(conf) + """
    <div class="container mx-auto px-4 py-10 text-center">
        <div class="glass p-12 rounded-[3.5rem] max-w-md mx-auto border-b-4 border-blue-600 shadow-2xl">
            <div class="w-20 h-20 bg-blue-600 rounded-full mx-auto flex items-center justify-center text-3xl font-black mb-4">""" + u['name'][0] + """</div>
            <h2 class="text-2xl font-black">""" + u['name'] + """</h2>
            <p class="text-blue-500 font-bold text-xs mt-2 uppercase tracking-widest">User ID: """ + u['uid'] + """</p>
            <div class="mt-8 pt-6 border-t border-white/5 space-y-4">
                <a href="/mail" class="block bg-slate-800 py-3 rounded-xl font-bold text-sm text-decoration-none text-white">My Notifications</a>
                <a href="/logout" class="block text-red-500 font-black text-xs uppercase tracking-widest text-decoration-none">Logout</a>
            </div>
        </div>
    </div>
    """ + get_user_footer()
    return render_template_string(html)

# --- ADMIN PANEL ROUTES ---

def get_admin_sidebar(active="dash"):
    return """
    <div class="w-full md:w-72 bg-[#080c14] border-r border-slate-900 p-8 flex flex-col shadow-2xl h-full sticky top-0">
        <h2 class="text-2xl font-black text-blue-500 mb-10 italic uppercase">Admin Panel</h2>
        <nav class="space-y-2 flex-grow">
            <a href="/admin" class="sidebar-link active"><i class="fa fa-dashboard"></i> Dashboard</a>
            <a href="/admin/requests" class="sidebar-link"><i class="fa fa-paper-plane"></i> User Requests</a>
            <a href="/admin/add" class="sidebar-link"><i class="fa fa-plus-circle"></i> Add Movie</a>
            <a href="/admin/settings" class="sidebar-link"><i class="fa fa-cog"></i> Settings</a>
            <a href="/logout" class="sidebar-link text-red-500 mt-20"><i class="fa fa-sign-out-alt"></i> Logout</a>
        </nav>
    </div>
    """

@app.route('/admin')
def admin_dash():
    if not session.get('admin'): return redirect('/login')
    search = request.args.get('search', '')
    query = {"name": {"$regex": search, "$options": "i"}} if search else {}
    movies = list(movies_col.find(query).sort("_id", -1))
    
    html = CSS + """
    <body class="flex flex-col md:flex-row min-h-screen">
        """ + get_admin_sidebar() + """
        <main class="flex-grow p-6 md:p-12">
            <div class="flex flex-col md:flex-row justify-between items-center mb-10 gap-4">
                <h1 class="text-3xl font-black uppercase tracking-tighter italic">Movie Management</h1>
                <form action="/admin" method="GET" class="flex bg-slate-900 rounded-2xl px-5 py-2 border border-slate-800 w-full md:w-96">
                    <input name="search" placeholder="Search movies..." class="bg-transparent border-none text-sm p-1" value='""" + search + """'>
                    <button type="submit" class="text-slate-500"><i class="fa fa-search"></i></button>
                </form>
            </div>
            <div class="glass rounded-[2.5rem] overflow-hidden">
                <table class="w-full text-left">
                    <thead class="bg-slate-900 text-slate-500 text-xs uppercase font-bold tracking-widest"><tr class="border-b border-white/5"><th class="p-6">Movie</th><th class="p-6">Category</th><th class="p-6 text-center">Action</th></tr></thead>
                    <tbody class="divide-y divide-slate-800">
                        {% for m in movies %}
                        <tr class="hover:bg-slate-800/50 transition">
                            <td class="p-6 flex items-center gap-4">
                                <img src="{{ m.poster }}" class="w-10 h-14 rounded-lg object-cover">
                                <span class="font-bold text-sm">{{ m.name }}</span>
                            </td>
                            <td class="p-6 text-xs text-blue-400 font-bold uppercase">{{ m.category }}</td>
                            <td class="p-6 text-center">
                                <a href="/admin/edit/{{ m._id }}" class="text-blue-500 mx-2 text-xl"><i class="fa fa-edit"></i></a>
                                <a href="/admin/delete/{{ m._id }}" class="text-red-500 mx-2 text-xl" onclick="return confirm('Delete?')"><i class="fa fa-trash"></i></a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </main>
    </body>
    """
    return render_template_string(html, movies=movies)

@app.route('/admin/requests', methods=['GET', 'POST'])
def admin_requests_page():
    if not session.get('admin'): return redirect('/login')
    if request.method == 'POST':
        rid, status, admin_text = request.form.get('req_id'), request.form.get('status'), request.form.get('admin_text')
        req = requests_col.find_one({"_id": ObjectId(rid)})
        if req:
            notif_col.insert_one({"user_id": req['user_id'], "message": "Regarding '" + req['movie_name'] + "': " + status + ". Admin Message: " + admin_text, "date": datetime.now().strftime("%d %b, %H:%M")})
            if status == "Uploaded/Done": requests_col.delete_one({"_id": ObjectId(rid)})
            else: requests_col.update_one({"_id": ObjectId(rid)}, {"$set": {"status": status}})
        return redirect('/admin/requests')

    reqs = list(requests_col.find().sort("_id", -1))
    html = CSS + """
    <body class="flex flex-col md:flex-row min-h-screen">
        """ + get_admin_sidebar() + """
        <main class="flex-grow p-6 md:p-12 space-y-6">
            <h1 class="text-3xl font-black mb-10 uppercase tracking-tighter italic">User Requests</h1>
            {% for r in reqs %}
            <div class="glass p-8 rounded-[2.5rem] flex flex-col md:flex-row justify-between items-center gap-6 shadow-xl">
                <div>
                    <h3 class="text-xl font-bold text-blue-500 uppercase">{{ r.movie_name }}</h3>
                    <p class="text-xs text-slate-400 font-bold mt-1 uppercase">From: {{ r.user_name }} | {{ r.date }} | {{ r.status }}</p>
                </div>
                <form method="POST" class="flex flex-col md:flex-row gap-2 w-full md:w-auto">
                    <input type="hidden" name="req_id" value="{{ r._id }}">
                    <input name="admin_text" placeholder="Note to user..." required class="text-xs w-full md:w-48">
                    <select name="status" class="text-xs w-full md:w-32"><option>Uploaded/Done</option><option>Rejected</option></select>
                    <button class="bg-blue-600 px-6 py-3 rounded-xl font-bold text-xs uppercase">Reply</button>
                </form>
            </div>
            {% endfor %}
        </main>
    </body>
    """
    return render_template_string(html, reqs=reqs)

@app.route('/admin/add', methods=['GET', 'POST'])
def admin_add_movie():
    if not session.get('admin'): return redirect('/login')
    cats = list(categories_col.find())
    if request.method == 'POST':
        labels, urls = request.form.getlist('l_name[]'), request.form.getlist('l_url[]')
        links = [{"label": labels[i], "url": urls[i]} for i in range(len(labels))]
        movies_col.insert_one({"name": request.form.get('name'), "poster": request.form.get('poster'), "badge": request.form.get('badge'), "category": request.form.get('category'), "links": links})
        return redirect('/admin')
    
    html = CSS + """
    <body class="flex flex-col md:flex-row min-h-screen">
        """ + get_admin_sidebar() + """
        <main class="flex-grow p-6 md:p-12">
            <form method="POST" class="glass p-10 rounded-[3rem] max-w-4xl mx-auto space-y-6 shadow-2xl">
                <h2 class="text-2xl font-black text-blue-500 uppercase italic">Add Movie</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <input name="name" placeholder="Movie Full Name" required>
                    <select name="category" required>
                        {% for c in cats %}<option value="{{ c.name }}">{{ c.name }}</option>{% endfor %}
                    </select>
                </div>
                <input name="poster" placeholder="Poster Image URL" required>
                <input name="badge" placeholder="Badge (e.g. 1080p Dual)">
                <div id="btn-box" class="space-y-3 pt-6 border-t border-slate-800"><label class="text-xs font-bold text-blue-500 uppercase">Links</label></div>
                <button type="button" onclick="addL()" class="text-blue-400 font-bold text-xs uppercase hover:underline tracking-widest">+ Add Download Link</button>
                <button class="w-full bg-blue-600 py-4 rounded-2xl font-bold uppercase tracking-widest">Publish</button>
            </form>
        </main>
        <script>
            function addL(){
                const b = document.getElementById('btn-box');
                const d = document.createElement('div');
                d.className = "flex gap-2";
                d.innerHTML = `<input name="l_name[]" placeholder="Label" required><input name="l_url[]" placeholder="URL" required>`;
                b.appendChild(d);
            } addL();
        </script>
    </body>
    """
    return render_template_string(html, cats=cats)

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings_page():
    if not session.get('admin'): return redirect('/login')
    conf = get_config(); cats = list(categories_col.find())
    if request.method == 'POST':
        if 'update_branding' in request.form:
            settings_col.update_one({"type": "config"}, {"$set": {"site_name": request.form.get('site_name'), "logo_url": request.form.get('logo_url'), "help_text": request.form.get('help_text'), "channel_link": request.form.get('channel_link'), "slider_limit": int(request.form.get('slider_limit', 5))}})
        elif 'add_cat' in request.form: categories_col.insert_one({"name": request.form.get('cat_name')})
        elif 'del_cat' in request.form: categories_col.delete_one({"_id": ObjectId(request.form.get('cat_id'))})
        elif 'update_ads' in request.form:
            ads = {k: request.form.get(k) for k in conf['ads'].keys()}
            settings_col.update_one({"type": "config"}, {"$set": {"ads": ads}})
        return redirect('/admin/settings')

    html = CSS + """
    <body class="flex flex-col md:flex-row min-h-screen">
        """ + get_admin_sidebar() + """
        <main class="flex-grow p-6 md:p-12 space-y-10">
            <h1 class="text-3xl font-black uppercase tracking-tighter italic">Global Settings</h1>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-10">
                <form method="POST" class="glass p-8 rounded-[2.5rem] space-y-4 shadow-2xl border-t-4 border-blue-600">
                    <h3 class="text-blue-500 font-bold uppercase text-xs border-b border-white/5 pb-2">Branding</h3>
                    <div class="space-y-1"><label class="text-[10px] uppercase font-bold text-slate-500">Site Name</label><input name="site_name" value="{{conf.site_name}}"></div>
                    <div class="space-y-1"><label class="text-[10px] uppercase font-bold text-slate-500">Logo URL</label><input name="logo_url" value="{{conf.logo_url}}"></div>
                    <textarea name="help_text" rows="3">{{conf.help_text}}</textarea>
                    <input name="channel_link" value="{{conf.channel_link}}" placeholder="Telegram">
                    <input type="number" name="slider_limit" value="{{conf.slider_limit}}">
                    <button name="update_branding" class="w-full bg-blue-600 py-3 rounded-xl font-bold uppercase tracking-widest">Update Site</button>
                </form>
                <form method="POST" class="glass p-8 rounded-[2.5rem] space-y-4 shadow-2xl border-t-4 border-green-600">
                    <h3 class="text-green-500 font-bold uppercase text-xs border-b border-white/5 pb-2">Genres</h3>
                    <div class="flex gap-2"><input name="cat_name" placeholder="New category"><button name="add_cat" class="bg-green-600 px-6 rounded-xl font-bold uppercase">ADD</button></div>
                    <div class="max-h-48 overflow-y-auto space-y-2 pt-2">
                        {% for c in cats %}<div class="flex justify-between items-center bg-slate-900 p-3 rounded-xl border border-white/5"><span>{{c.name}}</span><form method="POST" class="inline"><input type="hidden" name="cat_id" value="{{c._id}}"><button name="del_cat" class="text-red-500"><i class="fa fa-trash"></i></button></form></div>{% endfor %}
                    </div>
                </form>
            </div>
            <form method="POST" class="glass p-10 rounded-[3.5rem] space-y-8 shadow-2xl border-t-4 border-yellow-500">
                <h3 class="text-yellow-500 font-bold uppercase text-xs italic border-b border-white/5 pb-2">Ad Management (7 Slots)</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {% for k, v in conf.ads.items() %}<div class="space-y-1"><label class="text-[10px] uppercase font-bold text-slate-500 tracking-widest">{{k | upper}}</label><textarea name="{{k}}" rows="3">{{v}}</textarea></div>{% endfor %}
                </div>
                <button name="update_ads" class="bg-blue-600 px-12 py-4 rounded-xl font-bold uppercase shadow-2xl">Update System Ads</button>
            </form>
        </main>
    </body>
    """
    return render_template_string(html, conf=conf, cats=cats)

@app.route('/admin/edit/<id>', methods=['GET', 'POST'])
def edit_movie_page(id):
    if not session.get('admin'): return redirect('/login')
    movie = movies_col.find_one({"_id": ObjectId(id)})
    if request.method == 'POST':
        labels, urls = request.form.getlist('l_name[]'), request.form.getlist('l_url[]')
        links = [{"label": labels[i], "url": urls[i]} for i in range(len(labels))]
        movies_col.update_one({"_id": ObjectId(id)}, {"$set": {"name": request.form.get('name'), "poster": request.form.get('poster'), "badge": request.form.get('badge'), "category": request.form.get('category'), "links": links}})
        return redirect('/admin')
    
    html = CSS + """
    <body class="p-10"><form method="POST" class="glass p-10 max-w-2xl mx-auto space-y-4 rounded-3xl"><h2 class="text-xl font-black uppercase text-blue-500">Edit Entry</h2><input name="name" value="{{movie.name}}"><input name="poster" value="{{movie.poster}}"><input name="badge" value="{{movie.badge}}"><input name="category" value="{{movie.category}}"><div id="ec" class="space-y-2">{% for l in movie.links %}<div class="flex gap-2"><input name="l_name[]" value="{{l.label}}"><input name="l_url[]" value="{{l.url}}"></div>{% endfor %}</div><button class="bg-blue-600 w-full py-4 rounded-xl font-bold uppercase">Save</button></form></body>
    """
    return render_template_string(html, movie=movie)

@app.errorhandler(500)
def server_error(e):
    return "Internal Server Error: check log", 500

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
