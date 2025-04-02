#include <Math.h>
#include "chimes.h"

#define ISR_CYCLE 16 //16us

char strbuf[255];
uint16_t ADSR_default[] = {0, 0, 100, 0, MAX_VOLUME};
uint16_t ADSR_env[5];
uint16_t nSamples; //Number of samples in Array
uint8_t adsrPhase;
uint32_t tPeriod;
uint8_t *samples; //Array with samples
uint8_t *_envelope, _waveform, _duty_cycle;
uint16_t &_sustain_lvl = ADSR_env[4];

enum ADSR_phase
{
	ATTACK,
	DECAY,
	SUSTAIN,
	RELEASE
};

namespace Chimes
{
void init(uint8_t waveform, uint8_t duty_cycle, uint8_t *envelope)
{
	Serial.begin(115200);
	//PWM Signal generation
	DDRB |= (1 << PB3) + (1 << PB0);				  //OC2A, Pin 11
	TCCR2A = (1 << WGM21) + (1 << WGM20);			  //Fast PWM
	TCCR2A |= (0 << COM2A0) + (1 << COM2A1);		  //Set OC2A on compare match, clear OC2A at BOTTOM,(inverting mode).
	TCCR2B = (0 << CS22) + (0 << CS21) + (1 << CS20); //No Prescaling
	samples = (uint8_t *)malloc(0);
	_waveform = waveform;
	_duty_cycle = duty_cycle;
	_envelope = envelope;
}

void play(uint16_t freq, uint16_t duration)
{
	uint8_t waveform = _waveform;
	//Init adsr according to the length of the note
	for (int i = 0; i < 4; i++)
	{
		if (_envelope)
		{
			ADSR_env[i] = (uint32_t)_envelope[i] * duration / 100;
		}
		else
		{
			ADSR_env[i] = (uint32_t)ADSR_default[i] * duration / 100;
		}
		//Serial.println(ADSR_env[i]);
	}
	ADSR_env[4] = _envelope ? _envelope[4] : MAX_VOLUME;
	//Serial.println(ADSR_env[4]);

	if (freq == 0)    // 当频率为0时，表示这是一个休止符
	{ 
	    tPeriod = ISR_CYCLE * 100;    // 设置一个1600微秒的周期作为休止符长度
	    waveform = PAUSE;              // 将波形类型设置为PAUSE，输出静音
	}
	else
	    tPeriod = 1E6 / freq;         // 将频率(Hz)转换为周期(微秒)，1E6是1秒=1000000微秒
	
	nSamples = tPeriod / ISR_CYCLE;   // 计算一个周期需要多少个采样点
	                                  // 例如：440Hz的A音：
	                                  // tPeriod = 1000000/440 ≈ 2272.7微秒
	                                  // nSamples = 2272.7/16 ≈ 142个采样点
	realloc(samples, nSamples);
	uint16_t nDuty = (_duty_cycle * nSamples) / 100;

	switch (waveform)
	{
	case SINE: //Sinewave 类似笛子的音色
		for (int i = 0; i < nSamples; i++)
		{
			samples[i] = 128 + 127 * sin(2 * PI * i / nSamples);
		}
		break;

	case TRI: //Triangle 类似早期电子游戏的音效
		for (int16_t i = 0; i < nSamples; i++)
		{
			if (i < nDuty)
			{
				samples[i] = 255 * (double)i / nDuty; //Rise
			}
			else
			{
				samples[i] = 255 * (1 - (double)(i - nDuty) / (nSamples - nDuty)); //Fall
			}
		}
		break;
	case RECT: //Rectangle 类似老式电子音乐或8位游戏音效
		for (int16_t i = 0; i < nSamples; i++)
		{
			i < nDuty ? samples[i] = 255 : samples[i] = 0;
		}
		break;
	case PAUSE: //Rectangle
		memset(samples, 0, nSamples);
	}
	TIMSK2 = (1 << TOIE2);
	/*for(uint16_t i = 0; i < nSamples; i++) {
		sprintf(strbuf, "%d: %d", i, samples[i]);
		Serial.println(strbuf);
	}*/
}

//Returns true, while note is playing
boolean isPlaying()
{
	return (1 << TOIE2) & TIMSK2;
}
} // namespace Chimes

//Called every 16us (microseconds), when Timer2 overflows
ISR(TIMER2_OVF_vect)
{
	static uint32_t adsr_timer, adsr_time;
	static uint16_t cnt; //Index counter
	static uint8_t sustain_lvl, vol;
    // sample为完整的波形，vol为音量控制 ,/MAX_VOLUME是归一化处理
	OCR2A = vol * samples[cnt] / MAX_VOLUME;
	if (cnt < nSamples - 1)
	{
		cnt++;
	}
	else
	{
		cnt = 0;
		adsr_timer += tPeriod;
		if (adsr_timer >= 10000)
		{ //every 10 millisecond
			adsr_timer = 0;

			switch (adsrPhase)
			{
			case ATTACK:
				if (ADSR_env[ATTACK])
				{
					vol = MAX_VOLUME * (float)adsr_time / ADSR_env[ATTACK];
					if (vol == MAX_VOLUME)
					{ //Attack phase over
						adsrPhase = DECAY;
						adsr_time = 0;
					}
				}
				else
				{
					adsrPhase = DECAY;
					vol = MAX_VOLUME;
					adsr_time = 0;
				}
				break;

			case DECAY:
				if (ADSR_env[DECAY])
				{
					sustain_lvl = _sustain_lvl;
					vol = MAX_VOLUME - (MAX_VOLUME - _sustain_lvl) * (float)adsr_time / ADSR_env[DECAY];
					if (vol <= sustain_lvl)
					{
						adsr_time = 0;
						adsrPhase = SUSTAIN;
					}
				}
				else
				{
					adsrPhase = SUSTAIN;
					sustain_lvl = MAX_VOLUME;
					adsr_time = 0;
				}
				break;

			case SUSTAIN:
				if (adsr_time > ADSR_env[SUSTAIN])
				{
					adsrPhase = RELEASE;
					adsr_time = 0;
				}

				break;
			case RELEASE:
				if (ADSR_env[RELEASE])
				{
					vol = sustain_lvl * (1 - (float)adsr_time / ADSR_env[RELEASE]);
					if (vol == 0)
					{ //Attack phase over
						adsr_time = 0;
						TIMSK2 = (0 << TOIE2);
						adsrPhase = ATTACK;
					}
				}
				else
				{
					adsrPhase = ATTACK;
					vol = 0;
					adsr_time = 0;
					TIMSK2 = (0 << TOIE2);
				}
				break;
			}
			adsr_time += 10;
		}
	}
}