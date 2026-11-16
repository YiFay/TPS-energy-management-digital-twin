"""Generate original demonstration data. Reads no client design spreadsheets."""
import csv,math
from pathlib import Path
from engine import run,defaults
D=Path(__file__).resolve().parent/'data'
def write(name,rows):
    with (D/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
zones=[('Z-ELEC','MV electrical rooms','Ground',420,25,32),('Z-CTRL','Control and SCADA room','Ground',180,24,29),('Z-ADMIN','Administration and welfare','Ground',520,24,28),('Z-MOTOR','Motor and drive gallery','UG2',680,28,36),('Z-WORK','Maintenance workshop','Ground',360,26,32),('Z-SERVICE','Service and access rooms','UG1',220,27,34)]
write('hvac_zones.csv',[dict(zip(['zone_id','name','level','area_m2','setpoint_c','max_temp_c'],z),provenance='Assumed demonstration zone; not extracted room schedule') for z in zones])
a=[]
def add(i,s,n,z,p,u,lf,sch='continuous',boundary='TPS'):a.append(dict(asset_id=i,system=s,name=n,zone_id=z,boundary=boundary,input_kw=p,duty_units=u,load_factor=lf,schedule=sch,provenance='Synthetic illustrative electrical input; not a project load list'))
for i,z in enumerate(zones):add('HV-'+str(i+1).zfill(2),'HVAC',z[1]+' cooling',z[0],[55,20,60,70,35,25][i],1,[.72,.78,.7,.8,.65,.65][i],'daytime' if i in [2,4] else 'continuous')
add('VE-01','Ventilation','Dry-well safety ventilation','DRY',45,2,.8)
add('VE-02','Ventilation','Screen room extraction','SCREEN',25,2,.8)
add('OD-FN','Odour control','TPS extraction fans','OCU',160,2,.8)
add('OD-CI','Odour control','Scrubber circulation pumps','OCU',22,3,.8)
add('OD-DO','Odour control','Chemical dosing auxiliaries','OCU',3,4,.5)
add('RO-FN','Regional odour','Regional extraction fans','ROCF',110,4,.75,boundary='Network')
add('RO-CI','Regional odour','Regional scrubber circulation','ROCF',15,6,.8,boundary='Network')
add('CW-CH','Central cooling','Chiller (thermal duty / COP)','COOL',230,2,.62)
add('CW-PU','Central cooling','Cooling circulation pumps','COOL',45,3,.72)
add('CW-FA','Central cooling','Heat rejection fans','COOL',30,3,.7)
add('RW-01','Water services','RW polishing and service water','RW',80,1,.65)
add('SC-01','Auxiliary pumping','Self-cleaning pumps','WET',180,1,.7,'intermittent')
add('DR-01','Auxiliary pumping','Drainage pumps','DRY',30,2,.7,'intermittent')
add('IT-01','Controls and ICT','PLC and SCADA servers','Z-CTRL',14,1,.9)
add('IN-01','Controls and ICT','Field instruments and telemetry','DRY',5,1,.9)
add('CC-01','Controls and ICT','CCTV and access control','SITE',4,1,.9)
add('LI-01','Buildings and lighting','External lighting','SITE',32,1,.85,'night')
add('LI-02','Buildings and lighting','Internal lighting','Z-SERVICE',28,1,.7,'daytime')
add('EL-01','Electrical losses','Transformer and distribution losses','ELEC',55,1,.8)
add('UP-01','Electrical losses','UPS conversion losses','Z-CTRL',7,1,.75)
write('auxiliary_loads.csv',a)
write('weather_tariff.csv',[dict(minute=m,outdoor_c=round(33+6*math.cos(2*math.pi*(m/60-15)/24),2),tariff_aed_kwh=.28 if m<360 or m>=1320 else .46 if 840<=m<1200 else .35,provenance='Synthetic weather and illustrative time-of-use tariff; not utility pricing') for m in range(0,1440,5)])
d=defaults();r=run(d)
meters=[]
for i,x in enumerate(r['rows']):
    residual=.008*x['total_kw']*math.sin(i*1.8)+(.08*x['total_kw'] if 840<=x['minute']<960 else 0)
    meters.append(dict(minute=x['minute'],duration_h=x['duration_h'],measured_kw=round(x['total_kw']+residual,3),flow_m3s=round(x['outflow_m3s'],5),head_m=round(x['head_m'],3),provenance='SYNTHETIC COD Normal follow baseline with injected +8% load at 14:00-16:00; not measured'))
write('demo_meter_readings.csv',meters)
write('import_example_m3h.csv',[dict(stage='COD',time=f'{m//60:02d}:{m%60:02d}',hours=1/12,flow_m3h=round(5.2*(1+.2*math.cos(2*math.pi*(m/60-9)/24)+.09*math.cos(4*math.pi*(m/60-19)/24))*3600,3)) for m in range(0,1440,5)])
write('import_example_errors.csv',[dict(stage='COD',minute=0,duration_h=1/12,inflow_m3s=5),dict(stage='COD',minute=0,duration_h=1/12,inflow_m3s=5),dict(stage='COD',minute=10,duration_h=1/12,inflow_m3s=-3)])
print('Generated 6 HVAC zones, 26 auxiliary groups, weather/tariff and synthetic meter readings.')
