import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

# Vercel Handler
app = Flask(__name__)
app.secret_key = "dramaworld_bd_secure_ultra_key"

# --- MongoDB Connection ---
MONGO_URI = "mongodb+srv://freelancermaruf1735:6XaThbuVG2zOUWm4@cluster0.ywwppvf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['dramaworld_db']
movies_col = db['movies']
settings_col = db['settings']
categories_col = db['categories']

# --- Database Initialization ---
def init_db():
    if not settings_col.find_one({"type": "config"}):
        settings_col.insert_one({
            "type": "config",
            "admin_user": "admin",
            "admin_pass": "admin123",
            "slider_limit": 5,
            "ads": {
                "popunder": "", "socialbar": "", "native": "", 
                "banner": "", "header": "", "footer": "", "middle": ""
            }
        })
    if categories_col.count_documents({}) == 0:
        for cat in ["Action", "Drama", "Horror"]:
            categories_col.insert_one({"name": cat})

init_db()

# --- CSS Style ---
CSS = """
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    body { font-family: 'Poppins', sans-serif; background-color: #050811; color: #e2e8f0; margin:0; }
    .glass { background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.05); }
    .movie-card { transition: 0.3s; border: 1px solid rgba(255,255,255,0.05); cursor: pointer; }
    .movie-card:hover { transform: translateY(-5px); border-color: #3b82f6; }
    .slider-box { position: relative; width: 100%; height: 220px; overflow: hidden; border-radius: 20px; }
    @media(min-width: 768px) { .slider-box { height: 450px; } }
    .slide-img { display: none; width: 100%; height: 100%; object-fit: cover; animation: fade 1s; }
    .slide-active { display: block; }
    @keyframes fade { from { opacity: 0; } to { opacity: 1; } }
    input, select, textarea { background: #0f172a !important; color: white !important; border: 1px solid #1e293b !important; border-radius: 10px; padding: 10px; }
</style>
"""

# --- USER PANEL: HOME ---
HOME_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DramaWorld BD</title>
    """ + CSS + """
    {{ conf.ads.popunder | safe }}{{ conf.ads.socialbar | safe }}
</head>
<body>
    <nav class="glass sticky top-0 z-50 px-4 md:px-10 py-4 flex justify-between items-center shadow-2xl">
        <a href="/" class="text-2xl font-black text-blue-500 uppercase italic">DRAMA<span class="text-white">WORLD</span></a>
        <form action="/" method="GET" class="flex bg-slate-900 rounded-full px-4 py-1 border border-slate-800">
            <input type="text" name="search" placeholder="Search..." class="bg-transparent border-none outline-none text-sm w-32 md:w-64">
            <button type="submit"><i class="fa fa-search text-slate-500"></i></button>
        </form>
    </nav>

    <div class="container mx-auto px-4 py-6">
        <div class="mb-4 text-center">{{ conf.ads.header | safe }}</div>

        {% if slider_movies and not request.args.get('search') %}
        <div class="slider-box mb-10 shadow-2xl">
            {% for sm in slider_movies %}<a href="/movie/{{ sm._id }}"><img src="{{ sm.poster }}" class="slide-img"></a>{% endfor %}
        </div>
        {% endif %}

        <div class="mb-8 text-center">{{ conf.ads.middle | safe }}</div>

        <!-- Home Content Grouped by Category -->
        {% for cat_name, movies in grouped_movies.items() %}
            {% if movies %}
            <div class="mb-12">
                <h2 class="text-xl font-bold mb-6 flex items-center gap-3"><span class="w-1.5 h-8 bg-blue-600 rounded-full"></span> {{ cat_name }}</h2>
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 md:gap-6">
                    {% for m in movies %}
                    <div class="glass movie-card rounded-2xl overflow-hidden relative" onclick="location.href='/movie/{{ m._id }}'">
                        <img src="{{ m.poster }}" class="w-full h-56 md:h-72 object-cover">
                        <div class="absolute top-2 left-2 bg-blue-600 text-[10px] font-bold px-2 py-1 rounded-full uppercase">{{ m.badge }}</div>
                        <div class="p-3"><h3 class="font-bold text-xs h-8 overflow-hidden leading-tight">{{ m.name }}</h3></div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
        {% endfor %}

        <div class="mt-10 text-center">{{ conf.ads.banner | safe }}</div>
        <footer class="mt-20 py-10 text-center border-t border-slate-900 text-slate-500 text-xs">
            {{ conf.ads.footer | safe }}<p>&copy; 2024 DramaWorld BD</p>
        </footer>
    </div>
    <script>
        let sIdx = 0; const slides = document.querySelectorAll('.slide-img');
        function showS() { if(slides.length > 0){ slides.forEach(s => s.classList.remove('slide-active')); sIdx = (sIdx + 1) % slides.length; slides[sIdx].classList.add('slide-active'); } }
        if(slides.length > 0) { slides[0].classList.add('slide-active'); setInterval(showS, 5000); }
    </script>
