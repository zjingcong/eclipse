
import os
import pymel.core as pm

# path
OBJPATH = '/DPA/wookie/dpa/projects/eclipse/rnd/prods/waterThing'


def get_inputs():
    inputs = raw_input('Please type obj name and frange: <name>_<start>:<end>\n')
    object_name = inputs.split('_')[0].strip(' ')
    frange = inputs.split('_')[1]
    start = frange.split(':')[0].strip(' ')
    end = frange.split(':')[1].strip(' ')

    return object_name, start, end


def export(object_name, start, end):
    # select to export
    select_poly_list = pm.ls(selection=True)
    poly_num = len(select_poly_list)
    # triangulate
    for i in xrange(poly_num):
        poly_name = str(select_poly_list[i])
        pm.polyTriangulate(poly_name)
    # select polygon
    pm.select(select_poly_list)
    # export to obj
    for time in xrange(int(start), int(end) + 1):
        pm.currentTime(time)
        obj_name = os.path.join(OBJPATH, '{name}_tri.{num:04}.obj'.format(name=object_name, num=time))
        pm.exportSelected(obj_name, type='OBJexport')


def clear(object_name):
    # chmod all the .obj files
    obj_name = os.path.join(OBJPATH, '{name}_tri.*.obj'.format(name=object_name))
    chmod_cmd = 'chmod 777 {file}'.format(file=obj_name)
    os.system(chmod_cmd)
    # rm all the .mtl files
    mtl_name = os.path.join(OBJPATH, '{name}_tri.*.mtl'.format(name=object_name))
    clear_cmd = 'rm -rf {file}'.format(file=mtl_name)
    os.system(clear_cmd)


def main():
    object_name, start, end = get_inputs()
    export(object_name, start, end)
    clear(object_name)

main()
