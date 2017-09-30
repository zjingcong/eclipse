#!/usr/bin/env python
# arnoldRenderToTexture -f "/DPA/wookie/dpa/projects/eclipse/rnd/test/fx/oceanwetmap/maya/project"
# -r 512 -af "gaussian" -afw 2.0 -as 3;

import os
import time
import datetime

# path
MAYAFILE = '/DPA/wookie/dpa/projects/eclipse/rnd/test/fx/oceanwetmap/maya/wetmap.ma'
OUTPUTPATH = '/DPA/wookie/dpa/projects/eclipse/rnd/prods/wetMap'

# setting
start = 1
end = 120
resolution = 4096
object_name = 'float_1'  # object need to export
prod_name = 'float_1'
QUEUE = 'brie'

# ---------------------------------------------------------------------------------------------------------------

# create prod
object_prod_path = os.path.join(OUTPUTPATH, prod_name)
for root, dirs, files in os.walk(OUTPUTPATH):
    if root == OUTPUTPATH:
        if prod_name not in dirs:
            os.system("mkdir {}".format(object_prod_path))
            os.system("chmod -R 770 {}".format(object_prod_path))
        break

# create dir
timestamp = time.time()
dates = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d-%H-%M-%S')
folder_name = "{name}-{date}".format(name=prod_name, date=dates)
# create parent folder
parent_path = os.path.join(object_prod_path, folder_name)
# create script path
script_dir = os.path.join(parent_path, 'script')
# create nuke path
nuke_dir = os.path.join(parent_path, 'nuke')
# create products path
output_dir = os.path.join(parent_path, 'products')
# create mel path
mel_dir = os.path.join(parent_path, 'mel')
# create tmp frame folder for each frame
frame_dir = os.path.join(output_dir, 'tmp_{f:04}')

# mkdir
os.system("mkdir {}".format(parent_path))
os.system("mkdir {}".format(mel_dir))
os.system("mkdir {}".format(script_dir))
os.system("mkdir {}".format(nuke_dir))
os.system("mkdir {}".format(output_dir))
for frame_num in xrange(start, end + 1):
    os.system("mkdir {}".format(frame_dir.format(f=frame_num)))

# chmod
os.system("chmod -R 770 {}".format(parent_path))

# name convention
mel_name = 'wet2Tex_{}'.format(prod_name)
obj_name = prod_name
shell_name = 'batchWet2Tex_{}'.format(prod_name)


# create MEL scripts
def create_mel():
    for frame_num in xrange(start, end + 1):
        mel_file = '{mel}.{f:04}.mel'.format(mel=mel_name, f=frame_num)
        filepath = os.path.join(mel_dir, mel_file)
        frame_folder = frame_dir.format(f=frame_num)
        # write MEL script
        f = open(filepath, 'w')
        f.write("select {name};\n".format(name=object_name))  # select water surface to export
        f.write("currentTime {f};\n".format(f=frame_num))   # select frame number
        f.write(
            "arnoldRenderToTexture -f \"{framef}\" -r {r} -af \"gaussian\" -afw 2.0 -as 3;".format(framef=frame_folder,
                                                                                                   r=resolution))
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

if __name__ == '__main__':
    # exporting things
    print "Exporting {} to texture...".format(prod_name)
    if create_mel() and create_shell():
        print '-' * 100
        submit_task()
