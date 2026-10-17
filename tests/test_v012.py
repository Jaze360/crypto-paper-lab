import pandas as pd,pytest
from fastapi.testclient import TestClient
import app,universe,storage
from market_data import DataError

def market(i,cap=None,vol=None):
    return {'id':'coin-'+str(i),'name':'Coin '+str(i),'symbol':'c'+str(i),'market_cap':cap or 10000-i,'total_volume':vol or 1000-i,'market_cap_rank':i,'last_updated':'2026-10-17T16:00:00Z'}

def test_ranking_excludes_stable_wrapped_invalid_and_keeps_unmapped():
    rows=[market(i) for i in range(20)];rows[0]['id']='stable';rows[1]['name']='Wrapped BTC';rows[2]['total_volume']=None
    s=universe.select(rows,[{'id':'stable'}],10)
    assert len(s['selected'])==10 and len(s['excluded'])==3
    assert s['selected'][0]['id']=='coin-3'
    assert s['selected'][0]['score']==2 and s['selected'][0]['historical_symbol'] is None
    assert s['selected']==universe.select(list(reversed(rows)),[{'id':'stable'}],10)['selected']
    assert all(c['score']==c['cap_rank']+c['volume_rank'] for c in s['selected'])
    with pytest.raises(DataError):universe.select(rows,[],10)
    with pytest.raises(DataError):universe.select(rows,[{'id':'stable'}],7)
    with pytest.raises(DataError):universe.select(rows[:4],[{'id':'stable'}],5)

def test_volume_changes_the_combined_rank():
    rows=[market(i,10000-i,1000-i) for i in range(20)]
    rows[15]['total_volume']=1e9
    s=universe.select(rows,[{'id':'stable'}],10)
    changed=next(x for x in s['ranked_candidates'] if x['id']=='coin-15')
    assert changed['volume_rank']==1 and changed['score']==17
    assert universe.select(rows,[{'id':'stable'}],5)['selected']==s['selected'][:5]

def test_snapshot_preserves_acquisition_time_and_fails_without_live_or_cache(monkeypatch):
    raw={'markets':[market(i) for i in range(20)],'stablecoins':[{'id':'stable'}],'fetched_at':'2026-10-17T16:00:00Z'}
    monkeypatch.setattr(universe,'cache_get',lambda *a,**kw:raw)
    s=universe.snapshot(5);assert s['fetched_at']==raw['fetched_at']
    monkeypatch.setattr(universe,'cache_get',lambda *a,**kw:None)
    class Provider:key=None
    monkeypatch.setattr(universe,'CoinGeckoProvider',Provider)
    monkeypatch.setattr(universe.requests,'get',lambda *a,**kw:(_ for _ in ()).throw(universe.requests.ConnectionError()))
    with pytest.raises(DataError,match='geen verzonnen'):universe.snapshot(10)

@pytest.mark.parametrize('all_failed',[False,True])
def test_top_job_keeps_selection_errors_and_common_range(monkeypatch,all_failed):
    selected=universe.select([market(i) for i in range(20)],[{'id':'stable'}],5)
    selected['fetched_at']='2026-10-17T16:00:00Z'
    monkeypatch.setattr(app,'universe_snapshot',lambda size:selected)
    calls=[]
    def data(self,coin,days,interval,progress=None):
        calls.append((coin,days,interval))
        if all_failed or coin=='coin-1':raise DataError('Fixture: ontbrekend')
        times=pd.date_range(end=pd.Timestamp.now(tz='UTC').floor('4h')-pd.Timedelta(hours=4),periods=1400,freq='4h')
        return pd.DataFrame({'time':times})
    monkeypatch.setattr(app.HistoricalProvider,'candles',data)
    monkeypatch.setattr(app,'protocol_coin',lambda *a,**kw:{'notes':[]})
    monkeypatch.setattr(app,'summary',lambda d,p:{'coin':p.coin})
    request=app.ResearchJob(mode='top',universe_size=5)
    app._jobs['top-fixture']={'status':'running'};app.execute_job('top-fixture',request)
    state=app._jobs['top-fixture'];assert state['status']=='done'
    saved=storage.get_run(state['run_id'])['payload']
    assert saved['universe']==selected and len(saved['protocol_batch'])==5
    assert len(calls)==5 and all(x[1:]==(1095,240) for x in calls)
    assert len([x for x in saved['protocol_batch'] if x.get('error')])==(5 if all_failed else 1)
    assert [x['coin'] for x in saved['protocol_batch']]==[x['id'] for x in selected['selected']]

def test_top_count_request_is_bounded():
    client=TestClient(app.app)
    assert client.post('/api/research/jobs',json={'mode':'top','universe_size':7}).status_code==422
    assert client.get('/api/universe?size=100').status_code==422
