import numpy as np
import matplotlib.pyplot as plt
from piecewise_line import *
from scipy.optimize import curve_fit
import matplotlib
import re
import plot_phase_vs_pressure_many_gases as pp
import matplotlib.cm as cm

from_chas = True 
out_dir = '/home/dmartin/analyzedData/20190626/pramp/N2/'

gas ='He'

#base_path = "/processed_data/spinning/pramp_data/20190514/He/"
base_path = "/processed_data/spinning/pramp_data/20190626/N2/"

#in_fs = ['50kHz_4Vpp_1_','50kHz_4Vpp_2_','50kHz_4Vpp_3_']#,'50kHz_4Vpp_4_','50kHz_4Vpp_5_']#,'50kHz_4Vpp_6_']#,'50kHz_4Vpp_7_','50kHz_4Vpp_8_']
#base_path = "/processed_data/spinning/pramp_data/20190514/Xe/"
#in_fs = ['50kHz_4Vpp_1_','50kHz_4Vpp_2_1_','50kHz_4Vpp_2_2_']
#Xe:in_fs =['50kHz_4Vpp_1_','50kHz_4Vpp_2_','50kHz_4Vpp_3_']
#base_path = "/home/dmartin/analyzedData/20190514/pramp3/He/"
#in_fs = ['He_4Vpp_50kHz_1_','He_4Vpp_50kHz_3_','He_4Vpp_50kHz_4_']

in_fs = ['50kHz_4Vpp_1_','50kHz_4Vpp_2_','50kHz_4Vpp_3_']

num_files = len(in_fs)
cal = 0.66

def get_phi(fname):
    phi = np.load(base_path + fname + "phi.npy")
    return phi/2

def get_pressure(fname):
    pressures = np.load(base_path + fname + "pressures.npy")
    return pressures

def pressure_model(pressures, break_ind = 855 , p_ind = 1 , plt_press = True):
    ffun = lambda x, y0, m0, m1,m2: \
            pw_line(x, break_ind, 1e8, 1e7, y0, m0, m1, m2, 0.)

    n = np.shape(pressures)[0]
    inds = np.arange(n)
    popt, pcov = curve_fit(ffun, inds, pressures[:, p_ind])
    pfit = ffun(inds, *popt)

    if plt_press:
        p_dict = {0:"Pirani",1:"1 Torr Baratron", -1:"Baratron"}
        plt.plot(1.33322*pressures[:, p_ind], '-', label = p_dict[p_ind])
        plt.plot(1.33322*pfit, label = "piecewise linear fit")
        plt.xlabel("File [#]")
        plt.ylabel("Pressure [mbar]")
        plt.legend()
        plt.show()

    return pfit

def constline(x,m,b):
	return m*x + b
def phi_ffun(p, k, phinot):
    return -1*np.arcsin(np.clip(p/k, 0., 1)) + phinot

phases = np.array(map(get_phi, in_fs))
pressures = np.array(map(get_pressure, in_fs))
#p_fits = np.array(map(pressure_model, pressures))

if from_chas:
	phases /= 0.5

break_ind =  [0,166,0]

p_fits = [] 
for i in range(len(pressures)):
	print(i)
	p_fits.append(1.33322*np.array(pressure_model(pressures[i],break_ind[i])))

#1.33322
#for i in range(len(pressures)):
#	p, interp_p=np.array(pp.build_full_pressure(pressures[i],plot=True))
#	p_fits.append(interp_p)

#phases = -1 * phases

max_diff_ind = np.empty([len(in_fs)],dtype=int)
upper_bound =  0.08

