"""TPS Twin Studio: transparent, synthetic planning calculations; Python stdlib only."""
import csv, io, math, statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
STAGES=['COD','Expiry','Ultimate','Ultimate_plus']
SYSTEMS=['Main pumping','HVAC','Ventilation','Odour control','Regional odour','Central cooling','Water services','Auxiliary pumping','Controls and ICT','Buildings and lighting','Electrical losses']
FILES={'inflows':'inflow_profiles.csv','curve':'reference_pump_curve.csv','system':'shared_system_curves.csv','loads':'auxiliary_loads.csv','zones':'hvac_zones.csv','weather':'weather_tariff.csv','meters':'demo_meter_readings.csv'}
SCHEMAS={
'inflows':['stage','minute','duration_h','inflow_m3s'],
'curve':['q_m3s','head_m','pump_efficiency'],
'system':['head_case','total_flow_m3s','static_head_m','shared_friction_m'],
'loads':['asset_id','system','name','zone_id','boundary','input_kw','duty_units','load_factor','schedule'],
'zones':['zone_id','name','level','area_m2','setpoint_c','max_temp_c'],
'weather':['minute','outdoor_c','tariff_aed_kwh'],
'meters':['minute','duration_h','measured_kw','flow_m3s','head_m']}

def number(v,name,lo=-1e20,hi=1e20):
    try: n=float(v)
    except (TypeError,ValueError): raise ValueError(name+' must be numeric')
    if not math.isfinite(n) or not lo<=n<=hi: raise ValueError(name+' outside allowed range')
    return n

def integer(v,name,lo,hi):
    n=number(v,name,lo,hi)
    if n!=int(n):raise ValueError(name+' must be a whole number')
    return int(n)

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def defaults():return {k:read_csv(ROOT/'data'/v) for k,v in FILES.items() if (ROOT/'data'/v).exists()}

def validate(kind,rows):
    if kind not in SCHEMAS:raise ValueError('Unknown data type')
    if not rows or len(rows)>15000:raise ValueError('Supply 1 to 15,000 rows')
    seen=set();out=[]
    for i,r in enumerate(rows):
        try:
            for key in SCHEMAS[kind]:
                if key not in r or str(r[key]).strip()=='':raise ValueError('Missing '+key)
            x={k:str(v).strip() for k,v in r.items() if k is not None}
            if kind in ['inflows','meters','weather']:
                x['minute']=integer(r['minute'],'minute',0,1439)
                key=(r.get('stage',''),x['minute'])
                if key in seen:raise ValueError('Duplicate interval')
                seen.add(key)
                if kind!='weather':
                    x['duration_h']=number(r['duration_h'],'duration_h',1/3600,24)
                    if x['minute']/60+x['duration_h']>24+1e-8:raise ValueError('Interval crosses midnight')
            if kind=='inflows':
                if r['stage'] not in STAGES:raise ValueError('Unknown stage (use COD / Expiry / Ultimate / Ultimate_plus)')
                x['inflow_m3s']=number(r['inflow_m3s'],'inflow_m3s',0,100)
            elif kind=='curve':
                x.update(q_m3s=number(r['q_m3s'],'flow',0,10),head_m=number(r['head_m'],'head',.01,200),pump_efficiency=number(r['pump_efficiency'],'efficiency fraction',.01,.99))
            elif kind=='system':
                if r['head_case'] not in ['Low','Normal','High']:raise ValueError('Unknown head_case')
                x.update(total_flow_m3s=number(r['total_flow_m3s'],'total flow',0,100),static_head_m=number(r['static_head_m'],'static head',1,150),shared_friction_m=number(r['shared_friction_m'],'friction',0,100))
            elif kind=='loads':
                if r['asset_id'] in seen:raise ValueError('Duplicate asset_id')
                seen.add(r['asset_id'])
                if r['system'] not in SYSTEMS[1:]:raise ValueError('Unknown system')
                if r['boundary'] not in ['TPS','Network']:raise ValueError('Unknown boundary')
                if r['schedule'] not in ['continuous','daytime','night','intermittent']:raise ValueError('Unknown schedule')
                x.update(input_kw=number(r['input_kw'],'input_kw',0,10000),duty_units=integer(r['duty_units'],'duty_units',0,100),load_factor=number(r['load_factor'],'load_factor',0,1))
            elif kind=='zones':
                if r['zone_id'] in seen:raise ValueError('Duplicate zone_id')
                seen.add(r['zone_id']);x.update(area_m2=number(r['area_m2'],'area',1,100000),setpoint_c=number(r['setpoint_c'],'setpoint',15,40),max_temp_c=number(r['max_temp_c'],'temperature limit',20,60))
                if x['max_temp_c']<=x['setpoint_c']:raise ValueError('Temperature limit must exceed setpoint')
            elif kind=='weather':x.update(outdoor_c=number(r['outdoor_c'],'outdoor temperature',-20,60),tariff_aed_kwh=number(r['tariff_aed_kwh'],'tariff',0,10))
            elif kind=='meters':x.update(measured_kw=number(r['measured_kw'],'meter power',0,200000),flow_m3s=number(r['flow_m3s'],'meter flow',0,100),head_m=number(r['head_m'],'meter head',0,200))
            out.append(x)
        except ValueError as e:raise ValueError(f'Row {i+1}: {e}') from e
    if kind in ['inflows','meters']:
        out.sort(key=lambda x:(x.get('stage',''),x['minute']))
        for a,b in zip(out,out[1:]):
            if a.get('stage')==b.get('stage') and a['minute']+a['duration_h']*60>b['minute']+1e-7:raise ValueError('Intervals overlap')
    elif kind=='weather':
        out.sort(key=lambda x:x['minute'])
        if out[0]['minute']!=0:raise ValueError('Weather/tariff must start at minute 0; values held to next row')
    elif kind in ['curve','system']:
        field='q_m3s' if kind=='curve' else 'total_flow_m3s'
        groups=['pump'] if kind=='curve' else sorted({r['head_case'] for r in out})
        for group in groups:
            seq=sorted([r for r in out if kind=='curve' or r['head_case']==group],key=lambda r:r[field])
            if len(seq)<3 or any(a[field]>=b[field] for a,b in zip(seq,seq[1:])):raise ValueError('Curve needs 3+ unique flow points per case')
            if kind=='system' and max(r['static_head_m'] for r in seq)-min(r['static_head_m'] for r in seq)>1e-6:raise ValueError('Static head must be constant within a case')
        out.sort(key=lambda x:(x.get('head_case',''),x[field]))
    return out

