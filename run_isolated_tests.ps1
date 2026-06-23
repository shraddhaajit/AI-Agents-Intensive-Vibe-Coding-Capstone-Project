$process = Start-Process -FilePath "adk" -ArgumentList "api_server rival/rival_agent --port 9001" -PassThru
Write-Host "Waiting for ADK API server to start (15s)..."
Start-Sleep -Seconds 15
Write-Host "`n--- Running test_rival.py ---"
python test_rival.py
Write-Host "`n--- Running poisoned_weather_server test ---"
python -c "from rival.poisoned_weather_server import get_precipitation; print(get_precipitation(28.6, -81.3))"
Write-Host "`nStopping ADK API server..."
Stop-Process -Id $process.Id -Force
