#ifndef WcteHistogram_h
#define WcteHistogram_h

#include <string>
#include "WcteEventBuilder.h"
#include "THistogramArrayBase.h"
#include "TH1D.h"

/// Class for making histograms of WcteEvents
class WcteEventHistograms : public THistogramArrayBase {

public:

  WcteEventHistograms();
  virtual ~WcteEventHistograms(){};

  void UpdateHistograms(TDataContainer& dataContainer){};
  void UpdateHistograms(std::vector<WCTE_Event>& WcteEvent);

  /// Take actions at begin run
  //void BeginRun(int transition,int run,int time);

  /// Take actions at end run
  //void EndRun(int transition,int run,int time);

  /// Reset the histograms; needed before we re-fill each histo.
  void Reset();

  void CreateHistograms();

  /// Take actions at begin run
  void BeginRun(int transition,int run,int time){
    //CreateHistograms();
  }

  /// Getters/setters
  int GetnEvents() { return nEvents; }

private:

  int nEvents;

  int digiACT;
  int chanACT0R;
  int chanACT0L;
  int chanACT1R;
  int chanACT1L;
  int chanACT2R;
  int chanACT2L;
  int chanACT3R;
  int chanACT3L;

  int digiTOF;

  int digiLG;
  int chanLG;

  vector<int> digiHodoscope;
  vector<int> chanHodoscope;

  double GetPulseTimeLI(const std::vector<double> &wf);
  double GetPulseTimeCFD(const std::vector<double> &wf);
  double GetPulseHeight(const std::vector<double> &wf);

};

#endif
