#AUTHOR             : UJVALA K SHARMA
#SCRIPT NAME		: HAST_Analysis.py
#COMPANY            : RISKMAP CDS
#DATE               : 10/02/19
#VERSION            : 1.0
#PURPOSE            : This calculates losses for probabilistic windspeed data for 8 return periods and interpolates
#                     the probability values based on the windspeed limits from the Damage Functions data

import numpy as np
import pandas as pd
import geopandas as gpd
from geopandas import GeoDataFrame
from shapely.geometry import Point, LineString
from scipy import interpolate
import os,sys,time, datetime
import xml.etree.ElementTree as ET
import logging
import utility

def HAST_Probabilistic_Analysis():
    
    tree = ET.parse('settings.xml')
    sTractIDFieldName = 'TRACT_ID_GEN'    
    sLUTPath = tree.find('.//LUTPath').text
    #sOccupancyFieldName = 'OCCUPANCY'      
    sTractFldName = 'TRACT' #May have to move the Tract Field Name into the XML in the future for US wind data
    #sSoccIdFieldName = 'SOCCID' #Fetched below from the XML
         
    #Fecth field names of the input selected
    for item in tree.find('.//AnalysisFields'):
        logging.debug(str(datetime.datetime.now()) + ' AnalysisFields: ' + item.tag)
        if item.tag == 'SOID':
            sSoccIdFieldName = item.attrib['inputFieldName'] 

    #Logging setup
    LogFileName = tree.find('.//LogFileName').text
    Level = tree.find('.//Level').text
    if Level == 'INFO': 
        logging.basicConfig(filename=LogFileName, filemode='w', level=logging.INFO)
    else: 
        logging.basicConfig(filename=LogFileName, filemode='w', level=logging.DEBUG)            
    
    print("Analyzing HU losses for seven probabilistic return periods...")
    logging.info(str(datetime.datetime.now()) + 'Analyzing HU Losses... ')
    sPreProcessedDataFileName = tree.find('.//PreProcessedDataFileName').text
    
    points_CBSR = pd.read_csv(sPreProcessedDataFileName, delimiter = None)
    points_CBSR.columns = [x.upper() for x in points_CBSR.columns]
    points_CBSR[sSoccIdFieldName] = points_CBSR[sSoccIdFieldName].str.replace('\W', '')
    
    #print(2)
    #Need to check here(future) if the user has already supplied peak gusts for each RP (check columns & check if not null
    #if null put zero, warn that if there are zeros no losses will be generated.
    #if the windspeed is provided then PWindField will be blank and we need to calculate with the exisitng fields
    
    logging.info(str(datetime.datetime.now())+ ' Using wind speed data file provided by the user... ')

    #sProbabilisticWindSpeedFilePath = tree.find('.//PWindField').text
    #sProbabilisticWindSpeedFileName = tree.find('.//PWindFieldFileName').text
    
    #Pick the WindField Data the user selected
    sProbabilisticWindSpeedFileName = tree.find('.//WindFieldDataFile').text
    if sProbabilisticWindSpeedFileName == '':
        utility.popupmsg('Please select a valid input for probabilistic wind gusts')
        sys.exit()
    #df_Prob_WindSp = pd.read_csv(sProbabilisticWindSpeedFilePath + sProbabilisticWindSpeedFileName, delimiter = None)
    df_Prob_WindSp = pd.read_csv(sProbabilisticWindSpeedFileName, delimiter = None)
    df_Prob_WindSp.columns = [x.upper() for x in df_Prob_WindSp.columns]
    
    #PROBABILISTIC - Windspeed values for all 7RPs and rounded to 5ths
        
    points_CBSR = pd.merge(points_CBSR.astype(str), df_Prob_WindSp.astype(str),left_on=sTractIDFieldName, 
                           right_on=sTractFldName, how="inner" , suffixes=('_left', '_right'))

    #print(points_CBSR)
    #points_CBSR = points_CBSR.drop([sTractFldName])

    #print(5)
    #Nearest multiple of 5 for each windspeed (upper and lower)- a column for each RP 
        
    points_CBSR['F10YR_L'] = points_CBSR.apply (lambda row: roundtonearest5(row['F10YR']), axis=1)
    points_CBSR['F10YR_U'] = points_CBSR.apply (lambda row: row['F10YR_L'] + 5 if (row['F10YR_L'] > 0) else 0, axis=1)
    
    points_CBSR['F20YR_L'] = points_CBSR.apply (lambda row: roundtonearest5(row['F20YR']), axis=1)   
    points_CBSR['F20YR_U'] = points_CBSR.apply (lambda row: row['F20YR_L'] + 5 if (row['F20YR_L'] > 0) else 0, axis=1)
    
    points_CBSR['F50YR_L'] = points_CBSR.apply (lambda row: roundtonearest5(row['F50YR']), axis=1)
    points_CBSR['F50YR_U'] = points_CBSR.apply (lambda row: row['F50YR_L'] + 5 if (row['F50YR_L'] > 0) else 0, axis=1)
    
    points_CBSR['F100YR_L'] = points_CBSR.apply (lambda row: roundtonearest5(row['F100YR']), axis=1)
    points_CBSR['F100YR_U'] = points_CBSR.apply (lambda row: row['F100YR_L'] + 5 if (row['F100YR_L'] > 0) else 0, axis=1)
    
    points_CBSR['F200YR_L'] = points_CBSR.apply (lambda row: roundtonearest5(row['F200YR']), axis=1)
    points_CBSR['F200YR_U'] = points_CBSR.apply (lambda row: row['F200YR_L'] + 5 if (row['F200YR_L'] > 0) else 0, axis=1)
    
    points_CBSR['F500YR_L'] = points_CBSR.apply (lambda row: roundtonearest5(row['F500YR']), axis=1)
    points_CBSR['F500YR_U'] = points_CBSR.apply (lambda row: row['F500YR_L'] + 5 if (row['F500YR_L'] > 0) else 0, axis=1)
   
    points_CBSR['F1000YR_L'] = points_CBSR.apply (lambda row: roundtonearest5(row['F1000YR']), axis=1)
    points_CBSR['F1000YR_U'] = points_CBSR.apply (lambda row: row['F1000YR_L'] + 5 if (row['F1000YR_L'] > 0) else 0, axis=1)
    
    #print(6)
    
    logging.info(str(datetime.datetime.now())+ ' Loss Calcs Started... ')
    HAST_Probabilistic_LossCalcs(points_CBSR)
    logging.info(str(datetime.datetime.now())+ ' Loss Calcs Complete... ')
    logging.info(str(datetime.datetime.now())+ ' Analysis Complete... ')    
    print("Analysis Complete...")
    
    #sys.exit()
    
