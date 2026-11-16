"""Local Python web server; no dependencies, compatible with modern Python 3."""
import argparse,csv,io,json,mimetypes,secrets,sys,threading,webbrowser
from datetime import datetime,timezone
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from engine import defaults,run,compare,compact,analyse_meter,validate,SCHEMAS,FILES,ROOT
TOKEN=secrets.token_hex(24)

def import_preview(p):
    kind=p.get('kind');text=p.get('text','')
    if kind not in SCHEMAS:raise ValueError('Choose a supported data type')
    if len(text)>5_000_000:raise ValueError('CSV limit: 5 MB')
    if '\x00' in text:raise ValueError('CSV must be UTF-8 text')
    reader=csv.DictReader(io.StringIO(text.lstrip('\ufeff')))
    try:rows=list(reader)
    except csv.Error as e:raise ValueError('Malformed CSV: '+str(e)) from e
    headers=reader.fieldnames or []
    if not headers or any(not h.strip() for h in headers) or len(set(headers))!=len(headers):raise ValueError('CSV needs non-empty, unique column names')
    for i,row in enumerate(rows):
        if None in row or any(v is None for v in row.values()):raise ValueError(f'Row {i+1}: field count does not match the header')
    if not rows or len(rows)>15000:raise ValueError('CSV needs 1 to 15,000 rows')
    mapping=p.get('mapping',{});units=p.get('units',{});normalized=[];errors=[];dates=set()
    for i,row in enumerate(rows):
        x={f:row.get(mapping.get(f,f),'') for f in SCHEMAS[kind]}
        x['provenance']=str(p.get('provenance','User import; source unverified'))[:300]
        try:
            if 'minute' in x:
                t=str(x['minute']).strip()
                if ':' in t:
                    if 'T' in t or '-' in t:
                        ts=datetime.fromisoformat(t.replace('Z','+00:00'))
                        if ts.tzinfo is None:raise ValueError('ISO timestamps need a timezone, e.g. +04:00')
                        ts=ts.astimezone(timezone.utc);dates.add(ts.date().isoformat());x['minute']=ts.hour*60+ts.minute
                        if ts.second:raise ValueError('Timestamp seconds must be zero')
                    else:
                        hh,mm=map(int,t.split(':'))
                        if not 0<=hh<24 or not 0<=mm<60:raise ValueError('Invalid HH:MM time')
                        x['minute']=hh*60+mm
            for f in ['inflow_m3s','q_m3s','total_flow_m3s','flow_m3s']:
                if f in x:x[f]=float(x[f])/(3600 if units.get('flow')=='m3/h' else 1000 if units.get('flow')=='L/s' else 1)
            for f in ['measured_kw','input_kw']:
                if f in x:x[f]=float(x[f])*(1000 if units.get('power')=='MW' else 1)
            if 'pump_efficiency' in x:x['pump_efficiency']=float(x['pump_efficiency'])/(100 if units.get('efficiency')=='percent' else 1)
            normalized.append(x)
        except (ValueError,TypeError) as e:errors.append(f'Row {i+1}: {e}')
    if len(dates)>1:errors.append('Multiple UTC dates found; import one complete UTC day at a time')
    clean=[]
    if not errors:
        try:clean=validate(kind,normalized)
        except ValueError as e:errors.append(str(e))
    stats={}
    if clean:
        for k in SCHEMAS[kind]:
            vals=[r[k] for r in clean if isinstance(r[k],(int,float))]
            if vals:stats[k]={'min':min(vals),'max':max(vals),'mean':sum(vals)/len(vals)}
    coverage={}
    if kind in ['inflows','meters'] and clean:
        for stage in sorted({r.get('stage','Meter series') for r in clean}):coverage[stage]=sum(r['duration_h'] for r in clean if r.get('stage','Meter series')==stage)
    warnings=[]
    if coverage and any(abs(h-24)>1e-6 for h in coverage.values()):warnings.append('Coverage is not 24 hours. Inflow simulation requires a complete day; meter analysis matches only available intervals.')
    return dict(valid=not errors,rows=clean,preview=(clean or normalized)[:8],raw_count=len(rows),errors=errors,warnings=warnings,stats=stats,coverage=coverage,columns=reader.fieldnames)

