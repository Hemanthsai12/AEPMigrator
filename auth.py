import json, requests, jwt, datetime, calendar
import time
from os.path import join,dirname
from utility import *

def getAccessToken(orgData):
    orgFilePath = join(dirname(__file__).replace("\\","/"), "config/orgData.json")
    orgInfos = json.load(open(orgFilePath))
    config = orgInfos[orgData]
    ERROR_MESSAGE = "not found in current environment config file."
    print("Generating a new access token")
    print(config)
    if not(config["ORG_ID"]):
        raise Exception("ORG_ID" + ERROR_MESSAGE)
    elif not(config["TECHNICAL_ACCOUNT_ID"]):
        raise Exception("TECHNICAL_ACCOUNT_ID" + ERROR_MESSAGE)
    elif not(config["API_KEY"]):
        raise Exception("API_KEY" + ERROR_MESSAGE)
    elif not(config["CLIENT_SECRET"]):
        raise Exception("CLIENT_SECRET" + ERROR_MESSAGE)
    
    header_jwt = {'cache-control':'no-cache','content-type':'application/x-www-form-urlencoded'} ## setting the header

    '''{"exp":1643980664,
    "iss":"FD6415F354EEF3250A4C98A4@AdobeOrg",
    "sub":"C3F725DF61ECFC100A495FC6@techacct.adobe.com",
    "https://ims-na1.adobelogin.com/s/ent_dataservices_sdk":True,
    "aud":"https://ims-na1.adobelogin.com/c/f3b68a88667a4226b32cac29a42f9fa0"}'''

    # for exp time in a day
    date = datetime.datetime.utcnow()+datetime.timedelta(days=60) # specify days=number of days for token to expire
    utc_time = calendar.timegm(date.utctimetuple())

    jwtPayload = {

        "exp": utc_time,     #This is imp
        "iss": config["ORG_ID"],
        "sub": config["TECHNICAL_ACCOUNT_ID"],
        "https://ims-na1.adobelogin.com/s/ent_dataservices_sdk": True,
        "aud": "https://ims-na1.adobelogin.com/c/" + config["API_KEY"]
    }
    
    with open(join(dirname(__file__).replace("\\","/"), f"config/privatekeys/{orgData}-private.key"),'r') as f:
        private_key = f.read()

    jwtToken = jwt.encode(jwtPayload, private_key, algorithm='RS256')

    url = "https://ims-na1.adobelogin.com/ims/exchange/jwt/"
    header_jwt = {'cache-control':'no-cache','content-type':'application/x-www-form-urlencoded'}
    payload={'client_id': config["API_KEY"],
            'client_secret': config["CLIENT_SECRET"],
            'jwt_token': jwtToken}

    response = requests.request("POST", url,headers = header_jwt, data=payload)
    checkResponseCode(response)

    print('AccessToken generated successfully')
    json_response = response.json()
    expire = json_response['expires_in']
    print('Token valid till : ' + time.ctime(time.time()+ expire/1000))
    response=json.loads(response.text)
    config['ACCESS_TOKEN'] = json_response['access_token']

    orgInfos[orgData] = config

    f = open(orgFilePath, "w")
    json.dump(orgInfos, f,indent=4)
    f.close()

    data = {"Accept": "application/json",
            "Authorization": "Bearer "+ config['ACCESS_TOKEN'],
            "x-api-key": config["API_KEY"],
            "x-gw-ims-org-id": config["ORG_ID"]
            }

    with open(join(dirname(__file__).replace("\\","/"), f"config/headerfiles/{orgData}-headers.json"), 'w') as f:
        json.dump(data, f,indent=4)
        f.close() 
        print("The headerfile has also created/updated.")
