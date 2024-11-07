import json
import execjs
import os
from urllib.parse import quote, unquote, urlencode
import requests
import schedule
import time
from datetime import datetime

# 读取并编译JS文件
js_path = os.path.join(os.path.dirname(__file__), 'sign.js')
with open(js_path, 'r', encoding='utf-8') as f:
    js_code = f.read()

ctx = execjs.compile(js_code)


def get_sign_code(openid, lat="", lon=""):
    try:
        result = ctx.call("getCode", openid, lat, lon)
        return quote(result)
    except Exception as e:
        print(f"执行JS脚本出错: {e}")
        return None


def startPickingNumbers(openid, keyword, xingming="", tname="星辉三楼业务受理区", lat="", lon=""):
    url = "https://paidui.tupianquzi.com/api/index/index"
    headers = {
        "Host": "paidui.tupianquzi.com",
        "Connection": "keep-alive",
        "content-type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip,compress,br,deflate",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.53(0x1800352e) NetType/WIFI Language/zh_CN",
        "Referer": "http"
    }
    code = get_sign_code(openid, lat, lon)
    params = {
        "keyword": keyword,
        "xingming": xingming,
        "zdy": "",
        "zdy1": "",
        "zdy2": "",
        "zdy_name": "",
        "zdy_name1": "",
        "zdy_name2": "",
        "zdy_type": "",
        "zdy_type1": "",
        "zdy_type2": "",
        "xmdes": "姓名",
        "tname": tname,
        "msg": "[0,1,2]"
    }
    encoded_params = quote(json.dumps(params))
    data = f"code={code}&data={encoded_params}"

    try:
        res = requests.post(url, headers=headers, data=data, timeout=30)
        json_data = json.loads(res.text)
        return json_data
    except Exception as e:
        print(f"请求失败: {e}")
        return None


def try_get_number():
    openid = "oq_eI5Q4LQjpLlWN78PbQWlSI8tY"
    keyword = "1g5yr6it"
    xingming = "李"
    lat = "35.012981"
    lon = "118.269783"
    tname = "星辉三楼业务受理区"

    max_attempts = 50
    current_attempt = 0

    print(f"开始抢号 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    while current_attempt < max_attempts:
        current_attempt += 1
        print(f"第 {current_attempt} 次尝试")

        result = startPickingNumbers(openid, keyword, xingming, tname, lat, lon)

        if result is None:
            print("请求失败，等待5秒后重试...")
            time.sleep(5)
            continue

        print(f"返回结果: {result}")

        # 检查isever参数
        if result.get('data', {}).get('isever'):
            print(f"抢号成功! - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return

        # 等待5秒后重试
        time.sleep(5)

    print(f"达到最大尝试次数 {max_attempts}，停止抢号")


def main():
    # 设置每天早上8点执行
    schedule.every().day.at("13:20").do(try_get_number)

    print("定时任务已启动，等待执行...")

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()