#include "WcteEventHistograms.hxx"

#include "TDirectory.h"
#include "TH2.h"



WcteEventHistograms::WcteEventHistograms(){

  SetTabName("WCTE events");
  SetSubTabName("Analysis");
  SetUpdateOnlyWhenPlotted(false);
  
  //All ACTs are in digitizer D300
  digiACT = 0;
  chanACT0R = 0;
  chanACT0L = 1;
  chanACT1R = 2;
  chanACT1L = 3;
  chanACT2R = 4;
  chanACT2L = 5;
  chanACT3R = 6;
  chanACT3L = 7;

  // TOF channels
  digiTOF = 1;//digitizer D301

  // Lead Glass channels
  digiLG = 2;//digitizer D303
  chanLG = 0;

  // Hodoscope channels
  digiHodoscope.clear();
  chanHodoscope.clear();
  digiHodoscope.push_back(3); chanHodoscope.push_back(0); //CH0
  digiHodoscope.push_back(3); chanHodoscope.push_back(1); //CH1
  digiHodoscope.push_back(3); chanHodoscope.push_back(2); //CH2
  digiHodoscope.push_back(3); chanHodoscope.push_back(3); //CH3
  digiHodoscope.push_back(3); chanHodoscope.push_back(4); //CH4
  digiHodoscope.push_back(3); chanHodoscope.push_back(5); //CH5
  digiHodoscope.push_back(3); chanHodoscope.push_back(6); //CH6
  digiHodoscope.push_back(3); chanHodoscope.push_back(7); //CH7
  digiHodoscope.push_back(2); chanHodoscope.push_back(1); //CH8
  digiHodoscope.push_back(2); chanHodoscope.push_back(2); //CH9
  digiHodoscope.push_back(2); chanHodoscope.push_back(3); //CH10
  digiHodoscope.push_back(2); chanHodoscope.push_back(4); //CH11
  digiHodoscope.push_back(2); chanHodoscope.push_back(5); //CH12
  digiHodoscope.push_back(2); chanHodoscope.push_back(6); //CH13
  digiHodoscope.push_back(2); chanHodoscope.push_back(7); //CH14

  CreateHistograms();

}


void WcteEventHistograms::CreateHistograms(){

  // check if we already have histogramss.
  TH1D *tmp = (TH1D*)gDirectory->Get("Ana_0");
  if (tmp) return;

  // Otherwise make histograms
  clear();

  // TOF
  TH1D * h0 = new TH1D("Ana_0","TOF",300,0,30);
  h0->SetXTitle("time (ns)");
  h0->SetYTitle("Events");
  push_back(h0);//Histogram 0

  // Lead Glass vs TOF
  TH2D * h1 = new TH2D("Ana_1","",200,0,2000,300,0,30);
  h1->SetXTitle("Lead Glass Amplitude (mV)");
  h1->SetYTitle("TOF (ns)");
  push_back(h1);//Histogram 1

  // Lead Glass vs ACT2+ACT3
  TH2D * h2 = new TH2D("Ana_2","",200,0,2000,200,0,8000);
  h2->SetXTitle("Lead Glass Amplitude (mV)");
  h2->SetYTitle("ACT2+ACT3 Amplitude (mV)");
  push_back(h2);//Histogram 2

  // TOF vs ACT2+ACT3
  TH2D * h3 = new TH2D("Ana_3","",300,0,30,200,0,8000);
  h3->SetXTitle("TOF (ns)");
  h3->SetYTitle("ACT2+ACT3 Amplitude (mV)");
  push_back(h3);//Histogram 3

  // ACT0 vs ACT1
  TH2D * h4 = new TH2D("Ana_4","",200,0,4000,200,0,1000);
  h4->SetXTitle("ACT0 Amplitude (mV)");
  h4->SetYTitle("ACT1 Amplitude (mV)");
  push_back(h4);//Histogram 4

  // ACT2 vs ACT3
  TH2D * h5 = new TH2D("Ana_5","",200,0,4000,200,0,4000);
  h5->SetXTitle("ACT2 Amplitude (mV)");
  h5->SetYTitle("ACT3 Amplitude (mV)");
  push_back(h5);//Histogram 5

  // ACT2 + ACT3
  TH1D * h6 = new TH1D("Ana_6","",200,0,8000);
  h6->SetXTitle("ACT2+ACT3 Amplitude (mV)");
  h6->SetYTitle("Events");
  push_back(h6);//Histogram 6

  // ACT1 + TOF
  TH2D * h7 = new TH2D("Ana_7","",300,0,30,200,0,2000);
  h7->SetXTitle("TOF (ns)");
  h7->SetYTitle("ACT1 Amplitude (mV)");
  push_back(h7);//Histogram 7

  // Hodoscope hits (histogram 8)
  TH1D * hHodoHits = new TH1D("HodoHits","",15,0,15);
  hHodoHits->SetXTitle("Hodoscope channel");
  hHodoHits->SetYTitle("Number of hits");
  push_back(hHodoHits);

  // Hodoscope hits (histogram 9)
  TH2D * hHodoHitsLG = new TH2D("HodoHitsvsLG","",15,0,15,200,0,2000);
  hHodoHitsLG->SetXTitle("Hodoscope channel");
  hHodoHitsLG->SetYTitle("LG Amplitude (mV)");
  push_back(hHodoHitsLG);

  // Hodoscope hits (histogram 10)
  TH1D * hHodoMulti = new TH1D("HodoMulti","",15,0,15);
  hHodoMulti->SetXTitle("Hodoscope multiplicity");
  hHodoMulti->SetYTitle("Number of events");
  push_back(hHodoMulti);

  std::cout << "create WcteEventHistograms done "  << std::endl;

}


