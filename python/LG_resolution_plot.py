#This is a simple plotting code to fit the sigmaE/E against E to verify the proportionality constant. 

import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
import pandas as pd
from scipy.optimize import curve_fit

def linear(x, A, B):
    return x * A + B

def modifiedRootn(x, A, B):
    """Here we assume that the number of photons produced is proportional to the momentum"""
    return  np.sqrt(abs(A) / (x**2) + B)

def fitFunction(x, y, function):
    # Fit the Gaussian function to the data points
    x = np.array(x)
    y = np.array(y)
    params, covariance = curve_fit(linear, x, y, p0=[1, 0])
    return params, covariance

def fitFunction2(x, y, function):
    # Fit the Gaussian function to the data points
    x = np.array(x)
    y = np.array(y)
    params, covariance = curve_fit(modifiedRootn, x, y, p0=[1, 0])
    return params, covariance


def plotOneBranchAgainstAnotherAndFit(df_base, branch_x, branch_x_err, branch_y, branch_y_err, x_axis_title, y_axis_title, title = None, label = "Data"):

    #remove flags
    df_base = df_base[df_base[branch_x]!=-9999]
    df_base = df_base[df_base[branch_y]!=-9999]

    df_plus = df_base[df_base["runMomentum"]>0]
    df_minus = df_base[df_base["runMomentum"]<0]



    charge = ["Positively charged", "Negatively charged"]
    colors = ["red", "blue"]
    colors_fit = ["black", "gray"]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [3, 1]})

    for i, df in enumerate([df_plus, df_minus]):   
        if len(df[branch_x])>1:
            ax1.errorbar(df[branch_x],df[branch_y], xerr = df[branch_x_err], yerr = df[branch_y_err], color=colors[i], fmt = 'x', label="%s, %s"%(label, charge[i]))

            params, covariance = fitFunction(df[branch_x], df[branch_y], linear)

            x = np.linspace(min(df[branch_x])*0.9, max(df[branch_x])*1.1, 100)
            ax1.plot(x, linear(x, params[0], params[1]), '--', color = colors_fit[i], label = '%s\nLinear Fit: %.2e x + %.2f'%(charge[i], params[0], params[1]))


            ax2.errorbar(df[branch_x], (df[branch_y] - linear(df[branch_x], params[0], params[1]))/df[branch_y], xerr = df[branch_x_err], yerr = df[branch_y_err]/df[branch_y], fmt =  "x",  color = colors[i])

            ax2.axhline(0, linestyle = "--", color = "black")

    ax1.legend()

    ax1.set_xlabel(x_axis_title, fontsize = 13)
    ax1.set_ylabel(y_axis_title, fontsize = 13)

    ax2.set_xlabel(x_axis_title, fontsize = 13)
    ax2.set_ylabel("data-fit/data", fontsize = 13)

    ax2.grid()
    ax1.grid()

    if title != None:
        fig.suptitle(title, fontsize=22, weight ='bold')





    savingpath = "/home/ac4317/Laptops/Year1/WCTE/BeamTestJuly2023/DataAnalysis/data/analysis-code/T9BeamTestAna/pdf_LGcalibration_results/%s_against_%s.pdf"%(branch_x, branch_y)

    fig.savefig(savingpath)
    # plt.show()

# def plotAllMomentum(df):
#     #here get all particles fit displayed, not difficult.
#     for particle in ["muon", "pion", "proton", "deuterium"]:





#Read the information directly from the csv file

LG_info_path = "/home/ac4317/Laptops/Year1/WCTE/BeamTestJuly2023/DataAnalysis/data/analysis-code/T9BeamTestAna/pdf_LGcalibration_results/LGCalibration_information.csv"

# Read the CSV file into a DataFrame
df = pd.read_csv(LG_info_path)

df["zeros"] = df["runMomentum"] * 0
#df["protonMomentumError"] = abs(df["protonMomentumError"])

print(df.columns, df)

print(df["electronMomentumAtLG"])

