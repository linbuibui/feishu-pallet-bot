# -*- coding: utf-8 -*-
import json

def application(environ, start_response):
    method = environ.get('REQUEST_METHOD', 'GET')
    
    if method == 'GET':
        body = b'{"status":"ok"}'
        start_response('200 OK', [
            ('Content-Type', 'application/json'),
            ('Content-Length', str(len(body)))
        ])
        return [body]
    
    content_length = int(environ.get('CONTENT_LENGTH', 0))
    body = environ['wsgi.input'].read(content_length) if content_length > 0 else b''
    
    try:
        data = json.loads(body.decode('utf-8        data = {}
    
    if data'))
    except:
.get('type') == 'url_verification':
        response = json.dumps({"challenge": data.get("challenge")}).encode('utf-8')
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [response]
    
    response = json.dumps({"code": 0}).encode('utf-8')
    start_response('200 OK', [('Content-Type', 'application/json')])
    return [response]
