/********************************************************************\

Frontend program for getting waveforms from CAEN DT5743
Using SAMLONG SCA chip

We make calls to the CAEN digitizer library routines in order to 
setup the digitizer.  So this frontend requires the CAENDigitizer
libraries be installed.

T. Lindner, Dec 2019

  $Id$
\********************************************************************/
#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include "midas.h"
#include "mfe.h"
#include "unistd.h"
#include "time.h"
#include "sys/time.h"

#include "OdbDT5730.h"

// CAEN includes
#include <CAENDigitizer.h>

#define  EQ_NAME   "DT5730_"
#define  EQ_EVID   1
// #define  EQ_TRGMSK 0x0100
#define  EQ_TRGMSK 0x1111

#define CAEN_USE_DIGITIZERS

/* Globals */
#define N_DT5743 1

/* Hardware */
extern HNDLE hDB;
extern BOOL debug;

HNDLE hSet[N_DT5743];
DT5743_CONFIG_SETTINGS tsvc[N_DT5743];
const char BankName[N_DT5743][5]={"30FS"};
const char BankNameSlow[N_DT5743][5]={"30SL"};
char bank_name[20];

/* make frontend functions callable from the C framework */

/*-- Globals -------------------------------------------------------*/

/* The frontend name (client name) as seen by other MIDAS clients   */
const char *frontend_name = "feDT5730_";
/* The frontend file name, don't change it */
const char *frontend_file_name = (char*)__FILE__;

/* frontend_loop is called periodically if this variable is TRUE    */
BOOL frontend_call_loop = FALSE;

/* a frontend status page is displayed with this frequency in ms */
INT display_period = 000;

/* maximum event size produced by this frontend */
INT max_event_size = 32 * 340000;

/* maximum event size for fragmented events (EQ_FRAGMENTED) */
INT max_event_size_frag = 5 * 1024 * 1024*10;

/* buffer size to hold events */
INT event_buffer_size = 2 * max_event_size + 10000;

/* VME base address */
int   dt5743_handle[N_DT5743];

int  linRun = 0;
int  done=0, stop_req=0;

// handle to CAEN digitizer;
int handle;

//time_t rawtime;
//struct tm *timeinfo;
//struct timeval te;

/*-- Function declarations -----------------------------------------*/
INT frontend_init();
INT frontend_exit();
INT begin_of_run(INT run_number, char *error);
INT end_of_run(INT run_number, char *error);
INT pause_run(INT run_number, char *error);
INT resume_run(INT run_number, char *error);
INT frontend_loop();
extern void interrupt_routine(void);
INT read_trigger_event(char *pevent, INT off);
INT read_slow_event(char *pevent, INT off);

/*-- Equipment list ------------------------------------------------*/
#undef USE_INT
EQUIPMENT equipment[] = {

  { EQ_NAME "%02d",                 /* equipment name */
    {
      EQ_EVID, EQ_TRGMSK,     /* event ID, trigger mask */
      "SYSTEM",              /* event buffer */
      EQ_POLLED ,      /* equipment type */
      LAM_SOURCE(0, 0x8111),     /* event source crate 0, all stations */
      "MIDAS",                /* format */
      TRUE,                   /* enabled */
      RO_RUNNING,             /* read only when running */
      500,                    /* poll for 500ms */
      0,                      /* stop run after this event limit */
      0,                      /* number of sub events */
      0,                      /* don't log history */
      "", "", "",
    },
    read_trigger_event,       /* readout routine */
  },
  {""}
};



/********************************************************************\
              Callback routines for system transitions

  These routines are called whenever a system transition like start/
  stop of a run occurs. The routines are called on the following
  occations:

  frontend_init:  When the frontend program is started. This routine
                  should initialize the hardware.

  frontend_exit:  When the frontend program is shut down. Can be used
                  to releas any locked resources like memory, commu-
                  nications ports etc.

  begin_of_run:   When a new run is started. Clear scalers, open
                  rungates, etc.

  end_of_run:     Called on a request to stop a run. Can send
                  end-of-run event and close run gates.

  pause_run:      When a run is paused. Should disable trigger events.

  resume_run:     When a run is resumed. Should enable trigger events.
\********************************************************************/

