#include "TDT730Histogram.h"

#include "TDT730RawData.hxx"
#include "TDirectory.h"


/// Reset the histograms for this canvas
TDT730Waveform::TDT730Waveform(std::string bankid)
{

  bankID = bankid;
  SetNumSamples(1024);
  SetNanosecsPerSample(2); //ADC clock runs at 500Mhz on the 730 = units of 2 nsecs
  SetMilivoltsPerADC(2000./16384.); // 2000mV / 16384 counts (full scale)

  SetTabName("Waveforms");
  SetSubTabName("DT730_" +  bankID);
  SetUpdateOnlyWhenPlotted(false);
  
  CreateHistograms();

}


void TDT730Waveform::CreateHistograms(){

  // check if we already have histogramss.
  std::cout << "Creating waveform histograms"  << std::endl;

  char tname[100];
  sprintf(tname,"DT730_%s_Waveform_%i",bankID.c_str(),0);

  TH1D *tmp = (TH1D*)gDirectory->Get(tname);
  if (tmp) return;

  // Otherwise make histograms
  clear();
  
  for(int i = 0; i < 8; i++){ // loop over 2 channels
    
    char name[100];
    char title[100];
    sprintf(name,"DT730_%s_Waveform_%i",bankID.c_str(),i);
    sprintf(title,"DT730 waveform for digitizer=%s ch=%i",bankID.c_str(),i);
    
    TH1D *tmp = new TH1D(name, title, this->numSamples, 0, this->numSamples*this->nanosecsPerSample);
    tmp->SetXTitle("time (ns)");
    //tmp->SetYTitle("voltage (mV)");
    tmp->SetYTitle("adc");
    std::cout << " creating histogram "  << tmp->GetName() << std::endl;
    
    push_back(tmp);

  }


  std::cout << "TDT730Waveform done init...... " << std::endl;

}


void TDT730Waveform::UpdateHistograms(TDataContainer& dataContainer){
  
  //int eventid = dataContainer.GetMidasData().GetEventId();
  //int timestamp = dataContainer.GetMidasData().GetTimeStamp();

  TDT730RawData *dt730 = dataContainer.GetEventData<TDT730RawData>(("D3"+bankID).c_str());

  if(dt730){

    std::vector<RawChannelMeasurement> measurements = dt730->GetMeasurements();

    for(unsigned int i = 0; i < measurements.size(); i++){

      int chan = measurements[i].GetChannel();
      int nsamples = measurements[i].GetNSamples();
      //int evtnum = measurements[i].GetEvtNumber();

      //std::cout << "bank " << bankID << " channel " <<  chan 
      //            << " nsamples " <<  nsamples
      //            << " evtnum " <<  evtnum << std::endl;

      // change number of bins if different from default
      if (nsamples!=GetHistogram(chan)->GetNbinsX()) {
        this->SetNumSamples(nsamples);
        GetHistogram(chan)->Reset();
        GetHistogram(chan)->SetBins(nsamples, 0, nsamples*this->nanosecsPerSample);
      }

      for(int ib = 0; ib < nsamples; ib++){
        double adc = measurements[i].GetSample(ib);
        //double mv = adc*this->milivoltsPerADC;
        GetHistogram(chan)->SetBinContent(ib+1, adc);
      }

    }


  }
  
}


void TDT730Waveform::Reset(){
  
  
  for(int i = 0; i < 8; i++){ // loop over channels
    int index =  i;
    
    // Reset the histogram...
    for(int ib = 0; ib < GetHistogram(index)->GetNbinsX(); ib++) {
      GetHistogram(index)->SetBinContent(ib, 0);
    }
    
  }
}


