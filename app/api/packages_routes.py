from fastapi import FastAPI, APIRouter
import pkg_resources

router = APIRouter(prefix="/pkg")
import openpyxl
import paramiko
import cx_Oracle
import pymysql
import apscheduler
import httpx
import redis
import sqlite3
import websockets
import pip
import sqlalchemy
# import pymongo
# import pyodbc


@router.get("/packages")
async def list_packages():
    installed_packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
    return installed_packages
@router.get("/wanted")
async def wanted_packages():
    data={}
    data["redis"]=redis.__version__
    data["openpyxl"]=openpyxl.__version__
    data["paramiko"]=paramiko.__version__
    data["cx_Oracle"]=cx_Oracle.__version__
    data["pymysql"]=pymysql.__version__
    data["apscheduler"]=apscheduler.__version__
    data["httpx"]=httpx.__version__
    data["redis"]=redis.__version__
    data["sqlite3"]=sqlite3.version
    data["websockets"]=websockets.__version__
    data["pip"]=pip.__version__
    data["sqlalchemy"]=sqlalchemy.__version__
    # data["pymongo"]=pymongo.__version__
    # data["pyodbc"]=pyodbc.__version__
    return data

