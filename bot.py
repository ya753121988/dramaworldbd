import os
from flask import Flask, render_template_string, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId

# --- Vercel এর জন্য মেইন অ্যাপ অবজেক্ট ---
app = Flask(__name__)
app.secret_key = "premium_movie_secret"

# --- MongoDB Connection ---
MONGO_URI = "mongodb+srv://freelancermaruf1735:6XaThbuVG2zOUWm4@cluster0.ywwppvf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['dramaworld_db']
movies_col = db['movies']
settings_col = db['settings']

# Initial Database Setup
def init_db():
    if not settings_col.find_one({"type": "config"}):
        settings_col.insert_one({
            "type": "config",
            "slider": ["https://via.placeholder.com/1200x450?text=Welcome+to+DramaWorld"],
            "ads": {
                "popunder": "", "socialbar": "", "native": "",
                "header": "", "footer": "", "middle": "", "banner": ""
            }
        })

init_db()

# --- CSS & UI Styles ---
UI_STYLE = """
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    body { font-family: 'Inter', sans-serif; background-color: #0b0f1a; color: #e2e8f0; margin:0; }
    .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.1); }
    .movie-card:hover { transform: translateY(-5px); transition: 0.3s; }
    .slider-container { position: relative; width: 100%; height: 200px; overflow: hidden; border-radius: 15px; }
    @media(min-width: 768px) { .slider-container { height: 400px; } }
    .slide { display: none; width: 100%; height: 100%; object-fit: cover; }
    .active-slide { display: block; animation: fade 1s ease-in-out; }
    @keyframes fade { from { opacity: 0.5; } to { opacity: 1; } }
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
    <nav class="glass sticky top-0 z-50 px-6 py-4 flex justify-between items-center shadow-xl">
        <a href="/" class="text-2xl font-bold text-blue-500 tracking-tighter">DRAMA<span class="text-white">WORLD</span></a>
        <div class="flex items-center gap-4">
            <form action="/" method="GET" class="hidden md:flex bg-slate-800 rounded-full px-4 py-1 border border-slate-700">
                <input type="text" name="search" placeholder="Search drama..." class="bg-transparent border-none outline-none text-sm p-1 w-48 text-white">
                <button type="submit"><i class="fa fa-search text-slate-400"></i></button>
            </form>
            <a href="/admin" class="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-full text-xs font-bold uppercase transition">Admin</a>
        </div>
    </nav>

    <div class="container mx-auto px-4 py-6">
        <div class="mb-4 text-center overflow-hidden">{{ conf.ads.header | safe }}</div>

        {% if not request.args.get('search') and conf.slider %}
        <div class="slider-container mb-8 shadow-2xl">
            {% for img in conf.slider %}
            <img src="{{ img }}" class="slide">
            {% endfor %}
        </div>
        {% endif %}

        <div class="mb-6 text-center overflow-hidden">{{ conf.ads.middle | safe }}</div>

        <div class="flex justify-between items-center mb-6">
            <h2 class="text-xl font-bold border-l-4 border-blue-500 pl-3">Latest Uploads</h2>
            <div class="md:hidden">
                 <form action="/" method="GET" class="flex bg-slate-800 rounded-lg px-2 py-1">
                    <input type="text" name="search" placeholder="Search..." class="bg-transparent text-xs outline-none w-24">
                    <button type="submit"><i class="fa fa-search text-xs"></i></button>
                </form>
            </div>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 md:gap-6">
            {% for movie in movies %}
            <div class="glass movie-card rounded-xl overflow-hidden shadow-lg">
                <div class="relative">
                    <img src="{{ movie.poster }}" class="w-full h-56 md:h-72 object-cover">
                    <span class="absolute top-2 right-2 bg-blue-600 text-white text-[10px] font-bold px-2 py-1 rounded shadow-lg">
                        {{ movie.badge }}
                    </span>
                </div>
                <div class="p-3">
                    <p class="text-[10px] text-blue-400 font-bold mb-1 uppercase tracking-widest">{{ movie.category }}</p>
                    <h3 class="font-bold text-sm h-10 overflow-hidden leading-tight mb-3">{{ movie.name }}</h3>
                    <div class="flex flex-col gap-2">
                        {% for link in movie.links %}
                        <a href="{{ link.url }}" target="_blank" class="bg-slate-700 hover:bg-blue-600 text-center text-[11px] py-2 rounded-lg font-semibold transition">
                             {{ link.label }}
                        </a>
                        {% endfor %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <div class="mt-10 text-center overflow-hidden">{{ conf.ads.native | safe }}</div>

        <footer class="mt-12 py-8 text-center border-t border-slate-800 text-slate-500 text-xs">
            {{ conf.ads.footer | safe }}
            <p class="mt-4">&copy; 2024 DramaWorld BD - Premium Entertainment</p>
        </footer>
    </div>

    <script>
        let slideIndex = 0;
        const slides = document.querySelectorAll('.slide');
        function showSlides() {
            if(slides.length === 0) return;
            slides.forEach(s => s.classList.remove('active-slide'));
            slideIndex = (slideIndex + 1) % slides.length;
            slides[slideIndex].classList.add('active-slide');
        }
        if(slides.length > 0) {
            slides[0].classList.add('active-slide');
            setInterval(showSlides, 5000);
        }
    </script>
</body>
</html>
"""

