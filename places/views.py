# Tested using CURL
# Business Search must be done with POST and needs 'location' and 'business-type' parameters
# Example: curl -X POST http://localhost:8000/api/search/ -H "Content-Type: application/json" -d '{"location":"Kennebunkport, ME", "business-type":"restaurant"}'
# Returns JSON with business name, address, rating, phone number, opening hours, and a photo url that can be displayed on front end

import requests
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
import math # Imported math for haversine formula to calculate distance from origin to each place

# Retrieve the lat and longitude from a location
# Needed to retrieve from the user's original search location
def get_geocode(location):
    geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
    geocode_params = {
        'address': location,
        'key': settings.GOOGLE_PLACES_API_KEY,
    }

    geocode_response = requests.get(geocode_url, params=geocode_params)
    geocode_data = geocode_response.json()

    if geocode_data['status'] == 'OK':
        geometry = geocode_data['results'][0]['geometry']['location']
        return geometry['lat'], geometry['lng']
    else:
        return None, None

# Haversine formula - used to calculate distance from origin to each place
def haversine(lat1, lon1, lat2, lon2):
    # Radius of the Earth in km
    R = 6371.0
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Differences in coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # Distance in km
    distance_km = R * c

    # Distance in mi
    distance_miles = distance_km * 0.621371

    return distance_miles

@api_view(['POST'])
def search_businesses(request):
    location = request.data.get('location')
    business_type = request.data.get('business_type')

    # Get the coordinates of the original search location
    origin_lat, origin_lng = get_geocode(location)
    if origin_lat is None or origin_lng is None:
        return Response({'error': 'Invalid location'}, status=400)

    # Google Places API endpoint for text search
    google_places_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    # Parameters for the text search request
    params = {
        'query': f"{business_type} in {location}",
        'key': settings.GOOGLE_PLACES_API_KEY,
    }

    response = requests.get(google_places_url, params=params)
    data = response.json()

    # Extract top 10 results
    top_results = data.get('results', [])[:10]

    results = []
    for result in top_results:
        place_id = result.get('place_id')
        # get each place's location coordinates
        place_location = result.get('geometry', {}).get('location', {})
        place_lat = place_location.get('lat')
        place_lng = place_location.get('lng')

        # Calculate distance from the original search location
        distance = haversine(origin_lat, origin_lng, place_lat, place_lng)

        # Perform a Place Details search for each place
        if place_id:
            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
            details_params = {
                'place_id': place_id,
                'fields': 'name,formatted_address,rating,formatted_phone_number,opening_hours,photos,price_level',
                'key': settings.GOOGLE_PLACES_API_KEY,
            }
            details_response = requests.get(details_url, params=details_params)
            details_data = details_response.json().get('result', {})

            # Get the photo_reference from the photos array
            photo_reference = None
            if 'photos' in details_data and len(details_data['photos']) > 0:
                photo_reference = details_data['photos'][0].get('photo_reference')

            # If a photo_reference is found, get the photo URL
            photo_url = None
            if photo_reference:
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={settings.GOOGLE_PLACES_API_KEY}"

            result_data = {
                'name': details_data.get('name'),
                'address': details_data.get('formatted_address'),
                'rating': details_data.get('rating'),
                'phone_number': details_data.get('formatted_phone_number'),
                'opening_hours': details_data.get('opening_hours', {}).get('weekday_text'),
                'photo_url': photo_url,  # Include the photo URL
                'price_level': details_data.get('price_level'), # Price level goes from 0 to 4, 0 being free and 4 being most expensive
                'distance': distance, # Distance in miles
            }
            results.append(result_data)

    return Response(results)