def interpolate(rows,x,xfield,yfield):
    if x<rows[0][xfield]-1e-7 or x>rows[-1][xfield]+1e-7:raise ValueError('No extrapolation: flow beyond supplied curve')
    for a,b in zip(rows,rows[1:]):
        if a[xfield]-1e-7<=x<=b[xfield]+1e-7:
            return a[yfield]+(b[yfield]-a[yfield])*(x-a[xfield])/(b[xfield]-a[xfield])
    return rows[-1][yfield]

def config(settings):
    c=dict(stage='COD',head_case='Normal',boundary='TPS',strategy='follow',available=6,motor_eta=.965,vfd_eta=.985,pump_factor=1,hvac_cop=3.4,cooling_cop=4.5,fan_efficiency=.70,carbon=.4,pf=.96,area_m2=900,level_min=1,level_max=5,level_initial=3,min_run_min=15,min_off_min=10,annual_days=365,tariff_mode='profile',flat_tariff=.35,odour_dp_pa=3500,odour_min_air_m3h=150000,cooling_delta_k=5)
    c.update(settings or {})
    for key,lo,hi in [('motor_eta',.5,1),('vfd_eta',.5,1),('pump_factor',.8,1.04),('hvac_cop',2,6),('cooling_cop',2,8),('fan_efficiency',.5,.85),('carbon',0,5),('pf',.5,1),('area_m2',100,5000),('level_min',0,5),('level_max',1,10),('level_initial',0,10),('min_run_min',0,120),('min_off_min',0,120),('annual_days',1,366),('flat_tariff',0,10),('odour_dp_pa',500,10000),('odour_min_air_m3h',1000,1000000),('cooling_delta_k',2,10)]:c[key]=number(c[key],key,lo,hi)
    c['available']=integer(c['available'],'available pumps',1,6)
    if not c['level_min']<c['level_initial']<c['level_max']:raise ValueError('Initial water level must be inside the operating band')
    if c['stage'] not in STAGES or c['head_case'] not in ['Low','Normal','High'] or c['strategy'] not in ['follow','storage','tariff'] or c['boundary'] not in ['TPS','TPS + network']:raise ValueError('Unknown planning selection')
    if c['tariff_mode'] not in ['profile','flat']:raise ValueError('Unknown tariff mode')
    return c

