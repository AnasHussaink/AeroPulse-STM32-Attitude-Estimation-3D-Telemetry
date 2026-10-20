/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "lcd_i2c.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
#define MPU6500_CS_LOW() \
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_RESET)

#define MPU6500_CS_HIGH() \
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_SET)

#define RAD_TO_DEG 57.2957795f
/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
I2C_HandleTypeDef hi2c2;

SPI_HandleTypeDef hspi1;

UART_HandleTypeDef huart1;

/* USER CODE BEGIN PV */
/* USER CODE BEGIN PV */

/* ============================================================
 * MPU6500 sensor values
 * ============================================================ */

float accel_x_g = 0.0f;
float accel_y_g = 0.0f;
float accel_z_g = 0.0f;

float gyro_x_dps = 0.0f;
float gyro_y_dps = 0.0f;
float gyro_z_dps = 0.0f;


/* ============================================================
 * Gyroscope calibration offsets
 * ============================================================ */

float gyro_x_offset = 0.0f;
float gyro_y_offset = 0.0f;
float gyro_z_offset = 0.0f;


/* ============================================================
 * Accelerometer calculated angles
 * ============================================================ */

float roll_accel = 0.0f;
float pitch_accel = 0.0f;


/* ============================================================
 * Fused attitude
 *
 * These are the actual filter outputs.
 * ============================================================ */

float roll_fused = 0.0f;
float pitch_fused = 0.0f;
float yaw = 0.0f;


/* ============================================================
 * Master zero offsets
 *
 * STM32 owns the attitude reference.
 * ============================================================ */

float roll_zero_offset = 0.0f;
float pitch_zero_offset = 0.0f;
float yaw_zero_offset = 0.0f;


/* ============================================================
 * Final/canonical attitude
 *
 * These exact values go to:
 * 1. UART
 * 2. Physical LCD
 * 3. Python GUI
 * ============================================================ */

float roll_display = 0.0f;
float pitch_display = 0.0f;
float yaw_display = 0.0f;


/* ============================================================
 * Timing
 * ============================================================ */

uint32_t previous_tick = 0;
uint32_t lcd_previous_tick = 0;


/* ============================================================
 * UART
 * ============================================================ */

char uart_buffer[100];

uint8_t uart_rx_byte = 0;


/* ============================================================
 * LCD
 * ============================================================ */

char lcd_line1[17];
char lcd_line2[17];

char lcd_uart_buffer[64];


/* ============================================================
 * Device status
 * ============================================================ */

uint8_t mpu_who_am_i = 0;

/* USER CODE END PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_SPI1_Init(void);
static void MX_USART1_UART_Init(void);
static void MX_I2C2_Init(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
/* USER CODE BEGIN 0 */
/* USER CODE BEGIN 0 */


/* ============================================================
 * MPU6500 READ SINGLE REGISTER
 * ============================================================ */

uint8_t MPU6500_ReadRegister(uint8_t reg)
{
    uint8_t tx[2];
    uint8_t rx[2];

    tx[0] = reg | 0x80;
    tx[1] = 0x00;

    MPU6500_CS_LOW();

    HAL_SPI_TransmitReceive(
        &hspi1,
        tx,
        rx,
        2,
        HAL_MAX_DELAY
    );

    MPU6500_CS_HIGH();

    return rx[1];
}


/* ============================================================
 * MPU6500 WRITE SINGLE REGISTER
 * ============================================================ */

void MPU6500_WriteRegister(
    uint8_t reg,
    uint8_t data
)
{
    uint8_t tx[2];

    tx[0] = reg & 0x7F;
    tx[1] = data;

    MPU6500_CS_LOW();

    HAL_SPI_Transmit(
        &hspi1,
        tx,
        2,
        HAL_MAX_DELAY
    );

    MPU6500_CS_HIGH();
}


/* ============================================================
 * MPU6500 BURST READ
 * ============================================================ */

