import os
from flask import Flask, render_template_string, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "secret_movie_key"

# --- MongoDB Connection ---
# নিচের লিংকে আপনার নিজের MongoDB URI বসান
MONGO_URI = "mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@cluster.mongodb.net/myDatabase"
client = MongoClient(MONGO_URI)
db = client['movie_portal']
movies_col = db['movies']
settings_col = db['settings']

# Initial Settings Check (Slider & Ads)
if not settings_col.find_one({"type": "config"}):
    settings_col.insert_one({
        "type": "config",
        "slider": [],
        "ads": {
            "popunder": "", "socialbar": "", "native": "",
            "header": "", "footer": "", "middle": "", "banner": ""
        }
    })

# --- Premium UI Templates (CSS & Components) ---
LAYOUT_START = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Premium Movie Portal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        body { font-family: 'Inter', sans-serif; background-color: #0f172a; color: white; }
        .glass { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
        .slider-container { overflow: hidden; position: relative; border-radius: 15px; }
        .slide { display: none; width: 100%; height: 400px; object-fit: cover; }
        .active-slide { display: block; animation: fade 0.8s ease-in-out; }
        @keyframes fade { from { opacity: 0.4; } to { opacity: 1; } }
    </style>
    {{ ads.popunder | safe }}
    {{ ads.socialbar | safe }}
</head>
<body>
    <nav class="glass sticky top-0 z-50 px-6 py-4 flex justify-between items-center mb-6">
        <a href="/" class="text-2xl font-bold text-blue-500">MOVIE<span class="text-white">FLIX</span></a>
        <div class="flex items-center gap-4">
            <form action="/" method="GET" class="hidden md:flex bg-gray-800 rounded-lg px-3 py-1 border border-gray-700">
                <input type="text" name="search" placeholder="Search movies..." class="bg-transparent border-none outline-none text-sm p-1 w-64">
                <button type="submit"><i class="fa fa-search text-gray-400"></i></button>
            </form>
            <a href="/admin" class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-sm font-semibold transition">Admin</a>
        </div>
    </nav>
    <div class="container mx-auto px-4">
        <div class="w-full mb-4 text-center">{{ ads.header | safe }}</div>
"""

LAYOUT_END = """
        <div class="w-full mt-8 text-center border-t border-gray-800 pt-6">{{ ads.footer | safe }}</div>
        <footer class="py-10 text-center text-gray-500 text-sm">
            &copy; 2024 MovieFlix Premium - All Rights Reserved.
        </footer>
    </div>
    <script>
        let currentSlide = 0;
        const slides = document.querySelectorAll('.slide');
        function showSlides() {
            if(slides.length == 0) return;
            slides.forEach(s => s.classList.remove('active-slide'));
            currentSlide = (currentSlide + 1) % slides.length;
            slides[currentSlide].classList.add('active-slide');
            setTimeout(showSlides, 4000);
        }
        showSlides();
    </script>
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
        movies = list(movies_col.find())
    
    return render_template_string(f"""
        {LAYOUT_START}
        
        <!-- Premium Slider -->
        {% if conf.slider %}
        <div class="slider-container mb-8 shadow-2xl">
            {% for img in conf.slider %}
            <img src="{{{{ img }}}}" class="slide w-full">
            {% endfor %}
        </div>
        {% endif %}

        <div class="w-full mb-6">{{ ads.middle | safe }}</div>

        <!-- Movie Section -->
        <h2 class="text-xl font-bold mb-6 flex items-center gap-2">
            <span class="w-2 h-6 bg-blue-600 rounded"></span> Recent Uploads
        </h2>

        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
            {% for movie in movies %}
            <div class="glass rounded-xl overflow-hidden group hover:scale-105 transition duration-300">
                <div class="relative">
                    <img src="{{{{ movie.poster }}}}" class="w-full h-64 object-cover">
                    <span class="absolute top-2 left-2 bg-yellow-500 text-black text-xs font-bold px-2 py-1 rounded">
                        {{{{ movie.badge }}}}
                    </span>
                </div>
                <div class="p-4">
                    <p class="text-xs text-blue-400 font-semibold mb-1 uppercase">{{{{ movie.category }}}}</p>
                    <h3 class="font-bold text-sm h-10 overflow-hidden">{{{{ movie.name }}}}</h3>
                    
                    <div class="mt-3 flex flex-col gap-2">
                        {% for link in movie.links %}
                        <a href="{{{{ link.url }}}}" target="_blank" class="bg-gray-700 hover:bg-blue-600 text-center text-xs py-2 rounded transition">
                            <i class="fa fa-download mr-1"></i> {{{{ link.label }}}}
                        </a>
                        {% endfor %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <div class="mt-8 text-center">{{ ads.native | safe }}</div>
        {LAYOUT_END}
    """, conf=conf, movies=movies, ads=conf['ads'])

# --- Admin Panel ---

@app.route('/admin')
def admin_dashboard():
    movies = list(movies_col.find())
    return render_template_string("""
        {% extends "base_admin" %}
        {% block content %}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="glass p-6 rounded-xl border-l-4 border-blue-500">
                <h3 class="text-gray-400">Total Movies</h3>
                <p class="text-3xl font-bold">{{ movies|length }}</p>
            </div>
        </div>
        <div class="glass rounded-xl overflow-hidden">
            <table class="w-full text-left">
                <thead class="bg-gray-800">
                    <tr>
                        <th class="p-4">Movie</th>
                        <th class="p-4">Category</th>
                        <th class="p-4">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for m in movies %}
                    <tr class="border-t border-gray-800">
                        <td class="p-4 flex items-center gap-3">
                            <img src="{{ m.poster }}" class="w-10 h-10 rounded object-cover">
                            {{ m.name }}
                        </td>
                        <td class="p-4">{{ m.category }}</td>
                        <td class="p-4">
                            <a href="/admin/edit/{{ m._id }}" class="text-blue-400 mr-3"><i class="fa fa-edit"></i></a>
                            <a href="/admin/delete/{{ m._id }}" class="text-red-400" onclick="return confirm('Delete?')"><i class="fa fa-trash"></i></a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endblock %}
    """, movies=movies)

@app.route('/admin/add', methods=['GET', 'POST'])
def add_movie():
    if request.method == 'POST':
        labels = request.form.getlist('link_label[]')
        urls = request.form.getlist('link_url[]')
        links = [{"label": labels[i], "url": urls[i]} for i in range(len(labels))]
        
        movie_data = {
            "name": request.form.get('name'),
            "poster": request.form.get('poster'),
            "badge": request.form.get('badge'),
            "category": request.form.get('category'),
            "links": links
        }
        movies_col.insert_one(movie_data)
        return redirect('/admin')
    
    return render_template_string(ADMIN_FORM_TEMPLATE, movie=None)

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
    return render_template_string(ADMIN_FORM_TEMPLATE, movie=movie)

@app.route('/admin/delete/<id>')
def delete_movie(id):
    movies_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

@app.route('/admin/settings', methods=['GET', 'POST'])
def settings():
    conf = settings_col.find_one({"type": "config"})
    if request.method == 'POST':
        slider_urls = request.form.get('slider').split('\n')
        ads = {
            "popunder": request.form.get('popunder'),
            "socialbar": request.form.get('socialbar'),
            "native": request.form.get('native'),
            "header": request.form.get('header'),
            "footer": request.form.get('footer'),
            "middle": request.form.get('middle'),
            "banner": request.form.get('banner'),
        }
        settings_col.update_one({"type": "config"}, {"$set": {"slider": [u.strip() for u in slider_urls if u.strip()], "ads": ads}})
        return redirect('/admin/settings')
    
    slider_text = "\n".join(conf['slider'])
    return render_template_string("""
        {% extends "base_admin" %}
        {% block content %}
        <form method="POST" class="space-y-6">
            <div class="glass p-6 rounded-xl">
                <h3 class="text-lg font-bold mb-4">Slider Images (One URL per line)</h3>
                <textarea name="slider" rows="4" class="w-full bg-gray-800 border-gray-700 rounded-lg p-3 text-sm">{{ slider_text }}</textarea>
            </div>
            
            <div class="glass p-6 rounded-xl">
                <h3 class="text-lg font-bold mb-4 text-yellow-500">Ad Code Management</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {% for key, val in conf.ads.items() %}
                    <div>
                        <label class="block text-xs uppercase text-gray-400 mb-1">{{ key }} Ad</label>
                        <textarea name="{{ key }}" rows="3" class="w-full bg-gray-900 border-gray-700 rounded-lg p-2 text-xs font-mono">{{ val }}</textarea>
                    </div>
                    {% endfor %}
                </div>
            </div>
            <button type="submit" class="bg-green-600 px-8 py-3 rounded-lg font-bold hover:bg-green-700 transition">Update Settings</button>
        </form>
        {% endblock %}
    """, conf=conf, slider_text=slider_text)

# --- Admin Layout Helper ---
@app.context_processor
def inject_admin_layout():
    return dict(base_admin="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-[#0b1120] text-white flex min-h-screen">
    <div class="w-64 bg-[#0f172a] border-r border-gray-800 p-6 flex-shrink-0">
        <h2 class="text-2xl font-bold mb-10 text-blue-500">ADMIN Panel</h2>
        <nav class="space-y-4 text-gray-400">
            <a href="/admin" class="flex items-center gap-3 hover:text-white transition"><i class="fa fa-home"></i> Dashboard</a>
            <a href="/admin/add" class="flex items-center gap-3 hover:text-white transition"><i class="fa fa-plus-circle"></i> Add Movie</a>
            <a href="/admin/settings" class="flex items-center gap-3 hover:text-white transition"><i class="fa fa-cog"></i> Settings & Ads</a>
            <a href="/" class="flex items-center gap-3 hover:text-white transition pt-10 border-t border-gray-800"><i class="fa fa-globe"></i> View Site</a>
        </nav>
    </div>
    <main class="flex-grow p-10">
        {% block content %}{% endblock %}
    </main>
</body>
</html>
""")

ADMIN_FORM_TEMPLATE = """
{% extends "base_admin" %}
{% block content %}
<div class="max-w-3xl mx-auto glass p-8 rounded-2xl">
    <h2 class="text-2xl font-bold mb-6">{{ 'Edit' if movie else 'Add' }} Movie</h2>
    <form method="POST" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
            <div>
                <label class="text-sm text-gray-400">Movie Name</label>
                <input type="text" name="name" value="{{ movie.name if movie else '' }}" class="w-full bg-gray-800 border-none rounded-lg p-3" required>
            </div>
            <div>
                <label class="text-sm text-gray-400">Category</label>
                <select name="category" class="w-full bg-gray-800 border-none rounded-lg p-3">
                    <option value="Action" {% if movie and movie.category == 'Action' %}selected{% endif %}>Action</option>
                    <option value="Horror" {% if movie and movie.category == 'Horror' %}selected{% endif %}>Horror</option>
                    <option value="Drama" {% if movie and movie.category == 'Drama' %}selected{% endif %}>Drama</option>
                </select>
            </div>
        </div>
        <div>
            <label class="text-sm text-gray-400">Poster URL</label>
            <input type="text" name="poster" value="{{ movie.poster if movie else '' }}" class="w-full bg-gray-800 border-none rounded-lg p-3" required>
        </div>
        <div>
            <label class="text-sm text-gray-400">Badge Text (HD, 4K, Dual Audio)</label>
            <input type="text" name="badge" value="{{ movie.badge if movie else '' }}" class="w-full bg-gray-800 border-none rounded-lg p-3">
        </div>

        <div id="links-area" class="space-y-3">
            <label class="block text-sm text-gray-400">Download Buttons</label>
            {% if movie %}
                {% for link in movie.links %}
                <div class="flex gap-2">
                    <input type="text" name="link_label[]" value="{{ link.label }}" class="w-1/3 bg-gray-900 rounded-lg p-2 text-sm" placeholder="Button Name">
                    <input type="text" name="link_url[]" value="{{ link.url }}" class="w-2/3 bg-gray-900 rounded-lg p-2 text-sm" placeholder="URL">
                </div>
                {% endfor %}
            {% endif %}
        </div>
        
        <button type="button" onclick="addLink()" class="text-blue-500 text-sm font-semibold">+ Add Button Link</button>

        <div class="pt-6 flex gap-4">
            <button type="submit" class="bg-blue-600 px-6 py-2 rounded-lg font-bold">Save Data</button>
            <a href="/admin" class="bg-gray-700 px-6 py-2 rounded-lg">Back</a>
        </div>
    </form>
</div>
<script>
    function addLink() {
        const area = document.getElementById('links-area');
        const div = document.createElement('div');
        div.className = "flex gap-2";
        div.innerHTML = `
            <input type="text" name="link_label[]" class="w-1/3 bg-gray-900 rounded-lg p-2 text-sm" placeholder="Button Name" required>
            <input type="text" name="link_url[]" class="w-2/3 bg-gray-900 rounded-lg p-2 text-sm" placeholder="URL" required>
        `;
        area.appendChild(div);
    }
</script>
{% endblock %}
"""

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))
