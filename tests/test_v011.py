"""Regression hashes captured from v0.10 before moving the four rule implementations."""
import json,hashlib
import numpy as np,pandas as pd,pytest
from dataclasses import replace
from fastapi.testclient import TestClient
import app,storage,cartridges
from engine import PaperEngine
def candles():
    x=np.arange(1400);c=100+.01*x+8*np.sin(x*.03)+2*np.sin(x*.22)
    d=pd.DataFrame({'time':pd.date_range('2020-01-01',periods=len(x),freq='4h',tz='UTC'),'open':np.r_[c[0],c[:-1]],'close':c,'high':c+3,'low':c-3,'volume':100+100*(x%7==0)})
    d['high']=d[['high','open']].max(axis=1);d['low']=d[['low','open']].min(axis=1)
    d.attrs.update(volume_is_actual=True,quote='USDT');return d


EXPECTED={'ema:long': '7bf558078efc6dd9eced97c45b93cbf4d9634182fbb9cf46455f10a44b2ba3e1', 'ema:short': 'b92f3319972fe7cc8880df3030a88f4eda7a06a7894c670061c37a72f938dadf', 'ema:both': '3a2832e518691e94a5b03ad025a33e269ae330e1010fa323089ac7cb3aa0beb6', 'rsi:long': '138901772d21bac58b419870ac6fb3601c528df82feb5f73b7a80079941be25b', 'rsi:short': '87ce31fc4d2aa8af6a93d0216d73cd3de27828274df0f66a2f03d519d55d58c3', 'rsi:both': 'b992c2c65fa044a635873935eeaeddbf5dce6a9e78681bc932e2a9a895f111da', 'breakout:long': '0d790e7d8f59541f4f1f8dda13ebbe580a5dfb4101cc278eb2910323bcdcfafa', 'breakout:short': 'a1aebec8a2958d2a87ec2ec313bb589cec685aa1e84e50b3fca818e85c765729', 'breakout:both': '421b8172f057ed7cb1b7238c84b05326529bf2403896d79fed59dc34e310ac8f', 'pullback:long': 'cbdf6f93239fa97a49848ef5421cd68db8ad0f417a3f21bc129ba6ee17416f67', 'pullback:short': 'fb4560b8566f79ada0fda82e694fcd43424a693bc87f71ae3c45cb7d2daadb6f', 'pullback:both': '7512b80d9c677ad9c25cd83529a681b8598a97d471e68f42faa37f377803caa2'}

@pytest.mark.parametrize('case',list(EXPECTED))
def test_v010_execution_is_preserved(case):
    strategy,side=case.split(':')
    s=PaperEngine(candles(),strategy,parameters={'trade_mode':side}).finish()
    s['metrics'].pop('cartridge')
    assert hashlib.sha256(json.dumps(s,sort_keys=True,allow_nan=False).encode()).hexdigest()==EXPECTED[case]

def test_catalog_contract_and_request_validation():
    client=TestClient(app.app);r=client.get('/api/cartridges')
    assert r.status_code==200 and r.json()['paper_only'] is True
    items={c['id']:c for c in r.json()['cartridges']}
    assert {'ema','rsi','breakout','pullback'}<=set(items)
    assert items['breakout']['requires_volume']
    assert items['pullback']['protocol_only']
    assert items['pullback']['fixed']['max_holding_bars']==30
    assert set(items['rsi']['parameter_schema'])=={'rsi_period','rsi_entry','rsi_exit'}
    assert all(len(d)==64 for c in items.values() for d in c['code_sha256'].values())
    for value in ['../../evil','unknown','pullback']:
        assert client.post('/api/backtest',json={'strategy':value}).status_code==422

def test_signal_module_is_the_only_strategy_decision(monkeypatch):
    original=cartridges.get_cartridge('ema')
    assert PaperEngine(candles(),'ema').finish()['metrics']['trades']>0
    no_signal=lambda d,p:(pd.Series(False,index=d.index),pd.Series(False,index=d.index))
    monkeypatch.setattr(cartridges,'REGISTRY',{**cartridges.REGISTRY,'ema':replace(original,long=no_signal,short=no_signal)})
    r=PaperEngine(candles(),'ema',parameters={'trade_mode':'both'}).finish()
    assert r['metrics']['trades']==0 and r['equity']==10000

def test_saved_cartridge_fingerprint_and_resume_mismatch():
    client=TestClient(app.app)
    r=client.post('/api/replay/start',json={'source':'demo','strategy':'rsi'}).json()
    run=storage.get_run(r['run_id']);c=run['payload']['snapshot']['metrics']['cartridge']
    assert c['id']=='rsi' and c['version']=='1.0.0'
    assert client.post('/api/runs/'+r['run_id']+'/resume',json={}).status_code==200
    c['version']='different';storage.save_run('replay',run['params'],run['payload'],run['id'])
    assert client.post('/api/runs/'+r['run_id']+'/resume',json={}).status_code==409
    assert storage.get_run(run['id'])['payload']['snapshot']['metrics']['cartridge']['version']=='different'
