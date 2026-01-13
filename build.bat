@echo off
REM SafeLabs - Build Script for Multiple Labs
REM Usage: build.bat [lab1|lab2|lab3|all]

SET LAB=%1
IF "%LAB%"=="" SET LAB=lab1

echo ====================================
echo SafeLabs Multi-Lab Build System
echo ====================================
echo.

IF "%LAB%"=="all" GOTO BUILD_ALL

:BUILD_SINGLE
echo Building for %LAB%...
echo.

REM Copy the correct config file
IF "%LAB%"=="lab1" copy /Y "configs\lab1_config.h" "firmware\include\config.h"
IF "%LAB%"=="lab2" copy /Y "configs\lab2_config.h" "firmware\include\config.h"
IF "%LAB%"=="lab3" copy /Y "configs\lab3_config.h" "firmware\include\config.h"

REM Build firmware
cd firmware
python -m platformio run -e esp32doit-devkit-v1
cd ..

echo.
echo Build complete for %LAB%!
echo Firmware: firmware\.pio\build\esp32doit-devkit-v1\firmware.bin
echo.
echo To run simulation:
echo 1. Open simulations\%LAB%\diagram.json in VS Code
echo 2. Press F1 → "Wokwi: Start Simulator"
echo.
GOTO END

:BUILD_ALL
echo Building all labs...
echo.

FOR %%L IN (lab1 lab2 lab3) DO (
    echo.
    echo ==========================================
    echo Building %%L...
    echo ==========================================
    copy /Y "configs\%%L_config.h" "firmware\include\config.h"
    cd firmware
    python -m platformio run -e esp32doit-devkit-v1
    cd ..
    echo %%L build complete!
)

echo.
echo ==========================================
echo All labs built successfully!
echo ==========================================
echo.

:END
