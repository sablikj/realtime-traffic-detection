import os
import platform
import time
import pyodbc
import pandas as pd
import warnings
from dotenv import load_dotenv

from utils import saveData

warnings.filterwarnings("ignore")
load_dotenv()

if platform.system() == 'Windows':
    driver = os.getenv('DB_DRIVER_WIN')
else:
    driver = os.getenv('DB_DRIVER_LINUX')

conn = pyodbc.connect(
    f"Driver={driver};"
    f"Server={os.getenv('DB_SERVER')};"
    f"Database={os.getenv('DB_DATABASE')};"
    f"UID={os.getenv('DB_USERNAME')};"
    f"PWD={os.getenv('DB_PASSWORD')};"
    "TrustServerCertificate=YES"
)

"""
Returns vehicle data from the current day
"""
def fetchToday():
    data = pd.DataFrame()
    sql = "select v.VehicleID, v.Class, v.IntersectionOrigin, v.IntersectionExit, v.Timestamp from Vehicles as v where cast(Timestamp as Date) = cast(datetime.today().strftime('%d-%m-%Y') as Date)"
    try:
        data = pd.read_sql(sql, conn)
    except:
        print('Failed to fetch data from database!')

    return data

"""
Returns last vehicle ID in the database
"""
def getLastID():
    cursor = conn.cursor()
    id = cursor.execute('select max(VehicleID) from Vehicles').fetchone()
    conn.commit
    cursor.close

    return id[0]


"""
Function for saving vehicle data and postition points
to the database. If connection to database fails, data
are saved locally.
"""
def insert(data, points):
    try:
        t1 = time.time()
        cursor = conn.cursor()    
        cursor.fast_executemany = True

        #Find last VehicleID in db
        lastID = getLastID()
        data = data.loc[(data['VehicleID'] > lastID)]    

        # Insert Dataframe into SQL Server:
        for index, v in data.iterrows():
            cursor.execute("INSERT INTO Vehicles(VehicleID, Class, IntersectionOrigin, IntersectionExit, Timestamp) values(?,?,?,?,?)", v['VehicleID'], v['Class'], v['IntersectionOrigin'], v['IntersectionExit'], v['Timestamp'])
        for index, point in points.iterrows():
            cursor.execute("INSERT INTO PositionPoints(X_point, Y_point, VehicleID) values (?,?,?)", point['X_point'], point['Y_point'], point['VehicleID'])

        print('Succesfully saved data to DB in {0}.'.format(time.time() - t1))
        conn.commit()
        cursor.close()
    except:
        print('Failed to save data to the database! Saving locally instead.')
        saveData(data, points)


"""
Returns vehicle data or posision points from specified time period
"""
def download(dateFrom, dateTo, value):
    data = pd.DataFrame()
    sqlVehicles = "select v.VehicleID, v.Class, v.IntersectionOrigin, v.IntersectionExit, v.Timestamp from Vehicles as v where cast(v.Timestamp as Date) between cast('{0}' as Date) and cast('{1}' as Date)".format(dateFrom, dateTo)
    
    try:
        data = pd.read_sql(sqlVehicles, conn)
        data = data.set_index(pd.Index(['VehicleID']))
    except:
        print('Failed to fetch data from database!')

    if value == 'Vehicles':
        return data

    if value == 'Points':       
        sqlPoints = "select p.X_point, p.Y_point, p.VehicleID from PositionPoints as p where p.VehicleID between {0} and {1}".format(data['VehicleID'].min(), data['VehicleID'].max())
        try:
            data = pd.read_sql(sqlPoints, conn)
            data = data.set_index(pd.Index(['VehicleID']))
        except:
            print('Failed to fetch data from database!')
    
        return data