import openai
import json
from flask import Flask, jsonify, request
import requests
import json
from flask_cors import CORS
import json
import openai
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests
import requests
import xml.etree.ElementTree as ET
import datetime
from zeep import Client
from zeep.wsse.username import UsernameToken
from zeep.wsse.utils import WSU

app = Flask(__name__)
CORS(app)
openai.api_key = ""
jsonData = None
def get_customer_information(customer):
                    """Get the information about given customer."""
                    #url = "https://edrx-dev1.fa.us2.oraclecloud.com/fscmRestApi/resources/11.13.18.05/customerAccountSitesLOV"
                    url = "https://edrx-dev1.fa.us2.oraclecloud.com/fscmRestApi/resources/11.13.18.05/receivablesCustomerAccountSiteActivities?finder=CustomerAccountSiteActivitiesFinder;CustomerName=" + customer
                    #url = "https://edrx-dev1.fa.us2.oraclecloud.com/fscmRestApi/resources/11.13.18.05/receivablesCustomerAccountSiteActivities"
                    headers = {
                    'Authorization': 'Basic U3VicmF0YS5NdWtoZXJqZWU6c3VicmF0YTE5ODE='
                    }
                    global jsonData;
                    response = requests.get(url, headers=headers)
                    for item in response.json()['items']:
                        if customer in item["CustomerName"]  :
                            jsonData = json.loads(json.dumps(item))
                            return json.dumps(item)
                        
def get_credit_limit(creditLimit):
        
        """Get the information credit limit of given account number"""
        url = "https://ibmoic-idmfguxp1uca-ia.integration.ocp.oraclecloud.com/ic/api/integration/v1/flows/rest/GETCUSTOMERCREDITLIMIT/1.0/get_cust_credit_limit"
        body = {
            "accountNumber": creditLimit
        }
        headers = {
            "Authorization": "Basic VmlrcmFtaml0LnNlbjFAaWJtLmNvbTpXZWxjb21lQDIwMjQ=",
            "Content-Type": "application/json"
        }
        try:    
            response = requests.post(url, data=json.dumps(body), headers=headers)
        except Exception as e:
            print(str(e))
        return response.json()
def increase_credit_limit(customer,CreditLimit):

    url = "https://ibmoic-idmfguxp1uca-ia.integration.ocp.oraclecloud.com/ic/api/integration/v1/flows/rest/GETPARTYIDREPORTSERVICE/1.0/get_cust_party_id"
    body = {
        "customerName": customer
    }
    headers = {
        "Authorization": "Basic VmlrcmFtaml0LnNlbjFAaWJtLmNvbTpXZWxjb21lQDIwMjQ=",
        "Content-Type": "application/json"
    }  
    response = requests.post(url, data=json.dumps(body), headers=headers)


    timestamp_token = WSU.Timestamp()
    today_datetime = datetime.datetime.utcnow()
    expires_datetime = today_datetime + datetime.timedelta(minutes=10)
    timestamp_elements = [
    WSU.Created(today_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"),
    WSU.Expires(expires_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z")
    ]
    timestamp_token.extend(timestamp_elements)
    user_name_token = UsernameToken('Subrata.Mukherjee', 'subrata1981', timestamp_token=timestamp_token)

    soap_body = {
        'AccountNumber': response.json().get("AccountNumber"),
        'CustomerAccountId': response.json().get("custAccountId"),
        'PartyId': response.json().get("partyId"),
        'CreditLimit': CreditLimit,
        'CreditCurrencyCode': 'USD',
    }
    client = Client('https://edrx-dev1.fa.us2.oraclecloud.com/fscmService/ReceivablesCustomerProfileService?WSDL', wsse=user_name_token)
    response = client.service.updateCustomerProfile(customerProfile=soap_body)
    return response;
	

function_descriptions_multiple = [
    {
        "name": "get_customer_information",
        "description": "Get the information about given customer.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer": {
                    "type": "string",
                    "description": "The customer name, e.g. BKNIBM Corporation, Roopa Customer, Sumit Intl, TESTCUST1, DP customer"
                },

            },
            "required": ["customer"],
        },
    },
    {
        "name": "get_credit_limit",
        "description": "Get the credit limit of about given account number.",
        "parameters": {
            "type": "object",
            "properties": {
                "creditLimit": {
                    "type": "string",
                    "description": "The creditLimit is, e.g. 5000, 4000, 70078"
                },

            },
            "required": ["creditLimit"],
        },
    }
    ,{
        "name": "increase_credit_limit",
        "description": "increase credit limit based on given customer details",
        "parameters": {
            "type": "object",
            "properties": {
                "customer": {
                    "type": "string",
                    "description": "The customer name, e.g. BKNIBM Corporation, Roopa Customer, Sumit Intl, TESTCUST1, DP customer"
                },
                "CreditLimit": {
                    "type": "string",
                    "description": "Increase / Decrease or update the credit limit , e.g. 6000",
                }

            },
            "required": ["customer","CreditLimit"],
        },
    },
]

