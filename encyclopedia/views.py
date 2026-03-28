from collections import defaultdict
from rest_framework.views import APIView
from rest_framework.response import Response
from .mongo import plants_collection

class PlantsAPIView(APIView):
    """
    Returns all plants in a flat array, mapped for frontend
    """
    def get(self, request):
        plants_cursor = plants_collection.find({}).sort("common_name", 1)
        plants_list = []

        for idx, plant in enumerate(plants_cursor, start=1):
            plants_list.append({
                "id": idx,
                "name": plant.get("common_name"),
                "category": plant.get("plant_type")[0] if plant.get("plant_type") else "Unknown",
                "img": plant.get("images")[0] if plant.get("images") else "",
                "description": plant.get("description", ""),
                "family": plant.get("scientific_name", ""),
                "origin": ", ".join(plant.get("environment", {}).get("season", [])) if plant.get("environment") else "",
                "care": ", ".join([plant.get("care", {}).get("maintenance_level", ""), plant.get("care", {}).get("watering_frequency", "")]).strip()
            })
        return Response(plants_list)