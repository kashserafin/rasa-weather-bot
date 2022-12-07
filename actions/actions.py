# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, EventType

import requests
import creds

# overwrite to send welcome message proactively
class ActionSessionStart(Action):
    def name(self) -> Text:
        return "action_session_start"

    @staticmethod
    def fetch_slots(tracker: Tracker) -> List[EventType]:

        slots = []
        value = tracker.get_slot("city")
        if value is not None:
            slots.append(SlotSet(key="city", value=value))
        return slots

    async def run(
      self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        events = [SessionStarted()]
        
        events.extend(self.fetch_slots(tracker))

        msg = """Hi, I am WeatherBot, I provide weather forecast for the city of your choice. Try something like "weather forecast for Berlin" """
        dispatcher.utter_message(text=msg)

        events.append(ActionExecuted("action_listen"))

        return events

class ActionGetCityCoordinates(Action):
    def name(self) -> Text:
        return "action_get_city_coordinates"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        city = tracker.get_slot("city")

        url = "http://api.openweathermap.org/geo/1.0/direct"
        params = {'q':city,
                  'limit':1,
                  'appid':creds.api_key}
        response = requests.get(url, params=params).json()

        if not response:
            msg = f"Sorry, I couldn't find the coordinates of {city}. Please try again."
            dispatcher.utter_message(text=msg)
            return []

        return [SlotSet('city_lat', response[0]['lat']), 
                SlotSet('city_lon', response[0]['lon'])]

class ActionProvideWeatherForecast(Action):

    def name(self) -> Text:
        return "action_provide_weather_forecast"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        city = tracker.get_slot("city")
        city_lat = tracker.get_slot("city_lat")
        city_lon = tracker.get_slot("city_lon")

        url = "https://api.openweathermap.org/data/2.5/onecall"
        params = {'lat':city_lat, 
                  'lon':city_lon,
                  'units':'metric',
                  'appid':creds.api_key}
        response = requests.get(url, params=params).json()

        if not response:
            msg = "Sorry, something went wrong. Please try again later."
            dispatcher.utter_message(text=msg)
            return []

        temp = response['current']['temp']
        weather_desc = response['current']['weather'][0]['description']

        msg = f"The temperature in {city.capitalize()} is {temp}°C. It's {weather_desc} today."
        dispatcher.utter_message(text=msg)

        return []