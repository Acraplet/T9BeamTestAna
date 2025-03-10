#include "TAnaManager.hxx"
#include "TDT730Histogram.h"
#include "TNumberOfEvents.h"
#include "TTRB3Histogram.hxx"
#include "WcteEventHistograms.hxx"
#include "TDT730RawData.hxx"


TAnaManager::TAnaManager(){

  AddHistogram(new TNumberOfEvents());
  AddHistogram(new TDT730Waveform("00"));
  AddHistogram(new TDT730Waveform("01"));
  AddHistogram(new TDT730Waveform("02"));
  AddHistogram(new TDT730Waveform("03"));
  AddHistogram(new TDT730WaveformInteresting("00"));
  AddHistogram(new TDT730WaveformInteresting("01"));
  AddHistogram(new TDT730WaveformInteresting("02"));
  AddHistogram(new TDT730WaveformInteresting("03"));
  AddHistogram(new TDT730Amplitude("00"));
  AddHistogram(new TDT730Amplitude("01"));
  AddHistogram(new TDT730Amplitude("02"));
  AddHistogram(new TDT730Amplitude("03"));
  AddHistogram(new TDT730Time("00"));
  AddHistogram(new TDT730Time("01"));
  AddHistogram(new TDT730Time("02"));
  AddHistogram(new TDT730Time("03"));
  AddHistogram(new TDT730Charge("00"));
  AddHistogram(new TDT730Charge("01"));
  AddHistogram(new TDT730Charge("02"));
  AddHistogram(new TDT730Charge("03"));
  //AddHistogram(new TTRB3DiffHistograms());
  AddHistogram(new WcteEventHistograms());
  fEventBuilder = new WcteEventBuilder();
};


void TAnaManager::AddHistogram(THistogramArrayBase* histo) {

  histo->DisableAutoUpdate();
  //histo->CreateHistograms();
  fHistos.push_back(histo);

}


int TAnaManager::ProcessMidasEvent(TDataContainer& dataContainer){

  // Fill all the  histograms
  for (unsigned int i = 0; i < fHistos.size(); i++) {
    // Some histograms are very time-consuming to draw, so we can
    // delay their update until the canvas is actually drawn.
    if (!fHistos[i]->IsUpdateWhenPlotted()) {
      fHistos[i]->UpdateHistograms(dataContainer);
    }
  }

  // Add event fragments to event builder
  fEventBuilder->AddEventFragments(dataContainer);
  
  // Check for completed events
  fEventBuilder->CheckCompleteEvents();


  // Routine to check if more than 3seconds since we got digitizer data.
  // if >3s then do a spill check and delete any unmatched fragments
  if(fEventBuilder->CheckEndOfSpill(dataContainer)){

    if(fEventBuilder->GetNumberOfMissedFragments()==0){
      // Analyze all full events
      ((WcteEventHistograms*)fHistos[fHistos.size()-1])->UpdateHistograms(fEventBuilder->GetCompletedEvents());
    }

    fEventBuilder->ClearCompletedEventsVector();// delete all full events
    fEventBuilder->SpillStats();
    fEventBuilder->ClearFragments();
    fEventBuilder->ResetSpillCompletedEvents();
    fEventBuilder->ResetEvtNumbers();
    fEventBuilder->AddSpill();
  }

  return 1;

}


// Little trick; we only fill the transient histograms here (not cumulative), since we don't want
// to fill histograms for events that we are not displaying.
// It is pretty slow to fill histograms for each event.
void TAnaManager::UpdateTransientPlots(TDataContainer& dataContainer){
  std::vector<THistogramArrayBase*> histos = GetHistograms();
  
  for (unsigned int i = 0; i < histos.size(); i++) {
    if (histos[i]->IsUpdateWhenPlotted()) {
      histos[i]->UpdateHistograms(dataContainer);
    }
  }
}


