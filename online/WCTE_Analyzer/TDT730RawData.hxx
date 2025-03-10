#ifndef TDT730RawData_hxx_seen
#define TDT730RawData_hxx_seen

#include <vector>

#include "TGenericData.hxx"

/// Class for each channel measurement
/// For the definition of obscure variables see the CAEN DT730 manual (for raw (non-DPP) readout).
class RawChannelMeasurement {

  friend class TDT730RawData;

public:
  
	const int GetNSamples(){
		return  fSamples.size();
	}
	
	const int GetChannel(){ return fChan;}

	const int GetEvtNumber(){ return fEvtNumber;}
	void SetEvtNumber(int evtnum=0){ fEvtNumber = evtnum;}

	const int GetTriggerTime(){ return fTriggerTime;}
	void SetTriggerTime(int triggertime=0){ fTriggerTime = triggertime;}

        /// Get Errors
        const uint32_t GetSample(int i){
		if(i >= 0 && i < (int)fSamples.size())
			return fSamples[i];
		return 9999999;
	}

	void AddSamples(std::vector<uint32_t> Samples){
		fSamples = Samples;
	}

private:

	int fChan; // channel number

	int fEvtNumber; // event number

	uint32_t fTriggerTime; // trigger time

  /// Constructor; need to pass in header and measurement.
  RawChannelMeasurement(int chan){
		fChan = chan;
	}

	std::vector<uint32_t> fSamples;


};


/// Class to store raw data from CAEN DT730 (for raw readout, no-DPP).
class TDT730RawData: public TGenericData {

public:

  /// Constructor
  TDT730RawData(int bklen, int bktype, const char* name, void *pdata);

  void Print();

  /// Get the Vector of TDC Measurements.
  std::vector<RawChannelMeasurement>& GetMeasurements() {return fMeasurements;}

private:

  /// The overall global header for each event
  std::vector<uint32_t> fGlobalHeader;

  /// Get Event Counter
  uint32_t GetEventCounter() const {return (fGlobalHeader[2] & 0xffffff);};

  /// Get Event Size
  uint32_t GetEventSize() const {return (fGlobalHeader[0] & 0xfffffff);};

  /// Get Geographical Address
  uint32_t GetGeoAddress() const {return (fGlobalHeader[1] & 0xf8000000) >> 27 ;};

  /// Get the extended trigger time tag
  uint32_t GetTriggerTimeTag() const {return fGlobalHeader[3];};

  /// Get channel mask
  uint32_t GetChMask(){return (fGlobalHeader[1] & 0xff);};

  // We have vectors of the headers/trailers/etc, since there can be 
  // multiple events in a bank.

  /// Vector of DT730 Measurements.
  std::vector<RawChannelMeasurement> fMeasurements;

};

#endif
