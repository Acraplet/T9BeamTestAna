#ifndef TNumberOfEvents_h
#define TNumberOfEvents_h

#include <string>
#include "THistogramArrayBase.h"

/// Class for making histograms of raw DT730 waveforms;
class TNumberOfEvents : public THistogramArrayBase {

public:

  TNumberOfEvents();
  virtual ~TNumberOfEvents(){};

  void UpdateHistograms(TDataContainer& dataContainer);

  /// Take actions at begin run
  //void BeginRun(int transition,int run,int time);

  /// Take actions at end run  
  //void EndRun(int transition,int run,int time);

  /// Reset the histograms; needed before we re-fill each histo.
  void Reset();
  
  void CreateHistograms();
  
  /// Take actions at begin run
  void BeginRun(int transition,int run,int time){		
    CreateHistograms();		
  }

private:

};

#endif


