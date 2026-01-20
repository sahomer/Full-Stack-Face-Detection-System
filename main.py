import cv2
import numpy as np
import sqlite3
import io
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr

app = FastAPI()


def resim_analiz_et(resim_baytlari):
   
    nparr = np.frombuffer(resim_baytlari, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
  
  
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    


    faces = face_cascade.detectMultiScale(
        gray, 
        scaleFactor=1.03, 
        minNeighbors=3, 
        minSize=(20, 20)
    )
    
    
    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

 


    _, buffer = cv2.imencode('.jpg', img)
    return buffer.tobytes()




@app.get("/")
def ana_sayfa():
    return {"mesaj": "Face Detection System Live - Multiple Face Support Enabled"}

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    """
    Android'den gelen fotoğrafı analiz eder ve yüzleri kareye alarak geri döner.
    """
    resim_icerigi = await file.read()
    islenmis_resim = resim_analiz_et(resim_icerigi)
    
    if islenmis_resim is None:
        return {"hata": "Resim işlenemedi"}
    
    return StreamingResponse(io.BytesIO(islenmis_resim), media_type="image/jpeg")



class Kullanici(BaseModel):
    isim: str 
    email: EmailStr 

def veritabani_kur(): 
    conn = sqlite3.connect("uygulama.db") 
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kullanicilar 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, isim TEXT, email TEXT)
    ''')
    conn.commit()
    conn.close()

veritabani_kur()

@app.post("/kayit")
def kayit_ekle(user: Kullanici):
    conn = sqlite3.connect("uygulama.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO kullanicilar (isim, email) VALUES (?, ?)", (user.isim, user.email))
    conn.commit()
    conn.close()
    return {"durum": "basarili", "mesaj": f"{user.isim} kaydedildi!"}

@app.get("/kullanicilar")
def listele():
    conn = sqlite3.connect("uygulama.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM kullanicilar")
    veriler = cursor.fetchall()
    conn.close()
    return {"kullanicilar": veriler}

@app.delete("/kullanici/{kullanici_id}")
def kullanici_sil(kullanici_id: int):
    conn = sqlite3.connect("uygulama.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM kullanicilar WHERE id = ?", (kullanici_id,))
    conn.commit()
    conn.close()
    return {"durum": "basarili", "mesaj": f"ID {kullanici_id} silindi"}