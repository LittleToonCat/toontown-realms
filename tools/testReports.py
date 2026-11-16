import requests
from requests.structures import CaseInsensitiveDict

url = "https://new.toontownrealms.com/api/reports/new"

headers = CaseInsensitiveDict()
headers["Content-Type"] = "application/json"

data = """
{
  "reporterId": 100018841,
  "reporterName": "Sir Wacky Sillyguy",
  "timestamp": "2-14-2023 6:30PM EST",
  "category": "MODERATION_BAD_NAME",
  "reportDescription": "this name is offensive and inappropriate",
  "reportedId": 100045551,
  "reportedName": "Professor Inappropriatenamington"
}
"""


resp = requests.post(url, headers=headers, data=data, verify=False)

print(resp.status_code)

