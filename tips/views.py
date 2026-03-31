from rest_framework.decorators import api_view
from rest_framework.response import Response
from .mongo import get_random_tip
from .serializers import TipSerializer

@api_view(['GET'])
def random_tip(request):
    tip_data = get_random_tip()
    if not tip_data:
        return Response({"error": "No tips found"})
    return Response(tip_data)