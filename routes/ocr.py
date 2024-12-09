from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from PIL import Image
from sqlalchemy.orm import Session, joinedload
from models.models import User, Notes, Ingredient
from connect import get_db
from utils import get_current_user, create_response
import pytesseract, string, re, os, logging
import pandas as pd

router = APIRouter()
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# Load the ingredients dataset
ingredients_path = "models/ingredients.csv"
if not os.path.exists(ingredients_path):
    raise FileNotFoundError(f"File {ingredients_path} not found.")

df = pd.read_csv(ingredients_path)

# List ingredients from the name column
ingredients = df['nama'].dropna().str.lower().tolist()

# Levenshtein distance function
def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

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

# Closest match function for ingredients
def find_closest_match(part_cleaned, ingredients, threshold):
    closest_match = None
    closest_distance = float("inf")

    for candidate in ingredients:
        if abs(len(part_cleaned) - len(candidate)) <= threshold:  # To make it faster, compare with similar length
            distance = levenshtein_distance(part_cleaned, candidate)
            if distance < closest_distance:
                closest_distance = distance
                closest_match = candidate

    return closest_match, closest_distance

# Text preprocessing function
def preprocess_text(text):
    text = text.translate(str.maketrans('', '', string.punctuation + '-'))  # Remove punctuation
    text = " ".join(text.split())  # Remove extra spaces
    return text

# String matching function with OCR results
def process_ocr_text(ocr_text, ingredients, threshold=1):
    detected_ingredients = []
    ingredients_set = set(ingredients)

    # Keywords
    keywords = ['komposisi', 'ingredients', 'ingredient']
    match = None
    keyword_found = False

    for keyword in keywords:
        match = re.search(r'\b' + re.escape(keyword) + r'\b', ocr_text.lower())
        if match:
            keyword_found = True
            break

    # Split text
    ocr_parts = ocr_text.split(",") if not keyword_found else ocr_text[match.end():].split(",")

    for part in ocr_parts:
        part_cleaned = preprocess_text(part.strip().lower())
        if "/" in part_cleaned:
            part_cleaned = part_cleaned.split("/")[0].strip()

        if part_cleaned in ingredients_set:
            detected_ingredients.append(part_cleaned)
        else:
            closest_match, closest_distance = find_closest_match(part_cleaned, ingredients, threshold)
            if closest_distance <= threshold:
                detected_ingredients.append(closest_match)

    return detected_ingredients

from sqlalchemy import case, desc, asc

@router.post("/ocr")
async def ocr_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")

    try:
        # Load image
        image = Image.open(file.file)

        # Extract text using pytesseract OCR
        ocr_text = pytesseract.image_to_string(image)

        # Process OCR text to find ingredients
        detected_ingredients = process_ocr_text(ocr_text, ingredients)

        # Define custom category order using case, replace float('inf') with 999999
        category_order = case(
            (Ingredient.rating == "Terbaik", 1),
            (Ingredient.rating == "Baik", 2),
            (Ingredient.rating == "Rata-Rata", 3),
            (Ingredient.rating == "Buruk", 4),
            (Ingredient.rating == "Terburuk", 5),
            (Ingredient.rating == "Belum Dinilai", 6),
            else_=999999  # Use a large number instead of infinity
        )

        # Query with sorted ingredients from database
        matched_ingredients = db.query(Ingredient).filter(
            Ingredient.nama.in_(detected_ingredients)
        ).order_by(asc(category_order)).all()

        # Query Notes to get user-specific ingredient preferences
        user_notes = db.query(Notes).filter(Notes.users_id == current_user.Users_ID).join(Ingredient).filter(
            Ingredient.nama.in_(detected_ingredients)
        ).all()

        # Format response to include only selected fields
        response = []
        warnings = {
            "Bahan Cocok": set(),
            "Bahan Tidak Cocok": set(),
        }

        # Check preferences for each detected ingredient in user notes
        for item in matched_ingredients:
            ingredient_name = item.nama
            # Initialize flags for preferences
            suka_found = False
            tidak_suka_found = False

            # Find preferences in Notes for this ingredient
            for note in user_notes:
                if note.ingredient.nama == ingredient_name:
                    if note.notes == "Suka":
                        suka_found = True
                    elif note.notes == "Tidak Suka":
                        tidak_suka_found = True

            # Add warning based on preferences
            if suka_found:
                warnings["Bahan Cocok"].add(ingredient_name)
            elif tidak_suka_found:
                warnings["Bahan Tidak Cocok"].add(ingredient_name)

            # Add matched ingredient details to response
            response.append({
                "id": item.Id_Ingredients,
                "nama": item.nama,
                "rating": item.rating,
                "kategoriidn": item.kategoriidn
            })

        # Format warnings into structured JSON
        warnings_json = [
            {
                "category": category,
                "details": list(details)
            }
            for category, details in warnings.items() if details  # Include only non-empty categories
        ]
        return JSONResponse(content={
            "error": 'false',
            "message": 'success ocr',
            "matched_ingredients": response,
            "warnings": warnings_json  # Returning structured warnings
        })


    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")