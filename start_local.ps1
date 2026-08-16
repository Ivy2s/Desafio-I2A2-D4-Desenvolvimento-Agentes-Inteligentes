$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RootDir

$APIHost = if ($env:API_HOST) { $env:API_HOST } else { "127.0.0.1" }
$APIPort = if ($env:API_PORT) { $env:API_PORT } else { "18005" }
$FrontendHost = if ($env:FRONTEND_HOST) { $env:FRONTEND_HOST } else { "0.0.0.0" }
$FrontendPort = if ($env:FRONTEND_PORT) { $env:FRONTEND_PORT } else { "15179" }
$APIUrl = "http://${APIHost}:${APIPort}"

if (-not (Test-Path (Join-Path $RootDir ".env"))) {
    $envExample = Join-Path $RootDir ".env.example"
    if (Test-Path $envExample) {
        Copy-Item $envExample (Join-Path $RootDir ".env")
        Write-Host "Arquivo .env criado a partir de .env.example. Edite-o com a chave do provedor antes de continuar."
    }
}

$venvPython = Join-Path $RootDir ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Preparando ambiente virtual Python..."
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv (Join-Path $RootDir ".venv")
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv (Join-Path $RootDir ".venv")
    }
    else {
        throw "Python 3.11 ou superior não foi encontrado. Instale o Python e tente novamente."
    }
}

if (-not (Test-Path $venvPython)) {
    throw "Não foi possível criar o ambiente virtual .venv."
}

$versionOutput = & $venvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
if (-not $versionOutput) {
    throw "Não foi possível validar a versão do Python no ambiente virtual."
}

$versionText = ($versionOutput | Select-Object -First 1).Trim()
$version = [version]$versionText
if ($version.Major -lt 3 -or ($version.Major -eq 3 -and $version.Minor -lt 11)) {
    throw "Este projeto requer Python 3.11 ou superior. Versão atual: $versionText"
}

$dependencyCheck = $null
try {
    $dependencyCheck = & $venvPython -c "import dotenv, fastapi, langchain_core, langchain_google_genai, langchain_groq, multipart, pandas, uvicorn; print('ok')" 2>$null
}
catch {
    $dependencyCheck = $null
}

if (-not $dependencyCheck) {
    Write-Host "Instalando dependências Python..."
    & $venvPython -m pip install -r (Join-Path $RootDir "requirements.txt")
}

