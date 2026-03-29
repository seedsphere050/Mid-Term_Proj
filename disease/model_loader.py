import os
import json
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image as keras_image
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# MODEL_PATH        = os.path.join(BASE_DIR, "ml_model", "SeedSphere_MobileNetV2.keras")
# CLASS_INDICES_PATH = os.path.join(BASE_DIR, "ml_model", "class_indices.json")
MODEL_PATH = os.path.join(BASE_DIR, "disease", "ml_model", "SeedSphere_MobileNetV2.keras")
CLASS_INDICES_PATH = os.path.join(BASE_DIR, "disease", "ml_model", "class_indices.json")
# Load once at server startup
model = load_model(MODEL_PATH)

with open(CLASS_INDICES_PATH, "r") as f:
    raw_indices = json.load(f)

index_to_class = {int(v): k for k, v in raw_indices.items()}


def predict_disease(pil_img):
    """
    Args:   PIL Image
    Returns: (disease_name, confidence_float, class_index, model)
             class_index + model are passed to Grad-CAM.
    """
    img = pil_img.convert("RGB").resize((224, 224))
    arr = keras_image.img_to_array(img)
    arr = np.expand_dims(arr, axis=0)
    arr = preprocess_input(arr)

    preds        = model.predict(arr)
    class_index  = int(np.argmax(preds, axis=1)[0])
    confidence   = float(np.max(preds))
    disease_name = index_to_class.get(class_index, "Unknown")

    return disease_name, confidence, class_index, model