/********************************************************************/

/*-- Sequencer callback info  --------------------------------------*/
void seq_callback(INT hDB, INT hseq, void *info)
{
  KEY key;

  printf("odb ... Settings %x touched\n", hseq);
  for (int b=0;b<N_DT5743;b++) {
    if (hseq == hSet[b]) {
      db_get_key(hDB, hseq, &key);
      printf("odb ... Settings %s touched\n", key.name);
    }
  }
}

INT initialize_for_run();

/*-- Frontend Init -------------------------------------------------*/
INT frontend_init()
{
  int size, status;
  char set_str[80];

  // Suppress watchdog for PICe for nowma
  cm_set_watchdog_params(FALSE, 0);

  //  setbuf(stdout, NULL);
  //  setbuf(stderr, NULL);
  printf("begin of Init\n");
  /* Book Setting space */
  DT5743_CONFIG_SETTINGS_STR(dt5743_config_settings_str);

  sprintf(set_str, "/Equipment/DT5730_%02i/Settings/DT5730S",get_frontend_index());
  status = db_create_record(hDB, 0, set_str, strcomb(dt5743_config_settings_str));
  status = db_find_key (hDB, 0, set_str, &hSet[0]);
  if (status != DB_SUCCESS) cm_msg(MINFO,"FE","Key %s not found", set_str);

  /* Enable hot-link on settings/ of the equipment */
  size = sizeof(DT5743_CONFIG_SETTINGS);
  if ((status = db_open_record(hDB, hSet[0], &(tsvc[0]), size, MODE_READ, seq_callback, NULL)) != DB_SUCCESS)
    return status;

  // Open connection to digitizer
  CAEN_DGTZ_ErrorCode ret;

  //ret = CAEN_DGTZ_OpenDigitizer(CAEN_DGTZ_USB, 0 /*link num*/, 0, 0 /*base addr*/, &handle);
  //ret = CAEN_DGTZ_OpenDigitizer(CAEN_DGTZ_USB, 0 /*link num*/, 0,  0x81110000 , &handle);
  printf("OpenDigitizer use link: %d\n", 1+get_frontend_index());
  ret = CAEN_DGTZ_OpenDigitizer(CAEN_DGTZ_USB, 1+get_frontend_index() , 0,  0 , &handle);
  printf("OpenDigitizer ret: %d\n", ret);
  printf("DT5730S handle: %i\n", handle);

  if(ret){
    cm_msg(MERROR, "frontend_init", "cannot open dt5730");
    return 0;
  }else{
    cm_msg(MINFO, "frontend_init", "successfully opened digitizer");		
  }
  
  CAEN_DGTZ_BoardInfo_t BoardInfo;
  ret = CAEN_DGTZ_GetInfo(handle, &BoardInfo);
  if (ret) {
    cm_msg(MERROR, "frontend_init", "error getting info");
    
  }
  
  cm_msg(MINFO, "frontend_init", "Connected to CAEN Digitizer Model %s", BoardInfo.ModelName);
  printf("ROC FPGA Release is %s\n", BoardInfo.ROC_FirmwareRel);
  printf("AMC FPGA Release is %s\n", BoardInfo.AMC_FirmwareRel);
  printf("Serial Number is %i\n", BoardInfo.SerialNumber);

  // Check that we have the right serial number for each digitizer
  if(get_frontend_index() == 0 and BoardInfo.SerialNumber != 14834 ){
    cm_msg(MERROR, "frontend_init", "Frontend index 0 expecting board serial number 14384, but actual serial number  %i. Exit", BoardInfo.SerialNumber);
    return 0;
  }

  if(get_frontend_index() == 1 and BoardInfo.SerialNumber != 14452 ){
    cm_msg(MERROR, "frontend_init", "Frontend index 1 expecting board serial number 14452,but actual serial number  %i. Exit", BoardInfo.SerialNumber);
    return 0;
  }

  if(get_frontend_index() == 2 and BoardInfo.SerialNumber != 14016 ){
    cm_msg(MERROR, "frontend_init", "Frontend index 2 expecting board serial number 14016, but actual serial number  %i. Exit", BoardInfo.SerialNumber);
    return 0;
  }

  if(get_frontend_index() == 3 and BoardInfo.SerialNumber != 14453 ){
    cm_msg(MERROR, "frontend_init", "Frontend index 3 expecting board serial number 14453, but actual serial number  %i. Exit", BoardInfo.SerialNumber);
    return 0;
  }

  sprintf(bank_name,"D30%i",get_frontend_index());

  // If a run is going, start the digitizer running
  int state = 0; 
  size = sizeof(state); 
  db_get_value(hDB, 0, "/Runinfo/State", &state, &size, TID_INT, FALSE); 
  

  if (state == STATE_RUNNING) 
    initialize_for_run();
  
  //--------------- End of Init cm_msg debug ----------------
  
  set_equipment_status(equipment[0].name, "Initialized", "#00ff00");
  
  //exit(0);
  printf("end of Init\n");
  return SUCCESS;
}

