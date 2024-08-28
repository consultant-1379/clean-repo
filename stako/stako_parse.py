import pandas as pd
import requests
import json


filename="FOSS_uploaded.xls"
filenameFinal="SoS_Updated_Stako.xls"
data=pd.read_excel(filename)
count = 0

print ("**********************************************")
print ('Total Number of entries:', len(data))
print ('Column Names:', data.columns.values.tolist())
print ("**********************************************")

for i in range(len(data)):
    if data.loc[i, 'SW/License Type'] == 'FOSS':
        #print(f"Row: {i} 'SW/License Type': {data.loc[i, 'SW/License Type']}")
        print(f"Row: {i} '3PP Name': {data.loc[i, '3PP Name']}")
        #print(f"Row: {i} 'Product CAX': {data.loc[i, 'Product CAX']}")

        PrimID=data.loc[i, 'Product CAX']
        #print ("PrimID is:" + str(PrimID))
        new_PrimID = str(PrimID).replace("/", "\/" )
        print ("PrimID is:" + new_PrimID)
        count += 1

        url = 'http://papi.internal.ericsson.com'
        query = 'query={"username":"esiannk","token":"ddc7ba3d","facility":"COMPONENT_QUERY","prim":"' + new_PrimID + '"}'
        stako = None
        try:
            response = requests.get(url, query).json()
            #print(f"response: {response}")
            stako = response.get('stako')
        except (ValueError, KeyError) as err:
            print(f"Something went wrong: {err}")
        if stako is not None:
            print(f"Returned 'stako': {stako}")
            data.loc[i, 'Stako'] = stako

        print ("-----------------------------------------")

print("Number of FOSS: ", count)
print ("-----------------------------------------")
data.to_excel(filenameFinal, index=False)
data2=pd.read_excel(filenameFinal)
print ("-----------------------------------------")
print (f"Data after 'to_excel()':\n{data2}")
