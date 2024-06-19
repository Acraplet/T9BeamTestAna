import sys
import os

import json5

import numpy as np

import lowMomentum_analysis as lm

import matplotlib.pyplot as plt

from scipy.optimize import curve_fit

###########################################################
# New and final particle identification code, to be processed
# with the path to a config file, an example is 
# /config/analyse_000432.json to be used with
# python BeamDataAnalyser.py ../config/analyse_000432.json
# This code:
# 1. Opens the root file,
# 2.  identifies particles (based on hit time for the TG or particle selection cuts for the LM setup implemented in the config file, which should be based on 
# table "Selection cuts derived with integration windows of [-16 to 45ns] for all the datasets that are used for the beam flux studies"
# available in the beam flux technote: https://wcte.hyperk.ca/wg/beam/beam-test-2023/drafts/t9-beam-flux-technical-note.)
# 3. measures the TOF and associated momentum for each particle
# 4. produces many plots in the ../new_pdf(png)_results folders
# 5. outputs the number of particles, run characteristics, TOF and momentum information to the output file set in the config file
# written by acraplet, alie.craplet17@imperial.ac.uk
################################################################## 

config_file_name = sys.argv[1]

with open(config_file_name) as file:
    config = json5.load(file)["BeamDataAnalysis"]
print(config)

leadGlassID = config["channelNames"].index("PbGlass")

#make the analysis class
BeamDataAna = lm.LowMomentumAnalysis(config)

#open the data file 
BeamDataAna.openDataFile()

#make the helper, higher level variables  
BeamDataAna.makeSumTS()
BeamDataAna.makeSumTSwindow2()
BeamDataAna.makeSumDownstreamACTs()
BeamDataAna.makeSumACT1()
BeamDataAna.makeSumACT1window2()

#select events with exactly one coincidence (set in the config file)
BeamDataAna.nCoincidenceSelection()

#check the distribution of WholeWaveformIntPE against sumTS to check if cut is sensible
if "matchedHit0_Window2IntPE" in BeamDataAna.getBranchList(0):
    BeamDataAna.plot2DHistFromBranches((config["channelNames"].index("PbGlass")), "matchedHit0_Window2IntPE", 0, "sumTSwindow2", "(PE)", "(PE)", "sumTSwindow2_Window2IntPe_vsMatchedHit0_Window2IntPE_nCoincidence_noTSselection", True, [200, 300], [[0, 60], [0, 3000]])

#select low energy deposition in the TS that it is not 2-events
# The high enough charge deposited isn't necessary anymore, we have 2+2 coincidence now 
BeamDataAna.TStotalChargeSelection()

#This can be useful to have a look out: timing of hits
#add a new branch with the delay between the centre of the window and the peak time. 
if BeamDataAna.WindowBoundsAreAvailable:
    BeamDataAna.addOperationBranchToAllDetectors("delayBetweenCentreWindowAndPeakTime", "peakHit0_SignalTimeCorrected", "-", "matchedHit0_WindowCentralTimeCorrected")

#based on the -16ns to 45ns window selection, ID all particles that we have in this run, values in the config file
BeamDataAna.makeAllParticleSelection()

#Not yet available but soon to be: automated way to identify particles for the low momentum setup:
# BeamDataAna.findOptimalMuElCuts()


#make the 2D plots indicating where the cut lines are 
if BeamDataAna.isLowMomentum:
    BeamDataAna.plotAll2DSelections(True)


#Make plots and fit the lead glass charge distribution in the Lead Glass for muon and electron-like events, can be useful but not essential
BeamDataAna.fitMuonsAndElectronLGPeaks()

#using all the available particles measure the beam momentum with bins of 0.1, calculates the systematic error
#using many throws of the covariance matrix, see TN section III. C. 3, this is slow. 
BeamDataAna.measureMomentumUsingTOF(0.1)

#Make n= bins equally populated in terms of the Trigger scintillator 10 wholeWaveformIntPE charge and check the resolution of the time of flight there which should follow a 1/sqrt(TScharge) logic, work in progress, this is not needed anymore but if you want to compare the plots with the TN I leave this here
#BeamDataAna.measureElTOFresolutionFunctionOfTScharge(10)

#Useful to know: config["channelNames"].index("PbGlass") gives the index of the lead glass detector.

#for all the particles, plot the 1D histogram corresponding to certain high level branches that can be useful
BeamDataAna.plotBranchHistForAllParticles(0, "sumACT1", 5, True)
BeamDataAna.plotBranchHistForAllParticles(0, "sumDownstreamACTs", 5, True)

if BeamDataAna.thereIsSecondWindow:
    #only if we have calculated the second integration window can look at the TS distribution 
    BeamDataAna.plotBranchHistForAllParticles(0, "sumTSwindow2", 25, True)

#Look at the windowIntPE for all the particles for some interesting detectors 
if BeamDataAna.isLowMomentum:
    detectors = ["ACT0L", "ACT0R", "ACT1L", "ACT1R", "ACT2L", "ACT2R", "ACT3L", "ACT3R", "PbGlass"]
else:
    detectors = ["HD11", "HD12", "HD13", "HD14", "ACT3L", "ACT3R", "PbGlass", "TriggerScint"]


for detector in detectors:
    BeamDataAna.plotBranchHistForAllParticles(config["channelNames"].index(detector), "matchedHit0_WindowIntPE", 0.2, True, [0, 50])



#Output the results as a csv file, name of the output file in the config file 
BeamDataAna.outputResults()


#If interestested, one can study the weird electrons
if BeamDataAna.isLowMomentum:
    muonLikeWeirdElectron = BeamDataAna.muonLikeWeirdElectronArray
    pionLikeWeirdElectron = BeamDataAna.pionLikeWeirdElectronArray