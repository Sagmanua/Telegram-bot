import feedparser

def get_world_news():
    # Topic URL for WORLD news in English
    url = "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-US&gl=US&ceid=US:en"
    
    try:
        feed = feedparser.parse(url)
        
        if not feed.entries:
            return "No world news found at the moment."
            
        report = "🌍 Top World News Headlines:\n\n"
        
        # Taking top 5 for a better overview
        for entry in feed.entries[:5]:
            # entry.published contains the timestamp
            report += f"🔹 {entry.title}\n📅 {entry.published}\n🔗 {entry.link}\n\n"
            
        return report
            
    except Exception as e:
        return f"⚠️ Error: {e}"

print(get_world_news())