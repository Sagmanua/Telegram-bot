import requests

def get_weather(city):
    # This uses a free service called wttr.in which requires no API key
    url = f"https://wttr.in/{city}?format=j1"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        temp = data['current_condition'][0]['temp_C']
        desc = data['current_condition'][0]['weatherDesc'][0]['value']
        return f"It is currently {temp}°C in {city} with {desc}."
    else:
        return "City not found!"

print(get_weather("London"))