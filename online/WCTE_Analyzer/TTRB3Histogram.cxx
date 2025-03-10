#include "TTRB3Histogram.hxx"

#include "TTRB3DataV2.hxx"
#include "TDirectory.h"
#include "TH2.h"
//#include "ChannelMapping.hxx"
#include <fstream>

const int NchannelPerFpga = 64; /// what is right value?
const int Nfpga = 16;

/// channel mapping
/// PMT number of connectors, channels, and order of channels
/// on PMT face channel numbers go left to right top to bottom
/// same as reading order
const unsigned nconnector=4;
const unsigned nchan_per_con=16;


/// Reset the histograms for this canvas
TTRB3Histograms::TTRB3Histograms(){  

  SetGroupName("FPGA");
  SetChannelName("Channel");
  SetNumberChannelsInGroup(NchannelPerFpga);
  CreateHistograms();
}


void TTRB3Histograms::CreateHistograms(){

  // Don't recreate if we already have histograms
  char cname[100];
  sprintf(cname,"TRB3_%i_%i",0,0);
  TH1D *cold = (TH1D*)gDirectory->Get(cname);
  if (cold) return;


  // Otherwise make histograms
  clear();
  
  std::cout << "Create Histos" << std::endl;
  for(int j = 0; j < Nfpga; j++){ // loop over FPGA    
    for(int i = 0; i < NchannelPerFpga; i++){ // loop over channels    
      
      char name[100];
      char title[100];
      sprintf(name,"TRB3_%i_%i",j,i);
      
      // Delete old histograms, if we already have them
      TH1D *old = (TH1D*)gDirectory->Get(name);
      if (old){
        delete old;
      }
      
      
      // Create new histograms
      
      sprintf(title,"TRB3 histogram for fpga=%i channel=%i",j, i);	
      
      TH1D *tmp = new TH1D(name,title,50000,0,10000000);
      tmp->SetXTitle("Hit time (ps)");
      tmp->SetYTitle("Number of Entries");
      push_back(tmp);
    }
  }

}



  
/// Update the histograms for this canvas.
void TTRB3Histograms::UpdateHistograms(TDataContainer& dataContainer){

  TTRB3DataV2 *data = dataContainer.GetEventData<TTRB3DataV2>("TRB0");
  if(!data) data = dataContainer.GetEventData<TTRB3DataV2>("TRBA");
  if(data){
    //data->Print();
    //std::cout << "Got data " << std::endl;
    
    //double reftime = 0;
    for(int i = 0; i < data->GetNumberMeasurements(); i++){
      std::vector<TrbTdcMeasV2> meas =  data->GetMeasurements();
      double time = meas[i].GetFinalTime();
      uint32_t id = meas[i].GetBoardId();
      uint32_t ch = meas[i].GetChannel();
      int hch = NchannelPerFpga*id + ch;
      //std::cout << hch << " " << id << " " << ch << " " << time << std::endl;
      GetHistogram(hch)->Fill(time);

    }

  }    

}



/// Take actions at begin run
void TTRB3Histograms::BeginRun(int transition,int run,int time){

  CreateHistograms();

}


/// Reset the histograms for this canvas
TTRB3FineHistograms::TTRB3FineHistograms(){  

  SetGroupName("FPGA");
  SetChannelName("Channel");
  SetNumberChannelsInGroup(NchannelPerFpga);
  CreateHistograms();
}


