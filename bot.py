import os
from flask import Flask, render_template_string, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId

# ভার্সেলের জন্য 'app' অবজেক্টটি একদম উপরে এবং গ্লোবাল থাকতে হবে
app = Flask(__name__)
app.secret_key = "dramaworld_secret_key"

# --- MongoDB Connection ---
MONGO_URI = "mongodb+srv://freelancermaruf1735:6XaThbuVG2zOUWm4@cluster0.ywwppvf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['dramaworld_db']
movies_col = db['movies']
settings_col = db['settings']

# ডেটাবেস ইনিশিয়ালাইজেশন
def get_config():
    conf = settings_col.find_one({"type": "config"})
    if not conf:
        default_conf = {
            "type": "config",
            "slider": ["https://via.placeholder.com/1200x450?text=Welcome+to+DramaWorld"],
            "ads": {
                "popunder": "", "socialbar": "", "native": "",
                "header": "", "footer": "", "middle": "", "banner": ""
            }
        }
        settings_col.insert_one(default_conf)
        return default_conf
    return conf

# --- Premium UI Styles ---
UI_STYLE = """
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    body { font-family: 'Inter', sans-serif; background-color: #0b0f1a; color: #e2e8f0; margin:0; }
    .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.1); }
    .slider-container { position: relative; width: 100%; height: 220px; overflow: hidden; border-radius: 15px; }
    @media(min-width: 768px) { .slider-container { height: 450px; } }
    .slide { display: none; width: 100%; height: 100%; object-fit: cover; transition: opacity 1s ease-in-out; }
    .active-slide { display: block; }
</style>
"""

# --- User Panel Layout ---
USER_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DramaWorld BD</title>
    """ + UI_STYLE + """
    {{ conf.ads.popunder | safe }}
    {{ conf.ads.socialbar | safe }}
