from flask import Flask, render_template, request, jsonify
import json
import execjs
import os
from urllib.parse import quote
import requests
import schedule
import time
from datetime import datetime
import threading
import queue
import logging
import uuid
import sys
import webbrowser


# 获取正确的资源路径
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


app = Flask(__name__)

# 全局变量
running_task = None
log_queue = queue.Queue()
stop_flag = False
# 全局变量
running_tasks = {}  # 使用字典存储多个任务
log_queues = {}  # 每个任务一个日志队列
task_schedulers = {}  # 为每个任务创建独立的调度器

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put({
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': self.format(record)
        })


# JS编译
js_path = resource_path('sign.js')
with open(js_path, 'r', encoding='utf-8') as f:
    js_code = f.read()
ctx = execjs.compile(js_code)


def get_task_logger(task_id):
    if task_id not in log_queues:
        log_queues[task_id] = queue.Queue()
    task_logger = logging.getLogger(f'task_{task_id}')
    if not task_logger.handlers:
        task_logger.addHandler(QueueHandler(log_queues[task_id]))
    return task_logger


def get_sign_code(openid, lat="", lon=""):
    try:
        result = ctx.call("getCode", openid, lat, lon)
        return quote(result)
    except Exception as e:
        logger.error(f"执行JS脚本出错: {e}")
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
        logger.error(f"请求失败: {e}")
        return None


def try_get_number(config, task_id):
    logger = get_task_logger(task_id)
    max_attempts = int(config['max_attempts'])
    current_attempt = 0

    logger.info(f"开始抢号 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    while current_attempt < max_attempts and not running_tasks[task_id]['stop_flag']:
        current_attempt += 1
        logger.info(f"第 {current_attempt} 次尝试")

        result = startPickingNumbers(
            config['openid'],
            config['keyword'],
            config['xingming'],
            config['tname'],
            config['lat'],
            config['lon']
        )

        if result is None:
            logger.info("请求失败，等待5秒后重试...")
            time.sleep(3)
            continue

        logger.info(f"返回结果: {result}")

        if result.get('id', 0) > 0 and result.get('no', '') != '':
            logger.info(f"抢号成功! - 您的排队码是: {result['no']}")
            return

        time.sleep(3)

    logger.info(f"达到最大尝试次数 {max_attempts}，停止抢号")


def schedule_task(config, task_id):
    logger = get_task_logger(task_id)

    # 为每个任务创建独立的调度器
    task_scheduler = schedule.Scheduler()
    task_schedulers[task_id] = task_scheduler

    # 使用任务特定的调度器
    task_scheduler.every().day.at(config['start_time']).do(try_get_number, config, task_id)

    logger.info("定时任务已启动，等待执行...")

    try:
        while task_id in running_tasks and not running_tasks[task_id]['stop_flag']:
            # 使用任务特定的调度器运行待处理的任务
            task_scheduler.run_pending()
            time.sleep(1)
    except Exception as e:
        logger.error(f"任务执行出错: {str(e)}")
    finally:
        # 清理任务特定的调度器
        if task_id in task_schedulers:
            del task_schedulers[task_id]
        logger.info("任务已停止")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/start', methods=['POST'])
def start_task():
    config = request.json
    task_id = str(uuid.uuid4())

    # 先创建任务信息
    running_tasks[task_id] = {
        'config': config,
        'stop_flag': False,
        'thread': None
    }

    try:
        thread = threading.Thread(
            target=schedule_task,
            args=(config, task_id)
        )
        thread.daemon = True  # 设置为守护线程
        running_tasks[task_id]['thread'] = thread
        thread.start()

        return jsonify({
            'status': 'success',
            'message': '任务已启动',
            'task_id': task_id
        })
    except Exception as e:
        if task_id in running_tasks:
            del running_tasks[task_id]
        return jsonify({
            'status': 'error',
            'message': f'启动任务失败: {str(e)}'
        })


@app.route('/stop', methods=['POST'])
def stop_task():
    task_id = request.json.get('task_id')
    if task_id in running_tasks:
        running_tasks[task_id]['stop_flag'] = True
        # 等待线程结束后再删除任务信息
        if running_tasks[task_id]['thread']:
            running_tasks[task_id]['thread'].join()
        # 清理相关资源
        if task_id in task_schedulers:
            del task_schedulers[task_id]
        del running_tasks[task_id]
        if task_id in log_queues:
            del log_queues[task_id]
        return jsonify({'status': 'success', 'message': f'任务 {task_id} 已停止'})
    return jsonify({'status': 'error', 'message': '任务不存在'})


@app.route('/get_logs')
def get_logs():
    task_id = request.args.get('task_id')
    if task_id not in log_queues:
        return jsonify([])

    logs = []
    while not log_queues[task_id].empty():
        logs.append(log_queues[task_id].get())
    return jsonify(logs)


def open_browser():
    webbrowser.open('http://127.0.0.1:5000')


if __name__ == '__main__':
    # 启动浏览器
    threading.Timer(1.5, open_browser).start()
    # 启动Flask应用
    app.run(debug=False, port=5000)
