#!/bin/bash
log=/data/wcte_data/end_of_run.log
echo "$(date): End of run." &> $log
python3 /home/wcte/online/WCTE_Analyzer/create_runlog.py &>> $log
bash /home/wcte/online/WCTE_Analyzer/copy_files.sh &>> $log
ssh wcte-gw bash /home/wcte/online/WCTE_Analyzer/convert_files.sh &>> $log 
ssh wcte-gw bash /home/wcte/np/T9BeamTestAna/python/new_analysis/process_waveforms.sh &>> $log 