void MPU6500_ReadBurst(
    uint8_t start_reg,
    uint8_t *buffer,
    uint8_t length
)
{
    uint8_t address;

    address = start_reg | 0x80;

    MPU6500_CS_LOW();

    HAL_SPI_Transmit(
        &hspi1,
        &address,
        1,
        HAL_MAX_DELAY
    );

    HAL_SPI_Receive(
        &hspi1,
        buffer,
        length,
        HAL_MAX_DELAY
    );

    MPU6500_CS_HIGH();
}


/* ============================================================
 * READ ACCELEROMETER + GYROSCOPE
 * ============================================================ */

void MPU6500_ReadSensor(void)
{
    uint8_t data[14];

    int16_t accel_x_raw;
    int16_t accel_y_raw;
    int16_t accel_z_raw;

    int16_t gyro_x_raw;
    int16_t gyro_y_raw;
    int16_t gyro_z_raw;


    MPU6500_ReadBurst(
        0x3B,
        data,
        14
    );


    accel_x_raw =
        (int16_t)(
            ((uint16_t)data[0] << 8)
            | data[1]
        );

    accel_y_raw =
        (int16_t)(
            ((uint16_t)data[2] << 8)
            | data[3]
        );

    accel_z_raw =
        (int16_t)(
            ((uint16_t)data[4] << 8)
            | data[5]
        );


    gyro_x_raw =
        (int16_t)(
            ((uint16_t)data[8] << 8)
            | data[9]
        );

    gyro_y_raw =
        (int16_t)(
            ((uint16_t)data[10] << 8)
            | data[11]
        );

    gyro_z_raw =
        (int16_t)(
            ((uint16_t)data[12] << 8)
            | data[13]
        );


    /*
     * MPU6500 default accelerometer range:
     * +/-2g
     *
     * scale = 16384 LSB/g
     */

    accel_x_g =
        (float)accel_x_raw
        / 16384.0f;

    accel_y_g =
        (float)accel_y_raw
        / 16384.0f;

    accel_z_g =
        (float)accel_z_raw
        / 16384.0f;


    /*
     * MPU6500 default gyro range:
     * +/-250 deg/s
     *
     * scale = 131 LSB/(deg/s)
     */

    gyro_x_dps =
        (float)gyro_x_raw
        / 131.0f;

    gyro_y_dps =
        (float)gyro_y_raw
        / 131.0f;

    gyro_z_dps =
        (float)gyro_z_raw
        / 131.0f;
}


/* ============================================================
 * GYROSCOPE CALIBRATION
 *
 * Keep the board completely still during calibration.
 * ============================================================ */

void MPU6500_CalibrateGyro(void)
{
    float sum_x = 0.0f;
    float sum_y = 0.0f;
    float sum_z = 0.0f;

    for (int i = 0; i < 500; i++)
    {
        MPU6500_ReadSensor();

        sum_x += gyro_x_dps;
        sum_y += gyro_y_dps;
        sum_z += gyro_z_dps;

        HAL_Delay(5);
    }

    gyro_x_offset =
        sum_x / 500.0f;

    gyro_y_offset =
        sum_y / 500.0f;

    gyro_z_offset =
        sum_z / 500.0f;
}


/* ============================================================
 * SET CURRENT ATTITUDE AS ZERO
 *
 * This is now the only place where zero reference is created.
 * ============================================================ */

void Attitude_SetZero(void)
{
    roll_zero_offset =
        roll_fused;

    pitch_zero_offset =
        pitch_fused;

    yaw_zero_offset =
        yaw;
}


/* ============================================================
 * CALCULATE FINAL DISPLAY ATTITUDE
 * ============================================================ */

void Attitude_UpdateDisplayValues(void)
{
    roll_display =
        roll_fused
        - roll_zero_offset;

    pitch_display =
        pitch_fused
        - pitch_zero_offset;

    yaw_display =
        yaw
        - yaw_zero_offset;
}


/* ============================================================
 * CHECK COMMANDS RECEIVED FROM PYTHON
 *
 * Python sends:
 *
 * Z = set current attitude as zero
 * ============================================================ */

