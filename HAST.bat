@echo off

REM SET PATH=%cd%\python\conda_env\Scripts;%cd%\python\conda_env\Lib\site-packages;%cd%\python\conda_env;%cd%\python\conda_env\DLLs;%cd%conda_env\Lib\site-packages\fiona;%cd%conda_env\Lib\site-packages\PIL;%cd%\python\conda_env\Lib\site-packages\GDAL;%cd%\python\conda_env\Lib\site-packages\geopandas;%cd%\python\conda_env\Lib\site-packages\numpy%SystemRoot%\system32;%PATH%;

REM SET PYTHONPATH=%cd%\python\conda_env\Scripts;%cd%\python\conda_env\Lib\site-packages;%cd%\python\conda_env;%cd%\python\conda_env\DLLs;%cd%conda_env\Lib\site-packages\fiona;%cd%conda_env\Lib\site-packages\PIL;%cd%\python\conda_env\Lib\site-packages\GDAL;%cd%\python\conda_env\Lib\site-packages\geopandas;%cd%\python\conda_env\Lib\site-packages\numpy%SystemRoot%\system32;%PYTHONPATH%;

rem cd .\python\scripts
call activate conda_env
rem cd ..
cd .\python
python HAST_Main_GUI.py 
