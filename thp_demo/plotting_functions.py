from pandas import DataFrame
import matplotlib
from matplotlib.pylab import Axes, Line2D
from typing import List, Dict
from nzshm_common.location import CodedLocation
from thp_demo.data_functions import rp_from_poe, poe_from_rp

matplotlib.use('TkAgg')


AXIS_FONTSIZE = 28
TICK_FONTSIZE = 22

def plot_hazard_curve(
        hazard_data: DataFrame,
        location: CodedLocation,
        imt: str,
        ax: Axes,
        xlim: List[float],
        ylim: List[float],
        central: str ='mean',
        bandw: Dict[str,str] = {},
        ref_lines: List[dict] = [],
        quants: List[str] = [],
        xscale: str ='log',
        custom_label: str = '',
        color: str = '',
        title: str = '',
        linestyle: str = '-'
) -> List[Line2D]:
    
    lat, lon = location.code.split('~')

    hd_filt = hazard_data.loc[ (hazard_data['imt'] == imt) & (hazard_data['lat'] == lat) & (hazard_data['lon'] == lon)]

    levels = hd_filt.loc[ hazard_data['agg'] == central]['level'].iloc[0]
    values = hd_filt.loc[ hazard_data['agg'] == central]['apoe'].iloc[0]

    clr = color if color else 'k'

    label = custom_label if custom_label else central
    lh, = ax.plot(levels,values,color=clr,lw=3,label=label, linestyle=linestyle)

    clr = color if color else 'b'
    alpha1 = 0.25
    alpha2 = 0.8
    if bandw: #{'u1':'0.8,'u2':'0.95', ...}
        
        bandw_data = {}
        for k,v in bandw.items():
            values = hd_filt.loc[ hazard_data['agg'] == v]['apoe'].iloc[0]
            bandw_data[k] = values
        
        ax.fill_between(levels, bandw_data['upper1'], bandw_data['lower1'],alpha = alpha1, color=clr)
        ax.plot(levels, bandw_data['upper2'],color=clr,lw=1)
        ax.plot(levels, bandw_data['lower2'],color=clr,lw=1)
        # ax.plot(levels, bandw_data['upper2'],linestyle='--',color=clr,lw=1)
        # ax.plot(levels, bandw_data['lower2'],linestyle='--',color=clr,lw=1)
        # ax.plot(levels, bandw_data['upper1'],color=clr,lw=2)
        # ax.plot(levels, bandw_data['lower1'],color=clr,lw=2)
    if quants:
        for quant in quants:
            levels = hd_filt.loc[ hazard_data['agg'] == quant]['level'].iloc[0]
            values = hd_filt.loc[ hazard_data['agg'] == quant]['apoe'].iloc[0]
            ax.plot(levels,values,'b',alpha=alpha2,lw=1,label=quant)


    for ref_line in ref_lines:
        if ref_line['type'] == 'poe':
            poe = ref_line['poe']
            inv_time = ref_line['inv_time']
            rp = rp_from_poe(poe, inv_time)
        elif ref_line['type'] == 'rp':
            inv_time = ref_line['inv_time']
            rp = ref_line['rp']
            poe = poe_from_rp(poe, inv_time)

        text = f'{poe*100:.0f}% in {inv_time:.0f} years (1/{rp:.0f})'
        
        _ = ax.plot(xlim,[1/rp]*2,ls='--',color='dimgray',zorder=-1)
        # _ = ax.annotate(text, [xlim[1],1/rp], ha='right',va='bottom')
        if xscale == 'log':
            _ = ax.annotate(text, [xlim[0],1/rp], ha='left',va='bottom', fontsize=TICK_FONTSIZE*0.8)
        else:
            _ = ax.annotate(text, [xlim[1],1/rp], ha='right',va='bottom', fontsize=TICK_FONTSIZE*0.8)

    # if not bandw:
    _ = ax.legend(handlelength=2)

    if xscale == 'log':
        _ = ax.set_xscale('log')
    _ = ax.set_yscale('log')
    _ = ax.set_ylim(ylim)
    _ = ax.set_xlim(xlim)
    _ = ax.set_xlabel('Shaking Intensity, %s [g]'%imt, fontsize=AXIS_FONTSIZE)
    _ = ax.set_ylabel('Annual Probability of Exceedance', fontsize=AXIS_FONTSIZE)
    _ = ax.tick_params(axis='both', which='major', labelsize=TICK_FONTSIZE)
    _ = ax.grid(color='lightgray')  

    if title:
        ax.set_title(title)

    return lh, levels

            