# --- Admin Layout ---
ADMIN_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel</title>
    """ + UI_STYLE + """
</head>
<body class="bg-[#0b0f1a] text-white flex flex-col md:flex-row min-h-screen">
    <div class="w-full md:w-64 bg-slate-900 border-r border-slate-800 p-6">
        <h2 class="text-xl font-bold mb-8 text-blue-500 flex items-center gap-2">
            <i class="fa fa-user-shield"></i> ADMIN PANEL
        </h2>
        <nav class="space-y-2">
            <a href="/admin" class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-800 transition"><i class="fa fa-th-large"></i> Dashboard</a>
            <a href="/admin/add" class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-800 transition"><i class="fa fa-plus-circle"></i> Add Movie</a>
            <a href="/admin/settings" class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-800 transition"><i class="fa fa-ad"></i> Ads & Slider</a>
            <a href="/" class="flex items-center gap-3 p-3 rounded-lg hover:bg-blue-900 transition mt-10 border-t border-slate-800"><i class="fa fa-external-link-alt"></i> View Site</a>
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
    conf = settings_col.find_one({"type": "config"})
    search = request.args.get('search')
    if search:
        movies = list(movies_col.find({"name": {"$regex": search, "$options": "i"}}))
    else:
        movies = list(movies_col.find().sort("_id", -1))
    return render_template_string(USER_LAYOUT, movies=movies, conf=conf)

