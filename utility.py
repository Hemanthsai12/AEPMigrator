import requests,json, os
from os.path import dirname, join

def loadConfigFile():
    configFilePath = join(dirname(__file__), "config","org.json")
    config = json.load(open(configFilePath))    
    return config

def checkResponseCode(response):
    if not(response.status_code >= 200 and response.status_code <= 299):
        print(response.text)
        exit()

def checkAuthError(response):
    if (response.status_code >= 400 and response.status_code <= 499):
        return True
    else:
        return False

def checkKeyFile(privateKey):
    filename = privateKey.filename
    if "." in filename:
        ext = filename.rsplit(".", 1)[1]
        if ext.upper() in ["KEY"]:
            return True
        else:
            return False
    else:
        return False

def checkResponseCode(response):
   if not(response.status_code >= 200 and response.status_code <= 299):
      print(response.text)
      #print("\n"+ response["report"]["detailed-message"])

def checkDuplicateItems(selectedItems,destItems):
    duplicateItems=[]
    copySelectedItems=selectedItems.copy()
    for item in copySelectedItems:
        if item in destItems:
            duplicateItems.append(item)
            selectedItems.remove(item)

    print("Selected Item: ",str(selectedItems))
    print("Duplicate Item: ",str(duplicateItems))
    return selectedItems,duplicateItems

def saveResponseFile(filePath,componentName,componentResponse):
    os.makedirs(os.path.dirname(filePath), exist_ok=True)
    with open(filePath, 'w') as fp:
        json.dump(componentResponse,fp, indent=4)
    print("\n"+ componentName + " response saved in file")

def getAllIdNamespaces(headers):
    url = "https://platform.adobe.io/data/core/idnamespace/identities"
    payload={}
    headers['Accept']='application/json'
    response = requests.request("GET", url, headers=headers, data=payload)
    checkResponseCode(response)
    return response

def getIdNamespaceById(headers,identityId):
    url = "https://platform.adobe.io/data/core/idnamespace/identities/"+identityId
    payload={}
    headers['Accept']='application/json'
    response = requests.request("GET", url, headers=headers, data=payload)
    checkResponseCode(response)
    return response

def postIdNamespace(headers,filePath):
    url = "https://platform.adobe.io/data/core/idnamespace/identities"
    payload=open(filePath, 'rb')
    headers['Accept']='application/json'
    headers['Content-Type']='application/json'
    #print("\nDestination Headers: ",headers)
    response = requests.request("POST", url, headers=headers, data=payload)
    checkResponseCode(response)
    return response

def getAllClasses(headers):
    url = "https://platform.adobe.io/data/foundation/schemaregistry/tenant/classes"
    payload={}
    headers['Accept']='application/vnd.adobe.xed-id+json'
    response = requests.request("GET", url, headers=headers, data=payload)
    checkResponseCode(response)
    return response    

def getClassesById(headers,classesId):
    url = "https://platform.adobe.io/data/foundation/schemaregistry/tenant/classes/"+classesId
    payload={}
    headers['Accept']='application/vnd.adobe.xed-id+json; version=1'
    response = requests.request("GET", url, headers=headers, data=payload)
    #print("\nResponse: ",response)
    checkResponseCode(response)
    return response    

def postClasses(headers,filePath):
    url = "https://platform.adobe.io/data/foundation/schemaregistry/tenant/classes"
    payload=open(filePath, 'rb')
    headers['Accept']='application/json'
    headers['Content-Type']='application/json'
    #print("\nDestination Headers: ",headers)
    response = requests.request("POST", url, headers=headers, data=payload)
    checkResponseCode(response)
    return response  

def getAllMixins(headers):
    url = "https://platform.adobe.io/data/foundation/schemaregistry/tenant/mixins"
    payload={}
    headers['Accept']='application/vnd.adobe.xed-id+json'
    response = requests.request("GET", url, headers=headers, data=payload)
    checkResponseCode(response)
    response_json = json.loads(response.text)
    results = response_json['results']
    next_url = response_json['_links'].get('next')
    
    # get additional pages of results using the 'next' parameter
    while next_url:
        response = requests.request("GET", next_url, headers=headers, data=payload)
        checkResponseCode(response)
        response_json = json.loads(response.text)
        results.extend(response_json['results'])
        next_url = response_json['_links'].get('next')
    
    response_json['results'] = results
    return json.dumps(response_json)

def getMixinById(headers,mixinId):
    url = "https://platform.adobe.io/data/foundation/schemaregistry/tenant/mixins/"+mixinId
    payload={}
    headers['Accept']='application/vnd.adobe.xed-id+json;version=1'
    response = requests.request("GET", url, headers=headers, data=payload)
    #print("\nResponse: ",response)
    checkResponseCode(response)
    return response