</body>
</html>
"""

# --- USER PANEL: DETAILS ---
DETAILS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ movie.name }} - DramaWorld</title>""" + CSS + """
</head>
<body>
    <nav class="glass sticky top-0 z-50 px-4 md:px-10 py-4"><a href="/" class="text-2xl font-black text-blue-500 tracking-tighter">DRAMA<span class="text-white">WORLD</span></a></nav>
    <div class="container mx-auto px-4 py-10">
        <div class="flex flex-col md:flex-row gap-10">
            <div class="w-full md:w-1/3"><img src="{{ movie.poster }}" class="w-full rounded-3xl shadow-2xl border border-slate-800"></div>
            <div class="w-full md:w-2/3">
                <span class="bg-blue-600 px-4 py-1 rounded-full text-xs font-bold uppercase">{{ movie.badge }}</span>
                <h1 class="text-4xl font-bold mt-4 mb-2">{{ movie.name }}</h1>
                <p class="text-blue-400 font-bold mb-8 italic uppercase tracking-widest text-sm">{{ movie.category }}</p>
                <div class="glass p-8 rounded-3xl border border-blue-500/10">
                    <h3 class="text-xl font-bold mb-8 border-b border-slate-800 pb-3 flex items-center gap-2"><i class="fa fa-play-circle text-blue-500"></i> LINKS</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {% for link in movie.links %}
                        <a href="{{ link.url }}" target="_blank" class="bg-blue-600 hover:bg-blue-700 text-white text-center py-4 rounded-2xl font-bold transition"> {{ link.label }} </a>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
        <div class="mt-12 text-center">{{ conf.ads.native | safe }}</div>
    </div>
</body>
</html>
"""

# --- ADMIN PANEL: LOGIN ---
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Admin Login</title>""" + CSS + """</head>
<body class="bg-[#02040a] flex items-center justify-center min-h-screen">
    <form method="POST" class="glass p-10 rounded-3xl w-full max-w-md space-y-6">
        <h2 class="text-2xl font-bold text-center text-blue-500 uppercase">Admin Login</h2>
        {% with messages = get_flashed_messages() %}{% if messages %}<p class="text-red-500 text-xs text-center">{{ messages[0] }}</p>{% endif %}{% endwith %}
        <input type="text" name="user" placeholder="Username" class="w-full outline-none" required>
        <input type="password" name="pass" placeholder="Password" class="w-full outline-none" required>
        <button type="submit" class="w-full bg-blue-600 py-3 rounded-xl font-bold">LOGIN</button>
    </form>
</body>
</html>
"""

# --- ADMIN PANEL: DASHBOARD ---
ADMIN_LAYOUT = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><title>Admin Panel</title>""" + CSS + """
</head>
<body class="bg-[#02040a] flex flex-col md:flex-row min-h-screen">
    <div class="w-full md:w-72 bg-[#080c14] border-r border-slate-900 p-8 shadow-2xl">
        <h2 class="text-2xl font-black mb-10 text-blue-500 uppercase italic">Admin</h2>
        <nav class="space-y-4">
            <a href="/admin" class="flex items-center gap-4 p-4 rounded-2xl hover:bg-slate-800 transition">Dashboard</a>
            <a href="/admin/add" class="flex items-center gap-4 p-4 rounded-2xl bg-blue-600 text-white shadow-xl">Add Movie</a>
            <a href="/admin/settings" class="flex items-center gap-4 p-4 rounded-2xl hover:bg-slate-800 transition">Ads & Profile</a>
            <a href="/logout" class="flex items-center gap-4 p-4 rounded-2xl text-red-500 hover:bg-red-500/10 transition mt-10">Logout</a>
        </nav>
    </div>
    <main class="flex-grow p-6 md:p-12">{% block content %}{% endblock %}</main>
</body>
</html>
"""

# --- ROUTES ---

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
        grouped_movies = {}
        for cat in all_cats:
            grouped_movies[cat['name']] = list(movies_col.find({"category": cat['name']}).sort("_id", -1))
        movies = list(movies_col.find().sort("_id", -1))
        slider_movies = movies[:conf.get('slider_limit', 5)]
    return render_template_string(HOME_HTML, movies=movies, slider_movies=slider_movies, grouped_movies=grouped_movies, conf=conf)