void TTRB3FineHistograms::CreateHistograms(){
  
  // Don't recreate if we already have histograms
  char cname[100];
  sprintf(cname,"TRB3_Fine_%i_%i",0,0);
  TH1D *cold = (TH1D*)gDirectory->Get(cname);
  if (cold) return;

  // Otherwise make histograms
  clear();
  
  for(int j = 0; j < Nfpga; j++){ // loop over FPGA    
    for(int i = 0; i < NchannelPerFpga; i++){ // loop over channels    
      
      char name[100];
      char title[100];
      sprintf(name,"TRB3_Fine_%i_%i",j,i);
      
      // Delete old histograms, if we already have them
      TH1D *old = (TH1D*)gDirectory->Get(name);
      if (old){
        delete old;
      }
      
      
      // Create new histograms
      
      sprintf(title,"TRB3 Fine Times for fpga=%i channel=%i",j, i);	
      
      TH1D *tmp = new TH1D(name,title,512,-0.5,511.5);
      tmp->SetXTitle("Fine Time (DC)");
      tmp->SetYTitle("Number of Entries");
      push_back(tmp);
    }
  }

}



  
/// Update the histograms for this canvas.
void TTRB3FineHistograms::UpdateHistograms(TDataContainer& dataContainer){

  for(int j = 0; j < 4; j++){
    char bankname[5];
    sprintf(bankname,"TRB%i",j);
    TTRB3DataV2 *data = dataContainer.GetEventData<TTRB3DataV2>(bankname); 
    if(!data and j == 0)  data = dataContainer.GetEventData<TTRB3DataV2>("TRBA");
    if(data){

      for(int i = 0; i < data->GetNumberMeasurements(); i++){
	std::vector<TrbTdcMeasV2> meas =  data->GetMeasurements();
	uint32_t id = meas[i].GetBoardId();
	uint32_t ch = meas[i].GetChannel();
	int hch = (j*4*64) + NchannelPerFpga*id + ch;
	GetHistogram(hch)->Fill(meas[i].GetFineTime());
      }
    }else{
    }    
  }
}



/// Take actions at begin run
void TTRB3FineHistograms::BeginRun(int transition,int run,int time){
  CreateHistograms();
}




/// Reset the histograms for this canvas
TTRB3DiffHistograms::TTRB3DiffHistograms(){  

  SetGroupName("FPGA");
  SetChannelName("Channel");
  SetNumberChannelsInGroup(NchannelPerFpga);
  fReferenceFpga = 2; 
  fReferenceCh = 14;
  
  CreateHistograms();
}


void TTRB3DiffHistograms::CreateHistograms(){

  // Don't recreate if we already have histograms
  char cname[100];
  sprintf(cname,"aTRB3_diff_%i_%i",0,0);
  TH1D *cold = (TH1D*)gDirectory->Get(cname);
  if (cold) return;
  
  // Otherwise make histograms
  clear();
  
  std::cout << "Create Histos" << std::endl;
  for(int j = 2; j < 3; j++){ // loop over FPGA    
    for(int i = 0; i < 33; i++){ // loop over channels    
      
      char name[100];
      char title[100];
      sprintf(name,"TRB3_diff_%i_%i",j,i);
      
      // Delete old histograms, if we already have them
      TH1D *old = (TH1D*)gDirectory->Get(name);
      if (old){
        delete old;
      }
      
      
      // Create new histograms
      if(i == 0){
	sprintf(title,"Hits Per Channel");	
	
	TH1D *tmp = new TH1D(name,title,32,0.5,32.5);
	tmp->SetXTitle("TRB Hit channel");
	tmp->SetYTitle("Number of Entries");
	push_back(tmp);
      }else{
	sprintf(title,"TRB3 difference histogram for fpga=%i channel=%i",j, i);	
	
	TH1D *tmp = new TH1D(name,title,400,-20,20);
	tmp->SetXTitle("Hit time (ns)");
	tmp->SetYTitle("Number of Entries");
	push_back(tmp);
      }
    }
  }

}



  
/// Update the histograms for this canvas.
void TTRB3DiffHistograms::UpdateHistograms(TDataContainer& dataContainer){

  //TTRB3DataV2 *data = dataContainer.GetEventData<TTRB3DataV2>("TRB0");
  //if(!data) data = dataContainer.GetEventData<TTRB3DataV2>("TRBA");

  char bankname[5];
  sprintf(bankname,"TRB0");
  //  std::cout << "Checking TRB0 data"<<std::endl;
  TTRB3DataV2 *data = dataContainer.GetEventData<TTRB3DataV2>(bankname); 

  
  if(data){
    
    
      
      
    
    //data->Print();
    
    // Loop over first time to find the reference time
    double reftime = 0;
    double refstime = 0;
    bool foundRef = false;
    
    double ch1_time = -1;
    double ch2_time = -1;

    if( data->GetNumberMeasurements() > 0) std::cout <<"Got TRB3 data " << data->GetNumberMeasurements() << " " << data->GetSize(); //std::endl;
    
    int numberPulses = 0;
    for(int i = 0; i < data->GetNumberMeasurements(); i++){
      std::vector<TrbTdcMeasV2> meas =  data->GetMeasurements();
      double time = meas[i].GetFinalTime();
      double stime = meas[i].GetSemiFinalTime();
      uint32_t id = meas[i].GetBoardId();
      
      uint32_t ch = meas[i].GetChannel();
      if(ch!=0) GetHistogram(0)->Fill(ch);
	
      unsigned int max_fine = 0;
      unsigned int min_fine = 99999;
      if(ch !=0){
	if(meas[i].GetFineTime() > max_fine) max_fine = meas[i].GetFineTime();
	if(meas[i].GetFineTime() < min_fine) min_fine = meas[i].GetFineTime();
	
	if(0)std::cout << std::endl << "Fine time " << meas[i].GetFineTime() << " "
		  << min_fine <<"-" << max_fine << " " << ch << std::endl;
      }
      std::cout << " " << id << "/"<< ch;
      if(id==0 and ch > 0) std::cout << "Hit for fpga = " << id << " ch=" << ch << "  total hits="<< data->GetNumberMeasurements()
				     << std::endl;
      if(id == 3 && ch == 2){
	numberPulses++;
      }
      if(fReferenceFpga == id && fReferenceCh == ch){
	reftime = time;
	refstime = stime;
	foundRef = true;
	std::cout << " ref : " << ((double)meas[i].GetFinalTime());
      }      
    }
    if( data->GetNumberMeasurements() > 0)    std::cout << std::endl;
    
    if(ch1_time > 0 and ch2_time > 0){
      std::cout << "Hit times: " << ch1_time << " " << ch2_time << "  diff=" << ch1_time-ch2_time << std::endl;
	GetHistogram(1)->Fill((ch1_time-ch2_time)/1000.0);
    }
    
    if(foundRef && 1){
      
      for(int i = 0; i < data->GetNumberMeasurements(); i++){
	std::vector<TrbTdcMeasV2> meas =  data->GetMeasurements();
	double time = meas[i].GetFinalTime();
	double stime = meas[i].GetSemiFinalTime();
	//uint32_t id = meas[i].GetBoardId() ;
	uint32_t ch = meas[i].GetChannel();
	
	//int hch = NchannelPerFpga*id + ch;
	
	if(0)std::cout << ch << " Finetime: " << meas[i].GetFineTime() << " " << (time-reftime)/1000.0
		  << " " << time << " " << reftime << std::endl;
	std::cout << ch << "Semin time" << stime << " " << refstime << " " << (stime-refstime)/1000.0<< std::endl;
	if(ch!=0) GetHistogram(ch)->Fill((stime-refstime)/1000.0);
	
      }
      
      

      
    }    
    
  }

}



