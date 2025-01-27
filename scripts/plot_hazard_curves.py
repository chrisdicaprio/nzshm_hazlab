import os
from pathlib import Path
from nzshm_common.location.location import LOCATION_LISTS, location_by_id
from nzshm_common.location import CodedLocation
from nzshm_hazlab.store.curves import get_hazard, get_hazard_from_oqcsv
from nzshm_hazlab.plotting_functions import plot_hazard_curve
import matplotlib.pyplot as plt
from typing import Any

from nzshm_hazlab.locations import get_locations, lat_lon

CODED_LOCS = [CodedLocation(*lat_lon(key), 0.001) for key in LOCATION_LISTS["ALL"]["locations"]]

resolution = 0.001
INVESTIGATION_TIME = 50
PLOT_WIDTH = 12
PLOT_HEIGHT = 8.625
# colors = ['black', '#1b9e77', '#d95f02', '#7570b3','k']
colors = ['black', 'tab:orange', 'tab:green', 'tab:red', 'tab:blue']

xscale = 'log'
xlim = [1e-2,5]
# xlim = [0, 3.5]
# xlim = [0,3]
ylim = [1e-4,1]

def plot_diff(model0, model1, loc, imt, ax):

    lat, lon = loc.code.split('~')
    m0 = model0[(model0['lat'] == lat) & (model0['lon'] == lon) & (model0['imt'] == imt) & (model0['agg'] == 'mean')]
    m1 = model1[(model0['lat'] == lat) & (model1['lon'] == lon) & (model1['imt'] == imt) & (model1['agg'] == 'mean')]

    x = m0['level'].to_numpy()
    y0 = m0['apoe'].to_numpy()
    y1 = m1['apoe'].to_numpy()
    breakpoint()
    ax.plot(x,(y1-y0)/y0)
    ax.grid(color='lightgray')
    ax.set_xscale('log')


def location_2_dict(loc: CodedLocation) -> str:

    if loc in CODED_LOCS:
       ind = CODED_LOCS.index(loc)
       return location_by_id(LOCATION_LISTS["ALL"]["locations"][ind])
    return dict(
        id=loc.code,
        name=loc.code,
        latitude=loc.lat,
        longitude=loc.lon,
    )
    

def ref_lines(poes):
    refls = []
    for poe in poes:
        ref_line = dict(type = 'poe',
                        poe = poe,
                        inv_time = INVESTIGATION_TIME)
        refls.append(ref_line)
    return refls






error_bounds = {'lower2':'0.025','lower1':'0.1','upper1':'0.9','upper2':'0.975'}
# error_bounds = {}
aggs = list(error_bounds.values()) + ['mean']

hazard_models = [
    # dict(id='NSHM_v1.0.4_ST_crubhi_iso', name='CRU b high'),
    # dict(id='NSHM_v1.0.4_ST_geologic_iso', name='Geologic'),
    # dict(id='NSHM_v1.0.4_ST_geodetic_iso', name='Geodetic'),
    # dict(id='TEST_ARRAY_COUNT', name='new array counting'),
    # dict(id='TEST_32BIT_FIX', name='32bit storage'),
    dict(id='NSHM_v1.0.4', name='v1.0.4'),
    dict(id='TEST', name='TEST'),
    # dict(id='oq_output-/home/chrisdc/NSHM/DATA/WEL_250_Matt/hazard_curve-rlz-000-IMT_739.csv', name='rlz0', agg='rlz000'),
    # dict(id='oq_output-/home/chrisdc/NSHM/DATA/WEL_250_Matt/hazard_curve-rlz-001-IMT_739.csv', name='rlz0', agg='rlz001'),
    # dict(id='oq_output-/home/chrisdc/NSHM/DATA/WEL_250_Matt/hazard_curve-rlz-002-IMT_739.csv', name='rlz0', agg='rlz002'),
    # dict(id='oq_output-/home/chrisdc/NSHM/DATA/WEL_250_Matt/hazard_curve-rlz-003-IMT_739.csv', name='single model branch', agg='rlz003'),
]

# location_codes = ["TP"]
# locations = get_locations(location_codes)[0:1] + get_locations(["-44.3~170.8"])
# location_codes = ["WLG", "DUD", "CHC", "AKL"]
# location_codes = ["/home/chrisdc/NSHM/oqruns/RUNZI-MAIN-HAZARD/WeakMotionSiteLocs_SHORT.csv"]
# location_codes = ["-42.311~172.218", "-38.826~177.536", "-38.262~175.010"]
# location_codes = ["WLG"]
location_codes = ["-34.500~173.000"]
locations = get_locations(location_codes)

imts = ["PGA", "SA(1.0)"]
poes = [0.1, 0.02]
vs30s = [275]
no_cache = True
fig_dir = Path('/home/chrisdc/NSHM/oqresults/32bit')
save_figs = False

if no_cache and os.environ.get('NZSHM22_HAZARD_STORE_LOCAL_CACHE'):
    del os.environ['NZSHM22_HAZARD_STORE_LOCAL_CACHE']

for model in hazard_models:
    model['hcurves'] = {}
    for vs30 in vs30s:
        if 'oq_output' in model['id']:
            model['hcurves'][vs30] = get_hazard_from_oqcsv(model['id'].replace('oq_output-', ''), imts)
        else:
            model['hcurves'][vs30] = get_hazard(model['id'], vs30, locations, imts, aggs)


for loc in locations[0:3]:
    loc_dict = location_2_dict(loc)
    loc_key, loc_name = loc_dict["id"], loc_dict["name"]
    for imt in imts:
        for vs30 in vs30s:
            fig, ax = plt.subplots(1,1)
            fig.set_size_inches(PLOT_WIDTH,PLOT_HEIGHT)
            fig.set_facecolor('white')
            # title = f'{loc_name} {imt}, Vs30 = {vs30}m/s'
            title = ''
            for i, model in enumerate(hazard_models):
                if 'oq_output' in model['id']:
                    error_bounds_tmp = dict()
                    agg = model['agg']
                    linestyle = '-'
                else:
                    error_bounds_tmp = error_bounds
                    agg = 'mean'
                    linestyle = '-'
                plot_hazard_curve(
                    model['hcurves'][vs30], loc, imt, ax, xlim, ylim,
                    xscale=xscale,
                    central=agg,
                    ref_lines=ref_lines(poes),
                    color=colors[i],
                    custom_label=model['name'],
                    title=title,
                    bandw=error_bounds_tmp,
                    linestyle=linestyle,
                )

            # fname = f'{location_name}_{imt}_{vs30}.png' 
            if save_figs:
                fname = f'{loc_key}_{imt}_{vs30}.png' 
                fig.savefig(Path(fig_dir, fname))
                plt.close()
            else:
                plt.show()

        # fix, ax = plt.subplots(1,1)
        # plot_diff(hazard_models[0]['hcurves'], hazard_models[1]['hcurves'], loc, imt, ax)
