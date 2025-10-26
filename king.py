#!/usr/bin/env python3
"""
Facebook Messenger Automation Bot - Terminal Version
Based on Original LORD DEVIL Script
"""

import sys
import warnings
import os
import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import sqlite3
import hashlib
import subprocess

warnings.filterwarnings("ignore")

# Tumhara exact same functions
def install_chromedriver():
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "webdriver-manager==4.0.1", "--no-cache-dir"
        ], capture_output=True, check=True)
        
        from webdriver_manager.chrome import ChromeDriverManager
        driver_path = ChromeDriverManager().install()
        return driver_path
    except Exception as e:
        print(f"ChromeDriver install failed: {e}")
        return None

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_configs (
            user_id INTEGER PRIMARY KEY,
            chat_id TEXT,
            name_prefix TEXT,
            delay INTEGER DEFAULT 10,
            cookies TEXT,
            messages TEXT,
            automation_running BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        if c.fetchone():
            return False, "Username already exists"
        
        password_hash = hash_password(password)
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                 (username, password_hash))
        user_id = c.lastrowid
        
        c.execute('''
            INSERT INTO user_configs 
            (user_id, chat_id, name_prefix, delay, cookies, messages) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, '', '[LORD DEVIL]', 10, '', 'Hello!\nHow are you?'))
        
        conn.commit()
        conn.close()
        return True, "User created successfully"
    except Exception as e:
        return False, f"Error creating user: {str(e)}"

def verify_user(username, password):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        password_hash = hash_password(password)
        c.execute('SELECT id FROM users WHERE username = ? AND password_hash = ?', 
                 (username, password_hash))
        result = c.fetchone()
        conn.close()
        
        return result[0] if result else None
    except:
        return None

def get_user_config(user_id):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT chat_id, name_prefix, delay, cookies, messages 
            FROM user_configs WHERE user_id = ?
        ''', (user_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            return {
                'chat_id': result[0] or '',
                'name_prefix': result[1] or '',
                'delay': result[2] or 10,
                'cookies': result[3] or '',
                'messages': result[4] or 'Hello!'
            }
        return None
    except:
        return None

def update_user_config(user_id, chat_id, name_prefix, delay, cookies, messages):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        c.execute('''
            INSERT OR REPLACE INTO user_configs 
            (user_id, chat_id, name_prefix, delay, cookies, messages, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, chat_id, name_prefix, delay, cookies, messages))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_automation_running(user_id):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        c.execute('SELECT automation_running FROM user_configs WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        conn.close()
        
        return result[0] if result else False
    except:
        return False

def set_automation_running(user_id, running):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        c.execute('UPDATE user_configs SET automation_running = ? WHERE user_id = ?', 
                 (running, user_id))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_username(user_id):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        c.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        result = c.fetchone()
        conn.close()
        
        return result[0] if result else "Unknown"
    except:
        return "Unknown"

# Tumhara exact same browser setup
def setup_browser():
    print('[+] Setting up Chrome browser...')
    
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Termux paths
    CHROME_PATH = "/data/data/com.termux/files/usr/bin/chromium"
    CHROMEDRIVER_PATH = "/data/data/com.termux/files/usr/bin/chromedriver"
    
    driver = None
    
    try:
        if os.path.exists(CHROMEDRIVER_PATH):
            service = Service(CHROMEDRIVER_PATH)
            if os.path.exists(CHROME_PATH):
                chrome_options.binary_location = CHROME_PATH
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print('[+] Chrome started with system chromedriver!')
            return driver
    except Exception as e:
        print(f'[-] System chromedriver failed: {e}')
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print('[+] Chrome started with webdriver-manager!')
        return driver
    except Exception as e:
        print(f'[-] Webdriver-manager failed: {e}')
    
    print('[-] All ChromeDriver methods failed!')
    raise Exception("ChromeDriver setup failed")

# Tumhara exact same find_message_input function
def find_message_input(driver, process_id='AUTO-1'):
    print(f'[{process_id}] Finding message input...')
    time.sleep(8)
    
    message_input_selectors = [
        'div[role="textbox"][contenteditable="true"][data-lexical-editor="true"]',
        'div[contenteditable="true"][role="textbox"][aria-label*="Message"]',
        'div[contenteditable="true"][role="textbox"]',
        'div[aria-label="Message"][contenteditable="true"]',
        'div[data-lexical-editor="true"]',
        'div[contenteditable="true"]',
        'textarea',
    ]
    
    for selector in message_input_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                try:
                    if element.is_displayed() and element.is_enabled():
                        is_editable = driver.execute_script("""
                            return arguments[0].contentEditable === 'true' || 
                                   arguments[0].tagName === 'TEXTAREA';
                        """, element)
                        
                        if is_editable:
                            print(f'[{process_id}] Found message input')
                            element.click()
                            time.sleep(0.5)
                            return element
                except:
                    continue
        except:
            continue
    
    print(f'[{process_id}] No message input found')
    return None

# Tumhara exact same send_messages function
def send_messages(config, user_id, process_id='AUTO-1'):
    driver = None
    message_rotation_index = 0
    messages_sent = 0
    
    try:
        print(f'[{process_id}] Starting automation...')
        driver = setup_browser()
        
        print(f'[{process_id}] Navigating to Facebook...')
        driver.get('https://www.facebook.com/')
        time.sleep(6)
        
        if config['cookies'] and config['cookies'].strip():
            print(f'[{process_id}] Adding cookies...')
            cookie_array = config['cookies'].split(';')
            for cookie in cookie_array:
                cookie_trimmed = cookie.strip()
                if cookie_trimmed:
                    first_equal_index = cookie_trimmed.find('=')
                    if first_equal_index > 0:
                        name = cookie_trimmed[:first_equal_index].strip()
                        value = cookie_trimmed[first_equal_index + 1:].strip()
                        try:
                            driver.add_cookie({
                                'name': name,
                                'value': value,
                                'domain': '.facebook.com',
                                'path': '/'
                            })
                        except:
                            pass
        
        if config['chat_id']:
            chat_id = config['chat_id'].strip()
            print(f'[{process_id}] Opening conversation {chat_id}...')
            driver.get(f'https://www.facebook.com/messages/e2ee/t/{chat_id}')
            print(f'[{process_id}] Trying URL: https://www.facebook.com/messages/e2ee/t/{chat_id}')
        else:
            print(f'[{process_id}] Opening messages...')
            driver.get('https://www.facebook.com/messages')
        
        time.sleep(12)
        
        message_input = find_message_input(driver, process_id)
        
        if not message_input:
            print(f'[{process_id}] Message input not found!')
            set_automation_running(user_id, False)
            return 0
        
        delay = int(config['delay'])
        messages_list = [msg.strip() for msg in config['messages'].split('\n') if msg.strip()]
        
        if not messages_list:
            messages_list = ['Hello!']
        
        # Running state manually manage karenge
        running = True
        
        while running and messages_sent < 100:
            # Get next message (tumhara same logic)
            if messages_list:
                message = messages_list[message_rotation_index % len(messages_list)]
                message_rotation_index += 1
            else:
                message = 'Hello!'
            
            if config['name_prefix']:
                message_to_send = f"{config['name_prefix']} {message}"
            else:
                message_to_send = message
            
            try:
                driver.execute_script("""
                    const element = arguments[0];
                    const message = arguments[1];
                    
                    element.focus();
                    element.click();
                    
                    if (element.tagName === 'DIV' && element.contentEditable === 'true') {
                        element.innerHTML = '';
                        element.innerText = message;
                    } else if (element.tagName === 'TEXTAREA') {
                        element.value = '';
                        element.value = message;
                    } else {
                        element.textContent = '';
                        element.textContent = message;
                    }
                    
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                """, message_input, message_to_send)
                
                time.sleep(1)
                
                sent = False
                send_buttons = driver.find_elements(By.CSS_SELECTOR, 
                    '[aria-label*="Send" i], [data-testid="send-button"], button[type="submit"]')
                for btn in send_buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        driver.execute_script("arguments[0].click();", btn)
                        sent = True
                        break
                
                if not sent:
                    message_input.send_keys(Keys.ENTER)
                    sent = True
                
                time.sleep(1)
                
                messages_sent += 1
                print(f'[{process_id}] Message {messages_sent} sent: {message_to_send}')
                
                # Check if user wants to stop
                try:
                    # Non-blocking input check
                    import select
                    if select.select([sys.stdin], [], [], 0)[0]:
                        key = sys.stdin.read(1)
                        if key.lower() == 'q':
                            print(f'\n[{process_id}] Stopping by user request...')
                            running = False
                            break
                except:
                    pass
                
                time.sleep(delay)
                
            except Exception as e:
                print(f'[{process_id}] Error sending message: {str(e)}')
                break
        
        print(f'[{process_id}] Automation stopped! Total messages sent: {messages_sent}')
        set_automation_running(user_id, False)
        return messages_sent
        
    except Exception as e:
        print(f'[{process_id}] Fatal error: {str(e)}')
        set_automation_running(user_id, False)
        return 0
    finally:
        if driver:
            try:
                driver.quit()
                print(f'[{process_id}] Browser closed')
            except:
                pass

# Terminal Interface
def clear_screen():
    os.system('clear')

def print_banner():
    clear_screen()
    print("🔒" * 60)
    print("🤖 LORD DEVIL E2EE FACEBOOK CONVO - TERMINAL MODE")
    print("🔒" * 60)
    print()

def terminal_login():
    print_banner()
    print("📝 LOGIN TO YOUR ACCOUNT")
    print("=" * 50)
    
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    if not username or not password:
        print("❌ Username and password required!")
        return None
    
    user_id = verify_user(username, password)
    if user_id:
        print(f"✅ Welcome back, {username}!")
        return user_id
    else:
        print("❌ Invalid credentials!")
        return None

def terminal_signup():
    print_banner()
    print("📝 CREATE NEW ACCOUNT")
    print("=" * 50)
    
    username = input("Choose Username: ").strip()
    password = input("Choose Password: ").strip()
    confirm = input("Confirm Password: ").strip()
    
    if not username or not password:
        print("❌ Username and password required!")
        return None
    
    if password != confirm:
        print("❌ Passwords don't match!")
        return None
    
    success, message = create_user(username, password)
    if success:
        print(f"✅ {message}")
        return verify_user(username, password)
    else:
        print(f"❌ {message}")
        return None

def get_terminal_config(user_id):
    config = get_user_config(user_id)
    if not config:
        return None
    
    print_banner()
    print("⚙️  CURRENT CONFIGURATION")
    print("=" * 50)
    print(f"Chat ID: {config['chat_id']}")
    print(f"Prefix: {config['name_prefix']}") 
    print(f"Delay: {config['delay']} seconds")
    print(f"Messages: {len(config['messages'].splitlines())} messages")
    print()
    
    print("📝 UPDATE CONFIGURATION (press Enter to keep current)")
    print("=" * 50)
    
    chat_id = input(f"Chat ID [{config['chat_id']}]: ").strip()
    name_prefix = input(f"Name Prefix [{config['name_prefix']}]: ").strip()
    delay = input(f"Delay (seconds) [{config['delay']}]: ").strip()
    
    print("\nEnter Cookies (current will be kept if empty):")
    cookies_lines = []
    while True:
        line = input().strip()
        if line == "":
            break
        cookies_lines.append(line)
    cookies = ' '.join(cookies_lines)
    
    print("\nEnter Messages (one per line, empty line to finish):")
    messages = []
    while True:
        message = input().strip()
        if message == "" and messages:
            break
        if message:
            messages.append(message)
    
    # Update only changed values
    final_chat_id = chat_id if chat_id else config['chat_id']
    final_prefix = name_prefix if name_prefix else config['name_prefix']
    final_delay = int(delay) if delay else config['delay']
    final_cookies = cookies if cookies else config['cookies']
    final_messages = '\n'.join(messages) if messages else config['messages']
    
    if update_user_config(user_id, final_chat_id, final_prefix, final_delay, final_cookies, final_messages):
        print("✅ Configuration updated!")
        return get_user_config(user_id)
    else:
        print("❌ Failed to update configuration!")
        return config

def terminal_automation_control(user_id):
    config = get_user_config(user_id)
    if not config:
        print("❌ No configuration found!")
        return
    
    while True:
        print_banner()
        print("🚀 AUTOMATION CONTROL")
        print("=" * 50)
        print(f"Chat ID: {config['chat_id']}")
        print(f"Status: {'RUNNING' if get_automation_running(user_id) else 'STOPPED'}")
        print(f"Messages: {len(config['messages'].splitlines())}")
        print(f"Delay: {config['delay']} seconds")
        print()
        print("1. Start Automation")
        print("2. Stop Automation") 
        print("3. Edit Configuration")
        print("4. View Logs (if running)")
        print("5. Back to Main Menu")
        print()
        
        choice = input("Select option: ").strip()
        
        if choice == '1':
            if get_automation_running(user_id):
                print("❌ Automation is already running!")
                input("Press Enter to continue...")
                continue
            
            print("🚀 Starting automation... (Press 'q' to stop)")
            set_automation_running(user_id, True)
            
            # Start in separate thread
            def run_automation():
                send_messages(config, user_id)
            
            thread = threading.Thread(target=run_automation)
            thread.daemon = True
            thread.start()
            
            print("✅ Automation started in background!")
            input("Press Enter to continue...")
            
        elif choice == '2':
            set_automation_running(user_id, False)
            print("🛑 Automation stopped!")
            input("Press Enter to continue...")
            
        elif choice == '3':
            config = get_terminal_config(user_id)
            
        elif choice == '4':
            print("📊 Logs are displayed in real-time during automation")
            input("Press Enter to continue...")
            
        elif choice == '5':
            break
        else:
            print("❌ Invalid option!")
            input("Press Enter to continue...")

def main_menu():
    init_db()
    
    while True:
        print_banner()
        print("📱 MAIN MENU")
        print("=" * 50)
        print("1. Login")
        print("2. Sign Up") 
        print("3. Exit")
        print()
        
        choice = input("Select option: ").strip()
        
        if choice == '1':
            user_id = terminal_login()
            if user_id:
                while True:
                    print_banner()
                    print(f"👤 Welcome, {get_username(user_id)}!")
                    print("=" * 50)
                    print("1. Automation Control")
                    print("2. Configuration")
                    print("3. Logout")
                    print()
                    
                    user_choice = input("Select option: ").strip()
                    
                    if user_choice == '1':
                        terminal_automation_control(user_id)
                    elif user_choice == '2':
                        get_terminal_config(user_id)
                    elif user_choice == '3':
                        set_automation_running(user_id, False)
                        break
                    else:
                        print("❌ Invalid option!")
                        input("Press Enter to continue...")
                        
        elif choice == '2':
            user_id = terminal_signup()
            if user_id:
                input("Press Enter to continue...")
                
        elif choice == '3':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option!")
            input("Press Enter to continue...")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"💥 Error: {e}")