/// Take actions at begin run
void TTRB3DiffHistograms::BeginRun(int transition,int run,int time){

  CreateHistograms();

}


//PMT Display Histogram Added: AS 2018
PMTDisplay::PMTDisplay(){  
  CreateHistograms();
}


/// Reset the histograms for this canvas
TTRB3DiffTrigHistograms::TTRB3DiffTrigHistograms(){  

  SetGroupName("FPGA");
  SetChannelName("Channel");
  SetNumberChannelsInGroup(NchannelPerFpga);
  fReferenceFpga = 0; 
  fReferenceCh = 0;
  
  CreateHistograms();
}



void PMTDisplay::CreateHistograms(){
  // make histograms
  clear();
  TH2D *PMTDisplayHist = new TH2D("PMTDisplay","PMTDisplay",24,-12.,12.,24,-12.,12.0);
  PMTDisplayHist->SetXTitle("x (pixels)");
  PMTDisplayHist->SetYTitle("y (pixels)");
  push_back(PMTDisplayHist);
  
}


void TTRB3DiffTrigHistograms::CreateHistograms(){
  
  // Don't recreate if we already have histograms
  char cname[100];
  sprintf(cname,"TRB3_diff_trig_%i_%i",0,0);
  TH1D *cold = (TH1D*)gDirectory->Get(cname);
  if (cold) return;

  // Otherwise make histograms
  clear();
  
  std::cout << "Create Histos" << std::endl;
  for(int j = 0; j < Nfpga; j++){ // loop over FPGA    
    for(int i = 0; i < NchannelPerFpga; i++){ // loop over channels    
      
      char name[100];
      char title[100];
      sprintf(name,"TRB3_diff_trig_%i_%i",j,i);
      
      // Delete old histograms, if we already have them
      TH1D *old = (TH1D*)gDirectory->Get(name);
      if (old){
        delete old;
      }
      
      
      // Create new histograms
      
      sprintf(title,"Triggered TRB3 difference histogram for fpga=%i channel=%i",j, i);	
      
      TH1D *tmp = new TH1D(name,title,10000,-55100,55100);
      tmp->SetXTitle("Hit time (ps)");
      tmp->SetYTitle("Number of Entries");
      push_back(tmp);
    }
  }

}

