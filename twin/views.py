from django.shortcuts import render

# Create your views here.
# plants/views.py

import uuid
import os
import requests
from datetime import datetime
from django.utils import timezone
from django.utils.timezone import make_aware, is_naive
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
import pymongo
from rest_framework.parsers import JSONParser
from django.http import JsonResponse

from .serializers import PlantCreateSerializer, PlantUpdateSerializer
from .growth_engine import simulate_growth, PLANTS_WITH_GLB


# ── MongoDB connection (FIXED) ────────────────────────────────────────────────
_client = None
_db_handle = None

def _get_db():
    global _client, _db_handle
    if _db_handle is None:
        try:
            _client = pymongo.MongoClient("mongodb://localhost:27017/")
            _db_handle = _client["Seed"]   # ✅ FIXED

            print("✅ MongoDB connected to: Seed")

            # Indexes
            _db_handle['plant_profiles'].create_index('plant_id', unique=True)
            _db_handle['plant_models'].create_index([('plant_type', 1), ('stage', 1)])
            _db_handle['care_logs'].create_index([('plant_id', 1), ('logged_at', -1)])
            _db_handle['growth_logs'].create_index([('plant_id', 1), ('recorded_at', -1)])
        except Exception as e:
            print("❌ MongoDB error:", e)
            raise e

    return _db_handle


def _col(name):
    return _get_db()[name]


def _mongo_err(exc=None):
    if exc:
        print("MongoDB error:", exc)
    return JsonResponse({'error': 'MongoDB error occurred'}, status=500)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_simulation(doc):
    env = doc.get('environment', {})
    planting_date = doc.get('planting_date', timezone.now())

    if isinstance(planting_date, str):
        planting_date = datetime.fromisoformat(planting_date.replace('Z', '+00:00'))

    if is_naive(planting_date):
        planting_date = make_aware(planting_date)

    real_days = (timezone.now() - planting_date).total_seconds() / 86400

    return simulate_growth(
        plant_type=doc.get('plant_type', 'tulsi'),
        real_days=real_days,
        sunlight=env.get('sunlight', 'full_sun'),
        watering=env.get('watering_frequency', 'daily'),
        soil=env.get('soil_type', 'loamy'),
        pot=env.get('pot_size', 'medium'),
        environment=env.get('environment_type', 'outdoor'),
        location=env.get('location_type', 'ground'),
    )


def _iso(val):
    if not hasattr(val, 'isoformat'):
        return str(val)

    from datetime import timezone as tz, timedelta
    IST = tz(timedelta(hours=5, minutes=30))

    if val.tzinfo is None:
        val = val.replace(tzinfo=tz.utc)

    return val.astimezone(IST).isoformat()


def _serialize(doc, result):
    return {
        'plant_id': doc.get('plant_id', str(doc.get('_id', ''))),
        'plant_name': doc.get('plant_name', ''),
        'plant_type': doc.get('plant_type', ''),
        'owner_name': doc.get('owner_name', 'Gardener'),

        'planting_date': _iso(doc.get('planting_date', '')),
        'created_at': _iso(doc.get('created_at', '')),
        'last_watered': _iso(doc.get('last_watered')) if doc.get('last_watered') else None,

        # 🌱 Growth
        'current_stage': result.stage,
        'stage_label': result.stage_label,
        'growth_percentage': result.growth_percentage,

        # ❤️ Health
        'health_score': result.health_score,
        'health_label': result.health_label,
        'health_color': result.health_color,

        # 📊 Stats
        'real_days': result.real_days,
        'effective_days': result.effective_days,
        'growth_multiplier': result.growth_multiplier,
        'stage_progress': result.stage_progress,
        'days_to_next_stage': result.days_to_next_stage,

        # 🌤 Conditions
        'conditions': {
            'sunlight': {
                'score': result.condition_scores['sunlight'],
                'label': result.condition_labels['sunlight']
            },
            'watering': {
                'score': result.condition_scores['watering'],
                'label': result.condition_labels['watering']
            },
            'soil': {
                'score': result.condition_scores['soil'],
                'label': result.condition_labels['soil']
            },
            'pot': {
                'score': result.condition_scores['pot'],
                'label': result.condition_labels['pot']
            }
        },

        # 💡 Recommendations
        'recommendations': result.recommendations,

        # 🎨 UI styling
        'visual_profile': result.visual_profile,

        # 🌍 Raw env
        'environment': doc.get('environment', {}),
    }


