from datetime import tzinfo, datetime,timedelta
from pytz import timezone, utc

# Download Settings
last_file = '20190524.zip'
default_timeout  = 60
download_retries = 8
paths = {
    'aws_path': './data/awsloader',
    'bin_path': './data/bins'
    }

# Coordinates and grid
bbox_min = (-119, 33)
bbox_max = (-117, 35)
grid_size = 512

# Topic Settings
num_tokens = 30

# Time settings
local_tz = timezone('America/Los_Angeles')

# Bin settings
binsize = timedelta(days = 0, hours = 1, minutes = 0, seconds = 0)
first_bin = local_tz.localize(datetime(2019, 5, 25)).astimezone(utc)
def bin_name(utc_time):
    local_time = utc_time.astimezone(local_tz) 
    return '{}:00'.format(local_time.hour)
def bin_name_from_id(bin_id):
    return bin_name(first_bin + bin_id*binsize)

# Frame settings
framesize = timedelta(days = 0, hours = 6, minutes = 0, seconds = 0)
def frame_id(utc_time):
    local_time = utc_time.astimezone(local_tz) 
    #return local_time.day + local_time.month*100 + local_time.year*10000
    return local_time.day*10 + local_time.month*1000 + local_time.year*100000 + local_time.hour//6
def frame_name(utc_time):
    local_time = utc_time.astimezone(local_tz) 
    return '{},{}'.format(str(local_time.date()), local_time.hour//6)

# check sizes
if framesize%binsize != timedelta(0):
    raise ValueError('framesize must be divisible by binsize')

#def get_frame(time_obj):
#    local_time = time_obj.astimezone(local_tz) 
#    frame_id = (local_time.day + local_time.month*100 + local_time.year*10000) * 10
#    frame_name = str(local_time.date())
#    if local_time.hour < 12:
#        frame_name += ' Morning'
#    else:
#        frame_id += 1
#        frame_name += ' Afternoon'
#    return {'id': frame_id, 'name': frame_name}
    
#def get_frame(time_obj):
#    local_time = time_obj.astimezone(local_tz) 
#    frame_id = (local_time.day + local_time.month*100 + local_time.year*10000) * 10
#    frame_name = str(local_time.date())
#    if local_time.hour < 8:
#        frame_name += ' Morning'
#    elif local_time.hour < 16:
#        frame_id += 1
#        frame_name += ' Noon'
#    else:
#        frame_id += 2
#        frame_name += ' Evening'
#    return {'id': frame_id, 'name': frame_name}