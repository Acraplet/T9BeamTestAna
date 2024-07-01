import sys
import os

import json5

import numpy as np

import lowMomentum_analysis as lm

import matplotlib.pyplot as plt

from scipy.optimize import curve_fit

config_file_name = sys.argv[1]

with open(config_file_name) as file:
    config = json5.load(file)["BeamDataAnalysis"]
print(config)

leadGlassID = config["channelNames"].index("PbGlass")

#make the analysis class
BeamDataAna = lm.LowMomentumAnalysis(config)

BeamDataAna.correctParticleTSdEdx("muon")
BeamDataAna.correctParticleTSdEdx("pion")
BeamDataAna.correctParticleTSdEdx("electron")
BeamDataAna.correctParticleTSdEdx("proton")


#open the data file 
BeamDataAna.openDataFile()

#make the helper, higher level variables  
BeamDataAna.makeSumTS()
BeamDataAna.makeSumTSwindow2()
BeamDataAna.makeSumDownstreamACTs()
BeamDataAna.makeSumACT1()
BeamDataAna.makeSumDownstreamACTsWindow2()
BeamDataAna.makeSumACT1window2()

#get some efficiency ideas

# print("nCoincidence>0")
# hasMoreThan0 = BeamDataAna.arrayData[0]["SignalTimeMatchedTOF1"].map(len)>0

# print(hasMoreThan0)
# # hasMoreThan0 = np.where(hasMoreThan0 == True, 1, 0)
# _ = BeamDataAna.makeNewDataFrameFromSelection(BeamDataAna.getArrayData(), hasMoreThan0)

# print("nCoincidence==1")
# has1 = BeamDataAna.arrayData[0]["SignalTimeMatchedTOF1"].map(len)==1

# # has1 = np.where(has1 == True, 1, 0)
# # print(sum(has1), len(has1), sum(has1)/len(has1) *100)


# _ = BeamDataAna.makeNewDataFrameFromSelection(BeamDataAna.getArrayData(), has1)

# print("nCoincidence==1 and sumTS>240")
# isLargerThan240 = BeamDataAna.getSelectionBasedOnCondition(0, "sumTS", ">=", 240)

# a = np.where(has1 == True, isLargerThan240, False)
# # a = np.where(a == True, 1, 0)

# # print(sum(a), len(a), sum(a)/len(a)*100)


# _ = BeamDataAna.makeNewDataFrameFromSelection(BeamDataAna.getArrayData(), a)

# print("nCoincidence==1 and sumTSwindow<700")
# isSmallerThan700 = BeamDataAna.getSelectionBasedOnCondition(0, "sumTSwindow2", "<=", 700)

# b = np.where(has1 == True, isSmallerThan700, False)

# # print(b)
# # b = np.where(b == True, 1, 0)

# print(sum(b), len(b), sum(b)/len(b)*100)


# _ = BeamDataAna.makeNewDataFrameFromSelection(BeamDataAna.getArrayData(), b)

# print("nCoincidence==1 and sumTS>240 and sumTSwindow<700")

# c =  np.where(a == True, b, False)
# # c = np.where(c == True, 1, 0)
# # print(sum(c), len(c), sum(c)/len(c)*100)


# _ = BeamDataAna.makeNewDataFrameFromSelection(BeamDataAna.getArrayData(), c)

# print("nCoincidence==2")
# has2 = BeamDataAna.arrayData[0]["SignalTimeMatchedTOF1"].map(len)==2
# _ = BeamDataAna.makeNewDataFrameFromSelection(BeamDataAna.getArrayData(), has2)

# print("nCoincidence>=3")
# has3ormore = BeamDataAna.arrayData[0]["SignalTimeMatchedTOF1"].map(len)>=3
# _ = BeamDataAna.makeNewDataFrameFromSelection(BeamDataAna.getArrayData(), has3ormore)


# print(BeamDataAna.getBranchList(0))

#select events with exactly one coincidence (set in the config file)
BeamDataAna.nCoincidenceSelection()

BeamDataAna.plotAll2DSelections(True)