/*-- Frontend Exit -------------------------------------------------*/
INT frontend_exit()
{
  printf("End of exit\n");
  return SUCCESS;
}

char *gBuffer = NULL;

INT initialize_for_run(){
  
  printf("Initializing digitizer for running\n");
  
  // Reset digitizer
  CAEN_DGTZ_ErrorCode ret;
  ret = CAEN_DGTZ_Reset(handle);
  if (ret != 0) {
    printf("Error: Unable to reset digitizer.\nPlease reset digitizer manually then restart the program\n");
    return -1;
  }
  
  int module = 0;
  int status;
  
  // Get ODB settings
  int size = sizeof(DT5743_CONFIG_SETTINGS);
  if ((status = db_get_record (hDB, hSet[module], &tsvc[module], &size, 0)) != DB_SUCCESS)
    return status;
  
  // Set the record length
  ret = CAEN_DGTZ_SetRecordLength(handle, tsvc[module].record_length);
  if(ret != 0) printf("Error setting record length: %i %i\n",ret,tsvc[module].record_length);

  // Set the post-trigger size
  ret = CAEN_DGTZ_SetPostTriggerSize(handle, (uint32_t)tsvc[module].post_trigger_percent);
  if(ret != 0) printf("Error setting post trigger: %i, %i, %i \n",handle, ret, tsvc[module].post_trigger_percent);

  // Set the DC offset
  for(int i = 0; i < 8; i++){
    ret = CAEN_DGTZ_SetChannelDCOffset(handle,i,(uint32_t)tsvc[module].dac[i]);
    if(ret != 0 && ret != -17 ) printf("Error setting DAC: %i\n",ret);
  }

  // Set the channel mask (all channels enabled)
  ret = CAEN_DGTZ_SetChannelEnableMask(handle, 0xff);  
  if(ret != 0) printf("Error setting channel enable: %i\n",ret);

  // Set number of events per transfer block
  ret = CAEN_DGTZ_SetMaxNumEventsBLT(handle,50);
  if(ret != 0) printf("Error setting max number of events per transfer block: %i\n",ret);
  sleep(3);
  
  // set acquisition mode
  ret = CAEN_DGTZ_SetAcquisitionMode(handle, CAEN_DGTZ_SW_CONTROLLED);
  if(ret != 0) printf("Error setting Acq Mode: %i\n",ret);

  // disable the software  trigger
  ret = CAEN_DGTZ_SetSWTriggerMode(handle, CAEN_DGTZ_TRGMODE_DISABLED);
  if(ret != 0) printf("Error setting software trigger input mode: %i\n",ret);

  // enable the external trigger and use it to generate trigger output (GPO)
  ret = CAEN_DGTZ_SetExtTriggerInputMode(handle, CAEN_DGTZ_TRGMODE_ACQ_AND_EXTOUT);
  if(ret != 0) printf("Error setting external trigger input mode: %i\n",ret);
  
  // Use NIM IO for trigger in.
  //CAEN_DGTZ_WriteRegister(handle,0x811c,0x0);
  
  // Use TTL IO for trigger in.
  CAEN_DGTZ_WriteRegister(handle,0x811c,0x1);

  printf("Check values on DT5730S: \n");

  uint32_t val;

  CAEN_DGTZ_ReadRegister(handle,0x8100,&val);
	printf("Acquisition control settings = 0x%x\n",val); 
	printf("Trigger counting mode = 0x%x\n",val & 0x8); 

  CAEN_DGTZ_GetRecordLength(handle,&val);
  printf("Record length: %i\n",val);

  CAEN_DGTZ_GetPostTriggerSize(handle,&val);
  printf("Post-trigger size: %i\n",val);

  for(int i = 0; i < 8; i++){
    CAEN_DGTZ_GetChannelDCOffset(handle,i,&val);
    printf("Channel%i DC offset: %i\n",i,val);
  }
  
  for(int i = 0; i < 8; i++){
    CAEN_DGTZ_ReadTemperature(handle,i,&val);
    printf("Channel%i temperature: %i\n",i,val);
  }
  
  CAEN_DGTZ_ReadRegister(handle,0x800C,&val);
	printf("Number of buffers per channel = 0x%x\n",val); 

  CAEN_DGTZ_ReadRegister(handle,0x810c,&val);
	printf("Global trigger mask value = 0x%x\n",val); 

  CAEN_DGTZ_ReadRegister(handle,0x8110,&val);
	printf("GPO enable mask = 0x%x\n",val); 
  
  // Free buffer memory if allocated
  if(gBuffer!=NULL){
    printf("Freeing previously allocated readout buffer\n");
    ret = CAEN_DGTZ_FreeReadoutBuffer(&gBuffer);
    if(ret != 0) printf("Failed to free readout buffer: %i\n",ret);
    gBuffer = NULL;
  }

  // Allocate buffer memory.
  // WARNING: This malloc must be done after the digitizer programming
  uint32_t AllocatedSize;
  ret = CAEN_DGTZ_MallocReadoutBuffer(handle, &gBuffer,&AllocatedSize);
  if(ret != 0) printf("Failed to allocate readout buffer: %i\n",ret);
  
  printf("Allocated buffer size (bytes) = %i\n",AllocatedSize);
  
  // Start the acquisition
  CAEN_DGTZ_SWStartAcquisition(handle);
  
  return ret;
}