/// Reset the histograms for this canvas
TDT730WaveformInteresting::TDT730WaveformInteresting(std::string bankid)
{

  bankID = bankid;
  SetNumSamples(1024);
  SetNanosecsPerSample(2); //ADC clock runs at 500Mhz on the 730 = units of 2 nsecs
  SetMilivoltsPerADC(2000./16384.); // 2000mV / 16384 counts (full scale)

  SetTabName("Waveforms");
  SetSubTabName("DT730_" +  bankID);
  SetUpdateOnlyWhenPlotted(false);
  
  CreateHistograms();

}


void TDT730WaveformInteresting::CreateHistograms(){

  // check if we already have histogramss.
  std::cout << "Creating waveform histograms"  << std::endl;

  char tname[100];
  sprintf(tname,"DT730_Waveform_Interesting_%s_%i",bankID.c_str(),0);

  TH1D *tmp = (TH1D*)gDirectory->Get(tname);
  if (tmp) return;

  // Otherwise make histograms
  clear();
  
  for(int i = 0; i < 8; i++){ // loop over 2 channels
    
    char name[100];
    char title[100];
    sprintf(name,"DT730_Waveform_Interesting_%s_%i",bankID.c_str(),i);
    sprintf(title,"DT730 interesting event for digi=%s,ch=%i",bankID.c_str(),i);
    
    TH1D *tmp = new TH1D(name, title, this->numSamples, 0, this->numSamples*this->nanosecsPerSample);
    tmp->SetXTitle("time (ns)");
    //tmp->SetYTitle("voltage (mV)");
    tmp->SetYTitle("adc");
    std::cout << " creating histogram "  << tmp->GetName() << std::endl;
    
    push_back(tmp);

  }


  std::cout << "TDT730Waveform done init...... " << std::endl;

}


float set_threshold(int chan, std::string bankID){
  // Use a special threshold for ACT0                                                                                                                                                                                        
  // 2.5mV threshold for most channels, 100mV threshold for ACT0                                                                                                                                                             
  //float threshold = 2.5;
  //if(bankID== "00" and (chan == 0 or chan == 1)){ threshold = 100.0;}
  //return threshold;
  // disable threshold temporarily
  return -1;
    
	

}

void TDT730WaveformInteresting::UpdateHistograms(TDataContainer& dataContainer){
  
  //int eventid = dataContainer.GetMidasData().GetEventId();
  //int timestamp = dataContainer.GetMidasData().GetTimeStamp();

  TDT730RawData *dt730 = dataContainer.GetEventData<TDT730RawData>(("D3"+bankID).c_str());

  if(dt730){

    std::vector<RawChannelMeasurement> measurements = dt730->GetMeasurements();

    for(unsigned int i = 0; i < measurements.size(); i++){

      int chan = measurements[i].GetChannel();
      int nsamples = measurements[i].GetNSamples();
      //int evtnum = measurements[i].GetEvtNumber();

      //std::cout << "bank " << bankID << " channel " <<  chan 
      //            << " nsamples " <<  nsamples
      //            << " evtnum " <<  evtnum << std::endl;
      double peakAmp = 1e10;
      double peakPos = 0;

      for(int ib = 0; ib < nsamples; ib++){
        double adc = measurements[i].GetSample(ib);
        if (adc<peakAmp) {
          peakAmp = adc;
          peakPos = ib;
        }
      }
      double ped = 0;
      int nsamplesPed = 0;

      for(int ib = 0; ib < nsamples; ib++){
        double adc = measurements[i].GetSample(ib);
        if (fabs(peakPos-5)>0) {
          ped += adc;
          nsamplesPed++;
        }
      }

      ped = ped/(double)nsamplesPed;

      float pulse_height = (ped-peakAmp)*this->milivoltsPerADC;

      // Different thresholds for each channel
      float threshold = set_threshold(chan,bankID);

      if(pulse_height > threshold){

	// change number of bins if different from default
	if (nsamples!=GetHistogram(chan)->GetNbinsX()) {
	  this->SetNumSamples(nsamples);
	  GetHistogram(chan)->Reset();
	  GetHistogram(chan)->SetBins(nsamples, 0, nsamples*this->nanosecsPerSample);
	}
	
      

	for(int ib = 0; ib < nsamples; ib++){
	  double adc = measurements[i].GetSample(ib);
	  //double mv = adc*this->milivoltsPerADC;
	  GetHistogram(chan)->SetBinContent(ib+1, adc);
	}
      }

    }


  }
  
}


