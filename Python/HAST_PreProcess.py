#AUTHOR             : UJVALA K SHARMA
#SCRIPT NAME        : HAST_PreProcess.py
#COMPANY            : RISKMAP CDS
#DATE               : 09/10/19
#VERSION            : 1.0
#PURPOSE            : This pyhton script can be used to assign HU attributes to structure level datasets
#                     and perform loss analysis. Version 1.0 does not use the detailed Wind attributes.


import numpy as np
import pandas as pd
import geopandas as gpd
from geopandas import GeoDataFrame
from shapely.geometry import Point, LineString
from scipy import interpolate
import os,sys,time
import xml.etree.ElementTree as ET
import tkinter as tk, datetime
from tkinter import ttk
import logging
import utility
    
def HAST_dataPrep():

    
    gsTERRAINID = 'TERRAINID'
    gsWBID = 'WBID'
    
    #The input files and full path will be read from the GUI
    #Fetch file names from XML   
    tree = ET.parse('settings.xml')
    sLUTPath = tree.find('.//LUTPath').text
    sGeoJsonFileName = tree.find('.//CBGeoJson').text
    sInputFileName = tree.find('.//InputFileName').text
    sTerrainIDFileName = tree.find('.//TerrainIDFName').text
    sSurfaceRoughnessFileName = tree.find('.//SurfaceRoughNess').text
    sDfltWbIdFileName = tree.find('.//WbIdFName').text
    sInputPath = tree.find('.//InputPath').text
    sSateID = tree.find('.//stateID').text    
    sCBFldName = 'CENSUSBLOCK'    
    sSBTFldName = 'SBTNAME'
    sTractIDFieldName = 'TRACT_ID_GEN'   
    sPreProcessedDataFileName = os.path.splitext(sInputFileName)[0] + "_pre_processed.csv"
    
    #Logging setup
    LogFileName = tree.find('.//LogFileName').text
    Level = tree.find('.//Level').text
    if Level == 'INFO': 
        logging.basicConfig(filename=LogFileName, filemode='w', level=logging.INFO)
    else: 
        logging.basicConfig(filename=LogFileName, filemode='w', level=logging.DEBUG)
        
    logging.info(str(datetime.datetime.now())+ ' Pre-Processing Begin... ')
    
    
    #utility.popupmsg(sPreProcessedDataFileName)
    
    #Fecth field names of the input selected
    for item in tree.find('.//PreProcessingFields'):
        logging.debug(str(datetime.datetime.now())+ ' PreProcessingFields: ' + item.tag)
        if item.tag == 'SOID':
            sSoccIdFieldName = item.attrib['inputFieldName']
        elif item.tag == 'WBID':
            sWbIDFieldName = item.attrib['inputFieldName']
        elif item.tag == 'TerrainID':
            sTerrainIDFldName = item.attrib['inputFieldName']
        elif item.tag == 'HUSBT':
            sHuSBTFldName = item.attrib['inputFieldName']
        elif item.tag == 'Longitude':
            sLongitude = item.attrib['inputFieldName'] 
        elif item.tag == 'Latitude':
            sLatitude = item.attrib['inputFieldName']
    
    if sTerrainIDFldName == '':
        sTerrainIDFldName = gsTERRAINID
        
    if sWbIDFieldName == '':
        sWbIDFieldName = gsWBID
    #Read the input UDF dataset from the XML
    df_Input = pd.read_csv(sInputFileName, delimiter = None,encoding = "ISO-8859-1")    
    df_Input.columns = [x.upper() for x in df_Input.columns]
   
    #Check if TerrainID is a part of the input data (df_Input). If not then perform the following joins
    #If the user has provided the TerraID check if wbID is provided.     
    #print("Validating input data set...")
    logging.info(str(datetime.datetime.now())+" Validating inputs for required fields...")
    logging.debug(str(datetime.datetime.now())+" Validating started...")
    if sTerrainIDFldName in df_Input.columns:
        #print("Yes" , sLUTPath + sTerrainIDFileName)
        logging.debug(str(datetime.datetime.now())+" Inside checking TerrainID" + str(sLUTPath) + str(sTerrainIDFileName))

        #Check the data if the entries are valid
        df_TerrainID = pd.read_csv(sLUTPath + sTerrainIDFileName, delimiter = None)
        logging.debug(str(datetime.datetime.now())+' Check 2: df_TerrainID ' )        
        #print(2)
        
        df_TerrainID.columns = [x.upper() for x in df_TerrainID.columns]
        logging.debug(str(datetime.datetime.now())+ ' Check 3: f_TerrainID.columns '+ str(df_TerrainID.columns))        
        #print(3)  
        
        df_ValidateTr = pd.merge(df_Input.astype(str), df_TerrainID.astype(str),left_on = sTerrainIDFldName ,right_on = gsTERRAINID, how = "inner", suffixes=('_left', '_right'))
        logging.debug(str(datetime.datetime.now()) + ' Check 4: df_ValidateTr ')        
        #print(4)
        
        numOfRowsInput = len(df_Input.index)
        numOfRowsmatched = len(df_ValidateTr.index)
        
        #print(str(numOfRowsmatched))
        logging.debug(str(datetime.datetime.now())+' Number of Rows Matched: '+str(numOfRowsmatched))
        if numOfRowsmatched != numOfRowsInput:
            utility.popupmsg("Please check TerrainIDs so that they match with the " + sSurfaceRoughnessFileName + " looktup table.")
            logging.info(str(datetime.datetime.now())+" Please check TerrainIDs so that they match with the " + sSurfaceRoughnessFileName + " looktup table.")
            #print(df_TerrainID)
            sys.exit()
        elif sWbIDFieldName in df_Input.columns:
            #print("Checking field WbId")
            #print("Yes")
            logging.info(str(datetime.datetime.now())+' All TerrainIDs match! ')
            
            logging.debug(str(datetime.datetime.now())+' Checking field WbId: ' + str(sWbIDFieldName))
            
            #Check the data if the entries are valid
            df_WbID = pd.read_csv(sLUTPath + sDfltWbIdFileName, delimiter = None) 
            logging.debug(str(datetime.datetime.now())+' Check 5: df_WbID ')
            #print(5)
            
            df_WbID.columns = [x.upper() for x in df_WbID.columns]
            logging.debug(str(datetime.datetime.now())+' Check 6: df_WbID.columns ' + str(df_WbID.columns))
            #print(6)
        
            df_ValidateWb = pd.merge(df_Input.astype(str), df_WbID.astype(str),left_on = sWbIDFieldName,right_on = gsWBID, how = "inner", suffixes=('_left', '_right'))
            logging.debug(str(datetime.datetime.now())+' Check 7: df_ValidateWb ' )
            #print(7)
            
            numOfRowsInput = len(df_Input.index)
            numOfRowsmatched = len(df_ValidateWb.index)
            logging.info(str(datetime.datetime.now())+' Num of Rows Matched: ' + str(numOfRowsmatched))
            #print(str(numOfRowsmatched))
        
            if numOfRowsmatched != numOfRowsInput:
                logging.debug(str(datetime.datetime.now())+" Please check WbIds so that they match with the " + sDfltWbIdFileName[1:1 + len(sDfltWbIdFileName)]  + " looktup table.")
                popupmsg("Please check WbIds so that they match with the " + sDfltWbIdFileName[1:1 + len(sDfltWbIdFileName)]  + " looktup table.")
                sys.exit()
        logging.info(str(datetime.datetime.now())+" TerrainIds and WbIds match. Please proceed to perform the analyses.")
        #utility.popupmsg("TerrainIds and WbIds match. Please proceed to perform the analyses.")
        #sys.exit()
    #else:
    print("Pre-Processing the input to assign HU attributes...")
    logging.info(str(datetime.datetime.now())+' Pre-Processing input dataset to add the HU attributes...')
    #print("No")
    
    #CB data
    df_CB = gpd.read_file(sLUTPath + sGeoJsonFileName)
    df_CB.columns = [x.lower() for x in df_CB.columns] #setting to lower for the spatial join
    logging.debug(str(datetime.datetime.now())+' Check 8: df_CB.columns ' + str(df_CB.columns))
    #print(8)
    
    #SR LUT
    df_SuRCB = pd.read_csv(sLUTPath+sSurfaceRoughnessFileName , delimiter = None)
    df_SuRCB.columns = [x.upper() for x in df_SuRCB.columns]
    logging.debug(str(datetime.datetime.now())+' Check 9: df_SuRCB.columns ' + str(df_SuRCB.columns))
    #print(9)
    
    #WbId LUT
    df_WbId = pd.read_csv(sLUTPath + sDfltWbIdFileName, delimiter = None)
    df_WbId.columns = [x.upper() for x in df_WbId.columns]
    logging.debug(str(datetime.datetime.now())+' Check 10: df_WbId.columns ' +str(df_WbId.columns))
    #print(10)
    
    #Latitude and Longitude validation for the future
    #df_CheckLatLong = df_Input.apply(lambda row: (df_input['Longitude'].astype(str)=='' | df_input['Latitude'].astype(str)=='') , axis=1)

    #Longitude,Latitude field names now referenced from settings.xml
    geometry = [Point(xy) for xy in zip(df_Input[sLongitude], df_Input[sLatitude])]        
    crs = {'init': 'epsg:4326'}
    #logging.debug(str(datetime.datetime.now())+' Check 11: geometry ' + str(geometry))
    #print(11)
    
    #Join between structure level data and Census block to fecth the CBID
    #Check if any geometries are NULL
    df_Input = GeoDataFrame(df_Input, geometry=geometry, crs=crs)
    logging.debug(str(datetime.datetime.now())+' Check 12: df_Input ')
    #print(12)
    
    #Join the structure level input points to the hzCensusblock_TIGER to fetch the CBID
    if sCBFldName in df_Input.columns:
        df_Input.rename(columns={sCBFldName : sCBFldName + '_OLD'}, inplace=True)
    points_CBId = gpd.sjoin(df_Input, df_CB, how="inner", op='intersects')
    points_CBId.columns = [x.upper() for x in points_CBId.columns]        
    logging.debug(str(datetime.datetime.now())+' Check 13: points_CBId.columns ' + str(points_CBId.columns))
    
    #Fetch Surface Roughness from huTerrainB in the respective state
    if sSateID != 'VI':
        if gsTERRAINID not in df_Input.columns:
            points_CBSR = pd.merge(points_CBId.astype(str), df_SuRCB.astype(str),on = sCBFldName, how = "inner", suffixes=('_left', '_right'))  
            points_CBSR.columns = [x.upper() for x in points_CBSR.columns]
            logging.debug(str(datetime.datetime.now())+' Check 14: points_CBSR.columns ' + str(points_CBSR.columns))
            #TerrainID assignment from Surface Roughness Values
            #if sTerrainIDFldName == '':
            #    sTerrainIDFldName = gsTERRAINID
            points_CBSR[sTerrainIDFldName] = points_CBSR.apply (lambda row: get_terrainId(row), axis=1)
            logging.debug(str(datetime.datetime.now())+' Check 15: points_CBSR[sTerrainIDFldName] ' )
        else:
            points_CBSR = points_CBId
    else:
        #if sTerrainIDFldName == '':
        #    sTerrainIDFldName = gsTERRAINID            
        points_CBSR = points_CBId
        #df_Input.rename(columns={sCBFldName + '_OLD':sCBFldName}, inplace=True)
        if gsTERRAINID not in points_CBSR.columns:
            points_CBSR[sTerrainIDFldName] = 1

    #Assign the WbID on the basis of the HUSBT in the input
    if 'WBID' in points_CBSR.columns:
        points_CBSR = points_CBSR.drop(['WBID'], axis=1)   
    points_CBSR = pd.merge(points_CBSR.astype(str), df_WbId.astype(str),left_on=sHuSBTFldName, right_on=sSBTFldName,how="inner",suffixes=('_left', '_right'))
    logging.debug(str(datetime.datetime.now())+' Check 16: points_CBSR ' )
    logging.info(str(datetime.datetime.now())+ ' TERRAINID and WBID assignned... ' )
    
    #TRACTID added - avoid fetching for each record
    points_CBSR[sTractIDFieldName] = points_CBSR[sCBFldName].str[:11]

    #del cols
    if '' in points_CBSR.columns:
        points_CBSR = points_CBSR.drop([''], axis=1)
    if 'GEOMETRY' in points_CBSR.columns:
        points_CBSR = points_CBSR.drop(['GEOMETRY'], axis=1)            
    if 'INDEX_RIGHT' in points_CBSR.columns:
        points_CBSR = points_CBSR.drop(['INDEX_RIGHT'], axis=1)                        
    if 'OBJECTID_RIGHT' in points_CBSR.columns:
        points_CBSR = points_CBSR.drop(['OBJECTID_RIGHT'], axis=1)            
    if sSBTFldName in points_CBSR.columns:
        points_CBSR = points_CBSR.drop([sSBTFldName], axis=1)                        
    if 'SURFACEROUGHNESS' in points_CBSR.columns:
        points_CBSR = points_CBSR.drop(['SURFACEROUGHNESS'], axis=1)               
    if 'SRINDEX' in points_CBSR.columns:
        points_CBSR = points_CBSR.drop(['SRINDEX'], axis=1)                       
    if 'CHARDESCRIPTION' in points_CBSR.columns:
        points_CBSR = points_CBSR.drop(['CHARDESCRIPTION'], axis=1)                        
    if 'CASEID' in points_CBSR.columns:
        points_CBSR = points_CBSR.drop(['CASEID'], axis=1)                       
    if 'NWINDCHAR' in points_CBSR.columns:        
        points_CBSR = points_CBSR.drop(['NWINDCHAR'], axis=1)
    if 'CENSUSBLOCK_OLD' in points_CBSR.columns:    
        points_CBSR = points_CBSR.drop(['CENSUSBLOCK_OLD'], axis=1)            
    if 'OBJECTID' in points_CBSR.columns:
        points_CBSR = points_CBSR.drop(['OBJECTID'], axis=1)          
    points_CBSR = points_CBSR.loc[:, ~points_CBSR.columns.str.contains('^UNNAMED')]
    points_CBSR = points_CBSR[points_CBSR.columns.dropna()]
    
    #print(points_CBSR)
    #XML assignments if TERRAINID, WBID not in base data
    item = tree.getroot().find('.//TerrainID')
    item.attrib['inputFieldName'] = sTerrainIDFldName #gsTERRAINID

    item = tree.getroot().find('.//WBID')
    item.attrib['inputFieldName'] = sWbIDFieldName #gsWBID

    item = tree.getroot().find('.//CensusBlockID')
    item.attrib['inputFieldName'] = sCBFldName
    
    tree.getroot().find('.//PreProcessedDataFileName').text = sPreProcessedDataFileName
    
    tree.write('settings.xml')
    
    #Making sure all column names are caps
    points_CBId.columns = [x.upper() for x in points_CBId.columns]
    points_CBSR.to_csv(sPreProcessedDataFileName) 

    logging.info(str(datetime.datetime.now())+' Pre-Processing Complete...')
    print("Pre-Processing Complete...")      
        
def get_terrainId (row):
    if float(row['SURFACEROUGHNESS']) >= 0 and float(row['SURFACEROUGHNESS']) <= 0.03 :
        return 1
    if float(row['SURFACEROUGHNESS']) > 0.03 and float(row['SURFACEROUGHNESS']) <= 0.15 :
        return 2
    if float(row['SURFACEROUGHNESS']) > 0.15 and float(row['SURFACEROUGHNESS']) <= 0.35 :
        return 3
    if float(row['SURFACEROUGHNESS']) > 0.35 and float(row['SURFACEROUGHNESS']) <= 0.70 :
        return 4
    if float(row['SURFACEROUGHNESS']) > 0.70 and float(row['SURFACEROUGHNESS']) <= 1.00 :
        return 5
    return -1        
"""        
def popupmsg(msg):
    NORM_FONT= ("Tahoma", 10)
    popup = tk.Tk()
    popup.wm_title("!")
    label = ttk.Label(popup, text=msg, font=NORM_FONT)
    label.pack(side="top", fill="x", pady=10)
    B1 = ttk.Button(popup, text="Okay", command = popup.destroy)
    B1.pack()
    popup.mainloop()
"""   