void UART_CheckCommands(void)
{
    if (
        __HAL_UART_GET_FLAG(
            &huart1,
            UART_FLAG_RXNE
        )
        != RESET
    )
    {
        if (
            HAL_UART_Receive(
                &huart1,
                &uart_rx_byte,
                1,
                1
            )
            == HAL_OK
        )
        {
            if (
                uart_rx_byte == 'Z'
                ||
                uart_rx_byte == 'z'
            )
            {
                Attitude_SetZero();
            }
        }
    }
}


/* ============================================================
 * SEND ATTITUDE TELEMETRY TO PYTHON
 * ============================================================ */

void UART_SendAttitude(void)
{
    int len;

    len = snprintf(
        uart_buffer,
        sizeof(uart_buffer),
        "ROLL:%.2f,PITCH:%.2f,YAW:%.2f\r\n",
        roll_display,
        pitch_display,
        yaw_display
    );

    HAL_UART_Transmit(
        &huart1,
        (uint8_t *)uart_buffer,
        len,
        100
    );
}


/* ============================================================
 * UPDATE PHYSICAL 16x2 LCD
 *
 * Also sends the exact same two LCD lines to Python.
 * ============================================================ */

void LCD_UpdateAttitude(void)
{
    /*
     * Each physical LCD row can show maximum 16 characters.
     *
     * Example:
     *
     * R:+12.4 P: -3.2
     * Y: +25.1 IMU OK
     */


    snprintf(
        lcd_line1,
        sizeof(lcd_line1),
        "R:%+5.1f P:%+5.1f",
        roll_display,
        pitch_display
    );


    snprintf(
        lcd_line2,
        sizeof(lcd_line2),
        "Y:%+6.1f IMU OK",
        yaw_display
    );


    /* --------------------------------------------------------
     * Physical LCD - row 1
     * -------------------------------------------------------- */

    LCD_SetCursor(
        0,
        0
    );

    LCD_SendString(
        "                "
    );

    LCD_SetCursor(
        0,
        0
    );

    LCD_SendString(
        lcd_line1
    );


    /* --------------------------------------------------------
     * Physical LCD - row 2
     * -------------------------------------------------------- */

    LCD_SetCursor(
        1,
        0
    );

    LCD_SendString(
        "                "
    );

    LCD_SetCursor(
        1,
        0
    );

    LCD_SendString(
        lcd_line2
    );


    /* --------------------------------------------------------
     * Send same physical LCD line 1 to Python
     * -------------------------------------------------------- */

    snprintf(
        lcd_uart_buffer,
        sizeof(lcd_uart_buffer),
        "LCD1:%s\r\n",
        lcd_line1
    );

    HAL_UART_Transmit(
        &huart1,
        (uint8_t *)lcd_uart_buffer,
        strlen(lcd_uart_buffer),
        100
    );


    /* --------------------------------------------------------
     * Send same physical LCD line 2 to Python
     * -------------------------------------------------------- */

    snprintf(
        lcd_uart_buffer,
        sizeof(lcd_uart_buffer),
        "LCD2:%s\r\n",
        lcd_line2
    );

    HAL_UART_Transmit(
        &huart1,
        (uint8_t *)lcd_uart_buffer,
        strlen(lcd_uart_buffer),
        100
    );
}


