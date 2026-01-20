import cv2
import numpy as np
import sqlite3
import io
import mediapipe as mp
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr

app = FastAPI()

mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5)

def resim_analiz_et(resim_baytlari):
    nparr = np.frombuffer(resim_baytlari, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return None

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = face_detection.process(img_rgb)

    if results.detections:
        for detection in results.detections:
            bboxC = detection.location_data.relative_bounding_box
            ih, iw, _ = img.shape
            x, y, w, h = int(bboxC.xmin * iw), int(bboxC.ymin * ih), \
                         int(bboxC.width * iw), int(bboxC.height * ih)
            
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

    _, buffer = cv2.imencode('.jpg', img)
    return buffer.tobytes()

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

@app.get("/")
def ana_sayfa():
    return {"status": "active", "engine": "mediapipe"}

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    resim_icerigi = await file.read()
    islenmis_resim = resim_analiz_et(resim_icerigi)
    
    if islenmis_resim is None:
        return {"error": "Processing failed"}
    
    return StreamingResponse(io.BytesIO(islenmis_resim), media_type="image/jpeg")

@app.post("/kayit")
def kayit_ekle(user: Kullanici):
    conn = sqlite3.connect("uygulama.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO kullanicilar (isim, email) VALUES (?, ?)", (user.isim, user.email))
    conn.commit()
    conn.close()
    return {"status": "success"}

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
    return {"status": "deleted"}
