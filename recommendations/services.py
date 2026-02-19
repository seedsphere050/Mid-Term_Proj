# from django.conf import settings

# def get_recommended_plants(temp, humidity, condition):
#     collection = settings.PLANT_COLLECTION

#     query = {
#         "min_temp": {"$lte": temp},
#         "max_temp": {"$gte": temp},
#         "min_humidity": {"$lte": humidity},
#         "max_humidity": {"$gte": humidity},
#         "suitable_climate": condition
#     }

#     plants = collection.find(query)

#     return [
#         {
#             "name": plant["name"],
#             "category": plant["category"],
#             "soil_type": plant["soil_type"]
#         }
#         for plant in plants
#     ]
from django.conf import settings

def get_recommended_plants(
    climate_zone_id,
    plant_type=None,
    maintenance_level=None
):
    """
    Dynamic plant recommendation based on MongoDB data only
    """

    collection = settings.mongo_db["plants"]

    # Mandatory filter
    query = {
        "climate_zone_id": int(climate_zone_id)
    }

    # Optional filters (STRING based)
    if plant_type:
        query["plant_type"] = plant_type.lower()

    if maintenance_level:
        query["maintenance_level"] = maintenance_level.lower()

    plants = collection.find(query, {"_id": 0})

    return list(plants)