import openai
from dotenv import find_dotenv, load_dotenv
import time
import logging
import os
from datetime import datetime
import requests as r
import json

load_dotenv()


# using environment variables like below is a second layer of encryption, instead of hardcoding API key into code
# set up env variable in cmd line with 
# export NEWS_API_KEY="your_actual_api_key"

news_api_key = os.environ.get("NEWS_API_KEY")


if (news_api_key != None):
    print("API endpoint reached\n")


client = openai.OpenAI()
model = "gpt-4o-mini-2024-07-18"

# helpful OS cmd's (not related to project)

# os.getcwd() "current working directory"

# os.listdir(".")

# os.mkdir("new_directory")







def get_news(topic):
    url = f"https://newsapi.org/v2/everything?q={topic}&apiKey={news_api_key}&pageSize=5" 
    
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
    print(news[0])

class AssistantManager:
    thread_id = None
    assistant_id = None


    # initialized constructor
    def __init__(self, model: str = model) -> None:

        # client is a global var
        self.client = client
        self.model = model
        self.assistant = None,
        self.thread = None,
        self.run = None,

        # summary of the news of the topic we paste in
        self.summary = None

        if AssistantManager.assistant_id:
            self.assistant = self.client.beta.assistants.retrieve(assistant_id=AssistantManager.assistant_id)

        if AssistantManager.thread_id:
            self.thread_id = self.client.beta.threads.retrieve(AssistantManager.thread_id)

    def create_assistant(self, name, instructions, tools):
        if not self.assistant:
            assistant_obj = self.client.beta.assistants.create(
                name=name, 
                instructions=instructions,
                tools=tools,
                model=self.model
            )
            

            AssistantManager.assistant_id = assistant_obj.id
            self.assistant = assistant_obj
            print(f"AssisID:::: {self.assistant.id}")



    # if thread doesn't already exist, create AssistentManager with thread object from OpenAI func call
    def create_thread(self):
            
        if not self.thread:

            thread_obj = self.client.beta.threads.create()
            AssistantManager.thread_id = thread_obj
            self.thread = thread_obj
            print(f"ThreadID:::: {self.thread.id}")


    # if there already exists a thread, create a message to run on it
    def add_message_to_thread(self, role, content):
        if self.thread:
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role=role,
                content=content
            )

    # if there is a running thread and assistant has been initialized, run the thread
    def run_assistant(self, instructions):
        if self.thread and self.assistant:
            print("safe to run thread")

            self.run = self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                instructions=instructions
            )

    def process_message(self):
        if self.thread:

            # initialize messages with messages list from openAI func call
            messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
            summary = []

            last_message = messages.data[0]
            response = last_message.content[0].text.value
            role = last_message.role

            # append function adds response to end of summary
            summary.append(response)

            # interesting syntax can treat "" as a function call to a string
            self.summary = "\n".join(summary)


            print(f"SUMMARY-----> {role.capitalize()}: ==> {response}")

            # for msg in messages:
            #     role = msg.role
            #     content = msg.content[0].text.value

    def call_required_functions(self, required_actions):
        if not self.run:
            return
        tool_outputs = []

        for action in required_actions["tool_calls"]:
            func_name = action["function"]["name"]
            arguments = json.loads(action["function"]["arguments"])

            if func_name == "get_news":

                # news API comes in under topic tag with a dict
                output = get_news(topic=arguments["topic"])
                print(f"stuff{output}")

                final_str = ""

                for item in output:
                    final_str += "".join(item)

                # retrieve tool call and final string as part of the get_news call and add to tools_output after every iteration
                tool_outputs.append({"tool_call_id": action["id"],
                                     "output": final_str})
            
            else:
                raise ValueError(f"Unknown function: {func_name}")

            print("Submitting outputs back to the Assistant...")
            self.client.beta.threads.runs.submit_tool_outputs(
                thread_id=self.thread.id,
                run_id=self.run.id,
                tool_outputs=tool_outputs,
            )
                




    def wait_for_completed(self):
        if self.thread and self.run:
            while True:
                time.sleep(5)
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id,
                    run_id=self.run.id
                )
                print(f"RUN STATUS:::: {run_status.models_dump_json(indent=4)}")    

                if run_status.status == "completed":
                    self.process_message()
                    break

                elif run_status.status == "requires_action":                    
                    print("FUNCTION CALLING NOW...")
                    self.call_required_functions(self, required_actions)
    
        pass




if __name__ == "__main__":
    main()