def postMixin(headers,filePath):
    url = "https://platform.adobe.io/data/foundation/schemaregistry/tenant/mixins"
    payload=open(filePath, 'rb')
    headers['Accept']='application/json'
    headers['Content-Type']='application/json'
    #print("\nDestination Headers: ",headers)
    response = requests.request("POST", url, headers=headers, data=payload)
    checkResponseCode(response)
    return response

def getAllSchemas(headers):
    url = "https://platform.adobe.io/data/foundation/schemaregistry/tenant/schemas"
    payload={}
    headers['Accept']='application/vnd.adobe.xed-id+json'
    response = requests.request("GET", url, headers=headers, data=payload)
    checkResponseCode(response)

    # get the first page of results
    response_json = json.loads(response.text)
    results = response_json['results']
    next_url = response_json['_links'].get('next')
    
    # get additional pages of results using the 'next' parameter
    while next_url:
        response = requests.request("GET", next_url, headers=headers, data=payload)
        checkResponseCode(response)
        response_json = json.loads(response.text)
        results.extend(response_json['results'])
        next_url = response_json['_links'].get('next')
    
    response_json['results'] = results
    return json.dumps(response_json)

def getSchemaById(headers,schemaId):
    url = "https://platform.adobe.io/data/foundation/schemaregistry/tenant/schemas/"+schemaId
    payload={}
    headers['Accept']='application/vnd.adobe.xed-id+json;version=1'
    response = requests.request("GET", url, headers=headers, data=payload)
    checkResponseCode(response)
    return response

def postSchema(headers,filePath):
    url = "https://platform.adobe.io/data/foundation/schemaregistry/tenant/schemas"
    payload=open(filePath, 'rb')
    headers['Accept']='application/json'
    headers['Content-Type']='application/json'
    #print("\nDestination Headers: ",headers)
    response = requests.request("POST", url, headers=headers, data=payload)
    checkResponseCode(response)
    return response

def getAllDatasets(headers):
    url = "https://platform.adobe.io/data/foundation/catalog/dataSets?limit=100"
    payload={}
    headers['Accept']='application/json'
    response = requests.request("GET", url, headers=headers, data=payload)
    checkResponseCode(response)
    return response

def getDatasetById(headers,datasetId):
    url = "https://platform.adobe.io/data/foundation/catalog/dataSets/"+datasetId
    payload={}
    headers['Accept']='application/json'
    response = requests.request("GET", url, headers=headers, data=payload)
    checkResponseCode(response)
    return response

def postDataset(headers,filePath):
    url = "https://platform.adobe.io/data/foundation/catalog/dataSets"
    payload=open(filePath, 'rb')
    headers['Accept']='application/json'
    headers['Content-Type']='application/json'
    #print("\nDestination Headers: ",headers)
    response = requests.request("POST", url, headers=headers, data=payload)
    checkResponseCode(response)
    return response

def getAllSegments(headers):
    url = "https://platform.adobe.io/data/core/ups/segment/definitions"
    payload={}
    headers['Accept']='application/json'
    response = requests.request("GET", url, headers=headers, data=payload)
    checkResponseCode(response)
    return response

def getSegmentById(headers,segmentId):
    url = "https://platform.adobe.io/data/core/ups/segment/definitions/"+segmentId
    payload={}
    headers['Accept']='application/json'
    response = requests.request("GET", url, headers=headers, data=payload)
    checkResponseCode(response)
    return response

def postSegment(headers,filePath):
    url = "https://platform.adobe.io/data/core/ups/segment/definitions"
    payload=open(filePath, 'rb')
    headers['Accept']='application/json'
    headers['Content-Type']='application/json'
    #print("\nDestination Headers: ",headers)
    response = requests.request("POST", url, headers=headers, data=payload)
    checkResponseCode(response)
    return response

def getSchemaExport(headers,resourceId):
    url = "https://platform.adobe.io/data/foundation/schemaregistry/rpc/export/"+resourceId
    payload={}
    headers['Accept']='application/vnd.adobe.xed-id+json;version=1'
    response = requests.request("GET", url, headers=headers, data=payload)
    checkResponseCode(response)
    return response
    
def postSchemaExport(headers,filePath):
    url = "https://platform.adobe.io/data/foundation/schemaregistry/rpc/import"
    payload=open(filePath, 'rb')
    headers['Accept']='application/json'
    headers['Content-Type']='application/json'
    response = requests.request("POST", url, headers=headers, data=payload)
    checkResponseCode(response)
    return response