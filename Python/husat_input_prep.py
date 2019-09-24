import numpy as np
import pandas as pd
import geopandas as gpd
from geopandas import GeoDataFrame
from shapely.geometry import Point, LineString
from scipy import interpolate

def rdcsv():

    #The input files and full path will be read from the GUI
    df_Input = pd.read_csv('C:\_Hazus\June-Dec_2019\HUSAT\Input\HI_hzSchool_UDF_Input.csv', delimiter = None)
    df_CB = gpd.read_file('C:\_Hazus\June-Dec_2019\HUSAT\LUT\HI\hzCensusblock_TIGER.geojson')    
    df_SuRCB = pd.read_csv('C:\_Hazus\June-Dec_2019\HUSAT\LUT\HI\HI_HuCB_SurfaceRoughness.csv' , delimiter = None)
    df_WbId = pd.read_csv('C:\_Hazus\June-Dec_2019\HUSAT\LUT\HU_DefaultWbID.csv', delimiter = None)
    df_Prob_WindSp = pd.read_csv('C:\_Hazus\June-Dec_2019\HUSAT\WindField\Probabilistic\PWS_Tract_8RP.csv', delimiter = None)
    

    #Save the user input file on the Output folder and then use that for adding newly computed fields
    
    #FieldNames
    CBFldName = 'CensusBlock'
    
    #Create the geometry for the Longitude,Latitude in the input data
    #The structure level input need not have the geometry
    geometry = [Point(xy) for xy in zip(df_Input.Longitude, df_Input.Latitude)]        
    crs = {'init': 'epsg:4326'}
    
    #Join between structure level data and Census block to fecth the CBID
    df_Input = GeoDataFrame(df_Input, geometry=geometry, crs=crs)

    #print("After df_Input")
    
    #Join the structure level input points to the hzCensusblock_TIGER to fetch the CBID
    points_CBId = gpd.sjoin(df_Input, df_CB, how="inner", op='intersects')
    #points_CBId.to_csv('C:\_Hazus\June-Dec_2019\HUSAT\Output\AnalysisResults_points_CBId.csv')
       
    #Fetch Surface Roughness from huTerrainB in the respective state
    points_CBSR = pd.merge(points_CBId.astype(str), df_SuRCB.astype(str),on="CensusBlock", how="inner", 
                           suffixes=('_left', '_right'))
    points_CBSR.to_csv('C:\_Hazus\June-Dec_2019\HUSAT\Output\AnalysisResults.csv')    
    
    #Assign the WbID on the basis of the HUSBT in the input
    points_CBSR = pd.merge(points_CBSR.astype(str), df_WbId.astype(str),left_on='HUSBT', right_on='sbtName', how="inner", 
                           suffixes=('_left', '_right'))
        
    #points_CBSR['WBId'] = points_CBSR.apply (lambda row: get_WbId(row), axis=1)
    points_CBSR.to_csv('C:\_Hazus\June-Dec_2019\HUSAT\Output\AnalysisResults.csv')

    #Adding a column TerrainID and Assigning TerrainId on the basis of the Surface Roughness
    points_CBSR['TerrainID'] = points_CBSR.apply (lambda row: get_terrainId(row), axis=1)
    
    points_CBSR.to_csv('C:\_Hazus\June-Dec_2019\HUSAT\Output\AnalysisResults.csv')	
    
    #Add a new TractID_Calc column so that I do not have to fetch the tract for each record every time when 
    points_CBSR['Tract_ID_Gen'] = points_CBSR[CBFldName].str[:11]
    
    #PROBABILISTIC - Pull the windspeed values for all 8RPs and round them to nearest 5 
    points_CBSR = pd.merge(points_CBSR.astype(str), df_Prob_WindSp.astype(str),left_on='Tract_ID_Gen', 
                           right_on='Tract', how="inner", suffixes=('_left', '_right'))
    
    points_CBSR.to_csv('C:\_Hazus\June-Dec_2019\HUSAT\Output\AnalysisResults.csv')
    
    #Find the nearest multiple of 5 for each windspeed (upper and lower)- add a column for each RP 
    points_CBSR['f10yr_L'] = points_CBSR.apply (lambda row: roundtonearest5(row['f10yr']), axis=1)
    points_CBSR['f10yr_U'] = points_CBSR.apply (lambda row: row['f10yr_L'] + 5, axis=1)
    
    points_CBSR.to_csv('C:\_Hazus\June-Dec_2019\HUSAT\Output\AnalysisResults.csv')

    #Join with huDamaFunction.xlsx to find the probability 
    #print(points_CBSR['wbID'].astype(str))
    #x='1'
    #df_probab['WS' + points_CBSR['f10yr_L'].astype(str)] = df_Dmg_Func.apply(lambda row: 
    #                                    df_Dmg_Func['WS' + points_CBSR['f10yr_L'].astype(str)]
    #                                    (str(row['wbID']) == points_CBSR['wbID'].astype(str) 
    #                                     and str(row['TerrainID']) == points_CBSR['TerrainID'].astype(str) 
    #                                     and str(row['DamLossDescID']) == ['1']))
    
    #df_probabilites = pd.merge(points_CBSR.astype(str), df_Dmg_Func[['WS' + row['f10yr_L'] , 'WS' + row['f10yr_U']
    #    ,'DamLossDescID']],left_on='WBID,TerrainID,' + x , 
    #    right_on='WBID,TerrainID,DamLossDescID', how="inner", suffixes=('_left', '_right'))
    
    #point_CBSR['DamLossDescID_1'] = ''
    
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
    
    points_CBSR.to_csv('C:\_Hazus\June-Dec_2019\HUSAT\Output\AnalysisResults.csv')
    
    #Join with huDamaFunction.xlsx to find the probabilities and calculate
    points_CBSR = huprocessRPs_prob(points_CBSR)
    
    print("Complete")
    
def huprocessRPs_prob(df_WindSpeeds):
    RPs = [10,20,50,100,200,500,1000]
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
            
        cal_probabilities(df_RP,rp)
        
def cal_probabilities(df_WindSpeeds,rp):
    df_Dmg_Func = pd.read_csv('C:\_Hazus\June-Dec_2019\HUSAT\LUT\HU_DamageFunctions.csv', delimiter = None)
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
        
        for damLossId in range(8):
            #DamLossDescID = damLossId
            damLossId = damLossId + 1
            #print(damLossId)
            df_fetchedVals = df_Dmg_Func[(df_Dmg_Func['wbID']==wbId) & 
                                         (df_Dmg_Func['TERRAINID']==TerrainID) & 
                                         (df_Dmg_Func['DamLossDescID']==damLossId)]
        
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
            
            if damLossId == 5
                z = 
            df_WindSpeeds.at[i,rpFieldNameDmg] = z

    df_WindSpeeds.to_csv('..\Output\RP' + str(rp)+ 'Results.csv') 
    #print(df_WindSpeeds)
    return df_WindSpeeds



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
    

def main():
    print("Hello HUSAT!")
    rdcsv()

if __name__ == "__main__":
    main()