void WcteEventHistograms::UpdateHistograms(std::vector<WCTE_Event>& WcteEvent){


  // Loop over complete events
  for(unsigned int i = 0; i < WcteEvent.size(); i++){

    // ACT0-R
    vector<double> wfACT0R = WcteEvent[i].GetDigitizerWaveform(digiACT,chanACT0R);
    double pulseHeightACT0R = GetPulseHeight(wfACT0R);
    //double pulseTimeACT0R = GetPulseTimeLI(wfACT0R);

    // ACT0-L
    vector<double> wfACT0L = WcteEvent[i].GetDigitizerWaveform(digiACT,chanACT0L);
    double pulseHeightACT0L = GetPulseHeight(wfACT0L);
    //double pulseTimeACT0L = GetPulseTimeLI(wfACT0L);

    // ACT1-R
    vector<double> wfACT1R = WcteEvent[i].GetDigitizerWaveform(digiACT,chanACT1R);
    double pulseHeightACT1R = GetPulseHeight(wfACT1R);
    //double pulseTimeACT1R = GetPulseTimeLI(wfACT1R);

    // ACT1-L
    vector<double> wfACT1L = WcteEvent[i].GetDigitizerWaveform(digiACT,chanACT1L);
    double pulseHeightACT1L = GetPulseHeight(wfACT1L);
    //double pulseTimeACT1L = GetPulseTimeLI(wfACT1L);

    // ACT2-R
    vector<double> wfACT2R = WcteEvent[i].GetDigitizerWaveform(digiACT,chanACT2R);
    double pulseHeightACT2R = GetPulseHeight(wfACT2R);
    double pulseTimeACT2R = GetPulseTimeLI(wfACT2R);

    // ACT2-L
    vector<double> wfACT2L = WcteEvent[i].GetDigitizerWaveform(digiACT,chanACT2L);
    double pulseHeightACT2L = GetPulseHeight(wfACT2L);
    double pulseTimeACT2L = GetPulseTimeLI(wfACT2L);

    // ACT3-R
    vector<double> wfACT3R = WcteEvent[i].GetDigitizerWaveform(digiACT,chanACT3R);
    double pulseHeightACT3R = GetPulseHeight(wfACT3R);
    double pulseTimeACT3R = GetPulseTimeLI(wfACT3R);

    // ACT3-L
    vector<double> wfACT3L = WcteEvent[i].GetDigitizerWaveform(digiACT,chanACT3L);
    double pulseHeightACT3L = GetPulseHeight(wfACT3L);
    double pulseTimeACT3L = GetPulseTimeLI(wfACT3L);

    // combine ACT signal
    double pulseHeightACT0 = pulseHeightACT0R+pulseHeightACT0L;
    double pulseHeightACT1 = pulseHeightACT1R+pulseHeightACT1L;
    double pulseHeightACT2 = pulseHeightACT2R+pulseHeightACT2L;
    double pulseHeightACT3 = pulseHeightACT3R+pulseHeightACT3L;
    double pulseHeightACT23 = pulseHeightACT2+pulseHeightACT3;

    // TOF
    vector<double> time(8);
    for (unsigned int ch=0; ch<8; ch++) {
      vector<double> wf = WcteEvent[i].GetDigitizerWaveform(digiTOF,ch);
      time[ch]  = GetPulseTimeLI(wf);
    }

    double t0 = (time[0]+time[1]+time[2]+time[3])/4.;
    double t1 = (time[4]+time[5]+time[6]+time[7])/4.;
    double tof = t1-t0;

    // Lead Glass
    vector<double> wfLG = WcteEvent[i].GetDigitizerWaveform(digiLG,chanLG);
    double pulseHeightLG = GetPulseHeight(wfLG);

    // cuts
    bool pass = pulseTimeACT2R>20 &&
                pulseTimeACT2L>20 &&
                pulseTimeACT3R>20 &&
                pulseTimeACT3L>20;

    // Fill histos
    if (pass) {
      GetHistogram(0)->Fill(tof);
      GetHistogram(1)->Fill(pulseHeightLG,tof);
      GetHistogram(2)->Fill(pulseHeightLG,pulseHeightACT23);
      GetHistogram(3)->Fill(tof,pulseHeightACT23);
      GetHistogram(5)->Fill(pulseHeightACT2,pulseHeightACT3);
      GetHistogram(6)->Fill(pulseHeightACT23);
    }

    GetHistogram(4)->Fill(pulseHeightACT0,pulseHeightACT1);
    GetHistogram(7)->Fill(tof,pulseHeightACT1);

    // Hodoscope
    int nhodohits = 0;
    for (unsigned int hi=0; hi<digiHodoscope.size(); hi++) {
      vector<double> wf = WcteEvent[i].GetDigitizerWaveform(digiHodoscope[hi],chanHodoscope[hi]);
      double pulseHeight = GetPulseHeight(wf);
      if (pulseHeight>300) {
        GetHistogram(8)->Fill(hi);
        GetHistogram(9)->Fill(hi,pulseHeightLG);
        nhodohits++;
      }
    }
    GetHistogram(10)->Fill(nhodohits);

  }

}


