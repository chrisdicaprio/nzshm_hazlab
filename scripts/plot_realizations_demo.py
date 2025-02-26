from matplotlib.font_manager import font_scalings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import math
from nzshm_common.location.location import LOCATIONS_BY_ID
from nzshm_common.location.code_location import CodedLocation
from matplotlib.collections import LineCollection

def compute_hazard_at_poe(levels,values,poe,inv_time):

    rp = -inv_time/np.log(1-poe)
    haz = np.exp( np.interp( np.log(1/rp), np.flip(np.log(values)), np.flip(np.log(levels)) ) )
    return haz, 1/rp

def get_branch_inds(levels, branch_probs, target_prob, target_level, num_branches):
    
    nbranches = branch_probs.shape[0]
    dists = np.empty((nbranches,))
    min_dist = math.inf
    for i in range(nbranches):
        rlz_level, rlz_prob = compute_hazard_at_poe(levels,branch_probs[i,:],poe,inv_time)
        dists[i] = abs(rlz_level - target_level)
        # if dist < min_dist:
        #     nearest_rlz = i
        #     min_dist = dist
        #     nearest_level = rlz_level

    # return nearest_rlz
    sorter = np.argsort(dists)
    return sorter[:num_branches]


def get_branch_inds_heaviest(weights, num_branches):


    sorter = np.argsort(weights)

    return sorter[:num_branches]




def load_data(filepaths):

    dtype = {'lat':str,'lon':str}

    data = {}

    with open(source_branches_filepath,'r') as source_file:
        data['source_branches'] = json.load(source_file)

    with open(source_leaves_filepath,'r') as source_file:
        data['source_leaves'] = json.load(source_file)

    with open(grouped_source_leaves_filepath,'r') as source_file:
        data['grouped_source_leaves'] = json.load(source_file)

    data['weights'] = np.load(weights_filepath,allow_pickle=True)
    data['branch_probs'] = np.load(branch_probs_filepath,allow_pickle=True)
    data['agg_hcurves']  = pd.read_json(agg_filepath,dtype=dtype)

    return data


def get_agg_poe(agg_hcurves, location, imt, agg):
    pt = [(loc['latitude'], loc['longitude']) for loc in LOCATIONS_BY_ID.values() if loc['id']==location][0]
    ll = CodedLocation(*pt,0.001).downsample(point_res).code
    lat, lon = ll.split('~')

    levels = list(set(agg_hcurves['level']))
    levels.sort()
    levels = np.array(levels)

    apoe = agg_hcurves.loc[ (agg_hcurves['lat']==lat) & 
                            (agg_hcurves['lon']==lon) & 
                            (agg_hcurves['agg']==agg)  & 
                            (agg_hcurves['imt']==imt) , 'hazard'].to_numpy()

    return levels, apoe



agg_filepath = '/home/chrisdc/NSHM/oqresults/TAG_final/data/FullLT_allIMT_nz34_all_aggregates.json'
source_branches_filepath = '/home/chrisdc/NSHM/oqresults/TAG_final/data/realization_data/source_branches.json'
source_leaves_filepath = '/home/chrisdc/NSHM/oqresults/TAG_final/data/realization_data/source_leaves.json'
grouped_source_leaves_filepath = '/home/chrisdc/NSHM/oqresults/TAG_final/data/realization_data/grouped_source_leaves.json'
weights_filepath = '/home/chrisdc/NSHM/oqresults/TAG_final/data/realization_data/weights.npy'
branch_probs_filepath = '/home/chrisdc/NSHM/oqresults/TAG_final/data/realization_data/branch_probs.npy'

filepaths = dict(
    agg_filepath=agg_filepath,
    source_branches_filepath=source_branches_filepath,
    source_leaves_filepath=source_leaves_filepath,
    grouped_source_leaves_filepath=grouped_source_leaves_filepath,
    weights_filepath=weights_filepath,
    branch_probs_filepath=branch_probs_filepath
)

data = load_data(filepaths)

xlim = [1e-2,2e0]
ylim = [1e-5,1e-1]
imt = 'PGA'
location = 'AKL'
point_res = 0.001
poe = 0.1
inv_time = 50
agg = 'mean'
num_branches = 5000

levels, mean = get_agg_poe(data['agg_hcurves'],location, imt, 'mean')
levels, q0p5 = get_agg_poe(data['agg_hcurves'],location, imt, '0.5')
levels, q0p1 = get_agg_poe(data['agg_hcurves'],location, imt, '0.1')
levels, q0p9 = get_agg_poe(data['agg_hcurves'],location, imt, '0.9')
i = get_branch_inds_heaviest(data['weights'], num_branches)

fig, ax = plt.subplots(1,1)
fig.set_size_inches(12,11)
fig.set_facecolor('white')
segs = np.zeros((num_branches,29,2))
segs[:,:,0] = levels
segs[:,:,1] = data['branch_probs'][i,:]
line_segments = LineCollection(segs,linewidths=0.25,alpha=0.2)
c = list(range(num_branches))
ax.add_collection(line_segments)
plt.sci(line_segments) 

ax.plot(levels,mean,color='black',linestyle='-',lw=3,label='mean')
ax.plot(levels,q0p5,color='black',linestyle='--',lw=3,label='p50')
ax.plot(levels,q0p1,color='tab:orange',linestyle='--',lw=3,label='p10')
ax.plot(levels,q0p9,color='tab:orange',linestyle='--',lw=3,label='p90')
ax.set_xscale('log')
ax.set_yscale('log')
ax.grid(color='lightgray')
ax.set_xlim(xlim)
ax.set_ylim(ylim)
ax.set_xlabel('Acceleration (g)',fontsize=16)
ax.set_ylabel('Annual PoE',fontsize=16)
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
ax.legend()

plt.show()