@app.route('/movie/<id>')
def movie_details(id):
    conf = get_config()
    movie = movies_col.find_one({"_id": ObjectId(id)})
    if not movie: return redirect('/')
    return render_template_string(DETAILS_HTML, movie=movie, conf=conf)

@app.route('/login', methods=['GET', 'POST'])
def login():
    conf = get_config()
    if request.method == 'POST':
        if request.form.get('user') == conf['admin_user'] and request.form.get('pass') == conf['admin_pass']:
            session['logged_in'] = True
            return redirect('/admin')
        flash("Invalid Credentials")
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/admin')
def admin_dash():
    if not session.get('logged_in'): return redirect('/login')
    movies = list(movies_col.find().sort("_id", -1))
    return render_template_string(ADMIN_LAYOUT.replace('{% block content %}{% endblock %}', """
        <div class="flex justify-between items-center mb-10"><h1 class="text-3xl font-bold">Manage Movies</h1></div>
        <div class="glass rounded-3xl overflow-hidden shadow-2xl">
            <table class="w-full text-left">
                <thead class="bg-slate-900/50 text-slate-500 text-xs uppercase tracking-widest">
                    <tr><th class="p-6">Movie</th><th class="p-6">Category</th><th class="p-6">Action</th></tr>
                </thead>
                <tbody class="divide-y divide-slate-900">
                    {% for m in movies %}
                    <tr class="hover:bg-slate-800/30 transition">
                        <td class="p-6 flex items-center gap-4">
                            <img src="{{ m.poster }}" class="w-10 h-14 rounded shadow-lg object-cover">
                            <span class="font-bold text-sm">{{ m.name }}</span>
                        </td>
                        <td class="p-6 text-xs text-blue-400 font-bold uppercase">{{ m.category }}</td>
                        <td class="p-6 flex gap-6">
                            <a href="/admin/edit/{{ m._id }}" class="text-blue-500"><i class="fa fa-edit"></i></a>
                            <a href="/admin/delete/{{ m._id }}" class="text-red-500" onclick="return confirm('Delete?')"><i class="fa fa-trash"></i></a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    """), movies=movies)

@app.route('/admin/add', methods=['GET', 'POST'])
def add_movie():
    if not session.get('logged_in'): return redirect('/login')
    cats = list(categories_col.find())
    if request.method == 'POST':
        labels, urls = request.form.getlist('l_name[]'), request.form.getlist('l_url[]')
        links = [{"label": labels[i], "url": urls[i]} for i in range(len(labels))]
        movies_col.insert_one({
            "name": request.form.get('name'), "poster": request.form.get('poster'),
            "badge": request.form.get('badge'), "category": request.form.get('category'), "links": links
        })
        return redirect('/admin')
    return render_template_string(FORM_HTML, movie=None, cats=cats)

@app.route('/admin/edit/<id>', methods=['GET', 'POST'])
def edit_movie(id):
    if not session.get('logged_in'): return redirect('/login')
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
    return render_template_string(FORM_HTML, movie=movie, cats=cats)

@app.route('/admin/delete/<id>')
def delete_movie(id):
    if not session.get('logged_in'): return redirect('/login')
    movies_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

@app.route('/admin/settings', methods=['GET', 'POST'])
def settings():
    if not session.get('logged_in'): return redirect('/login')
    conf = get_config()
    cats = list(categories_col.find())
    if request.method == 'POST':
        if 'update_ads' in request.form:
            ads = {k: request.form.get(k) for k in conf['ads'].keys()}
            settings_col.update_one({"type": "config"}, {"$set": {"ads": ads, "slider_limit": int(request.form.get('slider_limit', 5))}})
        elif 'update_profile' in request.form:
            settings_col.update_one({"type": "config"}, {"$set": {"admin_user": request.form.get('admin_user'), "admin_pass": request.form.get('admin_pass')}})
        elif 'add_cat' in request.form:
            categories_col.insert_one({"name": request.form.get('cat_name')})
        elif 'del_cat' in request.form:
            categories_col.delete_one({"_id": ObjectId(request.form.get('cat_id'))})
        return redirect('/admin/settings')
    return render_template_string(SETTINGS_HTML, conf=conf, cats=cats)

# --- DB Helper ---
def get_config():
    return settings_col.find_one({"type": "config"})