double WcteEventHistograms::GetPulseTimeLI(const std::vector<double> &wf) {

  double timeRes  = 2.; //ADC clock runs at 500Mhz on the 730 = units of 2 nsecs

  int min = 9999999;
  int min_i = 0;
  for (unsigned int i=0; i<wf.size(); i++) {
    if (wf[i]<min) {
      min = wf[i];
      min_i = i;
    }
  }

  // Get pedestal
  // outside window around peak
  double ped = 0;
  int nsamples = 0;

  for(unsigned int i = 0; i < wf.size(); i++){
    double adc = wf[i];
    if (fabs(min_i-i)>25) {//25 samples (50ns)
      ped += adc;
      nsamples++;
    }
  }

  ped = ped/(double)nsamples;


  double percentage = 0.5;
  double wf_threshold = ped-percentage*(ped-min);
  for(int i = 0; i < min_i; i++){
    if (wf[i]>wf_threshold && wf[i+1]<=wf_threshold) {
      //do interpolation
      double wf_time = i+(wf_threshold-wf[i])/(wf[i+1]-wf[i]);
      return wf_time*timeRes;
      break;
    }
  }

  return 0;

}

double WcteEventHistograms::GetPulseTimeCFD(const std::vector<double> &wf) {

  double timeRes  = 2.; //ADC clock runs at 500Mhz on the 730 = units of 2 nsecs

  int min = 9999999;
  int min_i = 0;
  for (unsigned int i=0; i<wf.size(); i++) {
    if (wf[i]<min) {
      min = wf[i];
      min_i = i;
    }
  }

  // Get pedestal
  // outside window around peak
  double ped = 0;
  int nsamples = 0;

  for(unsigned int i = 0; i < wf.size(); i++){
    double adc = wf[i];
    if (fabs(min_i-i)>25) {//25 samples (50ns)
      ped += adc;
      nsamples++;
    }
  }

  ped = ped/(double)nsamples;

	// Find timing of pulse through constant-fraction discriminator.  
  double baseline = ped;
  int global_imin = min_i;
  double startp = 0.1;
  double endp = 0.9;
  double percentage = 0.5;


  double y_min = wf.at(global_imin)-baseline;
  double y_end = endp*y_min;
  double y_start = startp*y_min;
  double rise_amplitude = (endp-startp)*y_min;

  int j = global_imin;
  int j_end = 0;
  while (((wf.at(j)-baseline) < y_end) && (j > 1)) {
      j--;
      j_end = j-1;
  }

  j = global_imin;
  int j_start = 0;
  while (((wf.at(j)-baseline) < y_start) && (j > 1)) {
      j--;
      j_start = j+1;
  }

  if (j_end-j_start!=0) {
    double b = (y_end-y_start)/(double(j_end-j_start));
    double a = y_start - j_start*b;
    return ((percentage*rise_amplitude-a)/b)*timeRes;
  } 
  else {
    return j_end*timeRes;
  }

}


double WcteEventHistograms::GetPulseHeight(const std::vector<double> &wf) {

  // Find minimun of waveform
  int min = 9999999;
  int min_i = 0;
  for (unsigned int i=0; i<wf.size(); i++) {
    if (wf[i]<min) {
      min = wf[i];
      min_i = i;
    }
  }

  // Get pedestal
  // outside window around peak
  double ped = 0;
  int nsamples = 0;

  for(unsigned int i = 0; i < wf.size(); i++){
    double adc = wf[i];
    if (fabs(min_i-i)>25) {//25 samples (50ns)
      ped += adc;
      nsamples++;
    }
  }

  ped = ped/(double)nsamples;

  double scale = (2000./16384.); // 2000mV / 16384 counts (full scale)

  return (ped-min)*scale;

}

void WcteEventHistograms::Reset(){
  
  //for(int i = 0; i < fHistos.size(); i++){ // loop over channels
    GetHistogram(0)->Reset();
  //}

}
