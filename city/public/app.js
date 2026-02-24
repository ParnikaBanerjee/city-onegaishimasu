//city autofill
const mapboxToken="YOUR_TOKEN"
const input=document.getElementById("cityInput")
input.addEventListener("input", async()=>{
let query=input.value
let res=await fetch(
`https://api.mapbox.com/geocoding/v5/mapbox.places/${query}.json?access_token=${mapboxToken}`
)
let data=await res.json()
let suggestions=data.features.slice(0,5)
let box=document.getElementById("suggestions")
box.innerHTML=""
suggestions.forEach(city=>{
let div=document.createElement("div")
div.innerText=city.place_name
div.onclick=()=>loadCity(city)
box.appendChild(div)
})
})

//weather
async function getWeather(city){
let key="OPENWEATHER_KEY"
let res=await fetch(
`https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${key}&units=metric`
)
let data=await res.json()
document.getElementById("weather").innerHTML=
`
<h3>${data.name}</h3>
<p>${data.main.temp}°C</p>
<p>${data.weather[0].description}</p>
`
}

//scenetic image from unplash(50req/hr)
async function getWeather(city){

let key="OPENWEATHER_KEY"

let res=await fetch(
`https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${key}&units=metric`
)

let data=await res.json()

document.getElementById("weather").innerHTML=
`
<h3>${data.name}</h3>
<p>${data.main.temp}°C</p>
<p>${data.weather[0].description}</p>
`
}

//ambient colours
function changeAmbient(imgUrl){

let img=new Image()
img.crossOrigin="Anonymous"
img.src=imgUrl

img.onload=function(){

let canvas=document.createElement("canvas")
let ctx=canvas.getContext("2d")

canvas.width=img.width
canvas.height=img.height

ctx.drawImage(img,0,0)

let data=ctx.getImageData(0,0,1,1).data

document.body.style.background=
`rgba(${data[0]},${data[1]},${data[2]},0.3)`
}
}

//mealDB for food
async function getFood(country){

let res=await fetch(
`https://www.themealdb.com/api/json/v1/1/filter.php?a=${country}`
)

let data=await res.json()

let meal=data.meals[0]

document.getElementById("food").innerHTML=
`
<h3>Famous Dish</h3>
<p>${meal.strMeal}</p>
<img src="${meal.strMealThumb}" width="100%">
`
}


//deezer api with spotify oauth for music(1000req/hr)
async function getMusic(country){

let query = country + " traditional"

let res = await fetch(
`https://deezerdevs-deezer.p.rapidapi.com/search?q=${query}`,
{
headers:{
"X-RapidAPI-Key":"YOUR_RAPIDAPI_KEY",
"X-RapidAPI-Host":"deezerdevs-deezer.p.rapidapi.com"
}
}
)

let data = await res.json()

let track = data.data[0]

document.getElementById("music").innerHTML =
`
<h3>${track.title}</h3>
<p>${track.artist.name}</p>
<button onclick="play('${track.preview}')">Play</button>
`
}

function play(url){
let audio = new Audio(url)
audio.play()
}

//dresses and country's traditional info
async function getCountry(country){

let res=await fetch(
`https://restcountries.com/v3.1/name/${country}`
)

let data=await res.json()

document.getElementById("country").innerHTML=
`
<h3>${data[0].name.common}</h3>
<p>Capital: ${data[0].capital}</p>
<p>Population: ${data[0].population}</p>
`
}

//master function
function loadCity(city){

let name=city.text

getWeather(name)
getImage(name)
getMusic(name)
getCountry(city.context[0].text)
getFood(city.context[0].text)

}