</head>
<body>
    <nav class="glass sticky top-0 z-50 px-6 py-4 flex justify-between items-center shadow-2xl">
        <a href="/" class="text-2xl font-bold text-blue-500 uppercase tracking-tighter">DRAMA<span class="text-white">WORLD</span></a>
        <form action="/" method="GET" class="hidden md:flex bg-slate-800 rounded-full px-4 py-1 border border-slate-700">
            <input type="text" name="search" placeholder="Search movies..." class="bg-transparent border-none outline-none text-sm p-1 w-64 text-white">
            <button type="submit"><i class="fa fa-search text-slate-400"></i></button>
        </form>
        <a href="/admin" class="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-lg text-xs font-bold uppercase transition">Admin</a>
    </nav>

    <div class="container mx-auto px-4 py-6">
        <div class="mb-4 text-center overflow-hidden">{{ conf.ads.header | safe }}</div>

        {% if conf.slider and not request.args.get('search') %}
        <div class="slider-container mb-8 shadow-2xl">
            {% for img in conf.slider %}
            <img src="{{ img }}" class="slide">
            {% endfor %}
        </div>
        {% endif %}

        <div class="mb-6 text-center overflow-hidden">{{ conf.ads.middle | safe }}</div>

        <div class="flex justify-between items-center mb-6">
            <h2 class="text-xl font-bold border-l-4 border-blue-500 pl-3">Featured Dramas</h2>
            <div class="md:hidden">
                 <form action="/" method="GET" class="flex bg-slate-800 rounded-lg px-2 py-1">
                    <input type="text" name="search" placeholder="Search..." class="bg-transparent text-xs outline-none w-24">
                    <button type="submit"><i class="fa fa-search text-xs"></i></button>
                </form>
            </div>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 md:gap-6">
            {% for movie in movies %}
            <div class="glass rounded-xl overflow-hidden hover:scale-105 transition duration-300 shadow-lg">
                <div class="relative">
                    <img src="{{ movie.poster }}" class="w-full h-56 md:h-72 object-cover">
                    <span class="absolute top-2 right-2 bg-blue-600 text-white text-[10px] font-bold px-2 py-1 rounded">
                        {{ movie.badge }}
                    </span>
                </div>
                <div class="p-3">
                    <p class="text-[10px] text-blue-400 font-bold mb-1 uppercase">{{ movie.category }}</p>
                    <h3 class="font-bold text-sm h-10 overflow-hidden mb-3 leading-tight">{{ movie.name }}</h3>
                    <div class="flex flex-col gap-2">
                        {% for link in movie.links %}
                        <a href="{{ link.url }}" target="_blank" class="bg-slate-700 hover:bg-blue-600 text-center text-[10px] py-2 rounded-md font-bold transition">
                             {{ link.label }}
                        </a>
                        {% endfor %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <div class="mt-10 text-center overflow-hidden">{{ conf.ads.native | safe }}</div>

        <footer class="mt-12 py-10 text-center border-t border-slate-800 text-slate-500 text-xs">
            {{ conf.ads.footer | safe }}
            <p>&copy; 2024 DramaWorld BD - All Rights Reserved.</p>
        </footer>
    </div>

    <script>
        let sIdx = 0;
        const slides = document.querySelectorAll('.slide');
        function showS() {
            if(slides.length === 0) return;
            slides.forEach(s => s.classList.remove('active-slide'));
            sIdx = (sIdx + 1) % slides.length;
            slides[sIdx].classList.add('active-slide');
        }
        if(slides.length > 0) {
            slides[0].classList.add('active-slide');
            setInterval(showS, 5000);
        }
    </script>
</body>
</html>
"""

# --- Admin Layout ---
ADMIN_LAYOUT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Admin Panel</title>
    """ + UI_STYLE + """
</head>
<body class="bg-[#0b0f1a] text-white flex flex-col md:flex-row min-h-screen">
    <div class="w-full md:w-64 bg-slate-900 border-r border-slate-800 p-6">
        <h2 class="text-xl font-bold mb-8 text-blue-500 uppercase">Admin Control</h2>
        <nav class="space-y-3">
            <a href="/admin" class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-800 transition"><i class="fa fa-dashboard"></i> Dashboard</a>
            <a href="/admin/add" class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-800 transition"><i class="fa fa-plus-circle"></i> Add Movie</a>
            <a href="/admin/settings" class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-800 transition"><i class="fa fa-ad"></i> Ads & Slider</a>
            <a href="/" class="flex items-center gap-3 p-3 rounded-lg hover:bg-blue-900 transition mt-10 border-t border-slate-800"><i class="fa fa-globe"></i> View Site</a>
        </nav>
    </div>
    <main class="flex-grow p-6 md:p-10">
        {% block content %}{% endblock %}
    </main>
</body>
</html>
"""

# --- Routes ---

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
def admin():
    movies = list(movies_col.find().sort("_id", -1))
    return render_template_string(ADMIN_LAYOUT_TEMPLATE.replace('{% block content %}{% endblock %}', """
        <div class="flex justify-between items-center mb-8">
            <h1 class="text-2xl font-bold">Movies Management</h1>
            <span class="bg-blue-600 px-4 py-1 rounded text-xs font-bold">Count: {{ movies|length }}</span>
        </div>
        <div class="glass rounded-xl overflow-hidden shadow-2xl">
            <table class="w-full text-left">
                <thead class="bg-slate-800 text-slate-400 text-xs uppercase">
                    <tr><th class="p-4">Movie</th><th class="p-4">Category</th><th class="p-4">Action</th></tr>
                </thead>
                <tbody>
                    {% for m in movies %}
                    <tr class="border-t border-slate-800">
                        <td class="p-4 flex items-center gap-3">
                            <img src="{{ m.poster }}" class="w-10 h-14 rounded object-cover">
                            <div><p class="font-bold text-sm">{{ m.name }}</p></div>
                        </td>
                        <td class="p-4 text-sm text-slate-400">{{ m.category }}</td>
                        <td class="p-4 flex gap-4 text-lg">
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
def add():
    if request.method == 'POST':
        labels = request.form.getlist('l_name[]')
        urls = request.form.getlist('l_url[]')
        links = [{"label": labels[i], "url": urls[i]} for i in range(len(labels))]
        movies_col.insert_one({
            "name": request.form.get('name'),
            "poster": request.form.get('poster'),
            "badge": request.form.get('badge'),
            "category": request.form.get('category'),
            "links": links
        })
        return redirect('/admin')
    return render_template_string(FORM_HTML, movie=None)

@app.route('/admin/edit/<id>', methods=['GET', 'POST'])
def edit(id):
    movie = movies_col.find_one({"_id": ObjectId(id)})
    if request.method == 'POST':
        labels = request.form.getlist('l_name[]')
        urls = request.form.getlist('l_url[]')
        links = [{"label": labels[i], "url": urls[i]} for i in range(len(labels))]
        movies_col.update_one({"_id": ObjectId(id)}, {"$set": {
            "name": request.form.get('name'),
            "poster": request.form.get('poster'),
            "badge": request.form.get('badge'),
            "category": request.form.get('category'),
            "links": links
        }})
        return redirect('/admin')
    return render_template_string(FORM_HTML, movie=movie)

@app.route('/admin/delete/<id>')
def delete(id):
    movies_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

@app.route('/admin/settings', methods=['GET', 'POST'])
def settings():
    conf = get_config()
    if request.method == 'POST':
        s_imgs = request.form.get('slider').split('\n')
        ads = {k: request.form.get(k) for k in conf['ads'].keys()}
        settings_col.update_one({"type": "config"}, {"$set": {"slider": [i.strip() for i in s_imgs if i.strip()], "ads": ads}})
        return redirect('/admin/settings')
    return render_template_string(SETTINGS_HTML, conf=conf, s_text="\n".join(conf['slider']))

# --- Templates Part 2 ---

FORM_HTML = ADMIN_LAYOUT_TEMPLATE.replace('{% block content %}{% endblock %}', """
<div class="max-w-3xl mx-auto glass p-8 rounded-2xl">
    <h2 class="text-xl font-bold mb-6 text-blue-500 tracking-wider">ADD / EDIT MOVIE</h2>
    <form method="POST" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input type="text" name="name" value="{{ movie.name if movie else '' }}" placeholder="Movie Name" class="w-full bg-slate-800 p-3 rounded-lg outline-none border border-slate-700" required>
            <input type="text" name="category" value="{{ movie.category if movie else '' }}" placeholder="Category" class="w-full bg-slate-800 p-3 rounded-lg outline-none border border-slate-700" required>
        </div>
        <input type="text" name="poster" value="{{ movie.poster if movie else '' }}" placeholder="Poster URL" class="w-full bg-slate-800 p-3 rounded-lg outline-none border border-slate-700" required>
        <input type="text" name="badge" value="{{ movie.badge if movie else '' }}" placeholder="Badge (e.g. 4K, HD)" class="w-full bg-slate-800 p-3 rounded-lg outline-none border border-slate-700">
        
        <div id="btn-area" class="space-y-2">
            <label class="text-xs font-bold text-slate-500 uppercase">Buttons</label>
            {% if movie %}
                {% for l in movie.links %}
                <div class="flex gap-2"><input type="text" name="l_name[]" value="{{ l.label }}" class="w-1/3 bg-slate-900 p-2 text-xs rounded" placeholder="Button Name"><input type="text" name="l_url[]" value="{{ l.url }}" class="w-2/3 bg-slate-900 p-2 text-xs rounded" placeholder="URL"></div>
                {% endfor %}
            {% endif %}
        </div>
        <button type="button" onclick="addB()" class="text-blue-500 text-xs font-bold uppercase">+ Add Button</button>
        <div class="pt-6 flex gap-4">
            <button type="submit" class="bg-blue-600 px-10 py-3 rounded-lg font-bold">SAVE DATA</button>
            <a href="/admin" class="bg-slate-700 px-10 py-3 rounded-lg font-bold">BACK</a>
        </div>
    </form>
</div>
<script>
    function addB() {
        const d = document.createElement('div'); d.className = "flex gap-2";
        d.innerHTML = `<input type="text" name="l_name[]" class="w-1/3 bg-slate-900 p-2 text-xs rounded" placeholder="Button Name" required><input type="text" name="l_url[]" class="w-2/3 bg-slate-900 p-2 text-xs rounded" placeholder="URL" required>`;
        document.getElementById('btn-area').appendChild(d);
    }
</script>
""")

SETTINGS_HTML = ADMIN_LAYOUT_TEMPLATE.replace('{% block content %}{% endblock %}', """
<form method="POST" class="space-y-6">
    <div class="glass p-6 rounded-xl">
        <h3 class="text-sm font-bold text-blue-500 mb-4 uppercase">Slider Management</h3>
        <textarea name="slider" rows="5" class="w-full bg-slate-800 p-3 rounded-lg text-xs font-mono border border-slate-700" placeholder="Image URLs (one per line)">{{ s_text }}</textarea>
    </div>
    <div class="glass p-6 rounded-xl">
        <h3 class="text-sm font-bold text-yellow-500 mb-4 uppercase">Ad Placements</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            {% for k, v in conf.ads.items() %}
            <div>
                <label class="text-[10px] uppercase text-slate-500">{{ k }} AD CODE</label>
                <textarea name="{{ k }}" rows="3" class="w-full bg-slate-900 p-2 text-[10px] font-mono border border-slate-700">{{ v }}</textarea>
            </div>
            {% endfor %}
        </div>
    </div>
    <button type="submit" class="bg-green-600 px-10 py-4 rounded-xl font-bold shadow-xl">UPDATE EVERYTHING</button>
</form>
""")

# এই অংশটি ভার্সেল উপেক্ষা করবে কিন্তু লোকাল রান করতে সাহায্য করবে
if __name__ == '__main__':
    app.run(debug=True)
