import requests
import json

# --- 配置 ---
# 请根据您的服务实际运行地址和端口进行修改
BASE_URL = "http://localhost:8080/api/dashboard"
HEADERS = {
    "Content-Type": "application/json"
    # 如果你的接口需要token认证，在这里添加
    # "token": "your_auth_token_here"
}

# 用于统计测试结果
test_results = {"passed": 0, "failed": 0}


def run_test(test_name, endpoint, params=None):
    """
    一个通用的测试执行函数
    :param test_name: 测试用例的名称
    :param endpoint: API的路径 (例如: /stats/vehicle-status)
    :param params: GET请求的查询参数 (字典)
    """
    full_url = f"{BASE_URL}{endpoint}"
    print(f"🚀 [正在运行] {test_name}")
    print(f"   - URL: {full_url}")
    if params:
        print(f"   - Params: {params}")

    try:
        # 发起GET请求
        response = requests.get(full_url, params=params, headers=HEADERS, timeout=10)  # 10秒超时

        # 1. 检查HTTP状态码
        if response.status_code == 200:
            print(f"   - HTTP状态码: {response.status_code} (OK)")

            # 2. 尝试解析JSON
            try:
                data = response.json()

                # 3. 检查业务响应码 (根据您的Result.success()定义)
                #    通常成功的响应会有一个code字段，这里假设成功的code是1
                if 'code' in data and data['code'] == 1:
                    print(f"✅ [通过] {test_name}")

                    # --- 主要修改点在这里 ---
                    # 打印完整的、格式化后的JSON响应
                    print("   - 接口响应输出:")
                    # 使用 json.dumps 进行格式化打印，方便阅读
                    # indent=2 表示缩进2个空格
                    # ensure_ascii=False 确保中文等非ASCII字符能正常显示
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    # -------------------------

                    test_results["passed"] += 1
                else:
                    print(f"❌ [失败] {test_name} - 业务响应码不正确或缺少'code'字段。")
                    print(f"   - 响应内容: {data}")
                    test_results["failed"] += 1
            except json.JSONDecodeError:
                print(f"❌ [失败] {test_name} - 无法解析响应为JSON格式。")
                print(f"   - 响应内容: {response.text}")
                test_results["failed"] += 1
        else:
            print(f"❌ [失败] {test_name} - HTTP状态码不是200。")
            print(f"   - 实际状态码: {response.status_code}")
            print(f"   - 响应内容: {response.text}")
            test_results["failed"] += 1

    except requests.exceptions.RequestException as e:
        print(f"❌ [失败] {test_name} - 请求时发生网络错误。")
        print(f"   - 错误: {e}")
        test_results["failed"] += 1

    print("-" * 50)


# --- 测试用例定义 (保持不变) ---

def test_get_vehicle_status_stats():
    run_test("获取车辆状态分层数据", "/stats/vehicle-status")


def test_get_region_risk_distribution():
    run_test("获取区域风险分布数据", "/distribution/region-risks")


def test_get_health_assessment():
    # 尽管已弃用，但仍可测试接口是否能正常响应
    run_test("获取健康度评估数据 (已弃用)", "/stats/health-assessment")


def test_get_usage_intensity():
    run_test("获取车辆使用强度数据", "/kpis/usage-intensity")


def test_get_brand_distribution():
    run_test("获取车辆品牌分布数据", "/distribution/brands")


def test_get_charge_behavior():
    run_test("获取充电行为统计数据", "/stats/charge-behavior")


def test_get_charge_health_kpis():
    run_test("获取充电健康度指标数据", "/kpis/charge-health")


def test_get_charge_cycle_trend():
    run_test("获取充放电循环数据", "/trends/charge-cycles")


def test_get_core_kpis():
    run_test("获取核心KPI数据", "/kpis/summary")


def test_get_vehicle_distribution():
    # 测试不带参数的情况
    run_test("获取车辆地理分布数据 (无状态参数)", "/distribution/vehicles")
    # 测试带可选参数的情况
    run_test("获取车辆地理分布数据 (带状态参数)", "/distribution/vehicles", params={"status": "online"})


def test_get_fault_vehicle_charge_cycle_trend():
    # 测试带必需参数的情况
    run_test("获取故障车辆充放电循环趋势", "/trends/fault-vehicle-charge-cycles", params={"days": 30})


def test_get_vehicle_model_distribution():
    run_test("获取车型分布数据", "/distribution/vehicle-models")


def test_get_ranking():
    # 测试带必需参数的情况，请根据实际业务提供有效的 dimension 和 metric
    params = {
        "dimension": "region",  # 示例值
        "metric": "health"  # 示例值
    }
    run_test("获取动态排名数据", "/ranking", params=params)


# --- 主程序入口 (保持不变) ---
if __name__ == "__main__":
    print("========= 开始执行 Dashboard API 测试 =========")

    # 按顺序执行所有测试用例
    test_get_vehicle_status_stats()
    test_get_region_risk_distribution()
    test_get_health_assessment()
    test_get_usage_intensity()
    test_get_brand_distribution()
    test_get_charge_behavior()
    test_get_charge_health_kpis()
    test_get_charge_cycle_trend()
    test_get_core_kpis()
    test_get_vehicle_distribution()
    test_get_fault_vehicle_charge_cycle_trend()
    test_get_vehicle_model_distribution()
    test_get_ranking()

    print("========= 所有测试执行完毕 =========")
    print(f"测试结果统计:")
    print(f"  ✅ 通过: {test_results['passed']}")
    print(f"  ❌ 失败: {test_results['failed']}")
    print("=" * 36)