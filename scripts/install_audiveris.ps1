$ErrorActionPreference = 'Stop'
$installerPath = Join-Path $env:TEMP 'MusicConverter-Audiveris-5.11.0.msi'
Invoke-WebRequest -Uri 'https://github.com/Audiveris/audiveris/releases/download/5.11.0/Audiveris-5.11.0-windows-x86_64.msi' -OutFile $installerPath
$result = Start-Process -FilePath 'msiexec.exe' -ArgumentList ('/i "' + $installerPath + '"') -Wait -PassThru
if ($result.ExitCode -notin @(0, 3010)) { throw "Audiveris installation exited with code $($result.ExitCode)" }
Write-Host 'Audiveris installed. Restart MUSIC_CONVERTER and choose Sheet music / MIDI.'
