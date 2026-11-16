import requests
from requests.structures import CaseInsensitiveDict

url = "https://toontownrealms.com/api/serverlist/heartbeat"

headers = CaseInsensitiveDict()
headers["Content-Type"] = "application/json"
headers["Authorization"] = "Bearer 6yxE17sTPbs3SPL4zXmpcPJwfw7gNvqhNMs"

data = """
{
 "Name": "REALM!", 
 "Address": "68.116.161.182",
 "Port": 7198, 
 "Icon": "https://toontownrealms.com/images/favicon.png",
 "Description": "A Toontown Realms Realm.",
 "PopulationOnline": 0, 
 "PopulationMax": 16,
 "Timezone": "US/Pacific",
 "ExperienceMultiplier": 1.0,
 "LegitMode": 0, 
 "NerfsMode": 0,
 "DefaultMaxToon": 0
}
 
"""


resp = requests.post(url, headers=headers, data=data, verify=False)

print(resp.content)
