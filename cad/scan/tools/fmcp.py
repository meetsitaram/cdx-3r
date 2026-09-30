"""Tiny client for the local Autodesk Fusion MCP server (streamable HTTP, JSON-RPC).
python fmcp.py tools                      -> list tools
python fmcp.py call <tool> <json-args>    -> call a tool
python fmcp.py script <file.py> [readOnly]-> run a Fusion script file via fusion_mcp_execute
"""
import json, sys, urllib.request

URL = 'http://127.0.0.1:27182/mcp'
_sid = None
_id = 0


def rpc(method, params=None, notify=False):
    global _sid, _id
    body = {'jsonrpc': '2.0', 'method': method}
    if params is not None: body['params'] = params
    if not notify:
        _id += 1; body['id'] = _id
    h = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
    if _sid: h['Mcp-Session-Id'] = _sid
    req = urllib.request.Request(URL, json.dumps(body).encode(), h)
    with urllib.request.urlopen(req, timeout=600) as r:
        _sid = r.headers.get('Mcp-Session-Id') or _sid
        txt = r.read().decode('utf-8', 'replace')
    if notify or not txt.strip(): return None
    if txt.lstrip().startswith('{'): return json.loads(txt)
    out = None
    for line in txt.splitlines():                     # SSE: take the last data: message with our id
        if line.startswith('data:'):
            m = json.loads(line[5:])
            if m.get('id') == body.get('id'): out = m
    return out


def connect():
    rpc('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {},
                       'clientInfo': {'name': 'cdx-fmcp', 'version': '0.1'}})
    rpc('notifications/initialized', notify=True)


def call(tool, args):
    r = rpc('tools/call', {'name': tool, 'arguments': args})
    if 'error' in r: return 'ERROR ' + json.dumps(r['error'])
    return '\n'.join(c.get('text', '') for c in r['result'].get('content', []))


if __name__ == '__main__':
    connect()
    if sys.argv[1] == 'tools':
        for t in rpc('tools/list')['result']['tools']:
            print('==', t['name']); print(t.get('description', '')[:1500]); print(json.dumps(t.get('inputSchema'))[:1500])
    elif sys.argv[1] == 'call':
        print(call(sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}))
    elif sys.argv[1] == 'script':
        code = open(sys.argv[2], encoding='utf-8').read()
        args = {'featureType': 'script', 'object': {'script': code}}
        if len(sys.argv) > 3: args['object']['readOnly'] = True
        print(call('fusion_mcp_execute', args))