plotOneBranchAgainstAnotherAndFit(df, "electronMomentumAtLG", "electronMomentumErrorAtLG", "matchedHit0_WindowIntPE_mean", "matchedHit0_WindowIntPE_errmean", "Electron Momentum at LG (MeV/c)", "Electron charged in LG window [-16, 75]ns (a.u.)", "Lead-glass calibration window bounds: [-16, 75]ns")


plotOneBranchAgainstAnotherAndFit(df, "electronMomentumAtLG", "electronMomentumErrorAtLG", "matchedHit0_Window2IntPE_mean", "matchedHit0_Window2IntPE_errmean", "Electron Momentum at LG (MeV/c)", "Electron charge in LG window [-50, 190]ns (a.u.)", "Lead-glass calibration window bounds: [-50, 190]ns")

plotOneBranchAgainstAnotherAndFit(df, "runMomentum", "zeros", "pionMomentumMean", "pionMomentumError", "Set run momentum (MeV/c)", "Pion TOF-measured Momentum (MeV/c)", "Beam momentum measurement: Pions")

plotOneBranchAgainstAnotherAndFit(df, "runMomentum", "zeros", "muonMomentumMean", "muonMomentumError", "Set run momentum (MeV/c)", "Muon TOF-measured Momentum (MeV/c)", "Beam momentum measurement: Muons")

plotOneBranchAgainstAnotherAndFit(df, "runMomentum", "zeros", "protonMomentumMean", "protonMomentumError", "Set run momentum (MeV/c)", "Proton TOF-measured Momentum (MeV/c)", "Beam momentum measurement: Protons")

plotOneBranchAgainstAnotherAndFit(df, "runMomentum", "zeros", "deuteriumMomentumMean", "deuteriumMomentumError", "Set run momentum (MeV/c)", "Deuterium TOF-measured Momentum (MeV/c)", "Beam momentum measurement: Deuterium")

# plotAllMomentum(df)


raise end


#using dict is so much better 
##############################
run432_el = {"momentum": 460, 
            "E": 6.249,
            "sigmaE": 0.654,
            "E2":7.044,
            "sigmaE2":0.713,
            "n" : 94629,
            "TOFmomentum":430.15,
            "TOFmomentumError":4.517,
            "protonMomentum": 460.4,
            "protonMomentumError": 0.4}

run432_mu = {"momentum": 460, 
            "E": 3.305,
            "sigmaE": 0.374}
##############################
run412_el = {"momentum": 560, 
            "E": 7.907,
            "sigmaE": 0.828,
            "E2":8.908,
            "sigmaE2":0.895,
            "n" : 95452,
            "TOFmomentum":534.105,
            "TOFmomentumError": 5.4,
            "protonMomentum": 570.4,
            "protonMomentumError": 0.3}

run412_mu = {"momentum": 560, 
            "E": 3.474,
            "sigmaE": 0.383}
##############################
run438_el = {"momentum": 700, 
            "E": 10.558,
            "sigmaE": 1.107,
            "E2":11.847,
            "sigmaE2":1.198,
            "n": 74117,
            "TOFmomentum":666.15,
            "TOFmomentumError": 6.5,
            "protonMomentum": 710.3,
            "protonMomentumError": 0.2}

run438_mu = {"momentum": 700, 
            "E": 3.806,
            "sigmaE": 0.427}
##############################
run398_el = {"momentum": 900, 
            "E": 13.959,
            "sigmaE": 1.518, 
            "E2":15.613,
            "sigmaE2":1.638,
            "n":55931, 
            "TOFmomentum":858.55,
            "TOFmomentumError": 8.2,
            "protonMomentum": 914.0,
            "protonMomentumError": 0.3}

run398_mu = {"momentum": 900, 
            "E": 3.901,
            "sigmaE": 0.554}
##############################
run393_el = {"momentum": 1000, 
            "E": 15.890,
            "sigmaE": 1.763,
            "E2": 17.747,
            "sigmaE2": 1.913,
            "n": 75116,
            "TOFmomentum":947.65,
            "TOFmomentumError": 9.0,
            "protonMomentum": 1008.8,
            "protonMomentumError": 0.3}

