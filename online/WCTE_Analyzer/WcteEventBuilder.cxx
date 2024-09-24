#include "WcteEventBuilder.h"
#include "TDT730RawData.hxx"
#include "TTRB3DataV2.hxx"
#include "AnaTools.h"

#include <algorithm> 
#include <cmath>
#include <numeric>

#ifdef HAVE_MIDAS
#include "midas.h"
#endif

bool debug = false;

const std::vector<std::string> DataFragment::banknames = {"D300", "D301", "D302", "D303", "TRB0"};
std::vector<unsigned int> lastEvt(5,0);  // for detecting skips
unsigned int lastNCompleted = 1e6;
unsigned int incNCompleted = 1e6;
int invalidCt = 0;

WcteEventBuilder::WcteEventBuilder(): fTotalCompletedEvents(0), fSpillCompletedEvents(0), fSpillNumber(0), fTotalBadSpills(0) {

  fEnabled[0] = true;
  fEnabled[1] = true;
  fEnabled[2] = true;
  fEnabled[3] = true;
  fEnabled[4] = false;

  fDataFragments.resize(5);
  fDiscardedFragments.resize(5,0);

  fEvtNumbers.resize(5,0);
  fBankNEvts.resize(5);

  fLastDataTimestamp = 0;
};



// Add any event fragments from current MIDAS event to internal buffers
int WcteEventBuilder::AddEventFragments(TDataContainer& dataContainer){

  // Get the event ID and timestamp  
  int timestamp = dataContainer.GetMidasData().GetTimeStamp();

  for(int index = 0; index < 4; index++) {

    if(!fEnabled[index]) continue;

    TDT730RawData *dt730 = dataContainer.GetEventData<TDT730RawData>(DataFragment::banknames[index].c_str());
    
    if(dt730) {     

      std::vector<RawChannelMeasurement> measurements = dt730->GetMeasurements();

      // Create a pointer to a DT5730_Fragment object
      DT5730_Fragment * fragment = NULL;

      // Keep track of the number of events in the bank.
      unsigned int nevts_bank = 0;

      // Keep track of the current event number we are constructing
      unsigned int current_event = -1;
      
      for(unsigned int i = 0; i < measurements.size(); i++) {

        //std::cout << "index = " << index << ", number of measurements = " << measurements.size() << std::endl;
      
        int chan = measurements[i].GetChannel();
        int nsamples = measurements[i].GetNSamples();
        unsigned int eventid = measurements[i].GetEvtNumber();
        uint32_t triggertime = measurements[i].GetTriggerTime();

        // Save the old fragment object if we are on a new event.
        if(eventid != current_event) {

          // Only save events if we have a non-null fragment object (it's not the first event).
          if(fragment) {

            // Add the object to the fragments vector in the event builder
            fDataFragments[index].push_back(fragment);
            nevts_bank++;  // Add an event to the event bank counter
          }

          // Create a new fragment
          fragment = new DT5730_Fragment();
          fragment->setIndex(index);
          fragment->setTimestamp(timestamp);
          fragment->setTriggerTime(triggertime);
          //fragment->setEventNumber(eventid); // use hardware event/trigger number
          fragment->setEventNumber(fEvtNumbers[index]++);
        }

        // Set the current event to the current eventid.
        current_event = eventid;

        //std::cout << "index = " << index << ", channel = " << chan << ", nsamples = " 
        //          << nsamples << " Event ID = " << measurements[i].GetEvtNumber() << std::endl;
        // Print a message if we have skipped 1 or more events.
        if(chan == 0) {
          if(!(eventid == lastEvt[index] || eventid == lastEvt[index] + 1)) {
            invalidCt++;
            std::cout << "Skipped event(s): last event = " << lastEvt[index] << " and current event = " << eventid << std::endl;
          }
          lastEvt[index] = eventid;
        }
      
        // check if the channel is enabled for reading
        if (fragment->canReadOut(chan)) {

          std::vector<double> adcValues;
      
          // process all samples
          for(int ib = 0; ib < nsamples; ib++){
            double adc = measurements[i].GetSample(ib);
            adcValues.push_back(adc); // store the sample in adcValues
          }
      
          // set the waveform for the current channel
          fragment->setWaveform(chan, adcValues);
        }
      }

      // Save the last fragment if it exists.
      if(fragment) {

        // Add the object to the fragments vector in the event builder
        fDataFragments[index].push_back(fragment);
        nevts_bank++;  // Add an event to the event bank counter
      }

      // Record the number of events in this bank
      fBankNEvts[index].push_back(nevts_bank);

    } // end of if(dt730)

  } // end of loop over DT5730 elements

  // Process the TRB3 fragments
  if(fEnabled[4]) {

    TTRB3DataV2 *trb3 = dataContainer.GetEventData<TTRB3DataV2>(DataFragment::banknames[4].c_str());

    if(trb3) {

      // One event per bank for the TRB3, and using sequence nr as event number.
      uint32_t eventid = trb3->GetDecoder().GetTriggerNumber();
      std::vector<TrbTdcMeasV2> measurements = trb3->GetMeasurements();


      // Create a TRB3_Fragment object
      TRB3_Fragment * fragment = new TRB3_Fragment();
      fragment->setIndex(4);
      fragment->setTimestamp(timestamp);
      //fragment->setEventNumber(eventid); // use hardware trigger/event number
      fragment->setEventNumber(fEvtNumbers[4]++);

      // Print a message if we have skipped 1 or more events.
      if(!(eventid == lastEvt[4] || eventid == lastEvt[4] + 1)) {
        invalidCt++;
        std::cout << "Skipped event(s): last event = " << lastEvt[4] << " and current event = " << eventid << std::endl;
      }
      lastEvt[4] = eventid;

      for(unsigned int i = 0; i < measurements.size(); i++) {

        //std::cout << "TRB3 channel = " << measurements[i].GetChannel() << "; TDC = " << measurements[i].GetMeasurement() << std::endl;
         
        // Set the measurement values.
        TRB3_Measure measure; 
        measure.setBoardId(measurements[i].GetBoardId());
        measure.setTdcMeasurement(measurements[i].GetMeasurement());
        measure.setFinalTime(measurements[i].GetFinalTime());
        measure.setSemiFinalTime(measurements[i].GetSemiFinalTime());
        measure.setFineTime(measurements[i].GetFineTime());
        measure.setCoarseTime(measurements[i].GetCoarseTime());
        measure.setEpochCounter(measurements[i].GetEpochCounter());
        measure.setChannel(measurements[i].GetChannel());

        // Add the measurement to the fragment.
        fragment->addMeasurement(measure);
      }

      // Add the object to the fragments vector in the event builder
      fDataFragments[4].push_back(fragment);

    } // end of if(trb3)

  } // end of fEnabled[4]

  return 0;
}



