#include "chimes.h"
using namespace Chimes;
//Sum of ADSR values must not exceed 100%
uint8_t envelope[] = {
	0,  //attack[%]
	20, //decay[%]
	0,  //sustain[%]
	80, //release[%]
	16  //Sustain Level 1..32
};

void setup()
{
	init(
		TRI, //TRI: Triangle, RECT: Rectangle
		50,  //duty cycle 0..100%, only matters for Triangle and Rectangle
		envelope);
}

uint16_t melody[][2] = {{330, 1000}, {415, 1000}, {370, 1000}, {247, 1000}, {0, 1000}, {330, 1000}, {370, 1000}, {415, 1000}, {330, 1000}, {0, 1000}, {415, 1000}, {330, 1000}, {370, 1000}, {247, 1000}, {0, 1000}, {247, 1000}, {370, 1000}, {415, 1000}, {330, 1000}};

void loop()
{
	static int i = 0;
	if (i < 19 && !isPlaying())
	{
		play(melody[i][0], melody[i][1]);
		i++;
	}
}