#careful, muon fit at 1000 is very poor, sigmaE is overestimated
run393_mu = {"momentum": 1000, 
            "E": 3.994,
            "sigmaE": 0.670}

run_numbers = [432, 412, 438, 398, 393]
all_electron_dict = [run432_el, run412_el,  run438_el,  run398_el, run393_el]
all_muon_dict = [run432_mu, run412_mu,  run438_mu,  run398_mu, run393_mu]


plt.figure(figsize = [10, 6])
for i, dict in enumerate(all_electron_dict):
    E = dict["E"]
    sigmaE = dict["sigmaE"]
    plt.errorbar(E, (E/sigmaE)**2, yerr = sigmaE, fmt ='x', markersize = 10, label = "Run %i - p = %i MeV/c"%(run_numbers[i], dict["momentum"]))

plt.grid()
plt.xlabel("LG fitted mean E (a.u)", fontsize = 18)
plt.ylabel(r"LG fitted $(E/\sigma_E)^2$ (a.u)", fontsize = 18)
plt.title("LG electron WindowIntPE energy resolution", fontsize = 18)
plt.legend(fontsize = 15)
plt.tick_params(axis='both', which='major', labelsize=15)
# plt.show()

plt.savefig("../%s/ElectronLGenergyRelationCheck.pdf"%("pdf_2plus2Coincidence_nosumTScut"))
plt.savefig("../%s/ElectronLGenergyRelationCheck.png"%("png_2plus2Coincidence_nosumTScut"))


###########################################################
plt.figure(figsize = [10, 6])
for i, dict in enumerate(all_muon_dict):
    E = dict["E"]
    sigmaE = dict["sigmaE"]
    plt.errorbar(E, (E/sigmaE)**2, yerr = sigmaE, fmt ='x', markersize = 10, label = "Run %i - p = %i MeV/c"%(run_numbers[i], dict["momentum"]))

plt.grid()
plt.xlabel("LG fitted mean E (a.u)", fontsize = 18)
plt.ylabel(r"LG fitted $(E/\sigma_E)^2$ (a.u)", fontsize = 18)
plt.title("LG muon WindowIntPE energy resolution", fontsize = 18)
plt.legend(fontsize = 15)
plt.tick_params(axis='both', which='major', labelsize=15)
# plt.show()

plt.savefig("../%s/MuonLGenergyRelationCheck.pdf"%("pdf_2plus2Coincidence_nosumTScut"))
plt.savefig("../%s/MuonLGenergyRelationCheck.png"%("png_2plus2Coincidence_nosumTScut"))

########################################

########################################

array_x = []
array_y = []
plt.figure(figsize = [10, 6])
for i, dict in enumerate(all_electron_dict):
    E = dict["E"]
    sigmaE = dict["sigmaE"]
    mom = dict["momentum"]

    array_x.append(mom)
    array_y.append(sigmaE)
    
    
    plt.errorbar(mom, sigmaE, yerr = 0, fmt ='x', markersize = 10, label = "Run %i - p = %i MeV/c"%(run_numbers[i], dict["momentum"]))

print(array_x, array_y)
array_x = np.array(array_x)
array_y = np.array(array_y)
params, covariance = fitFunction(array_x, array_y, linear)
x = np.linspace(min(array_x)-10, max(array_x) + 10, 100)
plt.plot(x, linear(x, params[0], params[1]), 'k--', label = 'Linear Fit: %.2e x + %.2f'%(params[0], params[1]))


plt.grid()
plt.ylabel("LG fitted std E (a.u)", fontsize = 18)
plt.xlabel("Nominal beam momentum (MeV/c)", fontsize = 18)
plt.title("LG electron WindowIntPE std of energy against beam momentum", fontsize = 18)
plt.legend(fontsize = 15)
plt.tick_params(axis='both', which='major', labelsize=15)
# plt.show()

