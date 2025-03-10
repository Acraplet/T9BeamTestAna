/***************************************************************************/
/*                                                                         */
/*  Filename: OdbDT5743.h                                                   */
/*                                                                         */
/*  Function: headerfile for a single DT5743 module                         */
/*                                                                         */
/* ----------------------------------------------------------------------- */
/*                                                                         */
/***************************************************************************/

#ifndef  ODBDT5743_INCLUDE_H
#define  ODBDT5743_INCLUDE_H

typedef struct {
  DWORD record_length;
  DWORD trigger_source;         // 0x810C@[31.. 0]
  DWORD sw_trigger; 
  DWORD dac[8];                 // 0x1n98@[15.. 0]
  DWORD post_trigger_percent;
} DT5743_CONFIG_SETTINGS;

#define DT5743_CONFIG_SETTINGS_STR(_name) const char *_name[] = {\
"record length = DWORD : 64",\
"trigger source = DWORD : 0xffffffff",\
"software trigger = DWORD : 0",\
"dac = DWORD[8] : ",\
"[0] 0x7fff",\
"[1] 0x7fff",\
"[2] 0x7fff",\
"[3] 0x7fff",\
"[4] 0x7fff",\
"[5] 0x7fff",\
"[6] 0x7fff",\
"[7] 0x7fff",\
"post_trigger_percent = DWORD : 50",\
NULL }
#endif  //  ODBDT5743_INCLUDE_H
