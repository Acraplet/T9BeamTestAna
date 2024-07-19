#ifndef TDT730Histogram_h
#define TDT730Histogram_h

#include <string>

#include "THistogramArrayBase.h"

/// Class for making histograms of raw DT730 waveforms;
class TDT730Waveform : public THistogramArrayBase {

public:

  TDT730Waveform(std::string bankname);
  virtual ~TDT730Waveform(){};

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

  /// Getters/setters
  int GetNumSamples() { return numSamples; }
  void SetNumSamples(int nSamples) { this->numSamples = nSamples; }
  double GetNsecsPerSample() { return nanosecsPerSample; }
  void SetNanosecsPerSample(double nsecsPerSample) { this->nanosecsPerSample = nsecsPerSample; }
  double GetMilivoltsPerADC() { return milivoltsPerADC; }
  void SetMilivoltsPerADC(double mvPerADC) { this->milivoltsPerADC = mvPerADC; }

private:

  int numSamples;
  double nanosecsPerSample;
  double milivoltsPerADC;

  std::string bankID;

};



/// Class for making histograms of raw DT730 waveforms;
class TDT730WaveformInteresting : public THistogramArrayBase {

public:

  TDT730WaveformInteresting(std::string bankname);
  virtual ~TDT730WaveformInteresting(){};

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

  /// Getters/setters
  int GetNumSamples() { return numSamples; }
  void SetNumSamples(int nSamples) { this->numSamples = nSamples; }
  double GetNsecsPerSample() { return nanosecsPerSample; }
  void SetNanosecsPerSample(double nsecsPerSample) { this->nanosecsPerSample = nsecsPerSample; }
  double GetMilivoltsPerADC() { return milivoltsPerADC; }
  void SetMilivoltsPerADC(double mvPerADC) { this->milivoltsPerADC = mvPerADC; }

private:

  int numSamples;
  double nanosecsPerSample;
  double milivoltsPerADC;
  std::string bankID;

};

/// Class for making histograms of DT730 waveforms amplitudes;
class TDT730Amplitude : public THistogramArrayBase {

public:

  TDT730Amplitude(std::string bankid);
  virtual ~TDT730Amplitude(){};

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

  /// Getters/setters
  int GetNumSamples() { return numSamples; }
  void SetNumSamples(int nSamples) { this->numSamples = nSamples; }
  double GetNsecsPerSample() { return nanosecsPerSample; }
  void SetNanosecsPerSample(double nsecsPerSample) { this->nanosecsPerSample = nsecsPerSample; }
  int GetMilivoltsPerADC() { return milivoltsPerADC; }
  void SetMilivoltsPerADC(double mvPerADC) { this->milivoltsPerADC = mvPerADC; }

private:

  int numSamples;
  double nanosecsPerSample;
  double milivoltsPerADC;
  std::string bankID;

};

/// Class for making histograms of DT730 waveforms times;
class TDT730Time : public THistogramArrayBase {

public:

  TDT730Time(std::string bankid);
  virtual ~TDT730Time(){};

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

  /// Getters/setters
  int GetNumSamples() { return numSamples; }
  void SetNumSamples(int nSamples) { this->numSamples = nSamples; }
  double GetNsecsPerSample() { return nanosecsPerSample; }
  void SetNanosecsPerSample(double nsecsPerSample) { this->nanosecsPerSample = nsecsPerSample; }
  int GetMilivoltsPerADC() { return milivoltsPerADC; }
  void SetMilivoltsPerADC(double mvPerADC) { this->milivoltsPerADC = mvPerADC; }

private:

  int numSamples;
  double nanosecsPerSample;
  double milivoltsPerADC;
  std::string bankID;

};


/// Class for making histograms of DT730 waveforms amplitudes;
class TDT730Charge : public THistogramArrayBase {

public:

  TDT730Charge(std::string bankid);
  virtual ~TDT730Charge(){};

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

  /// Getters/setters
  int GetNumSamples() { return numSamples; }
  void SetNumSamples(int nSamples) { this->numSamples = nSamples; }
  double GetNsecsPerSample() { return nanosecsPerSample; }
  void SetNanosecsPerSample(double nsecsPerSample) { this->nanosecsPerSample = nsecsPerSample; }
  int GetMilivoltsPerADC() { return milivoltsPerADC; }
  void SetMilivoltsPerADC(double mvPerADC) { this->milivoltsPerADC = mvPerADC; }

private:

  int numSamples;
  double nanosecsPerSample;
  double milivoltsPerADC;
  std::string bankID;

};

/// Class for making histograms of raw DT730 waveforms;
class TDT730TOF : public THistogramArrayBase {

public:

  TDT730TOF();
  virtual ~TDT730TOF(){};

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

  /// Getters/setters
  int GetNumSamples() { return numSamples; }
  void SetNumSamples(int nSamples) { this->numSamples = nSamples; }
  double GetNsecsPerSample() { return nanosecsPerSample; }
  void SetNanosecsPerSample(double nsecsPerSample) { this->nanosecsPerSample = nsecsPerSample; }
  double GetMilivoltsPerADC() { return milivoltsPerADC; }
  void SetMilivoltsPerADC(double mvPerADC) { this->milivoltsPerADC = mvPerADC; }

private:

  int numSamples;
  double nanosecsPerSample;
  double milivoltsPerADC;
  double waveformBaseline(std::vector<double> waveform);
  double waveformMin(std::vector<double> waveform);
  double globalTiming(std::vector<double> waveform, const double baseline);
  double cfdTiming(std::vector<double> waveform, double baseline, const int global_imin, const float startp, const float endp, const float percentage);

};
#endif
