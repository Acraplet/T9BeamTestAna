#include "TDT730RawData.hxx"
#include <bitset>

TDT730RawData::TDT730RawData(int bklen, int bktype, const char* name, void *pdata):
    TGenericData(bklen, bktype, name, pdata)
{
  
  int counter = 0;
  int nevents_per_block = 0;
  int mem_block_size = 0;

  fGlobalHeader.push_back(0);
  fGlobalHeader.push_back(0);
  fGlobalHeader.push_back(0);
  fGlobalHeader.push_back(0);

  // Read events until reaching midas bank size
  while ( mem_block_size<bklen ){

    //std::cout << "header 0 " << std::bitset<32>(GetData32()[counter+0]) << std::endl;
    //std::cout << "header 1 " << std::bitset<32>(GetData32()[counter+1]) << std::endl;
    //std::cout << "header 2 " << std::bitset<32>(GetData32()[counter+2]) << std::endl;
    //std::cout << "header 3 " << std::bitset<32>(GetData32()[counter+3]) << std::endl;

    // Do some sanity checking.  
    // Make sure first word has right identifier
    if( (GetData32()[counter+0] & 0xf0000000) != 0xa0000000){
      std::cerr << "First word has wrong identifier; first word = 0x"
                //<< std::hex << GetData32()[counter+0] << std::dec << std::endl;
                << std::bitset<32>(GetData32()[counter+0]) << std::endl;
      return;
    }

    // Read header and advance counter
    fGlobalHeader[0] = GetData32()[counter++];
    fGlobalHeader[1] = GetData32()[counter++];
    fGlobalHeader[2] = GetData32()[counter++];
    fGlobalHeader[3] = GetData32()[counter++];

    int number_available_channels = 0;
    for(int ch = 0; ch < 8; ch++){
      if((1<<ch) & GetChMask()){
        number_available_channels++;
      }
    }
    //std::cout << "Number of channels " << number_available_channels << std::endl;

    int nwords_per_channel = (GetEventSize() - 4)/number_available_channels;
    //std::cout << "Number of words per channel " << nwords_per_channel << std::endl;

    // Loop over channel data
    for(int ch = 0; ch < 8; ch++){

      if((1<<ch) & GetChMask()){

        std::vector<uint32_t> Samples;
        for(int i = 0; i < nwords_per_channel; i++){
          uint32_t sample = (GetData32()[counter] & 0x3fff);
          Samples.push_back(sample);
          sample = (GetData32()[counter] & 0x3fff0000) >> 16;
          Samples.push_back(sample);
          counter++;
        }
        RawChannelMeasurement meas = RawChannelMeasurement(ch);
        meas.SetEvtNumber(GetEventCounter());
        meas.SetTriggerTime(GetTriggerTimeTag());
        meas.AddSamples(Samples);

        fMeasurements.push_back(meas);

      }
    }

    mem_block_size+=GetEventSize();
    nevents_per_block++;

  }

  if (mem_block_size!=bklen) {
    std::cerr << "Memory block is different than midas event size" << std::endl;
    std::cerr << "Memory block size " << mem_block_size << std::endl;
    std::cerr << "Size of midas event "  << bklen << std::endl;
  }

  //std::cout << "Number of events in memory block " << nevents_per_block << std::endl;

}

void TDT730RawData::Print(){

  std::cout << "DT730 decoder for bank " << GetName().c_str() << std::endl;


}