def compute(path,p):
    if path=='/api/import':return import_preview(p)
    data=p.get('data') or defaults();settings=p.get('settings',{})
    if path=='/api/run':
        result=run(data,settings);return {'result':result}
    if path=='/api/compare':return {'comparisons':compare(data,settings)}
    if path=='/api/analytics':return analyse_meter(data,run(data,settings))
    if path=='/api/scenario':
        base=run(data,settings);change=p.get('changes',{});alt=run(data,dict(settings,**change));out={'baseline':base,'alternative':alt}
        tolerance=.01*base['settings']['area_m2']*(base['settings']['level_max']-base['settings']['level_min']);comparable=base['overflow_m3']<1 and alt['overflow_m3']<1 and abs(base['storage_change_m3']-alt['storage_change_m3'])<tolerance and abs(base['volume_m3']-alt['volume_m3'])<tolerance and not base['emergency_stops'] and not alt['emergency_stops'] and not base['aux_overload_intervals'] and not alt['aux_overload_intervals'] and not base['odour_shortfall_intervals'] and not alt['odour_shortfall_intervals']
        out['comparable']=comparable;out['daily_cost_difference']=base['cost_aed']-alt['cost_aed'];out['daily_energy_difference']=base['energy_kwh']-alt['energy_kwh'];return out
    raise ValueError('Unknown analysis')

class Handler(BaseHTTPRequestHandler):
    def send(self,data,typ='application/json; charset=utf-8',status=200):
        if not isinstance(data,bytes):data=json.dumps(data,allow_nan=False).encode()
        self.send_response(status);self.send_header('Content-Type',typ);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data)
    def do_GET(self):
        path=self.path.split('?')[0]
        if path=='/api/bootstrap':self.send({'token':TOKEN,'data':defaults(),'schemas':SCHEMAS});return
        if path in ['/','/index.html']:file=ROOT/'static'/'index.html'
        elif path in ['/static/style.css','/static/app.js','/static/twin.js','/static/charts.js']:file=ROOT/path.lstrip('/')
        elif path.startswith('/data/') and path[6:] in list(FILES.values())+['import_example_m3h.csv','import_example_errors.csv']:file=ROOT/'data'/path[6:]
        else:self.send({'error':'Not found'},status=404);return
        self.send(file.read_bytes(),mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
    def do_POST(self):
        if self.headers.get('X-Session-Token')!=TOKEN:self.send({'error':'Refresh the page to renew the local session'},status=403);return
        origin=self.headers.get('Origin')
        if origin and origin not in ['http://'+self.headers.get('Host',''),'https://'+self.headers.get('Host','')]:self.send({'error':'Origin rejected'},status=403);return
        try:
            size=int(self.headers.get('Content-Length',0))
            if not 0<size<=12_000_000:raise ValueError('Request exceeds 12 MB')
            result=compute(self.path,json.loads(self.rfile.read(size)));self.send(result)
        except (ValueError,KeyError,TypeError,OverflowError,AttributeError) as e:self.send({'error':str(e)},status=400)
    def log_message(self,*args):pass
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=0);parser.add_argument('--host',default='127.0.0.1');parser.add_argument('--no-browser',action='store_true');parser.add_argument('--strictPort',action='store_true');args=parser.parse_args()
    httpd=ThreadingHTTPServer((args.host,args.port),Handler);url='http://127.0.0.1:'+str(httpd.server_port)
    print('TPS Twin Studio | Python',sys.version.split()[0]);print('Open this address:',url,flush=True);print('Keep this window open. No more commands needed. Stop: Ctrl+C.',flush=True)
    if not args.no_browser:threading.Timer(.8,lambda:webbrowser.open(url)).start()
    try:httpd.serve_forever()
    except KeyboardInterrupt:pass
    finally:httpd.server_close()