// Check for completed events
bool WcteEventBuilder::CheckCompleteEvents() {

    //if(debug) PrintFragmentArrays();

    //std::cout << "Finding min event number... " << std::endl;
    // Get the lowest event number for the last element of each array.
    int min_evtnum = -1;
    //int min_module = -1;
    bool empty = false;  // set to true if an enabled fragment vector is empty

    for(int i = 0; i < 5; i++) {
      if(fEnabled[i] && !empty) {
        int evtnum = -1;
        if(fDataFragments[i].size() > 0)
          evtnum = fDataFragments[i].back()->getEventNumber();
        else if(fDataFragments[i].size() == 0)
          empty = true;

        if(min_evtnum < 0 || evtnum < min_evtnum) {
          //min_module = i;
          min_evtnum = evtnum;
        }
      }
    }
    if(debug) std::cout << "Min event number is " << min_evtnum << std::endl;

    // Return false if there is at least one enabled fragments vector that is empty.
    // In this case, no events can be matched, but we must wait for more fragments.
    if(empty) {
      if(debug) std::cout << "At least 1 enabled fragments array is empty: waiting for more fragments..." << std::endl;
      return false;
    }

    // Match all events up to the minimum event at the end of all fragment arrays.
    std::map<int, std::vector<DataFragment*>> eventMap;
    std::vector<int> matched_counts(5, 0);
    std::vector<int> erased_counts(5, 0);

    // Loop through the digitizer fragments and add them to the map up to the minimum event number
    for(unsigned int i=0; i<fDataFragments.size(); i++) {

      if(fEnabled[i]) {

        std::vector<DataFragment*>& fragments = fDataFragments[i];
        unsigned int nfragments = fragments.size();
        if(debug) std::cout << "Looping through digitizer fragments for i = " << i << " with size = " << nfragments << std::endl;

        // Add all fragments with event number less than or equal to min_evtnum.
        if(nfragments > 0) {
          unsigned int ifragment = 0;
          int evtnum = fragments[ifragment]->getEventNumber();

          // If we have at least 1 event to be processed (<= min_evtnum), continue.
          if(evtnum <= min_evtnum) { 
          
            while(evtnum < min_evtnum && ifragment < nfragments) {
              eventMap[evtnum].push_back(fragments[ifragment]);
              ifragment++;
              if(ifragment < nfragments)
                evtnum = fragments[ifragment]->getEventNumber();
            }

            // If we have reached min_evtnum, push the event onto the event map.
            if(evtnum == min_evtnum && ifragment < nfragments) {
              eventMap[evtnum].push_back(fragments[ifragment]);
            }

            // Remove all fragments with event number less than min_evtnum.
            if(ifragment > 0) {
              fragments.erase(fragments.begin(), fragments.begin() + ifragment);
              erased_counts[i] += ifragment;
              if(debug) std::cout << "-- Erased " << ifragment << " counts" << std::endl;
            }
          }
        }
      }
    }

    // now loop through the events and create WCTE_Event instances for complete events
    for(auto & pair : eventMap) {
      int event_number = pair.first;
      auto & data_fragments = pair.second;

      // check if we have a fragment from each enabled DT5730 and TRB3
      std::vector<int> module_counts(5, 0);
      for(auto & fragment : data_fragments) {
        module_counts[fragment->getIndex()]++;
      }

      bool complete = true;
      for(int i=0; i<5; i++) {
        if(fEnabled[i] && module_counts[i] != 1) {
          complete = false;
          break;
        }
      }

      if(complete) {
        // construct the event and add to the list
        WCTE_Event wcte_event;
        wcte_event.SetEventNumber(event_number);
        wcte_event.SetSpillNumber(GetSpillNumber());
        wcte_event.SetDataFragments(data_fragments);
        //std::cout << "Pushing back event with spill number " << GetSpillNumber() << std::endl;
        fCompletedEvents.push_back(wcte_event);

        // increase matched counts
        for(auto & fragment : data_fragments) {
            matched_counts[fragment->getIndex()]++;
        }

        // If this is the min event number, we need to erase the 0th element of all enabled vectors.
        if(event_number == min_evtnum) {
          for(int i=0; i<5; i++) {
            if(fEnabled[i]) {
              fDataFragments[i].erase(fDataFragments[i].begin());
              erased_counts[i] += 1;
            }
          }
        }
      }
    } // end of loop through eventMap

    // Add the unmatched fragments
    for(int i = 0; i < 5; i++) {
      if(fEnabled[i]) { 
        fDiscardedFragments[i] += (erased_counts[i] - matched_counts[i]);
      }
    }

    // Add the completed events to the total numbers of completed events.
    //fTotalCompletedEvents += matched_counts[0]; //fCompletedEvents.size();
    fSpillCompletedEvents += matched_counts[0]; //fCompletedEvents.size();

    // Print report
    unsigned int ncompleted = GetTotalCompletedEvents();
    unsigned int ncompleted_spill = GetSpillCompletedEvents();
    if(debug || (ncompleted > lastNCompleted)) {
      lastNCompleted = ncompleted+incNCompleted;
      std::cout << "**************************************************************************\n";
      std::cout << "Enabled flags set to true:";
      for(int i=0; i<5; i++)
          if(fEnabled[i])
              std::cout << " " << i;
      std::cout << "\n";
      std::cout << "Total number of completed events before this spill: " << ncompleted << std::endl;
      std::cout << "Completed events in this loop: " << matched_counts[0] << std::endl;
      std::cout << "Number of completed events in this spill: " << ncompleted_spill << std::endl;
      for(int i=0; i<5; i++) {
        if(fEnabled[i]) {
          std::cout << "Total erased fragments for module " << i << ": " << fDiscardedFragments[i] << std::endl;
          std::cout << "Erased fragments for module " << i << ": " << erased_counts[i] << std::endl;
          std::cout << "Matched fragments for module " << i << ": " << matched_counts[i] << std::endl;
        }
      }
      for(int i=0; i<5; i++) {
        if(fEnabled[i]) {
          unsigned int nremaining = 0;
          nremaining = fDataFragments[i].size();
          std::cout << "Remaining fragments for module " << i << ": " << nremaining << std::endl;
        }
      }
      std::cout << "**************************************************************************\n";
    }

    if(debug && fCompletedEvents.size() > 0) {
      std::cout << "Last matched event " << fCompletedEvents[fCompletedEvents.size()-1].GetEventNumber() << std::endl;
    }

    // Check for any unmatched fragments in this call
    for(int i=0; i<5; i++) {
        if(fEnabled[i] && (erased_counts[i] - matched_counts[i]) != 0)
            return false; // return false if any fragments were unmatched
    }

    return true; // return true if all fragments were matched
}

