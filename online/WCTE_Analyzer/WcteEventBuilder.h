#ifndef wcteEventBuilder_h
#define wcteEventBuilder_h

#include <string>
#include <array>
#include <vector>
#include <map>
#include "TDataContainer.hxx"

// Class for storing data from a DT5730 event fragment (ie data from single DT5730 for single trigger)
#include <vector>

class DataFragment {
public:
  DataFragment(): index(-1), eventNumber(-1), timestamp(-1) {}
  virtual ~DataFragment() {}  // Make the destructor virtual to allow for dynamic casting

  void setIndex(int idx) {
    if (idx >= 0 && idx <= 4) {
      index = idx;
    }
    else {
      std::cerr << "Invalid index: setting to 0" << std::endl;
      index = 0;
    }
  }

  void setEventNumber(int en) { eventNumber = en; }
  void setTimestamp(int ts) { timestamp = ts; }
  void setTriggerTime(int tt) { triggertime = tt; }

  int getIndex() const { return index; }
  int getEventNumber() const { return eventNumber; }
  int getTimestamp() const { return timestamp; }
  uint32_t getTriggerTime() const { return triggertime; }

  // The bank names for all DT5730 digitizers
  static const std::vector<std::string> banknames;

private:
  int index;
  int eventNumber;
  int timestamp;
  uint32_t triggertime;
};

class DT5730_Fragment: public DataFragment {
public:
  DT5730_Fragment() {
    waveforms.resize(8); // Reserving space for 8 channels
    readOutChannel.resize(8, true); // Initially, no channel is set for readout
  }

  void setReadOut(int channel) {
    if (channel >= 0 && channel <= 7) {
      readOutChannel[channel] = true;
    }
    // else handle error...
  }

  void setWaveform(int channel, std::vector<double> wf) {
    if (channel >= 0 && channel <= 7) {
      waveforms[channel] = wf;
    }
    // else handle error...
  }

  bool canReadOut(int channel) const {
    if (channel >= 0 && channel <= 7) {
      return readOutChannel[channel];
    }
    else return false;
  }

  std::vector<double> getWaveform(int channel) const {
    if (channel >= 0 && channel <= 7) {
      return waveforms[channel];
    }
    else {
      std::cerr << "ERROR: invalid channel in getWaveform, returning wavform from channel 0" << std::endl;
      return waveforms[0];
    }
  }

private:
  std::vector<bool> readOutChannel;
  std::vector<std::vector<double>> waveforms;
};

class TRB3_Measure {

public:
  TRB3_Measure(): boardId(0), tdcMeasurement(0), finalTime(0.0), semiFinalTime(0.0), fineTime(0), coarseTime(0), epochCounter(0), channel(0) {
  }

  void setBoardId(uint32_t id) { boardId = id; }
  void setTdcMeasurement(uint32_t measurement) { tdcMeasurement = measurement; }
  void setFinalTime(double time) { finalTime = time; }
  void setSemiFinalTime(double time) { semiFinalTime = time; }
  void setFineTime(uint32_t time) { fineTime = time; }
  void setCoarseTime(uint32_t time) { coarseTime = time; }
  void setEpochCounter(uint32_t counter) { epochCounter = counter; }
  void setChannel(uint32_t ch) { channel = ch; }

  uint32_t getBoardId() const { return boardId; }
  uint32_t getTdcMeasurement() const { return tdcMeasurement; }
  double   getFinalTime() const { return finalTime; }
  double   getSemiFinalTime() const { return semiFinalTime; }
  uint32_t getFineTime() const { return fineTime; }
  uint32_t getCoarseTime() const { return coarseTime; }
  uint32_t getEpochCounter() const { return epochCounter; }
  uint32_t getChannel() const { return channel; }

private:

  uint32_t boardId;
  uint32_t tdcMeasurement;
  double   finalTime;
  double   semiFinalTime;

  uint32_t fineTime;
  uint32_t coarseTime;
  uint32_t epochCounter;
  uint32_t channel;

};

// Class for storing data from a TRB3 event fragment (ie data from TRB3 for single trigger)
class TRB3_Fragment: public DataFragment {
// FPGA, header, epoch, measurement
// /home/wcte/online/trb3_frontend/analyzer: save all private elements in TRB3DecoderV2.hxx
public:
  TRB3_Fragment() { setIndex(4); };

  // Add a measurement.
  void addMeasurement(TRB3_Measure& measure) {
    measurements.push_back(measure);
  }

  // Get the total number of measurements. 
  unsigned int getNMeasurements() { return measurements.size(); }

  // Get a specific measurement.
  TRB3_Measure getMeasurement(int m) { return measurements[m]; }

  // Clear all measurements.
  void clearMeasurements() { measurements.clear(); } 

private:

  std::vector<TRB3_Measure> measurements;  
};


// class for storing completed WCTE events (probably just a list of DT5730_Fragment and TRB3_Fragment objects)
class WCTE_Event {
public:
  WCTE_Event(): eventNumber(0) {}
  ~WCTE_Event() {

    // Delete the objects in the DataFragments array
    //for (auto ptr : data_fragments) {
    //  if(ptr != NULL) delete ptr;
    //}
  }

