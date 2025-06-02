Start-Process powershell -ArgumentList "cd ./backend; .\venv\Scripts\Activate.ps1; python app.py"
Start-Process powershell -ArgumentList "cd ./frontend; npm start"