def ask_and_reply(prompt):
    """Give LLM a given prompt and get an answer."""

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=[{"role": "user", "content": prompt}],
        # add function calling
        functions=function_descriptions_multiple,
        function_call="auto",  # specify the function call
    )

    output = completion.choices[0].message
    return output
	
@app.route('/', methods = ['GET', 'POST'])
def home():
    if(request.method == 'POST'):
        # user_prompt = "what is the CustomerAccountId of BKNIBM Corporation?"
        user_prompt = request.json.get("userMessage")
        print("user_prompt>>>>>>>"+user_prompt)
        print(ask_and_reply(user_prompt))
        output =ask_and_reply(user_prompt)
        try:
            if (output.function_call.name == "get_customer_information"):

                    params = json.loads(output.function_call.arguments)
                    chosen_function = eval(output.function_call.name)
                    flight = chosen_function(**params)
                    # # Get info for the next prompt
                    output  = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo-0613",
                            messages=[
                                {"role": "user", "content": user_prompt},
                                {"role": "function", "name": output.function_call.name, "content": flight},
                            ],
                            functions=function_descriptions_multiple,
                        )

                    # customer = json.loads(output.function_call.arguments).get("customer")
                    # chosen_function = eval(output.function_call.name)
                    # customerDetails = chosen_function(customer)

                    # print(customer)
                    # print(customerDetails)
					
                    # CustomerAccountId = json.loads(customerDetails).get("CustomerAccountId")
                    # PartyId = "2025"
                    # # CreditLimit = json.loads(customerDetails).get("CustomerAccountId")

                    # print(CustomerAccountId)
                    if len(output.choices[0].message.content)>100 :
                        return {'data':jsonData,'containJson':True}
                    else:
                          return {'data':output.choices[0].message.content,'containJson':False}
                
            elif output.function_call.name == "get_credit_limit" :
                creditLimit = json.loads(output.function_call.arguments).get("creditLimit")
                CreditLimitRes = get_credit_limit(creditLimit)
                
                output  = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo-0613",
                    messages=[
                        {"role": "user", "content": user_prompt},
                        {"role": "function", "name": output.function_call.name, "content": str(CreditLimitRes)},
                    ],
                    functions=function_descriptions_multiple,
                )
                return {'data':output.choices[0].message.content,'containJson':False}
                
            elif output.function_call.name == "increase_credit_limit" :
					# # Scenario 2: Book a new flight

                    # user_prompt = f"Increase the credit limit of {CustomerAccountId} to 5000 " + "Those are the additional details PartyId>

                    # print(ask_and_reply(user_prompt))

                    # output =ask_and_reply(user_prompt)

                    # # Get info for the next prompt


                    customer = json.loads(output.function_call.arguments).get("customer")
                    CreditLimit = json.loads(output.function_call.arguments).get("CreditLimit")
                    chosen_function = eval(output.function_call.name)
                    IncreaseCreditLimitRes = chosen_function(customer,CreditLimit)
                    
                    
                    output  = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo-0613",
                        messages=[
                            {"role": "user", "content": "What is the credit limit now?"},
                            {"role": "function", "name": output.function_call.name, "content": str(IncreaseCreditLimitRes)},
                        ],
                        functions=function_descriptions_multiple,
                    )
                    return {'data':"Your credit limit hasbeen updated."+output.choices[0].message.content,'containJson':False}
        except:
                    return {'data':openai.ChatCompletion.create(
						model="gpt-3.5-turbo-0613",
						messages=[{"role": "user", "content": user_prompt}],
					).choices[0].message.content,'containJson':False}    
if __name__ == '__main__':

    app.run(port='5000',host='0.0.0.0')
