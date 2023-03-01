from geopandas.tools import geocode
city="Moscow"
location = geocode(city, provider="nominatim", user_agent='my_request')
point = location.geometry.iloc[0]
longitude = point.x
latitude = point.y
print(latitude)
print(longitude)