plt.savefig("../%s/ElectronLGSigmaMomentumRelationCheck.pdf"%("pdf_2plus2Coincidence_nosumTScut"))
plt.savefig("../%s/ElectronLGSIgmaMomentumRelationCheck.png"%("png_2plus2Coincidence_nosumTScut"))
#######################################################
plt.figure(figsize = [10, 6])
for i, dict in enumerate(all_electron_dict):
    E = dict["E"]
    sigmaE = dict["sigmaE"]
    mom = dict["momentum"]
    plt.errorbar(mom, (E/sigmaE)**2, yerr = 0, fmt ='x', markersize = 10, label = "Run %i - p = %i MeV/c"%(run_numbers[i], dict["momentum"]))

plt.grid()
plt.ylabel(r"LG fitted $(E/\sigma_E)^2$ (a.u)", fontsize = 18)
plt.xlabel("Nominal beam momentum (MeV/c)", fontsize = 18)
plt.title("LG electron WindowIntPE square of inverse energy resolution \n against beam momentum", fontsize = 18)
plt.legend(fontsize = 15)
plt.tick_params(axis='both', which='major', labelsize=15)
# plt.show()

plt.savefig("../%s/ElectronInverseResolutionLGMomentumRelationCheck.pdf"%("pdf_2plus2Coincidence_nosumTScut"))
plt.savefig("../%s/ElectronInverseResolutionLGMomentumRelationCheck.png"%("png_2plus2Coincidence_nosumTScut"))

########################################

array_x = []
array_y = []
fig, (ax0, ax1) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [3, 1]}, figsize = [15, 10])
for i, dict in enumerate(all_electron_dict):
    E = dict["E"]
    sigmaE = dict["sigmaE"]
    mom = dict["momentum"]

    array_x.append(mom)
    array_y.append(E)
    ax0.errorbar(mom, E, yerr = sigmaE, fmt ='x', markersize = 10, label = "Run %i - p = %i MeV/c"%(run_numbers[i], dict["momentum"]))

print(array_x, array_y)
array_x = np.array(array_x)
array_y = np.array(array_y)
params, covariance = fitFunction(array_x, array_y, linear)
x = np.linspace(min(array_x)-10, max(array_x) + 10, 100)
ax0.plot(x, linear(x, params[0], params[1]), 'k--', label = 'Linear Fit: %.2e x + %.2f'%(params[0], params[1]))
for i, dict in enumerate(all_electron_dict):
    E = dict["E"]
    sigmaE = dict["sigmaE"]
    mom = dict["momentum"]
    ax1.errorbar(mom, (linear(mom, params[0], params[1])-E)/E, yerr = sigmaE/E, fmt ='x', markersize = 10)

ax1.plot([min(array_x)-10, max(array_x)+10], [0, 0], "k--", label = r"Total abs(fit-E)/E: %.2e"%(sum((abs(linear(array_x, params[0], params[1])-array_y)/array_y))))



ax0.grid()
ax0.set_ylabel("LG fitted mean E (a.u)", fontsize = 18)
ax0.set_xlabel("Nominal beam momentum (MeV/c)", fontsize = 18)
fig.suptitle("LG electron WindowIntPE mean +/- std energy against beam momentum", fontsize = 20, weight = "bold")

#residuals
# ax1.grid()
ax1.set_ylabel("Fit fractional residuals", fontsize = 18)
ax1.set_xlabel("Nominal beam momentum (MeV/c)", fontsize = 18)
plt.grid()
ax1.legend()

ax0.legend(fontsize = 15)
plt.tick_params(axis='both', which='major', labelsize=15)
# plt.show()

fig.savefig("../%s/ElectronLGMomentumRelationCheck.pdf"%("pdf_2plus2Coincidence_nosumTScut"))
fig.savefig("../%s/ElectronLGMomentumRelationCheck.png"%("png_2plus2Coincidence_nosumTScut"))
#################################################
array_x = []
array_y = []
plt.figure(figsize = [10, 6])
for i, dict in enumerate(all_electron_dict):
    E = dict["E"]
    sigmaE = dict["sigmaE"]
    mom = dict["momentum"]
    plt.errorbar(E, sigmaE/E, yerr = 0, fmt ='x', markersize = 10, label = "Run %i - p = %i MeV/c"%(run_numbers[i], dict["momentum"]))
    array_x.append(E)
    array_y.append(sigmaE/E)