#check the distribution of WholeWaveformIntPE against sumTS to check if cut is sensible
if "matchedHit0_Window2IntPE" in BeamDataAna.getBranchList(0):
    #long
    BeamDataAna.plot2DHistFromBranches((config["channelNames"].index("PbGlass")), "matchedHit0_Window2IntPE", 0, "sumTSwindow2", "(PE)", "(PE)", "sumTSwindow2_Window2IntPe_vsMatchedHit0_Window2IntPE_nCoincidence_noTSselection", True, [200, 300], [[0, 60], [0, 2000]])
    #short
    BeamDataAna.plot2DHistFromBranches((config["channelNames"].index("PbGlass")), "matchedHit0_Window2IntPE", 0, "sumTS", "(PE)", "(PE)", "sumTS_Window2IntPe_vsMatchedHit0_WindowIntPE_nCoincidence_noTSselection", True, [200, 300], [[0, 60], [0, 2000]])

#select low energy deposition in the TS but high eneough that it doesn't look like failed coincidence
BeamDataAna.TStotalChargeSelection()




#This can be useful to have a look out: timing of hits
#add a new branch with the delay between the centre of the window and the peak time. 
if BeamDataAna.WindowBoundsAreAvailable:
    BeamDataAna.addOperationBranchToAllDetectors("delayBetweenCentreWindowAndFirstPeakTime", "peakHit0_SignalTimeCorrected", "-", "matchedHit0_WindowCentralTimeCorrected")
    BeamDataAna.addOperationBranchToAllDetectors("delayBetweenCentreWindowAndSecondPeakTime", "peakHit1_SignalTimeCorrected", "-", "matchedHit0_WindowCentralTimeCorrected")

#based on the -16ns to 45ns window selection, ID all particles that we have in this run, values in the config file
BeamDataAna.makeAllParticleSelection()


#Fit the lead glass charge distribution in the Lead Glass
#for muon and electron-like events. 
BeamDataAna.fitMuonsAndElectronLGPeaks()

# BeamDataAna.fitMuonsAndPionsACTPeaks()
BeamDataAna.plotMuonsAndPionsACTseparation()


BeamDataAna.findOptimalPiMuElCuts("p2e")

raise end



#BeamDataAna.measureElTOFresolutionFunctionOfTScharge([6, 6, 5, 5, 5, 4])

BeamDataAna.plotBranchHistForAllParticles(leadGlassID, "MaxVoltage", 0.01, True, [-0.02, 1.5], True, False)

BeamDataAna.plotBranchHistForAllParticles(leadGlassID, "matchedHit0_WindowIntPE", 0.1, True, [-0.02, 25], False, False)

#using all the available particles measure the beam momentum with bins of 0.1 
BeamDataAna.measureMomentumUsingTOF(0.1)


#BeamDataAna.estimateSystematicErrorTOF()

fig, ax = plt.subplots(1, 1, figsize = (16, 9))
fig2, ax2 = plt.subplots(1, 1, figsize = (16, 9))

for i in range(8, 16):
    BeamDataAna.plotBranchHistForAllParticles(i, "delayBetweenCentreWindowAndSecondPeakTime", 2, True, [-150, 150], True, True)
    BeamDataAna.plotBranchHistForAllParticles(i, "delayBetweenCentreWindowAndFirstPeakTime", 2, True, [-150, 150], True, True)
    # fig3, ax3 = plt.subplots(1, 1, figsize = (16, 9))

    # BeamDataAna.plotBranchHistForAllParticles(i, "peakHit0_SignalTimeCorrected", 0.02, True, [-10, 10])

    #plot the narrow integration window
    BeamDataAna.plot1DHist(BeamDataAna.pionArray[i]["matchedHit0_WindowIntPE"], 2, "window [-5, 15] int. charge (PE)", "Occurences", "%s"%config["channelNames"][i], "Narrow  integration window \n Run %i - Momentum %i MeV/c - n = %.3f"%(BeamDataAna.runNumber, BeamDataAna.runMomentum, BeamDataAna.runRefractiveIndex), ax, fig, True, None, False)

    #plot the wide integration window
    BeamDataAna.plot1DHist(BeamDataAna.pionArray[i]["matchedHit0_Window2IntPE"], 2, "window [-50, 150] int. charge (PE)", "Occurences", "%s"%config["channelNames"][i], "Wide  integration window \n Run %i - Momentum %i MeV/c - n = %.3f"%(BeamDataAna.runNumber, BeamDataAna.runMomentum, BeamDataAna.runRefractiveIndex), ax2, fig2, True, [0, 600], False)

    #we do not used sumTS anymore, no need to flod the output folder with useless plots
    # BeamDataAna.plot2DHistFromBranches(i, "sumTS", i, "matchedHit0_Window2IntPE", "(PE)", "(PE)", "sumTS_vs_%s-WindowIntPE_nCoincidence_noTSselection"%(config["channelNames"][i]), True, [200, 300], [[0, 1500], [0, 3000/8]])

