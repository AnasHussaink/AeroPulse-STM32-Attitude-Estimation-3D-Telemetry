/*
 * lcd_i2c.c
 *
 *  Created on: Oct 14, 2026
 *      Author: Midtown Computers
 */


#include "lcd_i2c.h"

#define LCD_ADDR (0x27 << 1)

static I2C_HandleTypeDef *lcd_i2c;

static void LCD_SendCommand(uint8_t cmd);
static void LCD_SendData(uint8_t data);
static void LCD_Send4Bits(uint8_t data);
static void LCD_EnablePulse(uint8_t data);


static void LCD_EnablePulse(uint8_t data)
{
    uint8_t data_on;
    uint8_t data_off;

    data_on = data | 0x04;
    data_off = data & ~0x04;

    HAL_I2C_Master_Transmit(
        lcd_i2c,
        LCD_ADDR,
        &data_on,
        1,
        HAL_MAX_DELAY
    );

    HAL_Delay(1);

    HAL_I2C_Master_Transmit(
        lcd_i2c,
        LCD_ADDR,
        &data_off,
        1,
        HAL_MAX_DELAY
    );

    HAL_Delay(1);
}


static void LCD_Send4Bits(uint8_t data)
{
    /*
     PCF8574 common mapping:

     P0 -> RS
     P1 -> RW
     P2 -> EN
     P3 -> Backlight
     P4 -> D4
     P5 -> D5
     P6 -> D6
     P7 -> D7
    */

    data |= 0x08;   // Backlight ON

    HAL_I2C_Master_Transmit(
        lcd_i2c,
        LCD_ADDR,
        &data,
        1,
        HAL_MAX_DELAY
    );

    LCD_EnablePulse(data);
}


static void LCD_SendCommand(uint8_t cmd)
{
    uint8_t upper;
    uint8_t lower;

    upper = cmd & 0xF0;
    lower = (cmd << 4) & 0xF0;

    LCD_Send4Bits(
        upper | 0x00
    );

    LCD_Send4Bits(
        lower | 0x00
    );
}


static void LCD_SendData(uint8_t data)
{
    uint8_t upper;
    uint8_t lower;

    upper = data & 0xF0;
    lower = (data << 4) & 0xF0;

    LCD_Send4Bits(
        upper | 0x01
    );

    LCD_Send4Bits(
        lower | 0x01
    );
}


void LCD_Init(I2C_HandleTypeDef *hi2c)
{
    lcd_i2c = hi2c;

    HAL_Delay(50);

    // 4-bit initialization sequence

    LCD_Send4Bits(0x30);
    HAL_Delay(5);

    LCD_Send4Bits(0x30);
    HAL_Delay(1);

    LCD_Send4Bits(0x30);
    HAL_Delay(1);

    LCD_Send4Bits(0x20);
    HAL_Delay(1);

    // Function set
    // 4-bit, 2-line, 5x8 font
    LCD_SendCommand(0x28);

    // Display ON, cursor OFF
    LCD_SendCommand(0x0C);

    // Clear
    LCD_SendCommand(0x01);
    HAL_Delay(2);

    // Entry mode
    LCD_SendCommand(0x06);
}


void LCD_Clear(void)
{
    LCD_SendCommand(0x01);

    HAL_Delay(2);
}


void LCD_SetCursor(uint8_t row, uint8_t col)
{
    uint8_t address;

    if (row == 0)
    {
        address = 0x80 + col;
    }
    else
    {
        address = 0xC0 + col;
    }

    LCD_SendCommand(address);
}


void LCD_SendString(char *str)
{
    while (*str)
    {
        LCD_SendData(
            (uint8_t)*str
        );

        str++;
    }
}
