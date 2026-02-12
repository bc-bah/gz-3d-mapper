#!/usr/bin/env python3
"""Debug script to check path construction logic"""

import os
import sys
sys.path.append('scripts')
from utils.param import globalParam

# Simulate the path construction logic from server.py
x = 12345
y = 67890
z = 17
timestamp = 1766031273347
outputDirectory = "{timestamp}"
outputFile = "{z}/{x}/{y}.png"

# Replace placeholders
replaceMap = {
    "x": str(x),
    "y": str(y), 
    "z": str(z),
    "timestamp": str(timestamp),
}

for key, value in replaceMap.items():
    outputDirectory = outputDirectory.replace(f"{{{key}}}", value)
    outputFile = outputFile.replace(f"{{{key}}}", value)

filePath = os.path.join(globalParam.OUTPUT_BASE_PATH, outputDirectory, outputFile)

print(f"globalParam.OUTPUT_BASE_PATH: {globalParam.OUTPUT_BASE_PATH}")
print(f"outputDirectory: {outputDirectory}")
print(f"outputFile: {outputFile}")
print(f"Final filePath: {filePath}")
print(f"Directory part: {os.path.dirname(filePath)}")

# Check if the directory exists
directory = os.path.dirname(filePath)
print(f"Directory exists: {os.path.exists(directory)}")

if os.path.exists(directory):
    print(f"Contents: {os.listdir(directory)}")