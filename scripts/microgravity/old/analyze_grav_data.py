import cant_util as cu
import numpy as np
import matplotlib.pyplot as plt
import glob 
import bead_util as bu
import Tkinter
import tkFileDialog
import os, sys
from scipy.optimize import curve_fit
import bead_util as bu
from scipy.optimize import minimize_scalar as minimize
import cPickle as pickle

import image_util as imu

import warnings
warnings.filterwarnings("ignore")

###########################
# Script to analyze "gravity" data in which the cantilever is
# driven alongside the bead. The user can select the axis along 
# which the cantilever is driven.
###########################

out_fvpos = cu.Force_v_pos()


filstring = 'Z9um'

# CHOOSE WHETHER TO LOOK AT VARIOUS BIAS OR VARIOUS CANT POS
bias = False
stagestep = True
stepind = 0

dirs = [11,]
bdirs = [1,]
subtract_background = False

ddict = bu.load_dir_file( "/dirfiles/dir_file_sept2017.txt" )
maxfiles = 1000   # Maximum number of files to load from a directory

SWEEP_AX = 1     # Cantilever sweep axis, 1 for Y, 2 for Z
bin_size = 2     # um, Binning for final force v. pos
lpf = 150        # Hz, acausal top-hat filter at this freq
cantfilt = True

fig_title = 'Force vs. Cantilever Position:'
xlab = 'Distance along Cantilever [um]'

# Locate Calibration files
tf_path = '/calibrations/transfer_funcs/Hout_20170903.p'
step_cal_path = '/calibrations/step_cals/step_cal_20170903.p'
im_cal_path = '/calibrations/image_calibrations/stage_polynomial_1d_20170831.npy'
trap_ypix = 340

legend = True
leginds = [2,1]
ncol = 2
##########################################################
# Don't edit below this unless you know what you're doing

init_data = [0., 0., 0.]  # Separation data to initialize empy directories

cal_drive_freq = 41  # Hz


################


def proc_dir(d):
    # simple directory processing function to load data and find
    # different cantilever positions
    dv = ddict[d]
    init_data = [dv[0], [0,0,dv[-1]], dv[1]]
    dir_obj = cu.Data_dir(dv[0], [0,0,dv[-1]], dv[1])

    newfils = []
    for fil in dir_obj.files:
        if filstring in fil:
            newfils.append(fil)
    dir_obj.files = newfils

    # Load the calibrations
    dir_obj.load_H(tf_path)
    dir_obj.load_step_cal(step_cal_path)
    dir_obj.calibrate_H()

    dir_obj.load_dir(cu.diag_loader, maxfiles=maxfiles, prebin=True, nharmonics=10, noise=False, width=1., \
                     cant_axis=SWEEP_AX, reconstruct_lowf=True, lowf_thresh=lpf, drive_freq=cal_drive_freq, \
                     init_bin_sizes=[1.0, 1.0, 1.0], analyze_image=True, cantfilt=cantfilt)
    
    #dir_obj.filter_files_by_cantdrive(cant_axis=SWEEP_AX, nharmonics=10, noise=True, width=1.)

    dir_obj.get_avg_force_v_pos(cant_axis=SWEEP_AX, bin_size = bin_size, cantfilt=cantfilt, \
                                stagestep=stagestep, stepind=stepind, bias=bias, maxfiles=maxfiles)

   

    #dir_obj.diagonalize_files(reconstruct_lowf=True,lowf_thresh=lpf, #plot_Happ=True, \
    #                         build_conv_facs=True, drive_freq=cal_drive_freq, cantfilt=cantfilt)
    dir_obj.get_avg_force_v_pos(cant_axis=SWEEP_AX, bin_size = bin_size, diag=True, cantfilt=cantfilt, \
                                stagestep=stagestep, stepind=stepind, bias=bias, maxfiles=maxfiles)

    return dir_obj

# Do intial processing
dir_objs = map(proc_dir, dirs)
if subtract_background:
    bdir_objs = map(proc_dir, bdirs)



