@echo off

rem Install Poetry
cmd /k "py -m pip install --upgrade pip && exit"
cmd /k "py -m pip install poetry==1.3.2 && exit"

rem Install Poetry modules
cmd /k "cd .. && py -m poetry install && exit"

rem Check the versions of Poetry
setlocal
for /f "usebackq delims=" %%B in (`py -m poetry --version`) do set PoetryVer=%%B
echo %PoetryVer%
echo %PoetryVer% >> install_poetry.log
endlocal

echo === Poetry installed libraries. === >> install_poetry.log
cmd /k "cd .. && py -m poetry show && exit" >> install_poetry.log

cmd /k
