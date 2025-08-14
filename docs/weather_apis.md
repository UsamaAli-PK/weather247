# Free Weather APIs for Weather247

Based on research, the following free weather APIs are suitable for the Weather247 project:

## 1. OpenWeatherMap

**Website:** [https://openweathermap.org/](https://openweathermap.org/)

**Free Tier Details:**
- **API Calls:** 60 API calls/minute, 1,000,000 calls/month.
- **Data Available:** Current weather data, 3-hour forecast for 5 days, weather maps.
- **API Key:** Required. Obtained upon signing up.

**Suitability for Weather247:**
- **Real-time weather data:** Yes, through Current Weather Data API.
- **Historical weather trends:** Limited in free tier, may require paid plan or alternative for 5-year history.
- **24-hour predictions:** Yes, through 3-hour forecast for 5 days API.
- **Route planning weather:** Can be integrated by querying weather for multiple points along a route.
- **Severe weather alerts:** Available through One Call API 3.0 (check free tier limitations).

**Key Endpoints (Free Tier):**
- **Current weather data:** `api.openweathermap.org/data/2.5/weather?q={city name}&appid={API key}`
- **5-day / 3-hour forecast:** `api.openweathermap.org/data/2.5/forecast?q={city name}&appid={API key}`

## 2. Open-Meteo.com

**Website:** [https://open-meteo.com/](https://open-meteo.com/)

**Free Tier Details:**
- **API Calls:** Free access for non-commercial use, no API key required.
- **Data Available:** Hourly and daily weather forecasts, historical weather data, weather models.
- **API Key:** Not required.

**Suitability for Weather247:**
- **Real-time weather data:** Yes, through current weather and forecast endpoints.
- **Historical weather trends:** Yes, offers historical weather data.
- **24-hour predictions:** Yes, through hourly forecasts.
- **Route planning weather:** Can be integrated by querying weather for multiple points along a route.
- **Severe weather alerts:** Not explicitly mentioned, may need to be derived or supplemented.

**Key Endpoints:**
- **Forecast:** `api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,relative_humidity_2m,apparent_temperature`
- **Historical:** `archive-api.open-meteo.com/v1/archive?latitude={latitude}&longitude={longitude}&start_date={start_date}&end_date={end_date}&daily=temperature_2m_max,temperature_2m_min`

## 3. Weatherstack

**Website:** [https://weatherstack.com/](https://weatherstack.com/)

**Free Tier Details:**
- **API Calls:** 250 requests/month.
- **Data Available:** Real-time weather data, historical data, weather forecasts.
- **API Key:** Required.

**Suitability for Weather247:**
- **Real-time weather data:** Yes.
- **Historical weather trends:** Yes.
- **24-hour predictions:** Yes.
- **Route planning weather:** Possible, but limited by API call volume.
- **Severe weather alerts:** Not explicitly mentioned.

**Considerations:**
- The free tier is very limited (250 requests/month), which might not be sufficient for a fully functional application with multiple users and features like historical data and route planning. It might be suitable for initial development and testing.

**Recommendation:**
OpenWeatherMap and Open-Meteo.com appear to be the most robust free options for this project due to their higher API call limits and comprehensive data offerings. Open-Meteo.com's lack of an API key requirement is also a plus for rapid prototyping. We will primarily use OpenWeatherMap for real-time and forecast data, and Open-Meteo.com for historical data if OpenWeatherMap's free tier proves insufficient for historical trends. Weatherstack can be a backup for specific needs if its limitations are acceptable. We will need to manage API calls efficiently to stay within the free tier limits.