void TDT730WaveformInteresting::Reset(){
  
  
  for(int i = 0; i < 8; i++){ // loop over channels
    int index =  i;
    
    // Reset the histogram...
    for(int ib = 0; ib < GetHistogram(index)->GetNbinsX(); ib++) {
      GetHistogram(index)->SetBinContent(ib, 0);
    }
    
  }
}




/// Reset the histograms for this canvas
TDT730Amplitude::TDT730Amplitude(std::string bankid){

  bankID = bankid;
  SetNumSamples(1024);
  SetNanosecsPerSample(2); //ADC clock runs at 500Mhz on the 730 = units of 2 nsecs
  SetMilivoltsPerADC(2000.0/16384.0); // 2000mV / 16384 counts (full scale)

  SetTabName("Amplitudes");
  SetSubTabName("DT730_" +  bankID);
  SetUpdateOnlyWhenPlotted(false);
  
  CreateHistograms();

}


void TDT730Amplitude::CreateHistograms(){

  // check if we already have histogramss.
  char tname[100];
  sprintf(tname,"DT730_%s_Amplitude_%i",bankID.c_str(),0);

  TH1D *tmp = (TH1D*)gDirectory->Get(tname);
  if (tmp) return;

  // Otherwise make histograms
  clear();
  
  for(int i = 0; i < 8; i++){ // loop over 2 channels
    
    char name[100];
    char title[100];
    sprintf(name,"DT730_%s_Amplitude_%i",bankID.c_str(),i);
    sprintf(title,"DT730 amplitude for digitizer %s channel=%i",bankID.c_str(),i);
    
    TH1D *tmp = new TH1D(name, title, 1000, 0, 2000);//2mV bins
    tmp->SetXTitle("Amplitude (mV)");
    tmp->SetYTitle("Number of Events");
    std::cout << " creating histogram "  << tmp->GetName() << std::endl;
    
    push_back(tmp);

  }

  std::cout << "TDT730Amplitude done init...... " << std::endl;

}


void TDT730Amplitude::UpdateHistograms(TDataContainer& dataContainer){
  
  //int eventid = dataContainer.GetMidasData().GetEventId();
  //int timestamp = dataContainer.GetMidasData().GetTimeStamp();
  
  TDT730RawData *dt730 = dataContainer.GetEventData<TDT730RawData>(("D3"+bankID).c_str());
  
  if(dt730){      
    
    std::vector<RawChannelMeasurement> measurements = dt730->GetMeasurements();

    for(unsigned int i = 0; i < measurements.size(); i++){
           
      int chan = measurements[i].GetChannel();
      int nsamples = measurements[i].GetNSamples();

      // Get lowest point in waveform
      double peakAmp = 1e10;
      double peakPos = 0;

      for(int ib = 0; ib < nsamples; ib++){
        double adc = measurements[i].GetSample(ib);
        if (adc<peakAmp) {
          peakAmp = adc;
          peakPos = ib;
        }
      }

      // Get pedestal
      // outside a +/-25samples (+/-50ns)
      // window around peak
      double ped = 0;
      int nsamplesPed = 0;

      for(int ib = 0; ib < nsamples; ib++){
        double adc = measurements[i].GetSample(ib);
        if (fabs(peakPos-25)>0) {
          ped += adc;
          nsamplesPed++;
        }
      }

      ped = ped/(double)nsamplesPed;

      float pulse_height = (ped-peakAmp)*this->milivoltsPerADC;

      // Different thresholds for each channel
      float threshold = set_threshold(chan,bankID);

      if(pulse_height > threshold){
	GetHistogram(chan)->Fill(pulse_height);
      }

    }

  }
  
}


