import json
import os
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
import uuid
from datetime import datetime, timezone
from pathlib import Path
import server

class CollectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.testdir = Path(__file__).resolve().parent / ('test-data-'+str(uuid.uuid4()))
        cls.testdir.mkdir()
        server.DB = cls.testdir/'events.sqlite'
        server.initialize()
        cls.http = server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        cls.url = 'http://127.0.0.1:'+str(cls.http.server_port)
        threading.Thread(target=cls.http.serve_forever,daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown(); cls.http.server_close()
        for item in cls.testdir.iterdir(): item.unlink()
        cls.testdir.rmdir()

    def request(self,path,body=None,headers=None):
        req=urllib.request.Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,headers=headers or {})
        try:
            with urllib.request.urlopen(req) as response: return response.status,response.read()
        except urllib.error.HTTPError as e: return e.code,e.read()

    def event(self,**fields):
        event=dict(id=str(uuid.uuid4()),session=str(uuid.uuid4()),type='page_view',page='/article?email=secret',at=datetime.now(timezone.utc).isoformat(),data={'device':'Desktop','password':'secret','email':'secret'})
        event.update(fields);return event

    def test_unauthorized_report(self): self.assertEqual(self.request('/api/events')[0],401)
    def test_origin_rejected(self): self.assertEqual(self.request('/collect',{'site':server.SITE,'events':[self.event()]},{'Origin':'https://evil.example'})[0],403)
    def test_dedupe_and_redaction(self):
        event=self.event();payload={'site':server.SITE,'events':[event,event]}
        self.assertEqual(self.request('/collect',payload,{'Origin':'http://127.0.0.1:8790'})[0],200)
        status,raw=self.request('/api/events',headers={'Authorization':'Bearer '+server.TOKEN})
        self.assertEqual(status,200)
        matches=[e for e in json.loads(raw)['events'] if e['id']==event['id']]
        self.assertEqual(len(matches),1);self.assertEqual(matches[0]['page'],'/article');self.assertNotIn('secret',json.dumps(matches))
    def test_invalid_batch_atomic(self):
        event=self.event()
        self.assertEqual(self.request('/collect',{'site':server.SITE,'events':[event,self.event(type='keystroke')]},{'Origin':'http://127.0.0.1:8790'})[0],400)
        with server.connection() as conn: self.assertEqual(conn.execute('SELECT COUNT(*) FROM events WHERE id=?',(event['id'],)).fetchone()[0],0)
    def test_limits(self):
        self.assertEqual(self.request('/collect',{'site':server.SITE,'events':[self.event()]*31},{'Origin':'http://127.0.0.1:8790'})[0],400)
    def test_private_files(self): self.assertEqual(self.request('/private-data/analytics.sqlite')[0],404)
    def test_invalid_time(self): self.assertEqual(self.request('/collect',{'site':server.SITE,'events':[self.event(at='yesterday')]},{'Origin':'http://127.0.0.1:8790'})[0],400)

if __name__=='__main__':unittest.main()
