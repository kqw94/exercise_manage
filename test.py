import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

# 测试批量更新接口
def test_bulk_update():
    url = f"{BASE_URL}/timu/bulk-update/"
    headers = {"Content-Type": "application/json"}
    
    # 测试数据：假设这些 exercise_ids 存在于你的数据库中
    payload = {
        "exercise_ids": ["0", "1"],  # 替换为实际存在的 ID
        "exam_group": 1,                 # 替换为有效的 exam_group ID
        "level": 1,
        "score": 2
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    print("Bulk Update Test:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # 检查是否成功
    if response.status_code == 200:
        print("Bulk update successful")
    else:
        print("Bulk update failed")

# 测试练习列表接口（带排序）
def test_exercise_list_with_sorting():
    url = f"{BASE_URL}/exercises/"
    
    # 测试用例
    test_cases = [
        {"order_by": "id", "order_direction": "asc"},           # 按 ID 升序
        {"order_by": "level", "order_direction": "desc"},       # 按 level 降序
        {"order_by": "score", "order_direction": "asc"},        # 按 score 升序
        {"order_by": "exam.exercise_number", "order_direction": "desc"}  # 按 exam.exercise_number 降序
    ]
    
    for params in test_cases:
        response = requests.get(url, params=params)
        
        print(f"\nExercise List Test - Sorting by {params['order_by']} {params['order_direction']}:")
        print(f"Status Code: {response.status_code}")
        # print(f"Response: {response.json()}")
        
        # 检查是否成功并返回数据
        if response.status_code == 200 and response.json().get('results'):
            print("Sorting test successful")
            # 检查返回的数据是否按预期排序（简单验证前两个结果）
            results = response.json()['results']
            if len(results) > 1:
                if params['order_by'] == 'id':
                    key = 'exercise_id'
                else:
                    key = params['order_by']
                
                if params['order_direction'] == 'asc':
                    assert results[0][key] <= results[1][key], f"Sorting failed for {key} asc"
                else:
                    assert results[0][key] >= results[1][key], f"Sorting failed for {key} desc"
                print(f"Verified sorting order for {key}")
        else:
            print("Sorting test failed or no results returned")

# 运行测试
if __name__ == "__main__":
    print("Starting backend API tests...\n")
    
    # 测试批量更新
    # test_bulk_update()
    
    # 测试排序功能
    test_exercise_list_with_sorting()