// Reset the event numbers for each module.
void WcteEventBuilder::ResetEvtNumbers() {
  fEvtNumbers.resize(5,0);
  for(int i = 0; i < 5; i++ ) fEvtNumbers[i] = 0;
}

// Reset the number of events per bank.
void WcteEventBuilder::ResetBankNEvts() {
  for(int i = 0; i < 5; i++ ) fBankNEvts[i].clear();
}

// Reset the total number of events.
void WcteEventBuilder::ResetTotalCompletedEvents() {
  fTotalCompletedEvents = 0;
}

// Reset the spill number of events.
void WcteEventBuilder::ResetSpillCompletedEvents() {
  fSpillCompletedEvents = 0;
}

// Clear all completed events.
void WcteEventBuilder::ClearCompletedEventsVector() {
  for(auto evt : fCompletedEvents) {

    // Get the DataFragments array to be cleaned
    std::vector<DataFragment*> & data_fragments = evt.GetDataFragments();
    
    // Delete the objects in the DataFragments array
    for (auto ptr : data_fragments) {
      if(ptr != NULL) delete ptr;
    }
  }
  fCompletedEvents.clear();
}

// Clear the arrays of fragments.
void WcteEventBuilder::ClearFragments() {
  for(auto& data_fragment_vector : fDataFragments) {
    for (auto ptr : data_fragment_vector) { delete ptr; }
    data_fragment_vector.clear();
  }
}

