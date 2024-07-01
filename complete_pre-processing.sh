#This is a code that does all of the pre-processing required to go from a base root file to the final analysable code , you can call it with multiple run inputs

timingRange="final2"

for run in $@
do
    if [ $run -le 579 ]
    then
    config="config/config_noHodoscope.json"
    else
    config="config/config_hodoscope.json"
    fi
    echo "Starting the pre-processing for run "$run""
#     #this code does the peak finding and timing and creates the first ntuple, careful at this stage the signalTimeCorrected branch doesn't actually have the corrected timings
    python python/new_analysis/process_waveform_analysis.py data/root_run_$run.root $config peakAnalysed_$run.root

# # # # # # #     These codes, written by Arturo synchronise the timings across digitisers and then overwrites the signalTimeCorrected with the correctly shifted timings
    root -l -b -q 'macros/triggerTimeDrift.C("peakAnalysed_'$run'.root")'
    root -l -b -q 'macros/timeCorrection.C("peakAnalysed_'$run'.root", "triggerTimeDrift.txt", "peakAnalysed_timeCorr_'$run'.root", "timingCorrectionInfo_'$run'.root")'

#   This code performs the timing alignment of the hits (adds an arbitrary offset to the entire PMT timings to align the integration windows
#   It performs the window integration and converts signal to PE units.
# be careful: if you use the coincidence check you need to make sure that you are using the peakAnalysed_timeCorr code otherwise there will be format issues
    python python/new_analysis/process_ac_waveform_analysis.py data/root_run_$run.root peakAnalysed_timeCorr_$run.root $config WindowIntMatched_""$timingRange""_$run.root

done
