import os
from datetime import datetime
from datetime import timedelta
from herbie import Herbie
import xarray as xr
import logging
import warnings

warnings.filterwarnings('ignore')
CYCLING_INTERVAL = timedelta(seconds=3600)
EPSILON = timedelta(seconds=5)
searchString = '(:[U|V]GRD:10 m|:MSLMA:)'
logger = logging.getLogger('hrrr')

def download(cfg, cycle, bbox=[], combine=False, output_dir='./'):
    now = cycle
    end = cycle + timedelta(hours=cfg['length'])
    date_set = set()
    while now < end + EPSILON:
        date_set.add(now.strftime('%Y-%m-%d %H:%M'))
        now += CYCLING_INTERVAL
    date_list = list(date_set)
    date_list.sort()
    if not date_list:
        logger.warning('Nothing to do! Exiting.')
        exit(1)
    file_set = set()
    for date in date_list:
        try:
            ofile = get(date, cfg, bbox, output_dir)
            file_set.add(ofile)
        except Exception as ex:
            logger.error(f'Download failed for {date}: {ex}', exc_info=ex)
    file_list = list(file_set)
    file_list.sort()
    if combine:
        ds = xr.open_mfdataset(file_list, combine='nested', concat_dim='time')
        ofile = os.path.join(output_dir, 'combined.nc')
        ds.to_netcdf(ofile)
        return ofile
    else:
        return file_list

def get(date, cfg, bbox, output_dir):
    if cfg['source'].lower() == 'hrrr':
        H = Herbie(date=date, model='hrrr', product='sfc', fxx=cfg['fxx'], save_dir=output_dir)
    elif cfg['source'].lower() == 'gfs':
        H = Herbie(date=date, model='gfs', fxx=cfg['fxx'], save_dir=output_dir)
    lfile = H.download(search=searchString)
    if os.path.isfile(lfile):
        dirname = os.path.dirname(lfile)
        ofile = os.path.join(dirname, datetime.strptime(date, '%Y-%m-%d %H:%M').strftime('%Y%m%d_%Hz') + '.nc')
        ds = xr.open_dataset(lfile, engine='cfgrib')
        if not bbox:
            logger.info('Skip subsetting data ...')
            ds.to_netcdf(ofile)
        else:
            logger.info('Subset data based on given bounding box {}'.format(bbox))
            logger.error('This is not supported currently')
    return ofile
