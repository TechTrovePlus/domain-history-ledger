import requests

url = "https://urlhaus-api.abuse.ch/v1/host/"
key = "eb5f497a3cbe04aa373a5057e476694fc8f350364027b1d4"

# Try headers
resp1 = requests.post(url, headers={"Auth-Key": key}, data={"host": "google.com"})
print("Header Auth-Key:", resp1.status_code, resp1.text[:100])

resp2 = requests.post(url, headers={"API-Key": key}, data={"host": "google.com"})
print("Header API-Key:", resp2.status_code, resp2.text[:100])

# Try params
resp3 = requests.post(url, params={"auth-key": key}, data={"host": "google.com"})
print("Params auth-key:", resp3.status_code, resp3.text[:100])
