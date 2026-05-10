from __future__ import annotations

from app.models.city import City
from app.models.user import User
from app.repositories.city_repo import CityRepository
from app.services.weather_service import (
    GeoCity,
    WeatherReport,
    WeatherService,
)


class WeatherViewModel:
    """ViewModel pro hlavní obrazovku.

    Spravuje seznam měst přihlášeného uživatele, volá API pro
    geokódování a pro načtení počasí.
    """

    def __init__(
        self,
        user: User,
        cities: CityRepository | None = None,
        weather: WeatherService | None = None,
    ) -> None:
        if user.id is None:
            raise ValueError("WeatherViewModel vyžaduje uloženého uživatele s id.")
        self._user = user
        self._cities = cities or CityRepository()
        self._weather = weather or WeatherService()

    @property
    def user(self) -> User:
        return self._user

    def list_cities(self) -> list[City]:
        return self._cities.list_for_user(self._user.id)  # type: ignore[arg-type]

    def search_city(self, query: str) -> list[GeoCity]:
        return self._weather.search_city(query)

    def add_city(self, geo: GeoCity) -> City:
        if self._cities.exists_for_user(self._user.id, geo.latitude, geo.longitude):  # type: ignore[arg-type]
            raise ValueError("Toto město už máš přidané.")
        city = City(
            user_id=self._user.id,  # type: ignore[arg-type]
            name=geo.name,
            country=geo.country,
            latitude=geo.latitude,
            longitude=geo.longitude,
        )
        return self._cities.save(city)

    def remove_city(self, city: City) -> None:
        if city.id is None:
            return
        self._cities.delete(city.id)

    def fetch_weather(self, city: City) -> WeatherReport:
        return self._weather.fetch_weather(city.latitude, city.longitude)