def point(q,static,system,curve,c,nrange):
    if q<=1e-9:
        return dict(q=0,n=0,head=static,friction=0,kw=0,eta=0,speed=0,shaft_kw=0,motor_loss_kw=0,vfd_loss_kw=0) if 0 in nrange else None
    if q>system[-1]['total_flow_m3s']:return None
    friction=interpolate(system,q,'total_flow_m3s','shared_friction_m');head=static+friction;best=None
    qmin=max(2.05,curve[0]['q_m3s']);qmax=min(3.65,curve[-1]['q_m3s'])
    for n in nrange:
        if n==0:continue
        per=q/n;lo=max(.70/.941,per/qmax);hi=min(1,per/qmin)
        if lo>hi:continue
        def h(s):return s*s*interpolate(curve,per/s,'q_m3s','head_m')
        if h(hi)<head-1e-6 or h(lo)>head+1e-6:continue
        for _ in range(23):
            mid=(lo+hi)/2
            if h(mid)<head:lo=mid
            else:hi=mid
        speed=(lo+hi)/2;eta=min(.97,interpolate(curve,per/speed,'q_m3s','pump_efficiency')*c['pump_factor'])
        shaft=9.81*per*head/eta
        if shaft>3900:continue
        motor=shaft/c['motor_eta'];elec=motor/c['vfd_eta'];kw=n*elec
        if best is None or kw<best['kw']:
            best=dict(q=q,n=n,head=head,friction=friction,kw=kw,eta=eta,speed=speed*.941,shaft_kw=n*shaft,motor_loss_kw=n*(motor-shaft),vfd_loss_kw=n*(elec-motor))
    return best

def schedule_factor(kind,h):
    return {'continuous':1.,'daytime':1. if 7<=h<19 else .18,'night':1. if h<6 or h>=18 else .12,'intermittent':1. if int(h*60)%60<15 else 0.}[kind]

