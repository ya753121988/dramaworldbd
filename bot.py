import os
from flask import Flask, render_template_string, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId

# ভার্সেলের জন্য মেইন অ্যাপ হ্যান্ডলার
app = Flask(__name__)
app.secret_key = "dramaworld_bd_ultimate_premium_key"

# --- MongoDB Connection ---
MONGO_URI = "mongodb+srv://freelancermaruf1735:6XaThbuVG2zOUWm4@cluster0.ywwppvf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['dramaworld_db']
movies_col = db['movies']
settings_col = db['settings']

# ডেটাবেস চেক ও অ্যাড সেটিংস সেটআপ
def get_config():
    conf = settings_col.find_one({"type": "config"})
    if not conf:
        default_conf = {
            "type": "config",
            "ads": {
                "popunder": "", "socialbar": "", "native": "", 
                "banner": "", "header": "", "footer": "", "middle": ""
            }
        }
        settings_col.insert_one(default_conf)
        return default_conf
    return conf

# --- প্রিমিয়াম UI স্টাইল (CSS) ---
UI_STYLE = """
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    body { font-family: 'Poppins', sans-serif; background-color: #050811; color: #e2e8f0; margin:0; }
    .glass { background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.05); }
    .movie-card { transition: all 0.3s ease; border: 1px solid rgba(255,255,255,0.05); cursor: pointer; }
    .movie-card:hover { transform: translateY(-8px); border-color: #3b82f6; box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.3); }
    .slider-box { position: relative; width: 100%; height: 250px; overflow: hidden; border-radius: 20px; }
    @media(min-width: 768px) { .slider-box { height: 480px; } }
    .slide-img { display: none; width: 100%; height: 100%; object-fit: cover; animation: fade 1s ease-in-out; }
    .slide-active { display: block; }
    @keyframes fade { from { opacity: 0; } to { opacity: 1; } }
    input, select, textarea { background: #0f172a !important; color: white !important; border: 1px solid #1e293b !important; }
</style>
"""

# --- ইউজার প্যানেল: হোম পেজ (স্লাইডার অটো মুভি থেকে আসবে) ---
USER_HOME = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DramaWorld BD - Home</title>
    """ + UI_STYLE + """
    {{ conf.ads.popunder | safe }}
    {{ conf.ads.socialbar | safe }}
</head>
<body>
    <nav class="glass sticky top-0 z-50 px-4 md:px-10 py-4 flex justify-between items-center shadow-2xl">
        <a href="/" class="text-2xl font-black text-blue-500 tracking-tighter uppercase">DRAMA<span class="text-white">WORLD</span></a>
        <form action="/" method="GET" class="flex bg-slate-900 rounded-full px-4 py-1 border border-slate-800">
            <input type="text" name="search" placeholder="Search movies..." class="bg-transparent border-none outline-none text-sm p-1 w-32 md:w-64">
            <button type="submit"><i class="fa fa-search text-slate-500"></i></button>
        </form>
    </nav>

    <div class="container mx-auto px-4 py-6">
        <div class="mb-4 text-center">{{ conf.ads.header | safe }}</div>

        <!-- অটো স্লাইডার: সব ক্যাটাগরির লেটেস্ট মুভি থেকে আসবে -->
        {% if slider_movies and not request.args.get('search') %}
        <div class="slider-box mb-10 shadow-2xl">
            {% for sm in slider_movies %}
            <a href="/movie/{{ sm._id }}">
                <img src="{{ sm.poster }}" class="slide-img">
            </a>
            {% endfor %}
        </div>
        {% endif %}

        <div class="mb-8 text-center">{{ conf.ads.middle | safe }}</div>

        <h2 class="text-xl font-bold mb-8 flex items-center gap-3">
            <span class="w-2 h-8 bg-blue-600 rounded-full"></span> Latest Collection
        </h2>

        <!-- মুভি গ্রিড (ইউজার প্যানেলে কোনো এডমিন বা ডিলিট বাটন নেই) -->
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 md:gap-8">
            {% for movie in movies %}
            <div class="glass movie-card rounded-2xl overflow-hidden relative group" onclick="location.href='/movie/{{ movie._id }}'">
                <div class="relative overflow-hidden">
                    <img src="{{ movie.poster }}" class="w-full h-60 md:h-80 object-cover transition duration-500 group-hover:scale-110">
                    <div class="absolute top-3 left-3 bg-blue-600 text-[10px] font-bold px-3 py-1 rounded-full uppercase">
                        {{ movie.badge }}
                    </div>
                </div>
                <div class="p-4">
                    <p class="text-[10px] text-blue-400 font-bold mb-1 uppercase tracking-widest">{{ movie.category }}</p>
                    <h3 class="font-bold text-sm md:text-base h-12 overflow-hidden leading-tight">{{ movie.name }}</h3>
                </div>
            </div>
            {% endfor %}
        </div>

        <div class="mt-12 text-center">{{ conf.ads.banner | safe }}</div>
        <footer class="mt-20 py-10 text-center border-t border-slate-900 text-slate-500 text-sm">
            {{ conf.ads.footer | safe }}
            <p>&copy; 2024 DramaWorld BD</p>
        </footer>
    </div>

    <script>
        let sIdx = 0;
        const slides = document.querySelectorAll('.slide-img');
        function showS() {
            if(slides.length === 0) return;
            slides.forEach(s => s.classList.remove('slide-active'));
            sIdx = (sIdx + 1) % slides.length;
            slides[sIdx].classList.add('slide-active');
        }
        if(slides.length > 0) {
            slides[0].classList.add('slide-active');
            setInterval(showS, 5000);
        }
    </script>