ax.grid()
ax2.grid()

fig.savefig("../new_pdf_results/TOFwindowIntPE_narrowNew_Run%i.pdf"%(BeamDataAna.runNumber))
fig.savefig("../new_png_results/TOFwindowIntPE_narrowNew_Run%i.png"%(BeamDataAna.runNumber))
fig2.savefig("../new_pdf_results/TOFwindow2IntPE_wideNew_Run%i.pdf"%(BeamDataAna.runNumber))
fig2.savefig("../new_png_results/TOFwindow2IntPE_wideNew_Run%i.png"%(BeamDataAna.runNumber))



#Useful to know: config["channelNames"].index("PbGlass") gives the index of the lead glass detector.

#for all the particles, plot the 1D histogram corresponding to certain high level branches that can be useful
BeamDataAna.plotBranchHistForAllParticles(0, "sumACT1", 0.1, True, [0, 50], False, True)
BeamDataAna.plotBranchHistForAllParticles(0, "sumACT1window2", 0.1, True, [0, 50], False, True)



if BeamDataAna.thereIsSecondWindow:
    #only if we have calculated the second integration window can look at the TS distribution 
    BeamDataAna.plotBranchHistForAllParticles(0, "sumTSwindow2", 25, True, None, False, True)

#Look at the windowIntPE for all the particles for some interesting detectors 
# for detector in ["ACT0L", "ACT0R", "ACT1L", "ACT1R", "ACT2L", "ACT2R", "ACT3L", "ACT3R", "PbGlass"]:
#     BeamDataAna.plotBranchHistForAllParticles(config["channelNames"].index(detector), "matchedHit0_WindowIntPE", 0.2, True, [0, 50])


BeamDataAna.plotBranchHistForAllParticles(0, "sumDownstreamACTs", 0.2, True, [0, 100], False, True)
BeamDataAna.plotBranchHistForAllParticles(5, "sumDownstreamACTsWindow2", 0.2, True, [0, 100], False, True)


BeamDataAna.plotBranchHistForAllParticles(0, "matchedHit0_TOF", 0.1, True, None, False, True)







#Make n= bins equally populated in terms of the Trigger scintillator 10 wholeWaveformIntPE charge 
#BeamDataAna.measureElTOFresolutionFunctionOfTScharge(10)

#Output the results as a csv file
#BeamDataAna.outputResults()


#If interestested, one can study the weird electrons
muonLikeWeirdElectron = BeamDataAna.muonLikeWeirdElectronArray

pionLikeWeirdElectron = BeamDataAna.pionLikeWeirdElectronArray

#plot 2d hist of the selection for weird electrons:

BeamDataAna.plot2DHist(muonLikeWeirdElectron[leadGlassID]["sumACT1"], muonLikeWeirdElectron[leadGlassID]["sumDownstreamACTs"], [0.5, 1], "sumACT1", "(PE)", "sumDownstreamACTs", "(PE)", None, None, True, "Muon-likeWeirdElectrons")

BeamDataAna.plot2DHist(pionLikeWeirdElectron[leadGlassID]["sumACT1"], pionLikeWeirdElectron[leadGlassID]["sumDownstreamACTs"], [1, 0.5], "sumACT1", "(PE)", "sumDownstreamACTs", "(PE)", None, None, True, "Pion-LikeWeirdElectrons", [-1, 30])


