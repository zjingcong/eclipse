#!/usr/bin/env python

import os
import sys

folder = sys.argv[1]
product_path = os.path.join(os.getcwd(), folder, 'products')
print "Clean product path: ", product_path, '...'

for root, dir, files in os.walk(product_path, topdown=False):
    # clean tmp file
    if root == product_path:
        os.system("rm -rf {}".format(os.path.join(product_path, 'tmp*')))
    else:
        frame_id = root.split('/')[-1].split('_')[-1]
        img_name = files[0].split('.')[-2]
        img_tmp_path = os.path.join(root, files[0])
        img_path = os.path.join(product_path, '{name}.{f}.exr'.format(name=img_name, f=frame_id))
        os.system("cp {tmp} {new}".format(tmp=img_tmp_path, new=img_path))

print "Cleaning complete."
