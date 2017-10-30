#!/usr/bin/python

import os
import sys
import math
import argparse
import json

# os.environ['LD_LIBRARY_PATH'] = ':/DPA/wookie/dpa/projects/eclipse/share/gilligan/3rdparty/3rdbuild/lib/'
sys.path.append('/DPA/wookie/dpa/projects/eclipse/share/')

import gilligan.thurston.scene as scene
import gilligan.thurston.sim.ewavesim as ewsim
import gilligan.thurston.sim.wavemesh as simmesh
import gilligan.thurston.sim.wavemerge as simmerge
import gilligan.thurston.sim.wavesurfersim as wssim
import gilligan.thurston.sim.updates
import gilligan.thurston.parameter.thirsty as thirsty
import gilligan.thurston.parameter as param
import gilligan.thurston.util as util
from gilligan.thurston.logging import LogIt, beginJob, endJob
import gilligan.thurston.geometry.polygonal as poly
import gilligan.thurston.geometry.mesh as gmesh
import gilligan.thurston.camera as cam
import gilligan.thurston.colors as colors


# ------------------------ pre-setting -------------------------
WATERTHING = ""
PRODNAME = ""
PRODUCTSPATH = ""
LLC = ""
PATCHSIZE = ""
SIMSTART = 1

# to match maya displacement map setting
swell_typicalheight_mult = 1.0
swell_cuspscale_mult = 1.0
# for ewave simulation
time_offset = 0
ewave_capillary = 0.015
ewave_trimalpha = 0.05

# -------------------------------------------------------


def CreateWaterSims(name, wave_parms, ewave_llc, ewave_patch_size):
    simscene = scene.Scene(name)

    swell_waves = wssim.WaveSurferSim('swell_waves')
    swell_waves.set('oceantype', 'str("ochi")' )
    swell_waves.set('patchsize', '[ 4000.0, 4000.0 ]' )
    swell_waves.set('patchnxny', '[ 2048, 2048 ]' )

    swell_waves.set('typicalheight', wave_parms.get('swell_waves').get('typicalheight') * swell_typicalheight_mult)
    swell_waves.set('cuspscale', wave_parms.get('swell_waves').get('cuspscale') * swell_cuspscale_mult)

    swell_waves.set('travel', wave_parms.get('swell_waves').get('travel') )
    swell_waves.set('align', wave_parms.get('swell_waves').get('align') )
    swell_waves.set('direction', 90.0 )
    swell_waves.set('longest', wave_parms.get('swell_waves').get('longest') )
    swell_waves.set('shortest', wave_parms.get('swell_waves').get('shortest') )
    swell_waves.set('depth', wave_parms.get('swell_waves').get('depth') )
    swell_waves.generate_object()
    simscene.add_sim(swell_waves)
    
    pm_waves =  wssim.WaveSurferSim('small_waves')
    pm_waves.set('oceantype', 'str("deep")' )
    pm_waves.set('patchsize', '[ 30.0, 30.0 ]' )
    pm_waves.set('patchnxny', '[ 1024, 1024 ]' )
    pm_waves.set('typicalheight', 0.2 )
    pm_waves.set('direction', 0.0 )
    pm_waves.set('longest',  10.0 )
    pm_waves.set('shortest', 0.013 )
    pm_waves.set('cuspscale',  0.75*0.5 )
    # pm_waves.set('cuspscale',  '0.75*0.5*(thirsty.F-1.0)/3.0' )
    pm_waves.generate_object()
    simscene.add_sim(pm_waves)

    ewave_waves = ewsim.eWaveSim('thing_in_water_waves')
    # get patch nx ny according ewave patch size
    patch_x = float(ewave_patch_size.split(',')[0].strip('['))
    patch_y = float(ewave_patch_size.split(',')[1].strip(']'))
    if patch_x == max(patch_x, patch_y):
        patch_nx = 1024
        patch_ny = int((1024 * patch_y) / patch_x)
    else:
        patch_ny = 1024
        patch_nx = int((1024 * patch_x) / patch_y)
    patchnxny = str([patch_nx, patch_ny])

    ewave_waves.set('patchnxny', patchnxny )
    # ewave_waves.set('patchsize', '[ 40.0,20.0 ]' )
    ewave_waves.set('patchsize', ewave_patch_size)
    # ewave_waves.set('llc', '[ -20.0, 0.0 ]' )
    ewave_waves.set('llc', ewave_llc)
    ewave_waves.set('gravity',  9.8 )
    ewave_waves.set('depth', 10.0 )
    ewave_waves.set('displacementscale', 0.3 )
    ewave_waves.set('dohorizontal', True)
    ewave_waves.set('sourcescale', 1.0 )
    ewave_waves.set('ambientscale', 0.75*0.3 )

