#!/usr/bin/env python

import os
import sys
import time
import datetime
import json
import itertools

PARMSPATH = '/DPA/ewok/dpa/projects/eclipse/rnd/oceansurface/gilliganTest/python/parms/waveShape/swell_wedge'
WAVESCRIPT = '/DPA/ewok/dpa/projects/eclipse/rnd/oceansurface/gilliganTest/python/waveShape.py'
OUTPUTPATH = '/DPA/ewok/dpa/projects/eclipse/rnd/oceansurface/gilliganTest/results'

QUEUE = "brie"
frange = "1-120"
wedge_num = 0

# demo value: "swell_waves": {"travel": 3.0, "cuspscale": 3.0, "depth": 10.0, "longest": 1000.0, "typicalheight": 0.5405405405405405, "align": 8.0, "shortest": 4.0}
parm_value = [('typicalheight', [0.1, 0.9]),
              ('travel', [3.0]),
              ('align', [8.0]),
              ('cuspscale', [0.0, 0.75 * 6]),
              ('longest', [10.0, 1000.0]),
              ('shortest', [0.25, 4.0]),
              ('depth', [10])]


# create dir
timestamp = time.time()
dates = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d-%H-%M-%S')
folder_name = "swell_wedge-{}".format(dates)
# create parent folder
parent_path = os.path.join(OUTPUTPATH, folder_name)
script_dir = os.path.join(parent_path, 'script')
output_dir = os.path.join(parent_path, 'products')
parms_dir = os.path.join(parent_path, 'parms')
os.system("mkdir {}".format(parent_path))
# create parms folder
os.system("mkdir {}".format(parms_dir))
# create script path
os.system("mkdir {}".format(script_dir))
# create output path and sub path
os.system("mkdir {}".format(output_dir))
os.system("mkdir {}/images".format(output_dir))
os.system("mkdir {}/oceanmesh".format(output_dir))
os.system("mkdir {}/sim".format(output_dir))
os.system("mkdir {}/ewave_source".format(output_dir))
# chmod
os.system("chmod -R 770 {}".format(parent_path))


def wave_shape_parms_generator():
    parms_dict = dict()
    swell_waves_dict = dict()
    pm_waves_dict = dict()

    # generate swell parms
    parms_tuple_list = list(itertools.product(parm_value[0][1],
                                              parm_value[1][1],
                                              parm_value[2][1],
                                              parm_value[3][1],
                                              parm_value[4][1],
                                              parm_value[5][1],
                                              parm_value[6][1]))

    i = 0
    for parms_tuple in parms_tuple_list:
        for id in xrange(len(parm_value)):
            swell_waves_dict[parm_value[id][0]] = parms_tuple[id]

        parms_dict['swell_waves'] = swell_waves_dict
        parms_dict['pm_waves'] = pm_waves_dict

        parms_file_path = os.path.join(parms_dir, 'swell_wedge_parms_{num}.json'.format(num=i))
        with open(parms_file_path, 'w') as jsonfile:
            json.dump(parms_dict, jsonfile)
        i += 1

    wedge_num = len(parms_tuple_list)


def submit_task():
    # create script
    for root, dirs, files in os.walk(parms_dir):
        for parm_file in files:
            script_name = 'submit_{file}.sh'.format(file=parm_file.split('.')[0])
            filepath = os.path.join(script_dir, script_name)
            f = open(filepath, 'w')
            f.write("#!/bin/bash\n")
            f.write("export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/DPA/wookie/dpa/projects/eclipse/share/gilligan/3rdparty/3rdbuild/lib/\n")
            f.write("{exe} {parm}\n".format(exe=WAVESCRIPT,
                                            parm="-wn hand02_tri "
                                                 "-pn {prod} "
                                                 "-ap /DPA/ewok/dpa/projects/eclipse/rnd/oceansurface/gilliganTest/testAss/ "
                                                 "-pp {prodfile} "
                                                 "-f {frange} "
                                                 "-p {parmfile}".format(frange=frange,
                                                                        parmfile=os.path.join(root, parm_file),
                                                                        prodfile=output_dir,
                                                                        prod=parm_file.split('.')[0])))
            f.close()
            # chmod for script file
            os.system("chmod 777 {file}".format(file=filepath))

    print "Scripts generation complete."
    print '-' * 100

    # submit task
    num = 0
    for root, dirs, files in os.walk(script_dir):
        for name in files:
            script_path = os.path.join(root, name)
            # there's .log file in the same dir
            if script_path.endswith('.sh'):
                print "Submit task for script {}...".format(script_path)
                os.system("cqsubmittask {queue} {script}".format(queue=QUEUE, script=script_path))
                num += 1

    print "Submission complete."
    print "\t | Task Num: ", num

wave_shape_parms_generator()
submit_task()
