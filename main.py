from asyncio.windows_events import NULL
from flask import Flask,render_template,request,redirect,url_for,flash
import requests,json
import os
from os.path import dirname, join
from os import path

from utility import *
from auth import getAccessToken

app = Flask(__name__)

app.config['SECRET_KEY'] = 'SS!$#_'
app.config['CONFIG'] = join(dirname(__file__),"config/")

sourceSandboxHeaders={}
destSandboxHeaders={}
sourceSandboxDict={}
destSandboxDict={}
idNamespaceDict={}
classesDict={}
fieldGroupDict={}
schemaDict={}
datasetDict={}
segmentDict={}
sourceTenantId = ""
destinationTenantId = ""

def getTenantId(config):
    url = "https://platform.adobe.io/data/foundation/schemaregistry/stats"
    payload={}
    headers = {
    'Accept': 'application/json', 'Authorization': 'Bearer '+config["ACCESS_TOKEN"], 'x-api-key': config["API_KEY"], 'x-gw-ims-org-id': config["ORG_ID"], 'x-sandbox-name': 'prod',
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response

def loadHeaderFiles(orgName, orgData):
    headerFilePath = join(app.config['CONFIG'], "headerfiles")

    try:
        print(orgName)
        data = {"Accept": "application/json",
        "Authorization": 'Bearer ' + orgData["ACCESS_TOKEN"],
        "x-api-key": orgData["API_KEY"],
        "x-gw-ims-org-id": orgData["ORG_ID"]
        }
        with open(join(headerFilePath,f'{orgName}-headers.json'), 'w') as f:
            json.dump(data, f,indent=4)
            f.close() 
            print("The headerfile has also created/updated.")
    except:
        print(f'{orgData} header file not found! Try to delete and authorise again!')

@app.route('/', methods=['GET','POST'])
def home():
    if request.method == "GET":
        return render_template('home.html')
    elif request.method == "POST":
        return redirect(url_for('auth'))

@app.route('/auth', methods = ["GET","POST"])
def auth():
    orgFile = join(app.config['CONFIG'], "orgData.json")
    if not path.isfile(orgFile):
        os.makedirs(os.path.dirname(orgFile), exist_ok=True)
        with open(orgFile, 'w') as fp:
            json.dump({},fp,indent=4)
            fp.close()
        print("org.json created at "+orgFile)
    
    with open(orgFile, 'r') as fp:
        org = json.load(fp)
        fp.close()

    if request.method == "GET":
        #if len(list(org.keys()))>0:
        try:
            for orgdata in org:
                print("Org Name : ",orgdata)
                config = org[orgdata]
                if "ACCESS_TOKEN" in config.keys():
                    response = getTenantId(config)
                    if checkAuthError(response):
                        print("found expired accessToken. new accessToken will be generated.")
                        getAccessToken(orgdata)
                        with open(orgFile, 'r') as fp:
                            org = json.load(fp)
                            fp.close()
                        config = org[orgdata]
                        response = getTenantId(config)
                    else:
                        print("found working accessToken.")
                    response=json.loads(response.text)
                    config['tenantId'] = response['tenantId']
                    org[orgdata] = config
                    with open(orgFile, 'w') as fp:
                        json.dump(org,fp,indent=4)
                        fp.close()
                    
                    loadHeaderFiles(orgdata, org[orgdata])
                        
                else:
                    print("AccessToken not found! Generating new one.")
                    getAccessToken(orgdata)

            return render_template("auth.html", org=org)
        
        except:
            print("Error")
            return render_template("auth.html")


    elif request.method == "POST":
        with open(orgFile, 'r') as fp:
            org = json.load(fp)
            fp.close()
        if request.files:
            config=request.files["config-json"]
            privateKey = request.files["private-key"]
            orgName = request.form.get("org-name")
            
            if config.mimetype=='application/json' and checkKeyFile(privateKey):
                # Save the both the file in the directory and redirect to sandbox browse page
                print(config,privateKey)
                config = json.load(config)
                org[orgName] = config
                print(config)
                # config.save(join(app.config["CONFIG"], f"{orgName}.json"))
                privateKey.save(join(app.config["CONFIG"],"privatekeys", f"{orgName}-private.key"))
                print(org)
                with open(orgFile, 'w') as fp:
                    json.dump(org,fp,indent=4)
                    fp.close()
                print("generated new accessToken from uploaded file rn.")
                getAccessToken(orgName)  # Call auth.getAccessToken to generate token and update in the config file
                flash("Authorization Successfull.", category='success')
                with open(orgFile, 'r') as fp:
                    org = json.load(fp)
                    config = org[orgName]
                    fp.close()

                response = getTenantId(config)
                response=json.loads(response.text)
                config['tenantId'] = response['tenantId']
                org[orgName] = config
                with open(orgFile, 'w') as fp:
                    json.dump(org,fp,indent=4)
                    fp.close()
                return render_template("auth.html", org=org)

            else:
                flash("Invalid File Type!", category='error')
                print("Invalid File type.")
            return render_template("auth.html", org=org)

@app.route('/auth/delete/<orgName>',methods = ["GET","POST"])
def authDelete(orgName):
    
    orgFile = join(app.config['CONFIG'], "orgData.json")
    with open(orgFile, 'r') as fp:
        org = json.load(fp)
        fp.close()
    del org[orgName]

    with open(orgFile, 'w') as fp:
        json.dump(org,fp,indent=4)
        fp.close()

    headerFilePath = join(app.config['CONFIG'],'headerfiles',f'{orgName}-headers.json')
    privateKeyFilePath = join(app.config['CONFIG'],'privatekeys',f'{orgName}-private.key')
    if os.path.exists(headerFilePath):
        os.remove(headerFilePath)
    else:
        print(f"The {headerFilePath} does not exist")
    if os.path.exists(privateKeyFilePath):
        os.remove(privateKeyFilePath)
    else:
        print(f"The {privateKeyFilePath} does not exist")
    
    return render_template("auth.html", org=org)


@app.route('/sandbox/<step>', methods=['GET','POST'])
def sandbox(step):
    global sourceSandboxHeaders
    global destSandboxHeaders
    global sourceSandboxDict
    global destSandboxDict
    global orgList
    global sourceTenantId
    global destinationTenantId

    #try:
    with open(join(app.config["CONFIG"], "orgData.json"),'r') as f:
        orgData = json.load(f)
        f.close()

    if request.method=="GET":
        orgList = list(orgData.keys())
        print(orgList)

        '''
        for org in orgList:
            with open(join(app.config["CONFIG"],"headerfiles", f"{org}-headers.json"),'r') as f:
                headers = json.load(f)
                f.close()

            url = "https://platform.adobe.io/data/foundation/sandbox-management/"
            response = requests.request("GET", url, headers=headers)
            checkResponseCode(response)
            response=json.loads(response.text)
            for i in response['sandboxes']:
                sandboxDict[i['title']]=i['name']
            sandboxList=list(sandboxDict.keys())

            orgWithSandboxDict[org] = sandboxList

        print('orgWithSandboxDict - ',orgWithSandboxDict)'''
        
        return render_template('organisation.html', orgList=orgList)

    if request.method=="POST":

        if step=='org':
            srcOrg = request.form.get("sourceOrg")
            destOrg = request.form.get("destinationOrg")
            reqOrgSandboxlist={}

            with open(join(app.config["CONFIG"],"headerfiles", f"{srcOrg}-headers.json"),'r') as f:
                sourceSandboxHeaders = json.load(f)
                f.close()

            url = "https://platform.adobe.io/data/foundation/sandbox-management/"
            response = requests.request("GET", url, headers=sourceSandboxHeaders)
            checkResponseCode(response)
            response=json.loads(response.text)
            for i in response['sandboxes']:
                sourceSandboxDict[i['title']]=i['name']
            sandboxList=list(sourceSandboxDict.keys())
            print(sandboxList)
            reqOrgSandboxlist[srcOrg] = sandboxList

            with open(join(app.config["CONFIG"],"headerfiles", f"{destOrg}-headers.json"),'r') as f:
                destSandboxHeaders = json.load(f)
                f.close()
            
            url = "https://platform.adobe.io/data/foundation/sandbox-management/"
            response = requests.request("GET", url, headers=destSandboxHeaders)
            checkResponseCode(response)
            response=json.loads(response.text)
            for i in response['sandboxes']:
                destSandboxDict[i['title']]=i['name']
            sandboxList=list(destSandboxDict.keys())
            print(sandboxList)
            reqOrgSandboxlist[destOrg] = sandboxList
            sourceTenantId = orgData[srcOrg]['tenantId']
            destinationTenantId = orgData[destOrg]['tenantId']
            return render_template('sandbox.html', sourceOrg = srcOrg, destinationOrg = destOrg, sourceSandboxList = reqOrgSandboxlist[srcOrg], destinationSandboxList = reqOrgSandboxlist[destOrg])

        elif step == 'sandbox':
            
            sourceSandbox=request.form['sourceSandbox']
            destinationSandbox=request.form['destinationSandbox']

            #print("Source Sandbox: ",str(sourceSandbox), "\nDestination Sandbox: ", str(destinationSandbox))

            sourceSandboxHeaders['Accept']='application/vnd.adobe.xed-id+json'
            sourceSandboxHeaders['x-sandbox-name']=sourceSandboxDict[sourceSandbox]
            print("Source Sandbox Headers", sourceSandboxHeaders)
            
            destSandboxHeaders['Accept']='application/vnd.adobe.xed-id+json'
            destSandboxHeaders['x-sandbox-name']=destSandboxDict[destinationSandbox]
            print("\nDestination Sandbox Headers", destSandboxHeaders)

            return render_template('menu.html')
        
    '''except Exception as e:
        print(str(e))
        return redirect(url_for('home'))
    '''
@app.route('/idnamespace', methods=['GET','POST'])
def idnamespace():
    global idNamespaceDict
    global sourceSandboxHeaders
    global destSandboxHeaders
    try:
        if request.method=="GET":
            response=getAllIdNamespaces(sourceSandboxHeaders)
            response=json.loads(response.text) 
            idNamespaceDict ={}
            for i in response:
                idNamespaceDict[i['name']]=i['id']

        sourceIdNamespaceList=list(idNamespaceDict.keys())
        print("\nSource Identities List: ",sourceIdNamespaceList)
        
        if request.method=="POST":

            selectedIdNamespace=[]
            selectedIdNamespace=request.form.getlist("sourceIdNamespaceCheckBox")
            print("\nSelected Identity Namespaces: ",selectedIdNamespace)

            response=getAllIdNamespaces(destSandboxHeaders)
            response=json.loads(response.text) 
            
            destIdNamespaceList=[]
            for i in response:
                destIdNamespaceList.append(i['name'])
            
            selectedIdNamespace,duplicateIdNamespace=checkDuplicateItems(selectedIdNamespace,destIdNamespaceList)
            
            if len(duplicateIdNamespace)>1:
                print("Id Namespace already present in namespace. Deploying other Id Namespace")       
                flash("These Id Namespace are already present in Destination Sandbox:" +str(duplicateIdNamespace))
                flash("\nDeploying Id Namespace: " + str(selectedIdNamespace))
            elif len(duplicateIdNamespace)==1 and len(selectedIdNamespace)==0:
                print("Id Namespace already present in Destination")
                flash("This Id Namespace is already present in the Destination Sandbox:" +str(duplicateIdNamespace))
                #return render_template('home.html')
            else:
                pass
     
            for identity in selectedIdNamespace:
                identityId=idNamespaceDict[identity]
                response=getIdNamespaceById(sourceSandboxHeaders,str(identityId))
                response=json.loads(response.text)

                file_path = join(dirname(__file__).replace("\\","/"),"idNamespaceResponses/")+ identity + ".json"

                saveResponseFile(file_path,identity,response)
                
                response=postIdNamespace(destSandboxHeaders,file_path)
                response=json.loads(response.text) 
                flash(identity + " deployed in Destination Sandbox - " + destSandboxHeaders['x-sandbox-name'])

                
        return render_template('idnamespace.html',idNamespaceList=sourceIdNamespaceList)

    except Exception as e:
	        return(str(e))

@app.route('/class', methods=['GET','POST'])
def classesname():
    global classesDict
    global sourceSandboxHeaders
    global destSandboxHeaders
    global sourceTenantId
    global destinationTenantId
    try:
        if request.method=="GET":
            response=getAllClasses(sourceSandboxHeaders)
            response=json.loads(response.text) 

            for i in response['results']:
                classesDict[i['title']]=i['meta:altId']

        sourceClassesList=list(classesDict.keys())
        print("\nSource Classes List: ",sourceClassesList)  
        
        if request.method=="POST":

            selectedClasses=[]
            selectedClasses=request.form.getlist("sourceClassesCheckBox")
            print("\nSelected Classes: ",selectedClasses)

            response=getAllClasses(destSandboxHeaders)
            response=json.loads(response.text) 

            destClassesList=[]
            for i in response['results']:
                #print("Destination Class: ", response)
                destClassesList.append(i['title'])
            
            selectedClasses,duplicateClasses=checkDuplicateItems(selectedClasses,destClassesList)
            
            if len(duplicateClasses)>1:
                #print("These Classes are already present in Destination Sandbox: ",duplicateClasses, "\nDeploying other Field Groups: ",selectedClasst)
                flash("These Classes are already present in Destination Sandbox:" +str(duplicateClasses))
                flash("\nDeploying other Classes: " + str(selectedClasses))
            elif len(duplicateClasses)==1 and len(selectedClasses)==0:
                #print("This Class is already present in Destination Sandbox: ",duplicateClasses)
                flash("This Class is already present in Destination Sandbox:" +str(duplicateClasses))
            else:
                pass
     
            for classes in selectedClasses:
                classesId=classesDict[classes]
                response=getClassesById(sourceSandboxHeaders,classesId)
                # Replace response.text Tenant ID...
                responseStr = response.text
                responseStr = responseStr.replace(sourceTenantId, destinationTenantId)
                response=json.loads(responseStr)
                #print(response)

                file_path = join(dirname(__file__).replace("\\","/"),"ClassesResponses")+ classes + ".json"

                saveResponseFile(file_path,classes,response)
                
                response=postClasses(destSandboxHeaders,file_path)
                response=json.loads(response.text)  #*****do we need response???? (No - ABNS)*******
                message=classes + " deployed in Destination Sandbox - " + destSandboxHeaders['x-sandbox-name']
                flash(message)
                
        return render_template('classes.html',classesList=sourceClassesList)

    except Exception as e:
	        return(str(e))


@app.route('/fieldgroup', methods=['GET','POST'])
def fieldgroupname():
    global fieldGroupDict
    global sourceSandboxHeaders
    global destSandboxHeaders
    global sourceTenantId
    global destinationTenantId
    try:
        if request.method=="GET":
            response=getAllMixins(sourceSandboxHeaders)
            response_json = json.loads(response) 
            fieldGroupDict ={}

            for i in response_json['results']:
                fieldGroupDict[i['title']]=i['meta:altId']

        sourceFieldGroupList=list(fieldGroupDict.keys())
        print("\nSource Field Group List: ",sourceFieldGroupList)  
        
        if request.method=="POST":

            selectedFieldGroup=[]
            selectedFieldGroup=request.form.getlist("sourceFieldGroupCheckBox")
            print("\nSelected FieldGroups: ",selectedFieldGroup)

            response=getAllMixins(destSandboxHeaders)
            response_json = json.loads(response)

            destFieldGroupList=[]
            for i in response_json['results']:
                destFieldGroupList.append(i['title'])
            
            selectedFieldGroup,duplicateFieldGroups=checkDuplicateItems(selectedFieldGroup,destFieldGroupList)
            
            if len(duplicateFieldGroups)>1:
                #print("These Field Groups are already present in Destination Sandbox: ",duplicateFieldGroups, "\nDeploying other Field Groups: ",selectedFieldGroup)
                flash("These Field Groups are already present in Destination Sandbox:" +str(duplicateFieldGroups))
                flash("\nDeploying other Field Groups: " + str(selectedFieldGroup))
            elif len(duplicateFieldGroups)==1 and len(selectedFieldGroup)==0:
                #print("This Field Group is already present in Destination Sandbox: ",duplicateFieldGroups)
                flash("This Field Group is already present in Destination Sandbox:" +str(duplicateFieldGroups))
            else:
                pass
     
            for fieldgroup in selectedFieldGroup:
                fieldGroupId=fieldGroupDict[fieldgroup]
                response=getMixinById(sourceSandboxHeaders,fieldGroupId)
                # Replace response.text Tenant ID...
                responseStr = response.text
                responseStr = responseStr.replace(sourceTenantId, destinationTenantId)
                response=json.loads(responseStr)
                #print(response)

                file_path = join(dirname(__file__).replace("\\","/"),"FieldGroupResponses/")+ fieldgroup + ".json"

                saveResponseFile(file_path,fieldgroup,response)
                
                response=postMixin(destSandboxHeaders,file_path)
                response=json.loads(response.text)  #*****do we need response???? (No - ABNS)*******
                message=fieldgroup + " deployed in Destination Sandbox - " + destSandboxHeaders['x-sandbox-name']
                flash(message)
                
        return render_template('fieldgroup.html',fieldGroupList=sourceFieldGroupList)

    except Exception as e:
	        return(str(e))

@app.route('/schema', methods=['GET','POST'])
def schemaname():
    global schemaDict
    global sourceSandboxHeaders
    global destSandboxHeaders
    global sourceTenantId
    global destinationTenantId
    
    try:
        if request.method=="GET":
            response=getAllSchemas(sourceSandboxHeaders)
            response_json = json.loads(response)
            schemaDict ={}
            for i in response_json['results']:
                schemaDict[i['title']]=i['meta:altId']

        sourceSchemaList=list(schemaDict.keys())
        #print("\nSource Schema List: ",sourceSchemaList)  

        if request.method=="POST":
            selectedSchema=[]
            selectedSchema=request.form.getlist("sourceSchemaCheckBox")
            print("\nSelected Schema: ",selectedSchema)

            response=getAllSchemas(destSandboxHeaders)
            response_json = json.loads(response)

            destSchemaList=[]
            for i in response_json['results']:
                destSchemaList.append(i['title'])
                    
            selectedSchema,duplicateSchema=checkDuplicateItems(selectedSchema,destSchemaList)

            if len(duplicateSchema)>1:
                print("These Schemas are already present in Destination Sandbox: ",duplicateSchema, "\nDeploying other Field Groups: ",selectedSchema)
                flash("These Schemas are already present in Destination Sandbox:" +str(duplicateSchema))
                flash("\nDeploying other Schemas: " + str(selectedSchema))
            elif len(duplicateSchema)==1 and len(selectedSchema)==0:
                print("This Schema is already present in Destination Sandbox: ",duplicateSchema)
                flash("This Schema is already present in Destination Sandbox:" +str(duplicateSchema))
            else:
                pass
        
            for schema in selectedSchema:
                schemaId=schemaDict[schema]
                response=getSchemaById(sourceSandboxHeaders,schemaId)
                # Replace Tenant ID in response.text...
                responseStr = response.text
                responseStr = responseStr.replace(sourceTenantId, destinationTenantId)
                response=json.loads(responseStr)
                print(type(response))
                if "meta:immutableTags" in response.keys():
                    noProfile=response.pop("meta:immutableTags")
                print("Response Str: ", response)
                schema_file_path = join(dirname(__file__).replace("\\","/"),"SchemaResponses/")+ schema + ".json"

                saveResponseFile(schema_file_path,schema,response) #saving schema response

                #*****Extract Mixin/Field Group Id from schemas********
                schemaMixinId=[]
                for i in response['allOf']:
                    x=i['$ref'].split("mixins/")[-1]
                    if len(x)<len(i['$ref']) and x.isalnum():
                        mixinIdPath="_"+sourceTenantId+".mixins."+x
                        schemaMixinId.append(mixinIdPath)
                    else:
                        continue
                print("Schema Mixin Ids: ", str(schemaMixinId))

                #*****Getting Mixin/Field Group Title********
                schemaSpecificFieldGroups={}
                for mixinid in schemaMixinId:
                    response=getMixinById(sourceSandboxHeaders,mixinid)
                    response=json.loads(response.text) 
                    #for i in response_json['results']:
                    schemaSpecificFieldGroups[response['title']]=response['meta:altId']
                print("Checking mixin ids in destination")

                
                schemaFieldGroups=list(schemaSpecificFieldGroups.keys())
                
                response=getAllMixins(destSandboxHeaders)
                response_json = json.loads(response)

                destFieldGroupList=[]
                for i in response_json['results']:
                    destFieldGroupList.append(i['title'])
                
                missingFieldGroups,presentFieldGroups=checkDuplicateItems(schemaFieldGroups,destFieldGroupList)

                if len(missingFieldGroups)>0:
                    print("\nField Groups present in destination: ",presentFieldGroups,"\nMissing Field Groups: ", missingFieldGroups)
                    for fieldgroup in missingFieldGroups:
                        fieldGroupId=schemaSpecificFieldGroups[fieldgroup]
                        response=getMixinById(sourceSandboxHeaders,fieldGroupId)
                        #response=json.loads(response.text)

                        responseStr = response.text
                        responseStr = responseStr.replace(sourceTenantId, destinationTenantId)
                        response=json.loads(responseStr)

                        file_path = join(dirname(__file__).replace("\\","/"),"FieldGroupResponses/")+ fieldgroup + ".json"

                        saveResponseFile(file_path,fieldgroup,response)
                        
                        response=postMixin(destSandboxHeaders,file_path)
                        response=json.loads(response.text)  #*****do we need response????*******
                        print(fieldgroup + " deployed in Destination Sandbox - " + destSandboxHeaders['x-sandbox-name'])
                
                response=postSchema(destSandboxHeaders,schema_file_path)
                response=json.loads(response.text)  #*****do we need response????*******
                #message=schema + " deployed in Destination Sandbox - " + destSandboxHeaders['x-sandbox-name']
                #flash(message)

                response=getSchemaExport(sourceSandboxHeaders,schemaId)
                #response=json.loads(response.text)
                # Replace response.text Tenant ID...
                responseStr = response.text
                responseStr = responseStr.replace(sourceTenantId, destinationTenantId)
                response=json.loads(responseStr)

                file_path = join(dirname(__file__).replace("\\","/"),"ExportResponses/")+ schema + ".json"
                saveResponseFile(file_path,schema,response) #saving schema response

                response=open(file_path)
                response = json.load(response)
                copied_response=response.copy()

                for i in response:
                    index= response.index(i)
                    if i["meta:resourceType"]== "mixins" or i["meta:resourceType"]== "schemas":
                        copied_response.pop(index)
                    response=copied_response.copy()
                print("\n\nJson File: ", copied_response)

                payload_file = open(file_path, "w")
                json.dump(copied_response, payload_file,indent=4)
                payload_file.close()
                
                response=postSchemaExport(destSandboxHeaders,file_path)
                response=json.loads(response.text)  #*****do we need response????*******
                message=schema + " deployed in Destination Sandbox - " + destSandboxHeaders['x-sandbox-name']
                flash(message)

                # response=postSchema(destSandboxHeaders,file_path)
                # response=json.loads(response.text)  #*****do we need response????*******
                # message=schema + " deployed in Destination Sandbox - " + destSandboxHeaders['x-sandbox-name']
                # flash(message)


        return render_template('schema.html',schemaList=sourceSchemaList)
    except Exception as e:
	        return(str(e))

@app.route('/dataset', methods=['GET','POST'])
def datasetname():
    global sourceSandboxHeaders
    global destSandboxHeaders
    global sourceTenantId
    global destinationTenantId
    global datasetDict
    global schemaDict
    
    try:
        if request.method=="GET":
            response=getAllDatasets(sourceSandboxHeaders)
            response=json.loads(response.text) 
            #print(response)

            file_path = join(dirname(__file__).replace("\\","/"),"DatasetResponses/")+"all.json"
            saveResponseFile(file_path,"All Dataset",response) #saving dataset response

            for i in response:
                #print(i)
                #datasetDict[i]['name']=[i]['id']
                datasetDict[response[i]['name']]=i
            print(datasetDict)
        sourceDatasetList=list(datasetDict.keys())
        # print("\nSource Field Group List: ",sourceFieldGroupList)  
        
        if request.method=="POST":

            selectedDataset=[]
            selectedDataset=request.form.getlist("sourceDatasetCheckBox")
            print("\nSelected Dataset: ",selectedDataset)

            response=getAllDatasets(destSandboxHeaders)
            response=json.loads(response.text) 

            destDatasetList=[]

            for i in response:
                destDatasetList.append(response[i]['name'])
                    
            selectedDataset,duplicateDataset=checkDuplicateItems(selectedDataset,destDatasetList)

            if len(duplicateDataset)>1:
                print("These Dataset are already present in Destination Sandbox: ",duplicateDataset, "\nDeploying other Field Groups: ",selectedDataset)
                flash("These Dataset are already present in Destination Sandbox:" +str(duplicateDataset))
                flash("\nDeploying other Datasets: " + str(selectedDataset))
            elif len(duplicateDataset)==1 and len(selectedDataset)==0:
                print("This Dataset is already present in Destination Sandbox: ",duplicateDataset)
                flash("This Dataset is already present in Destination Sandbox:" +str(duplicateDataset))
            else:
                pass

            for dataset in selectedDataset:
                datasetId=datasetDict[dataset]
                response=getDatasetById(sourceSandboxHeaders,datasetId)
                #response=json.loads(response.text)
                                # Replace response.text Tenant ID...
                responseStr = response.text
                responseStr = responseStr.replace(sourceTenantId, destinationTenantId)
                response=json.loads(responseStr)

                file_path = join(dirname(__file__).replace("\\","/"),"DatasetResponses/")+ dataset + ".json"

                saveResponseFile(file_path,dataset,response) #saving dataset response
                
                response=open(file_path)
                response = json.load(response)
                json_file={}
                json_file['name']=dataset
                for i in response:
                    json_file['schemaRef']=response[i]['schemaRef']
                    json_file['fileDescription']=response[i]['fileDescription']
                print(json_file)

                payload_file = open(file_path, "w")
                json.dump(json_file, payload_file)
                payload_file.close()
                
                sid=response[i]['schemaRef']['id'].split("schemas/")[-1]
                print("Schema Id: ", str(sid))
                schemaId="_"+sourceTenantId+".schemas."+sid
                print("Schema Id: ", schemaId, "\n")

                response=getSchemaById(sourceSandboxHeaders,schemaId)
                response=json.loads(response.text) 
                print("Source Schema Response for name/tile: ",response)
                list1=[]
                schemaTitle=response['title']
                list1.append(schemaTitle)
                print(list1)
                
                #****Checking destination for schema without function because of 403/404 error will exit from checkresponsecode function
                url = "https://platform.adobe.io/data/foundation/schemaregistry/tenant/schemas/"+schemaId
                payload={}
                destSandboxHeaders['Accept']='application/vnd.adobe.xed-id+json;version=1'
                response = requests.request("GET", url, headers=destSandboxHeaders, data=payload)
                
                response=json.loads(response.text)
                
                if response['type']=='object':
                    #print("schema present condition")
                    response=postDataset(destSandboxHeaders,file_path)
                    message=dataset +" is deployed in destination system - "+destSandboxHeaders['x-sandbox-name']
                    flash(message)

                #elif (response['status']==403 or response['status']==404):
                elif (response['type']=='http://ns.adobe.com/aep/errors/XDM-1010-404' or response['status']==403):
                    #print("in if condition")
                    flash("Schema associated with dataset is not present in destination system")
                    flash("Redirecting to Schema page")
                    schemaDict={}
                    schemaDict[schemaTitle]=schemaId
                    return render_template("schema.html",schemaList=list1)

        return render_template('dataset.html',datasetList=sourceDatasetList)
    except Exception as e:
	    return(str(e))

@app.route('/segment', methods=['GET','POST'])
def segmentname():
    global segmentDict
    global sourceSandboxHeaders
    global destSandboxHeaders
    global sourceTenantId
    global destinationTenantId

    if request.method == "GET":
        try:
            response = getAllSegments(sourceSandboxHeaders)
            response = json.loads(response.text)
            for i in response['segments']:
                segmentDict[i['name']] = i['id']

            sourceSegmentsList = list(segmentDict.keys())
            print("\nSource Segments List: ", sourceSegmentsList)

            return render_template('segment.html', segmentList=sourceSegmentsList)

        except Exception as e:
            print(str(e))
            return str(e)

    elif request.method == "POST":
        try:
            selectedSegment = request.form.getlist("sourceSegmentCheckBox")
            print("\nSelected Segments: ", selectedSegment)

            response = getAllSegments(destSandboxHeaders)
            response = json.loads(response.text)

            destSegmentList = []
            for i in response['segments']:
                destSegmentList.append(i['name'])

            selectedSegment, duplicateSegments = checkDuplicateItems(selectedSegment, destSegmentList)

            if len(duplicateSegments) >= 1 and len(selectedSegment) != 0:
                flash("These Segments are already present in Destination Sandbox: " + str(duplicateSegments))
                flash("\nDeploying Segments: " + str(selectedSegment))
            elif len(duplicateSegments) == 1 and len(selectedSegment) == 0:
                flash("This Segment is already present in the Destination Sandbox: " + str(duplicateSegments))
            else:
                pass

            for segment in selectedSegment:
                segmentId = segmentDict[segment]
                response = getSegmentById(sourceSandboxHeaders, segmentId)
                responseStr = response.text
                responseStr = responseStr.replace(sourceTenantId, destinationTenantId)
                response = json.loads(responseStr)

                file_path = join(dirname(__file__).replace("\\", "/"), "SegmentResponses/") + segment + ".json"
                saveResponseFile(file_path, segment, response)

                response = open(file_path)
                response = json.load(response)
                json_file = response.copy()
                json_file.pop('mergePolicyId')

                payload_file = open(file_path, "w")
                json.dump(json_file, payload_file, indent=4)
                payload_file.close()

                response = postSegment(destSandboxHeaders, file_path)
                response = json.loads(response.text)
                message = segment + " deployed in Destination Sandbox - " + destSandboxHeaders['x-sandbox-name']
                flash(message)

            return redirect(url_for('segmentname'))

        except Exception as e:
            print(str(e))
            return str(e)

    else:
        return "Method not allowed" 


if __name__ =="__main__":
    app.run(debug=True, port=7373)