void TDT730Amplitude::Reset(){
  
  
  for(int i = 0; i < 8; i++){ // loop over channels
    int index =  i;
    
    // Reset the histogram...
    for(int ib = 0; ib < GetHistogram(index)->GetNbinsX(); ib++) {
      GetHistogram(index)->SetBinContent(ib, 0);
    }
    
    GetHistogram(index)->Reset();
    
  }
}


/// Reset the histograms for this canvas
TDT730Time::TDT730Time(std::string bankid){

  bankID = bankid;
  SetNumSamples(1024);
  SetNanosecsPerSample(2); //ADC clock runs at 500Mhz on the 730 = units of 2 nsecs
  SetMilivoltsPerADC(2000.0/16384.0); // 2000mV / 16384 counts (full scale)

  SetTabName("Times");
  SetSubTabName("DT730_" +  bankID);
  SetUpdateOnlyWhenPlotted(false);
  
  CreateHistograms();

}


void TDT730Time::CreateHistograms(){

  // check if we already have histogramss.
  char tname[100];
  sprintf(tname,"DT730_%s_Time_%i",bankID.c_str(),0);

  TH1D *tmp = (TH1D*)gDirectory->Get(tname);
  if (tmp) return;

  // Otherwise make histograms
  clear();
  
  for(int i = 0; i < 8; i++){ // loop over 2 channels
    
    char name[100];
    char title[100];
    sprintf(name,"DT730_%s_Time_%i",bankID.c_str(),i);
    sprintf(title,"DT730 time for digitizer %s channel=%i",bankID.c_str(),i);

    TH1D *tmp = new TH1D(name, title, 100, 0, 200);
    tmp->SetXTitle("Time (ns)");
    tmp->SetYTitle("Number of Events");
    std::cout << " creating histogram "  << tmp->GetName() << std::endl;
    
    push_back(tmp);

  }

  std::cout << "TDT730Time done init...... " << std::endl;

}


void TDT730Time::UpdateHistograms(TDataContainer& dataContainer){
  
  //int eventid = dataContainer.GetMidasData().GetEventId();
  //int timestamp = dataContainer.GetMidasData().GetTimeStamp();
  
  TDT730RawData *dt730 = dataContainer.GetEventData<TDT730RawData>(("D3"+bankID).c_str());
  
  if(dt730){      
    
    std::vector<RawChannelMeasurement> measurements = dt730->GetMeasurements();

    for(unsigned int i = 0; i < measurements.size(); i++){
           
      int chan = measurements[i].GetChannel();
      int nsamples = measurements[i].GetNSamples();
      
      if (nsamples!=GetHistogram(chan)->GetNbinsX()) {
        this->SetNumSamples(nsamples);
        GetHistogram(chan)->Reset();
        GetHistogram(chan)->SetBins(nsamples, 0, nsamples*this->nanosecsPerSample);
      }

      // First find the amplitude
      double ped = 0;
      double peakAmp = 1e10;
      int nsamplesPed = 0;

      for(int ib = 0; ib < nsamples; ib++){
        double adc = measurements[i].GetSample(ib);
        if (ib<=20) {
          ped += adc;
          nsamplesPed++;
        }
        if (adc<peakAmp) peakAmp = adc;
      }
      
      ped = ped/(double)nsamplesPed;

      // Now find the index of the first sample at half amplitude
      double halfPeak = 0.5*(ped-peakAmp);
      double val = ped - measurements[i].GetSample(0);
//      double prevVal = val;
      int ib;
      for(ib = 0; ib < nsamples; ib++){
//        prevVal = val;
        val = ped - measurements[i].GetSample(ib);
        if(val > halfPeak)
          break;
      }
     
      double time = (ib/*-(val-halfPeak)/(val-prevVal)*/)*this->nanosecsPerSample;
//      std::cout << "DEBUG: "<< ib << " " << time << std::endl;


      // Only fill time histogram for pulses over threshold
      float pulse_height = (ped-peakAmp)*this->milivoltsPerADC;

      // Different thresholds for each channel                                                                                                                                                                                   
      float threshold = set_threshold(chan,bankID);

      if(pulse_height > threshold){
        GetHistogram(chan)->Fill(time);
      }

      //GetHistogram(chan)->Fill(time);

    }


  }
  
}