### ewave parms
    # ewave_waves.set('capillary', 0.015)
    # ewave_waves.set('trimfraction', 0.1)
    # ewave_waves.set('trimalpha', 0.05)
    ewave_waves.set('capillary', ewave_capillary)
    ewave_waves.set('trimfraction', 0.1)
    ewave_waves.set('trimalpha', ewave_trimalpha)

    ewave_waves.set('compute_whitecaps', False)

    ewave_waves.generate_object()
    simscene.add_sim(ewave_waves)

    return simscene


def RetrieveThingInWater(f):
    thing_in_water_path = '{name}.{frame}.obj'.format(name=WATERTHING, frame=util.formattedFrame(f))
    thing_in_water = poly.Polygonal('thing_in_water')
    thing_in_water.set('objpath', thing_in_water_path)
    thing_in_water.visible = True

    return thing_in_water


#
#######################################################################################
#######################################################################################
#######################################################################################
#


def sim(input_frange, wave_parms, ewave_llc, ewave_patch_size, simstart):
    beginJob()

    # thirsty.FPS = 30.0
    thirsty.FPS = 24.0
    timestep = 1.0/float( thirsty.FPS )

    import gilligan.thurston.frange as frange
    frame_range = frange.Frange(input_frange)

    thirsty.F = 1
    # thirsty.F = simstart

    simscene = CreateWaterSims('water floating', wave_parms, ewave_llc, ewave_patch_size)
    simscene.set('frame', 'thirsty.F' )


    simscene.generate_object()

    # Need to assemble basewave from swell and pm
    merged_ocean = simmerge.WaveMerge('base_ocean')
    merged_ocean.add_wave( simscene.get_sim('swell_waves') )
    merged_ocean.add_wave( simscene.get_sim('small_waves') )
    merged_ocean.generate_object()
    merged_ocean.verbose = True

    # update ocean for offset time
    # current_time = simstart - 1
    # merged_ocean.update(current_time + timestep * time_offset)
    merged_ocean.update(timestep * time_offset)

    ew = simscene.get_sim('thing_in_water_waves')
    sw = simscene.get_sim('swell_waves')
    pw = simscene.get_sim('small_waves')
    ew.verbose = True
    ew.set('surface_geom', merged_ocean)

    #
    #  Update ocean to current time
    #

    frame_list = frame_range.frames
    floatingThing_name = WATERTHING.split('/')[-1]

    # start_ewave_time = 1 + time_offset
    # start_ewave_time = simstart + time_offset
    for f in range(1, frame_range.end + 1):
    # for f in xrange(start_ewave_time, frame_range.end + 1):
        LogIt(__file__, colors.color_magenta + "\n\n********************************** F R A M E  " + str(f) + " *****************************************\n" + colors.color_white)
        thirsty.F = int(f)
        LogIt(__file__, colors.color_yellow + "\n\n\tS I M U L A T I O N\n" + colors.color_white)
        merged_ocean.update(timestep)

        obj_time = f
        if obj_time < simstart:
            obj_time = simstart

        water_thing = RetrieveThingInWater(obj_time)
        ew.set('height_source_geom', water_thing)
        ew.set('compute_height_source', True)
        ew.update(timestep)
        LogIt(__file__, colors.color_yellow + "\n\n\tS I M U L A T I O N   F I N I S H E D\n" + colors.color_white)
        if f in frame_list:
            ew.write_displacement(os.path.join(PRODUCTSPATH, 'sim/{name}_ewave_{waterthing}.{f}.exr'.format(name=PRODNAME, waterthing=floatingThing_name, f=util.formattedFrame(f))))

    endJob()


