
import os
import re
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import sqlite3
from datetime import datetime
import urllib.parse

# Database setup
def init_db():
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

def extract_movie_info(text):
    """Extract movie information from text"""
    # Extract title (usually the first line or before quality info)
    lines = text.strip().split('\n')
    title = lines[0] if lines else "Unknown Movie"
    
    # Clean title from common patterns
    title = re.sub(r'🎬|📽️|🍿|▶️|⭐|🎭', '', title).strip()
    title = re.sub(r'\d{4}.*?(HD|CAM|DVDRip|BluRay|WEB-DL)', '', title).strip()
    
    # Extract quality
    quality_match = re.search(r'(480p|720p|1080p|4K|HD|CAM|DVDRip|BluRay|WEB-DL)', text, re.IGNORECASE)
    quality = quality_match.group(1) if quality_match else "HD"
    
    # Extract year
    year_match = re.search(r'(19|20)\d{2}', text)
    year = year_match.group(0) if year_match else "2024"
    
    # Extract language
    language = "Hindi"
    if re.search(r'(english|eng)', text, re.IGNORECASE):
        language = "English"
    elif re.search(r'(tamil|tam)', text, re.IGNORECASE):
        language = "Tamil"
    elif re.search(r'(telugu|tel)', text, re.IGNORECASE):
        language = "Telugu"
    elif re.search(r'(malayalam|mal)', text, re.IGNORECASE):
        language = "Malayalam"
    elif re.search(r'(kannada|kan)', text, re.IGNORECASE):
        language = "Kannada"
    
    # Extract URLs
    urls = re.findall(r'https?://[^\s]+', text)
    
    # Separate image URLs and movie URLs
    image_url = None
    movie_urls = []
    
    for url in urls:
        if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
            image_url = url
        else:
            movie_urls.append(url)
    
    return {
        'title': title,
        'quality': quality,
        'year': year,
        'language': language,
        'image_url': image_url,
        'movie_urls': movie_urls
    }

def save_movie(movie_info, username):
    """Save movie to database"""
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    
    movie_url = movie_info['movie_urls'][0] if movie_info['movie_urls'] else ""
    
    cursor.execute('''
        INSERT INTO movies (title, image_url, movie_url, quality, language, year, posted_date, telegram_user)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        movie_info['title'],
        movie_info['image_url'],
        movie_url,
        movie_info['quality'],
        movie_info['language'],
        movie_info['year'],
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        username
    ))
    
    movie_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return movie_id

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    welcome_text = """
🎬 Welcome to Movie Bot! 🎭

Send me movie details with links and I'll automatically:
• Extract movie title and info
• Get cover image
• Post to website
• Organize by quality and language

Commands:
/movie - Post a new movie
/help - Show this help

Just send me text with movie details and download links!
    """
    await update.message.reply_text(welcome_text)

async def movie_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Movie command handler"""
    await update.message.reply_text(
        "🎬 Send me the movie details with download links!\n\n"
        "Format example:\n"
        "Movie Title (2024) Hindi HD\n"
        "Quality: 720p/1080p\n"
        "Download links...\n"
        "Image URL (optional)"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages with captions containing movie information"""
    if not update.message.photo:
        return
        
    caption = update.message.caption or ""
    username = update.effective_user.username or update.effective_user.first_name
    
    # Get the largest photo
    photo = update.message.photo[-1]
    
    # Get file info and download URL
    file = await context.bot.get_file(photo.file_id)
    photo_url = f"https://api.telegram.org/file/bot{context.bot.token}/{file.file_path}"
    
    # Check if caption contains URLs (likely movie post)
    if 'http' in caption:
        # Extract movie information from caption
        movie_info = extract_movie_info(caption)
        
        # Use the photo URL as image_url
        movie_info['image_url'] = photo_url
        
        # Save to database
        movie_id = save_movie(movie_info, username)
        
        # Create response with direct website link
        website_url = f"https://{os.getenv('REPL_SLUG', 'your-repl')}-{os.getenv('REPL_OWNER', 'your-username')}.replit.app"
        movie_url = f"{website_url}/movie/{movie_id}"
        
        response = f"""
✅ Movie with Poster Posted Successfully!

🎬 **{movie_info['title']}**
📅 Year: {movie_info['year']}
🎭 Language: {movie_info['language']}
📺 Quality: {movie_info['quality']}
🆔 Movie ID: #{movie_id}
🖼️ Poster: Uploaded

🔗 Direct Link: {movie_url}
        """
        
        # Create inline keyboard
        keyboard = [
            [InlineKeyboardButton("🎬 View Movie", url=movie_url)],
            [InlineKeyboardButton("🌐 Browse All Movies", url=website_url)],
            [InlineKeyboardButton("📱 Share Movie", switch_inline_query=f"Check out {movie_info['title']} {movie_url}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            "Please add movie details with download links in the photo caption!"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages with movie information"""
    text = update.message.text
    username = update.effective_user.username or update.effective_user.first_name
    
    # Check if message contains URLs (likely movie post)
    if text and 'http' in text:
        # Extract movie information
        movie_info = extract_movie_info(text)
        
        # Save to database
        movie_id = save_movie(movie_info, username)
        
        # Create response with direct website link
        website_url = f"https://{os.getenv('REPL_SLUG', 'your-repl')}-{os.getenv('REPL_OWNER', 'your-username')}.replit.app"
        movie_url = f"{website_url}/movie/{movie_id}"
        
        response = f"""
✅ Movie Posted Successfully!

🎬 **{movie_info['title']}**
📅 Year: {movie_info['year']}
🎭 Language: {movie_info['language']}
📺 Quality: {movie_info['quality']}
🆔 Movie ID: #{movie_id}

🔗 Direct Link: {movie_url}
        """
        
        # Create inline keyboard with website links
        keyboard = [
            [InlineKeyboardButton("🎬 View Movie", url=movie_url)],
            [InlineKeyboardButton("🌐 Browse All Movies", url=website_url)],
            [InlineKeyboardButton("📱 Share Movie", switch_inline_query=f"Check out {movie_info['title']} {movie_url}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            "Please send movie details with download links! Use /movie for help."
        )

def main():
    """Start the bot"""
    # Initialize database
    init_db()
    
    # Bot token
    BOT_TOKEN = "7999034847:AAEBOHzENqFZm1KqXWTjUHx7WlSaBFrRXJI"
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("movie", movie_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    print("🤖 Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)

if __name__ == '__main__':
    main()
