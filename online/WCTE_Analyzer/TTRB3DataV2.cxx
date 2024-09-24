#include "TTRB3DataV2.hxx"

#include <iostream>



TTRB3DataV2::TTRB3DataV2(int bklen, int bktype, const char* name, void *pdata):
  TGenericData(bklen, bktype, name, pdata), decoder(bklen,pdata,std::string(name),bktype)
{
  

};

void TTRB3DataV2::Print(){

  std::cout << "TRB3 decoder for bank " << GetName().c_str() << std::endl;
  std::cout << "Packet size: " << GetPacketSize() << std::endl;
  std::cout << "Seq Number/Run Number: " << GetSeqNr()
            << "/" << GetRunNr() << std::endl;
  std::cout << "Date: " << GetYear() << "/" << GetMonth() << "/" << GetDay() << std::endl;
  std::cout << "Time: " << GetTime() << std::endl;  
  std::cout << "Number of measurements: " << GetNumberMeasurements()
            << std::endl;

}
