$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$webPath = Join-Path $root "health-coach-web"

if (!(Test-Path $webPath)) {
    Write-Error "프론트엔드 폴더를 찾을 수 없습니다: $webPath"
    exit 1
}

Set-Location $webPath
Write-Host "📂 Web 디렉터리:" (Get-Location).Path

if (!(Test-Path "node_modules")) {
    Write-Host "📦 node_modules 폴더가 없어 npm install을 실행합니다..." -ForegroundColor Yellow
    npm install
} else {
    Write-Host "✅ node_modules 폴더가 이미 있습니다. (npm install 생략)" -ForegroundColor Green
}

Write-Host "🚀 Next.js dev 서버 실행 (npm run dev)..." -ForegroundColor Green
npm run dev