#raise end
fig, ax = plt.subplots(1, 1, figsize = (16, 9))
title = "TimeOfFlight"

_, muonWEmeanTOF, muonWEstdTOF = BeamDataAna.calculateTOF(muonLikeWeirdElectron[leadGlassID]["matchedHit0_TOF"])

BeamDataAna.plot1DHist(muonLikeWeirdElectron[leadGlassID]["matchedHit0_TOF"], 0.1, "TOF (ns)", "Occurences/0.1ns", "Muon-looking weird electrons\nfitted TOF: %.2f +/- %.2f"%(muonWEmeanTOF, muonWEstdTOF), "Time of flight of weird electrons", ax, fig)

_, pionWEmeanTOF, pionWEstdTOF = BeamDataAna.calculateTOF(pionLikeWeirdElectron[leadGlassID]["matchedHit0_TOF"])

BeamDataAna.plot1DHist(pionLikeWeirdElectron[leadGlassID]["matchedHit0_TOF"], 0.1, "TOF (ns)", "Occurences/0.1ns", "Pion-looking weird electrons\nfitted TOF: %.2f +/- %.2f"%(pionWEmeanTOF, pionWEstdTOF), "Time of flight of weird electrons", ax, fig)

_, muonmeanTOF, muonstdTOF = BeamDataAna.calculateTOF(BeamDataAna.muonArray[leadGlassID]["matchedHit0_TOF"])

BeamDataAna.plot1DHist(BeamDataAna.muonArray[leadGlassID]["matchedHit0_TOF"], 0.1, "TOF (ns)", "Occurences/0.1ns", "Muons\nfitted TOF: %.2f +/- %.2f"%(muonmeanTOF, muonstdTOF), "Time of flight of weird electrons", ax, fig)

_, pionmeanTOF, pionstdTOF = BeamDataAna.calculateTOF(BeamDataAna.pionArray[leadGlassID]["matchedHit0_TOF"])

BeamDataAna.plot1DHist(BeamDataAna.pionArray[leadGlassID]["matchedHit0_TOF"], 0.1, "TOF (ns)", "Occurences/0.1ns", "Pions\nfitted TOF: %.2f +/- %.2f"%(pionmeanTOF, pionstdTOF), "Time of flight of weird electrons", ax, fig)

ax.grid()

plt.savefig("../new_pdf_results/WeirdElectrons_%s_Run%i.pdf"%(title, BeamDataAna.runNumber))
plt.savefig("../new_png_results/WeirdElectrons_%s_Run%i.png"%(title, BeamDataAna.runNumber))





fig, ax = plt.subplots(1, 1, figsize = (16, 9))
title = "matchedHit0_WindowIntPE"

BeamDataAna.plot1DHist(muonLikeWeirdElectron[leadGlassID]["matchedHit0_WindowIntPE"], 0.5, "WindowIntPE", "Occurences/0.5(a.u.)", "Muon-looking weird electrons", "Charge deposited in lead-glass for weird electrons", ax, fig, True)

BeamDataAna.plot1DHist(pionLikeWeirdElectron[leadGlassID]["matchedHit0_WindowIntPE"], 0.5, "WindowIntPE", "Occurences/0.5(a.u.)", "Pion-looking weird electrons", "Charge deposited in lead-glass for weird electrons", ax, fig, True)

BeamDataAna.plot1DHist(BeamDataAna.muonArray[leadGlassID]["matchedHit0_WindowIntPE"], 0.5, "WindowIntPE", "Occurences/0.5(a.u.)", "Muons", "Charge deposited in lead-glass for weird electrons", ax, fig, True)

BeamDataAna.plot1DHist(BeamDataAna.pionArray[leadGlassID]["matchedHit0_WindowIntPE"], 0.5, "WindowIntPE", "Occurences/0.5(a.u.)", "Pions", "Charge deposited in lead-glass for weird electrons", ax, fig, True)

#ax.grid()

