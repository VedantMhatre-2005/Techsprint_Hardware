#!/bin/bash
# SafeLabs - Build Script for Multiple Labs
# Usage: ./build.sh [lab1|lab2|lab3|all]

LAB=${1:-lab1}

echo "===================================="
echo "SafeLabs Multi-Lab Build System"
echo "===================================="
echo

if [ "$LAB" == "all" ]; then
    echo "Building all labs..."
    echo
    
    for lab in lab1 lab2 lab3; do
        echo
        echo "=========================================="
        echo "Building $lab..."
        echo "=========================================="
        cp "configs/${lab}_config.h" "firmware/include/config.h"
        cd firmware
        python -m platformio run -e esp32doit-devkit-v1
        cd ..
        echo "$lab build complete!"
    done
    
    echo
    echo "=========================================="
    echo "All labs built successfully!"
    echo "=========================================="
    echo
else
    echo "Building for $LAB..."
    echo
    
    # Copy the correct config file
    cp "configs/${LAB}_config.h" "firmware/include/config.h"
    
    # Build firmware
    cd firmware
    python -m platformio run -e esp32doit-devkit-v1
    cd ..
    
    echo
    echo "Build complete for $LAB!"
    echo "Firmware: firmware/.pio/build/esp32doit-devkit-v1/firmware.bin"
    echo
    echo "To run simulation:"
    echo "1. Open simulations/$LAB/diagram.json in VS Code"
    echo "2. Press F1 → 'Wokwi: Start Simulator'"
    echo
fi