/// Update the histograms for this canvas.
void PMTDisplay::UpdateHistograms(TDataContainer& dataContainer){
  //static bool first=true;


}

/// Take actions at begin run
void PMTDisplay::BeginRun(int transition,int run,int time){

  CreateHistograms();

}









///////////////////////////////////////////////////////////////////

//PMT Display Histogram Added: AS 2018
PMTNhitsDisplay::PMTNhitsDisplay(){  
  CreateHistograms();
}



void PMTNhitsDisplay::CreateHistograms(){
  // make histograms
  clear();
  TH1D *PMTNhitsDisplayHist = new TH1D("PMTNhitsDisplay","PMTNhitsDisplay",2000,-0.5,1999.5);
  PMTNhitsDisplayHist->SetXTitle("Number of hits");
  PMTNhitsDisplayHist->SetYTitle("Counts/bin");
  push_back(PMTNhitsDisplayHist);
  
}

/// Update the histograms for this canvas.
void PMTNhitsDisplay::UpdateHistograms(TDataContainer& dataContainer){
  static int updatecounter=0;
  TTRB3DataV2 *data = dataContainer.GetEventData<TTRB3DataV2>("TRB0");
  if(!data) data = dataContainer.GetEventData<TTRB3DataV2>("TRBA");
  if(data){
    ++updatecounter;

    std::vector<TrbTdcMeasV2> meas =  data->GetMeasurements();
    int num_measurements = 0;
    for(int i = 0; i < data->GetNumberMeasurements(); ++i){      
      uint32_t ch = meas[i].GetChannel();
      if ( ch!=0 ) ++num_measurements;   // Don't count channel zero (the timing channel)
    }

    //std::cout<<"PMTNhitsDisplay updatecounter="<<updatecounter<<std::endl;
    GetHistogram(0)->Fill( num_measurements );

  }
}

/// Update the histograms for this canvas.
void TTRB3DiffTrigHistograms::UpdateHistograms(TDataContainer& dataContainer){


  TTRB3DataV2 *data = dataContainer.GetEventData<TTRB3DataV2>("TRB0");
  if(!data) data = dataContainer.GetEventData<TTRB3DataV2>("TRBA");
  if(data){






    //data->Print();

    // Loop over first time to find the reference time
    double reftime = 0;
    bool foundRef = false;
    bool foundTrig = false;
    

    int numberPulses = 0;
    for(int i = 0; i < data->GetNumberMeasurements(); i++){
      std::vector<TrbTdcMeasV2> meas =  data->GetMeasurements();
      double time = meas[i].GetFinalTime();
      uint32_t id = meas[i].GetBoardId();
      uint32_t ch = meas[i].GetChannel();
      if(id == 3 && ch == 2){
	numberPulses++;
      }
      if(fReferenceFpga == id && fReferenceCh == ch){
        reftime = time;
        foundRef = true;
	//std::cout << "Found reference hit : " << dataContainer.GetMidasEvent().GetSerialNumber() << " " 
	//<< " " << fReferenceFpga << " " << fReferenceCh 
		       //	  <<  std::endl;
      }      
      if(2 == id && 7 == ch){
	//std::cout << "Found ref2 hit : " << dataContainer.GetMidasEvent().GetSerialNumber() << " " 
	//	  <<  std::endl;
      }      
       if(2 == id && 5 == ch){
        foundTrig = true;
      }      
    }
    
    if(foundTrig){
      //bool found1 = false, found2 = false;
      for(int i = 0; i < data->GetNumberMeasurements(); i++){
	std::vector<TrbTdcMeasV2> meas =  data->GetMeasurements();
	//uint32_t id = meas[i].GetBoardId();
	//uint32_t ch = meas[i].GetChannel();
	//if(id == 2 && ch == 6) found1 = true;
	//if(id == 2 && ch == 7) found2 = true;
      }
      //      std::cout << "Trig hit : " << found1 << " " << found2 << std::endl;
    }
    
    if(foundRef && foundTrig){

      int numberPulsesF3C4 = 0;
      for(int i = 0; i < data->GetNumberMeasurements(); i++){
        std::vector<TrbTdcMeasV2> meas =  data->GetMeasurements();
        double time = meas[i].GetFinalTime();
        uint32_t id = meas[i].GetBoardId();
        uint32_t ch = meas[i].GetChannel();

        int hch = NchannelPerFpga*id + ch;
        GetHistogram(hch)->Fill(time-reftime);

        //	if(id == 2 && ch == 7) std::cout << "Diff time: " << time << " " << reftime << " " << time-reftime << std::endl;

	if(id==1 && 0)
	  std::cout << "Finetime: " << meas[i].GetFineTime() << " " << time-reftime
		    << " " << time << " " << reftime << std::endl;
        
      }
      if(numberPulsesF3C4 > 1) std::cout << "Number of pulses for FPGA 3, chan 2 is " << numberPulsesF3C4 << std::endl;


    }
    
  }    

}