def HAST_Probabilistic_LossCalcs(df_WindSpeeds):
    
    tree = ET.parse('settings.xml')
    sLUTPath = tree.find('.//LUTPath').text
    sDamageFunctionFileName = tree.find('.//HUDamageFunctions').text
    sPreProcessedDataFileName = tree.find('.//PreProcessedDataFileName').text
    
    #Logging setup
    LogFileName = tree.find('.//LogFileName').text
    Level = tree.find('.//Level').text
    if Level == 'INFO': 
        logging.basicConfig(filename=LogFileName, filemode='w', level=logging.INFO)
    else: 
        logging.basicConfig(filename=LogFileName, filemode='w', level=logging.DEBUG)    
    
    logging.debug(str(datetime.datetime.now())+ ' Inside HAST_Probabilistic_LossCalcs func ')
    
    df_Dmg_Func = pd.read_csv(sLUTPath + sDamageFunctionFileName, delimiter = None)
    df_Dmg_Func.columns = [x.upper() for x in df_Dmg_Func.columns]
    
    logging.debug(str(datetime.datetime.now())+ ' Inside HAST_Probabilistic_LossCalcs func ')

    RPs = [10,20,50,100,200,500,1000]
        
    for rp in RPs:
        df_RP = df_WindSpeeds
        if rp == 10:           
            df_RP = df_RP.drop(columns=['F20YR','F20YR_U','F20YR_L'])
            df_RP = df_RP.drop(columns=['F50YR','F50YR_U','F50YR_L'])
            df_RP = df_RP.drop(columns=['F100YR','F100YR_U','F100YR_L'])
            df_RP = df_RP.drop(columns=['F200YR','F200YR_U','F200YR_L'])
            df_RP = df_RP.drop(columns=['F500YR','F500YR_U','F500YR_L'])
            df_RP = df_RP.drop(columns=['F1000YR','F1000YR_U','F1000YR_L'])
        elif rp == 20:    
            df_RP = df_RP.drop(columns=['F10YR','F10YR_U','F10YR_L'])
            df_RP = df_RP.drop(columns=['F50YR','F50YR_U','F50YR_L'])
            df_RP = df_RP.drop(columns=['F100YR','F100YR_U','F100YR_L'])
            df_RP = df_RP.drop(columns=['F200YR','F200YR_U','F200YR_L'])
            df_RP = df_RP.drop(columns=['F500YR','F500YR_U','F500YR_L'])
            df_RP = df_RP.drop(columns=['F1000YR','F1000YR_U','F1000YR_L'])
        elif rp == 50:     
            df_RP = df_RP.drop(columns=['F10YR','F10YR_U','F10YR_L'])
            df_RP = df_RP.drop(columns=['F20YR','F20YR_U','F20YR_L'])
            df_RP = df_RP.drop(columns=['F100YR','F100YR_U','F100YR_L'])
            df_RP = df_RP.drop(columns=['F200YR','F200YR_U','F200YR_L'])
            df_RP = df_RP.drop(columns=['F500YR','F500YR_U','F500YR_L'])
            df_RP = df_RP.drop(columns=['F1000YR','F1000YR_U','F1000YR_L'])
        elif rp == 100:     
            df_RP = df_RP.drop(columns=['F10YR','F10YR_U','F10YR_L'])
            df_RP = df_RP.drop(columns=['F20YR','F20YR_U','F20YR_L'])
            df_RP = df_RP.drop(columns=['F50YR','F50YR_U','F50YR_L'])
            df_RP = df_RP.drop(columns=['F200YR','F200YR_U','F200YR_L'])
            df_RP = df_RP.drop(columns=['F500YR','F500YR_U','F500YR_L'])
            df_RP = df_RP.drop(columns=['F1000YR','F1000YR_U','F1000YR_L'])
        elif rp == 200:     
            df_RP = df_RP.drop(columns=['F10YR','F10YR_U','F10YR_L'])
            df_RP = df_RP.drop(columns=['F20YR','F20YR_U','F20YR_L'])
            df_RP = df_RP.drop(columns=['F50YR','F50YR_U','F50YR_L'])            
            df_RP = df_RP.drop(columns=['F100YR','F100YR_U','F100YR_L'])
            df_RP = df_RP.drop(columns=['F500YR','F500YR_U','F500YR_L'])
            df_RP = df_RP.drop(columns=['F1000YR','F1000YR_U','F1000YR_L'])
        elif rp == 500:     
            df_RP = df_RP.drop(columns=['F10YR','F10YR_U','F10YR_L'])
            df_RP = df_RP.drop(columns=['F20YR','F20YR_U','F20YR_L'])
            df_RP = df_RP.drop(columns=['F50YR','F50YR_U','F50YR_L'])            
            df_RP = df_RP.drop(columns=['F100YR','F100YR_U','F100YR_L'])
            df_RP = df_RP.drop(columns=['F200YR','F200YR_U','F200YR_L'])
            df_RP = df_RP.drop(columns=['F1000YR','F1000YR_U','F1000YR_L'])          
        elif rp == 1000:     
            df_RP = df_RP.drop(columns=['F10YR','F10YR_U','F10YR_L'])
            df_RP = df_RP.drop(columns=['F20YR','F20YR_U','F20YR_L'])
            df_RP = df_RP.drop(columns=['F50YR','F50YR_U','F50YR_L'])            
            df_RP = df_RP.drop(columns=['F100YR','F100YR_U','F100YR_L'])
            df_RP = df_RP.drop(columns=['F200YR','F200YR_U','F200YR_L'])
            df_RP = df_RP.drop(columns=['F500YR','F500YR_U','F500YR_L'])
        logging.debug(str(datetime.datetime.now())+ ' Processing for ' + str(rp))  
        HAST_Probabilistic_GenRes(df_RP,rp,df_Dmg_Func)
        
