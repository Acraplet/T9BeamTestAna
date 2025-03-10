# T9BeamTestAna
Analysis package for the T9 beam test

2023
## Cleaned up version:


Coincidence and config PR: (slides with summary of changes: https://wcte.hyperk.ca/wg/beam/meetings/2024/20240408/meeting/coincidence-and-window-integration-pr)

Instead of taking the hit time in TOF10 as the reference for the window integration we are now using the average time accross 2PMTs in TOF1 for which there is coincidence in TOF1 and loose coincidence with a third PMT, this one in TOF0. We are saving the 'cleaned up' timings in SignalTimeMatchedTOF1 and SignalTimeMatchedTOF0, these will be useful for calculating a clean TOF.  The config files now include the bounds for the window integration for each detector (TODO: values not final yet) and decide whether the window integration should be made with respect to hit times in TOF10 only or with respect to the coincidence hit times over 2+1 PMTs, which PMTs are used in coincidence is set in the config file.

The pipeline also saves an extra branch called DigiTimingOffset which stores the timing offset for each event (this is 0 for digitiser 1) which is used when performing the window integration. The timing correction histograms produced by Arturo's ROOT macros are now saved in a SEPARATE ROOT file than the peakAnalysed root file used for analyses (formatting incompatibilities).

MERGE: all coincidence and window integration procedure are now ** available** for the TAGGED PHOTON set-up too with sensible results. 

A fine tuning PR will follow which will:

- decide on best integration window for all detectors
- correct for the particle time of flight in the window positioning
- remove the loose coincidence for hodoscope runs: we only expect positrons, allowing 20ns coincidence lowers the signal purity
- impelement an OR in the coincidence accross multiple PMT pairs to increase further the efficiency

The "base mechanics" are not expected to change anymore 



Timing PR: following the addition of the SignalTimeCorrected branch (Arturo's timing corrections) the pre-processing can now be run automatically with the following line:
```bash complete_pre-processing.sh 000393``` 
replacing the run with the correct run number. The code automatically selects the config file that is appropriate depending on if you are looking at low momentum or tagged photon runs. It follows a similar structure to what is presented below with the extra steps correcting the timing namely:


```root -l -b -q 'macros/triggerTimeDrift.C("peakAnalysed_'$run'.root")'; root -l -b -q 'macros/timeCorrection.C("peakAnalysed_'$run'.root", "triggerTimeDrift.txt", "peakAnalysed_timeCorr_'$run'.root")'```
Tested with ROOT 6.26/10. This step is not crutial in the analysis, if you choose to comment the two commands above out then the SignalTimeCorrected branch is a simple copy of the SignalTime branch. 

TODO: The pedestal value is taken as the most probable out of the non-analysis part of the waveform which is different for each event and can be influenced by the presence of a particle in the following bunch, especially in the ACT0 and lead glass. Eventually we might want to move to a fixed, run-dependant pedestal value. 

Minor bug fixes and improvements. 

Since the end of the beam time the analyis of the root files moved to python. Firstly the peak detect algorithm is applied to the root file using:

```python python/new_analysis/process_waveform_analysis.py data/root_run_000$run.root config/config_noHodoscope.json peakAnalysed_$run.root```
(note: you might have to use python3 instead of python, if you get errors)

where the config file contains:
 1. information about the analysis portion of the waveform and the pedestal portion
 2. the relative timing offset between the 8 PMTs composing the 2 time of flight detectors
 3. the channel names and whether they are active
 4. the voltage scale (forconverting ADC counts to V)

Note: the code is written in python3, you might need to run it with python3 instead of python depending how your environment is set up. 

The resulting root file contains the peak integrated charge for all of the peaks found in the signal. They can be accessed as shown in  python/peakMatching for example. 

Once we have information about the peak timing we can run the python analysis a second time to integrate a protion of the ACT waveform of a fixed duration around the expected time of arrival. The window duration is user-input (I used -16 to 45ns in general) and the timing offset calibration with respect to the TOF01 detector is done automatically at run time. This piece of code also adds two new branches to the data holding the peak and window integrated charges converted to the number of PE which is useful for comparisions. It is ran with: 

```python python/new_analysis/process_ac_waveform_analysis.py data/root_run_000$run.root peakAnalysed_$run.root -16 45 config/config_ac_noHodoscope.json windowPE_-16ns_45ns_run$run.root ```

where we take as input the initial root file and the one that has been analysed with the original peak finding analysis. The config file contains:
  1. V to PE conversion for the ACT PMTs
  2. all that is contained in config_noHodoscope.json
  3. typical timing calibration constants, not used but could be useful for debug

The whole analysis can be run for multiple files using:

```bash process_all_1PE.sh```

There are three helper python code for accessing the data and producing some (more or less) useful plots. These are ```python/multipeak_qualityChecks.py```, ```python/peakMatching.py``` and ```python/studyLenWindow.py```. There is now a comprehensive code that does particle ID and momentum measurements that can be called with:

```python python/particleID.py windowPE_-16ns_45ns_run$run.root runNumber +/-Momentum refractiveIndex isBerylliumTarget probabilityThatThereisAparticleInBunch``` e.g.: ```python python/particleID.py singlePEstudy/singlePE_-16ns_45ns_run432.root 432 +460 1.047 1 0.0023```

This code reads in the information stored in referenceParticleNumbers.txt to give a first proposition of the selection cuts that could be applied, depending on the beam momentum. This file has the same format as ```numberParticles.txt``` (see below) 

More information about how to use this code and what it does are here: https://wcte.hyperk.ca/wg/beam/meetings/2023/20231204/meeting/charge-particle-updates-and-future-studies/acraplet_041223_chargedparticlesetupupdates.pdf/view [1] 

The analysis code outputs a bunch of numbers to a ```numberParticles.txt``` file that stores the following informations:
1. run number
2. momentum (positive or negative depending on beam charge)
3. refIndex (index of refraction of aerogels ACT2 and ACT3)
4. nSpills (number of spills, calculated in the code)
5. probaBunch (probability for a bunch to contain a particle, see Dean's slides: https://wcte.hyperk.ca/wg/beam/meetings/2023/20231127/meeting/beam-structure-and-dead-time-studies-continued/beam_structure_v3.pdf/view
6. nParticles (total number of particles identified)
7. nElectrons
8. nMuons
9. nPions
10. nProtons
11. nDeuterium (if TOF is very large)
12. fractionPass1ParticleVeto (fraction of events where there is *exactly* one peak in *all* of the TOF PMTs, 8 in total)
13. fractionPassNanVeto (always one, just checking if there are any file corruptions)
14. ACTlinearA (linear coefficient for the selection cut in the ACT2+3 vs ACT1 plane, see ref [1]
15. ACTlinearB (second line coefficient for the selection)
16. piMuBorderACT (separation between the pion and muon (in units of PE) populations in ACT23)
17. ACTlower (lowest ACT23 bound, to avoid noise)
18. thereIsProtons (1 or 0 depending on the charge of the beam)
19. protonsTOFCut (in ns, 0 if there are no protons at all)
20. horizontal_el (in PE, horizontal cut to account for the scintillation and not misID pions/muons as electrons)
21. LGupper (lead glass signal above which the particle has to be an electron, to account for weird eletrons, see [1])
22. bery (whether the target is beryllium, or Aluminium, 1 for beryllium, 0 for Al)

Coding still left to do:
1. change the reference timing to be an average of TOF10, TOF11, TOF12 and TOF13 over peaks in coincidence (study ongoing) to limit risks of accidentals in TOF01 biasing the signal
2. look into pedestal estimation
3. probably merge the config files into 1 to have something cleaner
   



please get in touch if anything's unclear,

Alie


2023
## Quick and dirty start:

In essence the code runs in parallel over the four midas TTrees, where in every event each channel waveform is stored as TH1D; this is the first a C++ code to run a waveform analysis binary ./bin/waveform_analysis.app

Then there is ROOT macro scripts/MakeDataPlots.C to plot the charges etc to a root file. Next are ToF fit scripts, not updated for 2023 yet.


make

Bin edges to compute pedestal and search for the peak are defined in
config/config.json

Make a link to the directory where you store your midas-to-root converted data locally:

ln -s YOURDATAFOLDER data

Get commands what to run:

./python/run_wa_all.py

and choose what to run over

e.g.

./bin/waveform_analysis.app -i lists/list_root_run_000222.txt -o output/output_list_root_run_000222.root -c config/config.json

root -l -b -q  "scripts/MakeDataPlots.C(\"output/output_list_root_run_000222.root\", 1000)"

see histos/ then and histograms therein like

hRef_Voltage*

hRef_PedestalSigma*

quick simple plotting 1D:
python3 ./python/quickPlots1d.py histos/output_list_root_run_000222_plots.root
then close by File -> Quit ROOT in any of the Canvases that appear

more plots:
python3 ./python/slowPlots1d.py histos/output_list_root_run_000222_plots.root


July 17th 2023:

New default way: instead of getting the midas-to-ROOT converted files, for those not interested in waveforms, get the already waveform-analyzed ntuples with the anaTree from the wctePC:

cd output/ ; ./get.sh; cd ../

./python/run_mkplots.py

and choose what to run, e.g.

./python/run_mkplots.py | egrep "310|318"

./python/run_mkplots.py | grep "Make"

./python/run_mkplots.py | grep "quick"

./python/run_mkplots.py | grep "slow"

2023 SHIFTER:
./shifter/CheckRun.sh XYZ


More detailed:

save the https://wcte-daq/?cmd=custom&page=RunLog as html do Downloads on the daq proxy machine
then in your local analysis directory, get the file to share/:
cd share/ ; ./get.sh ; cd ../
Now you can run parse script to get/update run-momenta dictionary:
./python/parseWcteDaqRunsHtml.py and possibly modify to update data_runs_dicts.py
This also generates a C++ version of the run-momenta map: include/data_runs_dicts.h

Also
Add a list of bad runs based on length of files in output/:
First check it:
./python/makeBadRunList.py
If sure, add it:
./python/makeBadRunList.py > python/data_badruns.py 

Expected TOF times can be computed using utils in
python/tofUtil.py
and example can be run as
python/tofCompute.py

The momentum is determined for each run automatically by the 
./python/run_wa_all.py
script now, too.

New scripts under development are also:
./python/fitToF.py
so e.g.
./python/fitToF.py histos/output_list_root_run_000281_plots.root 


Jiri



2022 specific:

To compile the code type **make** in the main directory.

## Processing data

The first analysis stage includes processing data files. The output is a root file with anaTree TTRee. It includes, trigger timestamps, pedestals, pedestals standard deviations, signal amplitudes and times.

USAGE: **./bin/waveform_analysis.app** -i input_list_file -o output_root_file -c analysis_config.json

  **-i input_list_file**      --> ASCII file with run file names (one file per line). It allows users to run with multiple runs. If you put # before  the file name, it will be "commented out" (not used by the code)
  
  **-o output_root_file**     --> output root file
  
  **-c analysis_config.json** --> json configuration file (an example is located in config/config.json

## Making plots
Navigate to scripts/ directory. 

root -q -b '**MakeDataPlots.C**("output_file_from_step1", momentum)'

The script will use int momentum to recognize which cuts it needs to use. The script output is a root file with the same name as the input and "_plots" appended to the end. It contains:
  - reference histograms (they have "ref" in the name and don't change when you apply cuts) 
  - TOF histograms that are used to estimate the fraction of particles.  

## Fitting: the TOF distribution:
Done by **scripts/FitTOF.C**, a compilable ROOT macro
 - By default, a 3-component fit of 3 Gaussians is fitted to extract the number of e, mu and pi events;
 - In the macro, booleans isThreeComponentFit and isProtonFit are set automatically based on the momentum.

Example running:
 ** root -l "scripts/FitTOF.C(\"output_260n_plots.root\",-260)"


## Additional scripting over all momenta

The list of runs for every momentum is stored in **python/data_runs.py**
 - edit as needed, must enter also the total number of spills for the runs. The pipe separator between runs is needed as this is used to grep the proper runs. Again, 'p' and 'n' stand for positive and negative charged particles in given momentum setup.

The runs are split to low (200--280 MeV), high (300--360 MeV) and p (>= 400 MeV) runs.

Create a link name 'data' to a folded holding the TB ROOT files in name format as root_run_000153_0000_clean.root
  -  ln -s YOURPATHTODATA data

Running the waveform analysis, plotting and fitting for all momenta: done by **./python/run_momenta.py**

One has to specify whether really run (0/1), or just print the commands to choose from, or optionally not run but just fit by '0f'. Momentum range low/high/p must be specified, so e.g.:

 - python ./python/run_momenta.py 1 low    # run everything: waveforms analysis, make histos, fit the TOF; for low momenta
 - python ./python/run_momenta.py 1 high   # same as above; for high momenta
 - python ./python/run_momenta.py 0f low   # do not run the waveform analysis, just fit, higher momenta
 - python ./python/run_momenta.py 0m low   # do not run the waveform analysis, but run making the histograms and cuts
 - python ./python/run_momenta.py 0fm low  # do not run the waveform analysis, but run making the histograms and cuts; and fit	
 - python ./python/run_momenta.py 0 p      # just print commands for the proton runs

Output are png's, pdf's; and mainly ascii files with fitted numbers of e, mu, pi; or p; or mu+pi over 300 MeV.
 - E.g. ascii_output_220p_plots.txt

## Plotting the mu and pi yields scaled to per day rates

 The yields scaling is based on interval between spills of 40s; as function of the momentum.
 
 This is done by **python/plotFromAscii.py** for which one needs to choose the negative or positive beam p/n and the momenta range (low, high, or 'p' for protons).

  - python ./python/plotFromAscii.py p low
  - python ./python/plotFromAscii.py n low
  - python ./python/plotFromAscii.py p high
  - python ./python/plotFromAscii.py n high
  - python ./python/plotFromAscii.py p p # for protons

One can make a html page for viewing the fit results:
  -  ./scripts/make_html.sh