void TDT730Time::Reset(){
  
  
  for(int i = 0; i < 8; i++){ // loop over channels
    int index =  i;
    
    // Reset the histogram...
    for(int ib = 0; ib < GetHistogram(index)->GetNbinsX(); ib++) {
      GetHistogram(index)->SetBinContent(ib, 0);
    }
    
    GetHistogram(index)->Reset();
    
  }
}


/// Reset the histograms for this canvas
TDT730Charge::TDT730Charge(std::string bankid){

  bankID = bankid;
  SetNumSamples(1024);
  SetNanosecsPerSample(2); //ADC clock runs at 500Mhz on the 730 = units of 2 nsecs
  SetMilivoltsPerADC(2000.0/16384.0); // 2000mV / 16384 counts (full scale)

  SetTabName("Charge");
  SetSubTabName("DT730_" +  bankID);
  SetUpdateOnlyWhenPlotted(false);
  
  CreateHistograms();

}


void TDT730Charge::CreateHistograms(){

  // check if we already have histogramss.
  char tname[100];
  sprintf(tname,"DT730_%s_Charge_%i",bankID.c_str(),0);

  TH1D *tmp = (TH1D*)gDirectory->Get(tname);
  if (tmp) return;

  // Otherwise make histograms
  clear();
  
  for(int i = 0; i < 8; i++){ // loop over 2 channels
    
    char name[100];
    char title[100];
    sprintf(name,"DT730_%s_Charge_%i",bankID.c_str(),i);
    sprintf(title,"DT730 charge for digitizer %s channel=%i",bankID.c_str(),i);
    
    TH1D *tmp = new TH1D(name, title, 200, -20, 80);
    tmp->SetXTitle("Charge (10^6 electrons)");
    tmp->SetYTitle("Number of Events");
    std::cout << " creating histogram "  << tmp->GetName() << std::endl;
    
    push_back(tmp);

  }

  std::cout << "TDT730Charge done init...... " << std::endl;

}


void TDT730Charge::UpdateHistograms(TDataContainer& dataContainer){
  
  //int eventid = dataContainer.GetMidasData().GetEventId();
  //int timestamp = dataContainer.GetMidasData().GetTimeStamp();
  
  TDT730RawData *dt730 = dataContainer.GetEventData<TDT730RawData>(("D3"+bankID).c_str());
  
  if(dt730){      
    
    std::vector<RawChannelMeasurement> measurements = dt730->GetMeasurements();

    for(unsigned int i = 0; i < measurements.size(); i++){
           
      int chan = measurements[i].GetChannel();
      int nsamples = measurements[i].GetNSamples();
      
      // Get lowest point in waveform
      double peakAmp = 1e10;
      double peakPos = 0;

      for(int ib = 0; ib < nsamples; ib++){
        double adc = measurements[i].GetSample(ib);
        if (adc<peakAmp) {
          peakAmp = adc;
          peakPos = ib;
        }
      }

      // Get pedestal
      // outside a +/-5samples (+/-10ns)
      // window around peak
      double ped = 0;
      int nsamplesPed = 0;

      for(int ib = 0; ib < nsamples; ib++){
        double adc = measurements[i].GetSample(ib);
        if (fabs(peakPos-5)>0) {
          ped += adc;
          nsamplesPed++;
        }
      }

      ped = ped/(double)nsamplesPed;

      // Integrate waveform
      double integral = 0;

      for(int ib = 0; ib < nsamples; ib++){
        double adc = measurements[i].GetSample(ib);
        integral += (ped-adc);//ADC
      }

      // calculate integrated charge
      // q = (V/R)*dt
      double charge = (integral*this->milivoltsPerADC/50.)*this->nanosecsPerSample;//pC

      // normalize to number of electrons
      // #e = q/q_electron
      charge = charge*1e-12/1.6e-19/1e6;//10^6 electrons

      //if (chan==1 && bankID=="00") {
      //  std::cout << "charge " << charge << std::endl;
      //}

      GetHistogram(chan)->Fill(charge);

    }

  }
  
}


