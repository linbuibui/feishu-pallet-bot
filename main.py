# -*- coding: utf-8 -*-
import json
import urllib.request
import urllib.parse

CONFIG = {
    "feishu": {
        "app_id": "cli_a91da3f34b789bb5",
        "app_secret": "U86rraUxgJNHvEE1DVZP9cLPf5NskbGM"
    },
    "bitable": {
        "app_token": "KFohbZvtvak8iBs1AFrc9plPnzS",
        "pallet_table_id": "tbl1B0MLJST4JRWk"
    }
}

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    query_string = environ.get('QUERY_STRING', '')
    
    if method == 'GET':
        params = urllib.parse.parse_qs(query_string)
        challenge = params.get('challenge', [None])[0]
        if challenge:
            body = json.dumps({"challenge": challenge})
        else:
            body = json.dumps({"status": "ok"})
        
        start_response('200 OK', [('Content-Type', 'application/json'), ('Content-Length', str(len(body)))])
        return [body.encode('utf-8')]
    
    if method == 'POST':
        content_length = int(environ.get('CONTENT_LENGTH', 0))
        body = environ['wsgi.input'].read(content_length).decode('utf-8') if content_length > 0 else ''
        
        try:
            data = json.loads(body) if body else {}
        except:
            data = {}
        
        event_type = data.get("type")
        
        if event_type == "url_verification":
            response = json.dumps({"challenge": data.get("challenge")})
            start_response('200 OK', [('Content-Type', 'application/json')])
            return [response.encode('utf-8')]
        
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps({"code": 0}).encode('utf-8')]
    
    start_response('404 Not Found', [('Content-Type', 'application/json')])
    return [json.dumps({"error": "Not found"}).encode('utf-8')]
