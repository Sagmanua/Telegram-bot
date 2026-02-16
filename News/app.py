import requests

def get_news():
    api_key = '' # Make sure this is active
    # This looks for "Valencia" AND "Spain" to filter out tech/random noise
    url = f'https://newsapi.org/v2/everything?q=Україна&sortBy=publishedAt&apiKey={api_key}'

    
    try:
        response = requests.get(url)
        data = response.json()
        
        # Check if the API returned an error (like 401 Unauthorized or 429 Too Many Requests)
        if data.get('status') == 'error':
            return f"❌ API Error: {data.get('message')}"
            
        articles = data.get('articles', [])
        
        if articles:
            report = "🗞 Последние новости:\n\n"
            for art in articles[:3]:
                report += f"🔹 {art['title']}\n{art['url']}\n\n"
            return report
        else:
            return "Новостей по запросу 'Valencia' на русском языке не найдено."
            
    except Exception as e:
        return f"⚠️ Произошла ошибка: {e}"

print(get_news())