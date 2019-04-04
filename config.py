from datetime import tzinfo, datetime,timedelta
from pytz import timezone, utc

# Download Settings
last_file = '20190120.zip'
default_timeout  = 60
download_retries = 8

# Time settings
local_tz = timezone('America/Los_Angeles')

# Bin settings
binsize = timedelta(days = 0, hours = 1, minutes = 0, seconds = 0)
first_bin = local_tz.localize(datetime(2019, 1, 21)).astimezone(utc)
binpath = './data/bins/'

# Frame settings
framesize = timedelta(days = 1, hours = 0, minutes = 0, seconds = 0)
def get_frame(utc_time):
    local_time = utc_time.astimezone(local_tz) 
    frame_id = local_time.day + local_time.month*100 + local_time.year*10000
    frame_name = str(local_time.date())
    return {'id': frame_id, 'name': frame_name}
    
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