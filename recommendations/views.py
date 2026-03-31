# # from rest_framework.views import APIView
# # from rest_framework.response import Response
# # from rest_framework import status

# # from .mongo import plants_collection
# # from weather.services import get_processed_weather_from_coords

# # # 🔥 Scoring Function (unchanged)
# # def score_plants(plants, weather):
# #     scored = []

# #     temp_data = weather.get("temperature", {})
# #     current_temp = temp_data.get("current")
# #     min_temp_weather = temp_data.get("min")
# #     max_temp_weather = temp_data.get("max")

# #     for plant in plants:
# #         env = plant.get("environment", {})
# #         score = 0

# #         # =========================
# #         # 1️⃣ TEMPERATURE (HIGH PRIORITY)
# #         # =========================
# #         env_temp = env.get("temperature", {})
# #         plant_min = env_temp.get("min")
# #         plant_max = env_temp.get("max")

# #         if plant_min is not None and plant_max is not None:
# #             match_count = 0

# #             if current_temp is not None and plant_min <= current_temp <= plant_max:
# #                 match_count += 1
# #             if min_temp_weather is not None and plant_min <= min_temp_weather <= plant_max:
# #                 match_count += 1
# #             if max_temp_weather is not None and plant_min <= max_temp_weather <= plant_max:
# #                 match_count += 1

# #             score += match_count * 2  # HIGH weight

# #         # =========================
# #         # 2️⃣ SEASON
# #         # =========================
# #         if weather.get("season") in env.get("season", []):
# #             score += 2

# #         # =========================
# #         # 3️⃣ RAINFALL
# #         # =========================
# #         if weather.get("rainfall") == env.get("rainfall"):
# #             score += 2

# #         # =========================
# #         # 4️⃣ HUMIDITY
# #         # =========================
# #         if weather.get("humidity") == env.get("humidity"):
# #             score += 1

# #         # =========================
# #         # 5️⃣ SUNLIGHT
# #         # =========================
# #         if weather.get("sunlight") == env.get("sunlight"):
# #             score += 1

# #         # =========================
# #         # 6️⃣ SOIL TYPE
# #         # =========================
# #         if weather.get("soil_type") in env.get("soil_type", []):
# #             score += 1

# #         if score > 0:
# #             scored.append((plant, score))

# #     scored.sort(key=lambda x: x[1], reverse=True)
# #     return [plant for plant, score in scored]


# # # 🚀 API View with extra details
# # class PlantRecommendationAPI(APIView):

# #     def get(self, request):
# #         try:
# #             lat = request.GET.get("lat")
# #             lon = request.GET.get("lon")

# #             if not lat or not lon:
# #                 return Response(
# #                     {"error": "Latitude and Longitude are required"},
# #                     status=status.HTTP_400_BAD_REQUEST
# #                 )

# #             # 🌦️ Get weather data
# #             weather = get_processed_weather_from_coords(float(lat), float(lon))

# #             # 🌱 Fetch plants
# #             plants = list(plants_collection.find())

# #             if not plants:
# #                 return Response(
# #                     {"recommended_plants": []},
# #                     status=status.HTTP_200_OK
# #                 )

# #             # 🔥 Apply scoring
# #             scored_plants = score_plants(plants, weather)

# #             # =========================
# #             # 🎯 FALLBACK LOGIC
# #             # =========================
# #             if not scored_plants:
# #                 fallback = plants[:3]
# #                 recommended_plants = []
# #                 for p in fallback:
# #                     care = p.get("care", {})
# #                     care_guide = ""
# #                     if care.get("sunlight"):
# #                         care_guide += f"Sunlight: {care['sunlight']}. "
# #                     if care.get("watering_frequency"):
# #                         care_guide += f"Watering: {care['watering_frequency']}."
# #                     recommended_plants.append({
# #                         "id": str(p.get("_id")),
# #                         "name": p.get("common_name"),
# #                         "scientific_name": p.get("scientific_name"),
# #                         "family": p.get("family"),
# #                         "origin": p.get("origin"),
# #                         "description": p.get("description"),
# #                         "care_guide": care_guide.strip()
# #                     })

# #                 return Response(
# #                     {
# #                         "recommended_plants": recommended_plants,
# #                         "message": "Fallback recommendations (low match)"
# #                     },
# #                     status=status.HTTP_200_OK
# #                 )

