import requests

# 注册接口URL
# url = "http://127.0.0.1:8000/api/register/"
# url = "http://127.0.0.1:8000/api/login/"
url = "http://127.0.0.1:8000/api/role-permissions/"

headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQzOTAzNTkxLCJpYXQiOjE3NDM5MDMyOTEsImp0aSI6ImY4ZGQ3ZDhlZDZiNTRjOTNhMDBkMWUyMWQ3ZTM1ZTUyIiwidXNlcl9pZCI6MX0.ZrdEhxJgkFxlUjKmqU7g1HP6E8TS6kvW5MzoDUgZsEo",
    "Content-Type": "application/json"
}


# 请求数据
payload = {
    "role": "student",
    "model_name": "Exercise",
    "can_create": False,
    "can_read": True,
    "can_update": False,
    "can_delete": False
}

try:
    # 发送POST请求（JSON格式）
    response = requests.post(
        url,
        json=payload,  # 自动设置 Content-Type: application/json
        headers=headers,
        timeout=10     # 超时设置（秒）
    )

    # 检查响应状态码
    if response.status_code == 200:
        print("请求成功！响应数据：", response.json()['access'])
    else:
        print(f"请求失败！状态码：{response.status_code}, 错误信息：{response.text}")

except requests.exceptions.RequestException as e:
    print(f"请求异常：{str(e)}")

