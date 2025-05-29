import os
import random
import time
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import openai
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# Konfigurasi
SCOPES = ['https://www.googleapis.com/auth/blogger']
BLOG_ID = 'YOUR_BLOG_ID_HERE'  # Ganti dengan ID blog Anda
OPENAI_API_KEY = 'YOUR_OPENAI_API_KEY'
CREDENTIALS_FILE = 'credentials.json'  # File credentials dari Google API

# Daftar judul postingan
JUDUL_POSTINGAN = [
    "Tips Produktivitas Kerja di Era Digital",
    "Cara Membangun Kebiasaan Baik yang Konsisten",
    "Panduan Pemula untuk Investasi Saham",
    "Teknologi Terkini yang Mengubah Dunia",
    "Rahasia Memasak Makanan Sehat dan Lezat"
]

# Inisialisasi OpenAI
openai.api_key = OPENAI_API_KEY

def generate_content(title):
    """Generate konten blog menggunakan AI"""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Anda adalah penulis blog profesional."},
            {"role": "user", "content": f"Tulis artikel blog tentang {title}. Gunakan bahasa yang menarik dan mudah dipahami. Sertakan beberapa paragraf dengan subjudul."}
        ],
        temperature=0.7,
        max_tokens=1500
    )
    return response.choices[0].message.content

def generate_image(title):
    """Generate gambar sederhana untuk blog"""
    # Anda bisa mengganti ini dengan API seperti DALL-E atau Stable Diffusion
    # Di sini kita buat gambar sederhana dengan teks judul
    
    # Ukuran gambar
    width, height = 800, 400
    
    # Warna acak untuk background
    bg_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    
    # Buat gambar baru
    image = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    # Hitung posisi teks
    text_width, text_height = draw.textsize(title, font=font)
    x = (width - text_width) / 2
    y = (height - text_height) / 2
    
    # Gambar teks
    draw.text((x, y), title, fill=(255, 255, 255), font=font)
    
    # Simpan gambar ke buffer
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr

def upload_image_to_blogger(service, image_data, title):
    """Upload gambar ke Blogger"""
    media_body = {
        'name': f'{title.replace(" ", "_")}.png',
        'mimeType': 'image/png'
    }
    
    try:
        image = service.media().insert(
            blogId=BLOG_ID,
            media_body=media_body,
            body={'title': title}
        ).execute()
        
        # Upload data gambar
        upload_url = image['uploadLocation']
        headers = {'Content-Type': 'image/png'}
        response = requests.put(upload_url, data=image_data, headers=headers)
        
        if response.status_code == 200:
            return image['url']
        else:
            print(f"Gagal upload gambar: {response.text}")
            return None
    except Exception as e:
        print(f"Error upload gambar: {e}")
        return None

def create_blog_post(service, title, content, image_url=None):
    """Buat postingan blog"""
    body = {
        "title": title,
        "content": f"<img src='{image_url}'/><br/><br/>{content}" if image_url else content,
        "labels": ["AI Generated", "Otomatis"]
    }
    
    try:
        post = service.posts().insert(
            blogId=BLOG_ID,
            body=body,
            isDraft=False
        ).execute()
        
        print(f"Postingan berhasil dibuat: {post['url']}")
        return post
    except Exception as e:
        print(f"Error membuat postingan: {e}")
        return None

def authenticate_blogger():
    """Autentikasi ke Blogger API"""
    creds = None
    
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('blogger', 'v3', credentials=creds)

def main():
    # Autentikasi
    service = authenticate_blogger()
    
    # Pilih judul acak
    title = random.choice(JUDUL_POSTINGAN)
    print(f"Membuat postingan dengan judul: {title}")
    
    # Generate konten
    print("Membuat konten dengan AI...")
    content = generate_content(title)
    
    # Generate gambar
    print("Membuat gambar...")
    image_data = generate_image(title)
    
    # Upload gambar
    print("Mengupload gambar...")
    image_url = upload_image_to_blogger(service, image_data, title)
    
    # Buat postingan
    print("Membuat postingan blog...")
    create_blog_post(service, title, content, image_url)
    
    print("Proses selesai!")

if __name__ == '__main__':
    main()