void TDT730Charge::Reset(){
  
  
  for(int i = 0; i < 8; i++){ // loop over channels
    int index =  i;
    
    // Reset the histogram...
    for(int ib = 0; ib < GetHistogram(index)->GetNbinsX(); ib++) {
      GetHistogram(index)->SetBinContent(ib, 0);
    }
    
    GetHistogram(index)->Reset();
    
  }
}

/// Reset the histograms for this canvas
TDT730TOF::TDT730TOF()
{

  SetNumSamples(1024);
  SetNanosecsPerSample(2); //ADC clock runs at 500Mhz on the 730 = units of 2 nsecs
  SetMilivoltsPerADC(2000./16384.); // 2000mV / 16384 counts (full scale)

  SetTabName("Ana");
  SetSubTabName("TOF");
  SetUpdateOnlyWhenPlotted(false);
  
  CreateHistograms();

}


void TDT730TOF::CreateHistograms(){

  // check if we already have histogramss.
  std::cout << "Creating TOF histograms"  << std::endl;

  TH1D* tof_cfd = new TH1D("tof_cfd", "TOF CFD", 100, 0, 50);
  push_back(tof_cfd);

  std::cout << "TDT730TOF done init...... " << std::endl;

}

void TDT730TOF::UpdateHistograms(TDataContainer& dataContainer){
  
  //int eventid = dataContainer.GetMidasData().GetEventId();
  //int timestamp = dataContainer.GetMidasData().GetTimeStamp();

  TDT730RawData *dt730 = dataContainer.GetEventData<TDT730RawData>("D301");

  if(dt730){

    std::vector<RawChannelMeasurement> measurements = dt730->GetMeasurements();

    std::vector<std::vector<double>> waveforms;
    waveforms.resize(8);

    for(unsigned int i = 0; i < measurements.size(); i++){

      int chan = measurements[i].GetChannel();
      int nsamples = measurements[i].GetNSamples();
      //std::cout << chan << " " << nsamples << std::endl;

      for(int ib = 0; ib < nsamples; ib++) {
        double adc = measurements[i].GetSample(ib);
        waveforms[chan].push_back(adc);
      }// samples 

      // end of event all channels shoulw be full
      if (chan==7)  {

        //std::cout << "found end of event " << std::endl;

        // extract time from each channel
        vector<double> times0;
        vector<double> times1;

        for (int ch=0; ch<8; ch++) {
          //std::cout << waveforms[ch].size() << std::endl;
          double baseline = waveformBaseline(waveforms.at(ch));
          //std::cout << "baseline " << baseline << std::endl;
          int gTime = globalTiming(waveforms.at(ch), baseline);
          //std::cout << "global time " << gTime << std::endl;
          double min = waveformMin(waveforms.at(ch));
          double pulse_height = (baseline - min)*this->milivoltsPerADC;
          double time = cfdTiming(waveforms.at(ch), baseline, gTime, 0.1, 0.9, 0.5)*this->nanosecsPerSample;

          //std::cout << "channel " << ch << " height " << pulse_height << " time " << time << std::endl;

          float threshold = set_threshold(chan,"01");
          if (pulse_height>threshold) {
            if (ch<4) times0.push_back(time);
            else      times1.push_back(time);
          }
        }

        // calculate TOF
        double t0 = 0;
        for (unsigned int t=0; t<times0.size(); t++) t0+=times0[t];
        t0 = t0/(double)times0.size();
        //std::cout << "t0 " << t0 << std::endl;

        double t1 = 0;
        for (unsigned int t=0; t<times1.size(); t++) t1+=times1[t];
        t1 = t1/(double)times1.size();
        //std::cout << "t1 " << t1 << std::endl;

        double cfd_timing  = t1-t0;
        //std::cout << "tof " << cfd_timing << std::endl;
        GetHistogram(0)->Fill(cfd_timing);

        // clean waveforms
        for (int ch=0; ch<8; ch++) {
          waveforms[ch].clear();
        }

      }

    }// measurements

  } // dt730

}

