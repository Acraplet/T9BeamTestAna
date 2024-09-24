/********************************************************************\

Trivial frontend that creates a trivial event every 0.5seconds, 
so that analyzer always has something to process

T. Lindner, July 2023

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

#define  EQ_NAME   "TimeKeeper"
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

// VMEIO definition

/* make frontend functions callable from the C framework */

/*-- Globals -------------------------------------------------------*/

/* The frontend name (client name) as seen by other MIDAS clients   */
const char *frontend_name = "fetimekeeper";
/* The frontend file name, don't change it */
const char *frontend_file_name = (char*)__FILE__;

/* frontend_loop is called periodically if this variable is TRUE    */
BOOL frontend_call_loop = FALSE;

/* a frontend status page is displayed with this frequency in ms */
INT display_period = 000;

/* maximum event size produced by this frontend */
INT max_event_size = 32 * 34000;

/* maximum event size for fragmented events (EQ_FRAGMENTED) */
INT max_event_size_frag = 5 * 1024 * 1024;

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
struct timeval te;


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

  { EQ_NAME,                 /* equipment name */
    {
      EQ_EVID, EQ_TRGMSK,     /* event ID, trigger mask */
      "SYSTEM",              /* event buffer */
      EQ_PERIODIC ,      /* equipment type */
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
  return SUCCESS;
}

/*-- Frontend Exit -------------------------------------------------*/
INT frontend_exit()
{
  printf("End of exit\n");
  return SUCCESS;
}




/*-- Begin of Run --------------------------------------------------*/
INT begin_of_run(INT run_number, char *error)
{

  return SUCCESS;
}

/*-- End of Run ----------------------------------------------------*/
INT end_of_run(INT run_number, char *error)
{

  
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
    uint32_t Data = 0;
    //int ret;
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

  
   uint32_t *pddata;
   //   uint32_t sn = SERIAL_NUMBER(pevent);

   // Create event header
   bk_init32(pevent);


   char bank_name[20];
   sprintf(bank_name,"TIME");
   bk_create(pevent, bank_name, TID_DWORD, (void**)&pddata);// cast to void (arturo 25/11/15) 

   // copy data into event
   *pddata++ = 0xdeadbeef;

   bk_close(pevent, pddata);	

   return bk_size(pevent);

    

}
 