</body>
</html>
"""

# --- ইউজার প্যানেল: ডিটেইলস পেজ (এখানে সব বাটন থাকবে) ---
DETAILS_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ movie.name }} - DramaWorld</title>
    """ + UI_STYLE + """
</head>
<body>
    <nav class="glass sticky top-0 z-50 px-4 md:px-10 py-4 shadow-xl">
        <a href="/" class="text-2xl font-black text-blue-500">DRAMA<span class="text-white">WORLD</span></a>
    </nav>
    <div class="container mx-auto px-4 py-10">
        <div class="flex flex-col md:flex-row gap-10">
            <div class="w-full md:w-1/3">
                <img src="{{ movie.poster }}" class="w-full rounded-3xl shadow-2xl border border-slate-800">
            </div>
            <div class="w-full md:w-2/3">
                <span class="bg-blue-600 px-4 py-1 rounded-full text-xs font-bold uppercase shadow-lg">{{ movie.badge }}</span>
                <h1 class="text-4xl font-bold mt-4 mb-2">{{ movie.name }}</h1>
                <p class="text-blue-400 font-bold mb-8 italic uppercase tracking-widest text-sm">{{ movie.category }}</p>
                
                <div class="glass p-8 rounded-3xl border border-blue-500/10 shadow-2xl">
                    <h3 class="text-xl font-bold mb-8 border-b border-slate-800 pb-3 flex items-center gap-2">
                        <i class="fa fa-play-circle text-blue-500"></i> WATCH OR DOWNLOAD LINKS
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {% for link in movie.links %}
                        <a href="{{ link.url }}" target="_blank" class="bg-blue-600 hover:bg-blue-700 text-white text-center py-4 rounded-2xl font-bold transition transform hover:scale-105 shadow-xl">
                            {{ link.label }}
                        </a>
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

# --- এডমিন প্যানেল: লেআউট (এখান থেকে মুভি ম্যানেজ হবে) ---
ADMIN_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Admin Panel - Manage All</title>
    """ + UI_STYLE + """
</head>
<body class="bg-[#02040a] flex flex-col md:flex-row min-h-screen">
    <div class="w-full md:w-72 bg-[#080c14] border-r border-slate-900 p-8 shadow-2xl">
        <h2 class="text-2xl font-black mb-10 text-blue-500 uppercase italic">Admin Panel</h2>
        <nav class="space-y-4">
            <a href="/admin" class="flex items-center gap-4 p-4 rounded-2xl bg-blue-600/10 text-white border border-blue-600/20">Dashboard</a>
            <a href="/admin/add" class="flex items-center gap-4 p-4 rounded-2xl bg-blue-600 text-white shadow-xl hover:bg-blue-700 transition">Add New Movie</a>
            <a href="/admin/settings" class="flex items-center gap-4 p-4 rounded-2xl hover:bg-slate-800 transition text-slate-400">Settings & Ads</a>
            <a href="/" class="flex items-center gap-4 p-4 rounded-2xl hover:bg-slate-800 transition text-slate-500 mt-10 border-t border-slate-900">View Site</a>
        </nav>
    </div>
    <main class="flex-grow p-6 md:p-12">
        <div class="flex justify-between items-center mb-10">
            <h1 class="text-3xl font-bold">Manage Movies</h1>
            <span class="bg-slate-900 px-5 py-2 rounded-xl text-xs font-bold uppercase border border-slate-800">Total: {{ movies|length }}</span>
        </div>
        <div class="glass rounded-3xl overflow-hidden shadow-2xl">
            <table class="w-full text-left">
                <thead class="bg-slate-900/50 text-slate-500 text-xs uppercase tracking-widest">
                    <tr><th class="p-6">Movie</th><th class="p-6">Category / Badge</th><th class="p-6 text-center">Actions</th></tr>
                </thead>
                <tbody class="divide-y divide-slate-900">
                    {% for m in movies %}
                    <tr class="hover:bg-slate-800/30 transition">
                        <td class="p-6 flex items-center gap-4">
                            <img src="{{ m.poster }}" class="w-12 h-16 rounded shadow-lg object-cover">
                            <span class="font-bold text-sm">{{ m.name }}</span>
                        </td>
                        <td class="p-6">
                            <span class="text-xs text-blue-400 font-bold block uppercase">{{ m.category }}</span>
                            <span class="text-[10px] text-slate-500">{{ m.badge }}</span>
                        </td>
                        <td class="p-6">
                            <div class="flex justify-center gap-6">
                                <a href="/admin/edit/{{ m._id }}" class="text-blue-500 text-lg hover:text-white transition"><i class="fa fa-edit"></i></a>
                                <a href="/admin/delete/{{ m._id }}" class="text-red-500 text-lg hover:text-white transition" onclick="return confirm('Confirm Delete?')"><i class="fa fa-trash"></i></a>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </main>
</body>
</html>
"""

