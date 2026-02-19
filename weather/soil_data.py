STATE_SOIL_MAP = {
    "Andhra Pradesh": ["Red", "Black"],
    "Arunachal Pradesh": ["Mountain", "Forest"],
    "Assam": ["Alluvial", "Laterite"],
    "Bihar": ["Alluvial"],
    "Chhattisgarh": ["Red", "Laterite"],
    "Goa": ["Laterite"],
    "Gujarat": ["Black", "Alluvial"],
    "Haryana": ["Alluvial"],
    "Himachal Pradesh": ["Mountain", "Forest"],
    "Jharkhand": ["Red", "Laterite"],
    "Karnataka": ["Red", "Black", "Laterite"],
    "Kerala": ["Laterite"],
    "Madhya Pradesh": ["Black"],
    "Maharashtra": ["Black"],
    "Manipur": ["Forest", "Mountain"],
    "Meghalaya": ["Laterite", "Forest"],
    "Mizoram": ["Forest"],
    "Nagaland": ["Forest"],
    "Odisha": ["Red", "Laterite"],
    "Punjab": ["Alluvial"],
    "Rajasthan": ["Sandy", "Desert"],
    "Sikkim": ["Mountain"],
    "Tamil Nadu": ["Red", "Laterite"],
    "Telangana": ["Red", "Black"],
    "Tripura": ["Laterite"],
    "Uttar Pradesh": ["Alluvial"],
    "Uttarakhand": ["Mountain", "Forest"],
    "West Bengal": ["Alluvial", "Laterite"]
}
def get_soil_from_state(state):
    if not state:
        return []
    return STATE_SOIL_MAP.get(state, [])