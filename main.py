import uvicorn
import os  # Impor os untuk mengambil variabel lingkungan
from fastapi import FastAPI
from routes import asesmen, ocr

# Inisialisasi aplikasi FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from Cloud Run"}

app.include_router(asesmen.router)
app.include_router(ocr.router)

if __name__ == "__main__":
    server_port = int(os.environ.get('PORT', 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=server_port, log_level="info")