params, covariance = fitFunction2(array_x, array_y, modifiedRootn)

print(array_x)
print(params)

x = np.linspace(min(array_x), max(array_x), 100)

plt.plot(x, modifiedRootn(x, params[0], params[1]), 'k--', label = r'Function fit: $\sqrt{ %.2f / x + %.3f} $'%(params[0], params[1]))


plt.grid()
plt.ylabel(r"LG fitted $(\sigma_E/E)$ (a.u)", fontsize = 18)
plt.xlabel("Mean electron energy E", fontsize = 18)
plt.title("LG electron WindowIntPE fractional energy \n resolution against beam momentum", fontsize = 18)
plt.legend(fontsize = 15)
plt.tick_params(axis='both', which='major', labelsize=15)
# plt.show()

plt.savefig("../%s/ElectronesolutionLGMomentumRelationCheck.pdf"%("pdf_2plus2Coincidence_nosumTScut"))
plt.savefig("../%s/ElectronResolutionLGMomentumRelationCheck.png"%("png_2plus2Coincidence_nosumTScut"))


###################################
########################################

array_x = []
array_y = []
array_y2 = []
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728','#9467bd', '#8c564b', '#e377c2','#7f7f7f', '#bcbd22', '#17becf']

fig, (ax0, ax1) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [3, 1]}, figsize = [15, 10])
for i, dict in enumerate(all_electron_dict):
    E = dict["E"]
    sigmaE = dict["sigmaE"]
    E2 = dict["E2"]
    sigmaE2 = dict["sigmaE2"]
    mom = dict["TOFmomentum"]
    momError = dict["TOFmomentumError"]

    array_x.append(mom)
    array_y.append(E)
    array_y2.append(E2)
    if i == 0:
        ax0.errorbar(mom, E, xerr = momError, yerr = sigmaE, fmt ='x', markersize = 10, color = "k", label = "Integration window [-16, 75]")

        ax0.errorbar(mom, E2, xerr = momError, yerr = sigmaE2, fmt ='o', markersize = 10, color = "k", label = "Integration window [-50, 190]")
    
    ax0.errorbar(mom, E, xerr = momError, yerr = sigmaE, fmt ='+', markersize = 10, color = colors[i], label = "Run %i - nominal p = %i MeV/c"%(run_numbers[i], dict["momentum"]))

    ax0.errorbar(mom, E, xerr = momError, yerr = sigmaE, fmt ='x', markersize = 10, color = colors[i])

    ax0.errorbar(mom, E2, xerr = momError, yerr = sigmaE2, fmt ='o', markersize = 10, color = colors[i])

print(array_x, array_y)
array_x = np.array(array_x)
array_y = np.array(array_y)
params, covariance = fitFunction(array_x, array_y, linear)
x = np.linspace(min(array_x)-10, max(array_x) + 10, 100)
ax0.plot(x, linear(x, params[0], params[1]), 'k--', label = 'Linear Fit: %.2e x + %.2f'%(params[0], params[1]))


array_y2 = np.array(array_y2)

params2, covariance2 = fitFunction(array_x, array_y2, linear)
x = np.linspace(min(array_x)-10, max(array_x) + 10, 100)

ax0.plot(x, linear(x, params2[0], params2[1]), 'r--', label = 'Linear Fit: %.2e x + %.2f'%(params2[0], params2[1]))

for i, dict in enumerate(all_electron_dict):
    E = dict["E"]
    sigmaE = dict["sigmaE"]
    E2 = dict["E2"]
    sigmaE2 = dict["sigmaE2"]
    mom = dict["TOFmomentum"]
    momError = dict["TOFmomentumError"]

    #ax1.errorbar(mom, (linear(mom, params[0], params[1])-E)/E, xerr = momError, color = colors[i], yerr = sigmaE/E, fmt ='x', markersize = 10)

    ax1.errorbar(mom, (E2-linear(mom, params2[0], params2[1]))/E2, xerr = momError, color = colors[i], yerr = sigmaE2/E2, fmt ='o', markersize = 10)

