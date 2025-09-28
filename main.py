
import threading
import time
import asyncio
from bot import main as bot_main
from app import app

def run_bot():
    """Run the Telegram bot with proper asyncio loop"""
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        bot_main()
    finally:
        loop.close()

def run_web():
    """Run the Flask web application"""
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    print("🚀 Starting Cinevood Bot & Website...")
    
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Give bot time to start
    time.sleep(2)
    
    # Start web application
    print("🌐 Starting website on http://0.0.0.0:5000")
    run_web()