function Ensure-NodeJsInstalled {
    $nodeCommand = Get-Command node -ErrorAction SilentlyContinue
    $npmCommand = Get-Command npm -ErrorAction SilentlyContinue

    if ($nodeCommand -and $npmCommand) {
        $nodeVersion = (& node -p "process.versions.node.split('.')[0]") 2>$null
        if ($nodeVersion -and [int]$nodeVersion -ge 20) {
            return
        }
    }

    Write-Host "Node.js 20+ e npm não foram encontrados. Tentando instalar automaticamente..."

    $installSucceeded = $false

    if (Get-Command winget -ErrorAction SilentlyContinue) {
        try {
            & winget install --id OpenJS.NodeJS.LTS --source winget --accept-source-agreements --accept-package-agreements --silent
            if ($LASTEXITCODE -eq 0) {
                $installSucceeded = $true
            }
        }
        catch {
            Write-Host "winget falhou: $($_.Exception.Message)"
        }
    }

    if (-not $installSucceeded -and (Get-Command choco -ErrorAction SilentlyContinue)) {
        try {
            & choco install nodejs-lts -y --no-progress
            if ($LASTEXITCODE -eq 0) {
                $installSucceeded = $true
            }
        }
        catch {
            Write-Host "Chocolatey falhou: $($_.Exception.Message)"
        }
    }

    if (-not $installSucceeded) {
        try {
            $nodejsIndexUrl = "https://nodejs.org/dist/index.tab"
            $indexResponse = Invoke-WebRequest -Uri $nodejsIndexUrl -UseBasicParsing -TimeoutSec 30
            $latestNodeLine = ($indexResponse.Content -split "`r?`n" | Where-Object { $_ -match 'win-x64\.msi$' -and $_ -match 'v20\.|v22\.|v24\.' } | Select-Object -First 1)

            if (-not $latestNodeLine) {
                $latestNodeLine = ($indexResponse.Content -split "`r?`n" | Where-Object { $_ -match 'win-x64\.msi$' } | Select-Object -First 1)
            }

            if ($latestNodeLine) {
                $downloadPath = ($latestNodeLine -split "`t")[0]
                $nodeDownloadUrl = "https://nodejs.org/dist/$downloadPath"
                $installerPath = Join-Path $env:TEMP "node-vlts-installer.msi"

                Write-Host "Baixando instalador oficial do Node.js em: $nodeDownloadUrl"
                Invoke-WebRequest -Uri $nodeDownloadUrl -OutFile $installerPath -UseBasicParsing -TimeoutSec 60
                Start-Process msiexec.exe -Wait -ArgumentList "/i `"$installerPath`" /quiet /norestart"
                $installSucceeded = $true
            }
        }
        catch {
            Write-Host "Instalação direta falhou: $($_.Exception.Message)"
        }
    }

    $nodeInstallDirs = @(
        "$env:ProgramFiles\nodejs",
        "$env:ProgramFiles(x86)\nodejs",
        "$env:LOCALAPPDATA\Programs\nodejs",
        "$env:USERPROFILE\AppData\Roaming\npm"
    )

    foreach ($dir in $nodeInstallDirs) {
        if (Test-Path $dir) {
            $env:Path = "$dir;$env:Path"
        }
    }

    $nodeCommand = Get-Command node -ErrorAction SilentlyContinue
    $npmCommand = Get-Command npm -ErrorAction SilentlyContinue

    if (-not $nodeCommand -or -not $npmCommand) {
        if (-not $installSucceeded) {
            throw "Node.js 20+ e npm não foram encontrados e não foi possível instalar automaticamente. Instale o Node.js 20+ manualmente e tente novamente."
        }

        throw "A instalação do Node.js foi concluída, mas o comando node/npm ainda não está disponível no PATH. Feche e reabra o terminal e execute o script novamente."
    }

    $nodeVersion = (& node -p "process.versions.node.split('.')[0]") 2>$null
    if (-not $nodeVersion -or [int]$nodeVersion -lt 20) {
        throw "Este projeto requer Node.js 20 ou superior."
    }
}

Ensure-NodeJsInstalled

$frontendNodeModules = Join-Path $RootDir "frontend\node_modules\.bin\vite.cmd"
$frontendDir = Join-Path $RootDir "frontend"
if (-not (Test-Path $frontendNodeModules)) {
    Write-Host "Instalando dependências do frontend..."
    $npmExe = (Get-Command npm -ErrorAction SilentlyContinue).Source
    if (-not $npmExe) {
        $npmExe = Join-Path $env:ProgramFiles "nodejs\npm.cmd"
    }
    if (Test-Path $npmExe) {
        Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "`"$npmExe`" --prefix `"$frontendDir`" ci" -WorkingDirectory $frontendDir -Wait -NoNewWindow
    }
    else {
        Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm --prefix `"$frontendDir`" ci" -WorkingDirectory $frontendDir -Wait -NoNewWindow
    }
}

$configError = (& $venvPython -c "from services.config import ai_configuration_error; print(ai_configuration_error() or '')") 2>$null
if ($configError -and $configError.Trim()) {
    throw "Erro de configuração: $configError`nCopie .env.example para .env e informe uma chave válida."
}

function Test-ApiHealthy {
    try {
        $null = Invoke-WebRequest -Uri "$APIUrl/api/health" -TimeoutSec 2 -UseBasicParsing
        return $true
    }
    catch {
        return $false
    }
}

if (Test-ApiHealthy) {
    throw "Já existe uma API respondendo em $APIUrl. Feche o processo atual antes de reiniciar."
}

Write-Host "Iniciando backend..."
$backendProcess = Start-Process -FilePath $venvPython -ArgumentList @("-m", "uvicorn", "api.main:app", "--host", $APIHost, "--port", $APIPort) -WorkingDirectory $RootDir -PassThru

for ($attempt = 0; $attempt -lt 60; $attempt++) {
    if (Test-ApiHealthy) { break }
    Start-Sleep -Milliseconds 500
}

if (-not (Test-ApiHealthy)) {
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    throw "A API não iniciou em $APIUrl"
}

$env:VITE_API_PROXY_TARGET = $APIUrl
Write-Host "Iniciando frontend..."
$frontendStartCmd = "npm --prefix `"$frontendDir`" run dev -- --host $FrontendHost --port $FrontendPort"
$frontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $frontendStartCmd -WorkingDirectory $frontendDir -PassThru

Write-Host ""
Write-Host "Frontend: http://${FrontendHost}:${FrontendPort}"
Write-Host "Backend:  ${APIUrl}"
Write-Host ""
Write-Host "Processos iniciados com sucesso."
Write-Host "Para encerrar, use: Stop-Process -Id $($backendProcess.Id), $($frontendProcess.Id)"

try {
    Wait-Process -Id $backendProcess.Id, $frontendProcess.Id
}
finally {
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
}
