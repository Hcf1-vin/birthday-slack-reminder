import yaml
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
import json
import requests
import fastjsonschema as fj

logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

class ValidationException(Exception):
    pass

def read_file(file_name):
    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),file_name)
    f = open(file_path, "r")
    return f.read()

def convert_birthday(birthday):

    return datetime.strptime(str(birthday), "%d%m%Y")

def get_ordinal_age(age):

    age = str(age)

    if age[-1] == "1":
        ordinal_age = age + "st"
    elif age[-1] == "2":
        ordinal_age = age + "nd"
    elif age[-1] == "3":
        ordinal_age = age + "rd"
    else:
        ordinal_age = age + "th"

    return ordinal_age

def send_card(name, birthday, age, ordinal_age, days_until, address):

    if ordinal_age != None:
        message = f"It is {name}'s {ordinal_age} birthday in {days_until} days. Send a birthday card"
    else:
        message = f"It is {name}'s birthday in {days_until} days. Send a birthday card"
    
    if address != None:
        message = f"{message} to {address}."
    send_slack(message)

def send_message(name, birthday, age, ordinal_age):

    if today.hour in conf["config"]["alerts"]["message"]["schedule"]:
        if ordinal_age != None:
            message = f"Wish {name} a Happy {ordinal_age} Birthday"
        else:
            message = f"Wish {name} a Happy Birthday"

        send_slack(message)

def send_slack(message):

    slack_headers = {"Content-Type": "application/json"}

    slack_url = conf["config"]["slack"]["webhook_url"]
    
    slack_data = {}
    slack_data["icon_emoji"] = conf["config"]["slack"]["icon"]
    slack_data["channel"] = conf["config"]["slack"]["channel"]
    slack_data["username"] = conf["config"]["slack"]["bot_name"]
    slack_data["text"] = message

    slack_encode = json.dumps(slack_data).encode('utf-8')
    response = requests.post(slack_url, data=slack_encode, headers=slack_headers)
    print("Response: " + str(response.text))
    print("Response code: " + str(response.status_code))

def validate_schema():
    schema_file = read_file("schema.yaml")
    schema = yaml.load(schema_file, Loader=yaml.FullLoader)
    try:
        fj.validate(schema, conf)
    except fj.JsonSchemaException as e:
        send_slack("schema error")
        raise ValidationException(str(e))
if __name__ == "__main__":
    conf = yaml.load(read_file("conf.yaml"), Loader=yaml.FullLoader)
    validate_schema()
    today = datetime.today()
    for a in conf["birthdays"]:
        try:
            if "disabled" in a:
                if a["disabled"] == True:
                    disabled = a["disabled"]
                    print("************")
                    print("skipping " +  a["full_name"])
                    print("************")
                    continue

            name = a["name"]
            full_name = a["full_name"]

            if "year" in a:
                birthday = convert_birthday(str(a["day"]) + str(a["month"]) + str(a["year"]))
            else:
                birthday = convert_birthday(str(a["day"]) + str(a["month"])  + str(today.year))

            age = relativedelta(today, birthday).years + 1

            if age == 0:
                age = None
                ordinal_age = None
            else:
                ordinal_age = get_ordinal_age(age)

            days_until = (datetime(today.year, birthday.month, birthday.day) - today).days

            if days_until < 0:
                days_until = (datetime((today.year + 1), birthday.month, birthday.day) - today).days

            if "address" in a:
                address = a["address"]
            else:
                address = None

            print("name: " + name)
            print("full_name: " + str(full_name))
            print("birthday: " + str(birthday))
            print("age: " + str(age))
            print("ordinal_age: " + str(ordinal_age))
            print("days_until: " + str(days_until))

            if days_until in conf["config"]["alerts"]["send_card"]["schedule"]["days"] and today.hour in conf["config"]["alerts"]["send_card"]["schedule"]["hours"]:
                send_card(name, birthday, age, ordinal_age, days_until, address)

            if datetime(today.year, birthday.month, birthday.day) == datetime(today.year, today.month, today.day):
                send_message(name, birthday, age, ordinal_age)
        except Exception as e:
            print(a)
            continue