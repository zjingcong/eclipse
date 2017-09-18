#!/usr/bin/python

#######################################################################################
#
# runGilligan.py
#
# Gilligan demo surfswell 
#
# The scene consists of:
#    1. Ocean surface with ochi swell and pierson-moskowitz wind waves
#    2. Skydome with hdri sky image
#    3. Cargo ship 7 km distant
#    4. Atmospheric haze
#    5. underwater ground plane
#    6. underwater optics
#    7. Global illumination for all (except the cargo ship)
#    8. Camera bobbing 1 meter above the surface.
#    9. Toy submarine model transiting across the camera view
#    10. eWave interactive waves for the sub/water surface interface
#        The eWave source has been set very strong to give a big
#        visual outcome.  It can be controlled by the eWave parameter
#        'sourcescale'. Horizontal displacement and whitecaps are 
#        also in effect for the eWave.
#    11. Camera pans to keep the toy submarine centered in the frame
#
# Usage from the command line:
#
#    ./runGilligan.py <frame-range>
#
# where <frame-range> is the range of frame that are to be rendered and written to
# disk.  The frames are written to 
#
#     ../products/images/surfswell_scene3_FPS30.XXXX.exr
#
# where XXXX is the zero-padded four digit frame number.  The <frame-range> has the
# form of a frange list.  For example, if you want to render frames 5 through 26, 
# the frange is
#
#      5-26
#
# If you want to render every third frame in the range of 5 through 26, it is
#
#      5-26:3
#
# and if you want to also render frames 75 through 100, it is
#
#      5-26:3,75-100
#
# In all cases, simulation begins at frame 1 and marches to the last frame in the
# frange.  Rendering only takes place for frames listed in the frange in 
# <frame-range>.
#
# In addition to the image frames, the config file for the scene is written to the 
# same location as the image.
#
# The file 
#
#     ../products/images/surfswell_scene3_FPS30_output.mov
#
# is a quicktime movie of the rendered frames.
#
#
#######################################################################################

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
# ASSPATH = "/DPA/ewok/dpa/projects/eclipse/rnd/oceansurface/gilliganTest/testAss/"
# ASSNANE = "hand02_tri"
# PRODNAME = "waveShape_1"
# PRODUCTSPATH = "/DPA/ewok/dpa/projects/eclipse/rnd/oceansurface/gilliganTest/products"
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
    
    ewave_waves = ewsim.eWaveSim('thing_in_water_waves')
    ewave_waves.set('patchnxny', '[1024,512]' )
    ewave_waves.set('patchsize', '[ 40.0,20.0 ]' )
    ewave_waves.set('llc', '[ -20.0, 0.0 ]' )
    ewave_waves.set('gravity',  9.8 )
    ewave_waves.set('depth', 10.0 )
    ewave_waves.set('capillary', 0.015 )
    ewave_waves.set('trimfraction',  0.1 )
    ewave_waves.set('trimalpha', 0.05 )
    ewave_waves.set('displacementscale', 0.3 )
    ewave_waves.set('dohorizontal', True)
    ewave_waves.set('sourcescale', 1.0 )
    ewave_waves.set('ambientscale', 0.75*0.3 )
    ewave_waves.set('compute_whitecaps', False )
    # ewave_waves.set('compute_whitecaps', True)
    # ewave_waves.set('whitecaps_llc', ewave_waves.get('llc') )
    # ewave_waves.set('whitecaps_urc', '[20.0,20.0]' )
    # ewave_waves.set('whitecaps_nxny', ewave_waves.get('patchnxny') )
    # ewave_waves.set('whitecaps_halflife', 2.0 )
    # ewave_waves.set('whitecaps_threshold', 0.89 )

    ewave_waves.generate_object()
    simscene.add_sim(ewave_waves)
    return simscene


