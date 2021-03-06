import config
import requests
import json
import pyttsx3
import speech_recognition as sr
import re
import threading
import time

API_KEY = "tuhWsqTLrfzy"
PROJECT_TOKEN = "tnaGN6R9uz-5"
RUN_TOKEN = "tQqju6HHJHAY"


class Data:
    def __init__(self, api_key, project_token):
        self.api_key = api_key
        self.project_token = project_token
        self.params = {
            "api_key": self.api_key
        }  # Set up Authentication
        self.data = self.get_data()  # Most recent run

    # noinspection PyTypeChecker
    def get_data(self):
        response = requests.get(f'https://www.parsehub.com/api/v2/projects/{PROJECT_TOKEN}/last_ready_run/data', params=dict(
            api_key=API_KEY))  # Authentication for the get request
        data = json.loads(response.text)
        return data

    def get_total_cases(self):  # Get the total coronavirus cases
        data = self.data['total']
        for val in data:
            if val['name'] == "Coronavirus Cases:":
                return val['value']

    def get_total_deaths(self):  # Get the total coronavirus deaths
        data = self.data['total']
        for val in data:
            if val['name'] == "Deaths:":
                return val['value']
        return "0"

    # Get the details of cases and deaths in a country
    def get_country_data(self, country):
        data = self.data["country"]
        for val in data:
            if val['name'].lower() == country.lower():
                return val
        return "0"

    def get_list_of_countries(self):
        countries = []
        for country in self.data['country']:
            countries.append(country['name'].lower())
        return countries

    def update(self):  # Update the information
        response = requests.post(
            f'https://www.parsehub.com/api/v2/projects/{PROJECT_TOKEN}/run', params={"api_key": API_KEY})

        def poll():
            time.sleep(0.1)
            old_data = self.data
            while True:
                new_data = self.get_data()
                if new_data != old_data:  # Check if old data equals new data every 5 seconds
                    self.data = new_data  # Update
                    print("Data Updated!")
                    break
                time.sleep(5)

        # Run the voice assistant on one thread and update the information on another
        t = threading.Thread(target=poll)
        t.start()

# Voice Recognition


def speak(text):  # Speak
    engine = pyttsx3.init()  # Initialise the python text to speech engine
    engine.say(text)
    engine.runAndWait()


def get_audio():  # Listen
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        said = ""

        try:
            # Google to recognize the speech input
            said = r.recognize_google(audio)
        except Exception as e:
            print("Exception: ", str(e))
    return said.lower()


# noinspection PyTypeChecker
def main():
    print("Started Program!")
    data = Data(API_KEY, PROJECT_TOKEN)
    country_list = list(data.get_list_of_countries())

    # Look for REGEX patterns in the voice
    TOTAL_PATTERNS = {
        re.compile("[\w\s]+ total [\w\s]+ cases"): data.get_total_cases,
        re.compile("[\w\s]+ total cases"): data.get_total_cases,
        re.compile("[\w\s]+ total [\w\s]+ deaths"): data.get_total_deaths,
        re.compile("[\w\s]+ total deaths"): data.get_total_deaths
    }

    COUNTRY_PATTERNS = {
        re.compile("[\w\s]+ cases [\w\s]+"): lambda country: data.get_country_data(country)['total_cases'],
        re.compile("[\w\s]+ deaths [\w\s]+"): lambda country: data.get_country_data(country)['total_deaths'],
        re.compile("[\w\s]+ deaths [\w\s]+"): lambda country: data.get_country_data(country)['total_deaths']
    }

    UPDATE = "update"

    END_PHRASE = "stop"

    while True:
        print("Listening...")
        text = get_audio()
        print(text)
        result = None

        for pattern, func in COUNTRY_PATTERNS.items():
            if pattern.match(text):
                words = set(text.split(" "))
                for country in country_list:
                    if country in words:
                        result = func(country)
                        break

        for pattern, func in TOTAL_PATTERNS.items():
            if pattern.match(text):
                result = func()
                break

        if text == UPDATE:
            result = "Data is being updated. This may take a while."
            data.update()

        if result:
            speak(result)

        if text.find(END_PHRASE) != -1:  # Stop
            print("Exit")
            break


main()
