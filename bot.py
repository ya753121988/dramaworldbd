import os
from flask import Flask, render_template_string, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId

# ভার্সেলের জন্য মেইন অ্যাপ হ্যান্ডলার
app = Flask(__name__)
app.secret_key = "dramaworld_bd_premium_key"

# --- MongoDB Connection ---
MONGO_URI = "mongodb+srv://freelancermaruf1735:6XaThbuVG2zOUWm4@cluster0.ywwppvf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['dramaworld_db']
movies_col = db['movies']
settings_col = db['settings']

# ডেটাবেস চেক ও ডিফল্ট ডাটা সেটআপ
def get_config():
    conf = settings_col.find_one({"type": "config"})
    if not conf:
        default_conf = {
            "type": "config",
            "slider": ["https://via.placeholder.com/1200x450?text=Premium+Slider+1"],
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
    .movie-card { transition: all 0.3s ease; border: 1px solid rgba(255,255,255,0.05); }
    .movie-card:hover { transform: translateY(-8px); border-color: #3b82f6; box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.3); }
    .slider-box { position: relative; width: 100%; height: 250px; overflow: hidden; border-radius: 20px; }
    @media(min-width: 768px) { .slider-box { height: 480px; } }
    .slide-img { display: none; width: 100%; height: 100%; object-fit: cover; animation: fade 1s ease-in-out; }
    .slide-active { display: block; }
    @keyframes fade { from { opacity: 0; } to { opacity: 1; } }
    input, select, textarea { background: #0f172a !important; color: white !important; border: 1px solid #1e293b !important; }
</style>
"""

# --- ইউজার প্যানেল লেআউট ---
USER_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DramaWorld BD - Premium</title>
    """ + UI_STYLE + """
    {{ conf.ads.popunder | safe }}
    {{ conf.ads.socialbar | safe }}
</head>
<body>
    <nav class="glass sticky top-0 z-50 px-4 md:px-10 py-4 flex justify-between items-center">
        <a href="/" class="text-2xl font-black text-blue-500 tracking-tighter">DRAMA<span class="text-white">WORLD</span></a>
        <div class="flex items-center gap-4">
            <form action="/" method="GET" class="hidden md:flex bg-slate-900 rounded-full px-4 py-1 border border-slate-800">
                <input type="text" name="search" placeholder="Search movies..." class="bg-transparent border-none outline-none text-sm p-1 w-64">
                <button type="submit"><i class="fa fa-search text-slate-500"></i></button>
            </form>
            <a href="/admin" class="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-full text-xs font-bold transition uppercase">Admin</a>
        </div>
    </nav>

    <div class="container mx-auto px-4 py-6">
        <!-- Header Ad -->
        <div class="mb-6 text-center">{{ conf.ads.header | safe }}</div>

        <!-- Slider Section -->
        {% if conf.slider and not request.args.get('search') %}
        <div class="slider-box mb-8 shadow-2xl">
            {% for img in conf.slider %}
            <img src="{{ img }}" class="slide-img">
            {% endfor %}
        </div>
        {% endif %}

        <!-- Middle Ad -->
        <div class="mb-8 text-center">{{ conf.ads.middle | safe }}</div>

        <!-- Search for Mobile -->
        <div class="md:hidden mb-6">
            <form action="/" method="GET" class="flex bg-slate-900 rounded-xl px-4 py-2 border border-slate-800">
                <input type="text" name="search" placeholder="Search..." class="bg-transparent w-full outline-none text-sm">
                <button type="submit"><i class="fa fa-search text-blue-500"></i></button>
            </form>
        </div>

        <h2 class="text-2xl font-bold mb-8 flex items-center gap-3">
            <span class="w-2 h-8 bg-blue-600 rounded-full"></span> Latest Collection
        </h2>

        <!-- Movie Grid -->
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 md:gap-8">
            {% for movie in movies %}
            <div class="glass movie-card rounded-2xl overflow-hidden relative group">
                <!-- Edit/Delete for Admin on Card -->
                <div class="absolute top-2 right-2 z-10 flex gap-2 opacity-0 group-hover:opacity-100 transition">
                    <a href="/admin/edit/{{ movie._id }}" class="bg-blue-600 p-2 rounded-full text-xs shadow-lg"><i class="fa fa-edit"></i></a>
                    <a href="/admin/delete/{{ movie._id }}" class="bg-red-600 p-2 rounded-full text-xs shadow-lg" onclick="return confirm('Delete?')"><i class="fa fa-trash"></i></a>
                </div>

                <div class="relative overflow-hidden">
                    <img src="{{ movie.poster }}" class="w-full h-60 md:h-80 object-cover transition duration-500 group-hover:scale-110">
                    <div class="absolute top-3 left-3 bg-blue-600 text-[10px] font-bold px-3 py-1 rounded-full uppercase shadow-lg">
                        {{ movie.badge }}
                    </div>
                </div>
                <div class="p-4">
                    <p class="text-[10px] text-blue-400 font-bold mb-1 uppercase tracking-widest">{{ movie.category }}</p>
                    <h3 class="font-bold text-sm md:text-base h-12 overflow-hidden leading-tight mb-4">{{ movie.name }}</h3>
                    
                    <div class="space-y-2">
                        {% for link in movie.links %}
                        <a href="{{ link.url }}" target="_blank" class="block bg-slate-800 hover:bg-blue-600 text-center text-[11px] py-2.5 rounded-xl font-bold transition shadow-inner">
                            <i class="fa fa-play-circle mr-1"></i> {{ link.label }}
                        </a>
                        {% endfor %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <!-- Banner Ad -->
        <div class="mt-12 text-center">{{ conf.ads.banner | safe }}</div>
        
        <!-- Native Ad -->
        <div class="mt-6 text-center">{{ conf.ads.native | safe }}</div>

        <footer class="mt-20 py-10 text-center border-t border-slate-900 text-slate-500 text-sm">
            {{ conf.ads.footer | safe }}
            <p class="mt-4 font-bold tracking-widest text-blue-500">DRAMAWORLD BD &copy; 2024</p>
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

# --- এডমিন প্যানেল ডিজাইন ---
ADMIN_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Admin Dashboard</title>
    """ + UI_STYLE + """
</head>
<body class="bg-[#02040a] flex flex-col md:flex-row min-h-screen">
    <div class="w-full md:w-72 bg-[#080c14] border-r border-slate-900 p-8">
        <h2 class="text-2xl font-black mb-10 text-blue-500 uppercase italic">Control Panel</h2>
        <nav class="space-y-4">
            <a href="/admin" class="flex items-center gap-4 p-4 rounded-2xl hover:bg-blue-600/10 transition text-slate-400 hover:text-white">
                <i class="fa fa-grid-2"></i> Dashboard
            </a>
            <a href="/admin/add" class="flex items-center gap-4 p-4 rounded-2xl bg-blue-600 text-white shadow-lg shadow-blue-600/20">
                <i class="fa fa-plus-circle"></i> Add New Movie
            </a>
            <a href="/admin/settings" class="flex items-center gap-4 p-4 rounded-2xl hover:bg-blue-600/10 transition text-slate-400 hover:text-white">
                <i class="fa fa-ad"></i> Ads & Slider
            </a>
            <div class="pt-10 border-t border-slate-900 mt-10">
                <a href="/" class="flex items-center gap-4 p-4 rounded-2xl hover:bg-slate-800 transition text-slate-400">
                    <i class="fa fa-globe"></i> Visit Website
                </a>
            </div>
        </nav>
    </div>
    <main class="flex-grow p-6 md:p-12">
        {% block content %}{% endblock %}
    </main>
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
    else:
        movies = list(movies_col.find().sort("_id", -1))
    return render_template_string(USER_LAYOUT, movies=movies, conf=conf)

@app.route('/admin')
def admin_dash():
    search = request.args.get('search')
    if search:
        movies = list(movies_col.find({"name": {"$regex": search, "$options": "i"}}))
    else:
        movies = list(movies_col.find().sort("_id", -1))
    
    return render_template_string(ADMIN_LAYOUT.replace('{% block content %}{% endblock %}', """
        <div class="flex flex-col md:flex-row justify-between items-center mb-10 gap-4">
            <h1 class="text-3xl font-bold">Manage Movies</h1>
            <form action="/admin" class="flex bg-slate-900 border border-slate-800 rounded-full px-4 py-2">
                <input type="text" name="search" placeholder="Search in admin..." class="bg-transparent outline-none text-sm">
                <button><i class="fa fa-search text-blue-500"></i></button>
            </form>
        </div>
        <div class="glass rounded-3xl overflow-hidden shadow-2xl">
            <table class="w-full text-left">
                <thead class="bg-slate-900/50 text-slate-500 text-xs uppercase tracking-widest">
                    <tr>
                        <th class="p-6">Movie Information</th>
                        <th class="p-6">Category</th>
                        <th class="p-6">Buttons</th>
                        <th class="p-6">Actions</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-900">
                    {% for m in movies %}
                    <tr class="hover:bg-blue-600/5 transition">
                        <td class="p-6 flex items-center gap-4">
                            <img src="{{ m.poster }}" class="w-12 h-16 rounded-lg object-cover shadow-2xl">
                            <div>
                                <p class="font-bold">{{ m.name }}</p>
                                <p class="text-[10px] text-blue-500">{{ m.badge }}</p>
                            </div>
                        </td>
                        <td class="p-6 text-sm">{{ m.category }}</td>
                        <td class="p-6 text-xs text-slate-500">{{ m.links|length }} Buttons</td>
                        <td class="p-6">
                            <div class="flex gap-4">
                                <a href="/admin/edit/{{ m._id }}" class="text-blue-500 hover:text-white transition"><i class="fa fa-edit"></i></a>
                                <a href="/admin/delete/{{ m._id }}" class="text-red-500 hover:text-white transition" onclick="return confirm('Delete?')"><i class="fa fa-trash"></i></a>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    """), movies=movies)

@app.route('/admin/add', methods=['GET', 'POST'])
def add_movie():
    if request.method == 'POST':
        labels = request.form.getlist('link_name[]')
        urls = request.form.getlist('link_url[]')
        links = [{"label": labels[i], "url": urls[i]} for i in range(len(labels))]
        movies_col.insert_one({
            "name": request.form.get('name'),
            "poster": request.form.get('poster'),
            "badge": request.form.get('badge'),
            "category": request.form.get('category'),
            "links": links
        })
        return redirect('/admin')
    return render_template_string(MOVIE_FORM_HTML, movie=None)

@app.route('/admin/edit/<id>', methods=['GET', 'POST'])
def edit_movie(id):
    movie = movies_col.find_one({"_id": ObjectId(id)})
    if request.method == 'POST':
        labels = request.form.getlist('link_name[]')
        urls = request.form.getlist('link_url[]')
        links = [{"label": labels[i], "url": urls[i]} for i in range(len(labels))]
        movies_col.update_one({"_id": ObjectId(id)}, {"$set": {
            "name": request.form.get('name'),
            "poster": request.form.get('poster'),
            "badge": request.form.get('badge'),
            "category": request.form.get('category'),
            "links": links
        }})
        return redirect('/admin')
    return render_template_string(MOVIE_FORM_HTML, movie=movie)

@app.route('/admin/delete/<id>')
def delete_movie(id):
    movies_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

@app.route('/admin/settings', methods=['GET', 'POST'])
def settings():
    conf = get_config()
    if request.method == 'POST':
        s_list = request.form.get('slider').split('\n')
        ads = {k: request.form.get(k) for k in conf['ads'].keys()}
        settings_col.update_one({"type": "config"}, {"$set": {
            "slider": [i.strip() for i in s_list if i.strip()],
            "ads": ads
        }})
        return redirect('/admin/settings')
    return render_template_string(SETTINGS_FORM_HTML, conf=conf, s_text="\n".join(conf['slider']))

# --- ফর্ম HTML (Add/Edit) ---

MOVIE_FORM_HTML = ADMIN_LAYOUT.replace('{% block content %}{% endblock %}', """
<div class="max-w-4xl mx-auto glass p-8 md:p-12 rounded-3xl shadow-2xl">
    <h2 class="text-2xl font-bold mb-8 text-blue-500 uppercase">{{ 'Edit Movie' if movie else 'Add New Movie' }}</h2>
    <form method="POST" class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-2">
                <label class="text-xs font-bold text-slate-500 uppercase">Movie Name</label>
                <input type="text" name="name" value="{{ movie.name if movie else '' }}" class="w-full p-4 rounded-2xl outline-none" placeholder="Enter name" required>
            </div>
            <div class="space-y-2">
                <label class="text-xs font-bold text-slate-500 uppercase">Category</label>
                <select name="category" class="w-full p-4 rounded-2xl outline-none">
                    <option value="Action" {{ 'selected' if movie and movie.category=='Action' }}>Action</option>
                    <option value="Drama" {{ 'selected' if movie and movie.category=='Drama' }}>Drama</option>
                    <option value="Horror" {{ 'selected' if movie and movie.category=='Horror' }}>Horror</option>
                    <option value="Thriller" {{ 'selected' if movie and movie.category=='Thriller' }}>Thriller</option>
                </select>
            </div>
        </div>
        <div class="space-y-2">
            <label class="text-xs font-bold text-slate-500 uppercase">Poster URL</label>
            <input type="text" name="poster" value="{{ movie.poster if movie else '' }}" class="w-full p-4 rounded-2xl outline-none" placeholder="https://..." required>
        </div>
        <div class="space-y-2">
            <label class="text-xs font-bold text-slate-500 uppercase">Badge / Quality (e.g. 4K, HD)</label>
            <input type="text" name="badge" value="{{ movie.badge if movie else '' }}" class="w-full p-4 rounded-2xl outline-none" placeholder="HD 1080p">
        </div>

        <div id="links-container" class="space-y-4">
            <label class="block text-xs font-bold text-slate-500 uppercase">Unlimited Download/Watch Buttons</label>
            {% if movie %}
                {% for l in movie.links %}
                <div class="flex gap-3 animate-fade-in">
                    <input type="text" name="link_name[]" value="{{ l.label }}" class="w-1/3 p-3 rounded-xl text-sm" placeholder="Button Name">
                    <input type="text" name="link_url[]" value="{{ l.url }}" class="w-2/3 p-3 rounded-xl text-sm" placeholder="URL">
                </div>
                {% endfor %}
            {% endif %}
        </div>
        <button type="button" onclick="addLinkRow()" class="bg-blue-600/20 text-blue-500 px-6 py-2 rounded-xl text-xs font-bold uppercase hover:bg-blue-600 hover:text-white transition">+ Add Link Button</button>

        <div class="pt-10 flex gap-4">
            <button type="submit" class="bg-blue-600 hover:bg-blue-700 px-10 py-4 rounded-2xl font-bold shadow-xl transition">SAVE MOVIE DATA</button>
            <a href="/admin" class="bg-slate-800 px-10 py-4 rounded-2xl font-bold transition">CANCEL</a>
        </div>
    </form>
</div>
<script>
    function addLinkRow() {
        const div = document.createElement('div');
        div.className = "flex gap-3";
        div.innerHTML = `<input type="text" name="link_name[]" class="w-1/3 p-3 rounded-xl text-sm" placeholder="Button Name" required><input type="text" name="link_url[]" class="w-2/3 p-3 rounded-xl text-sm" placeholder="URL" required>`;
        document.getElementById('links-container').appendChild(div);
    }
</script>
""")

SETTINGS_FORM_HTML = ADMIN_LAYOUT.replace('{% block content %}{% endblock %}', """
<h1 class="text-3xl font-bold mb-10">Site Settings</h1>
<form method="POST" class="space-y-8">
    <div class="glass p-8 rounded-3xl">
        <h3 class="text-lg font-bold mb-4 text-blue-500">Premium Slider Images</h3>
        <p class="text-xs text-slate-500 mb-4">Paste image URLs (one per line)</p>
        <textarea name="slider" rows="6" class="w-full p-4 rounded-2xl outline-none font-mono text-xs">{{ s_text }}</textarea>
    </div>
    
    <div class="glass p-8 rounded-3xl">
        <h3 class="text-lg font-bold mb-6 text-yellow-500 uppercase tracking-widest">Ad Code Management (All Slots)</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            {% for k, v in conf.ads.items() %}
            <div class="space-y-2">
                <label class="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">{{ k }} AD CODE</label>
                <textarea name="{{ k }}" rows="3" class="w-full p-3 rounded-xl text-[10px] font-mono">{{ v }}</textarea>
            </div>
            {% endfor %}
        </div>
    </div>
    <button type="submit" class="bg-green-600 hover:bg-green-700 px-12 py-5 rounded-2xl font-bold shadow-2xl transition uppercase tracking-widest">Update All Systems</button>
</form>
""")

if __name__ == '__main__':
    app.run(debug=True)
