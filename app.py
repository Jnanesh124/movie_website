
from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

def get_movies(limit=50, language=None, quality=None, search=None):
    """Get movies from database with filters"""
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    
    query = "SELECT * FROM movies WHERE 1=1"
    params = []
    
    if language:
        query += " AND language = ?"
        params.append(language)
    
    if quality:
        query += " AND quality = ?"
        params.append(quality)
    
    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")
    
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    movies = cursor.fetchall()
    conn.close()
    
    # Convert to dict format
    movie_list = []
    for movie in movies:
        movie_list.append({
            'id': movie[0],
            'title': movie[1],
            'image_url': movie[2],
            'movie_url': movie[3],
            'quality': movie[4],
            'language': movie[5],
            'year': movie[6],
            'posted_date': movie[7],
            'telegram_user': movie[8]
        })
    
    return movie_list

@app.route('/')
def index():
    """Main page"""
    search = request.args.get('search', '')
    language = request.args.get('language', '')
    quality = request.args.get('quality', '')
    
    movies = get_movies(limit=50, language=language, quality=quality, search=search)
    
    # Get unique languages and qualities for filters
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT language FROM movies")
    languages = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT quality FROM movies")
    qualities = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return render_template('index.html', 
                         movies=movies, 
                         languages=languages, 
                         qualities=qualities,
                         current_language=language,
                         current_quality=quality,
                         search_query=search)

@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    """Movie detail page"""
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
    movie = cursor.fetchone()
    conn.close()
    
    if not movie:
        return "Movie not found", 404
    
    movie_data = {
        'id': movie[0],
        'title': movie[1],
        'image_url': movie[2],
        'movie_url': movie[3],
        'quality': movie[4],
        'language': movie[5],
        'year': movie[6],
        'posted_date': movie[7],
        'telegram_user': movie[8]
    }
    
    return render_template('movie_detail.html', movie=movie_data)

@app.route('/api/movies')
def api_movies():
    """API endpoint for movies"""
    limit = int(request.args.get('limit', 50))
    language = request.args.get('language')
    quality = request.args.get('quality')
    search = request.args.get('search')
    
    movies = get_movies(limit=limit, language=language, quality=quality, search=search)
    return jsonify(movies)

if __name__ == '__main__':
    # Initialize database
    if not os.path.exists('movies.db'):
        conn = sqlite3.connect('movies.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                image_url TEXT,
                movie_url TEXT,
                quality TEXT,
                language TEXT,
                year TEXT,
                posted_date TEXT,
                telegram_user TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
