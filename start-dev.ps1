# 一键启动开发环境：在两个新窗口分别启动后端(8000)与前端(5179)
# 用法：在项目根目录右键“用 PowerShell 运行”，或执行  .\start-dev.ps1
$root = $PSScriptRoot

Start-Process powershell -ArgumentList @(
    '-NoExit', '-Command',
    "Set-Location '$root\backend'; .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000"
)

Start-Process powershell -ArgumentList @(
    '-NoExit', '-Command',
    "Set-Location '$root\frontend'; npm run dev"
)

Write-Host ''
Write-Host '已在新窗口启动：后端 http://127.0.0.1:8000  /  前端 http://localhost:5179' -ForegroundColor Green
Write-Host '浏览器访问 http://localhost:5179 （账号 admin / admin12345）' -ForegroundColor Green
