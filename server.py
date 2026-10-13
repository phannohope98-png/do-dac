"""First-party analytics receiver. Python 3.11+, no third-party dependencies."""
import json
import os
import re
import sqlite3
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parent
DB = Path(os.environ.get('ANALYTICS_DB', str(ROOT / 'private-data' / 'analytics.sqlite')))
ORIGINS = set(os.environ.get('ANALYTICS_ORIGINS', 'http://127.0.0.1:8790').split(','))
REPORT_ORIGINS = set(os.environ.get('ANALYTICS_REPORT_ORIGINS', 'https://phannohope98-png.github.io').split(','))
RETENTION = max(1, min(365, int(os.environ.get('ANALYTICS_RETENTION_DAYS', '90'))))
TYPES = {'page_view', 'click', 'scroll', 'engagement', 'page_hidden', 'form_submit', 'goal', 'section_view'}

@contextmanager
def connection():
    conn = sqlite3.connect(DB, timeout=15)
    conn.row_factory = sqlite3.Row
    try:
        with conn: yield conn
    finally: conn.close()

def initialize():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with connection() as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, session TEXT NOT NULL, site TEXT NOT NULL, type TEXT NOT NULL, page TEXT NOT NULL, at TEXT NOT NULL, received INTEGER NOT NULL, data TEXT NOT NULL)')
        conn.execute('CREATE INDEX IF NOT EXISTS event_received ON events(received)')
        conn.execute('CREATE INDEX IF NOT EXISTS event_session ON events(session, at)')

def clean_text(value, length=80):
    if not isinstance(value, str): return ''
    return ''.join(ch for ch in value[:length] if ch.isalnum() or ch in '_ .-/').strip()

def clean_path(value):
    if not isinstance(value, str) or not value.startswith('/') or len(value) > 300: raise ValueError('page')
    return value.split('?')[0].split('#')[0]

