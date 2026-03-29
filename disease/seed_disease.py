"""
seed_diseases.py
----------------
Populates MongoDB with rich disease data for all 38 plant classes.
Run ONCE from the seedsphere_backend folder:

    python disease_detection/seed_diseases.py

Your .env must be present in seedsphere_backend/ before running.
"""
import os, json
from pathlib import Path
from dotenv import load_dotenv
import pymongo

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

client = pymongo.MongoClient(
    host=os.getenv("MONGO_HOST", "localhost"),
    port=int(os.getenv("MONGO_PORT", 27017)),
    username=os.getenv("MONGO_USER", "seedsphere_admin"),
    password=os.getenv("MONGO_PASSWORD", "SeedSphere@123"),
    authSource=os.getenv("MONGO_AUTH_SOURCE", "admin"),
)

db = client[os.getenv("MONGO_DB", "seedsphere")]
diseases_col = db["diseases"]
diseases_col.create_index("name", unique=True)

with open(BASE_DIR / "ml_model" / "class_indices.json") as f:
    class_indices = json.load(f)

# ── Rich disease data for key classes ────────────────────────────────────────
# For classes not listed here, a clean auto-generated entry is created.
RICH_DATA = {
    "Tomato___Late_blight": {
        "plant_name": "Tomato (Solanum lycopersicum)",
        "description": "Late blight is a fast-moving, devastating disease caused by the water mould Phytophthora infestans — the same pathogen responsible for the Irish Potato Famine. It can destroy an entire crop within days under cool, moist conditions.",
        "severity": "High",
        "symptoms": ["Water-soaked, pale green or brown lesions on leaves", "White fuzzy mould on the underside of leaves in humid conditions", "Dark brown patches spreading across stems", "Firm, brown, greasy-looking rot on fruit", "Entire plant may collapse within 1–2 weeks if untreated"],
        "treatment": {
            "chemical": ["Apply copper-based fungicide (Copper Hydroxide) immediately", "Chlorothalonil or Mancozeb every 7 days during wet weather"],
            "mechanical": ["Remove and bag all infected plant material immediately", "Do NOT compost infected tissue"],
            "schedule": "Begin spraying preventively before disease appears during wet, cool periods (below 24°C)."
        },
        "prevention": ["Space plants 60–90 cm apart for airflow", "Avoid overhead watering — use drip irrigation", "Mulch soil to prevent soil splash onto lower leaves", "Plant resistant varieties (e.g., Legend, Mountain Magic)"]
    },
    "Tomato___Early_blight": {
        "plant_name": "Tomato (Solanum lycopersicum)",
        "description": "Early blight is caused by Alternaria solani and typically starts on older, lower leaves, working its way upward. It reduces photosynthetic area and weakens the plant, reducing fruit yield.",
        "severity": "Medium",
        "symptoms": ["Dark brown spots with distinctive concentric rings (target-board pattern)", "Yellow halo surrounding each lesion", "Lesions first appear on the oldest, lowest leaves", "Stems may develop dark, sunken cankers near the soil line", "Fruit develops dark, leathery rot near the stem end"],
        "treatment": {
            "chemical": ["Chlorothalonil, Mancozeb, or Copper fungicides applied every 7–10 days", "Azoxystrobin (Quadris) for severe infections"],
            "mechanical": ["Remove and destroy affected lower leaves immediately", "Sanitise pruning tools between plants"],
            "schedule": "Start treatments when first symptoms appear or after any period of leaf wetness > 8 hours."
        },
        "prevention": ["Rotate crops — avoid planting tomatoes in the same bed for 2 years", "Remove all crop debris at end of season", "Avoid working with plants when foliage is wet"]
    },
    "Tomato___Bacterial_spot": {
        "plant_name": "Tomato (Solanum lycopersicum)",
        "description": "Bacterial spot is caused by Xanthomonas species and spreads rapidly through rain splash and contaminated tools. It causes significant fruit blemishing that makes tomatoes unmarketable.",
        "severity": "Medium",
        "symptoms": ["Small, water-soaked circular spots on leaves", "Spots turn brown-black with yellow margins", "Raised, scabby, wart-like lesions on fruit", "Defoliation in severe cases, exposing fruit to sunscald"],
        "treatment": {
            "chemical": ["Copper bactericide (copper hydroxide + mancozeb) every 5–7 days", "Acibenzolar-S-methyl (Actigard) as a plant defense activator"],
            "mechanical": ["Remove heavily infected plant parts", "Avoid overhead irrigation"],
            "schedule": "Begin applications at transplanting and continue through the season."
        },
        "prevention": ["Use certified disease-free seed", "Treat seeds with hot water (50°C for 25 minutes) before planting", "Avoid working in the field when plants are wet"]
    },
    "Potato___Late_blight": {
        "plant_name": "Potato (Solanum tuberosum)",
        "description": "The same Phytophthora infestans that destroys tomatoes devastates potato crops. It caused the Great Famine of 1845–1852 and remains one of the most economically damaging plant diseases globally.",
        "severity": "High",
        "symptoms": ["Dark, water-soaked lesions on leaf edges and tips", "White sporulation ring visible on lesion undersides", "Stems turn dark brown and collapse", "Tubers develop reddish-brown dry rot that extends inward"],
        "treatment": {
            "chemical": ["Metalaxyl + Mancozeb (Ridomil Gold) every 7 days", "Cymoxanil + Famoxadone for systemic protection"],
            "mechanical": ["Destroy infected haulm before harvest", "Do not store infected tubers"],
            "schedule": "Preventive spraying essential before disease onset during cool, wet periods."
        },
        "prevention": ["Plant certified disease-free seed potatoes", "Hill soil around stems to protect tubers", "Harvest tubers in dry conditions and cure before storage"]
    },
    "Apple___Apple_scab": {
        "plant_name": "Apple (Malus domestica)",
        "description": "Apple scab caused by Venturia inaequalis is the most common apple disease worldwide. It primarily affects leaves and fruit, causing cosmetic damage that makes fruit commercially unmarketable.",
        "severity": "Medium",
        "symptoms": ["Olive-green to brown velvety spots on upper leaf surface", "Corresponding lesions on lower leaf surface", "Lesions on fruit appear as dark, scabby, corky patches", "Severe infections cause leaf curl and early leaf drop"],
        "treatment": {
            "chemical": ["Captan or Myclobutanil fungicide at green tip through petal fall", "Lime sulfur during dormant season"],
            "mechanical": ["Rake and remove fallen leaves in autumn to reduce overwintering spores"],
            "schedule": "Follow an infection period model — spray within 24–48 hours of each infection event."
        },
        "prevention": ["Plant scab-resistant varieties (e.g., Redfree, Liberty, GoldRush)", "Prune for good airflow and light penetration", "Apply urea to fallen leaves in autumn to speed decomposition"]
    },
    "Peach___healthy": {
        "plant_name": "Peach (Prunus persica)",
        "description": "This entry represents the optimal phenotype of Prunus persica. A healthy peach tree requires an open canopy to allow sunlight to reach the inner fruiting wood, preventing the self-shading that leads to branch dieback.",
        "severity": "None",
        "symptoms": ["Leaves are uniformly green with no yellowing between veins", "Margins are smooth and not curled or thickened", "Bark lenticels are visible but not weeping or swollen", "New growth consists of 30–45 cm of reddish-green wood annually", "Terminal buds are intact and free of flagging (wilt)"],
        "treatment": {
            "mechanical": ["Fruit thinning (removing 50–70% of young fruit) to ensure size and tree health", "Summer pruning of water sprouts"],
            "chemical": ["None; prophylactic dormant oil for scale and mites"],
            "schedule": "Continuous monitoring for Peach Tree Borer at the soil line."
        },
        "prevention": ["Ensure soil is well-drained; peaches cannot tolerate waterlogged roots", "Maintain a 90–120 cm weed-free circle around the trunk", "Apply nitrogen in early spring only", "Thin fruit when marble-sized to prevent branch breakage"]
    },
    "Tomato___healthy": {
        "plant_name": "Tomato (Solanum lycopersicum)",
        "description": "A healthy tomato plant shows vigorous growth with deep green foliage, sturdy stems, and no signs of lesions, spots, or wilting. Proper nutrition and airflow are key to maintaining this state.",
        "severity": "None",
        "symptoms": ["Deep green leaves with no spots, yellowing, or curling", "Sturdy main stem with visible leaf axil buds", "Flowers are bright yellow and drop cleanly after pollination", "No white fly, aphid, or mite colonies visible on undersides of leaves"],
        "treatment": {"mechanical": ["None required"], "chemical": ["None required"], "schedule": "Continue regular monitoring."},
        "prevention": ["Maintain consistent soil moisture through mulching and drip irrigation", "Feed with balanced fertiliser (NPK 10-10-10) at transplant, then switch to low-nitrogen at flowering", "Stake or cage plants to keep foliage off the ground"]
    },
}