def _get_doc(plant_id):
    col = _col('plant_profiles')
    doc = col.find_one({'plant_id': plant_id})

    if not doc:
        try:
            doc = col.find_one({'_id': ObjectId(plant_id)})
        except:
            pass

    return doc


# ── Plant CRUD ────────────────────────────────────────────────────────────────
class PlantCareLogsView(APIView):
    def get(self, request, plant_id):
        doc = _get_doc(plant_id)

        if not doc:
            return Response({'error': 'Plant not found'}, status=404)

        try:
            logs = list(_col('care_logs').find(
                {'plant_id': doc['plant_id']},
                {'_id': 0}
            ).sort('logged_at', -1))

            # convert datetime → ISO (IST safe)
            for log in logs:
                if 'logged_at' in log:
                    log['logged_at'] = _iso(log['logged_at'])

            return Response({'logs': logs})

        except Exception as e:
            return _mongo_err(e)
        
class PlantListCreateView(APIView):
    parser_classes = [JSONParser]

    # def get(self, request):
    #     try:
    #         col = _col('plant_profiles')

    #         docs = list(col.find().sort('created_at', -1))

    #     except Exception as e:
    #         return _mongo_err(e)

    #     return Response({
    #         'plants': [_serialize(d, _run_simulation(d)) for d in docs],
    #         'count': len(docs)
    #     })
    def get(self, request):
        try:
            col = _col('plant_profiles')
            docs = list(col.find().sort('created_at', -1))

            plants = []

            for d in docs:
                result = _run_simulation(d)

                # ✅ ADD HERE
                _col('growth_logs').insert_one({
                    'plant_id': d['plant_id'],
                    'recorded_at': timezone.now(),
                    'stage': result.stage,
                    'health_score': result.health_score,
                    'effective_days': result.effective_days,
                    'growth_percentage': result.growth_percentage,
                })

                plants.append(_serialize(d, result))

        except Exception as e:
            return _mongo_err(e)

        return Response({
            'plants': plants,
            'count': len(plants)
        })
    def post(self, request):
        ser = PlantCreateSerializer(data=request.data)

        if not ser.is_valid():
            return Response(ser.errors, status=400)

        data = ser.validated_data

        doc = {
            'plant_id': str(uuid.uuid4()),
            'plant_name': data['plant_name'],
            'plant_type': data['plant_type'],
            'owner_name': 'User',
            'planting_date': timezone.now(),
            'created_at': timezone.now(),
            'last_watered': timezone.now(),
            'environment': data['environment'],
        }

        try:
            # ✅ insert plant
            _col('plant_profiles').insert_one(doc)

            # ✅ run simulation
            result = _run_simulation(doc)

            # ✅ save growth log (THIS creates your collection 🔥)
            _col('growth_logs').insert_one({
                'plant_id': doc['plant_id'],
                'recorded_at': timezone.now(),
                'stage': result.stage,
                'health_score': result.health_score,
                'effective_days': result.effective_days,
                'growth_percentage': result.growth_percentage,
            })

        except Exception as e:
            return _mongo_err(e)

        return Response(_serialize(doc, result), status=201)
    # def post(self, request):
    #     ser = PlantCreateSerializer(data=request.data)

    #     if not ser.is_valid():
    #         return Response(ser.errors, status=400)

    #     data = ser.validated_data

    #     doc = {
    #         'plant_id': str(uuid.uuid4()),
    #         'plant_name': data['plant_name'],
    #         'plant_type': data['plant_type'],
    #         'owner_name': 'User',
    #         'planting_date': timezone.now(),
    #         'created_at': timezone.now(),
    #         'last_watered': timezone.now(),
    #         'environment': data['environment'],
    #     }

    #     try:
    #         _col('plant_profiles').insert_one(doc)
    #         def post(self, request):
    # ser = PlantCreateSerializer(data=request.data)

    # if not ser.is_valid():
    #     return Response(ser.errors, status=400)

    # data = ser.validated_data

    # doc = {
    #     'plant_id': str(uuid.uuid4()),
    #     'plant_name': data['plant_name'],
    #     'plant_type': data['plant_type'],
    #     'owner_name': 'User',
    #     'planting_date': timezone.now(),
    #     'created_at': timezone.now(),
    #     'last_watered': timezone.now(),
    #     'environment': data['environment'],
    # }

    # try:
    #     # ✅ insert plant
    #     _col('plant_profiles').insert_one(doc)

    #     # ✅ RUN SIMULATION
    #     result = _run_simulation(doc)

    #     # ✅ ADD THIS BLOCK (VERY IMPORTANT 🔥)
    #     _col('growth_logs').insert_one({
    #         'plant_id': doc['plant_id'],
    #         'recorded_at': timezone.now(),
    #         'stage': result.stage,
    #         'health_score': result.health_score,
    #         'effective_days': result.effective_days,
    #         'growth_percentage': result.growth_percentage,
    #     })

    #     except Exception as e:
    #         return _mongo_err(e)

    #     return Response(_serialize(doc, result), status=201)
        # except Exception as e:
        #     return _mongo_err(e)

        # return Response(_serialize(doc, _run_simulation(doc)), status=201)