def run(data,settings=None):
    c=config(settings);clean={k:validate(k,data[k]) for k in ['inflows','curve','system','loads','zones','weather']}
    inflows=[r for r in clean['inflows'] if r['stage']==c['stage']]
    if not inflows:raise ValueError('No inflow data for the selected stage')
    if inflows[0]['minute']!=0 or abs(sum(r['duration_h'] for r in inflows)-24)>1e-6:raise ValueError('Storage simulation needs a complete contiguous 24-hour profile')
    for a,b in zip(inflows,inflows[1:]):
        if abs(a['minute']+a['duration_h']*60-b['minute'])>1e-6:raise ValueError('Missing inflow intervals; repair gaps before simulation')
    system=[r for r in clean['system'] if r['head_case']==c['head_case']]
    if not system:raise ValueError('No system curve for selected head case')
    zone_ids={z['zone_id'] for z in clean['zones']}
    for a in clean['loads']:
        if a['system']=='HVAC' and a['zone_id'] not in zone_ids:raise ValueError('HVAC load '+a['asset_id']+' references an unknown zone')
    rows=[];level=c['level_initial'];active=set();last_on=[-1e6]*6;last_off=[-1e6]*6;runtime=[0.]*6;starts=[0]*6
    syse={s:0. for s in SYSTEMS};assete={r['asset_id']:0. for r in clean['loads']};zonee={z:0. for z in zone_ids};emergency=0;overload_intervals=0;odour_shortfall_intervals=0
    for r in inflows:
        m=r['minute'];dt=r['duration_h'];sec=dt*3600;qin=r['inflow_m3s'];wx=max((w for w in clean['weather'] if w['minute']<=m),key=lambda w:w['minute'])
        tariff=wx['tariff_aed_kwh'] if c['tariff_mode']=='profile' else c['flat_tariff']
        target=c['level_initial']
        if c['strategy']=='tariff':target=c['level_min']+.25*(c['level_max']-c['level_min']) if tariff<.36 else c['level_min']+.75*(c['level_max']-c['level_min'])
        horizon=900 if c['strategy']=='follow' else 2400
        if m>=1380:target=c['level_initial'];horizon=600
        qtarget=max(0,qin+(level-target)*c['area_m2']/horizon)
        maxq=qin+max(0,level-c['level_min'])*c['area_m2']/sec
        qtarget=min(qtarget,maxq)
        static=system[0]['static_head_m']-(level-c['level_initial'])
        locked={i for i in active if m-last_on[i]<c['min_run_min']-1e-7}
        ready={i for i in range(c['available']) if i not in active and m-last_off[i]>=c['min_off_min']-1e-7}
        nr=range(len(locked),len(active)+len(ready)+1)
        p=point(qtarget,static,system,clean['curve'],c,nr)
        if not p:
            choices=[]
            upper=min(maxq,system[-1]['total_flow_m3s'],c['available']*3.65)
            for j in range(81):
                pp=point(upper*j/80,static,system,clean['curve'],c,nr)
                if pp:choices.append(pp)
            p=min(choices,key=lambda x:abs(x['q']-qtarget)) if choices else None
        if p is None:
            # Low-water protection overrides minimum run time, recorded explicitly.
            p=point(0,static,system,clean['curve'],c,range(1));emergency+=1
        n=p['n'];new=set(locked) if n>=len(locked) else set()
        for i in sorted(active-new,key=lambda i:runtime[i]):
            if len(new)<n:new.add(i)
        for i in sorted(ready,key=lambda i:runtime[i]):
            if len(new)<n:new.add(i)
        for i in new-active:last_on[i]=m;starts[i]+=1
        for i in active-new:last_off[i]=m
        active=new
        for i in active:runtime[i]+=dt
        end=level+(qin-p['q'])*sec/c['area_m2'];overflow=max(0,end-c['level_max'])*c['area_m2'];end=min(c['level_max'],end)
        if end<c['level_min']-1e-6:raise ValueError('Internal mass-balance lower-bound violation')
        systems={s:0. for s in SYSTEMS};systems['Main pumping']=p['kw'];assets={};zones={};overloaded=[];odour_air=0.
        stage_factor=[.82,.91,1,1.08][STAGES.index(c['stage'])]
        cooling_heat=650*stage_factor+.75*p['motor_loss_kw']
        for a in clean['loads']:
            power=a['input_kw']*a['duty_units']*a['load_factor']*schedule_factor(a['schedule'],m/60)
            if a['boundary']=='Network' and c['boundary']=='TPS':power=0
            if a['system']=='HVAC':power*=max(.55,min(1.5,(wx['outdoor_c']-20)/16))*3.4/c['hvac_cop']
            elif a['asset_id']=='CW-CH':power=cooling_heat/c['cooling_cop']
            elif a['system'] in ['Odour control','Regional odour'] and 'fan' in a['name'].lower():power*=.70/c['fan_efficiency']
            elif a['system'] not in ['Controls and ICT','Buildings and lighting']:power*=stage_factor
            if power>a['input_kw']*a['duty_units']+1e-6:overloaded.append(a['asset_id'])
            if a['system']=='Odour control' and 'fan' in a['name'].lower():odour_air+=power*c['fan_efficiency']*1000/c['odour_dp_pa']*3600
            assets[a['asset_id']]=power;systems[a['system']]+=power;assete[a['asset_id']]+=power*dt
            if a['system']=='HVAC':zones[a['zone_id']]=zones.get(a['zone_id'],0)+power;zonee[a['zone_id']]+=power*dt
        total=sum(systems.values())
        overload_intervals+=bool(overloaded)
        odour_shortfall_intervals+=odour_air<c['odour_min_air_m3h']-1e-6
        for s,pw in systems.items():syse[s]+=pw*dt
        temps={z['zone_id']:z['setpoint_c']+.7+max(0,wx['outdoor_c']-34)*.10+.35*math.sin(m/140+idx) for idx,z in enumerate(clean['zones'])}
        rows.append(dict(minute=m,duration_h=dt,inflow_m3s=qin,outflow_m3s=p['q'],level_start_m=level,level_end_m=end,overflow_m3=overflow,static_head_m=static,head_m=p['head'],friction_m=p['friction'],pumps_running=n,active_ids=[f'P-{i+1:02d}' for i in sorted(active)],speed_pct=p['speed']*100,pump_eta=p['eta'],main_kw=p['kw'],aux_kw=total-p['kw'],total_kw=total,energy_kwh=total*dt,water_m3=p['q']*sec,cost_aed=total*dt*tariff,tariff=tariff,outdoor_c=wx['outdoor_c'],cooling_heat_kw=cooling_heat,cooling_flow_ls=cooling_heat/(4.186*c['cooling_delta_k']),odour_airflow_m3h=odour_air,overloaded_assets=overloaded,systems=systems,assets=assets,zones=zones,zone_temps=temps,motor_loss_kw=p['motor_loss_kw'],vfd_loss_kw=p['vfd_loss_kw']))
        level=end
    energy=sum(r['energy_kwh'] for r in rows);volume=sum(r['water_m3'] for r in rows);inv=sum(r['inflow_m3s']*r['duration_h']*3600 for r in rows);overflow=sum(r['overflow_m3'] for r in rows);delta=(level-c['level_initial'])*c['area_m2']
    return dict(settings=c,rows=rows,energy_kwh=energy,volume_m3=volume,inflow_m3=inv,overflow_m3=overflow,storage_change_m3=delta,mass_balance_error_m3=inv-volume-overflow-delta,sec=energy/volume if volume else None,main_sec=syse['Main pumping']/volume if volume else None,cost_aed=sum(r['cost_aed'] for r in rows),co2_kg=energy*c['carbon'],peak_kw=max(r['total_kw'] for r in rows),systems=syse,assets=assete,zones=zonee,pump_hours=runtime,pump_starts=starts,total_starts=sum(starts),final_level_m=level,emergency_stops=emergency,aux_overload_intervals=overload_intervals,odour_shortfall_intervals=odour_shortfall_intervals,metadata={'profile':'Synthetic planning data unless replaced in Data studio','curve':'Approximate expected curve; not certified','geometry':'Schematic layout interpretation; not a BIM or as-built model','room_temperatures':'Illustrative signals, not a validated thermal simulation'})

