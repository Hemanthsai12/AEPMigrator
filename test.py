import json
file_path="ExportResponses\Eloqua Response.json"
response=open(file_path)
response = json.load(response)
#print(response)
copied_response=response.copy()
for i in response:
    index= response.index(i)
    if i["meta:resourceType"]== "schemas" or i["meta:resourceType"]== "mixins":
        copied_response.pop(index)
    # if i["meta:resourceType"]== "mixins":
    #     copied_response.pop(index)
    response=copied_response.copy()
print("\n\nJson File: ", response)
print("\n\nCopied Response: ", copied_response)
payload_file = open(file_path, "w")
json.dump(response, payload_file,indent=4)
payload_file.close()

response=open(file_path)
response = json.load(response)
print("\n\n File after removing mixins and schemas:", response)
