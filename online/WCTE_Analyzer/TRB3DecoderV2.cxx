#include "TRB3DecoderV2.hxx"


void Trb3CalibV2::UseTRB3LinearCalibration(bool uselinear){useLinearCalibration = uselinear;};
void Trb3CalibV2::SetTRB3LinearCalibrationConstants(float low_value, float high_value){
  trb3LinearLowEnd = low_value;
  trb3LinearHighEnd = high_value;
}

// Get endian byte swapping code; use built-in code for non-MacOS Linux
#if defined(OS_LINUX) && !defined(OS_DARWIN)
#include <Byteswap.h>
#else
/* Swap bytes in 32 bit value.  */
#define R__bswap_constant_32(x) \
     ((((x) & 0xff000000) >> 24) | (((x) & 0x00ff0000) >>  8) |               \
      (((x) & 0x0000ff00) <<  8) | (((x) & 0x000000ff) << 24))
#endif

// See figure 23 of TRB3 manual for description of TRB3 packet

TrbDecoderV2::TrbDecoderV2(int bklen, void *pdata, std::string bankname, int type){
  
  fPacketSize = 0;
  fDecoding = 0;
  fBoardId = 0;
  fSeqNr = 0;
  fRunNr = 0;
  fDate = 0;
  fTime = 0;

  // Bklen should be for 32-bit words.  If type is 1 (char type),
  // then need to fix the bklen
  if(type == 1) bklen /= 4;

  uint32_t* fData = reinterpret_cast<uint32_t*>(pdata);
  
  // check for correct endian-ness; if wrong, flip.
  // fourth word is endian encoding check word
  if(!((fData[3] & 0x1) == 1 && (fData[3] & 0x80000000) == 0)){

    for(int i = 0; i < bklen; i++){

#if defined(OS_LINUX) && !defined(OS_DARWIN)
      fData[i] = __bswap_32 (fData[i]);
#else
      fData[i] = R__bswap_constant_32(fData[i]);
#endif
      
      
    }
    
  }

  if(0)  std::cout << "sizes: " << fData[2]/4 << " " << bklen << " " 
	    << type << std::endl;


//  return;


  // This is the number of words in the sub-event packet, not including this word.
  int size_subevent = fData[2]/4;
  
  // Decode sub-event ID, trigger number and trigger code!!!
  fDecoding = fData[3];
  fSubEventID = fData[4] & 0xffff;
  fTriggerWord = fData[5];
  
  
  // Loop over rest of bank
  uint32_t fpgaWord = 0, headerWord = 0;
  int pointer = 6;
  
  // We search for words that look like the FPGA header words (sub-sub-event IDs);
  // if we don't find them, break out.
  bool finished = false;
  while (!finished){
    uint32_t word = fData[pointer];
    // Look for word indicating a new FPGA
    if((word & 0x0000ffff) == 0x00000100 ||
       (word & 0x0000ffff) == 0x00000101 ||
       (word & 0x0000ffff) == 0x00000102 ||
       (word & 0x0000ffff) == 0x00000103 ||
       (word & 0x0000ffff) == 0x00000200 ||
       (word & 0x0000ffff) == 0x00000201 ||
       (word & 0x0000ffff) == 0x00000202 ||
       (word & 0x0000ffff) == 0x00000203 ||
       (word & 0x0000ffff) == 0x00000300 ||
       (word & 0x0000ffff) == 0x00000301 ||
       (word & 0x0000ffff) == 0x00000302 ||
       (word & 0x0000ffff) == 0x00000303 ||
       (word & 0x0000ffff) == 0x00000400 ||
       (word & 0x0000ffff) == 0x00000401 ||
       (word & 0x0000ffff) == 0x00000402 ||
       (word & 0x0000ffff) == 0x00000403 ){
      fpgaWord = word;
      
      int nwords_subevent = ((word & 0xffff0000) >> 16);
      
      //    std::cout << "Found header for FPGA : " << std::hex << (fpgaWord & 0xffff) << std::dec << " at " << pointer << " nwords: " << nwords_subevent<< std::endl;
      
      // next word if TDC header
      pointer++;
      headerWord = fData[pointer];
      
      uint32_t epochWord = 0;
      // Now loop over the next couple words, grabbing the TDC data
      for(int i = 0; i < nwords_subevent; i++){
	pointer++;
	uint32_t word = fData[pointer];
	// Look for the epoch counter word; use this epoch word for all subsequent TDCs...
	if((word & 0xe0000000) == 0x60000000)
	  epochWord = word;
	
	if((word & 0xe0000000) == 0x80000000){
	  uint32_t tdcWord = fData[pointer];
          
	  if((fpgaWord & 0xf) > 3 ){
	    std::cout << "TDC FPGA ID > 3?  Not possible... " << std::hex << fpgaWord << " " << headerWord 
		      << " " << tdcWord << " " << pointer << " " << size_subevent << std::dec << std::endl;
	    for(int i = 0; i < 6 ; i++)
	      std::cout << i << " 0x"<<std::hex
			<< fData[i] << std::dec << std::endl;
	  }else{
	    
	    //                std::cout << std::hex << "Adding TDC " << headerWord << " " <<  epochWord << " " << tdcWord << std::endl;
	    fMeasurements.push_back(TrbTdcMeasV2(fpgaWord, headerWord,
						 epochWord, tdcWord));
	  }
	}          
      }
      
    }else{
      // The next word isn't a sub-sub-event ID word, so break out.
      finished = true;
    }
    
    
  }
  
  
  // Go to end of sub-event; check the trailer word
  int end_packet = 2+ size_subevent -1;
  if( fData[end_packet-1] != 0x15555){
    std::cout << "TRB3 sub-event ID trailer word = " << fData[end_packet-1] << "; not expected 0x15555; bank decoding error!!!" << std::endl;
  }
  
  

}