def compact(r):return {k:v for k,v in r.items() if k not in ['rows','assets','zones','metadata']}

def compare(data,settings):
    result=[]
    for stage in STAGES:
        if not any(r['stage']==stage for r in data['inflows']):continue
        for head in ['Low','Normal','High']:
            if any(r['head_case']==head for r in data['system']):result.append(compact(run(data,dict(settings,stage=stage,head_case=head))))
    return result

def solve(a,b):
    n=len(b);m=[list(row)+[v] for row,v in zip(a,b)]
    for k in range(n):
        i=max(range(k,n),key=lambda j:abs(m[j][k]));m[k],m[i]=m[i],m[k]
        if abs(m[k][k])<1e-10:raise ValueError('Insufficient variation to fit regression')
        d=m[k][k];m[k]=[v/d for v in m[k]]
        for i in range(n):
            if i!=k:
                d=m[i][k];m[i]=[x-d*y for x,y in zip(m[i],m[k])]
    return [r[-1] for r in m]

def analyse_meter(data,result):
    if not data.get('meters'):return {'available':False,'reason':'Import meter data to activate this analysis.'}
    meter=validate('meters',data['meters']);base={r['minute']:r for r in result['rows']};pairs=[]
    for m in meter:
        r=base.get(m['minute'])
        if r and abs(r['duration_h']-m['duration_h'])<1e-6:
            pairs.append(dict(minute=m['minute'],duration_h=m['duration_h'],observed=m['measured_kw'],physics=r['total_kw'],flow=m['flow_m3s'],head=m['head_m'],temperature=r['outdoor_c'],residual_kw=m['measured_kw']-r['total_kw']))
    if len(pairs)<20:return {'available':False,'reason':'Need at least 20 aligned intervals of equal duration.'}
    # Fit only the first half; evaluation and anomaly screening are held out.
    split=len(pairs)//2;train=pairs[:split];xs=[[1,p['flow']*p['head'],p['temperature']] for p in train];ys=[p['observed'] for p in train]
    try:beta=solve([[sum(x[i]*x[j] for x in xs) for j in range(3)] for i in range(3)],[sum(x[i]*y for x,y in zip(xs,ys)) for i in range(3)])
    except ValueError as e:return {'available':False,'reason':str(e)}
    train_err=[y-sum(a*b for a,b in zip(x,beta)) for x,y in zip(xs,ys)];sigma=max(1,math.sqrt(sum(v*v for v in train_err)/len(train_err)))
    for i,p in enumerate(pairs):
        p['prediction']=beta[0]+beta[1]*p['flow']*p['head']+beta[2]*p['temperature'];p['regression_residual']=p['observed']-p['prediction'];p['threshold_kw']=max(3*sigma,.03*abs(p['prediction']));p['holdout']=i>=split;p['flag']=p['holdout'] and abs(p['regression_residual'])>p['threshold_kw']
    test=pairs[split:];rmse=math.sqrt(sum(p['regression_residual']**2 for p in test)/len(test));ym=statistics.mean(p['observed'] for p in test);ss=sum((p['observed']-ym)**2 for p in test)
    return dict(available=True,rows=pairs,train_rows=split,test_rows=len(test),matched=len(pairs),unmatched=len(meter)-len(pairs),beta=beta,rmse_kw=rmse,r2=1-sum(p['regression_residual']**2 for p in test)/ss if ss>0 else None,flagged=sum(p['flag'] for p in test),positive_physics_deviation_kwh=sum(max(0,p['residual_kw'])*p['duration_h'] for p in pairs),bias_kw=statistics.mean(p['residual_kw'] for p in pairs),measured_kwh=sum(p['observed']*p['duration_h'] for p in pairs),source=next((m.get('provenance') for m in meter if m.get('provenance')),'User-imported meter series; provenance unverified'))
