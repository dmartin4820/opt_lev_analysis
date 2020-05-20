import sys, re, os

import dill as pickle

import numpy as np
import pandas as pd

from mpl_toolkits.mplot3d import Axes3D
from matplotlib.collections import PolyCollection
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 14})

import grav_util_3 as gu
import bead_util as bu
import configuration as config

import warnings
warnings.filterwarnings("ignore")


ncore = 30
# ncore = 10



# theory_data_dir = '/data/old_trap/grav_sim_data/2um_spacing_data/'
theory_data_dir = '/home/cblakemore/opt_lev_analysis/gravity_sim/results/7_6um-gbead_1um-unit-cells/'


data_dirs = ['/data/new_trap/20200320/Bead1/Shaking/Shaking378/']
new_trap = True

substr = 'Shaking3'  # for 20200210/.../...384/ and 20200320/.../...378

Nfiles = 10000

# redo_alpha_fit = True
redo_alpha_fit = False

plot_basis = False
plot_alpha_xyz = False
plot_bad_alphas = True

yuklambda = 100e-6

### Position of bead relative to the attractor coordinate system
p0_bead_dict = {'20200320': [392.0, 199.7, 50.0]}

# harms = [6]
harms = [3,4,5,6,7,8,9,11,12,13,14,15]
n_largest_harms = 10


#opt_ext = 'TEST'
opt_ext = '_harms'
for harm in harms:
    opt_ext += '-' + str(int(harm))
opt_ext += '_first-{:d}'.format(Nfiles)
if len(substr):
    opt_ext += '_{:s}'.format(substr)


for ddir in data_dirs:
    # Skip the ones I've already calculated
    #if ddir == data_dirs[0]:
    #    continue
    print()

    paths = gu.build_paths(ddir, opt_ext, new_trap=new_trap)
    agg_path = paths['agg_path']
    p0_bead = p0_bead_dict[paths['date']]

    agg_dat = gu.AggregateData([], p0_bead=p0_bead, harms=harms, new_trap=new_trap)
    agg_dat.load(agg_path)
    agg_dat.load_grav_funcs(theory_data_dir)

    agg_dat.bin_rough_stage_positions()
    #agg_dat.average_resp_by_coordinate()

    if redo_alpha_fit:   
        agg_dat.find_alpha_xyz_from_templates(plot=plot_alpha_xyz, plot_basis=plot_basis, \
                                                ncore=ncore, plot_bad_alphas=plot_bad_alphas, \
                                                n_largest_harms=n_largest_harms)

    # agg_dat.plot_sensitivity()

    # filenums = [5, 50, 500, 5000]
    filenums = list(map(int, np.linspace(10,10000,20)))
    # plot_alphas = list(np.logspace(-3, 0, 20))
    # plot_alphas = list(np.exp(np.linspace(-3, 0, len(filenums))))
    print('{:d} total...'.format(len(filenums)))

    show = False
    colors = bu.get_color_map(len(filenums), cmap='BuPu')
    lambind = np.argmin(np.abs(agg_dat.gfuncs_class.lambdas - yuklambda))

    best = []
    upper = []
    lower = []
    for i, j in enumerate(filenums):
        print(i, end=', ')
        # print(ind)
        if j == filenums[-1]:
            show = True

        profiles = \
            agg_dat.fit_alpha_xyz_onepos_simple(resp=[2], last_file=j, plot=True, \
                                                show=show, plot_color=colors[i], \
                                                plot_label='{:d} files'.format(j)) #, \
                                                # plot_alpha=plot_alphas[i])

        best_fit = agg_dat.alpha_best_fit[lambind]
        interval = np.abs(agg_dat.alpha_95cl[lambind])

        best.append(best_fit)
        upper.append(best_fit + interval)
        lower.append(best_fit - interval)

    fig, ax = plt.subplots(1,1)
    ax.plot(filenums, best, color='C0', zorder=3)
    ax.fill_between(filenums, lower, upper, color='C0', alpha=0.6, zorder=2)
    ax.axhline(0, ls='--', color='k', lw=2, zorder=1)

    ax.set_xlabel('Number of Files Integrated')
    ax.set_ylabel('Alpha')

    plt.tight_layout()

    plt.show()

    print()
