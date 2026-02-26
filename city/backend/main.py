from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import httpx, os, asyncio
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent / ".env")
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4321"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WEATHER_KEY  = os.getenv("OPENWEATHER_KEY")
UNSPLASH_KEY = os.getenv("UNSPLASH_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")


# ── Autocomplete ──────────────────────────────────────────────────────────────

@app.get("/autocomplete")
async def autocomplete(q: str):
    async with httpx.AsyncClient() as client:
        res = await client.get(
            "https://wft-geo-db.p.rapidapi.com/v1/geo/cities",
            params={
                "namePrefix": q,
                "limit": 8,
                "sort": "-population",
                "types": "CITY"
            },
            headers={
                "X-RapidAPI-Key":  RAPIDAPI_KEY,
                "X-RapidAPI-Host": "wft-geo-db.p.rapidapi.com"
            }
        )
        cities = [
            {
                "name":        c["name"],
                "state":       c.get("state", ""),
                "country":     c["country"],
                "countryCode": c["countryCode"],
            }
            for c in res.json().get("data", [])
        ]
        return {"suggestions": cities}


# ── Main place endpoint ───────────────────────────────────────────────────────

@app.get("/place")
async def get_place(name: str, country: str = "", countryCode: str = ""):
    async with httpx.AsyncClient(timeout=15) as client:
        # All calls fire at the same time — city name used for everything
        results = await asyncio.gather(
            fetch_weather(client, name, countryCode),
            fetch_scenery(client, name),        # scenic landscape photos
            fetch_architecture(client, name),   # buildings, monuments
            fetch_food_photos(client, name),    # food photos
            fetch_dress_photos(client, name),   # traditional dress
            fetch_music(client, name),          # music searched by city now
            return_exceptions=True
        )

    weather, scenery, architecture, food_photos, dress, music = results

    return {
        "place":        name,
        "country":      country,
        "weather":      weather       if not isinstance(weather,       Exception) else None,
        "scenery":      scenery       if not isinstance(scenery,       Exception) else [],
        "architecture": architecture  if not isinstance(architecture,  Exception) else [],
        "food_photos":  food_photos   if not isinstance(food_photos,   Exception) else [],
        "dress":        dress         if not isinstance(dress,         Exception) else [],
        "music":        music         if not isinstance(music,         Exception) else [],
    }


# ── Fetchers ──────────────────────────────────────────────────────────────────

async def fetch_weather(client: httpx.AsyncClient, city: str, country_code: str):
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


async def fetch_unsplash(client: httpx.AsyncClient, query: str, count: int = 4):
    """Reusable Unsplash helper — avoids repeating the same code 4 times."""
    res = await client.get(
        "https://api.unsplash.com/search/photos",
        params={"query": query, "per_page": count, "orientation": "landscape"},
        headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"}
    )
    return [
        {
            "url":   p["urls"]["regular"],
            "thumb": p["urls"]["small"],
            "color": p["color"],
            "alt":   p["alt_description"] or query,
        }
        for p in res.json().get("results", [])
    ]


async def fetch_scenery(client: httpx.AsyncClient, city: str):
    return await fetch_unsplash(client, f"{city} images", count=6)


async def fetch_architecture(client: httpx.AsyncClient, city: str):
    return await fetch_unsplash(client, f"{city} architecture monuments buildings", count=4)


async def fetch_food_photos(client: httpx.AsyncClient, city: str):
    return await fetch_unsplash(client, f"{city} food", count=4)


async def fetch_dress_photos(client: httpx.AsyncClient, city: str):
    return await fetch_unsplash(client, f"{city} traditional dress costume", count=4)


async def fetch_music(client: httpx.AsyncClient, city: str):
    res = await client.get(
        "https://deezerdevs-deezer.p.rapidapi.com/search",
        params={"q": f"songs from {city}"},
        headers={
            "X-RapidAPI-Key":  RAPIDAPI_KEY,
            "X-RapidAPI-Host": "deezerdevs-deezer.p.rapidapi.com"
        }
    )
    return [
        {
            "title":   t["title"],
            "artist":  t["artist"]["name"],
            "preview": t["preview"],
            "cover":   t["album"]["cover_medium"],
        }
        for t in res.json().get("data", [])[:3]
        if t.get("preview")
    ]