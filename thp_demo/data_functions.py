import numpy as np

def rp_from_poe(poe, inv_time):

    return -inv_time/np.log(1-poe)


def poe_from_rp(rp, inv_time):

    return 1 - np.exp(-inv_time/rp)