from fastapi import FastAPI
from dotenv import load_dotenv
import httpx, os

load_dotenv()
app = FastAPI()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
WEATHER_KEY = os.getenv("OPENWEATHER_KEY")
PLACES_KEY  = os.getenv("GOOGLE_PLACES_KEY")

@app.get("/search")
async def get_place_info(place: str):
    async with httpx.AsyncClient() as client:

        # Fetch weather
        weather_res = await client.get(
            f"https://api.openweathermap.org/data/2.5/weather",
            params={"q": place, "appid": WEATHER_KEY, "units": "metric"}
        )

        # Fetch top destinations via SerpAPI
        serp_res = await client.get(
            "https://serpapi.com/search",
            params={"q": f"top places to visit in {place}", "api_key": SERPAPI_KEY}
        )

        # Fetch famous food via SerpAPI
        food_res = await client.get(
            "https://serpapi.com/search",
            params={"q": f"famous food in {place}", "api_key": SERPAPI_KEY}
        )

    # Combine and return everything
    return {
        "place": place,
        "weather": weather_res.json(),
        "top_destinations": serp_res.json().get("organic_results", [])[:5],
        "famous_food": food_res.json().get("organic_results", [])[:5],
    }from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import httpx, os, asyncio

load_dotenv()
app = FastAPI()

# CORS lets your Astro frontend talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4321"],  # add your deployed frontend URL here later
    allow_methods=["*"],
    allow_headers=["*"],
)

SERPAPI_KEY  = os.getenv("SERPAPI_KEY")
WEATHER_KEY  = os.getenv("OPENWEATHER_KEY")
UNSPLASH_KEY = os.getenv("UNSPLASH_KEY")
GEODB_KEY    = os.getenv("GEODB_KEY")


# ── Autocomplete ──────────────────────────────────────────────────────────────

@app.get("/autocomplete")
async def autocomplete(q: str):
    async with httpx.AsyncClient() as client:
        res = await client.get(
            "https://wft-geo-db.p.rapidapi.com/v1/geo/cities",
            params={"namePrefix": q, "limit": 8, "sort": "-population", "types": "CITY"},
            headers={
                "X-RapidAPI-Key": GEODB_KEY,
                "X-RapidAPI-Host": "wft-geo-db.p.rapidapi.com"
            }
        )
        cities = [
            {
                "name": c["name"],
                "country": c["country"],
                "countryCode": c["countryCode"],
            }
            for c in res.json().get("data", [])
        ]
        return {"suggestions": cities}


# ── Main place endpoint ───────────────────────────────────────────────────────

@app.get("/place")
async def get_place(name: str, country: str = "", countryCode: str = ""):
    async with httpx.AsyncClient(timeout=15) as client:
        # All API calls run at the same time
        results = await asyncio.gather(
            fetch_weather(client, name, countryCode),
            fetch_photos(client, name),
            fetch_food(client, name),
            fetch_music(client, country or name),
            fetch_dress(client, country or name),
            return_exceptions=True
        )

    weather, photos, food, music, dress = results

    return {
        "place":   name,
        "country": country,
        "weather": weather if not isinstance(weather, Exception) else None,
        "photos":  photos  if not isinstance(photos,  Exception) else [],
        "food":    food    if not isinstance(food,    Exception) else [],
        "music":   music   if not isinstance(music,   Exception) else [],
        "dress":   dress   if not isinstance(dress,   Exception) else [],
    }


# ── Individual fetchers ───────────────────────────────────────────────────────

async def fetch_weather(client, city, country_code):
    q = f"{city},{country_code}" if country_code else city
    res = await client.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"q": q, "appid": WEATHER_KEY, "units": "metric"}
    )
    d = res.json()
    return {
        "temp":        round(d["main"]["temp"]),
        "feels_like":  round(d["main"]["feels_like"]),
        "humidity":    d["main"]["humidity"],
        "description": d["weather"][0]["description"].title(),
        "icon":        d["weather"][0]["icon"],
        "wind_speed":  d["wind"]["speed"],
    }


async def fetch_photos(client, place):
    res = await client.get(
        "https://api.unsplash.com/search/photos",
        params={"query": f"{place} scenic", "per_page": 6, "orientation": "landscape"},
        headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"}
    )
    return [
        {
            "url":   p["urls"]["regular"],
            "thumb": p["urls"]["thumb"],
            "color": p["color"],        # dominant hex — used for ambient lighting
            "alt":   p["alt_description"] or place,
        }
        for p in res.json().get("results", [])
    ]


async def fetch_food(client, place):
    res = await client.get(
        "https://serpapi.com/search",
        params={"q": f"famous traditional food of {place}", "api_key": SERPAPI_KEY, "num": 5}
    )
    return [
        {"title": r["title"], "snippet": r.get("snippet", "")}
        for r in res.json().get("organic_results", [])[:5]
    ]


async def fetch_music(client, country):
    res = await client.get(
        "https://api.deezer.com/search",
        params={"q": f"traditional folk {country}", "limit": 5}
    )
    return [
        {
            "title":   t["title"],
            "artist":  t["artist"]["name"],
            "preview": t["preview"],        # 30s MP3 — play directly in <audio>
            "cover":   t["album"]["cover_medium"],
        }
        for t in res.json().get("data", []) if t.get("preview")
    ]


async def fetch_dress(client, country):
    res = await client.get(
        "https://api.unsplash.com/search/photos",
        params={"query": f"{country} traditional dress costume", "per_page": 4},
        headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"}
    )
    return [
        {"url": p["urls"]["regular"], "thumb": p["urls"]["small"], "alt": p["alt_description"] or country}
        for p in res.json().get("results", [])
    ]
