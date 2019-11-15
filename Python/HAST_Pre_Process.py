#AUTHOR             : UJVALA K SHARMA
#SCRIPT NAME        : HAST_Pre_Process.py
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
import tkinter as tk
from tkinter import ttk
    
def HAST_dataPrep():

    #The input files and full path will be read from the GUI
    #Fetch file names from XML   
    tree = ET.parse('settings.xml')
    sLUTPath = tree.find('.//LUTPath').text
    sGeoJsonFileName = tree.find('.//CBGeoJson').text
    sInputFileName = tree.find('.//InputFileName').text
    sTerrainIDFileName = tree.find('.//TerrainID').text
    sSurfaceRoughnessFileName = tree.find('.//SurfaceRoughNess').text
    sDfltWbIdFileName = tree.find('.//WbId').text
    sInputPath = tree.find('.//InputPath').text
     
    sPreProcessedDataFileName = os.path.splitext(sInputFileName)[0] + "_pre_processed.csv"
    #popupmsg(sPreProcessedDataFileName)
    
    #FieldNames - Need to be fetched from the XML
    sWbIDFieldName = 'WBID'
    sCBFldName = 'CENSUSBLOCK'
    sHuSBTFldName = 'HUSBT'
    sSBTFldName = 'SBTNAME'
    sTerrainIDFldName = 'TERRAINID'
    sTractIDFieldName = 'TRACT_ID_GEN'
    #sTractFldName = 'TRACT'
    #sContentCostFldName = 'CONTENTCOST'
    
    #Read the input UDF dataset from the XML
    df_Input = pd.read_csv(sInputFileName, delimiter = None)    
    df_Input.columns = [x.upper() for x in df_Input.columns]
    #df_Input = df_Input.columns.str.strip()
    #Need to remove special charaters as the join is unsuccessful
    
    #How will I find the SOCCID fieldName (loop through the names in the xml)??
    #df_Input['SOCCID'] = df_Input['SOCCID'].map(lambda x: re.sub(r'\W+', '', x))
    
    """Need to replace the SOCCID with the field name from the settings.xml
    df_Input['SOCCID'] = df_Input['SOCCID'].str.replace('\W','')
    #print ('SOCCID')
    """
    
    #Check if TerrainID is a part of the input data (df_Input). If not then perform the following joins
    #If the user has provided the TerraID check if wbID is provided. 
    print(df_Input.columns)
    print("Checking field TerrainId")
    if sTerrainIDFldName in df_Input.columns:
        print("Yes" , sLUTPath)
        
        #sSRFN = os.path.join(sLUTPath,sSurfaceRoughnessFileName)
        #print(sSRFN)
        #Check the data if the entries are valid
        df_TerrainID = pd.read_csv(sLUTPath + sTerrainIDFileName, delimiter = None)
        
        print(2)
        df_TerrainID.columns = [x.upper() for x in df_TerrainID.columns]
        
        print(3)
        
        df_ValidateTr = pd.merge(df_Input.astype(str), df_TerrainID.astype(str),on = sTerrainIDFldName, how = "inner", suffixes=('_left', '_right'))
        
        print(4)
        numOfRowsInput = len(df_Input.index)
        numOfRowsmatched = len(df_ValidateTr.index)
        
        print(str(numOfRowsmatched))
        
        if numOfRowsmatched != numOfRowsInput:
            popupmsg("Please check TerrainIDs so that they match with the " + sSurfaceRoughnessFileName + " looktup table.")
            sys.exit()
        elif sWbIDFieldName in df_Input.columns:
            print("Checking field WbId")
            print("Yes")
        
            #Check the data if the entries are valid
            df_WbID = pd.read_csv(sLUTPath + sDfltWbIdFileName, delimiter = None) 
        
            print(5)
            df_WbID.columns = [x.upper() for x in df_WbID.columns]
        
            print(6)
        
            df_ValidateWb = pd.merge(df_Input.astype(str), df_WbID.astype(str),on = sWbIDFieldName, how = "inner", suffixes=('_left', '_right'))
        
            print(7)
            numOfRowsInput = len(df_Input.index)
            numOfRowsmatched = len(df_ValidateWb.index)
        
            print(str(numOfRowsmatched))
        
            if numOfRowsmatched != numOfRowsInput:
                popupmsg("Please check WbIds so that they match with the " + sDfltWbIdFileName[1:1 + len(sDfltWbIdFileName)]  + " looktup table.")
                sys.exit()
        popupmsg("TerrainIds and WbIds match. Please proceed to perform the analyses.")
        sys.exit()
    else:
        print("No")
    
        #Read the GeoJSON for the state that the user is tryin to analyze the data for
        #s = time.time()
        df_CB = gpd.read_file(sLUTPath + sGeoJsonFileName)
        #df_CB.to_json()
        df_CB.columns = [x.lower() for x in df_CB.columns] #setting to lower for the spatial join
        #print ('entire read write op on the json file just created - geopandas',time.time() - s)
        
        print(8)
        #Read the surface roughness LUT
        #df_SuRCB = pd.read_csv('C:\_Hazus\June-Dec_2019\HUSAT\LUT\HI\HI_HuCB_SurfaceRoughness.csv' , delimiter = None)
        df_SuRCB = pd.read_csv(sLUTPath+sSurfaceRoughnessFileName , delimiter = None)
        df_SuRCB.columns = [x.upper() for x in df_SuRCB.columns]
        
        print(9)
        #Read the WbId LUT
        #df_WbId = pd.read_csv('C:\_Hazus\June-Dec_2019\HUSAT\LUT\HU_DefaultWbID.csv', delimiter = None)
        df_WbId = pd.read_csv(sLUTPath + sDfltWbIdFileName, delimiter = None)
        df_WbId.columns = [x.upper() for x in df_WbId.columns]

        print(10)      
        #Latitude and Longitude validation for the future
        #df_CheckLatLong = df_Input.apply(lambda row: (df_input['Longitude'].astype(str)=='' | df_input['Latitude'].astype(str)=='') , axis=1)

        geometry = [Point(xy) for xy in zip(df_Input.LONGITUDE, df_Input.LATITUDE)]        
        crs = {'init': 'epsg:4326'}

        print(11)
        #Join between structure level data and Census block to fecth the CBID
        #Check if any geometries are NULL
        df_Input = GeoDataFrame(df_Input, geometry=geometry, crs=crs)
        #df_Input.columns = [x.upper() for x in df_Input.columns]
        
        print(12)
        #Join the structure level input points to the hzCensusblock_TIGER to fetch the CBID
        points_CBId = gpd.sjoin(df_Input, df_CB, how="inner", op='intersects')
        points_CBId.columns = [x.upper() for x in points_CBId.columns]
        
        print(13)
        #Fetch Surface Roughness from huTerrainB in the respective state
        points_CBSR = pd.merge(points_CBId.astype(str), df_SuRCB.astype(str),on = sCBFldName, how = "inner", suffixes=('_left', '_right'))  
        points_CBSR.columns = [x.upper() for x in points_CBSR.columns]
        
        print(14)
        #Assign the WbID on the basis of the HUSBT in the input
        points_CBSR = pd.merge(points_CBSR.astype(str), df_WbId.astype(str),left_on=sHuSBTFldName, right_on=sSBTFldName,how="inner",suffixes=('_left', '_right'))
                       
        print(15)
        #Add the column for WbId
        #points_CBSR[sDfltWbIdFileName] = points_CBSR.apply (lambda row: get_WbId(row), axis=1)

        print(16)
        #Adding a column TerrainID and Assigning TerrainId on the basis of the Surface Roughness
        points_CBSR[sTerrainIDFldName] = points_CBSR.apply (lambda row: get_terrainId(row), axis=1)

        print(17)

        #Add a new column for tractID that is computed from the CBFldName column so that we do not 
        #have to fetch the tract for each record every time when 
        points_CBSR[sTractIDFieldName] = points_CBSR[sCBFldName].str[:11]
        
        points_CBSR.to_csv(sPreProcessedDataFileName) 
    
        print("Pre-Processing Complete.")        
        
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
        
