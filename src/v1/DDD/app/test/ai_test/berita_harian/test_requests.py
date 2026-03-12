"""
Test with requests library (simpler, different TLS stack)
"""
import requests

headers = {
    "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
    "Accept": "*/*",
    "Host": "www.bharian.com.my",
    "Connection": "keep-alive"
}

url = "https://www.bharian.com.my/berita/"

print(f"Testing with requests library:")
print(f"  URL: {url}")

try:
    resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
    print(f"\nStatus: {resp.status_code}")
    if resp.status_code == 200:
        print(f"SUCCESS! Content length: {len(resp.text)}")
    else:
        print(f"FAILED!")
        print(f"Response headers: {dict(resp.headers)}")
except Exception as e:
    print(f"ERROR: {e}")
