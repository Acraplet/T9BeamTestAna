// Example Program for converting MIDAS format to ROOT format.
//
// T. Lindner (Jan 2016) 
//
// Example is for the CAEN V792 ADC module

#include <stdio.h>
#include <iostream>
#include <time.h>
#include <vector>

#include "TRootanaEventLoop.hxx"
#include "TFile.h"
#include "TTree.h"

#include "TDT730RawData.hxx"
#include "WcteEventBuilder.h"

#include "TH1D.h"

class Analyzer: public TRootanaEventLoop {

public:

  double nanosecsPerSample;
  double milivoltsPerADC;

  std::vector<std::string> dNames;

  // WCTE event builder
  WcteEventBuilder *fEventBuilder;

  // The tree to fill.
  TTree *fTree[4];

  int eventNumber[4];
  int spillNumber[4];
  uint32_t timeStamp[4];
  uint32_t triggerTime[4];
  std::vector<double> waveforms[4][8];

  Analyzer() {
    UseBatchMode();
  };

  virtual ~Analyzer() {};

  void Initialize(){}
  
  
  void BeginRun(int transition,int run,int time){

    nanosecsPerSample = 2; //ADC clock runs at 500Mhz on the 730 = units of 2 nsecs
    milivoltsPerADC = 2000./16384.; // 2000mV / 16384 counts (full scale)

    fEventBuilder = new WcteEventBuilder();

    // initial configuration with 3 digitizers
    // no TRB3
    if (run<=579) {
      fEventBuilder->SetEnabled(0,true);
      fEventBuilder->SetEnabled(1,true);
      fEventBuilder->SetEnabled(2,true);
      fEventBuilder->SetEnabled(3,false);
      fEventBuilder->SetEnabled(4,false);
      dNames.push_back("D300");
      dNames.push_back("D301");
      dNames.push_back("D302");
    }
    // hodoscope configuration with 4 digitizers
    // no TRB3
    else {
      fEventBuilder->SetEnabled(0,true);
      fEventBuilder->SetEnabled(1,true);
      fEventBuilder->SetEnabled(2,true);
      fEventBuilder->SetEnabled(3,true);
      fEventBuilder->SetEnabled(4,false);
      dNames.push_back("D300");
      dNames.push_back("D301");
      dNames.push_back("D302");
      dNames.push_back("D303");
    }


    for (unsigned int id=0; id<dNames.size(); id++) {

      // Create a TTree
      fTree[id] = new TTree(Form("midas_data_%s",dNames[id].c_str()),
                            Form("Digitizer %s",dNames[id].c_str()));

      std::cout << "Set Branches for tree " << dNames[id] << std::endl;    
      fTree[id]->Branch("eventNumber",&eventNumber[id],"eventNumber/i");
      fTree[id]->Branch("spillNumber",&spillNumber[id],"spillNumber/i");
      fTree[id]->Branch("timeStamp",&timeStamp[id],"timeStamp/i");
      fTree[id]->Branch("triggerTime",&triggerTime[id],"triggerTime/i");
      for(int i=0; i<8; i++) {
        fTree[id]->Branch(Form("Channel%d",i), &(waveforms[id][i]));
      }

    }

    std::cout << "Completed Begin Run" << std::endl;

  }


  void EndRun(int transition,int run,int time){
    for (unsigned int id=0; id<dNames.size(); id++) {
      std::cout << dNames[id] 
                << " entries " << fTree[id]->GetEntries()
                << std::endl;
    }
  }

 
  // Main work here; create ttree events for every sequenced event in 
  // Lecroy data packets.
  bool ProcessMidasEvent(TDataContainer& dataContainer){

    for (unsigned int id=0; id<dNames.size(); id++) {

      TDT730RawData *dt730 = dataContainer.GetEventData<TDT730RawData>(dNames[id].c_str());
    
      if(dt730){      

        std::vector<RawChannelMeasurement> measurements = dt730->GetMeasurements();

        for(unsigned int i = 0; i < measurements.size(); i++){
    
          int ch = measurements[i].GetChannel();
        
          waveforms[id][ch].clear();
          for (int s = 0; s<measurements[i].GetNSamples(); s++) {
            waveforms[id][ch].push_back(measurements[i].GetSample(s));
          }

          if (ch==7) {
            eventNumber[id] = measurements[i].GetEvtNumber();
            spillNumber[id] = 0;
            timeStamp[id] = 0;
            triggerTime[id]  = measurements[i].GetTriggerTime();
            fTree[id]->Fill();
          }

        }
      }
    }

    return true;

  };
  
  // Complicated method to set correct filename when dealing with subruns.
  std::string SetFullOutputFileName(int run, std::string midasFilename)
  {
    std::cout << "Setting output file from " << midasFilename << std::endl;
    char buff[128]; 
    Int_t in_num = 0, part = 0;
    Int_t num[2] = { 0, 0 }; // run and subrun values
    // get run/subrun numbers from file name
    for (int i=0; ; ++i) {
      char ch = midasFilename[i];
        if (!ch) break;
        if (ch == '/') {
          // skip numbers in the directory name
          num[0] = num[1] = in_num = part = 0;
        } else if (ch >= '0' && ch <= '9' && part < 2) {
          num[part] = num[part] * 10 + (ch - '0');
          in_num = 1;
        } else if (in_num) {
          in_num = 0;
          ++part;
        }
    }
    if (part == 2) {
      if (run != num[0]) {
        std::cerr << "File name run number (" << num[0]
                  << ") disagrees with MIDAS run (" << run << ")" << std::endl;
        exit(1);
      }
      sprintf(buff,"root_run_%.6d_%.4d.root", run, num[1]);
      printf("Using filename %s\n",buff);
    } else {
      sprintf(buff,"root_run_%.6d.root", run);
    }
    std::cout << "result " << buff << std::endl;
    return std::string(buff);
  };

}; 


int main(int argc, char *argv[])
{

  Analyzer::CreateSingleton<Analyzer>();
  return Analyzer::Get().ExecuteLoop(argc, argv);

}