def validate(event, site):
    if not isinstance(event, dict): raise ValueError('event')
    for field in ('id', 'session'):
        if not re.fullmatch(r'[a-fA-F0-9-]{36}', str(event.get(field, ''))): raise ValueError(field)
    kind = event.get('type')
    if kind not in TYPES: raise ValueError('type')
    page = clean_path(event.get('page'))
    at = datetime.fromisoformat(event.get('at', '').replace('Z', '+00:00'))
    if not at.tzinfo or abs(at.timestamp()-time.time()) > 86400: raise ValueError('time')
    incoming = event.get('data', {})
    if not isinstance(incoming, dict): raise ValueError('data')
    data = {}
    allowed = {'page_view': ['referrer','device','browser','source','medium','campaign'], 'click':['name','target','section','region'], 'section_view':['name','section'], 'goal':['name'], 'form_submit':['name']}
    for field in allowed.get(kind, []): data[field] = clean_text(incoming.get(field, ''), 300 if field in ('referrer','target') else 80)
    if kind in ('section_view','click'):
        for field in ('x','y','viewport'):
            if field in incoming:
                if type(incoming[field]) is not int or not 0 <= incoming[field] <= 10000000: raise ValueError(field)
                data[field] = incoming[field]
    if kind == 'section_view':
        seconds = incoming.get('seconds',0)
        if type(seconds) is not int or not 0 <= seconds <= 60: raise ValueError('seconds')
        data['seconds'] = seconds
        data['final'] = incoming.get('final') is True
    if kind == 'scroll':
        if incoming.get('percent') not in (25,50,75,100): raise ValueError('scroll')
        data['percent'] = incoming['percent']
    if kind == 'engagement':
        seconds = incoming.get('seconds')
        if type(seconds) is not int or not 0 <= seconds <= 60: raise ValueError('seconds')
        data['seconds'] = seconds
    return (event['id'], event['session'], site, kind, page, at.astimezone(timezone.utc).isoformat(), int(time.time()), json.dumps(data, ensure_ascii=False))

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass  # Do not persist visitor IPs or request URLs.

    def respond(self, status, body, content='application/json; charset=utf-8', cors=False):
        raw = body.encode() if isinstance(body,str) else json.dumps(body,ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type',content)
        self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        if cors and self.headers.get('Origin') in (REPORT_ORIGINS if urlparse(self.path).path.startswith('/api/') else ORIGINS):
            self.send_header('Access-Control-Allow-Origin',self.headers['Origin'])
            self.send_header('Vary','Origin')
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        report = urlparse(self.path).path.startswith('/api/')
        if self.headers.get('Origin') not in (REPORT_ORIGINS if report else ORIGINS):
            return self.respond(403, {'error':'origin'})
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin',self.headers['Origin'])
        self.send_header('Access-Control-Allow-Methods','GET, OPTIONS' if report else 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.send_header('Vary','Origin')
        self.end_headers()

    def do_POST(self):
        if urlparse(self.path).path != '/collect': return self.respond(404,{})
        if self.headers.get('Origin') not in ORIGINS: return self.respond(403,{'error':'origin'})
        try:
            size = int(self.headers.get('Content-Length','0'))
            if not 1 <= size <= 32768: return self.respond(413,{'error':'payload'},cors=True)
            payload = json.loads(self.rfile.read(size))
            site = urlparse(self.headers['Origin']).hostname
            if not site or payload.get('site') != site: raise ValueError('site')
            events = payload.get('events')
            if not isinstance(events,list) or not 1 <= len(events) <= 30: raise ValueError('batch')
            rows = [validate(event, site) for event in events]
            with connection() as conn:
                conn.executemany('INSERT OR IGNORE INTO events VALUES(?,?,?,?,?,?,?,?)',rows)
                conn.execute('DELETE FROM events WHERE received < ?', (int(time.time())-RETENTION*86400,))
            return self.respond(200,{'accepted':len(rows)},cors=True)
        except (ValueError, TypeError, AttributeError, KeyError): return self.respond(400,{'error':'invalid event'},cors=True)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == '/health':
            try:
                with connection() as conn: conn.execute('SELECT 1 FROM events LIMIT 1').fetchone()
                return self.respond(200,{'status':'ok'})
            except sqlite3.Error: return self.respond(503,{'status':'database unavailable'})
        if url.path in ('/api/events', '/api/sites'):
            query = parse_qs(url.query)
            try: days = max(1,min(90,int(query.get('days',['7'])[0])))
            except ValueError: return self.respond(400,{'error':'days'},cors=True)
            cutoff = int(time.time())-days*86400
            with connection() as conn:
                if url.path == '/api/sites':
                    rows = conn.execute("SELECT site, COUNT(DISTINCT session) AS sessions, SUM(type='page_view') AS views, SUM(type='click') AS clicks, MAX(at) AS last_seen FROM events WHERE received >= ? GROUP BY site ORDER BY last_seen DESC",(cutoff,)).fetchall()
                    return self.respond(200,{'sites':[dict(row) for row in rows]},cors=True)
                site = query.get('site',[''])[0]
                if not site: return self.respond(400,{'error':'site required'},cors=True)
                rows = conn.execute('SELECT id,session,type,page,at,data FROM events WHERE site = ? AND received >= ? ORDER BY at DESC, rowid DESC LIMIT 50000',(site,cutoff)).fetchall()
            events = [dict(row, data=json.loads(row['data'])) for row in rows]
            return self.respond(200,{'events':events,'limited':len(events)==50000,'site':site},cors=True)
        files = {'/':'dashboard.html','/tracker.js':'tracker.js','/demo':'demo.html','/demo/article':'demo.html', '/index.html':'index.html'}
        filename = files.get(url.path)
        if not filename: return self.respond(404,{'error':'not found'})
        content = 'application/javascript; charset=utf-8' if filename.endswith('.js') else 'text/html; charset=utf-8'
        self.respond(200,(ROOT/filename).read_text(encoding='utf-8'),content)

if __name__ == '__main__':
    initialize()
    print('Analytics: http://127.0.0.1:8790', flush=True)
    bind = os.environ.get('ANALYTICS_BIND','0.0.0.0' if os.environ.get('PORT') else '127.0.0.1')
    port = int(os.environ.get('PORT',os.environ.get('ANALYTICS_PORT','8790')))
    ThreadingHTTPServer((bind,port),Handler).serve_forever()