ax1.plot([min(array_x)-10, max(array_x)+10], [0, 0], "r--")#, label = r"Total abs(fit-E)/E: %.2e"%(sum((abs(linear(array_x, params[0], params[1])-array_y)/array_y))))


ax0.grid()
ax0.set_ylabel("LG fitted mean E (a.u)", fontsize = 18)
ax0.set_xlabel("Electron tof-measured momentum (MeV/c)", fontsize = 18)
fig.suptitle("LG electron WindowIntPE mean +/- std energy\nagainst TOF-measured electron momentum", fontsize = 20, weight = "bold")

#residuals
# ax1.grid()
ax1.set_ylabel("Fit fractional residuals", fontsize = 18)
ax1.set_xlabel("Electron tof-measured momentum (MeV/c)", fontsize = 18)
plt.grid()
# ax1.legend(fontsize = 15)
ax0.legend(fontsize = 15)

plt.tick_params(axis='both', which='major', labelsize=15)
# plt.show()

fig.savefig("../%s/ElectronLGTOFMomentumRelationCheck.pdf"%("pdf_2plus2Coincidence_nosumTScut"))
fig.savefig("../%s/ElectronLGTOFMomentumRelationCheck.png"%("png_2plus2Coincidence_nosumTScut"))


###################################
########################################

array_x = []
array_y = []
fig, (ax0, ax1) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [3, 1]}, figsize = [10, 12])
for i, dict in enumerate(all_electron_dict):
    p_protons = dict["protonMomentum"]
    p_protons_error = dict["protonMomentumError"]
    mom = dict["momentum"]
    momError = dict["TOFmomentumError"]

    array_x.append(mom)
    array_y.append(p_protons)
    ax0.errorbar(mom, p_protons, yerr = p_protons_error, fmt ='x', markersize = 14, label = "Run %i - nominal p = %i MeV/c"%(run_numbers[i], dict["momentum"]), linewidth=3)

print(array_x, array_y)
array_x = np.array(array_x)
array_y = np.array(array_y)
params, covariance = fitFunction(array_x, array_y, linear)
x = np.linspace(min(array_x)-10, max(array_x) + 10, 100)
ax0.plot(x, linear(x, params[0], params[1]), 'k--', label = 'Linear Fit: %.2e x + %.2f'%(params[0], params[1]))

for i, dict in enumerate(all_electron_dict):
    p_protons = dict["protonMomentum"]
    p_protons_error = dict["protonMomentumError"]
    mom = dict["momentum"]
    momError = dict["TOFmomentumError"]

    ax1.errorbar(mom, (linear(mom, params[0], params[1])-p_protons)/p_protons, yerr = p_protons_error/p_protons, fmt ='x', markersize = 14, linewidth=3)

ax1.plot([min(array_x)-10, max(array_x)+10], [0, 0], "k--", label = r"Total abs(fit-p)/p: %.2e"%(sum((abs(linear(array_x, params[0], params[1])-array_y)/array_y))))


ax0.grid()
ax0.set_xlabel("Nominal beam momentum (MeV/c)", fontsize = 18)
ax0.set_ylabel("Proton tof-measured momentum (MeV/c)", fontsize = 18)
fig.suptitle("TOF-measured momentum (protons) mean +/- std \n against nominal beam momentum", fontsize = 20, weight = "bold")

#residuals
# ax1.grid()
ax1.set_ylabel("Fit fractional residuals", fontsize = 18)
ax1.set_xlabel("Nominal beam momentum (MeV/c)", fontsize = 18)
plt.grid()
ax1.legend(fontsize = 15)

ax0.legend(fontsize = 15)
plt.tick_params(axis='both', which='major', labelsize=15)
# plt.show()

fig.savefig("../%s/ProtonTOFMomentumRelationCheck.pdf"%("pdf_2plus2Coincidence_nosumTScut"))
fig.savefig("../%s/ProtonTOFMomentumRelationCheck.png"%("png_2plus2Coincidence_nosumTScut"))