# --- এডমিন প্যানেল: মুভি ফর্ম (Unlimited Buttons) ---
MOVIE_FORM = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Movie Editor</title>
    """ + UI_STYLE + """
</head>
<body class="bg-[#02040a] p-6 md:p-10">
    <div class="max-w-4xl mx-auto glass p-8 md:p-12 rounded-3xl shadow-2xl">
        <h2 class="text-2xl font-bold mb-10 text-blue-500 uppercase tracking-widest">{{ 'Edit Movie' if movie else 'Add Movie' }}</h2>
        <form method="POST" class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="space-y-1">
                    <label class="text-xs font-bold text-slate-500 uppercase">Movie Name</label>
                    <input type="text" name="name" value="{{ movie.name if movie else '' }}" class="w-full p-4 rounded-2xl outline-none" required>
                </div>
                <div class="space-y-1">
                    <label class="text-xs font-bold text-slate-500 uppercase">Category</label>
                    <input type="text" name="category" value="{{ movie.category if movie else '' }}" class="w-full p-4 rounded-2xl outline-none" placeholder="e.g. Action, Drama" required>
                </div>
            </div>
            <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 uppercase">Poster URL</label>
                <input type="text" name="poster" value="{{ movie.poster if movie else '' }}" class="w-full p-4 rounded-2xl outline-none" required>
            </div>
            <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 uppercase">Badge (Poster Badge Text)</label>
                <input type="text" name="badge" value="{{ movie.badge if movie else '' }}" class="w-full p-4 rounded-2xl outline-none" placeholder="e.g. 4K, HD, New">
            </div>

            <div id="links-container" class="space-y-4 pt-6 border-t border-slate-800">
                <label class="block text-xs font-bold text-blue-500 uppercase">Unlimited Download Buttons</label>
                {% if movie %}
                    {% for l in movie.links %}
                    <div class="flex gap-4">
                        <input type="text" name="l_name[]" value="{{ l.label }}" class="w-1/3 p-3 rounded-xl text-sm" placeholder="Button Name">
                        <input type="text" name="l_url[]" value="{{ l.url }}" class="w-2/3 p-3 rounded-xl text-sm" placeholder="Link URL">
                    </div>
                    {% endfor %}
                {% endif %}
            </div>
            <button type="button" onclick="addL()" class="bg-blue-600/10 text-blue-500 px-6 py-2 rounded-xl text-xs font-bold hover:bg-blue-600 hover:text-white transition">+ ADD NEW BUTTON</button>

            <div class="pt-10 flex gap-4">
                <button type="submit" class="bg-blue-600 hover:bg-blue-700 px-12 py-4 rounded-2xl font-bold shadow-xl transition">SAVE MOVIE</button>
                <a href="/admin" class="bg-slate-800 px-12 py-4 rounded-2xl font-bold">CANCEL</a>
            </div>
        </form>
    </div>
    <script>
        function addL() {
            const container = document.getElementById('links-container');
            const d = document.createElement('div'); d.className = "flex gap-4";
            d.innerHTML = `<input type="text" name="l_name[]" class="w-1/3 p-3 rounded-xl text-sm" placeholder="Button Name" required><input type="text" name="l_url[]" class="w-2/3 p-3 rounded-xl text-sm" placeholder="Link URL" required>`;
            container.appendChild(d);
        }
    </script>
