import requests

session = requests.Session()

# Login
login_data = {
    "rider_id": "GW-8821",
    "password": "rider123"
}
res = session.post("http://127.0.0.1:8000/auth/login", data=login_data)
print("Login status:", res.status_code)
print("Cookies:", session.cookies.get_dict())

# Hit summary
res = session.get("http://127.0.0.1:8000/api/dashboard/summary")
print("Summary status:", res.status_code)
print("Summary text:", res.text)
