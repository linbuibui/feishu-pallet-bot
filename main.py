# -*- coding: utf-8 -*-
"""
飞书物料托盘管理机器人 - Vercel版本
"""
import json
import re
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional, Dict, List, Any

# 配置文件
CONFIG = {
    "feishu": {
        "app_id": "cli_a91da3f34b789bb5",
        "app_secret": "U86rraUxgJNHvEE1DVZP9cLPf5NskbGM",
        "callback_url": ""
    },
    "bitable": {
        "app_token": "KFohbZvtvak8iBs1AFrc9plPnzS",
        "pallet_table_id": "tbl1B0MLJST4JRWk"
    },
    "approvers": {
        "supervisor": {"name": "车间审核", "phone": "13536596453"},
        "manager": {"name": "QA审核", "phone": "13928031278"},
        "warehouse": {"name": "仓管员", "phone": "15919251046"}
    }
}

def http_request(url: str, method: str = "POST", data: dict = None, headers: dict = None) -> dict:
    req = urllib.request.Request(url, method=method)
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)
    if data:
        json_data = json.dumps(data).encode('utf-8')
        req.add_header('Content-Type', 'application/json')
        req.data = json_data
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = response.read().decode('utf-8')
            return json.loads(result)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return json.loads(error_body)
    except Exception as e:
        return {"code": -1, "msg": str(e)}

class FeishuAPI:
    BASE_URL = "https://open.feishu.cn/open-apis"
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self._token = None
    def get_token(self) -> str:
        if self._token:
            return self._token
        url = f"{self.BASE_URL}/auth/v3/tenant_access_token/internal"
        data = {"app_id": self.app_id, "app_secret": self.app_secret}
        result = http_request(url, "POST", data)
        if result.get("code") == 0:
            self._token = result.get("tenant_access_token")
            return self._token
        raise Exception(f"获取Token失败: {result}")
    def _headers(self) -> dict:
        token = self.get_token()
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    def send_message(self, user_id: str, msg_type: str, content: str) -> dict:
        url = f"{self.BASE_URL}/im/v1/messages?receive_id_type=user_id"
        headers = self._headers()
        data = {"receive_id": user_id, "msg_type": msg_type, "content": content}
        return http_request(url, "POST", data, headers)

feishu_api = FeishuAPI(CONFIG["feishu"]["app_id"], CONFIG["feishu"]["app_secret"])

