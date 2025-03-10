#ifndef AnaTools_h
#define AnaTools_h

#include <string>
#include <vector>

double setThreshold(int chan, std::string bankID);

double waveformBaseline(std::vector<double> waveform);

double waveformMin(std::vector<double> waveform);

double globalTiming(std::vector<double> waveform, const double baseline);

double cfdTiming(std::vector<double> waveform, double baseline, const int global_imin, const float startp, const float endp, const float percentage);

#endif
