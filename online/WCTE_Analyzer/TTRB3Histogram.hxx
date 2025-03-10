#ifndef TTRB3Histograms_h
#define TTRB3Histograms_h

#include <string>
#include "THistogramArrayBase.h"

/// Class for making histograms of TRB3 FPGA-TDC data.
class TTRB3Histograms : public THistogramArrayBase {
 public:
  TTRB3Histograms();
  virtual ~TTRB3Histograms(){};
  
  /// Update the histograms for this canvas.
  void UpdateHistograms(TDataContainer& dataContainer);

  /// Take actions at begin run
  void BeginRun(int transition,int run,int time);

  /// Take actions at end run  
  void EndRun(int transition,int run,int time){};

private:

  void CreateHistograms();
    
};

/// Class for making histograms of TRB3 raw fine times .
class TTRB3FineHistograms : public THistogramArrayBase {
 public:
  TTRB3FineHistograms();
  virtual ~TTRB3FineHistograms(){};
  
  /// Update the histograms for this canvas.
  void UpdateHistograms(TDataContainer& dataContainer);

  /// Take actions at begin run
  void BeginRun(int transition,int run,int time);

  /// Take actions at end run  
  void EndRun(int transition,int run,int time){};

private:

  void CreateHistograms();
    
};

/// Class for making diff histograms of TRB3 FPGA-TDC data.
class TTRB3DiffHistograms : public THistogramArrayBase {
 public:
  TTRB3DiffHistograms();
  virtual ~TTRB3DiffHistograms(){};
  
  /// Update the histograms for this canvas.
  void UpdateHistograms(TDataContainer& dataContainer);

  /// Take actions at begin run
  void BeginRun(int transition,int run,int time);

  /// Take actions at end run  
  void EndRun(int transition,int run,int time){};

private:

  void CreateHistograms();

  // specify the reference FPGA and Ch
  unsigned int fReferenceFpga; 
  unsigned int fReferenceCh;
  
};

//PMT Dislay Histogram
class PMTDisplay : public THistogramArrayBase {
 public:
  PMTDisplay();
  virtual ~PMTDisplay(){};

  /// Update the histograms for this canvas.
  void UpdateHistograms(TDataContainer& dataContainer);
  
  /// Take actions at begin run
  void BeginRun(int transition,int run,int time);
  
  /// Take actions at end run  
  void EndRun(int transition,int run,int time){};
  
  private:
  
  void CreateHistograms();
  
};

/// Class for making diff histograms of TRB3 FPGA-TDC data (for particular triggered events
class TTRB3DiffTrigHistograms : public THistogramArrayBase {
 public:
  TTRB3DiffTrigHistograms();
  virtual ~TTRB3DiffTrigHistograms(){};
  
  /// Update the histograms for this canvas.
  void UpdateHistograms(TDataContainer& dataContainer);

  /// Take actions at begin run
  void BeginRun(int transition,int run,int time);

  /// Take actions at end run  
  void EndRun(int transition,int run,int time){};

private:

  void CreateHistograms();
  // specify the reference FPGA and Ch
  unsigned int fReferenceFpga;
  unsigned int fReferenceCh;
  
};



//PMT Dislay Histogram
class PMTNhitsDisplay : public THistogramArrayBase {
public:
  PMTNhitsDisplay();
  virtual ~PMTNhitsDisplay(){};
  
  /// Update the histograms for this canvas.
  void UpdateHistograms(TDataContainer& dataContainer);

  /// Take actions at begin run
  void BeginRun(int transition,int run,int time);
  
  /// Take actions at end run  
  void EndRun(int transition,int run,int time){};
  
private:
  
  void CreateHistograms();
  
};



/// Class for making histograms of 
/// number of hits on each pixel (presumably usually 0 or 1)
class PMTNhChanDisplay : public THistogramArrayBase {
 public:
  PMTNhChanDisplay();
  virtual ~PMTNhChanDisplay(){};
  
  /// Update the histograms for this canvas.
  void UpdateHistograms(TDataContainer& dataContainer);

  /// Take actions at begin run
  void BeginRun(int transition,int run,int time);

  /// Take actions at end run  
  void EndRun(int transition,int run,int time);

private:

  void CreateHistograms();

  int first_time;
  int last_time;
    
};

/// Class for making histograms of FPGA # versus PMTChannel #
class TRB3Hits : public THistogramArrayBase {
 public:
  TRB3Hits();
  virtual ~TRB3Hits(){};
  
  /// Update the histograms for this canvas.
  void UpdateHistograms(TDataContainer& dataContainer);

  /// Take actions at begin run
  void BeginRun(int transition,int run,int time);

  /// Take actions at end run  
  void EndRun(int transition,int run,int time){};

private:

  void CreateHistograms();
    
};

/// Class for making normalized histograms of FPGA # versus PMTChannel #
class TRB3NHits : public THistogramArrayBase {
 public:
  TRB3NHits();
  virtual ~TRB3NHits(){};
  
  /// Update the histograms for this canvas.
  void UpdateHistograms(TDataContainer& dataContainer);

  /// Take actions at begin run
  void BeginRun(int transition,int run,int time);

  /// Take actions at end run  
  void EndRun(int transition,int run,int time){};

private:

  void CreateHistograms();
    
};

#endif