/* USER CODE END 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_SPI1_Init();
  MX_USART1_UART_Init();
  MX_I2C2_Init();

  /* USER CODE BEGIN 2 */


  /* ============================================================
   * MPU6500 INITIALIZATION
   * ============================================================ */

  MPU6500_CS_HIGH();

  HAL_Delay(100);


  /*
   * WHO_AM_I register = 0x75
   *
   * MPU6500 expected value = 0x70
   */

  mpu_who_am_i =
      MPU6500_ReadRegister(
          0x75
      );


  /*
   * Wake MPU6500
   *
   * PWR_MGMT_1 register = 0x6B
   * 0x00 = wake up
   */

  MPU6500_WriteRegister(
      0x6B,
      0x00
  );

  HAL_Delay(100);


  /* ============================================================
   * LCD INITIALIZATION
   * ============================================================ */

  LCD_Init(
      &hi2c2
  );

  LCD_Clear();

  LCD_SetCursor(
      0,
      0
  );

  LCD_SendString(
      "STM32 IMU"
  );

  LCD_SetCursor(
      1,
      0
  );

  LCD_SendString(
      "CALIBRATING..."
  );


  /* ============================================================
   * GYRO CALIBRATION
   *
   * Keep sensor completely still for approximately 3 seconds.
   * ============================================================ */

  MPU6500_CalibrateGyro();


  /* ============================================================
   * INITIAL ATTITUDE
   * ============================================================ */

  MPU6500_ReadSensor();


  roll_accel =
      atan2f(
          accel_y_g,
          accel_z_g
      )
      * RAD_TO_DEG;


  pitch_accel =
      atan2f(
          -accel_x_g,

          sqrtf(
              accel_y_g * accel_y_g
              +
              accel_z_g * accel_z_g
          )
      )
      * RAD_TO_DEG;


  /*
   * Start complementary filter from
   * accelerometer orientation.
   */

  roll_fused =
      roll_accel;

  pitch_fused =
      pitch_accel;

  yaw = 0.0f;


  /*
   * Startup physical position becomes
   * initial system zero.
   */

  Attitude_SetZero();

  Attitude_UpdateDisplayValues();


  /* ============================================================
   * READY MESSAGE
   * ============================================================ */

  LCD_Clear();

  LCD_SetCursor(
      0,
      0
  );

  LCD_SendString(
      "STM32 IMU READY"
  );

  LCD_SetCursor(
      1,
      0
  );

  LCD_SendString(
      "SPI UART I2C OK"
  );

  HAL_Delay(1200);

  LCD_Clear();


  /* ============================================================
   * START TIMERS
   * ============================================================ */

  previous_tick =
      HAL_GetTick();

  lcd_previous_tick =
      HAL_GetTick();


  /* USER CODE END 2 */


  /* USER CODE BEGIN WHILE */

  while (1)
  {
      uint32_t current_tick;

      float dt;

      float gyro_x_corrected;
      float gyro_y_corrected;
      float gyro_z_corrected;


      /* ========================================================
       * READ TIME
       * ======================================================== */

      current_tick =
          HAL_GetTick();


      /* ========================================================
       * READ MPU6500
       * ======================================================== */

      MPU6500_ReadSensor();


      /* ========================================================
       * REMOVE GYRO STATIC OFFSET
       * ======================================================== */

      gyro_x_corrected =
          gyro_x_dps
          - gyro_x_offset;

      gyro_y_corrected =
          gyro_y_dps
          - gyro_y_offset;

      gyro_z_corrected =
          gyro_z_dps
          - gyro_z_offset;


      /* ========================================================
       * LOOP TIME
       * ======================================================== */

      dt =
          (
              current_tick
              - previous_tick
          )
          / 1000.0f;

      previous_tick =
          current_tick;


      /*
       * Protect against invalid timing
       * during debugger pauses/startup.
       */

      if (
          dt <= 0.0f
          ||
          dt > 0.1f
      )
      {
          dt = 0.02f;
      }


      /* ========================================================
       * ACCELEROMETER ROLL
       * ======================================================== */

      roll_accel =
          atan2f(
              accel_y_g,
              accel_z_g
          )
          * RAD_TO_DEG;


      /* ========================================================
       * ACCELEROMETER PITCH
       * ======================================================== */

      pitch_accel =
          atan2f(
              -accel_x_g,

              sqrtf(
                  accel_y_g
                  * accel_y_g
                  +
                  accel_z_g
                  * accel_z_g
              )
          )
          * RAD_TO_DEG;


      /* ========================================================
       * COMPLEMENTARY FILTER - ROLL
       * ======================================================== */

      roll_fused =
          0.98f
          *
          (
              roll_fused
              +
              gyro_x_corrected
              * dt
          )
          +
          0.02f
          * roll_accel;


      /* ========================================================
       * COMPLEMENTARY FILTER - PITCH
       * ======================================================== */

      pitch_fused =
          0.98f
          *
          (
              pitch_fused
              +
              gyro_y_corrected
              * dt
          )
          +
          0.02f
          * pitch_accel;


      /* ========================================================
       * YAW
       *
       * MPU6500 has no magnetometer.
       * Therefore yaw is gyro integration only and can drift.
       * ======================================================== */

      yaw +=
          gyro_z_corrected
          * dt;


      /* ========================================================
       * CHECK FOR ZERO COMMAND FROM PYTHON
       * ======================================================== */

      UART_CheckCommands();


      /* ========================================================
       * APPLY MASTER ZERO REFERENCE
       * ======================================================== */

      Attitude_UpdateDisplayValues();


      /* ========================================================
       * SEND ATTITUDE TO PYTHON
       *
       * Approx sensor loop = 50 Hz
       * ======================================================== */

      UART_SendAttitude();


      /* ========================================================
       * UPDATE 16x2 LCD EVERY 200 ms
       *
       * 5 Hz is enough for a human-readable display.
       * ======================================================== */

      if (
          current_tick
          - lcd_previous_tick
          >= 200
      )
      {
          lcd_previous_tick =
              current_tick;

          LCD_UpdateAttitude();
      }


      /* ========================================================
       * APPROX 50 Hz SENSOR LOOP
       * ======================================================== */

      HAL_Delay(20);


      /* USER CODE END WHILE */

      /* USER CODE BEGIN 3 */
  }

}
/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief I2C2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_I2C2_Init(void)
{

  /* USER CODE BEGIN I2C2_Init 0 */

  /* USER CODE END I2C2_Init 0 */

  /* USER CODE BEGIN I2C2_Init 1 */

  /* USER CODE END I2C2_Init 1 */
  hi2c2.Instance = I2C2;
  hi2c2.Init.ClockSpeed = 100000;
  hi2c2.Init.DutyCycle = I2C_DUTYCYCLE_2;
  hi2c2.Init.OwnAddress1 = 0;
  hi2c2.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
  hi2c2.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
  hi2c2.Init.OwnAddress2 = 0;
  hi2c2.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
  hi2c2.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
  if (HAL_I2C_Init(&hi2c2) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN I2C2_Init 2 */

  /* USER CODE END I2C2_Init 2 */

}

/**
  * @brief SPI1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_SPI1_Init(void)
{

  /* USER CODE BEGIN SPI1_Init 0 */

  /* USER CODE END SPI1_Init 0 */

  /* USER CODE BEGIN SPI1_Init 1 */

  /* USER CODE END SPI1_Init 1 */
  /* SPI1 parameter configuration*/
  hspi1.Instance = SPI1;
  hspi1.Init.Mode = SPI_MODE_MASTER;
  hspi1.Init.Direction = SPI_DIRECTION_2LINES;
  hspi1.Init.DataSize = SPI_DATASIZE_8BIT;
  hspi1.Init.CLKPolarity = SPI_POLARITY_LOW;
  hspi1.Init.CLKPhase = SPI_PHASE_1EDGE;
  hspi1.Init.NSS = SPI_NSS_SOFT;
  hspi1.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_2;
  hspi1.Init.FirstBit = SPI_FIRSTBIT_MSB;
  hspi1.Init.TIMode = SPI_TIMODE_DISABLE;
  hspi1.Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE;
  hspi1.Init.CRCPolynomial = 10;
  if (HAL_SPI_Init(&hspi1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN SPI1_Init 2 */

  /* USER CODE END SPI1_Init 2 */

}

/**
  * @brief USART1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART1_UART_Init(void)
{

  /* USER CODE BEGIN USART1_Init 0 */

  /* USER CODE END USART1_Init 0 */

  /* USER CODE BEGIN USART1_Init 1 */

  /* USER CODE END USART1_Init 1 */
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 115200;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART1_Init 2 */

  /* USER CODE END USART1_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOD_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_SET);

  /*Configure GPIO pin : PA4 */
  GPIO_InitStruct.Pin = GPIO_PIN_4;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