def popupmsg(msg):
    NORM_FONT= ("Tahoma", 10)
    popup = tk.Tk()
    popup.wm_title("!")
    label = ttk.Label(popup, text=msg, font=NORM_FONT)
    label.pack(side="top", fill="x", pady=10)
    B1 = ttk.Button(popup, text="Okay", command = popup.destroy)
    B1.pack()
    popup.mainloop()
    
 #df_Prob_WindSp = pd.read_csv('C:\_Hazus\June-Dec_2019\HUSAT\WindField\Probabilistic\PWS_Tract_8RP.csv', delimiter = None)

    #df_SO_Pct = pd.read_csv('C:\_Hazus\June-Dec_2019\HUSAT\LUT\SO_PctDist.csv', delimiter = None)
    #df_SO_Pct['Occupancy'] = df_SO_Pct['Occupancy'].str.replace('\W', '')
    #PROBABILISTIC - Pull the windspeed values for all 8RPs and round them to nearest 5
    """    
    points_CBSR = pd.merge(points_CBSR.astype(str), df_Prob_WindSp.astype(str),left_on=sTractIDFieldName, 
                           right_on=sTractFldName, how="inner", suffixes=('_left', '_right'))
    """
    
    #points_CBSR.to_csv('C:\_Hazus\June-Dec_2019\HUSAT\Output\AnalysisResults.csv')    
    
    #Find the nearest multiple of 5 for each windspeed (upper and lower)- add a column for each RP 
    
    """
    points_CBSR['f10yr_L'] = points_CBSR.apply (lambda row: roundtonearest5(row['f10yr']), axis=1)
    points_CBSR['f10yr_U'] = points_CBSR.apply (lambda row: row['f10yr_L'] + 5, axis=1)
    
    points_CBSR['f20yr_L'] = points_CBSR.apply (lambda row: roundtonearest5(row['f20yr']), axis=1)
    points_CBSR['f20yr_U'] = points_CBSR.apply (lambda row: row['f20yr_L'] + 5, axis=1)
    
    points_CBSR['f50yr_L'] = points_CBSR.apply (lambda row: roundtonearest5(row['f50yr']), axis=1)
    points_CBSR['f50yr_U'] = points_CBSR.apply (lambda row: row['f50yr_L'] + 5, axis=1)
    
    points_CBSR['f100yr_L'] = points_CBSR.apply (lambda row: roundtonearest5(row['f100yr']), axis=1)
    points_CBSR['f100yr_U'] = points_CBSR.apply (lambda row: row['f100yr_L'] + 5, axis=1)
    
    points_CBSR['f200yr_L'] = points_CBSR.apply (lambda row: roundtonearest5(row['f200yr']), axis=1)
    points_CBSR['f200yr_U'] = points_CBSR.apply (lambda row: row['f200yr_L'] + 5, axis=1)
    
    points_CBSR['f500yr_L'] = points_CBSR.apply (lambda row: roundtonearest5(row['f500yr']), axis=1)
    points_CBSR['f500yr_U'] = points_CBSR.apply (lambda row: row['f500yr_L'] + 5, axis=1)
   
    points_CBSR['f1000yr_L'] = points_CBSR.apply (lambda row: roundtonearest5(row['f1000yr']), axis=1)
    points_CBSR['f1000yr_U'] = points_CBSR.apply (lambda row: row['f1000yr_L'] + 5, axis=1)
    """
    
    #points_CBSR.to_csv('C:\_Hazus\June-Dec_2019\HUSAT\Output\AnalysisResults.csv')
    #print(points_CBSR)
    
    #Calculate the content cost 
    
    """
    print("Before Content Cost Calcs")
    points_CBSR = pd.merge(points_CBSR,df_SO_Pct[['Occupancy','ContentValPct']],
                           left_on ='SOccId',right_on = "Occupancy", how='left')
    """
    #print("After the merge")
    #points_CBSR.to_csv('C:\_Hazus\June-Dec_2019\HUSAT\Output\AnalysisResults.csv')
    #print(points_CBSR)
    
    #points_CBSR.drop_duplicates(subset="OBJECTID", keep="last",inplace=True)
    
    #print("After removing dups")
    
    """
    points_CBSR[sContentCostFldName] = points_CBSR.apply (lambda row:
                                                          (float(row['Cost']) * (float(row['ContentValPct'])/100)), 
                                                          axis=1)
    """                                                                
    #print("After Calculating")
    #points_CBSR.to_csv('C:\_Hazus\June-Dec_2019\HUSAT\Output\AnalysisResults.csv')   
    
    #HUSAT Loss Analysis - Need to move to a different python or can be called from this file using 
    #FileName.FuntionName style
    
    """
    points_CBSR = HUSAT_LossAnalysis(points_CBSR) 
    """
    #print("Complete")
