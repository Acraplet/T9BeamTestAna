#include "TNumberOfEvents.h"

#include "TDT730RawData.hxx"
#include "TTRB3DataV2.hxx"
#include "TDirectory.h"


/// Reset the histograms for this canvas
TNumberOfEvents::TNumberOfEvents(){

  SetTabName("NumberOfEvents");
  SetSubTabName("Bank");
  SetUpdateOnlyWhenPlotted(false);
  
  CreateHistograms();

}


void TNumberOfEvents::CreateHistograms(){

  TH1D * temp = new TH1D("evts_bank", ";Bank ID", 5, 0, 5);
  push_back(temp);

  std::cout << "TNumberOfEvents done init...... " << std::endl;

}


void TNumberOfEvents::UpdateHistograms(TDataContainer& dataContainer){
  
  //int eventid = dataContainer.GetMidasData().GetEventId();
  //int timestamp = dataContainer.GetMidasData().GetTimeStamp();
  
  std::vector<std::string> bankNames = {"D300", "D301", "D302", "D303"};

  for (unsigned int ibank=0; ibank<bankNames.size(); ibank++) {

    TDT730RawData *dt730 = dataContainer.GetEventData<TDT730RawData>(bankNames[ibank].c_str());
    
    if(dt730){      
      
      std::vector<RawChannelMeasurement> measurements = dt730->GetMeasurements();

      int nevents = 0;
      for(unsigned int i = 0; i < measurements.size(); i++){
    
        int chan = measurements[i].GetChannel();
        //int nsamples = measurements[i].GetNSamples();
        //int evtnum = measurements[i].GetEvtNumber();
    
        if (chan==0) {
          //std::cout << "bank " << bankNames[ibank] << " channel " <<  chan 
          //            << " nsamples " <<  nsamples
          //            << " evtnum " <<  evtnum << std::endl;
          nevents++;
        }
      }

      GetHistogram(0)->Fill(ibank,nevents);
      //std::cout << "measurements per channel " << measurements.size()/8. << std::endl;
      //std::cout << "measurements per channel " << nevents << std::endl;


    }
  }
 
  // TRB3 data
  TTRB3DataV2 *trb3 = dataContainer.GetEventData<TTRB3DataV2>("TRB0");

  if(trb3){

    //std::cout << "trb3 bank " << trb3 << std::endl;
    std::vector<TrbTdcMeasV2> measurements = trb3->GetMeasurements();
    //std::cout << "measurements " << measurements.size() << std::endl;
    GetHistogram(0)->Fill(4);

    // This prints the TRB trigger number
    //std::cout << trb3->GetSeqNr() << " " << trb3->GetDecoder().GetTriggerNumber() << std::endl;
    for(unsigned int i = 0; i < measurements.size(); i++){

      //int chan = measurements[i].GetChannel();
      //double time = measurements[i].GetFinalTime();
      //if (chan>0  || 1) {
      //  std::cout << "bank TRB0 channel " <<  chan 
      //              //<< " nsamples " <<  nsamples
      //              << " time " << time << std::endl;
      //}
    }

  }

}



void TNumberOfEvents::Reset(){
  
  
  //for(int i = 0; i < 8; i++){ // loop over channels
    int index =  0;
    
    // Reset the histogram...
    for(int ib = 0; ib < GetHistogram(index)->GetNbinsX(); ib++) {
      GetHistogram(index)->SetBinContent(ib, 0);
    }
    
    GetHistogram(index)->Reset();
    
  //}
}