plt.savefig("../new_pdf_results/WeirdElectrons_%s_Run%i.pdf"%(title, BeamDataAna.runNumber))
plt.savefig("../new_png_results/WeirdElectrons_%s_Run%i.png"%(title, BeamDataAna.runNumber))


for i in range(10):
    plt.close()

branchList = ["matchedHit0_WindowIntPE","delayBetweenCentreWindowAndFirstPeakTime"]

#branchList = ["Pedestal", "PedestalSigma", "delayBetweenCentreWindowAndFirstPeakTime", "delayBetweenCentreWindowAndSecondPeakTime", "sumDownstreamACTs", "sumACT1"]


list_xlimits = [[-2,  50], [-50, 50], [0, 25], None, None]
#list_xlimits = [[1, 2], [0, 1], [-50, 150],  [-50, 200],  [-30, 30], None ]

binsList = [0.5, 0.5, 0.3, 1, 2]
#binsList = [0.005, 0.005, 3, 3, 1, 1, 1, 1 ]
 
for detectorName in ["ACT0R", "ACT0L"]:
#, "ACT2L", "ACT3L", "ACT2R", "ACT3R"]:
    for branchID in range(len(branchList)):
        fig, ax = plt.subplots(1, 1, figsize = (16, 9))
        branch = branchList[branchID]
        bin = binsList[branchID] 
        xlimits = list_xlimits[branchID]
        detector = config["channelNames"].index(detectorName)
        title = "%s_%s"%(detectorName, branch)

        BeamDataAna.plot1DHist(muonLikeWeirdElectron[detector][branch], bin, "%s %s"%(detectorName, branch),  "Occurences", "Muon-looking weird electrons", "%s in %s for weird electrons, muons, pions"%(branch, detectorName), ax, fig, False, xlimits, False, True)

        BeamDataAna.plot1DHist(pionLikeWeirdElectron[detector][branch], bin, "%s %s"%(detectorName, branch),  "Occurences", "Pion-looking weird electrons", "%s in %s for weird electrons, muons, pions"%(branch, detectorName), ax, fig, False, xlimits, False, True)

        BeamDataAna.plot1DHist(BeamDataAna.muonArray[detector][branch], bin, "%s %s"%(detectorName, branch),  "Occurences", "Muons", "%s in %s for weird electrons, muons, pions"%(branch, detectorName), ax, fig, False, xlimits, False, True)

        BeamDataAna.plot1DHist(BeamDataAna.pionArray[detector][branch], bin, "%s %s"%(detectorName, branch), "Occurences", "Pions", "%s in %s for weird electrons, muons, pions"%(branch, detectorName), ax, fig, True, xlimits, False, True)

        ax.grid()
        if xlimits != None:
            ax.set_xlim(xlimits)

        plt.savefig("../%s/WeirdElectrons_%s_Run%i.pdf"%(BeamDataAna.saving_folder_path_pdf,title, BeamDataAna.runNumber))
        plt.savefig("../%s/WeirdElectrons_%s_Run%i.png"%(BeamDataAna.saving_folder_path_png, title, BeamDataAna.runNumber))

        plt.close()


raise end
##############
#new module: to measure the optimal separation el/mu, chose from p = purity, pe = purity * efficiency, p2e = purity ^2 * efficiency
#need to do this beforehand 
BeamDataAna.findOptimalMuElCuts("p2e", True)


#BeamDataAna.measureElTOFresolutionFunctionOfTScharge([6, 6, 5, 5, 5, 4])

BeamDataAna.plotBranchHistForAllParticles(leadGlassID, "MaxVoltage", 0.01, True, [-0.02, 1.5], True, False)

BeamDataAna.plotBranchHistForAllParticles(leadGlassID, "matchedHit0_WindowIntPE", 0.1, True, [-0.02, 25], False, False)

#using all the available particles measure the beam momentum with bins of 0.1 
BeamDataAna.measureMomentumUsingTOF(0.1)


#BeamDataAna.estimateSystematicErrorTOF()

