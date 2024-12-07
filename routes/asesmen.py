import os
import tensorflow as tf
import numpy as np
import pandas as pd
import string
from fastapi import APIRouter, Depends , File, UploadFile, HTTPException, Form
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from connect import get_db
from utils import get_current_user, create_response
from models.models import User, Notes, Ingredient
from tensorflow.keras.preprocessing import image

router = APIRouter()

model_path = "models/skintype_model.tflite"
df = pd.read_csv('models/product_asesmen.csv')
df['ingredients'] = df['ingredients'].fillna('').astype(str)

def predict_skin_type(file_path: str, model_path: str) -> str:
    try:
        # Memuat model TFLite
        interpreter = tf.lite.Interpreter(model_path=model_path)
        interpreter.allocate_tensors()

        # Preprocessing gambar
        img = image.load_img(file_path, target_size=(224, 224))
        img_array = image.img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0).astype(np.float32)

        # Menentukan tensor input dan output
        input_index = interpreter.get_input_details()[0]['index']
        output_index = interpreter.get_output_details()[0]['index']

        # Melakukan prediksi
        interpreter.set_tensor(input_index, img_array)
        interpreter.invoke()
        predictions = interpreter.get_tensor(output_index)

        # Mapping hasil prediksi ke kelas
        class_names = ['Berjerawat', 'Berminyak', 'Kering', 'Normal']
        predicted_class = np.argmax(predictions)

        return class_names[predicted_class]
    except Exception as e:
        raise ValueError(f"Error in predict_skin_type: {e}")

# Remove punctuation for string matching
def remove_punctuation(text):
    return text.translate(str.maketrans('', '', string.punctuation))

# Levenshtein
def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        s1, s2 = s2, s1

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

dataset_ingredients = set(
    remove_punctuation(word.strip()).lower()
    for ing in df['ingredients']
    for word in ing.split(',')
)

# Correcting ingredients entered by the user
def koreksi_ingredients(input_string, dataset_ingredients, threshold=1):
    if not input_string:
        return []

    corrected_ingredients = []
    strings_to_check = [
        remove_punctuation(word.strip()).lower() for word in input_string.split(',')
    ]

    for string_to_check in strings_to_check:
        if string_to_check in dataset_ingredients:
            corrected_ingredients.append(string_to_check)
        else:
            closest_match = None
            closest_distance = float('inf')

            for candidate in dataset_ingredients:
                distance = levenshtein_distance(string_to_check, candidate)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_match = candidate

            if closest_distance <= threshold:
                corrected_ingredients.append(closest_match)

    return corrected_ingredients

# Product recommendations according to assessment
def recommended_product(kriteria, predicted_skin_type):
    sensitif = kriteria[0]
    tujuan = kriteria[1]
    fungsi = kriteria[2]
    hamil_menyusui = kriteria[3]
    ingredients = kriteria[4]

    # If the answer value for index 0 or sensitive is 'a' then sensitive skin type is also included in the filter
    if sensitif == 'a':
        jenis_kulit_list = [predicted_skin_type, 'Sensitif']
    else:
        jenis_kulit_list = [predicted_skin_type]  # If the value is not 'a' but 'b' then the skin type matches predicted_skin_type

    # Process ingredients if there is input from the user
    if ingredients and str(ingredients).lower() not in ['none', 'nan', '']:
        if isinstance(ingredients, list):
            corrected_ingredients = [
                koreksi_ingredients(ing, dataset_ingredients) for ing in ingredients
            ]
            corrected_ingredients = [item for sublist in corrected_ingredients for item in sublist]
        else:
            corrected_ingredients = koreksi_ingredients(ingredients, dataset_ingredients)

        corrected_ingredients_str = '|'.join(corrected_ingredients)

        if corrected_ingredients:
            produk = df[
                (df['jenis_kulit'].isin(jenis_kulit_list)) &
                (df['tujuan'] == tujuan) &
                (df['fungsi'].apply(lambda x: all(f in str(x).split(',') for f in fungsi))) &
                (df['hamil_menyusui'] == hamil_menyusui) &
                (~df['ingredients'].str.contains(corrected_ingredients_str, case=False, na=False))
            ]
        else:
            produk = df[
                (df['jenis_kulit'].isin(jenis_kulit_list)) &
                (df['tujuan'] == tujuan) &
                (df['fungsi'].apply(lambda x: all(f in str(x).split(',') for f in fungsi))) &
                (df['hamil_menyusui'] == hamil_menyusui)
            ]
    else:
        produk = df[
            (df['jenis_kulit'].isin(jenis_kulit_list)) &
            (df['tujuan'] == tujuan) &
            (df['fungsi'].apply(lambda x: all(f in str(x).split(',') for f in fungsi))) &
            (df['hamil_menyusui'] == hamil_menyusui)
        ]

    return produk['nama_product'].tolist()

def get_user_ingredients(user_id: str, db: Session):

    try:
        ingredients = (
            db.query(Ingredient.nama)
            .join(Notes, Notes.id_ingredients == Ingredient.Id_Ingredients)
            .filter(Notes.users_id == user_id)
            .all()
        )
        # Mengubah hasil query menjadi list string
        return [ingredient[0] for ingredient in ingredients]
    except Exception as e:
        raise ValueError(f"Error in get_user_ingredients: {e}")

@router.post("/asesmen")
async def asesmen(
    file: UploadFile = File(...),  # File tetap diterima sebagai UploadFile
    sensitif: str = Form(...),    # Ambil dari form-data
    tujuan: str = Form(...),
    fungsi: str = Form(...),      # Multi-value (string, dipisahkan koma)
    hamil_menyusui: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Split string untuk parameter 'fungsi'
        fungsi_list = fungsi.split(", ")  # Jika 'fungsi' berisi "a, b", hasilnya: ['a', 'b']

        # Input asesmen lainnya
        input_asesmen = [
            sensitif,
            tujuan,
            fungsi_list,
            hamil_menyusui,
            [],  # Ini placeholder untuk 'ingredients', nanti diisi dari database
        ]

        # Ambil predicted skin type
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        predicted_skin_type = predict_skin_type(file_path, model_path)

        # Ambil ingredients "Tidak Suka" dari database
        user_ingredients = get_user_ingredients(current_user.Users_ID, db)
        input_asesmen[-1] = user_ingredients  # Masukkan ingredients ke input asesmen

        # Rekomendasi produk
        product = recommended_product(input_asesmen, predicted_skin_type)

        # Hapus file sementara
        os.remove(file_path)

        return {"predicted_skin_type": predicted_skin_type, "recommended_products": product}
    #     return create_response(
    #     status_code=201,
    #     message="User registered successfully",
    #     data={
    #         "user_id": new_user.Users_ID,
    #         "username": new_user.Username,
    #         "email": new_user.Email,
    #         "created_at": new_user.created_at,  # Sertakan waktu pembuatan
    #     },
    # )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