class BitableService:
    def __init__(self, app_token: str, table_id: str):
        self.app_token = app_token
        self.table_id = table_id
        self.base_url = "https://open.feishu.cn/open-apis/bitable/v1"
    def _headers(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    def search_pallets(self, token: str, material_name: str) -> List[Dict]:
        url = f"{self.base_url}/apps/{self.app_token}/tables/{self.table_id}/records"
        headers = self._headers(token)
        filter_str = f'AND(contains(物料名称,"{material_name}"),equal(托盘状态,"在库"))'
        params = urllib.parse.urlencode({"filter": filter_str, "page_size": 50})
        full_url = f"{url}?{params}"
        result = http_request(full_url, "GET", None, headers)
        if result.get("code") == 0:
            return result.get("data", {}).get("items", [])
        return []

bitable_service = BitableService(CONFIG["bitable"]["app_token"], CONFIG["bitable"]["pallet_table_id"])

def extract_material_name(text: str) -> str:
    patterns = [r"显示.*含有(.+?)的托盘号", r"查找.*含有(.+?)的托盘", r"查询(.+)的托盘", r"帮我找(.+)"]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    match = re.search(r"[\"'](.+?)[\"']", text)
    if match:
        return match.group(1).strip()
    return text.replace("显示", "").replace("托盘号", "").replace("查找", "").strip()

def is_search_request(text: str) -> bool:
    keywords = ["显示", "查找", "托盘号", "查询", "帮我找"]
    return any(k in text for k in keywords)

def is_help_request(text: str) -> bool:
    return "帮助" in text or "help" in text.lower()

def handle_message(user_id: str, text: str) -> str:
    if is_search_request(text):
        material_name = extract_material_name(text)
        if not material_name:
            return "请输入要查询的物料名称，例如：显示物料名称含有V241101批JP-1366片的托盘号给我"
        try:
            token = feishu_api.get_token()
            records = bitable_service.search_pallets(token, material_name)
            if not records:
                return f"未找到物料名称含有\"{material_name}\"的托盘"
            result_text = f"🔍 物料查询结果\n含有物料名称为\"{material_name}\"的托盘如下：\n\n"
            for record in records:
                fields = record.get("fields", {})
                pallet_id = fields.get("托盘号", "")
                status = fields.get("托盘状态", "在库")
                location = fields.get("库位", "")
                material = fields.get("物料名称", "")
                status_emoji = "🟢" if status == "在库" else "🔴"
                result_text += f"托盘号: {pallet_id}\n状态: {status_emoji} {status}\n物料: {material}\n库位: {location}\n---\n"
            return result_text
        except Exception as e:
            return f"查询失败: {str(e)}"
    elif is_help_request(text):
        return """您好！我是物料托盘管理助手，可以帮您：
1️⃣ 查询托盘
   输入格式：显示物料名称含有XXX的托盘号
2️⃣ 查看帮助
   输入：帮助
"""
    return "您好！我可以帮您查询托盘信息。请输入：显示物料名称含有XXX的托盘号"

# Vercel WSGI 入口
def application(environ, start_response):
    """Vercel Python 入口函数 (WSGI格式)"""
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # 解析查询参数
    query_string = environ.get('QUERY_STRING', '')
    params = urllib.parse.parse_qs(query_string)
    
    # 处理GET请求（飞书URL验证）
    if method == 'GET':
        challenge = params.get('challenge', [None])[0]
        if challenge:
            response = {"challenge": challenge}
        else:
            response = {"status": "ok", "service": "飞书物料托盘管理机器人"}
        
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps(response).encode('utf-8')]
    
    # 处理POST请求
    if method == 'POST':
        try:
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            body = environ['wsgi.input'].read(content_length).decode('utf-8') if content_length > 0 else ''
        except:
            body = ''
        
        try:
            data = json.loads(body) if body else {}
        except:
            data = {}
        
        event_type = data.get("type")
        
        # 飞书URL验证
        if event_type == "url_verification":
            response = {"challenge": data.get("challenge")}
            start_response('200 OK', [('Content-Type', 'application/json')])
            return [json.dumps(response).encode('utf-8')]
        
        # 消息事件
        if event_type == "event_callback":
            event_data = data.get("event", {})
            event_type_inner = event_data.get("type")
            
            if event_type_inner == "im.message":
                message = event_data.get("message", {})
                message_type = message.get("message_type")
                
                if message_type == "text":
                    sender = event_data.get("sender", {})
                    user_id = sender.get("sender_id", {}).get("user_id", "")
                    
                    content = json.loads(message.get("content", "{}"))
                    text = content.get("text", "")
                    
                    response_text = handle_message(user_id, text)
                    feishu_api.send_message(user_id, "text", response_text)
        
        response = {"code": 0}
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps(response).encode('utf-8')]
    
    # 默认
    start_response('404 Not Found', [('Content-Type', 'application/json')])
    return [json.dumps({"error": "Not found"}).encode('utf-8')]

# Vercel Serverless Functions 入口 (备用)
def handler(event, context):
    """Vercel Python 入口函数 (Serverless格式)"""
    # 模拟WSGI环境
    environ = {
        'PATH_INFO': event.get('path', '/'),
        'REQUEST_METHOD': event.get('httpMethod', 'GET'),
        'QUERY_STRING': event.get('rawQuery', ''),
        'CONTENT_LENGTH': len(event.get('body', '')) if event.get('body') else 0,
        'wsgi.input': type('obj', (object,), {'read': lambda self, size: event.get('body', '').encode('utf-8')})()
    }
    
    def start_response(status, headers):
        pass
    
    return application(environ, start_response)
