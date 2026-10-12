@
# run_ngrok.ps1 - Start Flask server and expose via ngrok

# Ensure the virtual environment is activated if needed (adjust path as needed)
# .\venv\Scripts\Activate.ps1

# Start the Flask app in a background job
Start-Job -ScriptBlock { python "${PSScriptRoot}\main.py" }
# Give Flask a moment to start
Start-Sleep -Seconds 5

# Launch ngrok tunnel (ensure ngrok.exe is in $PSScriptRoot or on PATH)
./ngrok.exe http 5000 --url https://instagram1.ngrok-free.dev
@
