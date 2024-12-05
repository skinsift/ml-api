from fastapi import APIRouter, Depends 
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from connect import get_db
from utils import get_current_user
from models import User

router = APIRouter()

@router.post("/predict_images")
def predict_skin_type(file_path, tflite_model_path, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    return {"message": "Hello from Cloud Run"}

    # interpreter = tf.lite.Interpreter(model_path=tflite_model_path)
    # interpreter.allocate_tensors()

    # img = image.load_img(file_path, target_size=(224, 224))
    # img_array = image.img_to_array(img) / 255.0
    # img_array = np.expand_dims(img_array, axis=0).astype(np.float32)

    # # Manage input and output
    # input_index = interpreter.get_input_details()[0]['index']
    # output_index = interpreter.get_output_details()[0]['index']

    # # Inference
    # interpreter.set_tensor(input_index, img_array)
    # interpreter.invoke()
    # predictions = interpreter.get_tensor(output_index)

    # # Mapping results to classes
    # class_names = ['Berjerawat', 'Berminyak', 'Kering', 'Normal']
    # predicted_class = np.argmax(predictions)
    return class_names[predicted_class]