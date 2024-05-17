import math

from itertools import product
from typing import List, Tuple, Optional, Dict, Any
from nzshm_common.location import CodedLocation
from enum import Enum, auto

import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.compute as pc

from pyarrow import fs

try:
    import boto3
except ModuleNotFoundError:
    pass

imtls = np.array([
    0.0001, 0.0002, 0.0004, 0.0006, 0.0008,
    0.001, 0.002, 0.004, 0.006, 0.008,
    0.01, 0.02, 0.04, 0.06, 0.08,
    0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9,
    1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0
])

RESOLUTION = 0.001

class ArrowFS(Enum):
    LOCAL = auto()
    AWS = auto()

def get_local_fs(local_dir) -> Tuple[fs.FileSystem, str]:
    return fs.LocalFileSystem(), str(local_dir)


def get_s3_fs(region, bucket) -> Tuple[fs.FileSystem, str]:
    session = boto3.session.Session()
    credentials = session.get_credentials()
    filesystem = fs.S3FileSystem(
        secret_key=credentials.secret_key,
        access_key=credentials.access_key,
        region=region,
        session_token=credentials.token,
    )
    root = bucket
    return filesystem, root


def get_arrow_filesystem(
        fs_type: ArrowFS,
        aws_region: Optional[str] = None,
        local_dir: Optional[str] = None,
        s3_bucket: Optional[str] = None,
) -> Tuple[fs.FileSystem, str]:

    if fs_type is ArrowFS.LOCAL:
        filesystem, root = get_local_fs(local_dir)
    elif fs_type is ArrowFS.AWS:
        filesystem, root = get_s3_fs(aws_region, s3_bucket)
    else:
        filesystem = root = None
    return filesystem, root


def get_aggs_dataset(fs_specs):

    if fs_specs['arrow_fs'] == ArrowFS.LOCAL:
        filesystem, root = get_arrow_filesystem(ArrowFS.LOCAL, local_dir=fs_specs['arrow_dir'])
    elif fs_specs['arrow_fs'] == ArrowFS.AWS:
        filesystem, root = get_arrow_filesystem(ArrowFS.LOCAL, aws_region=fs_specs['aws_region'], s3_bucket=fs_specs['s3_bucket'])
    
    dataset = ds.dataset(root, format='parquet', filesystem=filesystem, partitioning='hive')
    return dataset

    

def get_hazard(
        hazard_id: str,
        vs30: int,
        locs: List[CodedLocation],
        imts: List[str],
        aggs: List[str],
        fs_specs: Dict[str, Any],
) -> pd.DataFrame:
    """download all locations, imts and aggs for a particular hazard_id and vs30."""

    dataset = get_aggs_dataset(fs_specs)

    loc_strs = [loc.downsample(RESOLUTION).code for loc in locs]
    naggs = len(aggs)
    nimts = len(imts)

    location = locs[0]
    imt = imts[0]
    nloc_001s = [loc.downsample(0.001).code for loc in locs]
    flt = (
        (pc.is_in(pc.field('agg'), pa.array(aggs)))
        & (pc.is_in(pc.field('imt'), pa.array(imts)))
        & (pc.is_in(pc.field('nloc_001'), pa.array(nloc_001s)))
        & (pc.field('vs30') == pc.scalar(vs30))
        & (pc.field('hazard_model_id') == pc.scalar(hazard_id))
    )
    columns = ['agg', 'values', 'vs30', 'imt', 'lat', 'lon']
    arrow_scanner = ds.Scanner.from_dataset(dataset, filter=flt, columns=columns)
    table = arrow_scanner.to_table()
    hazard_curves = table.to_pandas()
    hazard_curves[['lat', 'lon']] = hazard_curves[['lat', 'lon']].applymap(lambda x: '{0:.3f}'.format(x))
    hazard_curves['level'] = pd.NA
    for i in range(len(hazard_curves)):
        hazard_curves['level'].iloc[i] = imtls
    hazard_curves.rename({'values': 'apoe'}, axis='columns', inplace=True)

    return hazard_curves