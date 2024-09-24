#!/bin/sh

./kill_daq.sh

odbedit -c clean
#odbedit -c "rm /Analyzer/Trigger/Statistics"
#odbedit -c "rm /Analyzer/Scaler/Statistics"

mhttpd -e e1 -D 
sleep 2
#bash /home/koerich/online/ccusb-modified/frontend
# ./findCAMAC.sh
mlogger -e e1 &
./fedt5730.exe

#echo Please point your web browser to http://localhost:8080

#end file