# def CreateCamera(surface, view_object):
#     water_surface = surface.data_object
#     view_object_cm = view_object.info()['centerOfMass']
#     camera = cam.Camera()
#     camera.set( 'eye',    '[0.0,0.0,0.333333]' )
#     camera.set( 'view',   view_object_cm )
#     camera.set( 'up',     '[0.0,1.0,0.0]' )
#     camera.set( 'fov',    60.0 )
#     camera.set( 'aspect', 16.0/9.0 )
#     eye = camera.get('eye')
#     up = camera.get('up')
#     x = eye[0]
#     y = eye[1]
#     z = eye[2]
#     height = water_surface.WaveHeight( x,z )
#     DX = water_surface.WaveCuspDisplacementX( x,z )
#     DZ = water_surface.WaveCuspDisplacementY( x,z )
#     slopeX = water_surface.WaveSlopeX( x,z )
#     slopeZ = water_surface.WaveSlopeY( x,z )
#     DXX = water_surface.WaveCuspDisplacementGradientXX( x,z )
#     DXZ = water_surface.WaveCuspDisplacementGradientXY( x,z )
#     DZZ = water_surface.WaveCuspDisplacementGradientYY( x,z )
#     xn = slopeX *( 1.0 - DZZ ) + slopeZ*DXZ
#     yn = DXZ*DXZ - (1.0-DXX)*(1.0-DZZ)
#     zn = slopeZ * (1.0 - DXX) + slopeX*DXZ
#     normalizer = math.sqrt( xn*xn + yn*yn + zn*zn )
#     xn /= -normalizer
#     yn /= -normalizer
#     zn /= -normalizer
#     distance_off_surface = 1.0
#     up = [xn,yn,zn]
#     eye = [x - DX + xn*distance_off_surface, y + height + yn*distance_off_surface, z - DZ + zn*distance_off_surface]
#     camera.set('eye', eye)
#     camera.set('up', up )
#     return camera


