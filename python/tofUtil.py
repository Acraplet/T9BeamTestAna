#!/usr/bin/python3

from math import sqrt, pow
import ROOT
from collections import OrderedDict

momentaMeV = [200 + i*20 for i in range(1,9)]
momentaMeV.extend([500, 540, 600, 660, 860, 900, 940, 1000, 1060, 1120, 1200])
print(momentaMeV)



ms = OrderedDict()
ms['e'] = 0.511
ms['mu'] = 105.66
ms['pi'] = 139.57
ms['K'] = 493.7
ms['p'] = 938.3
ms['D'] = 1876.
ms['T'] = 3.01604928*931.494 # isotope mass in Da


pcols = OrderedDict()
pcols['e'] = ROOT.kRed
pcols['mu'] = ROOT.kBlue 
pcols['pi'] = ROOT.kGreen+2
pcols['K'] = ROOT.kGray+1
pcols['p'] = ROOT.kBlack
pcols['D'] = ROOT.kViolet
pcols['T'] = ROOT.kCyan+2

conv = 1.e9 # to ns
#TB2022 l = 2.90 # m
#TB2023:
l = 3.49 # m
c = 299792458 # m/s

print('*** The Time of Flight times for L = {} m as function of particles momenta ***'.format(l))

############################################################
def getBetaGamma(m, p):
    # beta*gamma:
    bg = p/m
    return bg
############################################################
def getBeta(m, p):
    # beta*gamma:
    bg = p/m
    beta = sqrt(bg*bg/(1+bg*bg))
    return beta

############################################################
def getTof(m, momentum):
    # bug fixed 14.2.2024!
    return l/c*sqrt(1.+pow(m/momentum,2))*conv

############################################################
def TofToMomentum(tof, m):
    #the tof needs to be the absolute flying time
    p = 0.
    val = pow((tof) * c / (conv * l), 2) - 1
    if val > 0.:
        p = m/sqrt(val)
    return p

############################################################
# input: tofdiff, i.e. time of flight difference of a particle and tof of electrons!
# then also mass of the particle and uncertainties in the emasured times of the particle and of electrons (not the tof resolution or fitted leaks widths!)
def TofDiffToMomentum(tofdiff, m, sigmate = 0., sigmatParticle = 0.):
    #the tof needs to be the tof subtracted by the electrons TOF
    coL = c / (conv * l) # c over L ;) [s^{-1}]
    val = pow((tofdiff) * coL + 1, 2) - 1
    p = 0.
    perr = 0.
    if val > 0.:
        p = m/sqrt(val)
        if sigmate > 0. or sigmatParticle > 0.:
            sigmatSq = pow(sigmate,2) + pow(sigmatParticle,2)
            if sigmatSq > 0.:
                sigmat = sqrt(sigmatSq)
                perr = pow(p,3) / pow(m,2) * ( tofdiff*coL + 1) * coL * sigmat
    return p, perr



############################################################

def getTofDiff(particle1, particle2, momentum):
    m1 = ms[particle1]
    m2 = ms[particle2]
    t1 = getTof(m1, momentum)
    t2 = getTof(m2, momentum)
    return t2 - t1

############################################################

def GenerateTimes(verbose = True):

    dts = OrderedDict()
    ts = OrderedDict()
    
    for pname in ms:
        ts[pname] = []
        dts[pname] = []


    for p in momentaMeV:
        line = 'p = {} MeV: '.format(p)
        for pname in ms:
            m = ms[pname]
            t = getTof(m, p) #l/c*sqrt(1.+pow(m/p,2))*conv
            line = line + ' {}: {:2.2f}'.format(pname, t)
            ts[pname].append(1.*t)
        line = line + ' ns'
        if verbose:
            print(line)

    for pname in ts:
        if pname == 'e':
            continue
        for ip in range(0,len(ts[pname])):
            dts[pname].append(ts[pname][ip] - ts['e'][ip])

    for pname in dts:
        if pname == 'e':
            continue
        if verbose:
            print('--- dt between {} and electrons ---'.format(pname))
        for ip in range(0,len(ts[pname])):
            if verbose:
                print('p={}: dt = t_{} - t_e = {:1.2f} ns'.format(momentaMeV[ip], pname, dts[pname][ip]))

    return dts

