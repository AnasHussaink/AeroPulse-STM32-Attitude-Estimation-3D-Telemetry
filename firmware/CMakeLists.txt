cmake_minimum_required(VERSION 3.20)
project(AeroScope LANGUAGES C ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_executable(aeroscope
  Core/Src/main.c
  Core/Src/lcd_i2c.c
  Core/Src/stm32f1xx_hal_msp.c
  Core/Src/stm32f1xx_it.c
  Core/Src/syscalls.c
  Core/Src/sysmem.c
  Core/Src/system_stm32f1xx.c
  Core/Startup/startup_stm32f103c8tx.s
  Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal.c
  Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_cortex.c
  Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_dma.c
  Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_exti.c
  Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_flash.c
  Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_flash_ex.c
  Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_gpio.c
  Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_gpio_ex.c
  Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_i2c.c
  Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_pwr.c
  Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_rcc.c
  Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_rcc_ex.c
  Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_spi.c
  Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_uart.c
)
set_target_properties(aeroscope PROPERTIES SUFFIX ".elf")
target_compile_definitions(aeroscope PRIVATE USE_HAL_DRIVER STM32F103xB)
target_include_directories(aeroscope PRIVATE
  Core/Inc Drivers/STM32F1xx_HAL_Driver/Inc
  Drivers/STM32F1xx_HAL_Driver/Inc/Legacy
  Drivers/CMSIS/Device/ST/STM32F1xx/Include Drivers/CMSIS/Include)
target_compile_options(aeroscope PRIVATE
  -mcpu=cortex-m3 -mthumb -mfloat-abi=soft -ffunction-sections -fdata-sections
  -Wall -Wextra "$<$<COMPILE_LANGUAGE:C>:-Os>")
target_link_options(aeroscope PRIVATE
  -mcpu=cortex-m3 -mthumb -mfloat-abi=soft
  "-T${CMAKE_CURRENT_SOURCE_DIR}/STM32F103C8TX_FLASH.ld"
  --specs=nano.specs --specs=nosys.specs -Wl,--gc-sections
  -Wl,-u,_printf_float "-Wl,-Map=${CMAKE_CURRENT_BINARY_DIR}/aeroscope.map")
target_link_libraries(aeroscope PRIVATE m)
set_property(TARGET aeroscope APPEND PROPERTY LINK_DEPENDS
  "${CMAKE_CURRENT_SOURCE_DIR}/STM32F103C8TX_FLASH.ld")
add_custom_command(TARGET aeroscope POST_BUILD
  COMMAND "${CMAKE_SIZE}" "$<TARGET_FILE:aeroscope>"
  COMMAND "${CMAKE_OBJCOPY}" -O ihex "$<TARGET_FILE:aeroscope>" aeroscope.hex
  COMMAND "${CMAKE_OBJCOPY}" -O binary "$<TARGET_FILE:aeroscope>" aeroscope.bin
  VERBATIM)
