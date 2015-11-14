import subprocess
from settings import *


# run ffprobe and returns number of frames
def calculate_duration_in_sec(path):
    filepath = path[len(DUMBPREFIX):]
    print(filepath)
    result = subprocess.Popen([FFPROBE_RUN_PATH, filepath], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    duration_string = [x.decode("utf-8") for x in result.stdout.readlines() if "Duration" in x.decode('utf-8')][-1]
    time = duration_string.replace(' ', '').split(',')[0].replace('Duration:', '').split(':')
    return int(time[0]) * 3600 + int(time[1]) * 60 + int(time[2].split('.')[0])


def get_frame_count(path):
    try:
        return PROJECT_TIMEBASE
    except NameError:
        filepath = path[len(DUMBPREFIX):]
        result = subprocess.Popen([FFPROBE_RUN_PATH, '-select_streams', 'v', '-show_streams', filepath],
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        frames = [x.decode("utf-8") for x in result.stdout.readlines() if "avg_frame_rate=" in x.decode('utf-8')][0]
        return frames


def calculate_duration(path):
    return calculate_duration_in_sec(path) * get_frame_count(path)


def make_unique(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]
