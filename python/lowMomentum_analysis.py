#This is the helper code doing the particleID_final analysis, class based instead of the previous messy multiple functions approach

import uproot as ur
import matplotlib.pyplot as plt
import math
import numpy as np
import pandas as pd
import sys
import awkward as ak
from scipy.optimize import curve_fit
from collections import OrderedDict
import scipy.integrate as integrate
import os.path
from scipy.integrate import quad

import csv



#the mass of the particles in MeV/c
ms = OrderedDict()
ms['electron'] = 0.511
ms['muon'] = 105.658
ms['pion'] = 139.6
ms['proton'] = 938.3
ms['deuterium'] = 1876.

conv = 1.e9 #convert back to ns
c = 299792458 # m/s


def gaussian(x, amplitude, mean, std_dev):
    return amplitude * np.exp(-0.5 * ((x - mean) / std_dev) ** 2)

def fitGaussian(counts, bins):
    y = np.array(counts)
    x = (bins[1]-bins[0])/2 + np.array(bins)[:-1]
    #amplitude, mean, std
    initial_guess = [max(y),  x[y.argmax(axis = 0)], 1]
    # Fit the Gaussian function to the data points
    params, covariance = curve_fit(gaussian, x, y, p0=initial_guess)

    return params, covariance


def oneOverSqrtN(x, A, B):
        return np.sqrt(A/(x) + B)