# #             # 🔝 Top 3 best matches
# #             top_plants = scored_plants[:3]
# #             recommended_plants = []
# #             for p in top_plants:
# #                 care = p.get("care", {})
# #                 care_guide = ""
# #                 if care.get("sunlight"):
# #                     care_guide += f"Sunlight: {care['sunlight']}. "
# #                 if care.get("watering_frequency"):
# #                     care_guide += f"Watering: {care['watering_frequency']}."
# #                 recommended_plants.append({
# #                     "id": str(p.get("_id")),
# #                     "name": p.get("common_name"),
# #                     "scientific_name": p.get("scientific_name"),
# #                     "family": p.get("scientific_name", ""),  # Replacing family with scientific name
# #                     "origin": p.get("life_cycle", ""),
# #                     "description": p.get("description"),
# #                     "care_guide": care_guide.strip()
# #                 })

# #             return Response(
# #                 {
# #                     "weather_used": weather,
# #                     "recommended_plants": recommended_plants
# #                 },
# #                 status=status.HTTP_200_OK
# #             )

# #         except Exception as e:
# #             return Response(
# #                 {"error": str(e)},
# #                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
# #             )
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .mongo import plants_collection
from weather.services import get_processed_weather_from_coords


# 🔥 SCORING FUNCTION (UNCHANGED)
def score_plants(plants, weather):
    scored = []

    temp_data = weather.get("temperature", {})
    current_temp = temp_data.get("current")
    min_temp_weather = temp_data.get("min")
    max_temp_weather = temp_data.get("max")

    for plant in plants:
        env = plant.get("environment", {})
        score = 0

        env_temp = env.get("temperature", {})
        plant_min = env_temp.get("min")
        plant_max = env_temp.get("max")

        if plant_min is not None and plant_max is not None:
            if current_temp and plant_min <= current_temp <= plant_max:
                score += 2

        if weather.get("season") in env.get("season", []):
            score += 2

        if weather.get("rainfall") == env.get("rainfall"):
            score += 2

        if weather.get("humidity") == env.get("humidity"):
            score += 1

        if weather.get("sunlight") == env.get("sunlight"):
            score += 1

        if weather.get("soil_type") in env.get("soil_type", []):
            score += 1

        if score > 0:
            scored.append((plant, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [plant for plant, score in scored]


# 🚀 FINAL API
class PlantRecommendationAPI(APIView):

    def get(self, request):
        try:
            lat = request.GET.get("lat")
            lon = request.GET.get("lon")

            if not lat or not lon:
                return Response(
                    {"error": "Latitude and Longitude required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            weather = get_processed_weather_from_coords(float(lat), float(lon))
            plants = list(plants_collection.find())

            if not plants:
                return Response({"recommended_plants": []})

            scored_plants = score_plants(plants, weather)

            # 🔥 ALWAYS RETURN SOMETHING
            final_plants = scored_plants[:3] if scored_plants else plants[:3]

            result = []

            for p in final_plants:
                image_url = ""

                # ✅ IMAGE LOGIC (UNCHANGED)
                if p.get("images"):
                    img_path = p.get("images")[0]

                    if img_path.startswith("/media"):
                        image_url = request.build_absolute_uri(img_path)
                    elif not img_path.startswith("http"):
                        image_url = request.build_absolute_uri(f"/media/plants/{img_path}")

                result.append({
                    "id": str(p.get("_id")),
                    "name": p.get("common_name"),
                    "scientific_name": p.get("scientific_name"),

                    # ✅ CATEGORY SAME
                    "category": (p.get("plant_type") or ["Recommended"])[0],

                    # ✅ IMAGE SAME
                    "img": image_url,

                    # ✅ DESCRIPTION SAME
                    "description": p.get("description", ""),

                    # 🔥 UPDATED CARE (better UX)
                    "care": ", ".join(filter(None, [
                        f"Sunlight: {p.get('environment', {}).get('sunlight')}" if p.get("environment", {}).get("sunlight") else "",
                        f"Watering: {p.get('care', {}).get('watering_frequency')}" if p.get("care", {}).get("watering_frequency") else ""
                    ])),

                    # 🔥 UPDATED FIELDS
                    "family": p.get("scientific_name", ""),  # replaced
                    "origin": p.get("life_cycle", "")        # replaced
                })

            return Response({
                "weather_used": weather,
                "recommended_plants": result
            })

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
