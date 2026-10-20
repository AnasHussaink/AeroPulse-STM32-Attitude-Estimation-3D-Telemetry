param([string]$Port = "COM3")
$repoRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $repoRoot "host\src"
$env:AEROSCOPE_SERIAL_PORT = $Port
python -m imu_visualizer.app_3d