// Get the vector of completed events.
std::vector<WCTE_Event> & WcteEventBuilder::GetCompletedEvents() { return fCompletedEvents; }

void WcteEventBuilder::PrintFragmentArrays() {

  // Loop over the data fragments and print.
  for (unsigned int i = 0; i < fDataFragments.size(); i++) {
    std::cout << "\nFragment array for module " << i << ":" << std::endl;
    for (const auto& fragment : fDataFragments[i]) {
      std::cout << " " << fragment->getEventNumber();
    }
  }
}

// Print statistics for the current spill.
void WcteEventBuilder::SpillStats() {

  std::cout << "***************************************************************************" << std::endl;
  std::cout << "SPILL " << GetSpillNumber() << " SUMMARY" << std::endl;
  std::cout << "***************************************************************************" << std::endl;
  std::cout << "Enabled flags set to true:";
  for(int i=0; i<5; i++) {
    if(fEnabled[i]) std::cout << " " << i;
  }
  std::cout << std::endl;

  std::cout << "Total number of completed events before this spill: " << GetTotalCompletedEvents() << std::endl;
  std::cout << "Number of completed events in this spill: " << GetSpillCompletedEvents() << std::endl;

  for(int i = 0; i < 5; i++) {
    if (!fEnabled[i]) {
        continue;
    }

    std::cout << "Digitizer " << i << std::endl;
    if (fBankNEvts[i].size()>0) {
      double sum = std::accumulate(fBankNEvts[i].begin(), fBankNEvts[i].end(), 0.0);
      double mean = sum / fBankNEvts[i].size();
    
      double sq_sum = std::inner_product(fBankNEvts[i].begin(), fBankNEvts[i].end(), fBankNEvts[i].begin(), 0.0);
      double stdev = sum / std::sqrt(sq_sum / fBankNEvts[i].size() - mean * mean);
    
      auto minmax = std::minmax_element(fBankNEvts[i].begin(), fBankNEvts[i].end());

      std::cout << "--> Mean number of events per bank: " << mean << std::endl;
      std::cout << "--> Std dev of events per bank: " << stdev << std::endl;
      std::cout << "--> Min events per bank: " << *minmax.first << std::endl;
      std::cout << "--> Max events per bank: " << *minmax.second << std::endl;
    }
    else {
      std::cout << "--> Mean number of events per bank: 0" << std::endl;
      std::cout << "--> Std dev of events per bank: 0" << std::endl;
      std::cout << "--> Min events per bank: 0" << std::endl;
      std::cout << "--> Max events per bank: 0" << std::endl;
    }
  }
  
  bool missing_events = false;
  int missed_events[5];
  for(int i=0; i<5; i++) {
    if(fEnabled[i]) {
      std::cout << "Unmatched fragments for module " << i << ": " << fDataFragments[i].size(); 

      if(fDataFragments[i].size() > 0){ missing_events = true; }
      missed_events[i] = fDataFragments[i].size();
	
      // print the event numbers of the first 5 unmatched fragments
      std::string eventNumbers = " [";
      for(unsigned int j=0; j<5 && j<fDataFragments[i].size(); j++) {
        eventNumbers += std::to_string(fDataFragments[i][j]->getEventNumber());
        if(j < 4 && j<fDataFragments[i].size()-1) eventNumbers += ", ";
      }
      eventNumbers += fDataFragments[i].size() > 5 ? ", ..." : "";
      eventNumbers += "]";
      std::cout << eventNumbers << std::endl;
    }
    else {
      missed_events[i] = 0;
    }
  }
  std::cout << "**************************************************************************" << std::endl;

  // Tabulate bad spill or completed events
  if(missing_events) { 
    AddBadSpill();
  }
  else {
    fTotalCompletedEvents += GetSpillCompletedEvents();
  }

#ifdef HAVE_MIDAS
  if(missing_events){
    cm_msg(MERROR,"eventbuilder","Event building failed for spill %i; [%i/%i good spills, %i total good events]; %i complete events, but missing event fragments [%i,%i,%i,%i,%i]",GetSpillNumber(),GetSpillNumber()+1-GetNumberOfBadSpills(),GetSpillNumber()+1,GetTotalCompletedEvents(),GetSpillCompletedEvents(),
	   missed_events[0],missed_events[1],missed_events[2],missed_events[3],missed_events[4]);
  }else{
    cm_msg(MINFO,"eventbuilder","Event building succeeded for spill %i; [%i/%i good spills, %i total good events]; %i complete events",GetSpillNumber(),GetSpillNumber()+1-GetNumberOfBadSpills(),GetSpillNumber()+1,GetTotalCompletedEvents(),GetSpillCompletedEvents());

  }
#endif

  
}