fig, ax = plt.subplots(1, 1, figsize = (16, 9))
fig2, ax2 = plt.subplots(1, 1, figsize = (16, 9))

for i in range(8, 16):
    BeamDataAna.plotBranchHistForAllParticles(i, "delayBetweenCentreWindowAndSecondPeakTime", 2, True, [-150, 150], True, True)
    BeamDataAna.plotBranchHistForAllParticles(i, "delayBetweenCentreWindowAndFirstPeakTime", 2, True, [-150, 150], True, True)
    # fig3, ax3 = plt.subplots(1, 1, figsize = (16, 9))

    # BeamDataAna.plotBranchHistForAllParticles(i, "peakHit0_SignalTimeCorrected", 0.02, True, [-10, 10])

    #plot the narrow integration window
    BeamDataAna.plot1DHist(BeamDataAna.pionArray[i]["matchedHit0_WindowIntPE"], 2, "window [-5, 15] int. charge (PE)", "Occurences", "%s"%config["channelNames"][i], "Narrow  integration window \n Run %i - Momentum %i MeV/c - n = %.3f"%(BeamDataAna.runNumber, BeamDataAna.runMomentum, BeamDataAna.runRefractiveIndex), ax, fig, True, None, False)

    #plot the wide integration window
    BeamDataAna.plot1DHist(BeamDataAna.pionArray[i]["matchedHit0_Window2IntPE"], 2, "window [-50, 150] int. charge (PE)", "Occurences", "%s"%config["channelNames"][i], "Wide  integration window \n Run %i - Momentum %i MeV/c - n = %.3f"%(BeamDataAna.runNumber, BeamDataAna.runMomentum, BeamDataAna.runRefractiveIndex), ax2, fig2, True, [0, 600], False)

    #we do not used sumTS anymore, no need to flod the output folder with useless plots
    # BeamDataAna.plot2DHistFromBranches(i, "sumTS", i, "matchedHit0_Window2IntPE", "(PE)", "(PE)", "sumTS_vs_%s-WindowIntPE_nCoincidence_noTSselection"%(config["channelNames"][i]), True, [200, 300], [[0, 1500], [0, 3000/8]])

ax.grid()
ax2.grid()

fig.savefig("../new_pdf_results/TOFwindowIntPE_narrowNew_Run%i.pdf"%(BeamDataAna.runNumber))
fig.savefig("../new_png_results/TOFwindowIntPE_narrowNew_Run%i.png"%(BeamDataAna.runNumber))
fig2.savefig("../new_pdf_results/TOFwindow2IntPE_wideNew_Run%i.pdf"%(BeamDataAna.runNumber))
fig2.savefig("../new_png_results/TOFwindow2IntPE_wideNew_Run%i.png"%(BeamDataAna.runNumber))



#Useful to know: config["channelNames"].index("PbGlass") gives the index of the lead glass detector.

#for all the particles, plot the 1D histogram corresponding to certain high level branches that can be useful
BeamDataAna.plotBranchHistForAllParticles(0, "sumACT1", 0.1, True, [0, 50], False, True)
BeamDataAna.plotBranchHistForAllParticles(0, "sumACT1window2", 0.1, True, [0, 50], False, True)



if BeamDataAna.thereIsSecondWindow:
    #only if we have calculated the second integration window can look at the TS distribution 
    BeamDataAna.plotBranchHistForAllParticles(0, "sumTSwindow2", 25, True, None, False, True)

#Look at the windowIntPE for all the particles for some interesting detectors 
# for detector in ["ACT0L", "ACT0R", "ACT1L", "ACT1R", "ACT2L", "ACT2R", "ACT3L", "ACT3R", "PbGlass"]:
#     BeamDataAna.plotBranchHistForAllParticles(config["channelNames"].index(detector), "matchedHit0_WindowIntPE", 0.2, True, [0, 50])


BeamDataAna.plotBranchHistForAllParticles(0, "sumDownstreamACTs", 0.2, True, [0, 100], False, True)
BeamDataAna.plotBranchHistForAllParticles(5, "sumDownstreamACTsWindow2", 0.2, True, [0, 100], False, True)


