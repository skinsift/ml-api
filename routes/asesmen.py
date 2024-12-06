import os
import tensorflow as tf
import numpy as np
from fastapi import APIRouter, Depends , File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from connect import get_db
from utils import get_current_user
from models.models import User
from tensorflow.keras.preprocessing import image

router = APIRouter()

TFLITE_MODEL_PATH = "models/skintype_model.tflite"
    
@router.post("/asesmen")
async def predict_skin_type(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    try:
        # Simpan file gambar sementara
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        # Muat model TensorFlow Lite
        interpreter = tf.lite.Interpreter(model_path=TFLITE_MODEL_PATH)
        interpreter.allocate_tensors()

        # Proses gambar
        img = image.load_img(file_path, target_size=(224, 224))
        img_array = image.img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0).astype(np.float32)

        # Kelola tensor input dan output
        input_index = interpreter.get_input_details()[0]['index']
        output_index = interpreter.get_output_details()[0]['index']

        # Inference
        interpreter.set_tensor(input_index, img_array)
        interpreter.invoke()
        predictions = interpreter.get_tensor(output_index)

        # Mapping hasil prediksi ke kelas
        class_names = ['Berjerawat', 'Berminyak', 'Kering', 'Normal']
        predicted_class = np.argmax(predictions)

        # Hapus file gambar sementara
        os.remove(file_path)

        return {"skin_type": class_names[predicted_class]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
