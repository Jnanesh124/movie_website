
import sqlite3
import os

def fix_image_urls():
    """Fix image URLs in database to work with Flask static serving"""
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    
    # Get all movies with image URLs
    cursor.execute("SELECT id, image_url FROM movies WHERE image_url IS NOT NULL")
    movies = cursor.fetchall()
    
    for movie_id, image_url in movies:
        if image_url and not image_url.startswith('/static/'):
            # If it's a local file path, convert to proper static URL
            if os.path.exists(image_url):
                filename = os.path.basename(image_url)
                new_url = f"/static/images/{filename}"
                cursor.execute("UPDATE movies SET image_url = ? WHERE id = ?", (new_url, movie_id))
                print(f"Updated movie {movie_id}: {image_url} -> {new_url}")
    
    conn.commit()
    conn.close()
    print("Image URLs fixed!")

if __name__ == '__main__':
    fix_image_urls()