"""
def calculateContentCost(pct,bldgCost):
    a = float(bldgCost)
    b = float(pct)
    c = (a * (b/100))
    print(str(c))
    return c

def HUSAT_LossAnalysis(df_WindSpeeds):
    #Move the file and field names to the XML
    df_Dmg_Func = pd.read_csv('C:\_Hazus\June-Dec_2019\HUSAT\LUT\HU_DamageFunctions.csv', delimiter = None)
    
    #Return periods should be in the XML
    RPs = [10,20,50,100,200,500,1000]
    
    #All field names will be in the XML
    for rp in RPs:
        df_RP = df_WindSpeeds
        if rp == 10:           
            df_RP = df_RP.drop(columns=['f20yr','f20yr_U','f20yr_L'])
            df_RP = df_RP.drop(columns=['f50yr','f50yr_U','f50yr_L'])
            df_RP = df_RP.drop(columns=['f100yr','f100yr_U','f100yr_L'])
            df_RP = df_RP.drop(columns=['f200yr','f200yr_U','f200yr_L'])
            df_RP = df_RP.drop(columns=['f500yr','f500yr_U','f500yr_L'])
            df_RP = df_RP.drop(columns=['f1000yr','f1000yr_U','f1000yr_L'])
        elif rp == 20:    
            df_RP = df_RP.drop(columns=['f10yr','f10yr_U','f10yr_L'])
            df_RP = df_RP.drop(columns=['f50yr','f50yr_U','f50yr_L'])
            df_RP = df_RP.drop(columns=['f100yr','f100yr_U','f100yr_L'])
            df_RP = df_RP.drop(columns=['f200yr','f200yr_U','f200yr_L'])
            df_RP = df_RP.drop(columns=['f500yr','f500yr_U','f500yr_L'])
            df_RP = df_RP.drop(columns=['f1000yr','f1000yr_U','f1000yr_L'])
        elif rp == 50:     
            df_RP = df_RP.drop(columns=['f10yr','f10yr_U','f10yr_L'])
            df_RP = df_RP.drop(columns=['f20yr','f20yr_U','f20yr_L'])
            df_RP = df_RP.drop(columns=['f100yr','f100yr_U','f100yr_L'])
            df_RP = df_RP.drop(columns=['f200yr','f200yr_U','f200yr_L'])
            df_RP = df_RP.drop(columns=['f500yr','f500yr_U','f500yr_L'])
            df_RP = df_RP.drop(columns=['f1000yr','f1000yr_U','f1000yr_L'])
        elif rp == 100:     
            df_RP = df_RP.drop(columns=['f10yr','f10yr_U','f10yr_L'])
            df_RP = df_RP.drop(columns=['f20yr','f20yr_U','f20yr_L'])
            df_RP = df_RP.drop(columns=['f50yr','f50yr_U','f50yr_L'])
            df_RP = df_RP.drop(columns=['f200yr','f200yr_U','f200yr_L'])
            df_RP = df_RP.drop(columns=['f500yr','f500yr_U','f500yr_L'])
            df_RP = df_RP.drop(columns=['f1000yr','f1000yr_U','f1000yr_L'])
        elif rp == 200:     
            df_RP = df_RP.drop(columns=['f10yr','f10yr_U','f10yr_L'])
            df_RP = df_RP.drop(columns=['f20yr','f20yr_U','f20yr_L'])
            df_RP = df_RP.drop(columns=['f50yr','f50yr_U','f50yr_L'])            
            df_RP = df_RP.drop(columns=['f100yr','f100yr_U','f100yr_L'])
            df_RP = df_RP.drop(columns=['f500yr','f500yr_U','f500yr_L'])
            df_RP = df_RP.drop(columns=['f1000yr','f1000yr_U','f1000yr_L'])
        elif rp == 500:     
            df_RP = df_RP.drop(columns=['f10yr','f10yr_U','f10yr_L'])
            df_RP = df_RP.drop(columns=['f20yr','f20yr_U','f20yr_L'])
            df_RP = df_RP.drop(columns=['f50yr','f50yr_U','f50yr_L'])            
            df_RP = df_RP.drop(columns=['f100yr','f100yr_U','f100yr_L'])
            df_RP = df_RP.drop(columns=['f200yr','f200yr_U','f200yr_L'])
            df_RP = df_RP.drop(columns=['f1000yr','f1000yr_U','f1000yr_L'])          
        elif rp == 1000:     
            df_RP = df_RP.drop(columns=['f10yr','f10yr_U','f10yr_L'])
            df_RP = df_RP.drop(columns=['f20yr','f20yr_U','f20yr_L'])
            df_RP = df_RP.drop(columns=['f50yr','f50yr_U','f50yr_L'])            
            df_RP = df_RP.drop(columns=['f100yr','f100yr_U','f100yr_L'])
            df_RP = df_RP.drop(columns=['f200yr','f200yr_U','f200yr_L'])
            df_RP = df_RP.drop(columns=['f500yr','f500yr_U','f500yr_L'])
            
        calc_probabilities(df_RP,rp,df_Dmg_Func)
        
def calc_probabilities(df_WindSpeeds,rp,df_Dmg_Func):
    
    df_fetchedVals = ""
    
    rpFieldName = 'f' + str(rp) + 'yr'
    rpFieldNameIpV = 'f' + str(rp) + 'yr_IpV'
    rpFieldNameU = 'f' + str(rp) + 'yr_U'
    rpFieldNameL = 'f' + str(rp) + 'yr_L'
    
    df_WindSpeeds[rpFieldNameIpV] = ""
    
    for i, row in df_WindSpeeds.iterrows():
        uWindFieldName = 'WS' +  str(row[rpFieldNameU])
        lWindFieldName = 'WS' + str(row[rpFieldNameL])
        wbId = int(row['wbID'])
        TerrainID = int(row['TerrainID'])
        
        #Was moved out of the 0-8 DamLossDescID loop so that the fecth from the 
        #Damage functions table is minimized to speed up the process
        df_ForWbIDTerrainId = df_Dmg_Func[(df_Dmg_Func['wbID']==wbId) & 
                                         (df_Dmg_Func['TERRAINID']==TerrainID)]
        
        for damLossId in range(8):
            #DamLossDescID = damLossId
            damLossId = damLossId + 1
            #print(damLossId)
            
            #df_fetchedVals = df_Dmg_Func[(df_Dmg_Func['wbID']==wbId) & 
             #                            (df_Dmg_Func['TERRAINID']==TerrainID) & 
              #                           (df_Dmg_Func['DamLossDescID']==damLossId)]
            
            df_fetchedVals = df_ForWbIDTerrainId[(df_ForWbIDTerrainId['DamLossDescID']==damLossId)]
        
            #print(df_fetchedVals)
            a = float(row[rpFieldName])        
            a1 = float(row[rpFieldNameL])        
            a2 = float(row[rpFieldNameU])
        
            for j, row1 in df_fetchedVals.iterrows():
                b2 = float(row1[uWindFieldName])
                b1 = float(row1[lWindFieldName])

            z = interpolate_ws(float(a),float(a1),float(a2),float(b1),float(b2))
            #df_WindSpeeds.at[i,rpFieldNameIpV] = z
        
            #Calculate all damages
            #1=Affected,2=Minor,3=Major,4=Destroyed,5=BuildingLoss,6=ContentLoss,7=LossOfUse,8=Brick & Wood Debris
            #9=Concrete & Steel debris
            rpFieldNameDmg = rpFieldNameIpV + '_dmg' + str(damLossId)
            
            if damLossId == 1 or damLossId == 2 or damLossId == 3 or damLossId == 4 or damLossId == 7 :
                df_WindSpeeds.at[i,rpFieldNameDmg] = z
            elif damLossId == 5:
                df_WindSpeeds.at[i,rpFieldNameDmg]  = z * float(row['Cost'])
            elif damLossId == 6:
                df_WindSpeeds.at[i,rpFieldNameDmg]  = z * float(row['ContentCost'])            
            elif damLossId == 8 or damLossId == 9:
                df_WindSpeeds.at[i,rpFieldNameDmg] = z * float(row['Area'])

    df_WindSpeeds.to_csv('..\Output\RP' + str(rp)+ 'Results.csv') 
    #print(df_WindSpeeds)
    return df_WindSpeeds

#This funn
def interpolate_ws(a,a1,a2,b1,b2):
    x = float(a)
    x1 = float(a1)
    x2 = float(a2)
    y1 = float(b1)
    y2 = float(b2)
    y = y1 + (((x-x1)/(x2-x1))*(y2-y1))
    return y
    
def roundtonearest5(x, base=5):
    y = float(x)
    return base * round(y/base)    
    

  
def main():
    print("Hello HUSAT!")
    HAST_dataPrep()

if __name__ == "__main__":
    main()
"""