from turtle import width
import requests
import pandas as pd
import json

def get_orders(url: str, Stall_ID: int):
    txt = f'{url}/query/cmd=ORDER&{Stall_ID}'
    res = pd.read_html(txt)[0]
    res = res.drop(res.columns[0], axis=1)
    return res

def json_to_dic(path: str):
    import json
    with open(path) as file:
        return json.load(file)

def notify_phone(number: str, Message: str):
    from twilio.rest import Client
    import os
    account_sid = 'ACcdf4ba64ae7c2ce3a80507fa80a29b65' 
    auth_token = '92b9680ab3bdf73d90cbc04884d998cc' 
    client = Client(account_sid, auth_token) 
    
    message = client.messages.create(  
                                messaging_service_sid='MG42b66d8934b1d8fdaecae06a0e3ea7a7', 
                                body=f'{Message}',      
                                to=f'+65{number}' 
                            ) 
    print(message.sid)

def PROCESSBARCODE(frame, det):
    import cv2

    data, vertices, _ = det.detectAndDecode(frame)
    if vertices is not None:
        if data:
            for x, y, width, height in vertices:
                cv2.putText(frame, data, (x, y - 10), cv2.FONT_HERSHEY_SCRIPT_COMPLEX, 0.9, color, stroke)  # PUT TEXT FOR LABELLING
                return data