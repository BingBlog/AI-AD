@echo off
REM 广告案例库统一启动脚本 (Windows)
REM 用途：统一启动前后端服务，确保使用正确的配置和环境

setlocal enabledelayedexpansion

echo ========================================
echo 广告案例库统一启动脚本
echo ========================================

REM 项目根目录
set "PROJECT_ROOT=%~dp0"
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "FRONTEND_DIR=%PROJECT_ROOT%frontend"

REM 1. 检查必要的目录和文件
echo.
echo [1/6] 检查项目结构...
if not exist "%BACKEND_DIR%" (
    echo ❌ 后端目录不存在: %BACKEND_DIR%
    exit /b 1
)
if not exist "%FRONTEND_DIR%" (
    echo ❌ 前端目录不存在: %FRONTEND_DIR%
    exit /b 1
)
echo ✅ 项目结构检查通过

REM 2. 检查后端环境变量文件
echo.
echo [2/6] 检查后端环境配置...
set "BACKEND_ENV=%BACKEND_DIR%\.env"
if not exist "%BACKEND_ENV%" (
    echo ⚠️  后端 .env 文件不存在，从 env.example 创建...
    if exist "%BACKEND_DIR%\env.example" (
        copy "%BACKEND_DIR%\env.example" "%BACKEND_ENV%"
        echo ⚠️  请编辑 %BACKEND_ENV% 文件，设置正确的配置（特别是数据库和向量模型路径）
        echo ⚠️  按 Enter 继续，或 Ctrl+C 退出进行配置...
        pause
    ) else (
        echo ❌ env.example 文件不存在
        exit /b 1
    )
)
echo ✅ 后端环境配置检查通过

REM 3. 检查数据库连接（需要 psql 命令）
echo.
echo [3/6] 检查数据库连接...
where psql >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  请手动验证数据库连接
    echo ⚠️  使用命令: psql -h localhost -p 5432 -U bing -d ad_case_db -c "SELECT 1;"
) else (
    echo ⚠️  psql 命令未找到，跳过数据库连接检查
)

REM 4. 检查 Python 虚拟环境
echo.
echo [4/6] 检查 Python 虚拟环境...
if "%VIRTUAL_ENV%"=="" (
    REM 尝试查找常见的虚拟环境目录
    set "VENV_FOUND=0"
    for %%d in ("%BACKEND_DIR%\venv" "%BACKEND_DIR%\.venv" "%PROJECT_ROOT%venv" "%PROJECT_ROOT%.venv") do (
        if exist "%%d\Scripts\activate.bat" (
            echo ⚠️  发现虚拟环境: %%d
            echo ⚠️  正在激活虚拟环境...
            call "%%d\Scripts\activate.bat"
            set "VENV_FOUND=1"
            goto :venv_found
        )
    )
    :venv_found
    if !VENV_FOUND! equ 0 (
        echo ❌ 未找到 Python 虚拟环境
        echo ⚠️  请创建虚拟环境：
        echo    cd %BACKEND_DIR%
        echo    python -m venv venv
        echo    venv\Scripts\activate
        echo    pip install -r requirements.txt
        exit /b 1
    )
) else (
    echo ✅ 虚拟环境已激活: %VIRTUAL_ENV%
)

REM 验证 Python 和依赖
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ FastAPI 未安装，请运行: pip install -r %BACKEND_DIR%\requirements.txt
    exit /b 1
)
echo ✅ Python 环境检查通过

REM 5. 检查前端依赖
echo.
echo [5/6] 检查前端环境...
if not exist "%FRONTEND_DIR%\node_modules" (
    echo ⚠️  前端依赖未安装，正在安装...
    cd /d "%FRONTEND_DIR%"
    where pnpm >nul 2>&1
    if %errorlevel% equ 0 (
        call pnpm install
    ) else (
        where npm >nul 2>&1
        if %errorlevel% equ 0 (
            call npm install
        ) else (
            echo ❌ 未找到 pnpm 或 npm
            exit /b 1
        )
    )
    cd /d "%PROJECT_ROOT%"
)

REM 检查前端环境变量
set "FRONTEND_ENV=%FRONTEND_DIR%\.env.local"
if not exist "%FRONTEND_ENV%" (
    if exist "%FRONTEND_DIR%\env.example" (
        echo ⚠️  前端 .env.local 文件不存在，从 env.example 创建...
        copy "%FRONTEND_DIR%\env.example" "%FRONTEND_ENV%"
    )
)
echo ✅ 前端环境检查通过

REM 6. 启动服务
echo.
echo [6/6] 启动服务...

REM 启动后端服务
echo 🚀 启动后端服务 (端口 8000)...
cd /d "%BACKEND_DIR%"
start "后端服务" cmd /k "python run.py"
timeout /t 3 /nobreak >nul

REM 启动前端服务
echo 🚀 启动前端服务 (端口 3000)...
cd /d "%FRONTEND_DIR%"
where pnpm >nul 2>&1
if %errorlevel% equ 0 (
    start "前端服务" cmd /k "pnpm run dev"
) else (
    start "前端服务" cmd /k "npm run dev"
)

cd /d "%PROJECT_ROOT%"

echo.
echo ========================================
echo ✅ 所有服务已启动
echo ========================================
echo 后端 API: http://localhost:8000
echo 前端应用: http://localhost:3000
echo API 文档: http://localhost:8000/docs
echo.
echo 服务已在新的窗口中启动
echo 关闭窗口即可停止相应的服务

pause