def HAST_Probabilistic_GenRes(df_WindSpeeds,rp,df_Dmg_Func):
    
    gsTERRAINID = 'TERRAINID'
    gsWBID = 'WBID'
    df_fetchedVals = ""    
    rpFieldName = 'F' + str(rp) + 'YR'
    rpFieldNameIpV = 'F' + str(rp) + 'YR_'
    rpFieldNameU = 'F' + str(rp) + 'YR_U'
    rpFieldNameL = 'F' + str(rp) + 'YR_L'
    
    tree = ET.parse('settings.xml')
    sOutputPath = tree.find('.//OutputPath').text
    sPreProcessedDataFileName = tree.find('.//PreProcessedDataFileName').text
    sResultFileNamePrefix = os.path.basename(os.path.splitext(sPreProcessedDataFileName)[0])
    #print(sResultFileNamePrefix)
    
    #Logging setup
    LogFileName = tree.find('.//LogFileName').text
    Level = tree.find('.//Level').text
    if Level == 'INFO': 
        logging.basicConfig(filename=LogFileName, filemode='w', level=logging.INFO)
    else: 
        logging.basicConfig(filename=LogFileName, filemode='w', level=logging.DEBUG)    
    
    logging.debug(str(datetime.datetime.now())+ ' Inside HAST_Probabilistic_GenRes ')  
    
    #Fecth field names of the input selected
    for item in tree.find('.//AnalysisFields'):
        logging.debug(str(datetime.datetime.now())+ ' AnalysisFields: ' + item.tag)
        if item.tag == 'WBID':
            sWbIDFieldName = item.attrib['inputFieldName']
        elif item.tag == 'TerrainID':        
            sTerrainIDFldName = item.attrib['inputFieldName']
        elif item.tag == 'BuildingArea':
            sBldgAreaFldName = item.attrib['inputFieldName']
        elif item.tag == 'BuildingValue':
            sBldgCostFldName = item.attrib['inputFieldName']
        elif item.tag == 'ContentValue':
            sContentCostFldName = item.attrib['inputFieldName']            
    #print(df_WindSpeeds.columns)
    df_WindSpeeds = df_WindSpeeds.loc[:,~df_WindSpeeds.columns.duplicated()]
    if 'UNNAMED: 0' in df_WindSpeeds.columns:
        df_WindSpeeds = df_WindSpeeds.drop(['UNNAMED: 0'], axis=1)
   
    for i, row in df_WindSpeeds.iterrows():
        uWindFieldName = 'WS' +  str(row[rpFieldNameU])
        lWindFieldName = 'WS' + str(row[rpFieldNameL])
        wbId = int(row[sWbIDFieldName])
        TerrainID = int(row[sTerrainIDFldName])
        
        #Was moved out of the DamLossDescID loop to speed up the process
        df_ForWbIDTerrainId = df_Dmg_Func[(df_Dmg_Func[gsWBID]==wbId) & 
                                         (df_Dmg_Func[gsTERRAINID]==TerrainID)]
        
        for damLossId in range(9):
            logging.debug(str(datetime.datetime.now())+ ' Calculating losses for damLossId = ' + str(damLossId))
            damLossId = damLossId + 1           
            df_fetchedVals = df_ForWbIDTerrainId[(df_ForWbIDTerrainId['DAMLOSSDESCID']==damLossId)]

            a = float(row[rpFieldName])        
            a1 = float(row[rpFieldNameL])        
            a2 = float(row[rpFieldNameU])
        
            #Add check for L (a1) and U(a2) = 0 : then z = 0 and no computation will be performed, instead all damLoss cats will
            #be set to 0
            for j, row1 in df_fetchedVals.iterrows():
                b2 = float(row1[uWindFieldName])
                b1 = float(row1[lWindFieldName])

            #z = interpolate_ws(float(a),float(a1),float(a2),float(b1),float(b2))
        
            #Loss cats
            #1=Affected,2=Minor,3=Major,4=Destroyed,5=BuildingLoss,6=ContentLoss,7=LossOfUse,8=Brick & Wood Debris
            #9=Concrete & Steel debris
            
            #print(str(damLossId))
            if damLossId == 1:
                damLossFldNameSuffix = 'Prob_Affected'
            elif damLossId == 2:
                damLossFldNameSuffix = 'Prob_Minor'
            elif damLossId == 3:
                damLossFldNameSuffix = 'Prob_Major'
            elif damLossId == 4:
                damLossFldNameSuffix = 'Prob_Destroyed'
            elif damLossId == 5:
                damLossFldNameSuffix = 'BuildingLoss_USD'                
            elif damLossId == 6:
                damLossFldNameSuffix = 'ContentLoss_USD'            
            elif damLossId == 7:
                damLossFldNameSuffix = 'LossOfUse_Days'
            elif damLossId == 8:
                damLossFldNameSuffix = 'BrickWoodDebris_lbs'
            elif damLossId == 9:
                damLossFldNameSuffix = 'ConSteelDebris_lbs'
                
            if (a >= 50 and a <= 250):
                for j, row1 in df_fetchedVals.iterrows():
                    b2 = float(row1[uWindFieldName])
                    b1 = float(row1[lWindFieldName])
                # logging.debug(str(datetime.datetime.now())+ ' a1 = ' + str(a1))
                # logging.debug(str(datetime.datetime.now())+ ' a2 = ' + str(a2))
                # logging.debug(str(datetime.datetime.now())+ ' b1 = ' + str(b1))
                # logging.debug(str(datetime.datetime.now())+ ' b2 = ' + str(b2))
                z = interpolate_ws(float(a),float(a1),float(a2),float(b1),float(b2))
            else:               
                z = 0                       
                
            rpFieldNameDmg = rpFieldNameIpV + damLossFldNameSuffix           
            logging.debug(str(datetime.datetime.now())+ ' Column name = ' + str(rpFieldNameDmg))
            if damLossId == 1 or damLossId == 2 or damLossId == 3 or damLossId == 4 or damLossId == 7 :
                df_WindSpeeds.at[i,rpFieldNameDmg] = z
            elif damLossId == 5:
                df_WindSpeeds.at[i,rpFieldNameDmg]  = z * float(row[sBldgCostFldName])
            elif damLossId == 6:
                df_WindSpeeds.at[i,rpFieldNameDmg]  = z * float(row[sContentCostFldName])            
            elif damLossId == 8 or damLossId == 9:
                df_WindSpeeds.at[i,rpFieldNameDmg] = z * float(row[sBldgAreaFldName])
                
    logging.debug(str(datetime.datetime.now())+ sOutputPath + sResultFileNamePrefix + "_RP" + str(rp) +  '_Results.csv')
    logging.info(str(datetime.datetime.now())+ sOutputPath + sResultFileNamePrefix + "_RP" + str(rp) +  '_Results.csv')
    print('Saving results to path:' + sOutputPath + sResultFileNamePrefix + "_RP" + str(rp) +  '_Results.csv')
    df_WindSpeeds.to_csv(sOutputPath + sResultFileNamePrefix + "_RP" + str(rp) +  '_Results.csv') 

