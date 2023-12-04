from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import pandas as pd
import time


API_KEY = ''

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/search-leads', methods=['POST'])
def search_leads():
    data = request.json
    formated = []

    businesses = data.get('array_bussinesses', [])
    location = data.get('location', '')
    num_of_queries = len(businesses)

    results = []
    for buisnes in businesses:
        place_ids, next_page_flag, next_page_token = find_places(buisnes, location, API_KEY)
        formated.append(get_details(place_ids, API_KEY))
        if next_page_flag == True:
            place_ids = load_next_page(next_page_token, API_KEY)
            formated.append(get_details(place_ids, API_KEY))   
    flat_data = [item for sublist in formated for item in sublist]
    flat_data = [dict(item, index=index) for index, sublist in enumerate(formated) for item in sublist]
    # Create a DataFrame
    df = pd.DataFrame(flat_data)
    # Save to Excel
    # df.to_excel("output.xlsx", index=False)
    # print(formated)

    return jsonify(formated)

def find_places(buisness, location, api_key):
    place_ids = []
    url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?query='+buisness+'%20in%20'+location+'&key='+api_key+''
    response = requests.get(url)
    if response.status_code == 200:
        counter = 0
        next_page_flag = None
        next_page_token = None
        # Successful request
        data = response.json()  # If the response contains JSON data
        if 'next_page_token' in data:
            next_page_flag = True
            next_page_token = data['next_page_token']
        for result in data['results']:
            place_ids.append(result['place_id'])
            counter += 1
        print('Page hits' + str(counter))
        print(place_ids)
        print("NEXT PAGE:" + str(next_page_flag))
        return place_ids, next_page_flag, next_page_token
    else:
        # Failed request
        print(f"Error: {response.status_code}")
        print(response.text)  # Print the error message or response content

def load_next_page(next_page_token, api_key):
    url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?pagetoken='+next_page_token+'&key='+api_key
    response = requests.get(url)
    place_ids = []
    counter = 0
    rec_res = []
    if response.status_code == 200:
        data = response.json()
        for result in data['results']:
            place_ids.append(result['place_id'])
            counter += 1
        print('Page hits' + str(counter))
        if 'next_page_token' in data:
            print("Sleeping for 5 seconds.....")
            time.sleep(5)
            rec_res = load_next_page(data['next_page_token'], api_key)
        return place_ids + rec_res  # Combine the results from the recursive call
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
    
def get_details(place_ids, api_key):
    details = []
    formated = []
    for place_id in place_ids:
        url = 'https://maps.googleapis.com/maps/api/place/details/json?fields=name%2Crating%2Cformatted_phone_number%2Cwebsite&place_id='+place_id+'&key='+api_key
        response = requests.get(url)
        results = response.json()
        details.append(results)
    for result in details:
        formated.append(result['result'])
    return formated



if __name__ == '__main__':
    app.run(debug=True)