def RetrieveThingInWater(f):
    thing_in_water_path = os.path.join(ASSPATH, '{name}.{frame}.obj'.format(name=ASSNANE, frame=util.formattedFrame(f)))
    # thing_in_water_path = "../assets/toysubmarine/model/products/geom/0001/obj/lo/toysubmarine." + util.formattedFrame(f) +".obj"
    thing_in_water = poly.Polygonal('thing_in_water')
    thing_in_water.set('objpath', thing_in_water_path)
    thing_in_water.visible = True
    return thing_in_water


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
    frame_range = [4]
    # if len(sys.argv) > 1:
    #     import gilligan.thurston.frange as frange
    #     frame_range = frange.Frange( sys.argv[1] )

    import gilligan.thurston.frange as frange
    frame_range = frange.Frange(input_frange)

    thirsty.F = 1

    simscene = CreateWaterSims('scene3', wave_parms)
    simscene.set('frame', 'thirsty.F' )


    simscene.generate_object()

    # Need to assemble basewave from swell and pm
    merged_ocean = simmerge.WaveMerge('base_ocean')
    merged_ocean.add_wave( simscene.get_sim('swell_waves') )
    merged_ocean.add_wave( simscene.get_sim('small_waves') )
    merged_ocean.generate_object()
    merged_ocean.verbose = True

    ew = simscene.get_sim('thing_in_water_waves')
    sw = simscene.get_sim('swell_waves')
    pw = simscene.get_sim('small_waves')
    ew.verbose = True
    ew.set('surface_geom', merged_ocean)


    #
    #  Update ocean to current time
    #  including ewave interaction with ocean
    #

    frame_list = frame_range.frames

    for f in range(1,frame_range.end+1):
        LogIt(__file__, colors.color_magenta + "\n\n********************************** F R A M E  " + str(f) + " *****************************************\n" + colors.color_white)
        thirsty.F = int(f)
        LogIt(__file__, colors.color_yellow + "\n\n\tS I M U L A T I O N\n" + colors.color_white)
        merged_ocean.update(timestep)
        water_thing = RetrieveThingInWater(f)
        ew.set('height_source_geom', water_thing)
        ew.set('compute_height_source', True)
        ew.update(timestep)
        LogIt(__file__, colors.color_yellow + "\n\n\tS I M U L A T I O N   F I N I S H E D\n" + colors.color_white)
        if f in frame_list:
            if ew.verbose:
                # fname = "../products/ewave_sim/" + ew.label + "." + util.formattedFrame(f) + ".exr"
                fname = "sim/" + ew.label + "." + util.formattedFrame(f) + ".exr"
                fname = os.path.join(PRODUCTSPATH, fname)
                ew.write_displacement(fname)
                sw.write_displacement(os.path.join(PRODUCTSPATH, 'sim/swell_wave.{}.exr'.format(util.formattedFrame(f))))
                pw.write_displacement(os.path.join(PRODUCTSPATH, 'sim/small_wave.{}.exr'.format(util.formattedFrame(f))))


    #
    # ###############################
    # #
    # #  Render phase
    # #
    # ###############################
    #
    #         LogIt(__file__, colors.color_yellow + "\n\n\tR E N D E R\n" + colors.color_white)
    #         renderscene = scene.Scene('renderscene')
    #         renderscene.set('frame', 'thirsty.F' )
    #
    #
    #
    #
    # #
    # #  Camera placement wrt to ocean surface
    # #
    #         camera = CreateCamera( simscene.get_sim('swell_waves'), water_thing )
    #         camera.change_label('ocean_camera')
    #         renderscene.add_camera(camera)
    #
    #
    # #
    # #  Shaders for resuse
    # #
    #
    #         import gilligan.thurston.material as material
    #         import gilligan.ash.python.ashUtils as au
    # ###### PUSH ############
    #         push = material.PushToOutputStack()
    #
    # ###### ATMOSPHERE ############
    #         atmos_lapse_rate = 50.0  # 0.1 km
    #         atmos_bottom = [0,0,0 ]
    #         atmos_up = [0,1,0]
    #         # atmos_color = [ 5.0,5.0,5.0, 0 ]
    #         atmos_color = [5.0, 5.0, 5.0, 1]
    #         # atmos_atten = [ 0.00015, 0.00013, 0.00013, 0 ]  # medium haze
    #         atmos_atten = [0.00015, 0.00013, 0.00013, 1]  # medium haze
    #         atmosphere = material.PlanarAtmosphere('atmosphere')
    #         atmosphere.set('bottompoint', atmos_bottom)
    #         atmosphere.set('up', atmos_up)
    #         atmosphere.set('lapserate', atmos_lapse_rate)
    #         atmosphere.set('color', atmos_color)
    #         atmosphere.set('attenuation', atmos_atten)
    #
    # ###### WATER VOLUME ############
    #         watervolume_bottom = [0,0,0]
    #         watervolume_up = [0,1,0]
    #         watervolume_lapse_rate = 10000.0
    #         # watervolume_color = [0.0, 0.6 * 2.5, 1.1 * 2.5, 0]
    #         watervolume_color = [ 0.0, 0.6*2.5, 1.1*2.5, 1 ]
    #         # watervolume_atten = [0.35 / 3.0, 0.1 / 3.0, 0.1 / 3.0, ]
    #         watervolume_atten = [ 0.35/3.0,0.1/3.0,0.1/3.0, 1 ]
    #         watervolume = material.WaterVolume('water_volume')
    #         watervolume.set('up', watervolume_up)
    #         watervolume.set('color',watervolume_color)
    #         watervolume.set('attenuation',watervolume_atten)
    #
    #
    #
    # #
    # #   Set up scene elements
    # #
    #
    # # ###### SHIP ############
    # # #### Container Ship
    # #         con_ship_texture = au.Texture( "../assets/ship/products/mearsk_arun_scaled/geom/0001/obj/lo/MEARSK_ARUN_OBJ/SHIP.exr"  )
    # #         con_ship_color = material.TexturedSpectralColor('container_ship_textured_spectral_color')
    # #         con_ship_color.set("texture", con_ship_texture)
    # #         con_ship_mat = material.Material('container_ship_material')
    # #         con_ship_mat.add_shader( atmosphere )
    # #         con_ship_mat.add_shader( con_ship_color )
    # #         con_ship_mat.add_shader( push )
    # #         con_ship_path = "../assets/ship/products/mearsk_arun_scaled/geom/0001/obj/lo/con_ship.obj"
    # #         con_ship = poly.Polygonal('container_ship')
    # #         con_ship.set('objpath', con_ship_path)
    # #         con_ship.material = con_ship_mat
    # #         con_ship.visible = True
    # #         renderscene.add_geometry(con_ship)
    # # #### Containers
    # #         container_texture = au.Texture("../assets/ship/products/mearsk_arun_scaled/geom/0001/obj/lo/MEARSK_ARUN_OBJ/Cont1.exr"  )
    # #         container_color = material.TexturedSpectralColor('containers_textured_spectral_color')
    # #         container_color.set("texture", container_texture)
    # #         container_mat = material.Material('containers_material')
    # #         container_mat.add_shader( atmosphere )
    # #         container_mat.add_shader( container_color )
    # #         container_mat.add_shader( push )
    # #         container_path = "../assets/ship/products/mearsk_arun_scaled/geom/0001/obj/lo/containers.obj"
    # #         container = poly.Polygonal('containers')
    # #         container.set('objpath', container_path)
    # #         container.material = container_mat
    # #         container.visible = True
    # #         renderscene.add_geometry(container)
    #
    #
    # ###### GROUND PLANE ############
    # #
    # #  Material
    # #
    #         # groundplane_color = [0.7 * 2.5, 0.4 * 2.5, 0.3 * 2.5, 0]
    #         groundplane_color = [ 0.7*2.5, 0.4*2.5, 0.3*2.5, 1 ]
    #         groundplane_lambertian = material.SpectralConstant('ground_plane_spectral_constant')
    #         groundplane_lambertian.set("color", groundplane_color)
    #         groundplane_mat = material.Material('ground_plane_material')
    #         groundplane_mat.add_shader( atmosphere )
    #         groundplane_mat.add_shader( watervolume )
    #         groundplane_mat.add_shader( groundplane_lambertian )
    #         groundplane_mat.add_shader( push )
    # #
    # # Geometry
    # #
    #         groundplane_path = os.path.join(ASSPATH, "groundplane/products/groundplane/geom/0001/obj/lo/groundplane.obj")
    #         # groundplane_path = os.path.join("../assets/groundplane/products/groundplane/geom/0001/obj/lo/groundplane.obj"
    #         groundplane = poly.Polygonal('ground_plane')
    #         groundplane.set('objpath', groundplane_path)
    #         groundplane.material = groundplane_mat
    #         groundplane.visible = True
    #         renderscene.add_geometry(groundplane)
    #
    #
    #
    # ###### SKYDOME ############
    # #
    # #  Material
    # #
    #         skydome_texture_path = os.path.join(ASSPATH, "skydome/products/skyhdri/image/0001/exr/5000x2500/hdrmaps_com_free_052.exr")
    #         skydome_texture = au.Texture( skydome_texture_path )
    #         # skydome_texture = au.Texture( "../assets/skydome/products/skyhdri/image/0001/exr/5000x2500/hdrmaps_com_free_052.exr" )
    #         skydome_map = material.TexturedMap('skydome_texturedmap')
    #         skydome_map.set("texture", skydome_texture)
    #         skydome_mat = material.Material('skydome_material')
    #         skydome_mat.add_shader( atmosphere)
    #         skydome_mat.add_shader( skydome_map )
    #         skydome_mat.add_shader( push )
    # #
    # # Geometry
    # #
    #         skydome_path = os.path.join(ASSPATH, "skydome/products/skydome/geom/0001/obj/lo/skydome.obj")
    #         # skydome_path = "../assets/skydome/products/skydome/geom/0001/obj/lo/skydome.obj"
    #         skydome = poly.Polygonal('skydome')
    #         skydome.set('objpath', skydome_path)
    #         skydome.material = skydome_mat
    #         skydome.visible = True
    #         renderscene.add_geometry(skydome)
    #
    #
    #
    # ###### THING IN WATER ############
    # #
    # #  Material
    # #
    #         lambertiansamples = 1
    #         # tiw_color = [ 1.0, 1.0, 5.0/255.0, 0 ]
    #         tiw_color = [1.0, 0.0, 0.0, 0]
    #         thing_in_water_color = material.SpectralLambertian('thing_in_water_lambertian')
    #         thing_in_water_color.set("color",tiw_color)
    #         thing_in_water_color.set("samples",lambertiansamples)
    #         thing_in_water_mat = material.Material('thing_in_water_material')
    #         thing_in_water_mat.add_shader( atmosphere )
    #         thing_in_water_mat.add_shader( watervolume )
    #         thing_in_water_mat.add_shader( thing_in_water_color )
    #         thing_in_water_mat.add_shader( push )
    # #
    # # Geometry
    # #
    #         thing_in_water = RetrieveThingInWater(f)
    #         thing_in_water.material = thing_in_water_mat
    #         renderscene.add_geometry(thing_in_water)
    #
    #
    #
    # ###### OCEAN ############
    # #
    # #  Material
    # #
    #
    # ### whitecaps from ewave
    #         import gilligan.thurston.texture as texture
    #         whitecaptex = texture.ImageTexture()
    #         whitecaptex.set('image',ew.whitecap_map )
    #         dynamics_whitecaps = material.OceanProceduralWhitecaps("wake_whitecaps")
    #         dynamics_whitecaps.set('texture', whitecaptex )
    #         dynamics_whitecaps.set('llc',ew.get('whitecaps_llc'))
    #         dynamics_whitecaps.set('urc',ew.get('whitecaps_urc'))
    #         dynamics_whitecaps.set('asymmetry',0.0)
    #         dynamics_whitecaps.set('surface',ew)
    #
    #         ocean_fresnel = material.OceanSurface()
    #         ocean_fresnel.set("iorabove",1.0)
    #         ocean_fresnel.set("iorbelow",1.34)
    #         ocean_fresnel.set("glitterroughness",0.0)
    #         ocean_mat = material.Material('ocean_surface_material')
    #         ocean_mat.add_shader( atmosphere )
    #         ocean_mat.add_shader( watervolume )
    #         if ew.get('compute_whitecaps'):
    #             LogIt(__file__, "using ewave whitecaps")
    #             ocean_mat.add_shader(dynamics_whitecaps)
    #         ocean_mat.add_shader( ocean_fresnel )
    #         ocean_mat.add_shader( push )
    # #
    # # Geometry
    # #
    #         oceanmesh = simmesh.WaveLODMesh('ocean_lod_mesh')
    #         oceanmesh.set('basewavesurface', merged_ocean )
    #         oceanmesh.set('topwavesurface', ew )
    #         oceanmesh.set('frustumcagestart',[-20.0,20.0,-10.0])
    #         oceanmesh.set('frustumcageend',[-6000.0,6000.0,8000.0])
    #         # oceanmesh.set('frustumcageend', [-3000.0, 3000.0, 4000.0])
    #         oceanmesh.set('resolution',0.03)
    #         # oceanmesh.set('loddoubledistance',14.0)
    #         oceanmesh.set('loddoubledistance', 5.0)
    #         eye = camera.get('eye')
    #         oceanmesh.set('start',[ eye[0],eye[2] ])
    #         view = camera.get('view')
    #         viewdir = [ view[0] - eye[0], view[2]-eye[2] ]
    #         viewdirmag = math.sqrt( viewdir[0]*viewdir[0] + viewdir[1]*viewdir[1] )
    #         viewdir[0] = viewdir[0]/viewdirmag
    #         viewdir[1] = viewdir[1]/viewdirmag
    #         LogIt(__file__, "oceanmesh view direction: " + str(viewdir) )
    #         oceanmesh.set('rangedirection', viewdir )
    #         oceanmesh.generate_object()
    #         oceanmesh.update(timestep)
    #
    # # --------------------------------------------------
    #         # write out ocean mesh geometry
    #         # write_obj(filename)
    #         if WRITEOBJ:
    #             obj_filename = os.path.join(PRODUCTSPATH, 'oceanmesh/ocean_{name}.{frame}.obj'.format(name=PRODNAME, frame=util.formattedFrame(f)))
    #             oceanmesh.write_obj(obj_filename)
    # # --------------------------------------------------
    #
    #         ocean = gmesh.Mesh('ocean_surface_mesh')
    #         ocean.set('trimesh', oceanmesh  )
    #         ocean.material = ocean_mat
    #         ocean.visible = True
    # # update mesh data to prepare for rendering
    #         ocean.generate_object()
    #         oceanmesh.reset_object()
    # #need the ocean geometry for the watervolume shader
    #         watervolume.SetWaterSurface(ocean)
    #         renderscene.add_geometry(ocean)
    #
    #
    #
    #
    # ### show the scene parameters going into the render
    #         renderscene.print_parameters()
    #
    #
    # ###### RENDER THE SCENE ############
    #         image = cam.Image('ocean_image')
    #         image.set('width', 960)
    #         image.set('height', 540)
    #         import gilligan.thurston.render.maryann as maryann
    #         renderer = maryann.MaryAnn('surfswell_render')
    #         renderer.set('frame', 'thirsty.F')
    #         renderer.set('aasamples', 40)
    #         renderer.set('rayhits', 10)
    #         renderer.set('threads', 8)
    #         # image_name = "../products/images/surfswell_scene3_FPS" + str(int(thirsty.FPS)) + ".exr"
    #         image_name = os.path.join(PRODUCTSPATH, "images/{name}_FPS{fps}.exr".format(name=PRODNAME, fps=str(int(thirsty.FPS))))
    #         renderer.set('imagename', image_name)
    #         renderer.verbose = True
    #         renderer.generate_object()
    #         if renderer.render_scene( renderscene, renderscene.get_camera('ocean_camera'), image):
    #             cam.write_image_with_metadata( image)
    #         else:
    #             LogIt(__file__,"Not writing image to disk")
    #
    #         for g in renderscene.geometry:
    #             g.reset_object()
    #
    #         renderscene.clear()
    #
    #
    #         LogIt(__file__, colors.color_yellow + "\n\n\tR E N D E R   F I N I S H E D\n" + colors.color_white)

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
                        default='/DPA/ewok/dpa/projects/eclipse/rnd/gilligan/products')
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