# ── Seed all 38 classes ────────────────────────────────────────────────────
created = updated = 0

for class_name in class_indices.keys():
    parts      = class_name.split("___")
    plant_raw  = parts[0].replace("_", " ") if len(parts) > 1 else "Unknown"
    disease_raw = parts[1].replace("_", " ") if len(parts) > 1 else class_name.replace("_", " ")
    is_healthy = "healthy" in class_name.lower()

    if class_name in RICH_DATA:
        doc = {"name": class_name, **RICH_DATA[class_name]}
    else:
        doc = {
            "name":        class_name,
            "plant_name":  plant_raw,
            "description": f"{'Healthy ' + plant_raw + ' plant.' if is_healthy else disease_raw + ' affecting ' + plant_raw + '.'}",
            "severity":    "None" if is_healthy else "Unknown",
            "symptoms":    ["No disease symptoms present. Plant appears healthy."] if is_healthy
                           else ["Refer to agricultural extension resources for detailed symptom list."],
            "treatment": {
                "mechanical": ["No treatment required." if is_healthy else "Remove visibly infected plant parts."],
                "chemical":   ["None required." if is_healthy else "Consult local agronomist for appropriate fungicide or bactericide."],
                "schedule":   "Routine monitoring only." if is_healthy else "Begin treatment immediately upon symptom detection.",
            },
            "prevention": ["Maintain good cultural practices: proper spacing, watering, and fertilisation."],
        }

    result = diseases_col.update_one(
        {"name": class_name},
        {"$setOnInsert": doc},
        upsert=True
    )
    if result.upserted_id:
        created += 1
        print(f"  ✅ Created : {class_name}")
    else:
        print(f"  ⏭  Exists  : {class_name}")

print(f"\n{'─'*50}")
print(f"Done. {created} created | {38 - created} already existed")
print(f"MongoDB collection 'diseases' now has {diseases_col.count_documents({})} entries.")
