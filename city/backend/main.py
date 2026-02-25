from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import httpx, os, asyncio

from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent / ".env")
#load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4321"],  # add deployed frontend URL later
    allow_methods=["*"],
    allow_headers=["*"],
)

WEATHER_KEY  = os.getenv("OPENWEATHER_KEY")
UNSPLASH_KEY = os.getenv("UNSPLASH_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")  # used for both GeoDB and Deezer


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
        # All 5 API calls fire at the same time
        results = await asyncio.gather(
            fetch_weather(client, name, countryCode),
            fetch_photos(client, name),
            fetch_music(client, country or name),
            fetch_dress(client, country or name),
            return_exceptions=True  # if one fails, others still return
        )

    weather, photos, music, dress = results

    return {
        "place":   name,
        "country": country,
        "weather": weather if not isinstance(weather, Exception) else None,
        "photos":  photos  if not isinstance(photos,  Exception) else [],
        #"food":    food    if not isinstance(food,    Exception) else [],
        "music":   music   if not isinstance(music,   Exception) else [],
        "dress":   dress   if not isinstance(dress,   Exception) else [],
    }


# ── Fetchers ──────────────────────────────────────────────────────────────────

async def fetch_weather(client: httpx.AsyncClient, city: str, country_code: str):
    q = f"{city},{country_code}" if country_code else city
    res = await client.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={
            "q":     q,
            "appid": WEATHER_KEY,
            "units": "metric"
        }
    )
    d = res.json()
    return {
        "temp":        round(d["main"]["temp"]),
        "feels_like":  round(d["main"]["feels_like"]),
        "humidity":    d["main"]["humidity"],
        "description": d["weather"][0]["description"].title(),
        "icon":        d["weather"][0]["icon"],   # used in <img src="openweathermap.org/img/wn/{icon}@2x.png">
        "wind_speed":  d["wind"]["speed"],
    }


async def fetch_photos(client: httpx.AsyncClient, place: str):
    res = await client.get(
        "https://api.unsplash.com/search/photos",
        params={
            "query":       f"{place} scenic landscape",
            "per_page":    6,
            "orientation": "landscape",
        },
        headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"}
    )
    return [
        {
            "url":   p["urls"]["regular"],
            "thumb": p["urls"]["thumb"],
            "color": p["color"],          # dominant hex color — used for ambient lighting in JS
            "alt":   p["alt_description"] or place,
        }
        for p in res.json().get("results", [])
    ]



async def fetch_music(client: httpx.AsyncClient, country: str):
    # Deezer via RapidAPI — same RAPIDAPI_KEY as GeoDB
    res = await client.get(
        "https://deezerdevs-deezer.p.rapidapi.com/search",
        params={"q": f"traditional folk {country}"},
        headers={
            "X-RapidAPI-Key":  RAPIDAPI_KEY,
            "X-RapidAPI-Host": "deezerdevs-deezer.p.rapidapi.com"
        }
    )
    return [
        {
            "title":   t["title"],
            "artist":  t["artist"]["name"],
            "preview": t["preview"],       # 30s MP3 URL — used directly in <audio src="">
            "cover":   t["album"]["cover_medium"],
        }
        for t in res.json().get("data", [])[:5]
        if t.get("preview")
    ]


async def fetch_dress(client: httpx.AsyncClient, country: str):
    res = await client.get(
        "https://api.unsplash.com/search/photos",
        params={
            "query":    f"{country} traditional dress",
            "per_page": 4,
        },
        headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"}
    )
    return [
        {
            "url":   p["urls"]["regular"],
            "thumb": p["urls"]["small"],
            "alt":   p["alt_description"] or country,
        }
        for p in res.json().get("results", [])
    ]