// Returns the total number of fragments missed.
unsigned int WcteEventBuilder::GetNumberOfMissedFragments() {

  unsigned int missed_fragments = 0;
  for(int i=0; i<5; i++) {
    if(fEnabled[i]) {
      missed_fragments += fDataFragments[i].size();
    }
  }
  return missed_fragments;
}

// Check for unmatched event fragments and delete any unused fragments
// return false if there was any unused fragments
// print a report to screen and to MIDAS log
//bool WcteEventBuilder::CheckUnmatchedFragments(){
//  return false;
//}

// Check whether it's been more than 3 seconds since last receiving data
bool WcteEventBuilder::CheckEndOfSpill(TDataContainer& dataContainer){
  // Get the timestamp
  int thisTimestamp = dataContainer.GetMidasData().GetTimeStamp();
  // Check each bank for data
  bool hasData = false;
  for(int index = 0; index < 4; index++) {
    if(!fEnabled[index]) continue;
    TDT730RawData *dt730 = dataContainer.GetEventData<TDT730RawData>(DataFragment::banknames[index].c_str());
    if(dt730){
      hasData = true;
      break;
    }
  }
  // if it has data, update clock
  if(hasData){
    fLastDataTimestamp = thisTimestamp;
  }
  // if clock has ever been updated, but was more than 3 seconds ago, it's the end of the spill
  else if(fLastDataTimestamp && (thisTimestamp - fLastDataTimestamp > 3)){
    // reset the clock before receiving next spill data
    fLastDataTimestamp = 0;
    return true;
  }
  // otherwise it's not the end of the spill
  return false;
}
