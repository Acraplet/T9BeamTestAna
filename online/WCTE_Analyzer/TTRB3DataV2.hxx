#ifndef TTRB3DataV2_hxx_seen
#define TTRB3DataV2_hxx_seen

#include <vector>

#include "TGenericData.hxx"
#include "TRB3DecoderV2.hxx"


/// Container for data packets from TRB3.
/// Uses the TRB3Decoder class.
class TTRB3DataV2: public TGenericData {

public:

  /// Constructor
  TTRB3DataV2(int bklen, int bktype, const char* name, void *pdata);

  void Print();

  const int GetNumberMeasurements(){return decoder.GetNumberMeasurements();}
  
  /// Get the Vector of TDC Measurements.
  std::vector<TrbTdcMeasV2>& GetMeasurements() {return decoder.GetMeasurements();}

  /// Get Packet size
  const uint32_t GetPacketSize(){return decoder.GetPacketSize();}
  // Get sequence number
  const uint32_t GetSeqNr(){return decoder.GetSeqNr();}
  // Get run number
  const uint32_t GetRunNr(){return decoder.GetRunNr();};
  // Get year
  const uint32_t GetYear(){return decoder.GetYear();};
  // Get month
  const uint32_t GetMonth(){return decoder.GetMonth();};
  // Get day
  const uint32_t GetDay(){return decoder.GetDay();};
  // Get time; seconds since when???
  const uint32_t GetTime(){return decoder.GetTime();};;
  
  /// Get decoder
  TrbDecoderV2& GetDecoder() {return decoder;}

  
private:

  /// Vector of TDC Measurements.
  std::vector<TrbTdcMeasV2> fMeasurements;

  TrbDecoderV2 decoder;
  
};

#endif
