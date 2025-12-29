Param()

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $MyInvocation.MyCommand.Path -Parent
Set-Location $projectRoot

$venvPath = Join-Path $projectRoot '.venv'
if (-Not (Test-Path $venvPath)) {
    Write-Host 'Создаю виртуальное окружение...'
    python -m venv $venvPath
}

$python = Join-Path $venvPath 'Scripts\python.exe'
Write-Host 'Устанавливаю зависимости...'
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt

$dataDir = Join-Path $projectRoot 'data'
if (-Not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir | Out-Null
}

$logsDir = Join-Path $projectRoot 'logs'
if (-Not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}

$envPath = Join-Path $projectRoot '.env'
if (-Not (Test-Path $envPath)) {
    @(
        'TELEGRAM_BOT_TOKEN=',
        'OPENAI_API_KEY=',
        'OPENAI_MODEL=gpt-4o-mini',
        'ADMIN_TELEGRAM_ID='
    ) | Set-Content -Path $envPath -Encoding UTF8
    Write-Host 'Создан шаблон .env'
}

$settingsPath = Join-Path $dataDir 'bot_settings.json'
if (-Not (Test-Path $settingsPath)) {
    $defaultSettings = @{
        welcome_message = 'Привет! Я GOROSKOPE бот. Используй /today или /week, чтобы получить гороскоп. Без подписки доступен один бесплатный прогноз в сутки.'
        system_prompt   = 'Ты дружелюбный астролог. Пиши лаконичные и вдохновляющие гороскопы, избегай повторов и клише.'
    } | ConvertTo-Json -Depth 3
    Set-Content -Path $settingsPath -Value $defaultSettings -Encoding UTF8
    Write-Host 'Создан файл data/bot_settings.json'
}

Write-Host 'Готово.'
