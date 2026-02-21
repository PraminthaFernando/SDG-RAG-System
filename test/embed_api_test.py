import requests

url = "https://inadvertently-measureless-ester.ngrok-free.dev/embed"

response = requests.post(
    url,
    json={"texts": ["hello world"]}
)

print(response.status_code)
print(response.text)