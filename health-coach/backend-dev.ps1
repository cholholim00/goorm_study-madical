param(
    # install / migrate / dev / all 중 하나를 바로 넘길 수도 있음
    [string]$Action
)

$ErrorActionPreference = "Stop"

# 이 스크립트가 있는 폴더 기준으로 경로 계산
$root = $PSScriptRoot
$backendPath = Join-Path $root "health-coach-backend"

if (!(Test-Path $backendPath)) {
    Write-Error "백엔드 폴더를 찾을 수 없습니다: $backendPath"
    exit 1
}

Set-Location $backendPath
Write-Host "📂 Backend 디렉터리:" (Get-Location).Path

if (-not $Action) {
    Write-Host ""
    Write-Host "=== AI 혈압 코치 백엔드 스크립트 ===" -ForegroundColor Cyan
    Write-Host "1) npm install"
    Write-Host "2) Prisma migrate dev"
    Write-Host "3) dev 서버 실행 (npm run dev)"
    Write-Host "4) 1 → 2 → 3 순서로 모두 실행"
    Write-Host ""
    $Action = Read-Host "번호를 선택하거나 (install/migrate/dev/all) 중 하나를 입력하세요"
}

switch ($Action) {
    "1" { $Action = "install" }
    "2" { $Action = "migrate" }
    "3" { $Action = "dev" }
    "4" { $Action = "all" }
}

switch ($Action.ToLower()) {
    "install" {
        Write-Host "📦 npm install 실행 중..." -ForegroundColor Yellow
        npm install
    }
    "migrate" {
        Write-Host "🔧 npx prisma migrate dev 실행 중..." -ForegroundColor Yellow
        npx prisma migrate dev
    }
    "dev" {
        Write-Host "🚀 npm run dev 실행 중..." -ForegroundColor Green
        npm run dev
    }
    "all" {
        Write-Host "📦 npm install 실행 중..." -ForegroundColor Yellow
        npm install

        Write-Host "🔧 npx prisma migrate dev 실행 중..." -ForegroundColor Yellow
        npx prisma migrate dev

        Write-Host "🚀 npm run dev 실행 중..." -ForegroundColor Green
        npm run dev
    }
    default {
        Write-Error "알 수 없는 Action 입니다: $Action (install / migrate / dev / all 사용 가능)"
    }
}