void TDT730TOF::Reset(){
  
  GetHistogram(0)->Reset();
}

double TDT730TOF::waveformMin(std::vector<double> waveform){
	/*
	Find baseline of a waveform from the first 20 samples. 
	*/

  double ymin = 99999999.;
  //int imin = 0;
  int nsamples = waveform.size();
  for (int k = 0; k < nsamples; k++){
    if (waveform.at(k) < ymin) {
        ymin = waveform.at(k);
        //imin = k;
        // std::cout<< "   " << ymin << std::endl;
    }
  }
  //std::cout << "min pos " << imin << " min adc " << ymin << std::endl;
  return ymin;
}

double TDT730TOF::waveformBaseline(std::vector<double> waveform){
	/*
	Find baseline of a waveform from the first 20 samples. 
	*/

  double ymin = 99999999.;
  int imin = 0;
  int nsamples = waveform.size();
  for (int k = 0; k < nsamples; k++){
    if (waveform.at(k) < ymin) {
        ymin = waveform.at(k);
        imin = k;
        // std::cout<< "   " << ymin << std::endl;
    }
  }
  //std::cout << "min pos " << imin << " min adc " << ymin << std::endl;

  double sample_sum = 0.;
  int count = 0;
	int waveform_size = waveform.size();

  for (int k=0; k<waveform_size; k++) {
    if (abs(k-imin)>25) {
      sample_sum += waveform.at(k);
      count++;
    }
  }
  //std::cout << "baselina samples " << count << std::endl;

  double baseline = sample_sum/float(count);
  return baseline;
}

double TDT730TOF::globalTiming(std::vector<double> waveform, const double baseline) {
	/*
	Find global minimum of a vector of double values.
	*/
  double ymin = 99999999.;
  int imin = 0;
  int nsamples = waveform.size();
  for (int k = 0; k < nsamples; k++){
    if (waveform.at(k) < ymin) {
        ymin = waveform.at(k);
        imin = k;
        // std::cout<< "   " << ymin << std::endl;
    }
  }
  //std::cout << "min pos " << imin << " min adc " << ymin << std::endl;
  return imin;

}
double TDT730TOF::cfdTiming(std::vector<double> waveform, double baseline, const int global_imin, const float startp, const float endp, const float percentage) {
	/* Find timing of pulse through constant-fraction discriminator.  
	*/ 
    double y_min = waveform.at(global_imin)-baseline;
    double y_end = endp*y_min;
    double y_start = startp*y_min;
    double rise_amplitude = (endp-startp)*y_min;

    int j = global_imin;
    int j_end = 0;
    while (((waveform.at(j)-baseline) < y_end) && (j > 1)) {
        j--;
        j_end = j-1;
    }

    j = global_imin;
    int j_start = 0;
    while (((waveform.at(j)-baseline) < y_start) && (j > 1)) {
        j--;
        j_start = j+1;
    }

    //std::cout << "j start " << j_start << " end " << j_end << std::endl;
    //std::cout << "y start " << y_start << " end " << y_end << std::endl;

    if (j_end-j_start!=0) {
      double b = (y_end-y_start)/(double(j_end)-double(j_start));
      double a = y_start - j_start*b;
      return (percentage*rise_amplitude-a)/b;
    } 
    else {
      return j_end;
    }
}