/*-- Begin of Run --------------------------------------------------*/
INT begin_of_run(INT run_number, char *error)
{


  initialize_for_run();

  //------ FINAL ACTIONS before BOR -----------
  printf("End of BOR\n");
  //sprintf(stastr,"GrpEn:0x%x", tsvc[0].group_mask); 
  set_equipment_status("feVeto", "BOR", "#00FF00");                                                                        
  return SUCCESS;
}

/*-- End of Run ----------------------------------------------------*/
INT end_of_run(INT run_number, char *error)
{

  printf("EOR\n");

  // Read temperatures
  uint32_t val;
  for(int i = 0; i < 8; i++){
    CAEN_DGTZ_ReadTemperature(handle,i,&val);
    printf("Channel%i temperature: %i\n",i,val);
  }

	// Stop acquisition
	CAEN_DGTZ_SWStopAcquisition(handle);
  
  return SUCCESS;
}

/*-- Pause Run -----------------------------------------------------*/
INT pause_run(INT run_number, char *error)
{
  linRun = 0;
  return SUCCESS;
}

/*-- Resume Run ----------------------------------------------------*/
INT resume_run(INT run_number, char *error)
{
  linRun = 1;
  return SUCCESS;
}

/*-- Frontend Loop -------------------------------------------------*/
INT frontend_loop()
{

  /* if frontend_call_loop is true, this routine gets called when
     the frontend is idle or once between every event */
  char str[128];
  static DWORD evlimit;

  if (stop_req && done==0) {
    db_set_value(hDB,0,"/logger/channels/0/Settings/Event limit", &evlimit, sizeof(evlimit), 1, TID_DWORD); 
    if (cm_transition(TR_STOP, 0, str, sizeof(str), BM_NO_WAIT, FALSE) != CM_SUCCESS) {
      cm_msg(MERROR, "feodeap", "cannot stop run: %s", str);
    }
    linRun = 0;
    done = 1;
    cm_msg(MERROR, "feodeap","feodeap Stop requested");
  }
  return SUCCESS;
}