######################################################################################################################
######################################################################################################################
######################################################################################################################
def HAST_UserSupplied_Analysis():

    tree = ET.parse('settings.xml')
         
    #Fecth field names of the input selected
    for item in tree.find('.//AnalysisFields'):
        logging.debug(str(datetime.datetime.now()) + ' AnalysisFields: ' + item.tag)
        if item.tag == 'PeakGusts':
            sPeakGusts = item.attrib['inputFieldName'] 

    #Logging setup
    LogFileName = tree.find('.//LogFileName').text
    Level = tree.find('.//Level').text
    if Level == 'INFO': 
        logging.basicConfig(filename=LogFileName, filemode='w', level=logging.INFO)
    else: 
        logging.basicConfig(filename=LogFileName, filemode='w', level=logging.DEBUG)            
    
    print("Analyzing HU losses for user-supplied wind gusts in the input dataset...")
    logging.info(str(datetime.datetime.now()) + ' Analyzing HU Losses... ')
    sPreProcessedDataFileName = tree.find('.//PreProcessedDataFileName').text

	#pek gusts check - replace nulls with zero
	#fetch upper and lower limit - nearest 5
    df_Input_wPeakGusts = pd.read_csv(sPreProcessedDataFileName, delimiter = None)
    df_Input_wPeakGusts.columns = [x.upper() for x in df_Input_wPeakGusts.columns]
    df_Input_wPeakGusts['PEAKGUSTS_L'] = df_Input_wPeakGusts.apply (lambda row: roundtonearest5(float(row[sPeakGusts])), axis=1)
    df_Input_wPeakGusts['PEAKGUSTS_U'] = df_Input_wPeakGusts.apply (lambda row: row['PEAKGUSTS_L'] + 5 if (row['PEAKGUSTS_L'] > 0) else 0, axis=1)

    logging.info(str(datetime.datetime.now())+ ' UD Loss Calcs Started... ')
    print("UD Loss Calcs Started... ")
    HAST_UserSupplied_GenRes(df_Input_wPeakGusts)
    logging.info(str(datetime.datetime.now())+ ' UD Loss Calcs Complete... ')
    print("UD Loss Calcs Complete... '")
    