class PlantDetailView(APIView):

    def get(self, request, plant_id):
        doc = _get_doc(plant_id)

        if not doc:
            return Response({'error': 'Plant not found'}, status=404)

        return Response(_serialize(doc, _run_simulation(doc)))

    def delete(self, request, plant_id):
        doc = _get_doc(plant_id)

        if not doc:
            return Response({'error': 'Plant not found'}, status=404)

        _col('plant_profiles').delete_one({'plant_id': doc['plant_id']})

        return Response({'message': 'Deleted'}, status=204)


# ── Watering ──────────────────────────────────────────────────────────────────

class PlantWaterView(APIView):

    def post(self, request, plant_id):
        doc = _get_doc(plant_id)

        if not doc:
            return Response({'error': 'Plant not found'}, status=404)

        now = timezone.now()

        # Update plant
        _col('plant_profiles').update_one(
            {'plant_id': doc['plant_id']},
            {'$set': {'last_watered': now}}
        )

        # ✅ ADD THIS (log entry)
        _col('care_logs').insert_one({
            'plant_id': doc['plant_id'],
            'action': 'watered',
            'logged_at': now,
        })

        return Response({'message': 'Watered successfully'})

class PlantFertilizeView(APIView):

    def post(self, request, plant_id):
        doc = _get_doc(plant_id)

        if not doc:
            return Response({'error': 'Plant not found'}, status=404)

        now = timezone.now()

        _col('plant_profiles').update_one(
            {'plant_id': doc['plant_id']},
            {'$set': {'last_fertilized': now}}
        )

        # log
        _col('care_logs').insert_one({
            'plant_id': doc['plant_id'],
            'action': 'fertilized',
            'logged_at': now,
        })

        return Response({'message': 'Fertilized successfully'})
# ── Weather API ───────────────────────────────────────────────────────────────

class WeatherView(APIView):

    def get(self, request):
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')

        if not lat or not lon:
            return Response({'error': 'lat/lon required'}, status=400)

        api_key = os.getenv('OPENWEATHER_API_KEY')

        try:
            r = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}
            )
            data = r.json()

            return Response({
                "temp": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "description": data["weather"][0]["description"]
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)