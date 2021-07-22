#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/sleep.h>
#include <stdlib.h>
#include <stdbool.h>
#include "delay.h"

#define DELAY_MS 100
#define SHORT_BUZZ 25
#define LONG_BUZZ 255
#define LEFT_PADDLE_LED PD0
#define RIGHT_PADDLE_LED PD1
#define BUZZER PB4
#define LEFT true
#define RIGHT false
#define PADDLE_TIMEOUT 0xff
#define MAX_GAMES 100

void moveBall();
void handleBallOnEdge();
void hitBall();
void endGame();
void blinkD(uint8_t led);
void onD(uint8_t led);
void offD(uint8_t led);
void showByte(uint8_t byte);
void playHitNote();
void playEndNote();
void runACD();
void sleep();

volatile bool direction = LEFT;    // Direction the ball is moving
volatile uint8_t left_paddle = 0;  // Left paddle active counter
volatile uint8_t right_paddle = 0; // Right paddle active counter
volatile uint8_t ball = 1;         // Ball position

// Left paddle button pressed
ISR(INT0_vect)
{
    // If left paddle not in use, reset counter
    if (left_paddle == 0)
    {
        left_paddle = PADDLE_TIMEOUT;
        onD(LEFT_PADDLE_LED);
    }
}

// Right paddle button pressed
ISR(INT1_vect)
{
    // If right paddle not in use, reset counter
    if (right_paddle == 0)
    {
        right_paddle = PADDLE_TIMEOUT;
        onD(RIGHT_PADDLE_LED);
    }
}

// Paddle timer overflow, dec paddle counters
ISR(TIMER0_OVF_vect)
{
    if (right_paddle > 0)
    {
        right_paddle--;
    }
    if (right_paddle == 0)
    {
        offD(RIGHT_PADDLE_LED);
    }
    if (left_paddle > 0)
    {
        left_paddle--;
    }
    if (left_paddle == 0)
    {
        offD(LEFT_PADDLE_LED);
    }
}

// Game timer overflow, handle game logic
ISR(TIMER1_COMPA_vect)
{
    // Move ball
    moveBall();
    // If ball shifted out of bounds, check for hit
    if (ball == 0)
    {
        handleBallOnEdge();
    }
    // Display ball position
    showByte(ball);
}

uint8_t num_games = 0;    //Number of games played
void main()
{
    DDRD = 0b11110011; // bits 0-1, 4-7 led output, bits 2-3 button input
    DDRB = 0b00011111; // bits 0-3 led output, bit 4 buzzer output
    PORTD = 0x00;
    PORTB = 0x00;

    cli();
    PRR &= ~(1 << PRADC);                                          // Turn off power reduction register bit
    ADCSRA = (1 << ADEN) |                                         // ADC enable
             (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0);           // Prescaler divide by 128
    ADMUX = (0 << REFS1) | (1 << REFS0) |                          // 5V internal reference
            (0 << ADLAR) |                                         // Right justify the result in ADC
            (0 << MUX3) | (0 << MUX2) | (0 << MUX1) | (1 << MUX0); // Uses PC1 and A1
    EIMSK |= (1 << INT0) + (1 << INT1);                            // Enable external INT0, INT1
    EICRA |= (1 << ISC01) + (1 << ISC00);                          // INT0 on rising edge
    EICRA |= (1 << ISC11) + (1 << ISC10);                          // INT1 on rising edge
    TIMSK0 = (1 << TOIE0);                                         // Timer0 overflow interrupts enable
    TIMSK1 = (1 << OCIE1A);                                        // Timer1 CTC interrupts enable
    TCCR0B = (0 << CS02) + (1 << CS01) + (1 << CS00);              // Timer0 IO clk / 64 prescaler
    TCCR1B = (0 << WGM13) + (1 << WGM12) +                         // CTC mode OCR1A
             (1 << CS12) + (0 << CS11) + (1 << CS10);              // Timer1 IO clk / 1024 prescaler
	set_sleep_mode(SLEEP_MODE_PWR_DOWN);
    runACD();                                                      // Set Timer1 TOP based on potentiometer
    sei();

    showByte(ball);
    while (1)
    {
    }
}

//Registers changes in ACD and changes delay based on those changes
void runACD()
{
    ADCSRA |= (1 << ADSC); // Starts ADC
    while ((ADCSRA & (1 << ADIF)) == 0)
        ;                         // Waits until ADIF == 1
    ADCSRA |= (1 << ADIF);        // Clears ADIF
    uint8_t lo = ADCL;            // Gets low byte
    uint8_t hi = ADCH;            // Gets high byte
    OCR1A = ((hi << 8) + lo) * 2; // Set TOP
}

// Shift ball value left or right based on direction
void moveBall()
{
    if (direction == RIGHT)
    {
        ball = (ball >> 1);
    }
    else
    {
        ball = (ball << 1);
    }
}

// Hit ball if paddle is active, end game otherwise
void handleBallOnEdge()
{
    if (direction == LEFT)
    {
        if (left_paddle > 0)
        {
            hitBall();
        }
        else
        {
            endGame();
        }
    }
    else
    {
        if (right_paddle > 0)
        {
            hitBall();
        }
        else
        {
            endGame();
        }
    }
}

// Reverse direction and place ball back on 'table'
void hitBall()
{
    playHitNote();
    direction = !direction;
    if (direction == LEFT)
    {
        ball = 0x01; // Place ball on the right
    }
    else
    {
        ball = 0x80; // Place ball on the left
    }
}

// Finish game, disable interrupts and start LED win animation
void endGame()
{
    cli();       // Turn off interrupts
    showByte(0); // Clear display
    playEndNote();
	
	num_games++;
	if (num_games > MAX_GAMES)
	{
	    //Players are likely away
		//Clear num_games and go to sleep
		num_games = 0;
		sleep();
	}
    else if (direction == LEFT)
    {
        while (1)
        {
            blinkD(RIGHT_PADDLE_LED);
        }
    }
    else
    {
        while (1)
        {
            blinkD(LEFT_PADDLE_LED);
        }
    }
}

// Enter a sleep state that can be awoken by any interrupt
void sleep()
{
	sleep_enable();
	sei();              // Set interrupts globally
	sleep_cpu();        // Sleep until interrupt
	cli();              // Clear interrupts globally
	sleep_disable();
}

// Blink PORTD led
void blinkD(uint8_t led)
{
    onD(led);           // Turn LED on
    delay1ms(DELAY_MS); // Delay
    offD(led);          // Turn LED off
    delay1ms(DELAY_MS); // Delay
}

// Turn on PORTD led
void onD(uint8_t led)
{
    PORTD |= (1 << led);
}

// Turn off PORTD led
void offD(uint8_t led)
{
    PORTD &= ~(1 << led);
}

// Display byte on PORTD upper bits and PORTB lower bits
void showByte(uint8_t byte)
{
    PORTD = (PORTD & ~(0xf0)) | ((byte << 4) & 0xf0); // Set upper four byte bits on leds
    PORTB = (PORTB & ~(0x0f)) | ((byte >> 4) & 0x0f); // Set lower four byte bits on leds
}

// Play a short note
void playHitNote()
{
    for (int i = 0; i < SHORT_BUZZ; i++)
    {
        PORTB |= (1 << BUZZER);
        delay1ms(1);
        PORTB &= ~(1 << BUZZER);
        delay1ms(1);
    }
}

// Play a long note
void playEndNote()
{
    for (int i = 0; i < LONG_BUZZ; i++)
    {
        PORTB |= (1 << BUZZER);
        delay1ms(2);
        PORTB &= ~(1 << BUZZER);
        delay1ms(1);
    }
}