/// Take actions at begin run
void PMTNhitsDisplay::BeginRun(int transition,int run,int time){

  CreateHistograms();

}
/// Take actions at begin run
void TTRB3DiffTrigHistograms::BeginRun(int transition,int run,int time){

  CreateHistograms();

}






/// Reset the histograms for this canvas
PMTNhChanDisplay::PMTNhChanDisplay(){  

  SetGroupName("PMT Nhits Channel");
  SetChannelName("Channel");
  SetNumberChannelsInGroup(NchannelPerFpga);
  CreateHistograms();
}


void PMTNhChanDisplay::CreateHistograms(){

  // Don't recreate if we already have histograms
  char cname[100];
  sprintf(cname,"PMTNhCh_%i_%i",0,0);
  TH1D *cold = (TH1D*)gDirectory->Get(cname);
  if (cold) return;


  // Otherwise make histograms
  clear();
  
  std::cout << "Create PMT Nhits each Channel Histos" << std::endl;
  for(int j = 0; j < Nfpga; j++){ // loop over FPGA    
    for(int i = 0; i < NchannelPerFpga; i++){ // loop over channels    
      
      char name[100];
      char title[100];
      sprintf(name,"PMTNhCh_%i_%i",j,i);
      
      // Delete old histograms, if we already have them
      TH1D *old = (TH1D*)gDirectory->Get(name);
      if (old){
        delete old;
      }
      
      
      // Create new histograms
      
      sprintf(title,"NHits for fpga=%i channel=%i",j, i);	
      
      TH1D *tmp = new TH1D(name,title,5,-0.5,4.5);
      tmp->SetXTitle("Nhits");
      tmp->SetYTitle("Number of Entries");
      push_back(tmp);
    }
  }

}



  
/// Update the histograms for this canvas.
void PMTNhChanDisplay::UpdateHistograms(TDataContainer& dataContainer){
  static bool first = true;
  
  TTRB3DataV2 *data = dataContainer.GetEventData<TTRB3DataV2>("TRB0");
  if(!data) data = dataContainer.GetEventData<TTRB3DataV2>("TRBA");
  if(data){
    //data->Print();
    if (first){
      first = false;
      first_time = data->GetTime();
    }
    last_time = data->GetTime();

    
    int hch_count[ Nfpga ][ NchannelPerFpga ];
    bzero( hch_count, Nfpga * NchannelPerFpga * sizeof( int ) );
    //double reftime = 0;
    for(int i = 0; i < data->GetNumberMeasurements(); i++){
      std::vector<TrbTdcMeasV2> meas =  data->GetMeasurements();
      //double time = meas[i].GetFinalTime();
      uint32_t id = meas[i].GetBoardId();
      uint32_t ch = meas[i].GetChannel();
      //int hch = NchannelPerFpga*id + ch;
      ++hch_count[ id ][ ch ];
    }
    
    for(int j = 0; j < Nfpga; ++j){ // loop over FPGA    
      for(int i = 0; i < NchannelPerFpga; ++i){ // loop over channels    
	int hch = NchannelPerFpga*j + i;
	GetHistogram( hch )->Fill( hch_count[j][i] );
      }
    }    
  }
}



/// Take actions at begin run
void PMTNhChanDisplay::BeginRun(int transition,int run,int time){
  CreateHistograms();

}