/*------------------------------------------------------------------*/
/********************************************************************\
  Readout routines for different events
\********************************************************************/
int Nloop, Ncount;

/*-- Trigger event routines ----------------------------------------*/
 INT poll_event(INT source, INT count, BOOL test)
/* Polling routine for events. Returns TRUE if event
   is available. If test equals TRUE, don't return. The test
   flag is used to time the polling */
{
  int i;  // , mod=-1;
  int lam = 0;

  for (i = 0; i < count; i++) {
    
    // Read the correct register to check number of events stored on digitizer.
    uint32_t Data;
    int ret;
    ret = CAEN_DGTZ_ReadRegister(handle,0xEF04,&Data); // redout status register : 0th bit =1 : event ready
    if(ret){
      printf("Failed to read event ready flag\n");
    }
    // printf("Read Register value %i \n", Data);
    //if(Data%2 == 1) lam = 1;'
    
    //    int val = Data & 0x4;
    if(Data & 0x1) lam = 1;
    // ret = CAEN_DGTZ_ReadRegister(handle,0x812c,&Data);
    // printf("Read Register value %i \n", ret);
    // if(Data > 0) lam = 1;
    
    //    ss_sleep(1);
    //usleep(10);
    if (lam) {
      Nloop = i; Ncount = count;
      if (!test){
        return lam;
      }
    }
  }
  return 0;
}

/*-- Interrupt configuration ---------------------------------------*/
 INT interrupt_configure(INT cmd, INT source, POINTER_T adr)
{
  switch (cmd) {
  case CMD_INTERRUPT_ENABLE:
    break;
  case CMD_INTERRUPT_DISABLE:
    break;
  case CMD_INTERRUPT_ATTACH:
    break;
  case CMD_INTERRUPT_DETACH:
    break;
  }
  return SUCCESS;
}

/*-- Event readout -------------------------------------------------*/
int vf48_error = 0;
#include <stdint.h>
INT read_trigger_event(char *pevent, INT off)
{
  
  //uint32_t Data; // added from 5724
  //CAEN_DGTZ_ReadRegister(handle,0x812c,&Data);
  //printf("Number of events stored before = %i\n",Data); 

  // Get number of events in buffer
  uint32_t buffsize;
  
  int ret =  CAEN_DGTZ_ReadData(handle, CAEN_DGTZ_SLAVE_TERMINATED_READOUT_MBLT, gBuffer, &buffsize);
  if(ret){
    printf("Failed to read data,\n");
  }
  
   uint32_t * words = (uint32_t*)gBuffer;
  //  printf("0x%x 0x%x 0x%x 0x%x\n",words[0],words[1],words[2],words[3]);

   uint32_t *pddata;
   //   uint32_t sn = SERIAL_NUMBER(pevent);

   // Create event header
   bk_init32(pevent);
   bk_create(pevent, bank_name, TID_DWORD, (void**)&pddata);// cast to void (arturo 25/11/15) 

   // copy data into event
   int buffsize_32 = buffsize/4; // Calculate number of 32-bit words
   //printf("buffer size %i\n",buffsize_32);
   for(int i = 0; i < buffsize_32; i++){
     *pddata++ = words[i];
    //  printf("  data[%i] = 0x%x\n",i,words[i]);
   }

   bk_close(pevent, pddata);	

   return bk_size(pevent);
    
}