def HAST_UserSupplied_GenRes(df_Input_wPeakGusts):
    
    gsTERRAINID = 'TERRAINID'
    gsWBID = 'WBID'    
    df_fetchedVals = ""    
    rpFieldNameIpV = 'UD_'
    rpFieldName = 'PEAKGUSTS'
    rpFieldNameU = 'PEAKGUSTS_U'
    rpFieldNameL = 'PEAKGUSTS_L'
    
    tree = ET.parse('settings.xml')
    sLUTPath = tree.find('.//LUTPath').text
    sDamageFunctionFileName = tree.find('.//HUDamageFunctions').text
    sOutputPath = tree.find('.//OutputPath').text
    sPreProcessedDataFileName = tree.find('.//PreProcessedDataFileName').text
    sResultFileNamePrefix = os.path.basename(os.path.splitext(sPreProcessedDataFileName)[0])
    
    #Logging setup
    LogFileName = tree.find('.//LogFileName').text
    Level = tree.find('.//Level').text
    if Level == 'INFO': 
        logging.basicConfig(filename=LogFileName, filemode='w', level=logging.INFO)
    else: 
        logging.basicConfig(filename=LogFileName, filemode='w', level=logging.DEBUG)    
    
    logging.debug(str(datetime.datetime.now())+ ' Inside HAST_UserSupplied_GenRes ') 
   
    df_Dmg_Func = pd.read_csv(sLUTPath + sDamageFunctionFileName, delimiter = None)
    df_Dmg_Func.columns = [x.upper() for x in df_Dmg_Func.columns]
    
    logging.debug(str(datetime.datetime.now())+ ' Inside HAST_Probabilistic_LossCalcs func ')	
    
    #Fetch field names of the input selected
    for item in tree.find('.//AnalysisFields'):
        logging.debug(str(datetime.datetime.now())+ ' AnalysisFields: ' + item.tag)
        if item.tag == 'WBID':
            sWbIDFieldName = item.attrib['inputFieldName']
        elif item.tag == 'TerrainID':        
            sTerrainIDFldName = item.attrib['inputFieldName']
        elif item.tag == 'BuildingArea':
            sBldgAreaFldName = item.attrib['inputFieldName']
        elif item.tag == 'BuildingValue':
            sBldgCostFldName = item.attrib['inputFieldName']
        elif item.tag == 'ContentValue':
            sContentCostFldName = item.attrib['inputFieldName']    
			
    #print(df_Input_wPeakGusts.columns)
    df_Input_wPeakGusts = df_Input_wPeakGusts.loc[:,~df_Input_wPeakGusts.columns.duplicated()]
    if 'UNNAMED: 0' in df_Input_wPeakGusts.columns:
        df_Input_wPeakGusts = df_Input_wPeakGusts.drop(['UNNAMED: 0'], axis=1)
   
    for i, row in df_Input_wPeakGusts.iterrows():
        uWindFieldName = 'WS' +  str(row[rpFieldNameU])
        lWindFieldName = 'WS' + str(row[rpFieldNameL])
        wbId = int(row[sWbIDFieldName])
        TerrainID = int(row[sTerrainIDFldName])
        
        #Was moved out of the DamLossDescID loop to speed up the process
        df_ForWbIDTerrainId = df_Dmg_Func[(df_Dmg_Func[gsWBID]==wbId) & 
                                         (df_Dmg_Func[gsTERRAINID]==TerrainID)]
        
        for damLossId in range(9):
            logging.debug(str(datetime.datetime.now())+ ' Calculating losses for damLossId = ' + str(damLossId))
            damLossId = damLossId + 1           
            df_fetchedVals = df_ForWbIDTerrainId[(df_ForWbIDTerrainId['DAMLOSSDESCID']==damLossId)]

            a = float(row[rpFieldName])        
            a1 = float(row[rpFieldNameL])        
            a2 = float(row[rpFieldNameU])

            #Loss cats
            #1=Affected,2=Minor,3=Major,4=Destroyed,5=BuildingLoss,6=ContentLoss,7=LossOfUse,8=Brick & Wood Debris
            #9=Concrete & Steel debris            
            if damLossId == 1:
                damLossFldNameSuffix = 'Prob_Affected'
            elif damLossId == 2:
                damLossFldNameSuffix = 'Prob_Minor'
            elif damLossId == 3:
                damLossFldNameSuffix = 'Prob_Major'
            elif damLossId == 4:
                damLossFldNameSuffix = 'Prob_Destroyed'
            elif damLossId == 5:
                damLossFldNameSuffix = 'BuildingLoss_USD'                
            elif damLossId == 6:
                damLossFldNameSuffix = 'ContentLoss_USD'            
            elif damLossId == 7:
                damLossFldNameSuffix = 'LossOfUse_Days'
            elif damLossId == 8:
                damLossFldNameSuffix = 'BrickWoodDebris_lbs'
            elif damLossId == 9:
                damLossFldNameSuffix = 'ConSteelDebris_lbs'
        
            if (a >= 50 and a <= 250):
                for j, row1 in df_fetchedVals.iterrows():
                    b2 = float(row1[uWindFieldName])
                    b1 = float(row1[lWindFieldName])
                z = interpolate_ws(float(a),float(a1),float(a2),float(b1),float(b2))
            else:               
                z = 0                
                
            rpFieldNameDmg = rpFieldNameIpV + damLossFldNameSuffix           
            logging.debug(str(datetime.datetime.now())+ ' Column name = ' + str(rpFieldNameDmg))
            if damLossId == 1 or damLossId == 2 or damLossId == 3 or damLossId == 4 or damLossId == 7 :
                df_Input_wPeakGusts.at[i,rpFieldNameDmg] = z
            elif damLossId == 5:
                df_Input_wPeakGusts.at[i,rpFieldNameDmg]  = z * float(row[sBldgCostFldName])
            elif damLossId == 6:
                df_Input_wPeakGusts.at[i,rpFieldNameDmg]  = z * float(row[sContentCostFldName])            
            elif damLossId == 8 or damLossId == 9:
                df_Input_wPeakGusts.at[i,rpFieldNameDmg] = z * float(row[sBldgAreaFldName])
                
    logging.debug(str(datetime.datetime.now())+ ' Saving ' + sOutputPath + sResultFileNamePrefix + "_UD_" + 'Results.csv')
    logging.info(str(datetime.datetime.now())+ ' Saving ' + sOutputPath + sResultFileNamePrefix + "_UD_" + 'Results.csv')
    print('Saving results to path:' + sOutputPath + sResultFileNamePrefix + "_UD_" + 'Results.csv...')
    df_Input_wPeakGusts.to_csv(sOutputPath + sResultFileNamePrefix + "_UD_" + 'Results.csv')     
    

