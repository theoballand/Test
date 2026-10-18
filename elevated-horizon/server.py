"""Elevated Horizon local CRM. Start: python3 server.py. Loopback only."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import argparse, json, sqlite3, secrets, os, datetime

ROOT = Path(__file__).resolve().parent
CHECKS = ['espace','tiers','meteo','assurance','qualification','materiel','acces','identification']
STAGES = ['Demande','Étude','Devis','Réservation','Captation','Aperçus','Solde','Livré','Clos']

class Store:
    def __init__(self,path):
        self.path=path
        path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as c:
            c.execute('CREATE TABLE IF NOT EXISTS records (kind TEXT, id TEXT, data TEXT, PRIMARY KEY(kind,id))')
        os.chmod(path,0o600)
    def connect(self):return sqlite3.connect(self.path)
    def all(self,kind):
        with self.connect() as c:return [json.loads(x[0]) for x in c.execute('SELECT data FROM records WHERE kind=? ORDER BY rowid',(kind,))]
    def save(self,kind,data):
        if kind not in ('contacts','missions','quotes'):raise ValueError('Type inconnu')
        if not isinstance(data,dict):raise ValueError('Objet attendu')
        data=dict(data)
        if kind=='contacts':
            data={k:data.get(k,'') for k in ('id','name','company','email','phone','type','next','notes','archived')}
            if not str(data['name']).strip():raise ValueError('Nom requis')
            if data['type'] not in ('Agence','Particulier','Autre professionnel'):raise ValueError('Type client invalide')
        if kind=='missions':
            data={k:data.get(k,'') for k in ('id','title','contact','address','date','stage','offer','price','deliverables','next','notes','checks','deposit','balance','archived')}
            if not str(data['title']).strip():raise ValueError('Titre requis')
            if data['stage'] not in STAGES:raise ValueError('Statut inconnu')
            if data['contact'] and data['contact'] not in [x['id'] for x in self.all('contacts')]:raise ValueError('Contact introuvable')
            try:
                price=Decimal(str(data['price']))
                if not price.is_finite() or price<=0 or price!=price.quantize(Decimal('.01')):raise ValueError('Prix positif au centime requis')
            except InvalidOperation:raise ValueError('Prix invalide')
            data['price']=str(price)
            for field in ('deposit','balance'):
                # These are manual bank reconciliation confirmations, not payment orders.
                data[field]=data[field] is True
            oldchecks=data['checks'] if isinstance(data['checks'],dict) else {}
            data['checks']={k:oldchecks.get(k) is True for k in CHECKS}
            if data['stage'] in ('Réservation','Captation','Aperçus','Solde','Livré','Clos') and not data['deposit']:
                raise ValueError('Confirmer l’encaissement réel de l’acompte avant ce statut. Aucun paiement ne sera exécuté.')
            if data['stage'] in ('Livré','Clos') and not data['balance']:
                raise ValueError('Confirmer l’encaissement réel du solde avant livraison.')
        if kind=='quotes':
            mission=next((x for x in self.all('missions') if x['id']==data.get('mission')),None)
            if not mission:raise ValueError('Mission introuvable')
            contact=next((x for x in self.all('contacts') if x['id']==mission['contact']),{})
            n=1+len([q for q in self.all('quotes') if q['mission']==mission['id']])
            data={'mission':mission['id'],'version':n,'snapshot':mission,'contactSnapshot':contact,'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'BROUILLON NON ÉMIS'}
        data['id']=data.get('id') or secrets.token_hex(8)
        data['updated']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        data['archived']=data.get('archived') is True
        with self.connect() as c:
            c.execute('INSERT INTO records VALUES(?,?,?) ON CONFLICT(kind,id) DO UPDATE SET data=excluded.data',(kind,data['id'],json.dumps(data,ensure_ascii=False)))
        return data

def handler(store,port,token):
 class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def respond(self,status,data,typ='application/json; charset=utf-8'):
        payload=json.dumps(data,ensure_ascii=False).encode() if isinstance(data,(dict,list)) else data
        self.send_response(status);self.send_header('Content-Type',typ);self.send_header('Content-Length',str(len(payload)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY')
        self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers();self.wfile.write(payload)
    def allowed(self):return self.headers.get('Host') in (f'127.0.0.1:{port}',f'localhost:{port}')
    def do_GET(self):
        if not self.allowed():return self.respond(403,{'error':'Host interdit'})
        if self.path=='/api/state':return self.respond(200,{k:store.all(k) for k in ('contacts','missions','quotes')}|{'token':token})
        if self.path=='/api/backup':return self.respond(200,{'format':'elevated-horizon-v1','exported':datetime.datetime.now(datetime.timezone.utc).isoformat(),**{k:store.all(k) for k in ('contacts','missions','quotes')}})
        allowed={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}
        if self.path not in allowed:return self.respond(404,{'error':'Introuvable'})
        typ={'/':'text/html','/app.js':'text/javascript','/style.css':'text/css'}[self.path]+'; charset=utf-8'
        self.respond(200,(ROOT/allowed[self.path]).read_bytes(),typ)
    def do_POST(self):
        origin=self.headers.get('Origin')
        if not self.allowed() or self.headers.get('X-CSRF-Token')!=token or (origin and origin not in (f'http://127.0.0.1:{port}',f'http://localhost:{port}')):
            return self.respond(403,{'error':'Requête refusée'})
        try:
            if self.headers.get_content_type()!='application/json':raise ValueError('JSON attendu')
            size=int(self.headers.get('Content-Length',0))
            if size<1 or size>200000:raise ValueError('Taille invalide')
            kind=self.path.removeprefix('/api/')
            value=store.save(kind,json.loads(self.rfile.read(size)))
            self.respond(200,value)
        except (ValueError,TypeError,KeyError) as e:self.respond(400,{'error':str(e)})
 return Handler

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);p.add_argument('--data',type=Path,default=ROOT/'private'/'crm.sqlite3');a=p.parse_args()
    store=Store(a.data);server=ThreadingHTTPServer(('127.0.0.1',a.port),handler(store,a.port,secrets.token_urlsafe(32)))
    print(f'Elevated Horizon : http://127.0.0.1:{a.port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:server.server_close()
