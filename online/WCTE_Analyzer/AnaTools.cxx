#include "AnaTools.h"

double setThreshold(int chan, std::string bankID){

  // Use a special threshold for ACT0
  // 2.5mV threshold for most channels, 100mV threshold for ACT0
  double threshold = 2.5;
  if(bankID== "00" and (chan == 0 or chan == 1)){ threshold = 100.0;}
  return threshold;

}

double waveformMin(std::vector<double> waveform){
	/*
	Find minimum of a waveform.
	*/

  double ymin = 99999999.;
  int nsamples = waveform.size();
  for (int k = 0; k < nsamples; k++){
    if (waveform.at(k) < ymin) {
      ymin = waveform.at(k);
    }
  }
  return ymin;
}

double waveformBaseline(std::vector<double> waveform){
	/*
	Find baseline of a waveform.
	*/

  // find waveform minimum position
  int imin = 0;
  double ymin = 99999999.;
  int nsamples = waveform.size();
  for (int k = 0; k < nsamples; k++){
    if (waveform.at(k) < ymin) {
      ymin = waveform.at(k);
      imin = k;
    }
  }

  // find baseline using samples
  // outside +/-25 window around waveform minimum
  double sample_sum = 0.;
  int count = 0;
  int waveform_size = waveform.size();

  for (int k=0; k<waveform_size; k++) {
    if (abs(k-imin)>25) {
      sample_sum += waveform.at(k);
      count++;
    }
  }
  //std::cout << "baseline samples " << count << std::endl;

  return sample_sum/double(count);
}

double globalTiming(std::vector<double> waveform, const double baseline) {
	/*
	Find global minimum of a vector of double values.
	*/

  double ymin = 99999999.;
  int imin = 0;
  int nsamples = waveform.size();
  for (int k = 0; k < nsamples; k++){
    if (waveform.at(k) < ymin) {
        ymin = waveform.at(k);
        imin = k;
    }
  }
  //std::cout << "min pos " << imin << " min adc " << ymin << std::endl;
  return (double)imin;
}

double cfdTiming(std::vector<double> waveform, 
                 double baseline,
                 const int global_imin,
                 const float startp,
                 const float endp,
                 const float percentage) {
	/* 
  Find timing of pulse through constant-fraction discriminator.  
	*/ 
  double y_min = waveform.at(global_imin)-baseline;
  double y_end = endp*y_min;
  double y_start = startp*y_min;
  double rise_amplitude = (endp-startp)*y_min;

  int j = global_imin;
  int j_end = 0;
  while (((waveform.at(j)-baseline) < y_end) && (j > 1)) {
      j--;
      j_end = j-1;
  }

  j = global_imin;
  int j_start = 0;
  while (((waveform.at(j)-baseline) < y_start) && (j > 1)) {
      j--;
      j_start = j+1;
  }

  //std::cout << "j start " << j_start << " end " << j_end << std::endl;
  //std::cout << "y start " << y_start << " end " << y_end << std::endl;

  if (j_end-j_start!=0) {
    double b = (y_end-y_start)/(double(j_end)-double(j_start));
    double a = y_start - j_start*b;
    return (percentage*rise_amplitude-a)/b;
  } 
  else {
    return j_end;
  }
}