f, axarr = plt.subplots(3,2,sharex='all',sharey='all',figsize=(7,8),dpi=100)
if subtract_background:
    f2, axarr2 = plt.subplots(3,2,sharex='all',sharey='all',figsize=(10,12),dpi=100)


for objind, obj in enumerate(dir_objs):    
    if subtract_background:
        bobj = bdir_objs[objind]

    keys = obj.avg_diag_force_v_pos.keys() 
    cal_facs = obj.conv_facs
    #cal_facs = [1.,1.,1.]

    keycolors = bu.get_color_map(len(keys))
    keys.sort(key = lambda x: float(x))
    for keyind, key in enumerate(keys):
        color = keycolors[keyind]
        # Force objects are indexed as follows:
        # data[response axis][velocity mult.][bins, data, or errs]
        #     response axis  : X=0, Y=1, Z=2
        #     velocity mult. : both=0, forward=1, backward=-1
        #     b, d, or e     : bins=0, data=1, errors=2 
        diagdat = obj.avg_diag_force_v_pos[key]
        dat = obj.avg_force_v_pos[key]

        if subtract_background:
            diagbdat = bobj.avg_diag_force_v_pos[key]
            bdat = bobj.avg_force_v_pos[key]

        #offset = 0
        if bias:
            lab = str(key) + ' V'
        elif stagestep:
            lab = str(key) + ' um'
        for resp in [0,1,2]:
            #offset = - dat[resp,0][1][-1]
            offset = - np.mean(dat[resp,0][1])
            #diagoffset = - diagdat[resp,0][1][-1]
            diagoffset = - np.mean(diagdat[resp,0][1])

            # refer to indexing eplanation above if this is confusing!
            axarr[resp,0].errorbar(dat[resp,0][0], \
                                   (dat[resp,0][1]+offset)*cal_facs[resp]*1e15, \
                                   dat[resp,0][2]*cal_facs[resp]*1e15, \
                                   fmt='.-', ms=10, color = color, label=lab)
            axarr[resp,1].errorbar(diagdat[resp,0][0], \
                                   (diagdat[resp,0][1]+diagoffset)*1e15, \
                                   diagdat[resp,0][2]*1e15, \
                                   fmt='.-', ms=10, color = color, label=lab)

            if subtract_background:
                axarr2[resp,0].errorbar(dat[resp,0][0], \
                                   (dat[resp,0][1]-bdat[resp,0][1]+offset)*cal_facs[resp]*1e15, \
                                   dat[resp,0][2]*cal_facs[resp]*1e15, \
                                   fmt='.-', ms=10, color = color, label=lab)
                axarr2[resp,1].errorbar(diagdat[resp,0][0], \
                                   (diagdat[resp,0][1]-diagbdat[resp,0][1]+diagoffset)*1e15, \
                                   diagdat[resp,0][2]*1e15, \
                                   fmt='.-', ms=10, color = color, label=lab)
        if key == keys[-1]:
            print key
            out_fvpos.bins = dat[0,0][0]
            out_fvpos.force = dat[0,0][1]*cal_facs[0]
            out_fvpos.diagbins = diagdat[0,0][0]
            out_fvpos.diagforce = diagdat[0,0][1]

            out_fvpos.paths = []
            out_fvpos.dat = []
            out_fvpos.seps = []
            out_fvpos.heights = []
            out_fvpos.errs = []
            out_fvpos.diagerrs = []

out_fvpos.save('/force_v_pos/20170903_grav_background_sep15um_h10um.p')

axarr[0,0].set_title('Raw Imaging Response')
axarr[0,1].set_title('Diagonalized Forces')

for col in [0,1]:
    axarr[2,col].set_xlabel(xlab)

axarr[0,0].set_ylabel('X-direction Force [fN]')
axarr[1,0].set_ylabel('Y-direction Force [fN]')
axarr[2,0].set_ylabel('Z-direction Force [fN]')

if legend:
    axarr[leginds[0]][leginds[1]].legend(loc=0, numpoints=1, ncol=ncol, fontsize=9)

dirlabel = dir_objs[0].label

if len(fig_title):
    f.suptitle(fig_title + ' ' + dirlabel, fontsize=18)

plt.show()
    
        