void PMTNhChanDisplay::EndRun(int transition,int run,int time){
  int running_time = last_time - first_time;
  std::cout<<"PMTNhChanDisplay::EndRun time="<<last_time
	   <<" start_time="<<first_time
	   <<" time_running="<<running_time
	   <<std::endl;
  if ( false ){ // enable this after timestamps are fixed
    for(int j = 0; j < Nfpga; ++j){ // loop over FPGA    
      for(int i = 0; i < NchannelPerFpga; ++i){ // loop over channels    
	int hch = NchannelPerFpga*j + i;
	TH1* curhist = GetHistogram( hch );
	curhist->SetYTitle("Rate (counts/s)");
      curhist->Scale( 1.0 / running_time );
      }
    }
  }
}



/// Reset the histograms for this canvas
TRB3Hits::TRB3Hits(){  

  CreateHistograms();

}

 // make histograms
void TRB3Hits::CreateHistograms(){
  clear();
  TH2D *TRB3HitsHist = new TH2D("TRB3HitsHist","TRB3 Total Hits",65,-0.5,64.5,Nfpga,-0.5,Nfpga-0.5);
  TRB3HitsHist->SetXTitle("PMT Channel");
  TRB3HitsHist->SetYTitle("FPGA");
  push_back(TRB3HitsHist);
  
}

/// Update the histograms for this canvas.
void TRB3Hits::UpdateHistograms(TDataContainer& dataContainer){
  //TTRB3DataV2 *data = dataContainer.GetEventData<TTRB3DataV2>("TRB0");
  //if(!data) data = dataContainer.GetEventData<TTRB3DataV2>("TRBA");

  for(int j = 0; j < Nfpga/4; j++){
    char bankname[5];
    sprintf(bankname,"TRB%i",j);
    TTRB3DataV2 *data = dataContainer.GetEventData<TTRB3DataV2>(bankname); 
    if(!data and j == 0)  data = dataContainer.GetEventData<TTRB3DataV2>("TRBA");
    
    if(data){
      
      for(int i=0; i < data->GetNumberMeasurements(); i++){
	std::vector<TrbTdcMeasV2> meas = data->GetMeasurements();
	uint32_t id = meas[i].GetBoardId() + j*4;
	uint32_t ch = meas[i].GetChannel();
	if(ch == 0) continue;
	if(id == 5 and ch == 20) continue;
	GetHistogram(0)->Fill(ch,id);
      }
    }
  }
}

/// Take actions at begin run
void TRB3Hits::BeginRun(int transition,int run,int time){

  CreateHistograms();

}

/// Reset the histograms for this canvas
TRB3NHits::TRB3NHits(){ 

  CreateHistograms();

}

 // make histograms
void TRB3NHits::CreateHistograms(){
  clear();
  TH2D *TRB3NHitsHist = new TH2D("TRB3NHitsHist","TRB3 Average Hits per Event",65,-0.5,64.5,Nfpga,-0.5,Nfpga-0.5);
  TRB3NHitsHist->SetXTitle("PMT Channel");
  TRB3NHitsHist->SetYTitle("FPGA");
  push_back(TRB3NHitsHist);
  
}

Double_t nEvent = 0;
/// Update the histograms for this canvas.
void TRB3NHits::UpdateHistograms(TDataContainer& dataContainer){
   //TTRB3DataV2 *data = dataContainer.GetEventData<TTRB3DataV2>("TRB0");
  //if(!data) data = dataContainer.GetEventData<TTRB3DataV2>("TRBA");

  
  for(int i = 0; i < Nfpga/4; i++){
    char bankname[5];
    sprintf(bankname,"TRB%i",i);
    TTRB3DataV2 *data = dataContainer.GetEventData<TTRB3DataV2>(bankname); 
    if(!data and i == 0)  data = dataContainer.GetEventData<TTRB3DataV2>("TRBA");

    if(data){

      nEvent++;
      for(int j=0; j < data->GetNumberMeasurements(); j++){
      std::vector<TrbTdcMeasV2> meas = data->GetMeasurements();
      uint32_t id = meas[j].GetBoardId() + i*4;
      uint32_t ch = meas[j].GetChannel();
      if(ch == 0) continue;
      if(id == 5 and ch == 20) continue;
      GetHistogram(0)->Fill(ch,id);
      }

      GetHistogram(0)->Scale(1/nEvent);

    }
  }
}

/// Take actions at begin run
void TRB3NHits::BeginRun(int transition,int run,int time){

  CreateHistograms();

}