for i in range(len(p_fits)):
	param = out_dir +'_'+ in_fs[i] + 'max_indices' + '_{}'.format(num_files) +'.npy'

	print(in_fs[i])
	
	plt.scatter(p_fits[i],phases[i])
	plt.show()
	
	try:	
		max_diff_ind[i] = np.load(param)
		continue
	except IOError:
		pass
		
	while int(raw_input('Continue? ')) == 1:
		#Find the point at which phase is random
		phase_diff_max = float(raw_input('Maximum phase diff: '))#0.5
		skip = int(raw_input('Skip indices: '))#400
		
		for j in range(len(phases[i][skip:])):
			phase_diff = phases[i][j+skip] - phases[i][(j+skip+1)%len(phases[i])]			
			print(np.abs(phase_diff))
			#print(phases[i][j+skip],phases[i][j+)
			if np.abs(phase_diff) > phase_diff_max:
				print(phase_diff,phase_diff_max)
				phase_diff_max = phase_diff
				max_diff_ind[i] = int(j+skip) 
				break
		#plot data and the point where phase is random
		print(max_diff_ind[i])
		plt.scatter(p_fits[i][max_diff_ind[i]],phases[i][max_diff_ind[i]])
		plt.plot(p_fits[i],phases[i],'r')
		plt.show()
	 
	np.save(param,max_diff_ind[i])

unwrap_cut = []
#unwrap_cut = [p_fits[0][max_diff_ind],0]
for i in range(len(p_fits)):
	unwrap_cut.append(p_fits[i][max_diff_ind[i]])
	mask = p_fits[i] < unwrap_cut[i]
	phases[i][mask] = np.unwrap(2.0*phases[i][mask])/2.0
	#phases[i] += np.pi
	#phases[i] = np.unwrap(2.0*phases[i],2.0*np.pi)/2.0
	#plt.scatter(p_fits[i],phases[i])
	#plt.show()

popts = []
pcovs = []


for i, p in enumerate(p_fits):
	p_new_interval = p_fits[i]<p_fits[i][max_diff_ind[i]] 
	#if i == 0:
	#	p_new_interval = p_fits[i]<0.06
	#	max_diff_ind[i] = 0.06
	p0 = [p_fits[i][max_diff_ind[i]], 0.0]
	#plt.plot(p_fits[i][p_new_interval],phases[i][p_new_interval])
	#plt.show()
	pphi, covphi = curve_fit(phi_ffun, p_fits[i][p_new_interval],phases[i][p_new_interval], p0 = p0)
	popts.append(pphi)
	pcovs.append(covphi)

meas_num = []
for i in range(len(p_fits)):

	meas_num.append(i)

#popts[1][0] = 0.06

t = np.arange(len(p_fits))
for i in range(len(p_fits)):
	plt.plot(p_fits[i],(phi_ffun(p_fits[i],*popts[i])-popts[i][1])/np.pi,label = r'Measurement {} Pmax = {}'.format(meas_num[i],round(popts[i][0],5)))
	
	plt.scatter(p_fits[i],(phases[i]-popts[i][1])/np.pi,alpha=0.75)

	#plt.scatter(p_fits[i][max_diff_ind[i]],(phases[i][max_diff_ind[i]]-popts[i][1])/np.pi)	
plt.ylabel(r'Phase Lag [$\pi$]')
plt.xlabel(r'Pressure [mbar]')
plt.legend()
if int(raw_input('save? ')) == 1:
	gas = raw_input('gas? ')
	plt.savefig('/home/dmartin/analyzedData/20190514/pramp3/He/meas_phaselag_pramp3_{}_1.png'.format(gas),dpi =300*10)
plt.show()


p_maxs = []
for i in range(len(p_fits)):
	
	p_maxs.append(popts[i][0])

param = out_dir+ gas +'_' + 'mean_and_std' + '_{}'.format(len(in_fs)) +'.npy'

print(np.mean(p_maxs),np.std(p_maxs)/len(p_maxs))
arr = [np.mean(p_maxs),np.std(p_maxs)/len(p_maxs)]

if int(raw_input('save avg and std? ')) == 1:
	np.save(param,arr)#np.array([np.mean(p_maxs),np.std(p_maxs)/len(p_maxs)]))	