BeamDataAna.plotBranchHistForAllParticles(0, "matchedHit0_TOF", 0.1, True, None, False, True)







#Make n= bins equally populated in terms of the Trigger scintillator 10 wholeWaveformIntPE charge 
#BeamDataAna.measureElTOFresolutionFunctionOfTScharge(10)

#Output the results as a csv file
#BeamDataAna.outputResults()


#If interestested, one can study the weird electrons
muonLikeWeirdElectron = BeamDataAna.muonLikeWeirdElectronArray

pionLikeWeirdElectron = BeamDataAna.pionLikeWeirdElectronArray

#plot 2d hist of the selection for weird electrons:

BeamDataAna.plot2DHist(muonLikeWeirdElectron[leadGlassID]["sumACT1"], muonLikeWeirdElectron[leadGlassID]["sumDownstreamACTs"], [0.5, 1], "sumACT1", "(PE)", "sumDownstreamACTs", "(PE)", None, None, True, "Muon-likeWeirdElectrons")

BeamDataAna.plot2DHist(pionLikeWeirdElectron[leadGlassID]["sumACT1"], pionLikeWeirdElectron[leadGlassID]["sumDownstreamACTs"], [1, 0.5], "sumACT1", "(PE)", "sumDownstreamACTs", "(PE)", None, None, True, "Pion-LikeWeirdElectrons", [-1, 30])


#raise end
fig, ax = plt.subplots(1, 1, figsize = (16, 9))
title = "TimeOfFlight"

_, muonWEmeanTOF, muonWEstdTOF = BeamDataAna.calculateTOF(muonLikeWeirdElectron[leadGlassID]["matchedHit0_TOF"])

BeamDataAna.plot1DHist(muonLikeWeirdElectron[leadGlassID]["matchedHit0_TOF"], 0.1, "TOF (ns)", "Occurences/0.1ns", "Muon-looking weird electrons\nfitted TOF: %.2f +/- %.2f"%(muonWEmeanTOF, muonWEstdTOF), "Time of flight of weird electrons", ax, fig)

_, pionWEmeanTOF, pionWEstdTOF = BeamDataAna.calculateTOF(pionLikeWeirdElectron[leadGlassID]["matchedHit0_TOF"])

BeamDataAna.plot1DHist(pionLikeWeirdElectron[leadGlassID]["matchedHit0_TOF"], 0.1, "TOF (ns)", "Occurences/0.1ns", "Pion-looking weird electrons\nfitted TOF: %.2f +/- %.2f"%(pionWEmeanTOF, pionWEstdTOF), "Time of flight of weird electrons", ax, fig)

_, muonmeanTOF, muonstdTOF = BeamDataAna.calculateTOF(BeamDataAna.muonArray[leadGlassID]["matchedHit0_TOF"])

BeamDataAna.plot1DHist(BeamDataAna.muonArray[leadGlassID]["matchedHit0_TOF"], 0.1, "TOF (ns)", "Occurences/0.1ns", "Muons\nfitted TOF: %.2f +/- %.2f"%(muonmeanTOF, muonstdTOF), "Time of flight of weird electrons", ax, fig)

_, pionmeanTOF, pionstdTOF = BeamDataAna.calculateTOF(BeamDataAna.pionArray[leadGlassID]["matchedHit0_TOF"])

BeamDataAna.plot1DHist(BeamDataAna.pionArray[leadGlassID]["matchedHit0_TOF"], 0.1, "TOF (ns)", "Occurences/0.1ns", "Pions\nfitted TOF: %.2f +/- %.2f"%(pionmeanTOF, pionstdTOF), "Time of flight of weird electrons", ax, fig)

ax.grid()

plt.savefig("../new_pdf_results/WeirdElectrons_%s_Run%i.pdf"%(title, BeamDataAna.runNumber))
plt.savefig("../new_png_results/WeirdElectrons_%s_Run%i.png"%(title, BeamDataAna.runNumber))





fig, ax = plt.subplots(1, 1, figsize = (16, 9))
title = "sumTS"

