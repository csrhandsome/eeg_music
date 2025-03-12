#ifndef CHIMES_H
#define CHIMES_H
#include "Arduino.h"

enum waveform
{
	SINE, //Sinus
	RECT, //Triangle
	TRI,  //Rectangle
	PAUSE //Internal, do not use
};
#define MAX_VOLUME 32

namespace Chimes
{
void init(uint8_t waveform = SINE, uint8_t duty_cycle = 50, uint8_t *envelope = NULL);
void play(uint16_t freq, uint16_t duration);

//Returns true while note is playing
boolean isPlaying();
} // namespace Chimes

#endif