class LowMomentumAnalysis:
    "This class sets up the analysis tools for either the low momentum or tagged gamma setups"
    def __init__(self, config):
        self.channelNames = config["channelNames"]
        self.dataFile = config["dataFile"]
        self.runNumber = config["runNumber"]
        self.runMomentum = config["runMomentum"]
        self.runRefractiveIndex = config["runRefractiveIndex"]
        self.referenceSelectionCutFile = config["referenceSelectionCutFile"]
        self.batchMode = config["batchMode"]
        self.saveRootFile = config["saveRootFile"]

        #Selection of events based on the number of coincident hits
        self.nCoincidenceSelectionBool = config["nCoincidenceSelectionBool"]
        self.nCoincidenceSelectionValue = config["nCoincidenceSelectionValue"]

        #Selection of events based on the dE/dx of particles in the trigger scintillator
        self.TStotalChargeSelectionBool = config["TStotalChargeSelectionBool"]
        
        if self.TStotalChargeSelectionBool:
            #self.TStotalChargeSelectionValue = config["TStotalChargeSelectionValue"] #this is technically not necessary anymore, with 2+2 coincidence
            #this is for 2 particle events
            self.TSwindow2totalChargeSelectionValue = config["TSwindow2totalChargeSelectionValue"]
        
        else:
            self.TStotalChargeSelectionBool = None
            self.TSwindow2totalChargeSelectionValue = None

        self.isLowMomentum = config["isLowMomentum"]

        self.downstreamACTs = ["ACT2L", "ACT2R", "ACT3L", "ACT3R"]


        self.openedFile = None
        #looking only at the window integrated charge
        #arrays holding the dataframes
        self.arrayData = []
        self.totalNumberOfEvents = None

        #Good event selection, by default
        #Has the number of coincidence that we want
        self.nCoincidenceSelectionPassed = None
        #doesn't deposit a lot of energy in the trigger scintillator
        #except if if it is a fast particle 
        self.TStotalChargeSelectionPassed = None
        self.TSwindow2totalChargeSelectionPassed = None


        #define some basic numbers
        self.numberOfTOFpmt = 4
        self.flag = -9999
        self.WindowBoundsAreAvailable = False

        #time of flight related items
        self.distanceTOF1toTOF0 = config["distanceTOF1toTOF0"]
        self.fractionalErrorDistanceTOF1toTOF0 = 0.003/config["distanceTOF1toTOF0"]
        self.momentumLossFractionalError = 0.15 #assume 15%
        self.electronMeanTOF = None

        #make the dataframes for the particles
        self.protonArray = None
        self.electronArray = None
        self.muonArray = None
        self.pionArray = None
        self.deuteriumArray = None

        #make the arry of bools, with the same shape as the original dataset with 
        #each particle type, try to apply the best possible cuts
        self.isProton = None
        self.isDeuterium = None
        self.isElectron = None
        self.isMuon = None
        self.isPion = None

        self.saving_folder_path_pdf = "pdf_2plus2Coincidence_fixedMuons"
        self.saving_folder_path_png = "png_2plus2Coincidence_fixedMuons"

        self.thereIsSecondWindow = False


        self.nProtons, self.nPions, self.nMuons, self.nDeuterium, self.nElectrons = None, None, None, None, None

        #get the selection items
        self.protonsTOFCut, self.protonsTOFMax = self.getProtonTOFSelectionBounds()
        

        if self.isLowMomentum:
            self.deuteriumTOFcut, self.deuteriumTOFmax = self.getDeuteriumTOFSelectionBounds()
    
        if self.isLowMomentum:
            self.ACTlinearA = config["ACTlinearA"]
            self.ACTlinearB = config["ACTlinearB"]

            self.horizontal_el = config["horizontal_el"]
            self.weirdElectronLGcut = config["weirdElectronLGcut"]

        #for deuterium/proton selection we only want to try to fit if we have a large number of events
        self.minNbEventsToFitTOF = 150

        #make dictionaries for the outputs
        #Tof
        self.dictTOFMean = {"electron": None, 
                            "muon": None,
                            "pion": None,
                            "proton": None,
                            "deuterium": None}

        self.dictTOFfitErrOnMean = {"electron": None, 
                            "muon": None,
                            "pion": None,
                            "proton": None,
                            "deuterium": None}
        
        self.dictTOFStd = {"electron": None, 
                            "muon": None,
                            "pion": None,
                            "proton": None,
                            "deuterium": None}
        
        self.dictTOFfitErrOnStd = {"electron": None, 
                            "muon": None,
                            "pion": None,
                            "proton": None,
                            "deuterium": None}
        

        #momentum
        self.dictMomentumMean = {"muon": None,
                            "pion": None,
                            "proton": None,
                            "deuterium": None}
        
        self.dictMomentumStatError = {"muon": None,
                            "pion": None,
                            "proton": None,
                            "deuterium": None}
        
        self.dictMomentumTotalError = {"muon": None,
                            "pion": None,
                            "proton": None,
                            "deuterium": None}
        
        
        #Number of particle fitted in the TOF dimension (useful for protons)
        self.dictTOFfittedNparticles = {"electron": None, 
                            "muon": None,
                            "pion": None,
                            "proton": None,
                            "deuterium": None}


        if self.isLowMomentum:
            #for the selection, check which particles we are looking for
            self.ACTLowerCut = config["ACTLowerCut"]
            self.piMuBorderACT = config["piMuBorderACT"]
            
            if self.runMomentum > 300:
                self.particleNamesList = ["electron", "muon", "pion", "proton",  "deuterium"]
            else:
                self.particleNamesList = ["electron", "muon", "pion"]
                
        else:
            self.particleNamesList = ["proton", "electron"]


        self.outputFileName = config["outputFileName"]

        #Dean's number of particle in each bunch study to remove deadtime, for now empty 
        self.probaBunch = 1

        #use throws of the dependance of sigma TOF on sumTSwindow2 to estimate the systematic error
        #values obtained with run 393 (widest range of sumTS) see TN
        self.TOF_fit_covariance = [[6.15153704, -1.25257584e-02],[-1.25257584e-02, 2.69301669e-05]] #values from run 393, see TN
        self.TOF_fit_mean_A = 14.46
        self.TOF_fit_mean_B = 0.069
            
    def setMinNbEventsToFitTOF(self,value):
        #set the minimum number of events that need to have passed any selection for the TOF-estimated momentum to be calculated, keeping a failry high number ensures that the statistical error is small
        self.minNbEventsToFitTOF = value

    def getProtonTOFSelectionBounds(self, p=None):
        #for plotting, it is useful to be able to get these bounds for any momentum. 
        if p == None:
            p = abs(self.runMomentum) #we need those bounds for selections, even if there are no expected protons
        TOFresolution = 0.35 #ns
        fiveSigmaOfPionTOF = self.momentumToTOF(p, 'pion') + 5 * TOFresolution
        protonTOFminus3ns = self.momentumToTOF(p, 'proton') - 3 
        protonTOFplus3ns = self.momentumToTOF(p, 'proton') + 3 
        deuteriumTOFminus5ns = self.momentumToTOF(p, 'deuterium') - 5 
        if self.isLowMomentum:
            #worry about deuterium
            return max(fiveSigmaOfPionTOF, protonTOFminus3ns), min(protonTOFplus3ns, (deuteriumTOFminus5ns+protonTOFplus3ns)/2)

        else:
            #no need to worry about deuterium
            return max(fiveSigmaOfPionTOF, protonTOFminus3ns), protonTOFplus3ns

        
    
    def getDeuteriumTOFSelectionBounds(self, p=None):
        #for plotting, it is useful to be able to get these bounds for any momentum. 
        if p == None:
            p = abs(self.runMomentum)
        TOFresolution = 0.35 #ns
        tenSigmaOfProtonTOF = self.momentumToTOF(p, 'proton') + 10 * TOFresolution
        deuteriumTOFminus5ns = self.momentumToTOF(p, 'deuterium') - 5 
        deutriumTOFplus5ns = self.momentumToTOF(p, 'deuterium') + 5 
        protonTOFplus5ns = self.momentumToTOF(p, 'proton') + 5 
        return max((deuteriumTOFminus5ns+protonTOFplus5ns)/2, deuteriumTOFminus5ns), deutriumTOFplus5ns
    
    
    def correctForTOFwrtElectron(self, tof):
        """"here we need to offset the TOF collected for each particle by the difference between the measured electron TOF and the physical elctron TOF, to account for any leftover cable length offset or calibration issues"""
        if self.electronMeanTOF == None:
            print("Electron TOF not measured, will have to measure later")
            TOF_array = self.getColumnDataFrameDetector("matchedHit0_TOF", 0, "electron") 
            _, self.electronMeanTOF, _ = self.calculateTOF(TOF_array)

        #if there is an offset in the electron flight time compared to the expected distance then we need to correct for that (cable lengths)
        electronTimeOffset = self.electronMeanTOF - self.distanceTOF1toTOF0 * conv / c

        print("The time offset between the electron mean TOF and the expected photon TOF is %.3fns"%electronTimeOffset)
        
        tof = tof - electronTimeOffset * self.distanceTOF1toTOF0

    
        return tof

    def correctParticleTSdEdx(self, particle):
        """Calculates, using the nominal beam momnetum and the NIST dataset the energy deposited in the trigger scintillators"""

        gamma = (np.sqrt(1 + (self.runMomentum/ms[particle])**2 ) - 1)
        beta = np.sqrt(1 - 1/gamma**2)
        kinetic_E = gamma * ms[particle]

        print("%s : Kinetic energy is: %.2f Mev/c, beta * gamma = %.1f"%(particle, kinetic_E, beta * gamma))

        TS_thickness = 1.2 #cm
        TS_density = 1.032 #g cm-3
        estimated_error_frac = self.momentumLossFractionalError
        stoppingPower = None
        if particle == "electron" or particle == "muon" or particle == "pion":
            print("Beta * gamma = %.1f, for %s"%(beta * gamma, particle))
            NIST_dataset = "../include/electronStoppingPowerPlasticScintillator.csv"
        elif particle == "proton" or particle == "deuterium":
            NIST_dataset = "../include/protonStoppingPowerPlasticScintillator.csv"
        
        else:
            #do not know how to handle deuterium yet
            return 0,0


        with open(NIST_dataset, mode = 'r') as file:
            psp = pd.read_csv(file) #psp = proton stopping power
        
        for i in range(0, len(psp)-1):
            #start at 1 header removal
            psp["Kinetic_energy"][i] = float(psp["Kinetic_energy"][i])
            psp["Total_st_pw"][i+1] = float(psp["Total_st_pw"][i+1])
            #find the point in the table corresponding to the momentum
            #needs to be ordered
            if kinetic_E >= psp["Kinetic_energy"][i] and kinetic_E < psp["Kinetic_energy"][i+1]:
                #make a weighted sum of the corresponding data points
                stoppingPower = (psp["Total_st_pw"][i+1] - psp["Total_st_pw"][i])/ (psp["Kinetic_energy"][i+1] - psp["Kinetic_energy"][i]) * (kinetic_E - psp["Kinetic_energy"][i]) + psp["Total_st_pw"][i]
                break

        
    
        stoppingPower = stoppingPower * TS_thickness * TS_density
        errorStoppingPower = stoppingPower * estimated_error_frac

        print(f"The stopping power for {particle} at {self.runMomentum} in {TS_thickness}cm of plastic scintillator is %.2f +/- %.2f MeV."%(stoppingPower, errorStoppingPower))

        ################ mylar window

        Mylar_thickness = 0.025 #cm
        Mylar_density = 1.4 #from G4 


        if particle == "electron" or particle == "muon" or particle == "pion":
            print("Beta * gamma = %.1f, for %s"%(beta * gamma, particle))
            NIST_dataset = "../include/electronStoppingPowerMylar.csv"
        elif particle == "proton" or particle == "deuterium":
            NIST_dataset = "../include/protonStoppingPowerMylar.csv"
        
        else:
            #do not know how to handle deuterium yet
            return 0,0


        with open(NIST_dataset, mode = 'r') as file:
            psp = pd.read_csv(file) #psp = proton stopping power
        
        for i in range(0, len(psp)-1):
            #start at 1 header removal
            psp["Kinetic_energy"][i] = float(psp["Kinetic_energy"][i])
            psp["Total_st_pw"][i+1] = float(psp["Total_st_pw"][i+1])
            #find the point in the table corresponding to the momentum
            #needs to be ordered
            if kinetic_E >= psp["Kinetic_energy"][i] and kinetic_E < psp["Kinetic_energy"][i+1]:
                #make a weighted sum of the corresponding data points
                stoppingPowerMylar = (psp["Total_st_pw"][i+1] - psp["Total_st_pw"][i])/ (psp["Kinetic_energy"][i+1] - psp["Kinetic_energy"][i]) * (kinetic_E - psp["Kinetic_energy"][i]) + psp["Total_st_pw"][i]
                break

        stoppingPowerMylar = stoppingPowerMylar * Mylar_thickness * Mylar_density
        errorStoppingPowerMylar = stoppingPowerMylar * estimated_error_frac

        print(f"The stopping power for {particle} at {self.runMomentum} in {Mylar_thickness}cm of Mylar is %.2f +/- %.2f MeV."%(stoppingPowerMylar, errorStoppingPowerMylar))


        return stoppingPower + stoppingPowerMylar, np.sqrt(errorStoppingPower**2 + errorStoppingPowerMylar**2)



    def TofToMomentum(self, tof, particle_label):
        #the tof needs to be the absolute flying time
        m = ms[particle_label]
        #account for the non-zero travel time of electrons, assume they travel at c
        # tof = tof - (self.distanceTOF1toTOF0) * conv /c
        
        p = m/np.sqrt(pow((tof) * c / (conv * self.distanceTOF1toTOF0), 2) - 1)
        return p
    
    def momentumToTOF(self, p, particle_label):
        m = ms[particle_label]
        TOF = (conv * self.distanceTOF1toTOF0) / c * np.sqrt((m*m)/(p*p) + 1)
        return TOF

    def openOneBranch(self, channelNumber):
        df_temp = self.openedFile[self.channelNames[channelNumber]].arrays(library = "pd")
        charge = pd.DataFrame(df_temp['WindowIntPE'].values.tolist())
        time = pd.DataFrame(df_temp['SignalTimeCorrected'].values.tolist())
        if 'Window2IntPE' in df_temp.columns:
            self.thereIsSecondWindow = True
            chargeWindow2 = pd.DataFrame(df_temp['Window2IntPE'].values.tolist())
            maxNbWindow2Events = np.array(chargeWindow2.shape)[1]


        
        #Calculate the max number of hits to form sensible column name
        maxNbMatchedEvents = np.array(charge.shape)[1]
        maxNbPeakEvents = np.array(time.shape)[1]

        #matched events informations
        names_windowIntPE=["matchedHit%i_WindowIntPE"%i for i in range(maxNbMatchedEvents)]
        names_TOF=["matchedHit%i_TOF"%i for i in range(maxNbMatchedEvents)]
        names_WindowUpperBound = ["matchedHit%i_WindowUpperTime"%i for i in range(maxNbMatchedEvents)]
        names_WindowLowerBound = ["matchedHit%i_WindowLowerTime"%i for i in range(maxNbMatchedEvents)]
        names_WindowCentralTime = ["matchedHit%i_WindowCentralTime"%i for i in range(maxNbMatchedEvents)]
        names_WindowCentralTimeCorrected = ["matchedHit%i_WindowCentralTimeCorrected"%i for i in range(maxNbMatchedEvents)]

        if self.thereIsSecondWindow:
            #second windowInformation, might not have the same format as the first window due to different size
            names_window2IntPE=["matchedHit%i_Window2IntPE"%i for i in range(maxNbWindow2Events)]
            names_Window2UpperBound = ["matchedHit%i_Window2UpperTime"%i for i in range(maxNbWindow2Events)]
            names_Window2LowerBound = ["matchedHit%i_Window2LowerTime"%i for i in range(maxNbWindow2Events)]
            

        #peak information
        names_IntPE=["peakHit%i_IntPE"%i for i in range(maxNbPeakEvents)]
        names_IntCharge=["peakHit%i_IntCharge"%i for i in range(maxNbPeakEvents)]
        names_SignalTimeCorrected=["peakHit%i_SignalTimeCorrected"%i for i in range(maxNbPeakEvents)]
        
        
        #Have a new column for TOF that will be filled either with the matched hit times or a flag at -9999
        #if the matching did not happen
        if 'SignalTimeMatchedTOF1' in df_temp.columns:
            print("SignalTimeMatched is available, using it to compute TOF")
            TOF = pd.DataFrame((ak.Array(df_temp['SignalTimeMatchedTOF1'].values.tolist())-ak.Array(df_temp['SignalTimeMatchedTOF0'].values.tolist())).tolist(), columns=names_TOF)
        
        else:
            print("SignalTimeMatched is not available, TOF will be set to %i"%self.flag)
            TOF = pd.DataFrame((df_temp['WindowIntPE']).values.tolist(), columns=names_TOF)
            for col in TOF.columns:
                TOF[col].values[:] = self.flag

        WindowIntPE = pd.DataFrame(df_temp['WindowIntPE'].values.tolist(), columns = names_windowIntPE)

        #peak information
        IntPE = pd.DataFrame(df_temp['IntPE'].values.tolist(), columns = names_IntPE)
        IntCharge = pd.DataFrame(df_temp['IntCharge'].values.tolist(), columns = names_IntCharge)
        SignalTimeCorrected = pd.DataFrame(df_temp['SignalTimeCorrected'].values.tolist(), columns = names_SignalTimeCorrected)

        #if we have information about the bounds
        if "WindowUpperTime" in df_temp.columns:
            self.WindowBoundsAreAvailable = True
            WindowUpperBound = pd.DataFrame(df_temp['WindowUpperTime'].values.tolist(), columns = names_WindowUpperBound)
            WindowLowerBound = pd.DataFrame(df_temp['WindowLowerTime'].values.tolist(), columns = names_WindowLowerBound)
            WindowCentralTime = pd.DataFrame(df_temp['WindowCentralTime'].values.tolist(), columns = names_WindowCentralTime)
            WindowCentralTimeCorrected = pd.DataFrame(df_temp['WindowCentralTimeCorrected'].values.tolist(), columns = names_WindowCentralTimeCorrected)

            df_temp = pd.concat([df_temp, WindowUpperBound], axis = 1)
            df_temp = pd.concat([df_temp, WindowLowerBound], axis = 1)
            df_temp = pd.concat([df_temp, WindowCentralTime], axis = 1)
            df_temp = pd.concat([df_temp, WindowCentralTimeCorrected], axis = 1)

        if self.thereIsSecondWindow:
            Window2UpperBound = pd.DataFrame(df_temp['Window2UpperTime'].values.tolist(), columns = names_Window2UpperBound)
            Window2LowerBound = pd.DataFrame(df_temp['Window2LowerTime'].values.tolist(), columns = names_Window2LowerBound)
            Window2IntPE = pd.DataFrame(df_temp['Window2IntPE'].values.tolist(), columns = names_window2IntPE)

            df_temp = pd.concat([df_temp, Window2UpperBound], axis = 1)
            df_temp = pd.concat([df_temp, Window2LowerBound], axis = 1)
            df_temp = pd.concat([df_temp, Window2IntPE], axis = 1)


    
    
        df_temp = pd.concat([df_temp, WindowIntPE], axis = 1)
        df_temp = pd.concat([df_temp, TOF], axis =1)
        df_temp = pd.concat([df_temp, IntPE], axis = 1)
        df_temp = pd.concat([df_temp, IntCharge], axis = 1)
        df_temp = pd.concat([df_temp, SignalTimeCorrected], axis =1)


        return df_temp

    def openDataFile(self):
        #only open the file once
        #if the plot saving folders do not already exist, create them
        os.makedirs("../%s"%self.saving_folder_path_png, exist_ok=True)
        os.makedirs("../%s"%self.saving_folder_path_pdf, exist_ok=True)

        if self.openedFile is None:
            print("Opening the data root file: %s"%self.dataFile)
            self.openedFile = ur.open(self.dataFile)
            availableChannels = [channel[:-2] for channel in self.openedFile.keys()]
            for channelNumber in range(len(self.channelNames)):
                print(f"Reading channel {self.channelNames[channelNumber]}...")
                if self.channelNames[channelNumber] in availableChannels:
                    df_temp = self.openOneBranch(channelNumber)
                    self.arrayData.append(df_temp)
                    self.totalNumberOfEvents = len(df_temp)
                    print(f"... done\n", end = "", flush=True)
                else:
                    #instead make a copy of the previous branch and set everything 
                    #to a flag value
                    df_temp = self.openOneBranch(channelNumber-1) * 0 + -9999
                    self.arrayData.append(df_temp)
                    print(f"... skipping channel")
            
        else:
            raise Exception("The file already seems to be open.")
        
    def makeSumDownstreamACTs(self):
        "Sum of the waveform integrated charge (PE) for all the ACT2, 3 PMTs"
        if self.isLowMomentum:
            sumDownsteamACTs = 0
            for downstreamACTpmt in self.downstreamACTs:
                if downstreamACTpmt in self.channelNames:
                    detectorID = self.channelNames.index(downstreamACTpmt)
                    sumDownsteamACTs += self.getDataFrameDetector(detectorID)["matchedHit0_WindowIntPE"]
                else:
                    print(f"Careful, PMT {downstreamACTpmt} is not in your dataset")
                    return 0
            self.addBranchToAllDetectors("sumDownstreamACTs", sumDownsteamACTs)
            
        else:
            print("This is the tagged photon set-up, not low momentum, not calculating the sum of downstream ACT light")
    
    def makeSumDownstreamACTsWindow2(self):
        "Sum of the waveform integrated charge (PE) for all the ACT2, 3 PMTs"
        if self.isLowMomentum:
            sumDownsteamACTs = 0
            for downstreamACTpmt in self.downstreamACTs:
                if downstreamACTpmt in self.channelNames:
                    detectorID = self.channelNames.index(downstreamACTpmt)
                    sumDownsteamACTs += self.getDataFrameDetector(detectorID)["matchedHit0_Window2IntPE"]
                else:
                    print(f"Careful, PMT {downstreamACTpmt} is not in your dataset")
                    return 0
            self.addBranchToAllDetectors("sumDownstreamACTsWindow2", sumDownsteamACTs)
            
        else:
            print("This is the tagged photon set-up, not low momentum, not calculating the sum of downstream ACT light")

    def getTotalNumberEvents(self):
        return self.totalNumberOfEvents

    def makeSumACT1window2(self):
        "Sum of the waveform integrated charge (PE) for all the ACT1 PMTs"
        sumACT1 = 0
        for ACTpmt in ["ACT1L", "ACT1R"]:
            if ACTpmt in self.channelNames:
                detectorID = self.channelNames.index(ACTpmt)
                sumACT1 += self.getDataFrameDetector(detectorID)["matchedHit0_Window2IntPE"]
            else:
                print(f"Careful, PMT {ACTpmt} is not in your dataset")
                return 0
        self.addBranchToAllDetectors("sumACT1window2", sumACT1)

    def makeSumACT1(self):
        "Sum of the waveform integrated charge (PE) for all the ACT1 PMTs"
        sumACT1 = 0
        for ACTpmt in ["ACT1L", "ACT1R"]:
            if ACTpmt in self.channelNames:
                detectorID = self.channelNames.index(ACTpmt)
                sumACT1 += self.getDataFrameDetector(detectorID)["matchedHit0_WindowIntPE"]
            else:
                print(f"Careful, PMT {ACTpmt} is not in your dataset")
                return 0
        self.addBranchToAllDetectors("sumACT1", sumACT1)

    def makeSumTS(self):
        "Sum of the window integrated charge (PE) for all the Trigger Scintillators PMTs"
        sumTS = 0
        for TSpmt in ["TOF00", "TOF01", "TOF02", "TOF03", "TOF10", "TOF11", "TOF12", "TOF13"]:
            if TSpmt in self.channelNames:
                detectorID = self.channelNames.index(TSpmt)
                sumTS += self.getDataFrameDetector(detectorID)["matchedHit0_WindowIntPE"]
            else:
                print(f"Careful, PMT {TSpmt} is not in your dataset")
                return 0
        
        self.addBranchToAllDetectors("sumTS", sumTS)
    
    def makeSumTSwindow2(self):
        "Sum of the second window integrated charge (PE) for all the Trigger Scintillators PMTs"
        if self.thereIsSecondWindow:
            sumTSwindow2 = 0
            for TSpmt in ["TOF00", "TOF01", "TOF02", "TOF03", "TOF10", "TOF11", "TOF12", "TOF13"]:
                if TSpmt in self.channelNames:
                    detectorID = self.channelNames.index(TSpmt)
                    sumTSwindow2 += self.getDataFrameDetector(detectorID)["matchedHit0_Window2IntPE"]
                else:
                    print(f"Careful, PMT {TSpmt} is not in your dataset")
                    return 0
            
            self.addBranchToAllDetectors("sumTSwindow2", sumTSwindow2)

    
    def getDataFrameAllDetectors(self, particle = None):
        # print("The data has ", len(self.arrayData),"entries which hold the following column in the dataframe: ", self.arrayData[0].columns)
        try:
            if particle == None:
                return self.arrayData
            if particle == "proton":
                return self.protonArray
            if particle == "electron":
                return self.electronArray
            if particle == "muon":
                return self.muonArray
            if particle == "pion":
                return self.pionArray
            if particle == "deuterium":
                return self.deuteriumArray
        except:
            raise Exception("Wrong particle name, leave empty for all particles, or electron, muon, pion, proton, deuterium")
    
    def getDataFrameDetector(self, detectorID, particle = None):
        #print("Returning the data frame for detector %i: %s"%(detectorID, self.channelNames[detectorID]))
        try:
            if particle == None:
                return self.arrayData[detectorID]
            if particle == "proton":
                return self.protonArray[detectorID]
            if particle == "electron":
                return self.electronArray[detectorID]
            if particle == "muon":
                return self.muonArray[detectorID]
            if particle == "pion":
                return self.pionArray[detectorID]
            if particle == "deuterium":
                return self.deuteriumArray[detectorID]
        except:
            raise Exception("Wrong particle name, leave empty for all particles, or electron, muon, pion, proton, deuterium")
    
    
    def getColumnDataFrameDetector(self, branch_name, detectorID, particle = None):
        #print("Returning the column %s in the data frame for detector %i: %s"%(branch_name, detectorID, self.channelNames[detectorID]))
        try:
            if particle == None:
                return self.arrayData[detectorID][branch_name]
            if particle == "proton":
                return self.protonArray[detectorID][branch_name]
            if particle == "electron":
                return self.electronArray[detectorID][branch_name]
            if particle == "muon":
                return self.muonArray[detectorID][branch_name]
            if particle == "pion":
                return self.pionArray[detectorID][branch_name]
            if particle == "deuterium":
                return self.deuteriumArray[detectorID][branch_name]
        except:
            raise Exception("Wrong particle name, leave empty for all particles, or electron, muon, pion, proton, deuterium")
    
    def addBranchToDataFrameDetector(self, new_branch_name, detectorID, value, particle = None):
        print("Adding the branch %s to the data frame for detector %i: %s"%(new_branch_name,detectorID, self.channelNames[detectorID]))
        try:
            if particle == None:
                self.arrayData[detectorID][new_branch_name] = value
            if particle == "proton":
                self.protonArray[detectorID][new_branch_name] = value
            if particle == "electron":
                self.electronArray[detectorID][new_branch_name] = value
            if particle == "muon":
                self.muonArray[detectorID][new_branch_name] = value
            if particle == "pion":
                self.pionArray[detectorID][new_branch_name] = value
            if particle == "deuterium":
                self.deuteriumArray[detectorID][new_branch_name] = value
        except:
            raise Exception(f"Branch adding has failed, possibly because the particle name: {particle} was not correct")
        
    def getArraysParticleData(self, particleIndex):
        return self.getDataFrameAllDetectors(self.particleNamesList[particleIndex])
    
    def makeAllParticleSelection(self):
        
        for particleName in self.particleNamesList:
            print("Making selection for %s"%particleName)
            
            if particleName == 'electron':
                self.makeElectronSelection()

            elif particleName == 'proton':  
                self.makeProtonSelection()

            elif particleName == 'muon':
                self.makeMuonSelection()

            elif particleName == 'pion':
                self.makePionSelection()

            elif particleName == 'deuterium':
                self.makeDeuteriumSelection()
        
    def propagateMomentumError(self,particle, errorTOF_delta, errorLength_tau, error_p_lost):
        """Using the different sources of error propagates it directly to form the total error, error on the tof dominates"""
        delta = self.dictTOFMean[particle]
        tau = (self.distanceTOF1toTOF0 / c) * conv
        m = ms[particle]

        errorTOF_delta = max(errorTOF_delta, self.dictTOFStd[particle])

        print(delta, tau, m, delta**2 - tau**2, errorTOF_delta)

        part1_tof = (m * tau * delta)/(delta ** 2 - tau ** 2)**(3/2) * errorTOF_delta 
        part2_length = (m * delta * delta)/(delta**2 - tau ** 2)**(3/2) * errorLength_tau
        part3_plost = error_p_lost

        print("part1", part1_tof, "part2", part2_length, "part3", part3_plost)

        total = np.sqrt(part1_tof**2 + part2_length**2 + part3_plost**2)

        return total

    def measureMomentumUsingTOF(self, binWidth = 0.5):
        """For each particle type, if we have identified it, fit the TOF peak to extract the momentum, only do it with protons if the other ones haven't been identified yet"""
        fig, ax = plt.subplots(1, 1, figsize = (16, 9))
        for particle in self.particleNamesList:
            if self.getDataFrameAllDetectors(particle) == None:
                if particle == "proton":
                    self.makeProtonSelection()
                elif particle == "electron":
                    self.makeElectronSelection()
            
            if self.getDataFrameAllDetectors(particle) != None:
                #for low momentum set-up sometimes we do not have any sensible number of particle, when there is not enough e.g. deuterium or protons at low momentum 
                if len(self.getDataFrameDetector(0, particle)) > self.minNbEventsToFitTOF or not(self.isLowMomentum):
                    calc_mom, stat_err_mom, error_p_lost = self.calculateMomentumUsingTOF(particle, fig, ax, binWidth)

                    self.dictMomentumMean[particle] = calc_mom
                    self.dictMomentumStatError[particle] = stat_err_mom

                    
                    
                    
        ax.legend(fontsize = 18)
        ax.grid()
        particleName = "AllParticles"
        ax.set_yscale('log')
        ax.set_ylim([0.5, None])
        ax.set_xlabel("Time of Flight (ns)", fontsize=15)
        ax.set_ylabel("Occurences/%.2f ns"%binWidth, fontsize=15)
        ax.set_title("Particle: %s"%particleName, fontsize=25)
        ax.tick_params(axis='both', which='major', labelsize=15)
        fig.suptitle('WCTE Beamtest - Run %i, p = %i MeV/c'%(self.runNumber, self.runMomentum), fontsize=22, weight ='bold')
        fig.savefig("../%s/TOFHisto_%s_Run%i.png"%(self.saving_folder_path_png, particleName, self.runNumber))
        fig.savefig("../%s/TOFHisto_%s_Run%i.pdf"%(self.saving_folder_path_pdf, particleName, self.runNumber))
        
                
    def calculateTOF(self, TOF_array, binWidth = 0.5, output_error_std = False):
        
        nBins = int((np.ceil(TOF_array.max() - np.floor(TOF_array.min())))/binWidth)
        
        counts, bins = np.histogram(TOF_array, nBins)

        params, covariance = fitGaussian(counts, bins)

        amplitude, mean, std = params[0], params[1], abs(params[2])

        if not(output_error_std):
            return amplitude, mean, std
        else:
            return amplitude, mean, std, covariance[2][2]
    
    def calculateMomentumUsingTOF(self, particleName, fig = None, ax = None, binWidth = 0.5):
        """here calculate the momentum by fitting the histogram of the particle TOF momentum, note we can use detector 0 because all have it now and it is a straight copy"""

        if "matchedHit0_TOF" not in (self.getBranchList(0, particleName)): 
            raise Exception("The matchedHit0_TOF branch is not available, make sure you are using the coincidence in your pre-processing of the data so that the TOF measurement is accurate ")
            
        TOF_array = self.getColumnDataFrameDetector("matchedHit0_TOF", 0, particleName) 

        print("Particle", particleName, )
        nBins = int((np.ceil(TOF_array.max() - np.floor(TOF_array.min())))/binWidth)

        fig_particle, ax_particle = plt.subplots(1, 1, figsize = (16, 9))
        
        counts, bins, _ = ax_particle.hist(TOF_array, nBins, histtype = 'step', label = '# events passing the selection: %i\n(%.1f percent of all events)'%(len(TOF_array), (len(TOF_array)/self.totalNumberOfEvents) * 100))

        if ax != None:
            ax.hist(TOF_array, nBins, histtype = 'step', label = '# events passing the %s selection: %i\n(%.1f percent of all events)'%(particleName, len(TOF_array), (len(TOF_array)/self.totalNumberOfEvents) * 100))


        params, covariance = fitGaussian(counts, bins)

        amplitude, mean, std = params[0], params[1], abs(params[2])

        #need to correct for cable length offsets, especially important for TG set-up
        if particleName != "electron":
            mean = self.correctForTOFwrtElectron(mean)

        self.dictTOFMean[particleName] = mean
        self.dictTOFfitErrOnMean[particleName] = covariance[1][1]
        self.dictTOFStd[particleName] = std
        self.dictTOFfitErrOnStd[particleName] = covariance[2][2]

        p_pred = self.TofToMomentum(mean, particleName)

        
        p_lost, p_lost_error  = self.correctParticleTSdEdx(particleName)
        
        p_pred = p_pred + p_lost
        

        n_events_inPeak = integrate.quad(gaussian, 0, 50, args = (amplitude, mean, std))

        n_events_inPeak = n_events_inPeak[0]/binWidth

        self.dictTOFfittedNparticles[particleName] = n_events_inPeak
        #error on the p_error is (proportional to) sigma_TOF/sqrt(n) where n is the number of events in the peak 
        p_error_stat = (p_pred * std/mean)  * (p_pred /(ms[particleName]) * (mean/((self.distanceTOF1toTOF0 * conv)/c))) ** 2 / np.sqrt(n_events_inPeak) 
        #/ np.sqrt(n_events_inPeak) 

        if self.isLowMomentum:
            #only do the complicated error propagation for LM run when we want accurate error on the momentum estimate
            errorTOF_delta = self.estimateSystematicErrorTOF(particleName)
        else:
            #it is enough to look at the std in the TG 
            errorTOF_delta = std
        
        errorLength_tau = self.fractionalErrorDistanceTOF1toTOF0  * conv * self.distanceTOF1toTOF0 / c

        p_error_tot = self.propagateMomentumError(particleName, errorTOF_delta, errorLength_tau, p_lost_error) / np.sqrt(n_events_inPeak) 

        print("Total error:", p_error_tot, " error on mean:", p_error_stat)

        
        self.dictMomentumTotalError[particleName] = p_error_tot

        print(f"Predicted momentum for {particleName} is {p_pred} MeV/c, true is {self.runMomentum} MeV/c.")

        x = np.linspace(bins[0], bins[-1], 1000)

        if particleName != "electron":
            ax_particle.plot(x, gaussian(x, *params), '--', label = '# %s in fitted peak %.1f \n (%.1f percent of all events)\nTOF = %.2f +/- %.2f ns\nMomentum: %.1f +/- %.1f(total) MeV/c'%(particleName, n_events_inPeak, (n_events_inPeak/self.totalNumberOfEvents) * 100, mean, std, p_pred, p_error_tot))
        
        else:
            ax_particle.plot(x, gaussian(x, *params), '--', label = '# %s in fitted peak %.1f \n (%.1f percent of all events)\nTOF = %.2f +/- %.2f ns\nMomentum lost to 2 TS: %.1f +/- %.1f(total) MeV/c'%(particleName, n_events_inPeak, (n_events_inPeak/self.totalNumberOfEvents) * 100, mean, std, p_lost * 2, p_lost_error * 2))


        if ax != None:
            if particleName != 'electron':
                ax.plot(x, gaussian(x, *params), '--', label = 'TOF = %.2f +/- %.2f ns\nMomentum: %.1f +/- %.1f(total) MeV/c'%(mean, std, p_pred, p_error_tot))
            else:
               ax.plot(x, gaussian(x, *params), '--', label = 'TOF = %.2f +/- %.2f ns'%(mean, std)) 

        ax_particle.legend(fontsize = 18)
        ax_particle.grid()
        ax_particle.set_xlabel("Time of Flight (ns)", fontsize=15)
        ax_particle.set_ylabel("Occurences/%.2f ns"%binWidth, fontsize=15)
        ax_particle.set_title("Particle: %s"%particleName, fontsize=25)
        ax_particle.tick_params(axis='both', which='major', labelsize=15)
        fig_particle.suptitle('WCTE Beamtest - Run %i, p = %i MeV/c'%(self.runNumber, self.runMomentum), fontsize=22, weight ='bold')
        fig_particle.savefig("../%s/TOFHisto_dEdxCorrected_%s_Run%i.png"%(self.saving_folder_path_png, particleName, self.runNumber))
        fig_particle.savefig("../%s/TOFHisto_dEdxCorrected_%s_Run%i.pdf"%(self.saving_folder_path_pdf, particleName, self.runNumber))

        return p_pred, p_error_tot, p_lost_error
    

    def plotBranchHistForAllParticles(self, detectorID, branch_name, binwidth = 1, logScale = False, lim = None, values = False, normalise = False):
        """Plot for all the particles the branch in the given detector """
        fig, ax = plt.subplots(1, 1, figsize = (16, 9)) 
        ax.grid()

        if lim !=None:
            ax.set_xlim(lim)
        
        for particle in self.particleNamesList:
            if branch_name in self.getBranchList(detectorID, particle):

                if values:
                    data = self.getColumnDataFrameDetector(branch_name, detectorID, particle)
                    
                    self.plot1DHist(self.getColumnDataFrameDetector(branch_name, detectorID, particle), binwidth, "%s %s"%(self.channelNames[detectorID], branch_name), "Number of occurences", "%s mean: %.2f, std: %.3f"%(particle, data.mean(), data.std()), "%s_%s_allParticles"%(self.channelNames[detectorID], branch_name), ax, fig, logScale, lim, False, normalise)
                else:
                    data = self.getColumnDataFrameDetector(branch_name, detectorID, particle)
                    self.plot1DHist(self.getColumnDataFrameDetector(branch_name, detectorID, particle), binwidth, "%s %s"%(self.channelNames[detectorID], branch_name), "Number of occurences", "%s"%(particle), "%s_%s_allParticles"%(self.channelNames[detectorID], branch_name), ax, fig, logScale, lim, False, normalise)
                
            else:
                break
        if logScale:
            if branch_name in self.getBranchList(detectorID):
                self.plot1DHist(self.getColumnDataFrameDetector(branch_name, detectorID), binwidth,"%s %s"%(self.channelNames[detectorID], branch_name), "Number of occurences", "All particles", "%s_%s_allParticles"%(self.channelNames[detectorID], branch_name), ax, fig, True, lim, False, normalise)

        else:
            if branch_name in self.getBranchList(detectorID):
                self.plot1DHist(self.getColumnDataFrameDetector(branch_name, detectorID), binwidth, "%s %s"%(self.channelNames[detectorID], branch_name), "Number of occurence", "All particles", "%s_%s_allParticles"%(self.channelNames[detectorID], branch_name), ax, fig, logScale, lim, False, normalise)
    
        if normalise:
            plt.savefig("../%s/Hist1D_allParticles_%s_%s_normalised_Run%i.png"%(self.saving_folder_path_png, self.channelNames[detectorID], branch_name, self.runNumber))
            plt.savefig("../%s/Hist1D_allParticles_%s_%s_normalised_Run%i.pdf"%(self.saving_folder_path_pdf, self.channelNames[detectorID], branch_name, self.runNumber))

        else:
            plt.savefig("../%s/Hist1D_allParticles_%s_%s_Run%i.png"%(self.saving_folder_path_png, self.channelNames[detectorID], branch_name, self.runNumber))
            plt.savefig("../%s/Hist1D_allParticles_%s_%s_Run%i.pdf"%(self.saving_folder_path_pdf, self.channelNames[detectorID], branch_name, self.runNumber))
        
        

    def measureElTOFresolutionFunctionOfTScharge(self, nBins = None):
        """Plot the standard deviation of the fitted TOF distribution for the electron, pion, muon, protons, deuterium sample after having split it accounding to bins (of equal number of events, int to only give electron number of bins, range of int to give for each particle) in the Trigger Scintillator window2 summed charge (given as waveformIntPE)"""

        if not(self.isLowMomentum):
            #only do for the LM setup
            return 0

        particles =  ["electron", "proton"] #self.particleNamesList

        if nBins == None:
            list_bins = [10, 6, 3, 4, 5]
        else:
            list_bins = [10, 6, 3, 4, 5]
        array_mean, array_std, array_meanX, array_stdX, array_stdErr = [], [], [], [], []

        fig, ax1 = plt.subplots(1, 1, figsize = (16, 9))
        fig3, ax3 = plt.subplots(1, 1, figsize = (16, 9))

        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2','#7f7f7f', '#bcbd22', '#17becf']

        for i, particle in enumerate(particles):
            electronSample = self.getColumnDataFrameDetector("sumTSwindow2", 0, particle)
            fig2, ax2 = plt.subplots(1, 1, figsize = (16, 9))
            ESsorted = sorted(electronSample)
            bins = list_bins[i]
            nbEventsPerBin = int(len(ESsorted)/bins)
            array_meanParticle, array_stdParticle, array_meanXParticle, array_stdXParticle, array_stdErrParticle = [], [], [], [], []
        
            for bin in range(bins):
                binMinIndex = bin * nbEventsPerBin
                binMaxIndex = min((bin+1) * nbEventsPerBin, len(ESsorted))
                valuesInBin = np.array(ESsorted[binMinIndex:binMaxIndex])
                binEdgeMin = min(valuesInBin)
                binEdgeMax = max(valuesInBin)
                
                meanBinValue = valuesInBin.mean()
                stdBin = valuesInBin.std()
                
                ax2.axvspan(binEdgeMin,binEdgeMax, alpha = 0.2, color = colors[bin], label = 'Bin %i, Mean: %.1f PE, std: %.1f PE'%(bin, meanBinValue, stdBin))

                medianBinValue = valuesInBin[int(len(valuesInBin)/2)]

                #print("Bin %i ranges between %.2f (ID: %i) and %.2f(ID: %i), holds %i values with a mean of %.2f and an std of %.2f with a median of %.2f"%(bin, binEdgeMin, binMinIndex, binEdgeMax,binMaxIndex, len(valuesInBin), meanBinValue, stdBin, medianBinValue))

                isAboveLowerBinBound = (electronSample>=binEdgeMin)
                isBelowUpperBinBound = (electronSample<=binEdgeMax)
                isInBin = isAboveLowerBinBound & isBelowUpperBinBound
                e_sampleInBin = self.makeNewDataFrameFromSelection(self.getDataFrameAllDetectors("%s"%particle), isInBin)

                try:
                    _, TOF_mean, TOF_std, TOF_std_err = self.calculateTOF(e_sampleInBin[0]["matchedHit0_TOF"], 0.5, True)
                except:
                    #if the fit failed, still continue
                    _, TOF_mean, TOF_std, TOF_std_err = np.nan, np.nan, np.nan, np.nan

                #print("Mean time of flight in bin: %.2f std: %.3f"%(TOF_mean, TOF_std))

                array_mean.append(TOF_mean)
                array_std.append(TOF_std)
                array_stdErr.append(TOF_std_err)
                array_meanX.append(meanBinValue)
                array_stdX.append(stdBin)

                if not (particle=="deuterium" and self.runMomentum<700):
                    array_meanParticle.append(TOF_mean)
                    array_stdParticle.append(TOF_std)
                    array_stdErrParticle.append(TOF_std_err)
                    array_meanXParticle.append(meanBinValue)
                    array_stdXParticle.append(stdBin)

            ax2.grid()
            self.plot1DHist(electronSample, 10, 'sumTSwindow2', 'Number of %s'%particle, None, "Particle: %s"%particle, ax2, fig2, False, None)

            if not (particle=="deuterium" and self.runMomentum<700):
                ax1.errorbar(array_meanXParticle, array_stdParticle, xerr = array_stdXParticle, yerr = array_stdErrParticle, fmt = 'x', label = '%s'%particle)

                ax3.errorbar(array_meanXParticle, array_meanParticle, xerr = array_stdXParticle, yerr = array_stdParticle, fmt = 'x', label = '%s'%particle)
            


        plot_saving = 'GaussianFitTOFstd_TSbins_allParticles'
        plot_saving3 = 'TimeofFlight_TSbins_allParticles'
        # ax1.errorbar(array_meanX, array_std, xerr = array_stdX, yerr = TOF_std_err, fmt = 'x')
        
        params, covariance = curve_fit(oneOverSqrtN, array_meanX, array_std, p0 = [array_mean[0], 0.3])

        print("Run %i covariance matrix for a fit A/sqrt(n) + b:\n"%self.runNumber, covariance)

        x = np.linspace(array_meanX[0], array_meanX[-1], 100)
        ax1.plot(np.array(x), np.array(oneOverSqrtN(x, params[0], params[1])), 'r--', label = r'Fit: $\sqrt{\frac{(%.1f \pm %.1f)}{x} + (%.3f \pm %.3f)}$ ns'%(params[0], np.sqrt(covariance[0][0]),params[1],  np.sqrt(covariance[1][1])) )
        ax1.legend(fontsize = 18)

        ax1.set_xlabel("Mean sumTSwindow2  in bin +/- std (PE)", fontsize = 18)
        ax1.set_ylabel("Std of particle time of flight (ns)", fontsize = 18)
        ax1.grid()

        fig.suptitle('WCTE Beamtest - Run %i, p = %i MeV/c n = %s'%(self.runNumber, self.runMomentum, self.runRefractiveIndex), fontsize=18, weight ='bold')
        ax1.tick_params(axis='both', which='major', labelsize=15)


        ax3.legend(fontsize = 18)

        ax3.set_xlabel("Mean sumTSwindow2  in bin +/- std (PE)", fontsize = 18)
        ax3.set_ylabel("Mean of particle time of flight (ns)", fontsize = 18)
        ax3.grid()
        
        fig3.suptitle('WCTE Beamtest - Run %i, p = %i MeV/c n = %s'%(self.runNumber, self.runMomentum, self.runRefractiveIndex), fontsize=18, weight ='bold')
        ax3.tick_params(axis='both', which='major', labelsize=15)


        fig.savefig("../%s/%s_fitted_Run%i.pdf"%(self.saving_folder_path_pdf, plot_saving, self.runNumber))
        fig.savefig("../%s/%s_fitted_Run%i.png"%(self.saving_folder_path_png, plot_saving, self.runNumber))

        fig3.savefig("../%s/%s_fitted_Run%i.pdf"%(self.saving_folder_path_pdf, plot_saving3, self.runNumber))
        fig3.savefig("../%s/%s_fitted_Run%i.png"%(self.saving_folder_path_png, plot_saving3, self.runNumber))

        #now we use values obtained for run 393, not updateing tehm anymore
        # self.TOF_fit_covariance = covariance
        # self.TOF_fit_mean_A = params[0]
        # self.TOF_fit_mean_B = params[1]


    def estimateSystematicErrorTOF(self, particle = "proton"):
        """This is a function to estimate the systematic error on the Time of flight measured, so we can accurately propagate it to the momentum estimate. The idea is to obtain the typical error fo each run based on resonnable values of A and B obtained from the fit above."""

        #Step 1: throw n values of A and B (correlated) from the fitted refenrence correlation matrix (for now we use the one fitted for this run but we will settle on a single one soon)

        n_throws_AB = 1000
        # self.measureElTOFresolutionFunctionOfTScharge([6, 6, 5, 5, 5, 4])

        mean_A_B = [self.TOF_fit_mean_A, self.TOF_fit_mean_B]

        print(self.TOF_fit_covariance)
        A_B_samples = np.random.multivariate_normal(mean_A_B, self.TOF_fit_covariance, n_throws_AB)

        A_samples = A_B_samples[:, 0]
        B_samples = A_B_samples[:, 1]

        fig = plt.figure(figsize=(12, 5))

        plt.subplot(1, 2, 1)
        plt.hist(A_samples, bins=50, alpha=0.75, color='blue', label='A samples')
        plt.axvline(self.TOF_fit_mean_A, color='red', linestyle='dashed', linewidth=2, label=r'A drawn from:'"\n"r'%.2f $\pm$ %.3f ns$^2$ PE'%(self.TOF_fit_mean_A, np.sqrt(self.TOF_fit_covariance[0][0])))
        plt.title('Distribution of A samples - %i throws'%(n_throws_AB))
        plt.legend()
        plt.xlabel(r"A (ns$^2$ PE)")

        plt.subplot(1, 2, 2)
        plt.hist(B_samples, bins=50, alpha=0.75, color='green', label='B samples')
        plt.axvline(self.TOF_fit_mean_B, color='red', linestyle='dashed', linewidth=2, label=r'B drawn from:'"\n"r'%.2f $\pm$ %.3f ns$^2$'%(self.TOF_fit_mean_B, np.sqrt(self.TOF_fit_covariance[1][1])))
        plt.title('Distribution of B samples - %i throws'%(n_throws_AB))
        plt.legend()
        plt.xlabel(r"B (ns$^2$)")

        fig.savefig("../%s/DistributionTOFfitAB_Run%i.pdf"%(self.saving_folder_path_pdf, self.runNumber))
        fig.savefig("../%s/DistributionTOFfitAB_Run%i.png"%(self.saving_folder_path_png, self.runNumber))

        #step 2 for each A, B value make the distribution of standard deviations for each data point

        TOTALerrorOnTOF = 0


        A_samples = A_samples[np.newaxis, :]  # Shape (num_samples, 1)
        B_samples = B_samples[np.newaxis, :]  # Shape (num_samples, 1)
        
        #2.1: for all particles get the values
        if not (particle=="deuterium" and self.runMomentum<700):
            electron_sumTSwindow2 = self.getColumnDataFrameDetector("sumTSwindow2",0, particle)
            nevents = len(electron_sumTSwindow2)
            TOF_mean = np.tile(self.getColumnDataFrameDetector("matchedHit0_TOF",0, particle).mean(), (nevents,n_throws_AB))

            #need to make the same dimensions
            # tiled_electron_sumTSwindow2 = np.tile(electron_sumTSwindow2, (1, n_throws_AB))
            # tiled_A_samples = np.tile(A_samples, (1, nevents)).T #need to transpose
            # tiled_B_samples = np.tile(B_samples, (1, nevents)).T #need to transpose


            # electron_throws_std = np.sqrt(tiled_A_samples/tiled_electron_sumTSwindow2 + tiled_B_samples)

            # Reshape the arrays for broadcasting
            
            electron_sumTSwindow2 = electron_sumTSwindow2[:, np.newaxis]  # Shape (1, num_events)

            # Calculate the time of flight 2D array
            electron_throws_std = np.sqrt(A_samples / electron_sumTSwindow2 + B_samples)
            print(electron_throws_std)

            # Draw random values for the time of flight for each event
            random_tof = np.random.normal(TOF_mean, electron_throws_std)      

            print(random_tof, len(random_tof), electron_throws_std)

            fig = plt.figure(figsize=(12, 10))
            for i in range(4):  # Visualize for the first 3 events
                plt.subplot(2, 2, i+1)
                print(A_samples[0][i], B_samples[0][i])
                
                counts, bins, _ = plt.hist(random_tof[:, i], bins=50, alpha=0.75, color='blue', label=r"TOF throw %i""\n"r"A = %.2f PE ns$^2$""\n"r"B = %.2e ns$^2$"%(i+1, A_samples[0][i], B_samples[0][i]))

                #print(bins, counts, len(bins), len(counts))

                params, covariance = curve_fit(gaussian, bins[:len(counts)] + (bins[1]-bins[0])/2, counts, p0 = [nevents, TOF_mean[i][0], electron_throws_std[i][0]])

                print("results: ", params)

                x_array = np.linspace(bins[0] + (bins[1]-bins[0])/2, bins[len(counts)] + (bins[1]-bins[0])/2, 100)

                plt.axvline(TOF_mean[i][0], color='red', linestyle='dashed', linewidth=2, label='Measured TOF %s: %.3f ns'%(particle, TOF_mean[i][0]))

                plt.axvline(params[1], color='black', linestyle='dashed', linewidth=1)

                plt.plot(x_array, gaussian(x_array, *params), color='black', linestyle='dashed', linewidth=1, label=r"Fit to the throw""\n"r"Mean = %.3f $\pm$ %.1e ns""\n"r"std = %.3e $\pm$ %.2e ns"%(params[1], np.sqrt(covariance[1][1]), params[2], np.sqrt(covariance[2][2])))

                plt.title(f'Distribution of TOF for throw {i+1}')
                plt.xlabel('Time of flight (ns)')
                plt.ylabel('Number of events')
                plt.legend()

                fig.suptitle('WCTE Beamtest - Run %i, p = %i MeV/c n = %s \n%s'%(self.runNumber, self.runMomentum, self.runRefractiveIndex, particle), fontsize=18, weight ='bold')
                fig.savefig("../%s/Example_%s_TOFdrawnFromAB_Run%i.pdf"%(self.saving_folder_path_pdf, particle, self.runNumber))
                fig.savefig("../%s/Example_%s_TOFdrawnFromAB_Run%i.png"%(self.saving_folder_path_png, particle, self.runNumber))
            plt.tight_layout()


            array_std = []
            array_mean = []
            for i in range(n_throws_AB):
                # print("computing throw", i)
                #step 3 fit everny distribution to get the sigmas out
                counts, bins = np.histogram(random_tof[:, i], bins=50)

                bins = bins[:len(counts)] +  (bins[1]-bins[0])/2

                params, covariance = curve_fit(gaussian, bins, counts, p0 = [nevents, TOF_mean[0][0], electron_throws_std[0][0]])

                array_std.append(params[2])
                array_mean.append(params[1])


            fig = plt.figure(figsize=(16, 9))
            
            plt.subplot(1, 2, 2)
            counts, bins, _ = plt.hist(array_std, bins=50, alpha=0.75, color='blue', label=r"Total: %i throws"%(n_throws_AB))

            #print(bins, counts, len(bins), len(counts))
            params, covariance = curve_fit(gaussian, bins[:len(counts)] + (bins[1]-bins[0])/2, counts, p0 = [n_throws_AB, electron_throws_std[0][0], 0.01])

            #teh error is the quadric sum of the mean std and of the std of the stds
            TOTALerrorOnTOF = np.sqrt(params[1]**2 + params[2]**2)

            x_array = np.linspace(bins[0] + (bins[1]-bins[0])/2, bins[len(counts)-1] + (bins[1]-bins[0])/2, 100)

            plt.plot(x_array, gaussian(x_array, *params), color='black', 
            linestyle='dashed', linewidth=1, label=r"Fit to the distribution of throws""\n"r"Mean = %.3f $\pm$ %.1e ns""\n"r"std = %.3e $\pm$ %.2e ns"%(params[1], np.sqrt(covariance[1][1]), params[2], np.sqrt(covariance[2][2])))

            fig.suptitle('WCTE Beamtest - Run %i, p = %i MeV/c n = %s \n%s'%(self.runNumber, self.runMomentum, self.runRefractiveIndex, particle), fontsize=18, weight ='bold')


            plt.title(f'Distribution of std of TOF for all throw \n %s'%particle)
            plt.xlabel('Std of time of flight (ns)', fontsize = 17)
            plt.ylabel('Number of throws', fontsize = 17)
            plt.legend()

            plt.subplot(1, 2, 1)
            counts, bins, _ = plt.hist(array_mean, bins=50, alpha=0.75, color='blue', label=r"Total: %i throws"%(n_throws_AB))

            plt.axvline(TOF_mean[0][i], color='red', linestyle='dashed', linewidth=2, label='Measured TOF %s: %.3f ns'%(particle, TOF_mean[0][i]))

            #print(bins, counts, len(bins), len(counts))
            params, covariance = curve_fit(gaussian, bins[:len(counts)] + (bins[1]-bins[0])/2, counts, p0 = [n_throws_AB, TOF_mean[0][i], 0.01])

            x_array = np.linspace(bins[0] + (bins[1]-bins[0])/2, bins[len(counts)] + (bins[1]-bins[0])/2, 100)

            plt.plot(x_array, gaussian(x_array, *params), color='black', linestyle='dashed', linewidth=1, label=r"Fit to the distribution of throws""\n"r"Mean = %.3f $\pm$ %.1e ns""\n"r"std = %.3e $\pm$ %.2e ns"%(params[1], np.sqrt(covariance[1][1]), params[2], np.sqrt(covariance[2][2])))

            plt.title(f'Distribution of mean TOF for all throw \n %s'%particle)
            plt.xlabel('Mean time of flight (ns)', fontsize = 17)
            plt.ylabel('Number of throws', fontsize = 17)
            plt.legend()
            fig.suptitle('WCTE Beamtest - Run %i, p = %i MeV/c n = %s \n%s'%(self.runNumber, self.runMomentum, self.runRefractiveIndex, particle), fontsize=18, weight ='bold')
            fig.savefig("../%s/TOTAL_%s_TOFdrawnFromAB_Run%i.pdf"%(self.saving_folder_path_pdf, particle, self.runNumber))
            fig.savefig("../%s/TOTAL_%s_TOFdrawnFromAB_Run%i.png"%(self.saving_folder_path_png, particle, self.runNumber))
            plt.tight_layout()

        

        return TOTALerrorOnTOF 
    
    def plotAll2DSelections(self, plotSelections = True):
        """It is nice to see the 2D plots but they take a while to load, speed up process that way"""
        if plotSelections == True:
            self.plotSelectionACT1sumDownstreamACT(100)
            self.plotSelectionWindow2ACT1sumDownstreamACT(60)
            self.plotSelectionTOFLG()
        else:
            print("Not plotting the selection 2D plots to save time")

    def calculateMuPiAndElPurityEfficiency(self, is_selected_mupi= None, is_selected_electron = None, is_genuine_mupi = None, is_genuine_electron = None):

        
        selected_genuine_mupi = is_genuine_mupi & is_selected_mupi
        selected_genuine_electron = is_genuine_electron & is_selected_electron
        if sum(is_selected_mupi) < 1:
            mupi_purity = 0
            mupi_efficiency = 0
        else:
            mupi_purity = sum(selected_genuine_mupi)/sum(is_selected_mupi)
            mupi_efficiency = sum(selected_genuine_mupi)/sum(is_genuine_mupi)
            
        if sum(is_selected_electron) < 1:
            electron_efficiency = 0
            electron_purity = 0
        else:
            electron_purity = sum(selected_genuine_electron)/sum(is_selected_electron)
            electron_efficiency = sum(selected_genuine_electron)/sum(is_genuine_electron)
        
        return mupi_purity, mupi_efficiency, electron_purity, electron_efficiency, sum(is_selected_mupi), sum(is_selected_electron)

    def scanOverACTLinearAB(self, start_A_value, start_B_value, start_H_value, start_L_value, coarse_bounds, nTests, metric = "purity2_times_efficiency"):
        
        slowEvents= self.makeNewDataFrameFromSelection(self.arrayData, self.arrayData[0]["matchedHit0_TOF"] < self.protonsTOFCut)
    
        #define genuine electron and mu/pi events
        LGid = self.channelNames.index("PbGlass")

        #we are deciding the position of the lead glass cut based on the fitted gaussians for windowIntPE distribution of electron and muon populations

        eMu_LG_params = self.fitMuonsAndElectronLGPeaks()
        e_params = eMu_LG_params[0]
        mu_params = eMu_LG_params[1]
        
        five_sigma_e = e_params[1] - 5 * e_params[2]
        five_sigma_mu = mu_params[1] + 5 * mu_params[2]

        three_sigma_e = e_params[1] - 3 * e_params[2]
        three_sigma_mu = mu_params[1] + 3 * mu_params[2]

        four_sigma_e = e_params[1] - 4 * e_params[2]
        four_sigma_mu = mu_params[1] + 4 * mu_params[2]

        if five_sigma_mu < five_sigma_e:
            electronLGcut =  five_sigma_e
            mupiLGcut = five_sigma_mu
        
        elif four_sigma_mu < four_sigma_e:
            electronLGcut =  four_sigma_e
            mupiLGcut = four_sigma_mu
        
        elif three_sigma_mu < three_sigma_e:
            electronLGcut =  three_sigma_e
            mupiLGcut = three_sigma_mu

        else:
            weighted_mean_distance = ((mu_params[2] + mu_params[1]) * e_params[0] +  ( - e_params[2] + e_params[1]) * mu_params[0]) / (e_params[0] + mu_params[0])
            electronLGcut =  weighted_mean_distance # self.weirdElectronLGcut
            mupiLGcut = weighted_mean_distance # self.weirdElectronLGcut 

        is_genuine_electron = slowEvents[LGid]["matchedHit0_WindowIntPE"] > electronLGcut

        print(sum(is_genuine_electron))
        is_genuine_mupi = slowEvents[LGid]["matchedHit0_WindowIntPE"] < mupiLGcut
        #list storing values:
        A_values=[]
        B_values=[]
        nMuPi_values=[]
        nE_values=[]
        mupi_pur_values=[]
        mupi_eff_values=[]
        electron_pur_values=[]
        electron_eff_values=[]
        hori_values = []
        lower_values = []

        #select values of ACTLinearA and ACTLinearB within +/-50% of default values, first do a coarse search, need to make sure that the order is correct
        if start_A_value * (1-coarse_bounds) < start_A_value * (1+coarse_bounds):
            coarse_values_ACTLinearA = np.linspace(start_A_value * (1-coarse_bounds), start_A_value * (1+coarse_bounds), nTests)
        else:
            coarse_values_ACTLinearA = np.linspace(start_A_value * (1+coarse_bounds), start_A_value * (1-coarse_bounds), nTests)

        if start_B_value * (1-coarse_bounds) < start_B_value * (1+coarse_bounds):
            coarse_values_ACTLinearB = np.linspace(start_B_value * (1-coarse_bounds), start_B_value * (1+coarse_bounds), nTests)
        else:
            coarse_values_ACTLinearB = np.linspace(start_B_value * (1+coarse_bounds), start_B_value * (1-coarse_bounds), nTests)

        if start_H_value * (1-coarse_bounds * 2) < start_H_value * (1+coarse_bounds):
            coarse_values_H = np.linspace(start_H_value * (1-coarse_bounds * 2), start_H_value * (1+coarse_bounds), nTests)
        else:
            coarse_values_H = np.linspace(start_H_value * (1+coarse_bounds), start_H_value * (1-coarse_bounds * 2), nTests)

        if start_L_value * (1-coarse_bounds * 3) < start_L_value * (1+coarse_bounds * 3):
            coarse_values_L = np.linspace(start_L_value * (1-coarse_bounds * 5), start_L_value * (1+coarse_bounds * 5), nTests)
        else:
            coarse_values_L = np.linspace(start_L_value * (1+coarse_bounds * 5), start_L_value * (1-coarse_bounds * 5), nTests)




        print(coarse_values_ACTLinearA, coarse_values_ACTLinearB)

        
    

        #for granularity in ["coarse", "fine"]:
        for coarse_A in coarse_values_ACTLinearA:
            for coarse_B in coarse_values_ACTLinearB:
                for coarse_H in coarse_values_H:  
                        
                        is_above_diag = slowEvents[LGid]["sumDownstreamACTs"] > (slowEvents[LGid]["sumACT1"] * coarse_A + coarse_B) 
                        
                        is_left =  slowEvents[LGid]["sumACT1"] < (coarse_H-coarse_B)/(coarse_A) 

                        is_above_hori = slowEvents[LGid]["sumDownstreamACTs"] > coarse_H

                        is_right =  slowEvents[LGid]["sumACT1"] > (coarse_H-coarse_B)/(coarse_A) 

                        is_selected_left = is_above_diag & is_left
                        is_selected_right = is_above_hori & is_right

                        is_selected_electron = is_selected_left | is_selected_right 

                        
                        is_below_diag = slowEvents[LGid]["sumDownstreamACTs"] < (slowEvents[LGid]["sumACT1"] * coarse_A + coarse_B)
                        is_below_hori = slowEvents[LGid]["sumDownstreamACTs"] < coarse_H
                        isAboveMin = slowEvents[LGid]["sumDownstreamACTs"] > start_L_value

                        is_selected_mupi = is_below_diag | is_below_hori
                        is_selected_mupi = is_selected_mupi & isAboveMin

                        mupi_pur, mupi_eff, electron_pur, electron_eff, nMuPi, nE = self.calculateMuPiAndElPurityEfficiency(is_selected_mupi, is_selected_electron, is_genuine_mupi, is_genuine_electron)

                        # print(r"ACTLinearA = %.3f, ACTLinearB = %.3f: "%(coarse_A, coarse_B),
                        #       "\n"r"$\mu\pi$ purity =  %.2f percent"%(mupi_pur *100),
                        #       "\n"r"$\mu\pi$ efficiency =  %.2f percent"%(mupi_eff*100),
                        #       "\n"r"electron purity =  %.2f percent"%(electron_pur*100),
                        #       "\n"r"electron efficiency =  %.2f percent"%(electron_eff*100),
                        #       "\n\n")
                        
                        A_values.append(coarse_A)
                        B_values.append(coarse_B)
                        hori_values.append(coarse_H)
                        lower_values.append(start_L_value)
                        nMuPi_values.append(nMuPi)
                        nE_values.append(nE)
                        mupi_pur_values.append(mupi_pur*100)
                        mupi_eff_values.append(mupi_eff*100)
                        electron_pur_values.append(electron_pur*100)
                        electron_eff_values.append(electron_eff*100)

            

        print("\n---------------------------------------------\n",
              "Run %i p = %i MeV/c: The maximal (muon or pion) purity achieved \nin the (%i, %i) points scan within \n the %.0f percent of the A, B values (%.2f, %.2f) is for: " %(self.runNumber, self.runMomentum, nTests, nTests, coarse_bounds * 100, start_A_value, start_B_value))
        bestI = mupi_pur_values.index(max(mupi_pur_values)) 
        print(r"ACTLinearA = %.3f, ACTLinearB = %.3f: "%(A_values[bestI], B_values[bestI]),
                    "\n"r"%i $\mu\pi$ and %i e"%(nMuPi_values[bestI], nE_values[bestI]),
                      "\n"r"$\mu\pi$ purity =  %.3f percent"%(mupi_pur_values[bestI]),
                      "\n"r"$\mu\pi$ efficiency =  %.3f percent"%(mupi_eff_values[bestI]),
                      "\n"r"electron purity =  %.3f percent"%(electron_pur_values[bestI]),
                      "\n"r"electron efficiency =  %.3f percent"%(electron_eff_values[bestI]),
                      "\n\n")
        
        print("\n---------------------------------------------\n",
              "Run %i p = %i MeV/c: The maximal (muon or pion) purity * efficiency achieved \nin the (%i, %i) points scan within \n the %.0f percent of the A, B values (%.2f, %.2f) is for: " %(self.runNumber, self.runMomentum, nTests, nTests, coarse_bounds * 100, start_A_value, start_B_value))
        quality_metric = np.array(mupi_pur_values) * np.array(mupi_eff_values)
        bestIpe = list(quality_metric).index(max(quality_metric)) 
        print(r"ACTLinearA = %.3f, ACTLinearB = %.3f: "%(A_values[bestIpe], B_values[bestIpe]),
                    "\n"r"%i $\mu\pi$ and %i e"%(nMuPi_values[bestIpe], nE_values[bestIpe]),
                      "\n"r"$\mu\pi$ purity =  %.3f percent"%(mupi_pur_values[bestIpe]),
                      "\n"r"$\mu\pi$ efficiency =  %.3f percent"%(mupi_eff_values[bestIpe]),
                      "\n"r"electron purity =  %.3f percent"%(electron_pur_values[bestIpe]),
                      "\n"r"electron efficiency =  %.3f percent"%(electron_eff_values[bestIpe]),
                      "\n\n")
        
        print("\n---------------------------------------------\n",
              "Run %i p = %i MeV/c: The maximal (muon or pion) purity ^ 2 * efficiency achieved \nin the (%i, %i) points scan within \n the %.0f percent of the A, B values (%.2f, %.2f) is for: " %(self.runNumber, self.runMomentum, nTests, nTests, coarse_bounds * 100, start_A_value, start_B_value))
        quality_metric = np.array(mupi_pur_values) * np.array(mupi_pur_values) * np.array(mupi_eff_values)
        bestIp2e = list(quality_metric).index(max(quality_metric))  
        print(r"ACTLinearA = %.3f, ACTLinearB = %.3f: "%(A_values[bestIp2e], B_values[bestIp2e]),
                    "\n"r"%i $\mu\pi$ and %i e"%(nMuPi_values[bestIp2e], nE_values[bestIp2e]),
                      "\n"r"$\mu\pi$ purity =  %.3f percent"%(mupi_pur_values[bestIp2e]),
                      "\n"r"$\mu\pi$ efficiency =  %.3f percent"%(mupi_eff_values[bestIp2e]),
                      "\n"r"electron purity =  %.3f percent"%(electron_pur_values[bestIp2e]),
                      "\n"r"electron efficiency =  %.3f percent"%(electron_eff_values[bestIp2e]),
                      "\n\n")
        
        if metric == "p":
            #chosen metric: muon/pion purity
            bestI_chosen =  bestI

        if metric == "pe":
            #chosen metric purity * efficiency for (mu or pi)
            bestI_chosen =  bestIpe
            
        if metric == "p2e":
            bestI_chosen =  bestIp2e
            
        
        coarse_A, coarse_B, coarse_H = A_values[bestI_chosen], B_values[bestI_chosen], hori_values[bestI_chosen]

        for coarse_L in coarse_values_L: 
            is_above_diag = slowEvents[LGid]["sumDownstreamACTs"] > (slowEvents[LGid]["sumACT1"] * coarse_A + coarse_B) 
            
            is_left =  slowEvents[LGid]["sumACT1"] < (coarse_H-coarse_B)/(coarse_A) 

            is_above_hori = slowEvents[LGid]["sumDownstreamACTs"] > coarse_H

            is_right =  slowEvents[LGid]["sumACT1"] > (coarse_H-coarse_B)/(coarse_A) 

            is_selected_left = is_above_diag & is_left
            is_selected_right = is_above_hori & is_right

            is_selected_electron = is_selected_left | is_selected_right 

            
            is_below_diag = slowEvents[LGid]["sumDownstreamACTs"] < (slowEvents[LGid]["sumACT1"] * coarse_A + coarse_B)
            is_below_hori = slowEvents[LGid]["sumDownstreamACTs"] < coarse_H
            isAboveMin = slowEvents[LGid]["sumDownstreamACTs"] > coarse_L

            is_selected_mupi = is_below_diag | is_below_hori
            is_selected_mupi = is_selected_mupi & isAboveMin

            mupi_pur, mupi_eff, electron_pur, electron_eff, nMuPi, nE = self.calculateMuPiAndElPurityEfficiency(is_selected_mupi, is_selected_electron, is_genuine_mupi, is_genuine_electron)

            A_values.append(coarse_A)
            B_values.append(coarse_B)
            hori_values.append(coarse_H)
            lower_values.append(coarse_L)
            nMuPi_values.append(nMuPi)
            nE_values.append(nE)
            mupi_pur_values.append(mupi_pur*100)
            mupi_eff_values.append(mupi_eff*100)
            electron_pur_values.append(electron_pur*100)
            electron_eff_values.append(electron_eff*100)


        #need to recalculate the best value:
        quality_metric = np.array(mupi_pur_values)
        #chosen metric purity * efficiency for (mu or pi)
        bestI = list(quality_metric).index(max(quality_metric))
        if metric == "p":
            #chosen metric: muon/pion purity
            bestI_chosen = bestI
        quality_metric = np.array(mupi_pur_values) * np.array(mupi_eff_values)
        bestIpe = list(quality_metric).index(max(quality_metric))  
        if metric == "pe":
            #chosen metric purity * efficiency for (mu or pi)
            bestI_chosen = bestIpe
        quality_metric = np.array(mupi_pur_values) * np.array(mupi_pur_values) * np.array(mupi_eff_values)
        bestIp2e = list(quality_metric).index(max(quality_metric))

        if metric == "p2e":
            bestI_chosen = bestIp2e

        self.plotSelectionScan(start_A_value, start_B_value, start_H_value, start_L_value, A_values, B_values, hori_values, lower_values, mupi_pur_values, mupi_eff_values, nMuPi_values, nE_values, bestI, bestIpe, bestIp2e, is_genuine_mupi, is_genuine_electron, electronLGcut, mupiLGcut)

        return bestI_chosen, A_values, B_values,  hori_values, lower_values,  mupi_pur_values, mupi_eff_values,electron_pur_values, electron_eff_values
        
        

    def findOptimalPiMuElCuts(self, quality_metric = "p2e", runOptimalSelection = False):
        """This function is designed to find the optimal cut line in ACT1 and sumDowsntream ACTs between the muons and electrons, based on the lead glass distribution"""
        
        if self.isLowMomentum: 
            #decide the number of points we want to search
            nTests = 7
            nTests_fine = 7
            coarse_bounds = 0.5 
            fine_bounds = 0.2 #+/-10% of the best fitted coarse value
            bestI, A_values, B_values, H_values, L_values,  mupi_pur_values, mupi_eff_values,electron_pur_values, electron_eff_values = self.scanOverACTLinearAB(self.ACTlinearA, self.ACTlinearB, self.horizontal_el, self.ACTLowerCut, coarse_bounds, nTests, quality_metric)

            #might be useful to catch extremums.. will see 
            #if A_values[bestI] == max(A_values) or A_values[bestI] == min(A_values) or :

            bestI_fine, A_values_fine, B_values_fine, H_values_fine, L_values_fine, mupi_pur_values_fine, mupi_eff_values_fine,electron_pur_values_fine, electron_eff_values_fine = self.scanOverACTLinearAB(A_values[bestI], B_values[bestI], H_values[bestI], L_values[bestI], fine_bounds, nTests_fine, quality_metric)


            if runOptimalSelection:
                #update the pion/muon cut, using true
                self.piMuBorderACT = self.plotMuonsAndPionsACTseparation(True)

                self.saving_folder_path_pdf = self.saving_folder_path_pdf + "_Optimal"
                self.saving_folder_path_png = self.saving_folder_path_png + "_Optimal"
                
                os.makedirs("../%s"%self.saving_folder_path_png, exist_ok=True)
                os.makedirs("../%s"%self.saving_folder_path_pdf, exist_ok=True)
                self.horizontal_el = H_values_fine[bestI_fine]
                self.ACTLinearA = A_values_fine[bestI_fine]
                self.ACTLinearB = B_values_fine[bestI_fine]
                self.ACTLower = L_values_fine[bestI_fine]

                self.makeAllParticleSelection()

            

    
    def addBranchToAllDetectors(self, new_branch_name, value, particle = None):
        print("Adding the branch %s to the data frame for  all detectors"%(new_branch_name))
        for dectector in range(len(self.arrayData)):
            self.addBranchToDataFrameDetector(new_branch_name, dectector, value, particle)
        return 0 
    
    def addOperationBranchToAllDetectors(self, new_branch_name,  branch1_name, operation, branch2_name, particle = None):
        dataFrameOfInterest = self.getDataFrameAllDetectors(particle)
        for detectorID in np.arange(0, len(dataFrameOfInterest), 1):
            if operation=="+":
                res = self.getColumnDataFrameDetector(branch1_name, detectorID, particle) + self.getColumnDataFrameDetector(branch2_name, detectorID, particle)
            elif operation == '-':
                res = self.getColumnDataFrameDetector(branch1_name, detectorID, particle) - self.getColumnDataFrameDetector(branch2_name, detectorID, particle)
            elif operation == '*':
                res = self.getColumnDataFrameDetector(branch1_name, detectorID, particle) * self.getColumnDataFrameDetector(branch2_name, detectorID, particle)
            elif operation == '/':
                res = self.getColumnDataFrameDetector(branch1_name, detectorID, particle) / self.getColumnDataFrameDetector(branch2_name, detectorID, particle)
            else:
                raise Exception("Wrong operator, use '+' or '-' or '*' or '/' please.")
            self.addBranchToDataFrameDetector(new_branch_name, detectorID, res)


    
    def plotHist1DfromData(self, array_columns, targetDetectors, plot_saving, normalise = False, MinBound = None, MaxBound = None, additionalLabel = None, yscale=None, nMaxColumns = 4, nbBins = 100, statsBin= False):
        #print("Plotting 1D histogram of columns: ", array_columns, " normalisation is set to: ", normalise)
        fig, ax = plt.subplots(max(1, math.ceil(len(targetDetectors)/nMaxColumns)), nMaxColumns, figsize = (16, 9))
        range_min = []
        range_max = []
        binwidth = []

        if MinBound!=None:
            #in case we gave an int
            if type(MinBound) == int or type(MinBound) == float:
                MinBound = [MinBound for i in range(len(targetDetectors))]
            #in case we gave an array of the wrong size
            elif len(MinBound) != len(targetDetectors):
                print("\nWarning: you have not given the correct number of min Bounds, asusming some of them")
                MinBound = [MinBound[0] for i in range(len(targetDetectors))]

        if MaxBound!=None:
            #in case we gave an int
            if type(MaxBound) == int or type(MaxBound) == float:
                MaxBound = [MaxBound for i in range(len(targetDetectors))]
            #in case we gave an array of the wrong size
            elif len(MaxBound) != len(targetDetectors):
                print("\nWarning: you have not given the correct number of Max Bounds, asusming some of them")
                MaxBound = [MaxBound[0] for i in range(len(targetDetectors))]

        for variableID, column in enumerate(array_columns):
            #label the plot depending on the column we are looking at
            if (column.find('Time') != -1):
                xaxis_label = 'Time (ns)'
            elif (column.find('TOF') != -1):
                xaxis_label = 'Time of Flight (ns)'
            elif (column.find('PE') != -1):
                xaxis_label = 'Charge (PE)'
            else:
                xaxis_label = column
            for indexInTargetDetector, channelID in enumerate(targetDetectors):
                #channelID is the detector of interest, indexInTargetDetector is only for detectors we
                #want to plot
                if (variableID == 0):
                    #so the same variables will have the same bins 
                    if MinBound == None:
                        possible_min = min(self.arrayData[channelID][column]) * 0.8
                        if np.isnan(possible_min) or min(self.arrayData[channelID][column]) == -9999:
                            possible_min = -1

                        range_min.append(possible_min)
                    else:
                        possible_min = max(MinBound[indexInTargetDetector],min(self.arrayData[channelID][column]) * 0.8)
                        range_min.append(possible_min)
                    

                    if MaxBound == None:
                        possible_max = max(self.arrayData[channelID][column]) * 1.2
                        if np.isnan(possible_max) or max(self.arrayData[channelID][column]) == -9999:
                            possible_max = possible_min + 2
                        range_max.append(possible_max)
                    else:
                        range_max.append(min(MaxBound[indexInTargetDetector], max(self.arrayData[channelID][column]) * 1.2))

                    

                    binwidth.append((range_max[-1]-range_min[-1])/nbBins)

                if len(targetDetectors) == 1:
                    axis = ax
                elif len(targetDetectors)>nMaxColumns:
                    #if we have multiple subplots: need to put into correct one
                    plot_row = math.floor(indexInTargetDetector/nMaxColumns)
                    plot_column = indexInTargetDetector - (plot_row * nMaxColumns)

                    axis = ax[plot_row, plot_column]
                else:
                    axis = ax[indexInTargetDetector]

                if statsBin:
                    label = "%s: %i entries\n Mean: %.2f Std: %.2f"%(column, len(self.arrayData[channelID][column]), self.arrayData[channelID][column].mean(), self.arrayData[channelID][column].std())
                else:
                    label = "%s: %i entries"%(column, len(self.arrayData[channelID][column]))
                
                axis.hist(self.arrayData[channelID][column], bins = nbBins, range = (range_min[indexInTargetDetector], range_max[indexInTargetDetector]), label = label, density=normalise, histtype="step")
        #cosmetics titles etcs
        for indexInTargetDetector, channelID in enumerate(targetDetectors):
            if len(targetDetectors) == 1:
                axis = ax
            elif len(targetDetectors)>nMaxColumns:
                    plot_row = math.floor(indexInTargetDetector/nMaxColumns)
                    plot_column = indexInTargetDetector - (plot_row * nMaxColumns)
                    axis = ax[plot_row, plot_column]
            else:
                axis = ax[indexInTargetDetector]
            
            if yscale == 'log':
                axis.set_yscale('log')
                axis.set_ylim([0.5, None])
            
            if nMaxColumns >= len(targetDetectors):
                axis.legend(fontsize = 15)
            else:
                axis.legend(fontsize = 10)
            axis.set_title("%s"%(self.channelNames[channelID]), fontsize = 18, weight = "bold")
            axis.set_xlabel("%s"%xaxis_label, fontsize = 18)
            if binwidth[indexInTargetDetector] > 10e3:
                axis.set_ylabel("Occurences/%.3e"%(binwidth[indexInTargetDetector]), fontsize = 18)
            if binwidth[indexInTargetDetector] > 1:
                axis.set_ylabel("Occurences/%.1f"%(binwidth[indexInTargetDetector]), fontsize = 18)
            elif binwidth[indexInTargetDetector] > 0.1:
                axis.set_ylabel("Occurences/%.2f"%(binwidth[indexInTargetDetector]), fontsize = 18)
            elif binwidth[indexInTargetDetector] > 0.01:
                axis.set_ylabel("Occurences/%.3f"%(binwidth[indexInTargetDetector]), fontsize = 18)
            elif binwidth[indexInTargetDetector] > 0.001:
                axis.set_ylabel("Occurences/%.3e"%(binwidth[indexInTargetDetector]), fontsize = 18)
            axis.grid()

        if normalise:
            fig.suptitle('WCTE Beamtest - Run %i, p = %i MeV/c n = %s - density \n%s'%(self.runNumber, self.runMomentum, self.runRefractiveIndex, additionalLabel), fontsize=18, weight ='bold')
        else:
            fig.suptitle('WCTE Beamtest - Run %i, p = %i MeV/c \n%s'%(self.runNumber, self.runMomentum, additionalLabel), fontsize=18, weight ='bold')
        plt.tight_layout()
        plt.savefig("../%s/%s_Run%i.png"%(self.saving_folder_path_png, plot_saving, self.runNumber))
        plt.savefig("../%s/%s_Run%i.pdf"%( self.saving_folder_path_pdf, plot_saving, self.runNumber))
        

    def plotSelectionACT1sumDownstreamACT(self, ymax = 100):
        if self.isLowMomentum:
            xmin, xmax = 0, 20
            ymin, ymax = 0, ymax
            fig, ax = self.plot2DHistFromBranches(0, "sumACT1", 0, "sumDownstreamACTs", "(PE)", "(PE)", "SelectionACTs", True, [500, 300], [[xmin, xmax], [ymin, ymax]], False)
            
            xrange = np.linspace(xmin, xmax, 100)
            

            muonElcut = np.where(self.ACTlinearA * xrange + self.ACTlinearB > self.horizontal_el, self.ACTlinearA * xrange + self.ACTlinearB, self.horizontal_el)

            ax.plot(xrange, self.piMuBorderACT + xrange * 0, 'r--', label = 'pi/mu separation', linewidth = 2)
            ax.plot(xrange, self.ACTLowerCut + xrange * 0, 'r-', label = 'pi/noise separation', linewidth = 2)
            ax.plot(xrange, muonElcut, 'k--', label = 'mu/el separation', linewidth = 2)

            ax.legend()

            plt.savefig("../%s/SelectionACTs_Run%i.png"%(self.saving_folder_path_png, self.runNumber))
            plt.savefig("../%s/SelectionsACTs_Run%i.pdf"%( self.saving_folder_path_pdf, self.runNumber))

    def makeMuPiESelectionUsingCuts(self, coarse_A, coarse_B, coarse_H, coarse_L, is_genuine_mupi, is_genuine_electron):
        #do the input values as first ones
        slowEvents= self.makeNewDataFrameFromSelection(self.arrayData, self.arrayData[0]["matchedHit0_TOF"] < self.protonsTOFCut)
        # coarse_A = self.ACTlinearA
        # coarse_B = self.ACTlinearB
        # coarse_H = self.horizontal_el
        # coarse_L = self.ACTLowerCut

        LGid = self.channelNames.index("PbGlass")

        is_above_diag = slowEvents[LGid]["sumDownstreamACTs"] > (slowEvents[LGid]["sumACT1"] * coarse_A + coarse_B)   
        
        is_left =  slowEvents[LGid]["sumACT1"] < (coarse_H-coarse_B)/(coarse_A) 
        is_above_hori = slowEvents[LGid]["sumDownstreamACTs"] > coarse_H
        is_right =  slowEvents[LGid]["sumACT1"] > (coarse_H-coarse_B)/(coarse_A) 
        is_selected_left = is_above_diag & is_left
        is_selected_right = is_above_hori & is_right
        is_selected_electron = is_selected_left | is_selected_right 


        is_below_diag = slowEvents[LGid]["sumDownstreamACTs"] < (slowEvents[LGid]["sumACT1"] * coarse_A + coarse_B)
        is_below_hori = slowEvents[LGid]["sumDownstreamACTs"] < coarse_H
        isAboveMin = slowEvents[LGid]["sumDownstreamACTs"] > coarse_L
        is_selected_mupi = is_below_diag | is_below_hori
        is_selected_mupi = is_selected_mupi & isAboveMin
        mupi_pur_start, mupi_eff_start, electron_pur_start, electron_eff_start, nMuPi_start, nE_start = self.calculateMuPiAndElPurityEfficiency(is_selected_mupi, is_selected_electron, is_genuine_mupi, is_genuine_electron)

        return mupi_pur_start, mupi_eff_start, electron_pur_start, electron_eff_start, nMuPi_start, nE_start, is_selected_electron, is_selected_mupi

    def plotSelectionScan(self, start_A_value, start_B_value, start_H_value, start_L_value, A_values, B_values, hori_values, lower_values,  mupi_pur_values, mupi_eff_values, nMuPi_values, nE_values, bestI, bestIpe, bestIp2e, is_genuine_mupi, is_genuine_electron, electronLGcut, mupiLGcut):
        xmin, xmax = -0.2, 20
        ymin, ymax = -2, max(max(B_values) * 1.3, max(hori_values) * 1.3)
        
        
        fig, ax = self.plot2DHistFromBranches(0, "sumACT1", 0, "sumDownstreamACTs", "(PE)", "(PE)", "Initially A: %.2f, B: %.2f, H: %.2f, L: %.2f, LG e cut: %.2f, LG muPi cut: %.2f" %(start_A_value, start_B_value, start_H_value, start_L_value, electronLGcut, mupiLGcut), True, [500, 300], [[xmin, xmax], [ymin, ymax]], False)
        
        xrange = np.linspace(xmin, xmax, 100)

        muonElcut = np.where(start_A_value * xrange + start_B_value > self.horizontal_el, start_A_value * xrange + start_B_value, self.horizontal_el)

        ax.plot(xrange, self.ACTLowerCut + xrange * 0, 'k-', linewidth = 2)
        
        slowEvents= self.makeNewDataFrameFromSelection(self.arrayData, self.arrayData[0]["matchedHit0_TOF"] < self.protonsTOFCut)
    
        # #define genuine electron and mu/pi events
        LGid = self.channelNames.index("PbGlass")

        # #do the input values as first ones
        # coarse_A = self.ACTlinearA
        # coarse_B = self.ACTlinearB
        # coarse_H = self.horizontal_el
        # coarse_L = self.ACTLowerCut
        # is_above_diag = slowEvents[LGid]["sumDownstreamACTs"] > (slowEvents[LGid]["sumACT1"] * coarse_A + coarse_B)   
        
        # is_left =  slowEvents[LGid]["sumACT1"] < (coarse_H-coarse_B)/(coarse_A) 
        # is_above_hori = slowEvents[LGid]["sumDownstreamACTs"] > coarse_H
        # is_right =  slowEvents[LGid]["sumACT1"] > (coarse_H-coarse_B)/(coarse_A) 
        # is_selected_left = is_above_diag & is_left
        # is_selected_right = is_above_hori & is_right
        # is_selected_electron = is_selected_left | is_selected_right 


        # is_below_diag = slowEvents[LGid]["sumDownstreamACTs"] < (slowEvents[LGid]["sumACT1"] * coarse_A + coarse_B)
        # is_below_hori = slowEvents[LGid]["sumDownstreamACTs"] < coarse_H
        # isAboveMin = slowEvents[LGid]["sumDownstreamACTs"] > start_L_value
        # is_selected_mupi = is_below_diag | is_below_hori
        # is_selected_mupi = is_selected_mupi & isAboveMin
        # mupi_pur_start, mupi_eff_start, electron_pur_start, electron_eff_start, nMuPi_start, nE_start = self.calculateMuPiAndElPurityEfficiency(is_selected_mupi, is_selected_electron, is_genuine_mupi, is_genuine_electron)


        ######### start with config only ########

        # coarse_A = self.ACTlinearA
        # coarse_B = self.ACTlinearB
        # coarse_H = self.horizontal_el
        # coarse_L = self.ACTLowerCut

        mupi_pur_start, mupi_eff_start, electron_pur_start, electron_eff_start, nMuPi_start, nE_start, is_selected_electron, is_selected_mupi = self.makeMuPiESelectionUsingCuts(self.ACTlinearA, self.ACTlinearB, self.horizontal_el, self.ACTLowerCut, is_genuine_mupi, is_genuine_electron)


        ax.plot(xrange, muonElcut, 'k-', label = 'mupi/el separation: from config \nA: %.2f B: %.2f H: %.2f L:%.2f\n# selected mupi: %i, e: %i\nmupi pur. = %.2f%% eff. = %.2f%%'%(self.ACTlinearA, self.ACTlinearB, self.horizontal_el,  self.ACTLowerCut, nMuPi_start, nE_start, mupi_pur_start * 100, mupi_eff_start * 100), linewidth = 2)

        area_scan_x = [0, (max(hori_values) - max(B_values))/max(A_values),
                       xmax, xmax, 
                       (min(hori_values) - min(B_values))/min(A_values), 0, 0]
        
        area_scan_y = [max(B_values), max(hori_values), max(hori_values), min(hori_values), min(hori_values), max(min(B_values), min(hori_values)), max(B_values)]

        ax.fill(area_scan_x, area_scan_y, alpha = 0.1, color = "magenta", label = 'Region scanned')

        area_scan_x = [0, xmax, xmax, 0]
        
        area_scan_y = [max(lower_values), max(lower_values), min(lower_values), min(lower_values)]

        ax.fill(area_scan_x, area_scan_y, alpha = 0.1, color = "magenta")

        muonElcut_purity = np.where(A_values[bestI] * xrange + B_values[bestI] > hori_values[bestI], A_values[bestI] * xrange + B_values[bestI], hori_values[bestI])

        ax.plot(xrange, muonElcut_purity, 'g--', label = 'mupi/el separation: max purity\nA: %.2f B: %.2f H: %.2f L:%.2f\n# selected mupi: %i, e: %i\nmupi pur. = %.2f%% eff. = %.2f%%'%(A_values[bestI], B_values[bestI],  hori_values[bestI],  lower_values[bestI], nMuPi_values[bestI], nE_values[bestI], mupi_pur_values[bestI], mupi_eff_values[bestI]), linewidth = 2)


        ax.plot(xrange, np.array(muonElcut_purity) * 0 + lower_values[bestI], 'g--', linewidth = 2)

        muonElcut_pe = np.where(A_values[bestIpe] * xrange + B_values[bestIpe] > hori_values[bestIpe], A_values[bestIpe] * xrange + B_values[bestIpe], hori_values[bestIpe])
        

        ax.plot(xrange, muonElcut_pe, 'b--', label = 'mupi/el separation: max purity x efficiency\nA: %.2f B: %.2f H: %.2f L:%.2f\n# selected mupi: %i, e: %i\nmupi pur. = %.2f%% eff. = %.2f%%'%(A_values[bestIpe], B_values[bestIpe],  hori_values[bestIpe],  lower_values[bestIpe], nMuPi_values[bestIpe], nE_values[bestIpe], mupi_pur_values[bestIpe], mupi_eff_values[bestIpe]), linewidth = 2)

        ax.plot(xrange, np.array(muonElcut_purity) * 0 + lower_values[bestIpe], 'b--', linewidth = 2)


        muonElcut_p2e = np.where(A_values[bestIp2e] * xrange + B_values[bestIp2e] > hori_values[bestIp2e], A_values[bestIp2e] * xrange + B_values[bestIp2e], hori_values[bestIp2e])

        ax.plot(xrange, muonElcut_p2e, 'r--', label = 'mupi/el separation: max purity^2 x efficiency\nA: %.2f B: %.2f H: %.2f L:%.2f\n# selected mupi: %i, e: %i\nmupi pur. = %.2f%% eff. = %.2f%%'%(A_values[bestIp2e], B_values[bestIp2e],  hori_values[bestIp2e],  lower_values[bestIp2e], nMuPi_values[bestIp2e], nE_values[bestIp2e], mupi_pur_values[bestIp2e], mupi_eff_values[bestIp2e]), linewidth = 2)

        ax.plot(xrange, np.array(muonElcut_purity) * 0 + lower_values[bestIp2e], 'r--', linewidth = 2)

        ax.legend(fontsize = 15, loc = 1)

        plt.savefig("../%s/SelectionACTsScan_startA%.2f_startB%.2f_startH%.2f_startL%.2f_Run%i.png"%(self.saving_folder_path_png, start_A_value, start_B_value, start_H_value, start_L_value, self.runNumber))
        plt.savefig("../%s/SelectionACTsScan_startA%.2f_startB%.2f_startH%.2f_startL%.2f_Run%i.pdf"%( self.saving_folder_path_pdf,start_A_value, start_B_value, start_H_value, start_L_value, self.runNumber))


        fig, ax = self.plot2DHistFromBranches(0, "sumACT1", 0, "sumDownstreamACTs", "(PE)", "(PE)", "Initially A: %.2f, B: %.2f, H: %.2f, L: %.2f" %(start_A_value, start_B_value, start_H_value, start_L_value), True, [500, 300], [[xmin, xmax], [ymin, ymax]], False)

        for i in range(len(hori_values)):
            muonElcut_pe = np.where(A_values[i] * xrange + B_values[i] > hori_values[i], A_values[i] * xrange + B_values[i], hori_values[i])
            
            ax.plot(xrange, muonElcut_pe, alpha = 0.2, color = 'black', linewidth = 1)
            ax.plot(xrange, muonElcut_pe * 0 + lower_values[i], alpha = 0.2, color = 'lightgray')

        ax.plot(xrange, muonElcut_pe, alpha = 0.2, color = 'black', linewidth = 1, label = 'Cut lines tested')

        


        ax.legend(fontsize = 15, loc = 1)
        plt.savefig("../%s/SelectionACTsScan_startA%.2f_startB%.2f_startH%.2f_startL%.2f_CutLines_Run%i.png"%(self.saving_folder_path_png, start_A_value, start_B_value, start_H_value, start_L_value, self.runNumber))
        plt.savefig("../%s/SelectionACTsScan_startA%.2f_startB%.2f_startH%.2f_startL%.2f_CutLines_Run%i.pdf"%( self.saving_folder_path_pdf,start_A_value, start_B_value, start_H_value, start_L_value, self.runNumber))


        #need to visualise the quality of the cuts using the LG
        #step1: gray histogram of the LG distribution of all slow events
        for i in range(20):
            plt.close()

        indices_metric = [0, bestI, bestIpe, bestIp2e]
        metric_names = ["Default, from config", "Maximizing only purity", r"Maximizing  purity $\times$ efficiency", r"Maximizing purity$^2 \times$ efficiency", "Lead glass particle identification"]

        for m, metric in enumerate(["default", "p", "pe", "p2e", "justLG"]):
            isJustLG = False
            if metric == "justLG":
                isJustLG = True

            elif metric == "default":
                A, B, H, L = self.ACTlinearA, self.ACTlinearB, self.horizontal_el, self.ACTLowerCut
                mupi_pur_start, mupi_eff_start, electron_pur_start, electron_eff_start, nMuPi_start, nE_start, is_selected_electron, is_selected_mupi = self.makeMuPiESelectionUsingCuts(self.ACTlinearA, self.ACTlinearB, self.horizontal_el, self.ACTLowerCut, is_genuine_mupi, is_genuine_electron)
            
            else:
                A, B, H, L = A_values[indices_metric[m]], B_values[indices_metric[m]], hori_values[indices_metric[m]], lower_values[indices_metric[m]]
                mupi_pur_start, mupi_eff_start, electron_pur_start, electron_eff_start, nMuPi_start, nE_start, is_selected_electron, is_selected_mupi = self.makeMuPiESelectionUsingCuts(A_values[indices_metric[m]], B_values[indices_metric[m]], hori_values[indices_metric[m]], lower_values[indices_metric[m]], is_genuine_mupi, is_genuine_electron) 

            #############################################################
            fig, ax = plt.subplots(1, 1, figsize = (16, 9))
            LG_all = slowEvents[LGid]["matchedHit0_WindowIntPE"]
            nBins = 200
            binWidth = (max(LG_all)-min(LG_all)) / nBins
            bins_all = int((max(LG_all)-min(LG_all)) / binWidth)
            counts, bins, _ = ax.hist(LG_all, bins = bins_all, histtype="stepfilled", 
                    color="lightgray", 
                    label = "All slow particles: %i (%.2f %% of total)"%(len(LG_all), len(LG_all)/len(self.getArrayData()[LGid]["matchedHit0_WindowIntPE"])* 100))

            #returns the gaussian fit to the electron and muon distributions from the original cut value, we need to propagate the bins for the fit params to make sense
            electron_muon_LG_gaussian_params = self.fitMuonsAndElectronLGPeaks(bins, False)

            x_range = np.linspace(min(LG_all), max(LG_all), 400)
            ax.plot(x_range, gaussian(x_range, *electron_muon_LG_gaussian_params[0]), "b--", label = 'Fitted electron peak\nA= %.1e mean = %.2f std = %.2f'%(electron_muon_LG_gaussian_params[0][0], electron_muon_LG_gaussian_params[0][1], electron_muon_LG_gaussian_params[0][2]))
            ax.plot(x_range, gaussian(x_range, *electron_muon_LG_gaussian_params[1]), "g--", label = 'Fitted muon peak\nA= %.1e mean = %.2f std = %.2f'%(electron_muon_LG_gaussian_params[1][0], electron_muon_LG_gaussian_params[1][1], electron_muon_LG_gaussian_params[1][2]))
            ax.axvline(electronLGcut, color = "red", label = "electron LG cut: %.1f \n%i genuine electrons "%(electronLGcut, sum(is_genuine_electron)))

            # Annotate with an arrow pointing right for the genuine electrons
            ax.annotate(
                '', xy=(electronLGcut+1, len(slowEvents[LGid]["matchedHit0_WindowIntPE"] * 0.07)), xycoords='data',  # Pointing at the top of the vertical line
                xytext=(electronLGcut, len(slowEvents[LGid]["matchedHit0_WindowIntPE"] * 0.07)), textcoords='data',  # Pointing to the right, yes this is confusing but see figure
                arrowprops=dict(arrowstyle='->', color='red', lw = 5)
            )

            ax.axvline(mupiLGcut, color = "black", label = "mu and pi LG cut: %.1f \n%i genuine muons and pions "%(mupiLGcut, sum(is_genuine_mupi)))


            ax.annotate(
                '', xy=(mupiLGcut, len(slowEvents[LGid]["matchedHit0_WindowIntPE"] * 0.07)), xycoords='data',  # Pointing at the top of the vertical line
                xytext=(mupiLGcut-1, len(slowEvents[LGid]["matchedHit0_WindowIntPE"] * 0.07)), textcoords='data',  # Pointing to the left
                arrowprops=dict(arrowstyle='<-', color='black', lw = 5)
            )

            ax.set_xlabel("Lead Glass WindowIntPE", fontsize = 18)
            ax.set_ylabel("Number of events", fontsize = 18)
            ax.tick_params(axis='both', which='major', labelsize=15)


            if not(isJustLG):
                muPiLG = slowEvents[LGid]["matchedHit0_WindowIntPE"][is_selected_mupi]
                electronLG = slowEvents[LGid]["matchedHit0_WindowIntPE"][is_selected_electron]
                nBinsMuPiLG = int((max(muPiLG)-min(muPiLG)) / binWidth)
                nBinsELG = int((max(electronLG)-min(electronLG)) / binWidth)
                colors = ["green", "blue"]
                
                ax.hist([muPiLG, electronLG], bins, 
                        histtype='step', color = colors, stacked=False, 
                        label = ["Selected muons and pions: %i\n(%.3f %% of slow events)\npurity: %.2f%%, efficiciency: %.2f%%"%(len(muPiLG), len(muPiLG)/len(slowEvents[LGid]["matchedHit0_WindowIntPE"]) * 100, mupi_pur_start * 100, mupi_eff_start * 100),
                        "Selected electrons: %i\n(%.3f %% of slow events)"%(len(electronLG), len(electronLG)/len(slowEvents[LGid]["matchedHit0_WindowIntPE"]) * 100)])

               
                ax.set_title("Selection cuts: A: %.2f B: %.2f H: %.2f L: %.2f"%(A, B, H, L), fontsize = 12)
            ax.legend(fontsize = 15)
            ax.grid()
            ax.set_xlim(min(LG_all), max(LG_all))
                
            fig.suptitle('WCTE Beamtest - Run %i, p = %i MeV/c n = %s \n %s'%(self.runNumber, self.runMomentum, self.runRefractiveIndex, metric_names[m]), fontsize=18, weight ='bold')
            ax.set_yscale("log")
            ax.set_ylim(0.5, len(slowEvents[LGid]["matchedHit0_WindowIntPE"]) * 1.1)

            fig.savefig("../%s/MuPi_E_LGseparation_%s_startA%.2f_startB%.2f_startH%.2f_startL%.2f_Run%i.png"%(self.saving_folder_path_png, metric, start_A_value, start_B_value, start_H_value, start_L_value, self.runNumber))
        
            fig.savefig("../%s/MuPi_E_LGseparation_%s_startA%.2f_startB%.2f_startH%.2f_startL%.2f_Run%i.pdf"%(self.saving_folder_path_pdf, metric, start_A_value, start_B_value, start_H_value, start_L_value, self.runNumber))

            # plt.show()

            #########################################################

    def plotMuonsAndPionsACTseparation(self):
        #original cut value, we need to propagate the bins for the fit params to make sense

            

            # if five_sigma_mu > five_sigma_pi:
            #     piACTcut =  five_sigma_pi
            #     muACTcut = five_sigma_mu
            
            # elif four_sigma_mu > four_sigma_pi:
            #     piACTcut =  four_sigma_pi
            #     muACTcut = four_sigma_mu
            
            # elif three_sigma_mu > three_sigma_pi:
            #     piACTcut =  three_sigma_pi
            #     muACTcut = three_sigma_mu

            # else:
            #     weighted_mean_distance = ((mu_params[1] - mu_params[2]) * mu_params[0] + ( + pi_params[2] + pi_params[1]) * pi_params[0]) / (pi_params[0] + mu_params[0])
                
            #     piACTcut =  weighted_mean_distance # self.weirdElectronLGcut
            #     muACTcut = weighted_mean_distance # self.weirdElectronLGcut 

            
            self.isNotElectron = list(~self.isElectron)

            print(len(self.isNotElectron))
            
            #slowEvents= self.makeNewDataFrameFromSelection(self.arrayData, self.arrayData[0]["matchedHit0_TOF"] < self.protonsTOFCut)
            fig, ax = plt.subplots(1, 1, figsize = (16, 9))

            ACT_all = self.arrayData[0]
            print(ACT_all)
            ACT_all = ACT_all[self.isNotElectron]
            print(ACT_all)
            slowEvents = ACT_all[ACT_all["matchedHit0_TOF"]< self.protonsTOFCut] 
            ACT_all = slowEvents["sumDownstreamACTs"]
            
            # slowEvents[0]["sumDownstreamACTs"]
            # ACT_all = ACT_all

            nBins = 200
            binWidth = (max(ACT_all)-min(ACT_all)) / nBins
            bins_all = int((max(ACT_all)-min(ACT_all)) / binWidth)

            counts, bins, _ = ax.hist(ACT_all, bins = bins_all, histtype="stepfilled", 
                    color="lightgray", 
                    label = "All non-electron slow particles: %i (%.2f %% of total)"%(len(ACT_all), len(ACT_all)/len(self.getArrayData()[0]["matchedHit0_WindowIntPE"])* 100))
            
            ax.hist([self.pionArray[0]["sumDownstreamACTs"], self.muonArray[0]["sumDownstreamACTs"]], alpha = 0.3, bins = bins, histtype="stepfilled", stacked = True, 
                    color=["red", "green"], 
                    label = ["Config-file identified pions: %i (%.2f %% of total)"%(len(self.pionArray[0]["sumDownstreamACTs"]), len(self.pionArray[0]["sumDownstreamACTs"])/len(self.getArrayData()[0]["matchedHit0_WindowIntPE"])* 100),  "Config-file identified muons: %i (%.2f %% of total)"%(len(self.muonArray[0]["sumDownstreamACTs"]), len(self.muonArray[0]["sumDownstreamACTs"])/len(self.getArrayData()[0]["matchedHit0_WindowIntPE"])* 100)])


            #pion_muon_ACT_gaussian_params = self.fitMuonsAndPionsACTPeaks(100, False)

            pion_muon_ACT_gaussian_params = self.fitMuonsAndPionsACTPeaks(bins)
            pi_params = pion_muon_ACT_gaussian_params[0]
            mu_params = pion_muon_ACT_gaussian_params[1]

            nPoints = 30
            steps = (mu_params[1]-pi_params[1])/nPoints
            previous_metric = 0

            figQuality, (axQualityPurityMuon, axQualityPurityPion) = plt.subplots(1, 2, figsize = (16, 9), tight_layout=True)
            axQualityEfficiencyPion = axQualityPurityPion.twinx() 
            axQualityEfficiencyMuon = axQualityPurityMuon.twinx() 

            mu_pur_array = []
            pi_pur_array = []
            mu_eff_array = []
            pi_eff_array = []
            cutPosition = []

            for i in range(nPoints):
                test_cut = pi_params[1] + i * steps
                
                
                nTotalMuons = quad(gaussian, 0, 1000, args = (mu_params[0], mu_params[1], mu_params[2]))[0] * (bins[1]-bins[0])
                nTotalPions =  quad(gaussian, 0, 1000, args = (pi_params[0], pi_params[1], pi_params[2]))[0] * (bins[1]-bins[0])
                
                
                nGenuineMuonsInMuonSel =  quad(gaussian, test_cut, 1000, args = (mu_params[0], mu_params[1], mu_params[2]))[0] * (bins[1]-bins[0])
                nGenuinePionsInMuonSel =  quad(gaussian, test_cut, 1000, args = (pi_params[0], pi_params[1], pi_params[2]))[0] * (bins[1]-bins[0])
                
                nGenuinePionsInPionSel = quad(gaussian, 0, test_cut, args = (pi_params[0], pi_params[1], pi_params[2]))[0] * (bins[1]-bins[0])
                nGenuineMuonsInPionSel = quad(gaussian, 0, test_cut, args = (mu_params[0], mu_params[1], mu_params[2]))[0] * (bins[1]-bins[0])

                muon_purity = nGenuineMuonsInMuonSel/(nGenuineMuonsInMuonSel+nGenuinePionsInMuonSel)

                muon_efficiency = nGenuineMuonsInMuonSel/nTotalMuons

                pion_purity = nGenuinePionsInPionSel/(nGenuineMuonsInPionSel+nGenuinePionsInPionSel)

                pion_efficiency = nGenuinePionsInPionSel/nTotalPions

                mu_pur_array.append(muon_purity)
                pi_pur_array.append(pion_purity)
                mu_eff_array.append(muon_efficiency)
                pi_eff_array.append(pion_efficiency)
                cutPosition.append(test_cut)

                if muon_purity * pion_purity > previous_metric:
                    muon_purity_final = muon_purity
                    muon_efficiency_final = muon_efficiency
                    pion_purity_final = pion_purity
                    pion_efficiency_final = pion_efficiency
                    
                    test_cut_best = test_cut
                    previous_metric = muon_purity * pion_purity
                

            muonPurity, muonEfficiency, pionPurity, pionEfficiency = muon_purity_final, muon_efficiency_final, pion_purity_final, pion_efficiency_final

            muACTcut = test_cut_best
            axQualityPurityMuon.set_title("Muons", fontsize = 15, weight = "bold")
            axQualityPurityPion.set_title("Pions", fontsize = 15, weight = "bold")

            axQualityPurityMuon.plot(cutPosition, mu_pur_array, color = 'green', marker = '^') 
            axQualityPurityPion.plot(cutPosition, pi_pur_array, color = 'green', marker = '^') 

            axQualityPurityMuon.set_ylim(0.4, 1.01)
            axQualityEfficiencyMuon.set_ylim(0.4, 1.01)
            axQualityPurityPion.set_ylim(0.4, 1.01)
            axQualityEfficiencyPion.set_ylim(0.4, 1.01)
            
            axQualityEfficiencyMuon.plot(cutPosition, mu_eff_array, color = 'red', marker = 'o') 
            axQualityEfficiencyPion.plot(cutPosition, pi_eff_array, color = 'red', marker = 'o') 

        
            axQualityEfficiencyMuon.set_ylabel('Efficiency', color = 'red', fontsize = 16)
            axQualityEfficiencyPion.set_ylabel('Efficiency', color = 'red', fontsize = 16)

            axQualityPurityMuon.set_ylabel('Purity', color = 'green', fontsize = 16)
            axQualityPurityPion.set_ylabel('Purity', color = 'green', fontsize = 16)

            axQualityPurityMuon.grid()
            axQualityPurityPion.grid()

            axQualityPurityMuon.tick_params(axis ='y', labelcolor = 'green')
            axQualityPurityPion.tick_params(axis ='y', labelcolor = 'green')

            axQualityEfficiencyMuon.tick_params(axis ='y', labelcolor = 'red')
            axQualityEfficiencyPion.tick_params(axis ='y', labelcolor = 'red')

            axQualityPurityMuon.axvline(muACTcut, color = 'black', label= "Cut line chosen: %.2f PE \n Muon purity = %.2f, efficiency = %.2f"%(muACTcut, muonPurity * 100, muonEfficiency * 100))
            axQualityPurityPion.axvline(muACTcut, color = 'black', label= "Cut line chosen: %.2f PE \n Pion purity = %.2f, efficiency = %.2f"%(muACTcut, pionPurity * 100, pionEfficiency * 100))

            axQualityPurityMuon.legend(fontsize = 16)
            axQualityPurityPion.legend(fontsize = 16)
            #axQualityEfficiencyMuon.legend(fontsize = 16)
            
            axQualityPurityPion.set_xlabel("Cut position in sumDownstreamACTs (PE)", fontsize = 16)
            axQualityPurityMuon.set_xlabel("Cut position in sumDownstreamACTs (PE)", fontsize = 16)


            

            figQuality.suptitle('WCTE Beamtest - Run %i, p = %i MeV/c n = %s'%(self.runNumber, self.runMomentum, self.runRefractiveIndex), fontsize=18, weight ='bold')

            figQuality.savefig("../%s/Mu_Pi_ACTseparationQuality_Run%i.png"%(self.saving_folder_path_png, self.runNumber))
            figQuality.savefig("../%s/Mu_Pi_ACTseparationQuality_Run%i.pdf"%(self.saving_folder_path_pdf, self.runNumber))


            
            

            x_range = np.linspace(min(ACT_all), max(ACT_all), 400)

            ax.axvline(muACTcut, color = "black", label = "Optimal pi/mu ACT cut: %.2f PE"%(muACTcut))


            ax.plot(x_range, gaussian(x_range, *pion_muon_ACT_gaussian_params[0]), "r--", label = 'Fitted pion peak\nA= %.1e mean = %.2f PE std = %.2f PE \n Purity = %.2f%% Efficiency = %.2f%%'%(pion_muon_ACT_gaussian_params[0][0], pion_muon_ACT_gaussian_params[0][1], pion_muon_ACT_gaussian_params[0][2], pionPurity * 100, pionEfficiency * 100))
            ax.plot(x_range, gaussian(x_range, *pion_muon_ACT_gaussian_params[1]), "g--", label = 'Fitted muon peak\nA= %.1e mean = %.2f PE std = %.2f PE\n Purity = %.2f%% Efficiency = %.2f%%'%(pion_muon_ACT_gaussian_params[1][0], pion_muon_ACT_gaussian_params[1][1], pion_muon_ACT_gaussian_params[1][2], muonPurity * 100, muonEfficiency * 100))
            
            
            #ax.axvline(electronLGcut, color = "red", label = "electron LG cut: %.1f \n%i genuine electrons "%(electronLGcut, sum(is_genuine_electron)))

            # Annotate with an arrow pointing right for the genuine electrons
            # ax.annotate(
            #     '', xy=(electronLGcut+1, len(slowEvents[LGid]["matchedHit0_WindowIntPE"] * 0.07)), xycoords='data',  # Pointing at the top of the vertical line
            #     xytext=(electronLGcut, len(slowEvents[LGid]["matchedHit0_WindowIntPE"] * 0.07)), textcoords='data',  # Pointing to the right, yes this is confusing but see figure
            #     arrowprops=dict(arrowstyle='->', color='red', lw = 5)
            # )

            

            # ax.annotate(
            #     '', xy=(mupiLGcut, len(slowEvents[LGid]["matchedHit0_WindowIntPE"] * 0.07)), xycoords='data',  # Pointing at the top of the vertical line
            #     xytext=(mupiLGcut-1, len(slowEvents[LGid]["matchedHit0_WindowIntPE"] * 0.07)), textcoords='data',  # Pointing to the left
            #     arrowprops=dict(arrowstyle='<-', color='black', lw = 5)
            # )

            ax.set_xlabel("sum of dowstream ACTs", fontsize = 18)
            ax.set_ylabel("Number of events", fontsize = 18)
            ax.tick_params(axis='both', which='major', labelsize=15)


            # if not(isJustLG):
            #     muPiLG = slowEvents[LGid]["matchedHit0_WindowIntPE"][is_selected_mupi]
            #     electronLG = slowEvents[LGid]["matchedHit0_WindowIntPE"][is_selected_electron]
            #     nBinsMuPiLG = int((max(muPiLG)-min(muPiLG)) / binWidth)
            #     nBinsELG = int((max(electronLG)-min(electronLG)) / binWidth)
            #     colors = ["green", "blue"]
                
            #     ax.hist([muPiLG, electronLG], bins, 
            #             histtype='step', color = colors, stacked=False, 
            #             label = ["Selected muons and pions: %i\n(%.3f %% of slow events)\npurity: %.2f%%, efficiciency: %.2f%%"%(len(muPiLG), len(muPiLG)/len(slowEvents[LGid]["matchedHit0_WindowIntPE"]) * 100, mupi_pur_start * 100, mupi_eff_start * 100),
            #             "Selected electrons: %i\n(%.3f %% of slow events)"%(len(electronLG), len(electronLG)/len(slowEvents[LGid]["matchedHit0_WindowIntPE"]) * 100)])

               
            #     ax.set_title("Selection cuts: A: %.2f B: %.2f H: %.2f L: %.2f"%(A, B, H, L), fontsize = 12)
            ax.legend(fontsize = 15)
            ax.grid()
            ax.set_xlim(min(ACT_all), max(ACT_all))
                
            fig.suptitle('WCTE Beamtest - Run %i, p = %i MeV/c n = %s'%(self.runNumber, self.runMomentum, self.runRefractiveIndex), fontsize=18, weight ='bold')
            #we do not want log just yet
            
            ax.set_ylim(0, max(pi_params[0] * 1.1, mu_params[0] * 1.1))

            fig.savefig("../%s/Mu_Pi_ACTseparation_Run%i.png"%(self.saving_folder_path_png, self.runNumber))
            fig.savefig("../%s/Mu_Pi_ACTseparation_Run%i.pdf"%(self.saving_folder_path_pdf, self.runNumber))

            ax.set_yscale("log")
            ax.set_ylim(0.5, len(ACT_all) * 1.1)
            fig.savefig("../%s/Mu_Pi_ACTseparationLOG_Run%i.png"%(self.saving_folder_path_png, self.runNumber))
            fig.savefig("../%s/Mu_Pi_ACTseparationLOG_Run%i.pdf"%(self.saving_folder_path_pdf, self.runNumber))

        
            return muACTcut
        
            # fig.savefig("../%s/MuPi_E_LGseparation_%s_startA%.2f_startB%.2f_startH%.2f_startL%.2f_Run%i.pdf"%(self.saving_folder_path_pdf, metric, start_A_value, start_B_value, start_H_value, start_L_value, self.runNumber))

            # plt.show()


    def plotSelectionWindow2ACT1sumDownstreamACT(self, ymax = 100):
        if self.isLowMomentum:
            if "sumACT1window2" not in self.getBranchList(0):
                return 0
            xmin, xmax = 0, 20
            ymin, ymax = 0, ymax
            fig, ax = self.plot2DHistFromBranches(0, "sumACT1window2", 0, "sumDownstreamACTsWindow2", "(PE)", "(PE)", "SelectionACTs", True, [500, 300], [[xmin, xmax], [ymin, ymax]], False)
            
            xrange = np.linspace(xmin, xmax, 100)
            

            muonElcut = np.where(self.ACTlinearA * xrange + self.ACTlinearB > self.horizontal_el, self.ACTlinearA * xrange + self.ACTlinearB, self.horizontal_el)

            # ax.plot(xrange, self.piMuBorderACT + xrange * 0, 'r--', label = 'pi/mu separation', linewidth = 2)
            # ax.plot(xrange, self.ACTLowerCut + xrange * 0, 'r-', label = 'pi/noise separation', linewidth = 2)
            # ax.plot(xrange, muonElcut, 'k--', label = 'mu/el separation', linewidth = 2)

            ax.legend()

            plt.savefig("../%s/SelectionACTswind2_Run%i.png"%(self.saving_folder_path_png, self.runNumber))
            plt.savefig("../%s/SelectionsACTswind2_Run%i.pdf"%(self.saving_folder_path_pdf, self.runNumber))



    def plotSelectionTOFLG(self):
        if self.isLowMomentum:
            xmin = conv * self.distanceTOF1toTOF0/c - 3
            if self.deuteriumTOFmax !=None:
                xmax = self.deuteriumTOFmax + 4
            elif self.protonsTOFMax !=None:
                xmax = self.protonsTOFMax + 4
            else:
                xmax = 30
            ymin, ymax = 0, 25
            fig, ax = self.plot2DHistFromBranches(0, "matchedHit0_TOF",  self.channelNames.index("PbGlass"), "matchedHit0_WindowIntPE", "(PE)", "(a.u.)", "Selection TOF-Lead Glass", True, [200, 300], [[xmin, xmax], [ymin, ymax]], False)
            
            xrange = np.linspace(xmin, self.protonsTOFCut, 100)


            ax.plot(xrange, self.weirdElectronLGcut + xrange * 0, 'r--', label = 'weird electron separation')

            if self.protonsTOFCut!= None:
                ax.plot([self.protonsTOFCut, self.protonsTOFCut], [ymin, ymax], 'k--', label = 'Proton TOF Cut')
                ax.plot([self.protonsTOFMax, self.protonsTOFMax], [ymin, ymax], 'k-', label = 'Proton TOF Max')
            if self.deuteriumTOFcut!= None:
                ax.plot([self.deuteriumTOFcut, self.deuteriumTOFcut], [ymin, ymax], 'b--', label = 'Deuterium TOF Cut')
                ax.plot([self.deuteriumTOFmax, self.deuteriumTOFmax], [ymin, ymax], 'b-', label = 'Deuterium TOF Max')

            ax.legend()

            plt.savefig("../%s/SelectionPbGlassTOFnew_Run%i.png"%(self.saving_folder_path_png, self.runNumber))
            plt.savefig("../%s/SelectionPbGlassTOFnew_Run%i.pdf"%(self.saving_folder_path_pdf, self.runNumber))



    def plotAllHist1DfromData(self, array_columns, plot_saving, normalise = False, MinBound = None, MaxBound = None, additionalLabel = None, yscale = None, nMaxColumns = 4, nbBins = 100):
        targetDetectors = range(len(self.arrayData))
        self.plotHist1DfromData(array_columns, targetDetectors, plot_saving, normalise, MinBound, MaxBound, additionalLabel, yscale, nMaxColumns, nbBins)
    
    def plotSomeDetectorHist1DfromData(self, array_columns, targetDetectors, plot_saving,  normalise = False, MinBound = None, MaxBound = None, additionalLabel = None, yscale = None, nMaxColumns = 4, nbBins = 100, statsBin = False):
        #if we only want to plot a few detectors
        if len(targetDetectors)<=4:
            nMaxColumns = len(targetDetectors)
        self.plotHist1DfromData(array_columns, targetDetectors, plot_saving, normalise, MinBound, MaxBound, additionalLabel, yscale, nMaxColumns, nbBins, statsBin)

    def plot1DHist(self, data1D, binWidth = 1, xlabel = 'x', ylabel = 'y', legend = None, title = None, ax = None, fig = None, ylogscale = False, lims = None, save = True, normalise = False):

        if len(data1D) == 0:
            return 0
        
        else:
            if lims != None:
                maximum = lims[1]
                minimum = lims[0]
            else:
                maximum = max(data1D)
                minimum = min(data1D)
        
            bins = int((maximum-minimum)/binWidth)
            if bins == 0:
                bins = 10
            if ax == None or fig == None:
                fig, ax = plt.subplots(1, 1, figsize = (16, 9))
            if legend != None:
                ax.hist(data1D, bins = bins, label = '%s\n%i events'%(legend, len(data1D)), histtype= 'step', density= normalise)
                ax.legend(fontsize = 18)
            else:
                ax.hist(data1D, bins = bins, histtype= 'step', label = '%i events'%(len(data1D)), density= normalise)
                ax.legend(fontsize = 18)

            # ax.grid()
            ax.set_xlabel("%s"%xlabel, fontsize = 18)
            if normalise:
                ax.set_ylabel("%s Fraction of total/%.2f "%(ylabel, binWidth), fontsize = 18)
            
            else:
                ax.set_ylabel("%s/%.2f"%(ylabel, binWidth), fontsize = 18)
            ax.tick_params(axis='both', which='major', labelsize=15)
            if title != None:
                fig.suptitle("%s Run %i - %.0f MeV/c"%(title, self.runNumber, self.runMomentum), fontsize = 20, weight = 'bold')
            else:
                fig.suptitle("Run %i - %.0f MeV/c"%(self.runNumber, self.runMomentum), fontsize = 20, weight = 'bold')

            if ylogscale:
                ax.set_yscale('log')

            if save:
                plt.savefig("../%s/Hist1d_%s_Run%i.pdf"%(self.saving_folder_path_pdf, title, self.runNumber))
                plt.savefig("../%s/Hist1d_%s_Run%i.png"%(self.saving_folder_path_png, title, self.runNumber))

    def plot2DHist(self, datax, datay, binWidth = [1, 1], xlabel = 'x', xunits = '', ylabel = 'y', yunits = '', ax = None, fig = None, zlogscale = False, additionalLabel = None, xRange = None):
        binsX = int((max(datax)-min(datax))/binWidth[0])
        binsY = int((max(datay)-min(datay))/binWidth[1])

        if ax == None or fig == None:
            fig, ax = plt.subplots(1, 1, figsize = (16, 9))

        if zlogscale:
            hist = ax.hist2d(datax, datay, bins = [binsX, binsY], norm = 'log', cmap = "viridis")
        else:
            hist = ax.hist2d(datax, datay, bins = [binsX, binsY], cmap = "viridis")

        clb = fig.colorbar(hist[3], ax=ax)
        clb.ax.set_title(label = 'Occurences/%.2f %s %.2f %s'%(binWidth[0], xunits, binWidth[1], yunits), fontsize=18)
        # ax.legend()
        ax.grid()
        # ax.set_xlim(range[0])
        # ax.set_ylim(range[1])
        ax.set_xlabel("%s %s"%(xlabel, xunits), fontsize=18)
        ax.set_ylabel("%s %s"%(ylabel, yunits), fontsize=18)
        if xRange!=None:
            ax.set_xlim(xRange)

        if additionalLabel != None:
            fig.suptitle('WCTE Beamtest - Run %i, p = %i MeV/c n = %s\n%s'%(self.runNumber, self.runMomentum, self.runRefractiveIndex, additionalLabel), fontsize=18, weight ='bold')
            plt.savefig("../%s/Hist2D_%s_%s_%s_Run%i.png"%(self.saving_folder_path_png, additionalLabel, xlabel, ylabel, self.runNumber))
            plt.savefig("../%s/Hist2D_%s_%s_%s_Run%i.pdf"%( self.saving_folder_path_pdf, additionalLabel, xlabel, ylabel, self.runNumber))
        else:
            fig.suptitle('WCTE Beamtest - Run %i, p = %i MeV/c n = %s'%(self.runNumber, self.runMomentum, self.runRefractiveIndex), fontsize=18, weight ='bold')
            plt.savefig("../%s/Hist2D_%s_%s_Run%i.png"%(self.saving_folder_path_png, xlabel, ylabel, self.runNumber))
            plt.savefig("../%s/Hist2D_%s_%s_Run%i.pdf"%(self.saving_folder_path_pdf, xlabel, ylabel, additionalLabel, self.runNumber))

        
        






    def plot2DScatterFromBranches(self, detector_x,  branch_name_x, detector_y, branch_name_y, detector_z = None, branch_name_z = None, units_x = "", units_y = "", units_z = "", additionalLabel = None, logz = False):
        fig, ax = plt.subplots(1, 1, figsize = (16, 9))
        x = self.arrayData[detector_x][branch_name_x]
        y = self.arrayData[detector_y][branch_name_y]

        range = [[max(x.mean()*0.6, min(x)*0.8), max(x)*1.04], [min(y)*0.8, max(y)*1.02]]
        if logz:
            hist = ax.scatter(x, y, c= self.arrayData[detector_z][branch_name_z], s = 3, norm = 'log', cmap = "viridis")
        else:
            hist = ax.scatter(x, y, c= self.arrayData[detector_z][branch_name_z],s = 3,  cmap = "viridis")

        fig.colorbar(hist, ax=ax, label = '%s %s %s'%(self.channelNames[detector_z],branch_name_z, units_z))
        ax.legend()
        ax.grid()
        # ax.set_xlim(range[0])
        # ax.set_ylim(range[1])
        ax.set_xlabel("%s %s %s"%(self.channelNames[detector_x], branch_name_x, units_x), fontsize=18)
        ax.set_ylabel("%s %s %s"%(self.channelNames[detector_y], branch_name_y, units_y), fontsize=18)
        fig.suptitle('WCTE Beamtest - Run %i, p = %i MeV/c n = %s\n%s'%(self.runNumber, self.runMomentum, self.runRefractiveIndex, additionalLabel), fontsize=18, weight ='bold')
        plt.savefig("../%s/Scatter_%s_%s_Run%i.png"%(self.saving_folder_path_png, self.channelNames[detector_z],branch_name_z, self.runNumber))
        plt.savefig("../%s/Scatter_%s_%s_Run%i.pdf"%(self.saving_folder_path_pdf, self.channelNames[detector_z], branch_name_z, self.runNumber))

    def plot2DHistFromBranches(self, detector_x,  branch_name_x, detector_y, branch_name_y, units_x = "", units_y = "", additionalLabel = None, logz = False, bins = [100, 100], range = None, save = True):
        fig, ax = plt.subplots(1, 1, figsize = (16, 9))
        x = self.arrayData[detector_x][branch_name_x]
        y = self.arrayData[detector_y][branch_name_y]

        if range == None:
            range = [[max(x.mean()*0.6, min(x)*0.8), max(x)*1.04], [min(y)*0.8, max(y)*1.02]]
        
        if logz:
            hist = ax.hist2d(x, y, bins = bins, norm = 'log', range = range, cmap = "viridis")
        else:
            hist = ax.hist2d(x, y, bins = bins, range = range, cmap = "viridis")

        clb = fig.colorbar(hist[3], ax=ax)
        clb.ax.set_title(label = 'Occurences/%.2f %s %.2f %s'%((range[0][1]-range[0][0])/bins[0], units_x, (range[1][1]-range[1][0])/bins[1], units_y), fontsize=18)
        # ax.legend()
        ax.grid()
        ax.set_xlim(range[0])
        ax.set_ylim(range[1])
        ax.set_xlabel("%s %s %s"%(self.channelNames[detector_x], branch_name_x, units_x), fontsize=18)
        ax.set_ylabel("%s %s %s"%(self.channelNames[detector_y], branch_name_y, units_y), fontsize=18)
        fig.suptitle('WCTE Beamtest - Run %i, p = %i MeV/c n = %s\n%s'%(self.runNumber, self.runMomentum, self.runRefractiveIndex, additionalLabel), fontsize=18, weight ='bold')

        if save:
            plt.savefig("../%s/Hist2d_%s%s_%s%s_Run%i.png"%( self.saving_folder_path_png, self.channelNames[detector_x],branch_name_x, self.channelNames[detector_y],branch_name_y, self.runNumber))
            plt.savefig("../%s/Hist2d_%s%s_%s%s_Run%i.pdf"%(self.saving_folder_path_pdf, self.channelNames[detector_x],branch_name_x, self.channelNames[detector_y],branch_name_y, self.runNumber))

        else:
            return fig, ax


    def getAcceptancenCoincidenceCut(self):
        return sum(self.nCoincidenceSelectionPassed)/len(self.nCoincidenceSelectionPassed)
    
    def getArrayData(self):
        return self.arrayData

    def nCoincidenceSelection(self):
        if self.openedFile is None:
            self.openDataFile(self)

        #only if we want the nCoincidenceSelection
        if self.nCoincidenceSelectionBool and "SignalTimeMatchedTOF1" in self.arrayData[0].columns:
            print(f"Performing nCoincidenceSelection with n = {self.nCoincidenceSelectionValue} for run {self.runNumber}...")
            #the branches SignalTimeMatchedTOF1/0 have the format of the coincidence, we can just have a
            #read over them in one detector to have the general selection
            self.nCoincidenceSelectionPassed = self.arrayData[0]["SignalTimeMatchedTOF1"].map(len)==self.nCoincidenceSelectionValue
            self.applyCut(self.nCoincidenceSelectionPassed)
        
        elif self.nCoincidenceSelectionBool:
            print("\nCannot perform a selection on the number of coincidence found: no coincidence was processed for this file, please make sure that the branch SignalTimeMatchedTOF1 (and0) exists in the dataframe, might need to change the config_(no)Hodoscope.json...\n")
            #this will always be true, but it is usefulme sure keep the same output
            # self.nCoincidenceSelectionPassed = self.arrayData[0]["DigitimingOffset"]!= -9998
            # self.applyCut(self.nCoincidenceSelectionPassed)

        else:
             print(f"In the config file, checking the coincidence is set to {self.nCoincidenceSelectionBool}, we are therefore not processing the change", end="", flush=True)
            #  self.nCoincidenceSelectionPassed = self.arrayData[0]["DigitimingOffset"]!= -9998

    def fitMuonsAndElectronLGPeaks(self, bins_values = 100, savefigs = True):
        """FIt and plot a Guassian distribution to the energy deposited in the lead glass for electrons and  muons - LM only"""
        leadGlassID = self.channelNames.index("PbGlass")
        if self.isLowMomentum:
            particle_list = ["electron", "muon"]
            if self.electronArray == None:
                self.makeAllParticleSelection()
            population_list = [self.electronArray[leadGlassID], self.muonArray[leadGlassID]]
            all_params = []

            if "matchedHit0_Window2IntPE" in self.getBranchList(leadGlassID):
                branches = ["MaxVoltage", "matchedHit0_WindowIntPE", "matchedHit0_Window2IntPE"]
            else:
                branches = ["MaxVoltage", "matchedHit0_WindowIntPE"]

            

            for p, population in enumerate(population_list):
                for branch in branches:
                    plt.figure(figsize = [16, 9])
                    electron_leadGlass = population[branch]
                    particle = particle_list[p]
                    counts, bins, _ = plt.hist(electron_leadGlass, bins = bins_values, alpha = 0.75, label = "%s-like: %i events"%(particle, len(electron_leadGlass)))
                    params, covariance = fitGaussian(counts, bins)
                    plt.plot(np.linspace(bins[0], bins[-1], 100), gaussian(np.linspace(bins[0], bins[-1], 100), *params), 'k--', label = 'Mean = %.3f V std = %.3f V'%(params[1], params[2]))
                    plt.grid()
                    plt.legend(fontsize = 19)
                    plt.xlabel(branch, fontsize = 18)
                    plt.ylabel("Number of events", fontsize = 18)

                    plt.title('WCTE Beamtest - Run %i, p = %i MeV/c n = %s'%(self.runNumber, self.runMomentum, self.runRefractiveIndex), fontsize=18, weight ='bold')

                    plt.tick_params(axis='both', which='major', labelsize=15)

                    if savefigs:
                        plt.savefig("../%s/%s_fitted_Run%i.pdf"%(self.saving_folder_path_pdf, "%s_%s"%(particle, branch), self.runNumber))

                        plt.savefig("../%s/%s_fitted_Run%i.png"%(self.saving_folder_path_png, "%s_%s"%(particle, branch), self.runNumber))
                    if branch == "matchedHit0_WindowIntPE":
                        all_params.append(params)
            
            return all_params


        for i in range(20):
            plt.close()

    def fitMuonsAndPionsACTPeaks(self, bins_values = 100, savefigs = True):
        """FIt and plot a Guassian distribution to the energy deposited in the lead glass for electrons and  muons - LM only"""
        leadGlassID = self.channelNames.index("ACT2L")
        if self.isLowMomentum:
            particle_list = ["pion", "muon"]
            if self.pionArray == None:
                self.makeAllParticleSelection()

            population_list = [self.pionArray[leadGlassID], self.muonArray[leadGlassID]]
            all_params = []

            if "sumDownstreamACTsWindow2" in self.getBranchList(leadGlassID):
                branches = ["sumDownstreamACTs", "sumDownstreamACTsWindow2"]
            else:
                branches = ["sumDownstreamACTs"]

            for p, population in enumerate(population_list):
                for branch in branches:
                    plt.figure(figsize = [16, 9])
                    electron_leadGlass = population[branch]
                    particle = particle_list[p]
                    counts, bins, _ = plt.hist(electron_leadGlass, bins = bins_values, alpha = 0.75, label = "%s-like: %i events"%(particle, len(electron_leadGlass)))
                    params, covariance = fitGaussian(counts, bins)
                    plt.plot(np.linspace(bins[0], bins[-1], 100), gaussian(np.linspace(bins[0], bins[-1], 100), *params), 'k--', label = 'Mean = %.3f PE std = %.3f PE'%(params[1], params[2]))
                    plt.grid()
                    plt.legend(fontsize = 19)
                    plt.xlabel(branch, fontsize = 18)
                    plt.ylabel("Number of events", fontsize = 18)

                    plt.title('WCTE Beamtest - Run %i, p = %i MeV/c n = %s'%(self.runNumber, self.runMomentum, self.runRefractiveIndex), fontsize=18, weight ='bold')

                    plt.tick_params(axis='both', which='major', labelsize=15)

                    if savefigs:
                        plt.savefig("../%s/%s_fitted_Run%i.pdf"%(self.saving_folder_path_pdf, "%s_%s"%(particle, branch), self.runNumber))

                        plt.savefig("../%s/%s_fitted_Run%i.png"%(self.saving_folder_path_png, "%s_%s"%(particle, branch), self.runNumber))
                    if branch == "sumDownstreamACTs":
                        all_params.append(params)
            
            return all_params

        


    def TStotalChargeSelection(self):
        """"Apply a cut on the minimum energy deposited in the Trigger scintillator (sum of all of the windowIntPE in TOFxy PMTs) to get rid of the poor coincidence matches to improve the TOF resolution"""
        if self.openedFile is None:
            self.openDataFile(self)
        
        if self.TStotalChargeSelectionBool:
            if "sumTS" not in self.getBranchList(0):
                self.makeSumTS()

        #With the 2+2 coincidence we do not need the selection based on small TS window, see TN
            # depositsEnoughEnergy = self.getSelectionBasedOnCondition(0, "sumTS", ">=", self.TStotalChargeSelectionValue)
            # isFast = self.getSelectionBasedOnCondition(0, "matchedHit0_TOF", ">=", self.protonsTOFCut)

            # self.TStotalChargeSelectionPassed =  depositsEnoughEnergy
            # #apply that cut to the main dataframe with all of the data
            # self.applyCut(self.TStotalChargeSelectionPassed)

        if self.thereIsSecondWindow:
            if "sumTSwindow2" not in self.getBranchList(0):
                self.makeSumTSwindow2()

            if self.TSwindow2totalChargeSelectionValue == None:
                #if we do not have a selection cut, do not apply it
                depositsNotTooMuchEnergy = True
                
            else:
                depositsNotTooMuchEnergy = self.getSelectionBasedOnCondition(0, "sumTSwindow2", "<=", self.TSwindow2totalChargeSelectionValue)
            
            isFast = self.getSelectionBasedOnCondition(0, "matchedHit0_TOF", ">=", self.protonsTOFCut)
            
            self.TSwindow2totalChargeSelectionPassed = depositsNotTooMuchEnergy | isFast

            self.applyCut(self.TSwindow2totalChargeSelectionPassed)


    def applyCut(self, cut_boolean):
        print("... this cut keeps %i events (%.2f percent), relative to df before this cut\n"%(sum(cut_boolean), sum(cut_boolean)/len(cut_boolean) * 100))
        for i in range(len(self.arrayData)):
            self.arrayData[i] = self.arrayData[i][cut_boolean]
        return self.arrayData
    
    def makeNewDataFrameFromSelection(self, initial_df_array, cut_boolean):
        print("... this cut keeps %i events (%.2f percent), relative to df before this cut\n"%(sum(cut_boolean), sum(cut_boolean)/len(cut_boolean) * 100))
        final_df_array = initial_df_array.copy()
        for detector in range(len(initial_df_array)):
            final_df_array[detector] = initial_df_array[detector][cut_boolean]
        return final_df_array


    def getBranchList(self, detectorID, particle = None):
        "Default we get the main datafram but then we can have others"
        if particle == None:
            return self.arrayData[detectorID].columns
        if particle == "proton":
            if self.protonArray == None:
                raise Exception("proton branch not yet defined, run makeAllParticleSelection or makeProtonSelection first")
            return self.protonArray[detectorID].columns
        if particle == "electron":
            if self.electronArray == None:
                raise Exception("electron branch not yet defined, run makeAllParticleSelection or makeElectronSelection first")
            return self.electronArray[detectorID].columns
        if particle == "muon":
            if self.muonArray == None:
                raise Exception("muon branch not yet defined, run makeAllParticleSelection or makeMuonSelection first")
            return self.muonArray[detectorID].columns
        if particle == "pion":
            if self.pionArray == None:
                raise Exception("pion branch not yet defined, run makeAllParticleSelection or makePionSelection first")
            return self.pionArray[detectorID].columns
        if particle == "deuterium":
            if self.deuteriumArray == None:
                raise Exception("deuterium branch not yet defined, run makeAllParticleSelection or makeDeuteriumSelection first")
            return self.deuteriumArray[detectorID].columns
        
    
    def cutBasedOnCondition(self, detectorID, branch_name, operation, value):
        """directly applies the cut on the main datafram, a bit dangerous, not recommended to use"""
        print(f"Performing condition based selection, keeping {self.channelNames[detectorID]} {branch_name} {operation} {value}...")
        if operation == ">=":
            passedSelection = self.arrayData[detectorID][branch_name] >= value
        if operation == ">":
            passedSelection = self.arrayData[detectorID][branch_name] > value
        if operation == "<":
            passedSelection = self.arrayData[detectorID][branch_name] < value
        if operation == "==":
            passedSelection = self.arrayData[detectorID][branch_name] == value
        self.applyCut(passedSelection)

    def getSelectionBasedOnCondition(self, detectorID, branch_name, operation, value, initial_df=None):
        "Get for a given array the array of bools being true if the event passes selection, false otherwise"
        if initial_df == None:
            initial_df = self.arrayData

        print(f"Performing condition based selection, keeping {self.channelNames[detectorID]} {branch_name} {operation} {value}...")
        if operation == ">=":
            passedSelection = initial_df[detectorID][branch_name] >= value
        if operation == "<=":
            passedSelection = initial_df[detectorID][branch_name] <= value
        if operation == ">":
            passedSelection = initial_df[detectorID][branch_name] > value
        if operation == "<":
            passedSelection = initial_df[detectorID][branch_name] < value
        if operation == "==":
            passedSelection = initial_df[detectorID][branch_name] == value
        return passedSelection

    def makeProtonSelection(self, timingCut = None, maxTimingCut = None):
        if timingCut == None:
            #use the default timing cut from the config file
            timingCut = self.protonsTOFCut
            
        if  maxTimingCut == None:
            maxTimingCut = self.protonsTOFMax 
        print(f"Selecting as protons all the events that have TOF larger than {timingCut} and smaller than {maxTimingCut}")
        if self.protonArray != None:
            print("This is overwriting the existing proton selection")
        isSlow = self.getSelectionBasedOnCondition(0, "matchedHit0_TOF", '>=', timingCut)
        isNotDeuterium = self.getSelectionBasedOnCondition(0, "matchedHit0_TOF", '<=', maxTimingCut)
        self.isProton = isSlow & isNotDeuterium

        # if self.isLowMomentum:
        #     isNotElectron = self.getSelectionBasedOnCondition(0, "sumDownstreamACTs", "<=", self.horizontal_el)
        #     self.isProton = self.isProton & isNotElectron
        self.protonArray = self.makeNewDataFrameFromSelection(self.arrayData, self.isProton)

    def makeDeuteriumSelection(self,  timingCut = None, maxTimingCut = None):
        if  maxTimingCut == None:
            maxTimingCut = self.deuteriumTOFmax
        if  timingCut == None:
            timingCut = self.deuteriumTOFcut
        print(f"Selecting as deuterium all the events that have TOF larger than {maxTimingCut}")
        isFasterThanProtons = self.getSelectionBasedOnCondition(0, "matchedHit0_TOF", '>', timingCut)
        isNotTooFast = self.getSelectionBasedOnCondition(0, "matchedHit0_TOF", '<', maxTimingCut)

        self.isDeuterium = isFasterThanProtons & isNotTooFast

        
        # if self.isLowMomentum:
        #     #deuterium events should not deposit a lot of light in 
        #     #the downstream ACT, these could be electrons with coincidence issues. 
        #     isNotElectron = self.getSelectionBasedOnCondition(0, "sumDownstreamACTs", "<=", self.horizontal_el)
        #     self.isDeuterium = self.isDeuterium & isNotElectron

        self.deuteriumArray = self.makeNewDataFrameFromSelection(self.arrayData, self.isDeuterium)

    def makePionSelection(self):
        if "sumDownstreamACTs" not in self.getBranchList(0):
                self.makeSumDownstreamACTs()

        print(f"Selecting as pions all the events that have sumDownstreamACTs larger than {self.ACTLowerCut} and smaller than {self.piMuBorderACT}")
        #I am not sure whether we should keep that, we are actually expecting to have 0 charge there, maybe we are loosing quite a bit of pions, but actually it was less than percentage
        isAboveACTLower = self.getSelectionBasedOnCondition(0, "sumDownstreamACTs", ">=", self.ACTLowerCut)

        isBelowPiMuCutLine = self.getSelectionBasedOnCondition(0, "sumDownstreamACTs", "<", self.piMuBorderACT)

        isNotWeirdElectron = self.getSelectionBasedOnCondition(self.channelNames.index("PbGlass"), "matchedHit0_WindowIntPE", "<", self.weirdElectronLGcut)
    
        isSlow = self.getSelectionBasedOnCondition(0, "matchedHit0_TOF", "<", self.protonsTOFCut)

        ACTSelection = isAboveACTLower & isBelowPiMuCutLine

        isPotentialPion = ACTSelection & isSlow

        self.isPion  = isPotentialPion & isNotWeirdElectron
        # self.nPions = sum(self.isPion)
        self.pionArray = self.makeNewDataFrameFromSelection(self.arrayData, self.isPion)

        self.isPionLikeWeirdElectron = isPotentialPion & np.logical_not(isNotWeirdElectron)

        self.pionLikeWeirdElectronArray = self.makeNewDataFrameFromSelection(self.arrayData, self.isPionLikeWeirdElectron)


    def makeMuonSelection(self):
        if "sumACT1" not in self.getBranchList(0):
                    self.makeSumACT1()
        if "sumDownstreamACTs" not in self.getBranchList(0):
                self.makeSumDownstreamACTs()

        isNotWeirdElectron = self.getSelectionBasedOnCondition(self.channelNames.index("PbGlass"), "matchedHit0_WindowIntPE", "<", self.weirdElectronLGcut)

        isBelowMuElCut = self.getSelectionBasedOnCondition(0, "sumDownstreamACTs", "<=", self.getDataFrameDetector(0)["sumACT1"] * self.ACTlinearA + self.ACTlinearB)

        isBelowHorizontalElCut = self.getSelectionBasedOnCondition(0, "sumDownstreamACTs", "<=", self.horizontal_el)

        isAbovePiMuCutLine = self.getSelectionBasedOnCondition(0, "sumDownstreamACTs", ">=", self.piMuBorderACT)

        isSlow = self.getSelectionBasedOnCondition(0, "matchedHit0_TOF", "<", self.protonsTOFCut)

        isLeftOfPoint = self.getSelectionBasedOnCondition(0, "sumACT1", "<", (self.horizontal_el-self.ACTlinearB)/(self.ACTlinearA))

        print("sum isLeftOf: ", sum(isLeftOfPoint))
        print("sum isBelowMuElCut: ", sum(isBelowMuElCut))
        print("sum isLeftOf & isBelowMuElCut: ", sum(isLeftOfPoint & isBelowMuElCut))

        isRightOfPoint = self.getSelectionBasedOnCondition(0, "sumACT1", ">", (self.horizontal_el-self.ACTlinearB)/(self.ACTlinearA))

        


        isBelowMuElCut = isBelowMuElCut #& isLeftOfPoint

        isBelowHorizontalElCut = isBelowHorizontalElCut #& isRightOfPoint

        print("sum isRightOf: ", sum(isRightOfPoint))
        print("sum isBelowHorizontalElCut: ", sum(isBelowHorizontalElCut))
        print("sum isBelowHorizontalElCut & isRightOf: ", sum(isBelowHorizontalElCut & isRightOfPoint))

        isNotElectron = isBelowMuElCut | isBelowHorizontalElCut

        print("isNotElectron: ", sum(isNotElectron))
        

        isMuonOrElectron = isSlow & isAbovePiMuCutLine

        isPotentialMuon = isMuonOrElectron & isNotElectron

        self.isMuon = isPotentialMuon & isNotWeirdElectron

        self.muonArray = self.makeNewDataFrameFromSelection(self.arrayData, self.isMuon)

        self.isMuonLikeWeirdElectron = isPotentialMuon & np.logical_not(isNotWeirdElectron)

        self.muonLikeWeirdElectronArray = self.makeNewDataFrameFromSelection(self.arrayData, self.isMuonLikeWeirdElectron)


    def makeElectronSelection(self):
        if self.isLowMomentum:
            if "sumACT1" not in self.getBranchList(0):
                    self.makeSumACT1()
            if "sumDownstreamACTs" not in self.getBranchList(0):
                    self.makeSumDownstreamACTs()

            isAboveMuElCut = self.getSelectionBasedOnCondition(0, "sumDownstreamACTs", ">", self.getDataFrameDetector(0)["sumACT1"] * self.ACTlinearA + self.ACTlinearB)

            isAboveHorizontalElCut = self.getSelectionBasedOnCondition(0, "sumDownstreamACTs", ">", self.horizontal_el)

            #need to know if we are on the right or lefthandside of the cut line
            isLeftOfPoint = self.getSelectionBasedOnCondition(0, "sumACT1", "<", (self.horizontal_el-self.ACTlinearB)/(self.ACTlinearA))

            isRightOfPoint = self.getSelectionBasedOnCondition(0, "sumACT1", ">", (self.horizontal_el-self.ACTlinearB)/(self.ACTlinearA))

            isSlow = self.getSelectionBasedOnCondition(0, "matchedHit0_TOF", "<", self.protonsTOFCut)

            self.isElectron = isAboveMuElCut & isLeftOfPoint
            
            self.isAboveLine = isAboveHorizontalElCut & isRightOfPoint

            self.isElectron = self.isElectron | self.isAboveLine

            self.isElectron = self.isElectron & isSlow

            self.electronArray = self.makeNewDataFrameFromSelection(self.arrayData, self.isElectron)

        else:
            self.isElectron = self.getSelectionBasedOnCondition(0, "matchedHit0_TOF", "<", self.protonsTOFCut)
            self.electronArray = self.makeNewDataFrameFromSelection(self.arrayData, self.isElectron)

    def getNumberEventsPassingSelection(self, particle = None):
        if particle == None:
            return len(self.getDataFrameDetector(0)["spillNumber"])
        else:
            if self.getDataFrameAllDetectors(particle)!=None:
                return len(self.getDataFrameAllDetectors(particle)[0]["spillNumber"])
            else:
                return None
            
    def plotTOFbounds(self):
        '''Simple function to plot the TOF bounds used to select the proton and deuterium like events'''
        p_range = np.arange(200, 1200, 10)
        upper = []
        lower = []
        expected_proton = []
        upperD = []
        lowerD = []
        expected_deuterium = []
        for p in p_range:
            TOFprotonLower,TOFprotonUpper =  self.getProtonTOFSelectionBounds(p)
            upper.append(TOFprotonUpper)
            lower.append(TOFprotonLower)
            expected_proton.append(self.momentumToTOF(p, "proton"))
            
            TOFdeuteriumLower,TOFdeuteriumUpper = self.getDeuteriumTOFSelectionBounds(p)
            upperD.append(TOFdeuteriumUpper)
            lowerD.append(TOFdeuteriumLower)
            expected_deuterium.append(self.momentumToTOF(p, "deuterium"))
        fig, ax = plt.subplots(1, 1, figsize = (16, 9))
        ax.fill_between(p_range, lower, upper, color = 'blue', alpha = 0.3, label = 'Proton TOF selection Bounds')
        ax.plot(p_range, expected_proton, 'b--', label = 'Nominal proton TOF')
        # ax.fill_between(p_range, lowerD, upperD, color = 'red', alpha = 0.3, label = 'Deuterium TOF selection Bounds')
        # ax.plot(p_range, expected_deuterium, 'r--', label = 'Nominal deuterium TOF')
        ax.set_xlabel("Nominal beam momentum (MeV/c)",fontsize = 18)
        ax.set_ylabel("Time of flight (ns)",fontsize = 18)
        ax.tick_params(axis='both', which='major', labelsize=15)
        
        ax.grid()
        ax.legend(fontsize = 18)
        if self.isLowMomentum:
            ax.fill_between(p_range, lowerD, upperD, color = 'red', alpha = 0.3, label = 'Deuterium TOF selection Bounds')
            ax.plot(p_range, expected_deuterium, 'r--', label = 'Nominal deuterium TOF')
            ax.set_title("Time of flight selection for\n protons and deuterium - Low momentum configuration",fontsize = 20, weight = 'bold')
            fig.savefig("../%s/SelectionTOFBoundsLM.png"%self.saving_folder_path_png)
            fig.savefig("../%s/SelectionTOFBoundsLM.pdf"%self.saving_folder_path_pdf)
        else:
            ax.set_title("Time of flight selection for\n protons and deuterium - Tagged photon configuration",fontsize = 20, weight = 'bold')
            fig.savefig("../%s/SelectionTOFBoundsTG.png"%self.saving_folder_path_png)
            fig.savefig("../%s/SelectionTOFBoundsTG.pdf"%self.saving_folder_path_pdf)




    def getProbaParticleInBunch(self):
        """TODO: complete with the calculation, as described in the beam flux paper by Dean of the calculation of the probability of having a particle in a given bunch, based on the delay between particles arrival times"""
        return self.probaBunch
    
    def plotBeamSpot(self, particle=None):
        """TODO: write a function that plots for each particle type (or all particles when None) where those particles hit the TS based on the weighted sum of their windowIntPE signal in the TS, see Jiri's study"""


            

    def outputResults(self):
        """Output all of the relevant information into a csv file"""

        entriesNames = ["runNumber",
                        "runMomentum", 
                        "runRefractiveIndex",
                        "totalNumberSpills",  
                        "probabilityToHaveParticleInBunch", "totalNumberOfEvents", 
                        "numberOfEventsPassingBaseSelections", 
                        "numberOfEventsPassingElectronSelection", 
                        "numberOfEventsPassingMuonSelection", 
                        "numberOfEventsPassingPionSelection", 
                        "numberOfEventsPassingProtonSelection",
                        "numberOfEventsPassingDeuteriumSelection",
                        "meanTOFelectron",
                        "meanTOFmuon",
                        "meanTOFpion",
                        "meanTOFproton",
                        "meanTOFdeuterium",
                        "stdTOFelectron",
                        "stdTOFmuon",
                        "stdTOFpion",
                        "stdTOFproton",
                        "stdTOFdeuterium",
                        "meanMomentumMuon",
                        "meanMomentumPion",
                        "meanMomentumProton",
                        "meanMomentumDeuterium",
                        "meanMomentumStatErrMuon",
                        "meanMomentumStatErrPion",
                        "meanMomentumStatErrProton",
                        "meanMomentumStatErrDeuterium",
                        "numberOfTOFfittedElectron",
                        "numberOfTOFfittedMuon",
                        "numberOfTOFfittedPion",
                        "numberOfTOFfittedProton",
                        "numberOfTOFfittedDeuterium",
                        ]

        entries = {"runNumber": self.runNumber,
                   "runMomentum": self.runMomentum,
                   "runRefractiveIndex": self.runRefractiveIndex,
                   "totalNumberSpills": max(self.getDataFrameDetector(0)["spillNumber"]),
                   "probabilityToHaveParticleInBunch": self.getProbaParticleInBunch(),
                   "totalNumberOfEvents": self.totalNumberOfEvents,
                   #nCoincidence, TS charge cut, etc... for each perticle
                   "numberOfEventsPassingBaseSelections": self.getNumberEventsPassingSelection(),
                   "numberOfEventsPassingElectronSelection": self.getNumberEventsPassingSelection("electron"),
                   "numberOfEventsPassingMuonSelection": self.getNumberEventsPassingSelection("muon"),
                   "numberOfEventsPassingPionSelection": self.getNumberEventsPassingSelection("pion"),
                   "numberOfEventsPassingProtonSelection": self.getNumberEventsPassingSelection("proton"),
                   "numberOfEventsPassingDeuteriumSelection":self.getNumberEventsPassingSelection("deuterium"),
                   #TOF estimates
                   "meanTOFelectron": self.dictTOFMean["electron"],"meanTOFmuon": self.dictTOFMean["muon"],
                   "meanTOFpion": self.dictTOFMean["pion"],
                   "meanTOFproton": self.dictTOFMean["proton"],
                   "meanTOFdeuterium": self.dictTOFMean["deuterium"],
                   "stdTOFelectron": self.dictTOFStd["electron"],
                   "stdTOFmuon": self.dictTOFStd["muon"],
                   "stdTOFpion": self.dictTOFStd["pion"],
                   "stdTOFproton": self.dictTOFStd["proton"],
                   "stdTOFdeuterium": self.dictTOFStd["deuterium"],
                   #momentum estimates
                   "meanMomentumMuon": self.dictMomentumMean["muon"],
                   "meanMomentumPion": self.dictMomentumMean["pion"],
                   "meanMomentumProton": self.dictMomentumMean["proton"],
                   "meanMomentumDeuterium": self.dictMomentumMean["deuterium"],
                   "meanMomentumStatErrMuon": self.dictMomentumStatError["muon"],
                   "meanMomentumStatErrPion": self.dictMomentumStatError["pion"],
                   "meanMomentumStatErrProton": self.dictMomentumStatError["proton"],
                   "meanMomentumStatErrDeuterium": self.dictMomentumStatError["deuterium"],
                   "numberOfTOFfittedElectron": self.dictTOFfittedNparticles["electron"],
                   "numberOfTOFfittedMuon": self.dictTOFfittedNparticles["muon"],
                   "numberOfTOFfittedPion": self.dictTOFfittedNparticles["pion"],
                   "numberOfTOFfittedProton": self.dictTOFfittedNparticles["proton"],
                   "numberOfTOFfittedDeuterium": self.dictTOFfittedNparticles["deuterium"],

                   
        }


        
        if not(os.path.exists(self.outputFileName)):
            with open(self.outputFileName, "w") as f:
                writer = csv.DictWriter(f, fieldnames = entriesNames)
                writer.writeheader()
                writer.writerow(entries)
        else:
            with open(self.outputFileName, "a") as f:
                writer = csv.DictWriter(f, fieldnames = entriesNames)
                writer.writerow(entries)
            
            
        
        







        