  // getters
  std::vector<DataFragment*>& GetDataFragments() { return data_fragments; }
  unsigned int GetEventNumber() { return eventNumber; }
  unsigned int GetSpillNumber() { return spillNumber; }
  unsigned int GetTimeStamp(int index) {
    for(auto &data_fragment : data_fragments) {
      // first, check if the fragment index matches the requested digitizer index
      if(data_fragment->getIndex() == index) {
        // attempt to cast the data_fragment to a DT5730_Fragment
        DT5730_Fragment * dt5730_fragment = dynamic_cast<DT5730_Fragment*>(data_fragment);
        // if the dynamic_cast is successful, it means that the fragment is indeed of type DT5730_Fragment
        if(dt5730_fragment != NULL) {
          //std::cout << "CAST SUCCESSFUL" << std::endl;
          // if the channel can be read out, return the waveform
          //if(dt5730_fragment->canReadOut(channel)) {
            //std::cout << "GOT WAVEFORM CH " << channel << std::endl;
            return dt5730_fragment->getTimestamp();
          //}
        }
      }
    }
    // if no suitable fragment found, return 0
    return 0;
  }
  uint32_t GetTriggerTime(int index) {
    for(auto &data_fragment : data_fragments) {
      // first, check if the fragment index matches the requested digitizer index
      if(data_fragment->getIndex() == index) {
        // attempt to cast the data_fragment to a DT5730_Fragment
        DT5730_Fragment * dt5730_fragment = dynamic_cast<DT5730_Fragment*>(data_fragment);
        // if the dynamic_cast is successful, it means that the fragment is indeed of type DT5730_Fragment
        if(dt5730_fragment != NULL) {
          //std::cout << "CAST SUCCESSFUL" << std::endl;
          // if the channel can be read out, return the waveform
          //if(dt5730_fragment->canReadOut(channel)) {
            //std::cout << "GOT WAVEFORM CH " << channel << std::endl;
            return dt5730_fragment->getTriggerTime();
          //}
        }
      }
    }
    // if no suitable fragment found, return 0
    return 0;
  }
  std::vector<double> GetDigitizerWaveform(int index, int channel) {
    for(auto &data_fragment : data_fragments) {
      // first, check if the fragment index matches the requested digitizer index
      if(data_fragment->getIndex() == index) {
        // attempt to cast the data_fragment to a DT5730_Fragment
        DT5730_Fragment * dt5730_fragment = dynamic_cast<DT5730_Fragment*>(data_fragment);
        // if the dynamic_cast is successful, it means that the fragment is indeed of type DT5730_Fragment
        if(dt5730_fragment != NULL) {
          //std::cout << "CAST SUCCESSFUL" << std::endl;
          // if the channel can be read out, return the waveform
          if(dt5730_fragment->canReadOut(channel)) {
            //std::cout << "GOT WAVEFORM CH " << channel << std::endl;
            return dt5730_fragment->getWaveform(channel);
          }
        }
      }
    }
    // if no suitable fragment found, return an empty vector
    return std::vector<double>{};
  }

  // setters
  void SetDataFragments(const std::vector<DataFragment*>& fragments) { data_fragments = fragments;}
  void SetEventNumber(unsigned int event_number) { eventNumber = event_number; }
  void SetSpillNumber(unsigned int spill_number) { spillNumber = spill_number; }

private:
  std::vector<DataFragment*> data_fragments;
  unsigned int eventNumber;
  unsigned int spillNumber;
};


/// Class for storing event fragments from different equipment and then building events
/// For each MIDAS event, the event builder will
/// i) Add new event fragments  (AddEventFragments)
/// ii) Build any complete events; complete = have fragments from each enabled equipment (CheckCompleteEvents)
/// The event builder will then pass the new set of completed events to any other process that wants to analyze the completed events (GetCompletedEvents)
/// The event builder will also have a method for checking how many unmatched event fragments we have and throwing out unmatched; will
/// somehow call this method after spill is finished...
class WcteEventBuilder {

public:
  WcteEventBuilder();

  int AddEventFragments(TDataContainer& dataContainer);
  bool CheckCompleteEvents();
  void AnalyzeEvents();

  void SetEnabled(int i, bool enabled) { fEnabled[i] = enabled; }

  unsigned int GetTotalCompletedEvents() { return fTotalCompletedEvents; }
  unsigned int GetSpillCompletedEvents() { return fSpillCompletedEvents; }
  unsigned int GetSpillNumber()          { return fSpillNumber;          }
  unsigned int GetNumberOfBadSpills()    { return fTotalBadSpills;       }
  unsigned int GetNumberOfMissedFragments();

  // Methods for resetting and clearing
  void ResetEvtNumbers();
  void ResetBankNEvts();
  void ResetTotalCompletedEvents();
  void ResetSpillCompletedEvents();
  void ResetSpillNumber() { fSpillNumber = 0; }
  void ResetBadSpills()   { fTotalBadSpills = 0; }
  void ClearCompletedEventsVector();
  void ClearFragments();

  // Print methods
  void PrintFragmentArrays();
  void SpillStats();

  // Spill methods
  void AddSpill() { fSpillNumber++; }
  void AddBadSpill() { fTotalBadSpills++; }
  bool CheckEndOfSpill(TDataContainer& dataContainer);

  // Direct access to the array of completed events
  std::vector<WCTE_Event> & GetCompletedEvents();

private:

  // Let's have an enable flag for each equipment
  // fEnabled[0-3]: DT5730 0-3
  // fEnabled[4]: TRB3
  bool fEnabled[5];
  unsigned int fTotalCompletedEvents;
  unsigned int fSpillCompletedEvents;
  unsigned int fSpillNumber;
  unsigned int fTotalBadSpills;

  std::vector<unsigned int> fEvtNumbers;
  std::vector<std::vector<unsigned int>> fBankNEvts;

  // Need some internal arrays of event fragments
  std::vector< std::vector< DataFragment* > > fDataFragments;
  //std::vector< TRB3_Fragment > fTRB3_Fragments;

  // Array of recently completed events
  std::vector<WCTE_Event> fCompletedEvents;

  // Number of discarded fragments
  std::vector<int> fDiscardedFragments;

  // Keep track of when the last data was received
  int fLastDataTimestamp;
};

#endif


