$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$python = Get-Command python -ErrorAction SilentlyContinue

if (-not $python) {
	throw "Python não encontrado no PATH. Instale Python 3.10+ e execute este script novamente."
}

$venv = Join-Path $backend "venv"
if (-not (Test-Path $venv)) {
	& $python.Source -m venv $venv
}

$venvPython = Join-Path $venv "Scripts\python.exe"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $backend "requirements.txt")

$npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $npmCommand) {
	$npmPath = Join-Path ${env:ProgramFiles} "nodejs\npm.cmd"
	if (Test-Path $npmPath) {
		$env:Path = "$(Split-Path $npmPath);$env:Path"
		$npmCommand = Get-Command $npmPath
	}
}

if (-not $npmCommand) {
	throw "Node.js/npm não encontrado. Instale Node.js 18+ e execute este script novamente."
}

Start-Process powershell -WorkingDirectory $backend -ArgumentList "-NoExit", "-Command", "& '$venvPython' 'app.py'"
Push-Location $frontend
try {
	& $npmCommand.Source install
} finally {
	Pop-Location
}
Start-Process powershell -WorkingDirectory $frontend -ArgumentList "-NoExit", "-Command", "& '$($npmCommand.Source)' start"