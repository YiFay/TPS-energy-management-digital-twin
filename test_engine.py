import copy,json,math,threading,unittest,urllib.request,urllib.error
from engine import defaults,run,compare,analyse_meter,validate,config
from app import import_preview,compute,Handler,TOKEN
from http.server import ThreadingHTTPServer

class EngineeringTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=defaults();cls.base=run(cls.data)
 def test_twelve_scenarios_conserve_water_and_energy(self):
  cases=compare(self.data,{})
  self.assertEqual(len(cases),12)
  for r in cases:
   self.assertLess(abs(r['mass_balance_error_m3']),1e-5)
   self.assertAlmostEqual(r['energy_kwh'],sum(r['systems'].values()),5)
   self.assertGreater(r['energy_kwh'],0)
 def test_hydraulic_energy_and_shaft_rating(self):
  for r in self.base['rows']:
   if not r['pumps_running']:continue
   expected=9.81*r['outflow_m3s']*r['head_m']/r['pump_eta']/.965/.985
   self.assertAlmostEqual(r['main_kw'],expected,5)
   self.assertLessEqual(r['main_kw']*.965*.985/r['pumps_running'],3900.01)
   self.assertGreaterEqual(r['speed_pct'],70-1e-5);self.assertLessEqual(r['speed_pct'],94.1+1e-5)
 def test_common_pipe_uses_station_flow(self):
  # Piecewise-linear common curve, not a single-pump curve.
  for r in self.base['rows']:
   q=r['outflow_m3s'];a=math.floor(q);expected=.025*(a*a+(q-a)*((a+1)**2-a*a))
   self.assertAlmostEqual(r['friction_m'],expected,7)
 def test_inventory_and_zone_reconcile(self):
  r=self.base
  self.assertAlmostEqual(sum(r['zones'].values()),r['systems']['HVAC'],7)
  self.assertAlmostEqual(sum(r['assets'].values())+r['systems']['Main pumping'],r['energy_kwh'],5)
 def test_minimum_run_and_rest(self):
  r=run(self.data,{'strategy':'tariff'});c=r['settings'];last_start=[-1e6]*6;last_stop=[-1e6]*6;prev=set()
  self.assertEqual(r['emergency_stops'],0)
  for x in r['rows']:
   active=set(x['active_ids']);m=x['minute']
   for p in active-prev:
    i=int(p[-2:])-1;self.assertGreaterEqual(m-last_stop[i],c['min_off_min']);last_start[i]=m
   for p in prev-active:
    i=int(p[-2:])-1;self.assertGreaterEqual(m-last_start[i],c['min_run_min']);last_stop[i]=m
   prev=active
 def test_outage_is_not_fake_energy_savings(self):
  r=run(self.data,{'available':1,'stage':'Ultimate_plus'})
  self.assertGreater(r['overflow_m3'],0)
  self.assertLess(abs(r['mass_balance_error_m3']),1e-5)
  self.assertLessEqual(max(x['pumps_running'] for x in r['rows']),1)
  c=compute('/api/scenario',{'data':self.data,'settings':{'stage':'Ultimate_plus'},'changes':{'available':1}})
  self.assertFalse(c['comparable'])
 def test_power_factor_does_not_change_kwh(self):
  r=run(self.data,{'pf':.7});self.assertAlmostEqual(r['energy_kwh'],self.base['energy_kwh'],7)
 def test_network_boundary(self):
  r=run(self.data,{'boundary':'TPS + network'})
  self.assertEqual(self.base['systems']['Regional odour'],0)
  self.assertAlmostEqual(r['energy_kwh']-self.base['energy_kwh'],r['systems']['Regional odour'],5)
 def test_efficiency_preserves_water_service(self):
  r=compute('/api/scenario',{'data':self.data,'settings':{},'changes':{'pump_factor':1.02,'motor_eta':.975,'vfd_eta':.99,'cooling_cop':5.2,'hvac_cop':3.8,'fan_efficiency':.75}})
  self.assertTrue(r['comparable']);self.assertGreater(r['daily_energy_difference'],0)
 def test_storage_and_tariff_terminal_recovery(self):
  for strategy in ['storage','tariff']:
   r=run(self.data,{'strategy':strategy})
   self.assertLess(abs(r['mass_balance_error_m3']),1e-5)
   self.assertLess(abs(r['final_level_m']-r['settings']['level_initial']),.04)
 def test_cooling_link_and_no_double_count(self):
  r=self.base['rows'][140];self.assertAlmostEqual(r['assets']['CW-CH'],r['cooling_heat_kw']/4.5,7)
  self.assertGreater(r['motor_loss_kw'],0);self.assertGreater(r['vfd_loss_kw'],0)
 def test_reject_nonfinite_duplicate_negative_and_gap(self):
  for change in ['nan','duplicate','negative','gap']:
   d=copy.deepcopy(self.data)
   if change=='nan':d['inflows'][0]['inflow_m3s']='NaN'
   elif change=='duplicate':d['inflows'].append(d['inflows'][0])
   elif change=='negative':d['inflows'][0]['inflow_m3s']=-1
   else:d['inflows'].pop(0)
   with self.assertRaises(ValueError):run(d)
 def test_mapping_units_and_validation(self):
  from pathlib import Path
  text=(Path(__file__).parent/'data/import_example_m3h.csv').read_text()
  r=import_preview({'kind':'inflows','text':text,'mapping':{'minute':'time','duration_h':'hours','inflow_m3s':'flow_m3h'},'units':{'flow':'m3/h'}})
  self.assertTrue(r['valid']);self.assertAlmostEqual(r['rows'][0]['inflow_m3s'],float(self.data['inflows'][0]['inflow_m3s']),4)
  bad=import_preview({'kind':'inflows','text':'stage,minute,duration_h,inflow_m3s\nCOD,0,0.083333,5\nCOD,0,0.083333,6'})
  self.assertFalse(bad['valid'])
 def test_imported_shared_curve_changes_head(self):
  d=copy.deepcopy(self.data)
  for row in d['system']:row['shared_friction_m']=float(row['shared_friction_m'])*1.3
  r=run(d);self.assertGreater(r['energy_kwh'],self.base['energy_kwh'])
 def test_meter_split_and_seeded_event(self):
  a=analyse_meter(self.data,self.base)
  self.assertTrue(a['available']);self.assertEqual(a['train_rows'],144);self.assertEqual(a['test_rows'],144)
  self.assertTrue(all(not x['flag'] for x in a['rows'] if not x['holdout']))
  self.assertGreater(sum(x['flag'] for x in a['rows'] if 840<=x['minute']<960),18)
 def test_invalid_settings(self):
  for settings in [{'available':2.5},{'available':7},{'level_initial':8},{'motor_eta':1.1},{'pf':0}]:
   with self.assertRaises(ValueError):config(settings)
 def test_auxiliary_overload_blocks_service_comparison(self):
  r=compute('/api/scenario',{'data':self.data,'settings':{},'changes':{'fan_efficiency':.5}})
  self.assertGreater(r['alternative']['aux_overload_intervals'],0)
  self.assertFalse(r['comparable'])
 def test_ocu_air_duty_preserved_by_efficiency_change(self):
  r=run(self.data,{'fan_efficiency':.8})
  for a,b in zip(self.base['rows'],r['rows']):self.assertAlmostEqual(a['odour_airflow_m3h'],b['odour_airflow_m3h'],6)
  self.assertLess(r['systems']['Odour control'],self.base['systems']['Odour control'])
 def test_malformed_csv_header_and_field_counts(self):
  for text in ['minute,minute\n0,0','stage,minute,duration_h,inflow_m3s\nCOD,0,0.1,4,extra']:
   with self.assertRaises(ValueError):import_preview({'kind':'inflows','text':text})
 def test_load_import_mw_conversion(self):
  text='asset_id,system,name,zone_id,boundary,input_kw,duty_units,load_factor,schedule\nX,HVAC,Test,Z-ELEC,TPS,0.055,1,0.7,continuous'
  r=import_preview({'kind':'loads','text':text,'units':{'power':'MW'}})
  self.assertTrue(r['valid']);self.assertAlmostEqual(r['rows'][0]['input_kw'],55)
 def test_http_token_and_static_assets(self):
  server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
  try:
   for path in ['/','/static/app.js','/static/twin.js','/data/auxiliary_loads.csv']:
    with urllib.request.urlopen(url+path) as r:self.assertEqual(r.status,200)
   body=json.dumps({'settings':{}}).encode()
   with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(urllib.request.Request(url+'/api/run',body,{'Content-Type':'application/json'}))
   with urllib.request.urlopen(urllib.request.Request(url+'/api/run',body,{'Content-Type':'application/json','X-Session-Token':TOKEN})) as r:self.assertGreater(json.load(r)['result']['energy_kwh'],0)
   with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(url+'/../engine.py')
  finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__':unittest.main(verbosity=2)