@app.route('/admin')
def admin_dash():
    movies = list(movies_col.find().sort("_id", -1))
    return render_template_string(ADMIN_LAYOUT.replace('{% block content %}{% endblock %}', """
        <div class="flex justify-between items-center mb-8">
            <h1 class="text-2xl font-bold">Manage Movies</h1>
            <span class="bg-blue-600 px-4 py-1 rounded-full text-xs">Total: {{ movies|length }}</span>
        </div>
        <div class="glass rounded-xl overflow-x-auto">
            <table class="w-full text-left border-collapse">
                <thead class="bg-slate-800 text-slate-400 text-xs uppercase">
                    <tr>
                        <th class="p-4">Movie Info</th>
                        <th class="p-4">Category</th>
                        <th class="p-4">Action</th>
                    </tr>
                </thead>
                <tbody>
                    {% for m in movies %}
                    <tr class="border-t border-slate-800 hover:bg-slate-800/50 transition">
                        <td class="p-4 flex items-center gap-3">
                            <img src="{{ m.poster }}" class="w-12 h-16 rounded object-cover shadow-lg">
                            <div>
                                <p class="font-bold text-sm">{{ m.name }}</p>
                                <p class="text-[10px] text-slate-500">{{ m.badge }}</p>
                            </div>
                        </td>
                        <td class="p-4 text-sm text-slate-400">{{ m.category }}</td>
                        <td class="p-4">
                            <div class="flex gap-3">
                                <a href="/admin/edit/{{ m._id }}" class="text-blue-500 hover:text-white"><i class="fa fa-edit"></i></a>
                                <a href="/admin/delete/{{ m._id }}" class="text-red-500 hover:text-white" onclick="return confirm('Are you sure?')"><i class="fa fa-trash"></i></a>
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
        labels = request.form.getlist('link_label[]')
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
    return render_template_string(ADMIN_FORM_HTML, movie=None)

@app.route('/admin/edit/<id>', methods=['GET', 'POST'])
def edit_movie(id):
    movie = movies_col.find_one({"_id": ObjectId(id)})
    if request.method == 'POST':
        labels = request.form.getlist('link_label[]')
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
    return render_template_string(ADMIN_FORM_HTML, movie=movie)

@app.route('/admin/delete/<id>')
def delete_movie(id):
    movies_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

@app.route('/admin/settings', methods=['GET', 'POST'])
def settings():
    conf = settings_col.find_one({"type": "config"})
    if request.method == 'POST':
        slider_urls = request.form.get('slider').split('\n')
        ads = {k: request.form.get(k) for k in conf['ads'].keys()}
        settings_col.update_one({"type": "config"}, {"$set": {
            "slider": [u.strip() for u in slider_urls if u.strip()],
            "ads": ads
        }})
        return redirect('/admin/settings')
    return render_template_string(ADMIN_SETTINGS_HTML, conf=conf, slider_text="\n".join(conf['slider']))

# --- Admin HTML Templates ---

ADMIN_FORM_HTML = ADMIN_LAYOUT.replace('{% block content %}{% endblock %}', """
<div class="max-w-3xl mx-auto glass p-6 md:p-8 rounded-2xl shadow-2xl">
    <h2 class="text-xl font-bold mb-6 text-blue-500">{{ 'Update Movie' if movie else 'Add New Movie' }}</h2>
    <form method="POST" class="space-y-5">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 uppercase">Movie Name</label>
                <input type="text" name="name" value="{{ movie.name if movie else '' }}" class="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 outline-none focus:border-blue-500 transition" required>
            </div>
            <div class="space-y-1">
                <label class="text-xs font-bold text-slate-500 uppercase">Category</label>
                <select name="category" class="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 outline-none">
                    <option value="Action" {{ 'selected' if movie and movie.category=='Action' }}>Action</option>
                    <option value="Drama" {{ 'selected' if movie and movie.category=='Drama' }}>Drama</option>
                    <option value="Horror" {{ 'selected' if movie and movie.category=='Horror' }}>Horror</option>
                    <option value="Thriller" {{ 'selected' if movie and movie.category=='Thriller' }}>Thriller</option>
                    <option value="Romance" {{ 'selected' if movie and movie.category=='Romance' }}>Romance</option>
                </select>
            </div>
        </div>
        <div class="space-y-1">
            <label class="text-xs font-bold text-slate-500 uppercase">Poster URL</label>
            <input type="text" name="poster" value="{{ movie.poster if movie else '' }}" class="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 outline-none focus:border-blue-500" required>
        </div>
        <div class="space-y-1">
            <label class="text-xs font-bold text-slate-500 uppercase">Badge (HD, 4K, Subtitle)</label>
            <input type="text" name="badge" value="{{ movie.badge if movie else '' }}" class="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 outline-none" placeholder="e.g. 1080p HD">
        </div>

        <div id="btn-container" class="space-y-3">
            <label class="block text-xs font-bold text-slate-500 uppercase">Download / Watch Buttons</label>
            {% if movie %}
                {% for link in movie.links %}
                <div class="flex gap-2">
                    <input type="text" name="link_label[]" value="{{ link.label }}" class="w-1/3 bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs" placeholder="Button Name">
                    <input type="text" name="link_url[]" value="{{ link.url }}" class="w-2/3 bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs" placeholder="URL">
                </div>
                {% endfor %}
            {% endif %}
        </div>
        <button type="button" onclick="addBtn()" class="text-blue-500 text-xs font-bold hover:underline">+ ADD NEW BUTTON</button>

        <div class="pt-6 flex gap-4">
            <button type="submit" class="bg-blue-600 hover:bg-blue-700 px-8 py-3 rounded-lg font-bold shadow-lg transition">SAVE MOVIE</button>
            <a href="/admin" class="bg-slate-700 px-8 py-3 rounded-lg font-bold">CANCEL</a>
        </div>
    </form>
</div>
<script>
    function addBtn() {
        const div = document.createElement('div');
        div.className = "flex gap-2 animate-pulse";
        div.innerHTML = `<input type="text" name="link_label[]" class="w-1/3 bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs" placeholder="Button Name" required><input type="text" name="link_url[]" class="w-2/3 bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs" placeholder="URL" required>`;
        document.getElementById('btn-container').appendChild(div);
        setTimeout(() => div.classList.remove('animate-pulse'), 500);
    }
</script>
""")

ADMIN_SETTINGS_HTML = ADMIN_LAYOUT.replace('{% block content %}{% endblock %}', """
<h1 class="text-2xl font-bold mb-8">Site Settings & Ad Management</h1>
<form method="POST" class="space-y-6">
    <div class="glass p-6 rounded-xl">
        <h3 class="text-sm font-bold text-blue-400 mb-4 uppercase tracking-wider">Main Slider Images</h3>
        <p class="text-[10px] text-slate-500 mb-2">Paste image URLs (one per line)</p>
        <textarea name="slider" rows="5" class="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-xs font-mono">{{ slider_text }}</textarea>
    </div>
    
    <div class="glass p-6 rounded-xl">
        <h3 class="text-sm font-bold text-yellow-500 mb-4 uppercase tracking-wider">Ad Code Management</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            {% for key, val in conf.ads.items() %}
            <div class="space-y-1">
                <label class="text-[10px] font-bold text-slate-400 uppercase">{{ key }} AD Code</label>
                <textarea name="{{ key }}" rows="3" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-[10px] font-mono">{{ val }}</textarea>
            </div>
            {% endfor %}
        </div>
    </div>
    <button type="submit" class="bg-green-600 hover:bg-green-700 px-10 py-4 rounded-xl font-bold shadow-2xl transition">UPDATE SYSTEM</button>
</form>
""")

if __name__ == '__main__':
    app.run(debug=True)
