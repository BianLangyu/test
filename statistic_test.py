import requests
import json
import time
from tabulate import tabulate
import sys

# ================= 配置区域 =================
BASE_URL = "http://localhost:8080/api/statistics"

# 测试参数 (请根据数据库实际情况修改)
CONFIG = {
    "carSeries": "ALL",
    "start": "2023-10-01",
    "end": "2023-11-01",
    "vin_keyword": "L",  # 用于搜索的VIN关键字
    "multi_series": "深蓝SL03,阿维塔11",
    "days": 30
}


# ===========================================

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class APITester:
    def __init__(self):
        self.results = []

    def log(self, msg, color=Colors.ENDC):
        print(f"{color}{msg}{Colors.ENDC}")

    def validate_keys(self, data, expected_keys):
        """递归或单层验证 keys 是否存在"""
        if not expected_keys:
            return True, ""

        if isinstance(data, list):
            if not data: return True, "Empty list returned (Warning)"
            item = data[0]  # 检查列表第一项
        else:
            item = data

        if not isinstance(item, dict):
            # 如果是 List<String> 这种简单类型，跳过 key 检查
            return True, ""

        missing = [key for key in expected_keys if key not in item]
        if missing:
            return False, f"Missing keys: {missing}"
        return True, ""

    def run_request(self, method, endpoint, params=None, desc="", expected_keys=None, is_csv=False):
        url = f"{BASE_URL}{endpoint}"
        start_time = time.time()
        result = {
            "id": len(self.results) + 1,
            "desc": desc,
            "url": endpoint,
            "status": "FAIL",
            "time": 0,
            "note": ""
        }

        print("-" * 80)
        self.log(f"测试 #{result['id']}: {desc}", Colors.HEADER)
        self.log(f"URL: {url}")
        if params: self.log(f"Params: {json.dumps(params, ensure_ascii=False)}")

        try:
            response = requests.request(method, url, params=params, timeout=10)
            duration = (time.time() - start_time) * 1000
            result["time"] = round(duration, 2)

            self.log(f"HTTP Status: {response.status_code}",
                     Colors.OKGREEN if response.status_code == 200 else Colors.FAIL)

            if response.status_code != 200:
                result["note"] = f"HTTP {response.status_code}"
                self.results.append(result)
                return

            # CSV 处理逻辑
            if is_csv:
                content_type = response.headers.get("Content-Type", "")
                self.log(f"Content-Type: {content_type}")
                content = response.content.decode('utf-8')
                if "text/csv" in content_type or "application/csv" in content_type or "," in content:
                    if content.startswith('\ufeff'):
                        self.log("BOM Head detected (Excel safe)", Colors.OKCYAN)

                    lines = content.splitlines()
                    preview = "\n".join(lines[:3])
                    self.log(f"CSV Preview:\n{preview}", Colors.OKBLUE)

                    result["status"] = "PASS"
                else:
                    self.log("Response does not look like CSV", Colors.FAIL)
                    result["note"] = "Invalid Content-Type"

            # JSON 处理逻辑
            else:
                res_json = response.json()

                # 检查业务 Code
                if res_json.get("code") == 1:
                    data = res_json.get("data")

                    # 数据结构校验
                    is_valid, msg = self.validate_keys(data, expected_keys)

                    if is_valid:
                        result["status"] = "PASS"
                        result["note"] = msg  # 可能是 Empty list warning

                        # 数据预览
                        data_str = json.dumps(data, ensure_ascii=False, indent=2)
                        if len(data_str) > 500:
                            data_str = data_str[:500] + "\n... (truncated)"
                        self.log(f"Data Preview:\n{data_str}", Colors.OKBLUE)
                    else:
                        self.log(f"Data Validation Failed: {msg}", Colors.FAIL)
                        result["note"] = "Structure Mismatch"
                else:
                    self.log(f"API Error: {res_json.get('msg')}", Colors.FAIL)
                    result["note"] = res_json.get("msg")

        except Exception as e:
            self.log(f"Exception: {str(e)}", Colors.FAIL)
            result["note"] = "Exception"

        # 打印最终状态
        color = Colors.OKGREEN if result["status"] == "PASS" else Colors.FAIL
        self.log(f"Result: {result['status']} ({result['time']}ms)", color)
        self.results.append(result)

    def print_summary(self):
        print("\n" + "=" * 80)
        print("TEST SUMMARY REPORT")
        print("=" * 80)

        headers = ["ID", "Test Case", "Endpoint", "Status", "Time(ms)", "Note"]
        table_data = [[r["id"], r["desc"], r["url"], r["status"], r["time"], r["note"]] for r in self.results]

        # 着色处理
        for row in table_data:
            if row[3] == "PASS":
                row[3] = f"{Colors.OKGREEN}PASS{Colors.ENDC}"
            else:
                row[3] = f"{Colors.FAIL}FAIL{Colors.ENDC}"

        print(tabulate(table_data, headers=headers, tablefmt="grid"))

        pass_count = sum(1 for r in self.results if r["status"] == "PASS")
        total = len(self.results)
        print(f"\nTotal: {total}, Passed: {pass_count}, Failed: {total - pass_count}")


# ================= 执行测试 =================

tester = APITester()

# 1. Series List
tester.run_request("GET", "/series-list",
                   desc="1.获取车系列表",
                   expected_keys=[])  # 简单列表，不检查key

# 2. Overview
tester.run_request("GET", "/overview",
                   params={"carSeries": CONFIG["carSeries"]},
                   desc="2.获取KPI概览",
                   expected_keys=["monitored_vehicle_count", "normal_ratio"])

# 3. Vehicle Distribution
tester.run_request("GET", "/vehicle-distribution",
                   params={"carSeries": CONFIG["carSeries"]},
                   desc="3.地图数据",
                   expected_keys=["name", "value"])

# 4. Maintenance
tester.run_request("GET", "/maintenance",
                   desc="4.运维统计",
                   expected_keys=["total_push_count"])

# 5. Charge Process
tester.run_request("GET", "/charge-process",
                   params={"carSeries": CONFIG["carSeries"], "start": CONFIG["start"], "end": CONFIG["end"]},
                   desc="5.充放电监控",
                   expected_keys=["chargeDischarge", "overCurrent", "soc"])

# 6. Driving Behavior
tester.run_request("GET", "/driving-behavior",
                   params={"carSeries": CONFIG["carSeries"], "start": CONFIG["start"], "end": CONFIG["end"]},
                   desc="6.驾驶行为监控",
                   expected_keys=["speedDistribution", "energyTrend"])

# 7. Vehicle List (Page 1)
tester.run_request("GET", "/vehicle-list",
                   params={"page": 1, "pageSize": 5, "carSeries": CONFIG["carSeries"]},
                   desc="7.车辆列表(分页)",
                   expected_keys=["total", "records"])

# 8. Export CSV
tester.run_request("GET", "/vehicle-list/export",
                   params={"carSeries": CONFIG["carSeries"]},
                   desc="8.车辆导出(CSV)",
                   is_csv=True)

# 9. Multi-Series Charge Trends
tester.run_request("GET", "/charge-trends/multi-series",
                   params={"series": CONFIG["multi_series"], "days": CONFIG["days"]},
                   desc="9.多车系充电趋势",
                   expected_keys=["date", "model", "fast_charge_count"])

# 10. Multi-Series Driving Trends
tester.run_request("GET", "/driving-trends/multi-series",
                   params={"series": CONFIG["multi_series"], "days": CONFIG["days"]},
                   desc="10.多车系驾驶趋势",
                   expected_keys=["date", "model", "avg_speed"])

# 生成报告
tester.print_summary()