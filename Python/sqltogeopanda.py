from pymssql import connect
from pandas import read_sql
from shapely.wkt import loads
from geopandas import GeoDataFrame

def rd_sql(server, database, table, col_names=None, where_col=None, where_val=None, geo_col=True, epsg='4326', export=False, path='save.csv'):
    """
    Imports data from MSSQL database, returns GeoDataFrame. Specific columns can be selected and specific queries within columns can be selected. Requires the pymssql package, which must be separately installed.
    Arguments:
    server -- The server name (str). e.g.: 'SQL2012PROD03'
    database -- The specific database within the server (str). e.g.: 'LowFlows'
    table -- The specific table within the database (str). e.g.: 'LowFlowSiteRestrictionDaily'
    col_names -- The column names that should be retrieved (list). e.g.: ['SiteID', 'BandNo', 'RecordNo']
    where_col -- The sql statement related to a specific column for selection (must be formated according to the example). e.g.: 'SnapshotType'
    where_val -- The WHERE query values for the where_col (list). e.g. ['value1', 'value2']
    geo_col -- Is there a geometry column in the table?
    epsg -- The coordinate system (int)
    export -- Should the data be exported
    path -- The path and csv name for the export if 'export' is True (str)
    """
    
    print ('1')
    if col_names is None and where_col is None:
        stmt1 = 'SELECT * FROM ' + table
    elif where_col is None:
        stmt1 = 'SELECT ' + str(col_names).replace('\'', '"')[1:-1] + ' FROM ' + table
    else:
        stmt1 = 'SELECT ' + str(col_names).replace('\'', '"')[1:-1] + ' FROM ' + table + ' WHERE ' + str([where_col]).replace('\'', '"')[1:-1] + ' IN (' + str(where_val)[1:-1] + ')'
    conn = connect(server, database=database)
    df = read_sql(stmt1, conn)
    
    print ('2')

    ## Read in geometry if required
    if geo_col:
        geo_col_stmt = "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME=" + "\'" + table + "\'" + " AND DATA_TYPE='geometry'"
        geo_col = str(read_sql(geo_col_stmt, conn).iloc[0,0])
        print (geo_col)
        if where_col is None:
            stmt2 = 'SELECT ' + geo_col + '.STGeometryN(1).ToString(),Censusblock' + ' FROM ' + table
        else:
            stmt2 = 'SELECT ' + geo_col + '.STGeometryN(1).ToString()' + ' FROM ' + table + ' WHERE ' + str([where_col]).replace('\'', '"')[1:-1] + ' IN (' + str(where_val)[1:-1] + ')'
        df2 = read_sql(stmt2, conn)
        df2.columns = ['geometry',"CensusBlock"]
        print('After assigning geometry: ' + stmt2)
        
        geometry = [loads(x) for x in df2.geometry]
        print('geom obj set')
        df = GeoDataFrame(df2, geometry=geometry, crs={'init' :'epsg:' + str(epsg)})
        print('after projection')
        df.to_file("hzCensusblock_TIGER.geojson", driver="GeoJSON")
        print ('3')
    if export:
        df.to_csv(path, index=False)

    conn.close()
    #return(df)
    
def main():
    print("Hello SQL!")
    #rd_sql('DESKTOP-QKR1K2P\HAZUSPLUSSRVR','HI','hzCensusblock_TIGER')
    rd_sql('DESKTOP-QKR1K2P\HAZUSPLUSSRVR','VI','hzCensusblock_TIGER')

if __name__ == "__main__":
    main()    