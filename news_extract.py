import openai
from dotenv import find_dotenv, load_dotenv
import time
import logging
import os
from datetime import datetime
import requests as r
import json

#load_dotenv()

news_api_key = os.environ.get("NEWS_API_KEY")

print(news_api_key)

#client = openai.OpenAI()
model = "gpt-4o-mini-2024-07-18"


def get_news(topic):
    url = {
        f"https://newsapi.org/v2/everything?q={topic}&apiKey={news_api_key}&pageSize=5" 
    }
    
    try:
        response = r.get(url)
        if response.status_code == 200:

            # json dumps: Serialize obj to a JSON formatted str.
            # new is the payload with all the news
            news = json.dumps(response.json(), indent=4)

            # needs to be converted into a python dictionary to access
            news_json = json.loads(news)

            data = news_json


            
            # access all the fields and extract the information that we want

            status = data["status"]
            total_results = data["totalResults"]
            articles = data["articles"]

            # empty array init
            final_news = []

            # looping through objects in a series is much easier in python

            for article in articles:

                # a lot of these params are defined through the JSON request on the NEWSAPI site, however, the format is like any type of hash or set calling we would see in c++
                # source name is defined as the second parameter in the source paramenters, JSON format defines this as 
#                       "source": {
#                          "id": null,
#                          "name": "Yahoo Entertainment"
#                       },
#                       "author": "Will Shanklin",
#                       "title": "Belkin’s new accessory is a magnetic power bank and camera grip rolled into one",
#                       "description": "Belkin has a new phone accessory at CES 2025 that somehow brings something fresh to the crowded field of magnetic charging accessories (in other words, MagSafe and non-Apple-certified alternatives). The company’s Stage PowerGrip is a wireless power bank, came…",
#                       "url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_1c076267-246c-470d-a753-97acfbfafc65",
#                       "urlToImage": null,
#                       "publishedAt": "2025-01-05T17:00:57Z",
#                       "content": "If you click 'Accept all', we and our partners, including 238 who are part of the IAB Transparency &amp; Consent Framework, will also store and/or access information on a device (in other words, use … [+678 chars]"

#               },

                source_name = article["source"]["name"]
                author = article["author"]
                title = article["title"]
                description = article["description"]
                url = article["url"]
                content = article["content"]
                


                title_description = f"""
                    Title: {title},
                    Author: {author},
                    Source: {source_name}, 
                    Description: {description},
                    URL: {url}
                """

                final_news.append(title_description)

            return final_news


            print(status)


    except r.exceptions.RequestException as e:
        print("An Error occurred during API request", e)




def main():

    news = get_news("bitcoin")
    print(news)


if __name__ == "__main__":
    main()
