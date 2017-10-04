#!/usr/bin/env python
# nuke10 -F 3 -x export_wetmap.nk

import os
import time
import datetime

# path
NUKEFILE = '/DPA/ewok/dpa/projects/eclipse/rnd/prods/wetMap/float_1/export_wetmap_float_1.nk'
OUTPUTPATH = '/DPA/ewok/dpa/projects/eclipse/rnd/prods/wetMap/float_1'

# setting
start = 1
end = 120
prod_name = 'nukeQueue-{}'.format(NUKEFILE.split('/')[-1].split('.')[0])
QUEUE = 'cheezwhiz'

# ---------------------------------------------------------------------------------------------------------------

# create dir
timestamp = time.time()
dates = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d-%H-%M-%S')
script_dir = os.path.join(OUTPUTPATH, "{name}-{date}".format(name=prod_name, date=dates))
# mkdir
os.system("mkdir {}".format(script_dir))
# chmod
os.system("chmod -R 770 {}".format(script_dir))
# name convention
shell_name = prod_name


def create_shell():
    for frame_num in xrange(start, end + 1):
        shell_file = '{shell}.{f:04}.sh'.format(shell=shell_name, f=frame_num)
        shell_path = os.path.join(script_dir, shell_file)
        # write shell script
        f = open(shell_path, 'w')
        f.write("#!/bin/bash\n")
        f.write("nuke10 -F {frame} -x {nuke}".format(frame=frame_num, nuke=NUKEFILE))
        f.close()
        # chmod for script file
        os.system("chmod 777 {file}".format(file=shell_path))

    print "Shell scripts generation complete."
    return True


def submit_task():
    num = 0
    for frame_num in xrange(start, end + 1):
        shell_file = '{shell}.{f:04}.sh'.format(shell=shell_name, f=frame_num)
        shell_path = os.path.join(script_dir, shell_file)
        print "Submit task for script {}...".format(shell_path)
        os.system("cqsubmittask {queue} {script}".format(queue=QUEUE, script=shell_path))
        num += 1

    print "Submission complete."
    print "\t | Task Num: ", num

if __name__ == '__main__':
    # exporting things
    print "Nuke Batch render {}".format(prod_name)
    if create_shell():
        print '-' * 100
        submit_task()