def interpolate_ws(a,a1,a2,b1,b2):
    x = float(a)
    x1 = float(a1)
    x2 = float(a2)
    y1 = float(b1)
    y2 = float(b2)
    y = y1 + (((x-x1)/(x2-x1))*(y2-y1))
    return y
    
def roundtonearest5(x, base=5):
    #Add check for 0 and -ve numbers
    y = float(x)
    if y <= 0:
        retVal = 0
    else:
        z = base * round(y/base)
        if y <= z:
            retVal = z - 5
        else:
            retVal = z
            
    return retVal 



    """
    #print(3)
    #sSOPctFileName = tree.find('.//SOPct').text
    #df_SO_Pct = pd.read_csv(sLUTPath + sSOPctFileName, delimiter = None)
    #df_SO_Pct.columns = [x.upper() for x in df_SO_Pct.columns]
    #df_SO_Pct[sOccupancyFieldName] = df_SO_Pct[sOccupancyFieldName].str.replace('\W', '')
    #print(4)
    
    #Calculate the content cost 
    print("Before Content Cost Calcs")
    points_CBSR = pd.merge(points_CBSR,df_SO_Pct[[sOccupancyFieldName,sContentValPctFieldName]],
                           left_on = sSoccIdFieldName,right_on = sOccupancyFieldName, how='left')

    print(7)
    
    #Need to add a ID field in the begining so that duplicates can be removed at this step 
    points_CBSR.drop_duplicates(subset="OBJECTID", keep="last",inplace=True)  

    #print(points_CBSR)
    print("8. After removing dups")
    
    points_CBSR[sContentCostFldName] = points_CBSR.apply (lambda row:(float(row[sCostFieldName]) * (float(row['CONTENTVALPCT'])/100)),axis=1)                                                                   
    print("9. After Calculating")
    
    #points_CBSR.to_csv(sPreProcessedDataFileName)   
    
    #points_CBSR = HAST_Analysis(points_CBSR) 
    #print(points_CBSR)
    """