</body>
</html>
"""

# --- এডমিন প্যানেল: সেটিংস (Ads Slot) ---
SETTINGS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Global Ad Settings</title>
    """ + UI_STYLE + """
</head>
<body class="bg-[#02040a] p-6 md:p-12">
    <div class="max-w-5xl mx-auto space-y-10">
        <h1 class="text-3xl font-black text-blue-500 uppercase italic">Ad Management (All 7 Slots)</h1>
        <form method="POST" class="space-y-8">
            <div class="glass p-8 rounded-3xl shadow-2xl">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {% for k, v in conf.ads.items() %}
                    <div class="space-y-2">
                        <label class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{{ k }} AD CODE</label>
                        <textarea name="{{ k }}" rows="4" class="w-full bg-slate-900 border-none rounded-2xl p-4 text-[10px] font-mono">{{ v }}</textarea>
                    </div>
                    {% endfor %}
                </div>
            </div>
            <div class="flex gap-6">
                <button type="submit" class="bg-green-600 hover:bg-green-700 px-12 py-5 rounded-2xl font-bold shadow-2xl transition uppercase">Update All Ads</button>
                <a href="/admin" class="bg-slate-800 px-12 py-5 rounded-2xl font-bold uppercase">Back</a>
            </div>
        </form>
    </div>
</body>
</html>
"""

# --- রুটস (Routes) ---

@app.route('/')
def index():
    conf = get_config()
    search = request.args.get('search')
    if search:
        movies = list(movies_col.find({"name": {"$regex": search, "$options": "i"}}))
        slider_movies = []
    else:
        movies = list(movies_col.find().sort("_id", -1))
        slider_movies = movies[:6] # স্লাইডারে লেটেস্ট ৬টি মুভি অটো আসবে
    return render_template_string(USER_HOME, movies=movies, slider_movies=slider_movies, conf=conf)

@app.route('/movie/<id>')
def movie_details(id):
    conf = get_config()
    movie = movies_col.find_one({"_id": ObjectId(id)})
    return render_template_string(DETAILS_PAGE, movie=movie, conf=conf)

@app.route('/admin')
def admin():
    movies = list(movies_col.find().sort("_id", -1))
    return render_template_string(ADMIN_DASHBOARD, movies=movies)

@app.route('/admin/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        labels, urls = request.form.getlist('l_name[]'), request.form.getlist('l_url[]')
        links = [{"label": labels[i], "url": urls[i]} for i in range(len(labels))]
        movies_col.insert_one({
            "name": request.form.get('name'), "poster": request.form.get('poster'),
            "badge": request.form.get('badge'), "category": request.form.get('category'), "links": links
        })
        return redirect('/admin')
    return render_template_string(MOVIE_FORM, movie=None)

@app.route('/admin/edit/<id>', methods=['GET', 'POST'])
def edit(id):
    movie = movies_col.find_one({"_id": ObjectId(id)})
    if request.method == 'POST':
        labels, urls = request.form.getlist('l_name[]'), request.form.getlist('l_url[]')
        links = [{"label": labels[i], "url": urls[i]} for i in range(len(labels))]
        movies_col.update_one({"_id": ObjectId(id)}, {"$set": {
            "name": request.form.get('name'), "poster": request.form.get('poster'),
            "badge": request.form.get('badge'), "category": request.form.get('category'), "links": links
        }})
        return redirect('/admin')
    return render_template_string(MOVIE_FORM, movie=movie)

@app.route('/admin/delete/<id>')
def delete(id):
    movies_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

@app.route('/admin/settings', methods=['GET', 'POST'])
def settings():
    conf = get_config()
    if request.method == 'POST':
        ads = {k: request.form.get(k) for k in conf['ads'].keys()}
        settings_col.update_one({"type": "config"}, {"$set": {"ads": ads}})
        return redirect('/admin/settings')
    return render_template_string(SETTINGS_HTML, conf=conf)

if __name__ == '__main__':
    app.run(debug=True)
