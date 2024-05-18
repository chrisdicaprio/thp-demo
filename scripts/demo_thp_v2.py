import os
from nzshm_common.location.location import get_locations
from thp_demo.curves_v4 import get_hazard as get_hazard_v4, ArrowFS
from thp_demo.plotting_functions import plot_hazard_curve
import matplotlib.pyplot as plt

resolution = 0.001
INVESTIGATION_TIME = 50
PLOT_WIDTH = 12
PLOT_HEIGHT = 8.625
colors = ['k', '#1b9e77', '#d95f02', '#7570b3']
xscale = 'log'
xlim = [1e-2,5]
# xlim = [0,3]
ylim = [1e-6,1]


def ref_lines(poes):
    refls = []
    for poe in poes:
        ref_line = dict(type = 'poe',
                        poe = poe,
                        inv_time = INVESTIGATION_TIME)
        refls.append(ref_line)
    return refls


error_bounds = {'lower2':'0.01','lower1':'0.1','upper1':'0.9','upper2':'0.99'}
aggs = list(error_bounds.values()) + ['mean']

location_codes = ["WLG"]
locations = get_locations(location_codes)

imts = ["PGA"]
poes = [0.1, 0.02]
fs_specs = dict(
    arrow_fs=ArrowFS.LOCAL,
    arrow_dir=os.getenv('THP_THS_AGG_LOCAL_DIR')
)

model_ids = ['NSHM_2022_DEMO', 'HIGHEST_WEIGHT', 'CRUSTAL_ONLY']
# model_ids = ['NSHM_2022_DEMO', 'CRUSTAL_ONLY']
vs30 = 275

hazard_models = dict()
for model_id in model_ids:
    hazard_models[model_id] = get_hazard_v4(model_id, vs30, locations, imts, aggs, fs_specs)


for loc in locations:
    for imt in imts:
        fig, ax = plt.subplots(1,1)
        fig.set_size_inches(PLOT_WIDTH,PLOT_HEIGHT)
        fig.set_facecolor('white')
        title = f'{loc} {imt}, Vs30 = {vs30}m/s'
        for i, (model_id, hazard) in enumerate(hazard_models.items()):
            lh, levels = plot_hazard_curve(
                hazard, loc, imt, ax, xlim, ylim,
                xscale=xscale,central='mean',
                ref_lines=ref_lines(poes),
                color=colors[i],
                custom_label=model_id,
                title=title,
                bandw=error_bounds
            )
        plt.show()