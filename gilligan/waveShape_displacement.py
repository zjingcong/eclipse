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
ASSPATH = ""
ASSNANE = ""
PRODNAME = ""
PRODUCTSPATH = ""
WRITEOBJ = True
# -------------------------------------------------------


def CreateWaterSims(name, wave_parms):
    simscene = scene.Scene(name)

    swell_waves = wssim.WaveSurferSim('swell_waves')
    swell_waves.set('oceantype', 'str("ochi")' )
    swell_waves.set('patchsize', '[ 4000.0, 4000.0 ]' )
    swell_waves.set('patchnxny', '[ 2048, 2048 ]' )
    # swell_waves.set('typicalheight', 2.0/3.7 )
    # swell_waves.set('travel', 3.0 )
    # swell_waves.set('align', 8.0 )
    # swell_waves.set('direction', 90.0 )
    # swell_waves.set('cuspscale', 0.75*4.0 )
    # swell_waves.set('longest', 1000.0 )
    # swell_waves.set('shortest', 4.0 )
    # swell_waves.set('depth', 10.0 )
    swell_waves.set('typicalheight', wave_parms.get('swell_waves').get('typicalheight') )
    swell_waves.set('travel', wave_parms.get('swell_waves').get('travel') )
    swell_waves.set('align', wave_parms.get('swell_waves').get('align') )
    swell_waves.set('direction', 90.0 )
    swell_waves.set('cuspscale', wave_parms.get('swell_waves').get('cuspscale') )
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

    return simscene

#
#######################################################################################
#######################################################################################
#######################################################################################
#


def sim(input_frange, wave_parms):
    beginJob()

    # thirsty.FPS = 30.0
    thirsty.FPS = 24.0
    timestep = 1.0/float( thirsty.FPS )

    import gilligan.thurston.frange as frange
    frame_range = frange.Frange(input_frange)

    thirsty.F = 1

    simscene = CreateWaterSims('water shape', wave_parms)
    simscene.set('frame', 'thirsty.F' )


    simscene.generate_object()

    # Need to assemble basewave from swell and pm
    merged_ocean = simmerge.WaveMerge('base_ocean')
    merged_ocean.add_wave( simscene.get_sim('swell_waves') )
    merged_ocean.add_wave( simscene.get_sim('small_waves') )
    merged_ocean.generate_object()
    merged_ocean.verbose = True

    sw = simscene.get_sim('swell_waves')
    pw = simscene.get_sim('small_waves')

    #
    #  Update ocean to current time
    #

    frame_list = frame_range.frames

    for f in range(1,frame_range.end+1):
        LogIt(__file__, colors.color_magenta + "\n\n********************************** F R A M E  " + str(f) + " *****************************************\n" + colors.color_white)
        thirsty.F = int(f)
        merged_ocean.update(timestep)
        if f in frame_list:
            sw.write_displacement(os.path.join(PRODUCTSPATH, 'sim/{name}_swell_wave.{f}.exr'.format(name=PRODNAME, f=util.formattedFrame(f))))
            pw.write_displacement(os.path.join(PRODUCTSPATH, 'sim/{name}_small_wave.{f}.exr'.format(name=PRODNAME, f=util.formattedFrame(f))))

    endJob()


def get_argvs():
    parser = argparse.ArgumentParser(description="Wave parms setting.")
    parser.add_argument('-wn', '--waterthingname', type=str, dest='wn',
                        help='Input water thing name.', default='hand02_tri')
    parser.add_argument('-pn', '--prodname', type=str, dest='pn',
                        help='Input products name.', default='waveShape')
    parser.add_argument('-ap', '--asspath', type=str, dest='ap',
                        help='Input ass file path.',
                        default='/DPA/ewok/dpa/projects/eclipse/rnd/gilligan/testAss')
    parser.add_argument('-pp', '--prodpath', type=str, dest='pp',
                        help='Input products path.',
                        default='/DPA/ewok/dpa/projects/eclipse/rnd/prods/waterDisplacement/default ')
    parser.add_argument('-p', '--parms', type=str, dest='parms',
                        help='Input parms config path.',
                        default='/DPA/ewok/dpa/projects/eclipse/rnd/gilligan/python/parms/waveShape/test.json')

    parser.add_argument('-f', '--frange', type=str, dest='f', help='Input frange.', default='1')
    parser.add_argument('-obj', '--objexport', dest='obj', action='store_true', default=False, help='Export to obj.')

    args = parser.parse_args()

    return args


if __name__ == '__main__':
    # cmdline parser
    args = get_argvs()
    ASSPATH = args.ap
    ASSNANE = args.wn
    PRODNAME = args.pn
    PRODUCTSPATH = args.pp
    WRITEOBJ = args.obj

    input_frange = args.f
    wave_parms_path = args.parms

    # load parms
    wave_parms = dict()
    with open(wave_parms_path) as jsonfile:
        wave_parms = json.load(jsonfile)

    # do simulation and rendering
    sim(input_frange, wave_parms)