BeamDataAna.plot1DHist(muonLikeWeirdElectron[leadGlassID]["sumTS"], 10, "SumTS", "Occurences/0.1(PE)", "Muon-looking weird electrons", "Total charge deposited in TS for weird electrons", ax, fig)

BeamDataAna.plot1DHist(pionLikeWeirdElectron[leadGlassID]["sumTS"], 10, "sumTS", "Occurences/0.1(PE)", "Pion-looking weird electrons", "Total charge deposited in TS for weird electrons", ax, fig)

BeamDataAna.plot1DHist(BeamDataAna.muonArray[leadGlassID]["sumTS"], 10, "SumTS", "Occurences/10(PE)", "Muons", "Total charge deposited in TS for weird electrons", ax, fig)

BeamDataAna.plot1DHist(BeamDataAna.pionArray[leadGlassID]["sumTS"], 10, "sumTS", "Occurences/10(PE)", "Pions", "Total charge deposited in TS for weird electrons", ax, fig)

ax.grid()

plt.savefig("../new_pdf_results/WeirdElectrons_%s_Run%i.pdf"%(title, BeamDataAna.runNumber))
plt.savefig("../new_png_results/WeirdElectrons_%s_Run%i.png"%(title, BeamDataAna.runNumber))


for i in range(10):
    plt.close()

branchList = ["matchedHit0_WindowIntPE","delayBetweenCentreWindowAndFirstPeakTime"]

#branchList = ["Pedestal", "PedestalSigma", "delayBetweenCentreWindowAndFirstPeakTime", "delayBetweenCentreWindowAndSecondPeakTime", "sumDownstreamACTs", "sumACT1"]


list_xlimits = [[-2,  50], [-50, 50], [0, 25], None, None]
#list_xlimits = [[1, 2], [0, 1], [-50, 150],  [-50, 200],  [-30, 30], None ]

binsList = [0.5, 0.5, 0.3, 1, 2]
#binsList = [0.005, 0.005, 3, 3, 1, 1, 1, 1 ]
 
for detectorName in ["ACT0R", "ACT0L"]:
#, "ACT2L", "ACT3L", "ACT2R", "ACT3R"]:
    for branchID in range(len(branchList)):
        fig, ax = plt.subplots(1, 1, figsize = (16, 9))
        branch = branchList[branchID]
        bin = binsList[branchID] 
        xlimits = list_xlimits[branchID]
        detector = config["channelNames"].index(detectorName)
        title = "%s_%s"%(detectorName, branch)

        BeamDataAna.plot1DHist(muonLikeWeirdElectron[detector][branch], bin, "%s %s"%(detectorName, branch),  "Occurences", "Muon-looking weird electrons", "%s in %s for weird electrons, muons, pions"%(branch, detectorName), ax, fig, False, xlimits, False, True)

        BeamDataAna.plot1DHist(pionLikeWeirdElectron[detector][branch], bin, "%s %s"%(detectorName, branch),  "Occurences", "Pion-looking weird electrons", "%s in %s for weird electrons, muons, pions"%(branch, detectorName), ax, fig, False, xlimits, False, True)

        BeamDataAna.plot1DHist(BeamDataAna.muonArray[detector][branch], bin, "%s %s"%(detectorName, branch),  "Occurences", "Muons", "%s in %s for weird electrons, muons, pions"%(branch, detectorName), ax, fig, False, xlimits, False, True)

        BeamDataAna.plot1DHist(BeamDataAna.pionArray[detector][branch], bin, "%s %s"%(detectorName, branch), "Occurences", "Pions", "%s in %s for weird electrons, muons, pions"%(branch, detectorName), ax, fig, True, xlimits, False, True)

        ax.grid()
        if xlimits != None:
            ax.set_xlim(xlimits)

        plt.savefig("../%s/WeirdElectrons_%s_Run%i.pdf"%(BeamDataAna.saving_folder_path_pdf,title, BeamDataAna.runNumber))
        plt.savefig("../%s/WeirdElectrons_%s_Run%i.png"%(BeamDataAna.saving_folder_path_png, title, BeamDataAna.runNumber))

        plt.close()