def get_argvs():
    parser = argparse.ArgumentParser(description="Wave parms setting.")
    parser.add_argument('-w', '--waterthing', type=str, dest='w', help='Input water thing path.',
                        default='/DPA/wookie/dpa/projects/eclipse/rnd/prods/waterThing/animfloat2_tri')
    parser.add_argument('-pn', '--prodname', type=str, dest='pn',
                        help='Input products name.', default='wave_floating')
    parser.add_argument('-pp', '--prodpath', type=str, dest='pp',
                        help='Input products path.',
                        default='/DPA/ewok/dpa/projects/eclipse/rnd/prods/waterDisplacement/default')
    parser.add_argument('-p', '--parms', type=str, dest='parms',
                        help='Input parms config path.',
                        default='/DPA/ewok/dpa/projects/eclipse/rnd/gilligan/python/parms/waveShape/test.json')
    # parser.add_argument('-llc', type=str, dest='llc', help='llc for ewave sim.', default='[ -20.0, -20.0 ]')
    # parser.add_argument('-patch', type=str, dest='patch', help='patch size for ewave sim.', default='[ 40.0, 40.0 ]')

    parser.add_argument('-f', '--frange', type=str, dest='f', help='Input frange.', default='1')

    # for maya custom ewave_patch
    parser.add_argument('-scale', type=str, dest='scale', help='Input Maya ewave patch scale.', default='[40.0, 40.0]')
    parser.add_argument('-trans', type=str, dest='trans', help='Input Maya ewave patch translate.', default='[0.0, 0.0]')
    parser.add_argument('-height', type=float, dest='height', help='Input Maya swell height mult parms.', default=1.0)
    parser.add_argument('-cusp', type=float, dest='cusp', help='Input Maya swell cuspscale mult parms',
                        default=1.0)
    parser.add_argument('-timeoffset', type=int, dest='timeoffset', help='Input Maya ewave simulation time offset',
                        default=0)
    parser.add_argument('-capillary', type=float, dest='capillary', help='Input Maya ewave simulation capillary',
                        default=0.015)
    parser.add_argument('-trimalpha', type=float, dest='trimalpha', help='Input Maya ewave simulation trimalpha',
                        default=0.05)
    parser.add_argument('-simstart', type=int, dest='simstart', help='Sim start time.')

    args = parser.parse_args()

    return args


if __name__ == '__main__':
    # cmdline parser
    args = get_argvs()
    WATERTHING = args.w
    PRODNAME = args.pn
    PRODUCTSPATH = args.pp
    # LLC = args.llc
    # PATCHSIZE = args.patch
    SIMSTART = args.simstart

    input_frange = args.f
    wave_parms_path = args.parms

    maya_ewave_patch_scale = args.scale
    maya_ewave_patch_trans = args.trans
    # get llc and patch size
    patch_scaleX = float(maya_ewave_patch_scale.split(',')[0].strip('['))
    patch_scaleZ = float(maya_ewave_patch_scale.split(',')[1].strip(']'))
    patch_transX = float(maya_ewave_patch_trans.split(',')[0].strip('['))
    patch_transZ = float(maya_ewave_patch_trans.split(',')[1].strip(']'))
    llc_x = patch_transX - (patch_scaleX * 0.5)
    llc_y = patch_transZ - (patch_scaleZ * 0.5)

    LLC = '[{x}, {y}]'.format(x=llc_x, y=llc_y)
    PATCHSIZE = maya_ewave_patch_scale

    print "ewave llc: ", LLC
    print "ewave patch size: ", PATCHSIZE

    # load parms
    wave_parms = dict()
    with open(wave_parms_path) as jsonfile:
        wave_parms = json.load(jsonfile)

    swell_cuspscale_mult = args.cusp
    swell_typicalheight_mult = args.height
    time_offset = args.timeoffset
    ewave_capillary = args.capillary
    ewave_trimalpha = args.trimalpha

    print "swell_cuspscale_mult: ", swell_cuspscale_mult
    print "swell_typicalheight_mult: ", swell_typicalheight_mult
    print "time_offset: ", time_offset
    print "ewave_capillary: ", ewave_capillary
    print "ewave_trimalpha: ", ewave_trimalpha
    print "simstart: ", SIMSTART

    # do simulation and export displacement map for swell/small/ewave sim
    sim(input_frange, wave_parms, LLC, PATCHSIZE, SIMSTART)
