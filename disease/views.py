# disease/views.py
import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image

from .mongo_client import diseases_col, users_col, history_col
from .model_loader import predict_disease
from .gradcam import generate_gradcam

# ─────────────────────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _parse_body(request):
    try:
        return json.loads(request.body), None
    except json.JSONDecodeError:
        return None, JsonResponse({"message": "Invalid JSON"}, status=400)

# Example password/token helpers (replace with your actual implementations)
def hash_password(password):
    return password + "_hashed"

def verify_password(password, hashed):
    return hash_password(password) == hashed

def generate_token(email, name, role):
    return f"token_for_{email}"

def get_user_from_request(request):
    # Example: Replace with your actual auth logic
    token = request.headers.get("Authorization")
    if token == "test-token":
        return {"email": "test@example.com", "name": "Test User", "role": "user"}
    return None

# ─────────────────────────────────────────────────────────────────────────────
# DETECT DISEASE ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
def detect_disease(request):
    if request.method == "GET":
        return JsonResponse({"message": "API is working"})

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not request.FILES.get("image"):
        return JsonResponse({"error": "No image uploaded. POST with field 'image'."}, status=400)

    try:
        pil_img = Image.open(request.FILES["image"])
    except Exception as e:
        return JsonResponse({"error": f"Invalid image: {e}"}, status=400)

    img_for_gradcam = pil_img.copy()
    disease_name, confidence, class_index, keras_model = predict_disease(pil_img)
    confidence_percent = round(confidence * 100, 2)

    if confidence < 0.60:
        return JsonResponse({
            "error": "low_confidence",
            "confidence": confidence_percent,
            "message": "This image does not appear to be a valid plant leaf."
        }, status=200)

    disease = diseases_col.find_one({"name": disease_name}, {"_id": 0})
    if not disease:
        return JsonResponse({"error": f"'{disease_name}' not in database."}, status=404)

    gradcam_b64 = generate_gradcam(img_for_gradcam, keras_model, class_index)
    user_data = get_user_from_request(request)
    if user_data:
        history_col.insert_one({
            "user_email": user_data["email"],
            "disease_name": disease_name,
            "plant_name": disease.get("plant_name", ""),
            "confidence": confidence_percent,
            "detected_at": datetime.utcnow(),
        })

    return JsonResponse({
        "name": disease.get("name"),
        "plant_name": disease.get("plant_name"),
        "description": disease.get("description"),
        "severity": disease.get("severity"),
        "symptoms": disease.get("symptoms"),
        "treatment": disease.get("treatment"),
        "prevention": disease.get("prevention"),
        "confidence": confidence_percent,
        "gradcam_image": gradcam_b64,
    })

# ─────────────────────────────────────────────────────────────────────────────
# USERS / AUTH
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
def register(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    data, err = _parse_body(request)
    if err:
        return err

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    phone = data.get("phone", "").strip()
    password = data.get("password", "")

    if not all([name, email, phone, password]):
        return JsonResponse({"message": "All fields are required"}, status=400)
    if users_col.find_one({"email": email}):
        return JsonResponse({"message": "Email already registered"}, status=409)

    users_col.insert_one({
        "name": name,
        "email": email,
        "phone": phone,
        "password": hash_password(password),
        "role": "user",
        "is_active": True,
        "created_at": datetime.utcnow(),
    })
    return JsonResponse({"success": True, "message": "Account created successfully"}, status=201)

@csrf_exempt
def login(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    data, err = _parse_body(request)
    if err:
        return err

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return JsonResponse({"message": "Email and password required"}, status=400)

    user = users_col.find_one({"email": email})
    if not user or not verify_password(password, user["password"]):
        return JsonResponse({"message": "Invalid email or password"}, status=401)
    if not user.get("is_active", True):
        return JsonResponse({"message": "Account deactivated"}, status=403)

    token = generate_token(user["email"], user["name"], user.get("role", "user"))
    return JsonResponse({
        "token": token,
        "name": user["name"],
        "email": user["email"],
        "role": user.get("role", "user"),
    })

# ─────────────────────────────────────────────────────────────────────────────
# DISEASE ENCYCLOPEDIA
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
def get_diseases(request):
    diseases = list(diseases_col.find({}, {"_id": 0}).sort("plant_name", 1))
    return JsonResponse({"diseases": diseases})

@csrf_exempt
def get_disease_detail(request, disease_name):
    disease = diseases_col.find_one({"name": disease_name}, {"_id": 0})
    if not disease:
        return JsonResponse({"error": "Not found"}, status=404)
    return JsonResponse(disease)