# --- FORM & SETTINGS HTML ---
FORM_HTML = ADMIN_LAYOUT.replace('{% block content %}{% endblock %}', """
<div class="max-w-4xl mx-auto glass p-8 md:p-12 rounded-3xl shadow-2xl">
    <h2 class="text-2xl font-bold mb-10 text-blue-500 uppercase">{{ 'Edit' if movie else 'Add New' }} Movie</h2>
    <form method="POST" class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <input type="text" name="name" value="{{ movie.name if movie else '' }}" placeholder="Movie Name" class="w-full outline-none" required>
            <select name="category" class="w-full outline-none" required>
                {% for c in cats %}<option value="{{ c.name }}" {{ 'selected' if movie and movie.category == c.name }}>{{ c.name }}</option>{% endfor %}
            </select>
        </div>
        <input type="text" name="poster" value="{{ movie.poster if movie else '' }}" placeholder="Poster URL" class="w-full outline-none" required>
        <input type="text" name="badge" value="{{ movie.badge if movie else '' }}" placeholder="Badge (Poster Text, e.g. HD, 4K)" class="w-full outline-none">
        
        <div id="btn-container" class="space-y-4 pt-6">
            <label class="block text-xs font-bold text-blue-500">UNLIMITED DOWNLOAD BUTTONS</label>
            {% if movie %}{% for l in movie.links %}
            <div class="flex gap-4"><input type="text" name="l_name[]" value="{{ l.label }}" class="w-1/3 p-3 rounded-xl text-sm"><input type="text" name="l_url[]" value="{{ l.url }}" class="w-2/3 p-3 rounded-xl text-sm"></div>
            {% endfor %}{% endif %}
        </div>
        <button type="button" onclick="addL()" class="text-blue-500 text-xs font-bold">+ ADD BUTTON</button>
        <div class="pt-10 flex gap-4"><button type="submit" class="bg-blue-600 px-12 py-4 rounded-2xl font-bold shadow-xl transition">SAVE MOVIE</button></div>
    </form>
</div>
<script>
    function addL() {
        const container = document.getElementById('btn-container');
        const d = document.createElement('div'); d.className = "flex gap-4";
        d.innerHTML = `<input type="text" name="l_name[]" class="w-1/3 p-3 rounded-xl text-sm" placeholder="Name" required><input type="text" name="l_url[]" class="w-2/3 p-3 rounded-xl text-sm" placeholder="URL" required>`;
        container.appendChild(d);
    }
</script>
""")

SETTINGS_HTML = ADMIN_LAYOUT.replace('{% block content %}{% endblock %}', """
<div class="space-y-10">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
        <!-- Profile & Slider Limit -->
        <form method="POST" class="glass p-8 rounded-3xl space-y-4">
            <h3 class="font-bold text-blue-500">Admin Profile & Slider</h3>
            <input type="text" name="admin_user" value="{{ conf.admin_user }}" class="w-full outline-none" placeholder="Username">
            <input type="text" name="admin_pass" value="{{ conf.admin_pass }}" class="w-full outline-none" placeholder="Password">
            <label class="text-[10px] text-slate-500 uppercase">Slider Limit (Max Posts in Slider)</label>
            <input type="number" name="slider_limit" value="{{ conf.slider_limit }}" class="w-full outline-none">
            <button type="submit" name="update_profile" class="w-full bg-blue-600 py-3 rounded-xl font-bold">Update Profile</button>
        </form>

        <!-- Category Management -->
        <div class="glass p-8 rounded-3xl space-y-4">
            <h3 class="font-bold text-green-500">Manage Categories</h3>
            <form method="POST" class="flex gap-2">
                <input type="text" name="cat_name" placeholder="Category Name" class="w-full text-xs" required>
                <button type="submit" name="add_cat" class="bg-green-600 px-4 rounded-xl text-xs font-bold">Add</button>
            </form>
            <div class="space-y-2 h-40 overflow-y-auto pt-4">
                {% for c in cats %}
                <form method="POST" class="flex justify-between items-center bg-slate-900/50 p-3 rounded-xl">
                    <span class="text-sm">{{ c.name }}</span>
                    <input type="hidden" name="cat_id" value="{{ c._id }}">
                    <button type="submit" name="del_cat" class="text-red-500"><i class="fa fa-trash"></i></button>
                </form>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- Ads Slot Management -->
    <form method="POST" class="glass p-8 rounded-3xl space-y-6">
        <h3 class="font-bold text-yellow-500 uppercase">Manage All 7 Ad Slots</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            {% for k, v in conf.ads.items() %}
            <div class="space-y-1">
                <label class="text-[10px] uppercase text-slate-500">{{ k }} AD CODE</label>
                <textarea name="{{ k }}" rows="3" class="w-full p-3 text-[10px] font-mono rounded-xl">{{ v }}</textarea>
            </div>
            {% endfor %}
        </div>
        <button type="submit" name="update_ads" class="bg-green-600 px-12 py-4 rounded-2xl font-bold shadow-2xl">Update System</button>
    </form>
</div>
""")

if __name__ == '__main__':
    app.run(debug=True)
