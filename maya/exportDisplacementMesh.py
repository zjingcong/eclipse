#!/usr/bin/env python

import os
import time
import datetime

# path
MAYAFILE = '/DPA/wookie/dpa/projects/eclipse/rnd/test/fx/oceandisplacement/maya/displacement.ma'
OUTPUTPATH = '/DPA/wookie/dpa/projects/eclipse/rnd/prods/water_surface_obj'

# setting
start = 1
end = 2
surface_name = 'water_surface'
QUEUE = 'brie'

# ---------------------------------------------------------------------------------------------------------------

# create prod
surface_prod_path = os.path.join(OUTPUTPATH, surface_name)
for root, dirs, files in os.walk(OUTPUTPATH):
    if root == OUTPUTPATH:
        if surface_name not in dirs:
            os.system("mkdir {}".format(surface_prod_path))
            os.system("chmod -R 770 {}".format(surface_prod_path))
        break

# create dir
timestamp = time.time()
dates = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d-%H-%M-%S')
folder_name = "{name}-{date}".format(name=surface_name, date=dates)
# create parent folder
parent_path = os.path.join(surface_prod_path, folder_name)
# create script path
script_dir = os.path.join(parent_path, 'script')
# create products path
output_dir = os.path.join(parent_path, 'products')
# create mel path
mel_dir = os.path.join(parent_path, 'mel')

os.system("mkdir {}".format(parent_path))
os.system("mkdir {}".format(mel_dir))
os.system("mkdir {}".format(script_dir))
os.system("mkdir {}".format(output_dir))
# chmod
os.system("chmod -R 770 {}".format(parent_path))

# name convention
mel_name = 'dis2Mesh_{}'.format(surface_name)
obj_name = surface_name
shell_name = 'batchDis2Mesh_{}'.format(surface_name)


# create MEL scripts
def create_mel():
    for frame_num in xrange(start, end + 1):
        mel_file = '{mel}.{f:04}.mel'.format(mel=mel_name, f=frame_num)
        filepath = os.path.join(mel_dir, mel_file)
        obj_file = '{obj}.{f:04}.obj'.format(obj=obj_name, f=frame_num)
        objpath = os.path.join(output_dir, obj_file)
        # write MEL script
        f = open(filepath, 'w')
        f.write("select {name};\n".format(name=surface_name))  # select water surface to export
        f.write("currentTime {f};\n".format(f=frame_num))   # select frame number
        f.write("arnoldBakeGeo -f \"{obj}\";".format(obj=objpath))  # set obj file path
        f.close()
        # chmod for script file
        os.system("chmod 777 {file}".format(file=filepath))

    print "MEL scripts generation complete."
    return True


def create_shell():
    for frame_num in xrange(start, end + 1):
        shell_file = '{shell}.{f:04}.sh'.format(shell=shell_name, f=frame_num)
        shell_path = os.path.join(script_dir, shell_file)
        # corresponding MEL script
        mel_path = os.path.join(mel_dir, '{mel}.{f:04}.mel'.format(mel=mel_name, f=frame_num))
        # write shell script
        f = open(shell_path, 'w')
        f.write("#!/bin/bash\n")
        f.write("maya2016 -batch -file {maya} -script {script}".format(maya=MAYAFILE, script=mel_path))
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

# exporting things
print "Exporting {} displacement map to mesh obj file...".format(surface_name)
create_mel()
create_shell()
if create_mel() and create_shell():
    print '-' * 100
    submit_task()
