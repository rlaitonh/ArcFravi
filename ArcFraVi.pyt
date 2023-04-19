# - * - coding: utf-8 - * -

import arcpy
import os

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = 'Evaluación de la fragilidad visual del paisaje'
        #self.alias = "ArcFraVi"

        # List of tool classes associated with this toolbox
        self.tools = [ArcFraVi]


class ArcFraVi(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "ArcFravi"
        self.description = ""
        self.canRunInBackground = True

    def getParameterInfo(self):

        metodo = arcpy.Parameter(
            displayName = "Método de análisis",
            name = "metodo_analisis",
            datatype="String",
            parameterType="Required",
            direction="Input",
            )
        metodo.filter.type = "ValueList"
        metodo.filter.list = ["Método Yeomans", "Método híbrido Yeomans & Escribano Et al."]

        gdb = arcpy.Parameter(
            displayName = "Entrada: Base de datos Modelo ANLA",
            name ="gdb_anla",
            datatype ="DEWorkspace",
            parameterType = "Required",
            direction = "Input"
            )
        gdb.filter.list = ["Local Database"]

        dem = arcpy.Parameter(
            displayName = "Entrada: Modelo Digital de Elevación (MDE)",
            name = "dem",
            datatype =  ["DERasterDataset" ,"GPRasterLayer"], 
            parameterType = "Required",
            direction ="Input"
            )  

        vias = arcpy.Parameter(
            displayName = "Entrada: Vías de acceso",
            name = "vias",
            datatype = ['DEFeatureClass', 'GPFeatureLayer'],
            parameterType = "Required",
            direction = "Input"
        ) 
        

        distancia = arcpy.Parameter(
            displayName= "Análisis de visibilidad: distancia entre observadores ",
            name ="distancia_observ",
            datatype = ["GPLinearUnit"],
            parameterType = "Optional",
            category = "Parámetros avanzados {}".format(metodo.filter.list[1].encode('utf-8')),
            direction ="Input" 
        ) 

        output = arcpy.Parameter(
            displayName="Ubicación de salida",
            name="output_workspace",
            datatype= "DEWorkspace",
            parameterType= "Required",
            direction="Input"
        )

        params = [metodo, dem, vias, gdb, distancia, output ]
        return params

    def metYeomans (self):   
        """ 
            Realiza la valoración del paisaje conforme con el metodo Yeomans (1986)
        """
        #Definicion de variables                
        inGDB = self.inGDB        
        cav = "in_memory\\cav"
        fvpMetYeomans = "in_memory\\fvpMetYeomans"
        


        # Paso 1: Ejecucion criterio Relieve (S)
        # Declaracion de variables
        raster_pendiente = "in_memory\\raster_pendiente" 
        categPendiente = "in_memory\\categPendiente"              
        inPendiente = inGDB + "\\T_12_GEOMORFOLOGIA\\Pendiente"

        # Ejecucion criterio Relieve (S)
        arcpy.FeatureToRaster_conversion(inPendiente,"PENDIENTE", raster_pendiente, "12.5")
        arcpy.gp.Reclassify_sa(raster_pendiente, "VALUE", "6010 3;6010 6020 3;6020 6030 3;6030 6040 3;6040 6050 2;6050 6060 2;6060 6070 1;6070 6080 1;6080 6090 1", categPendiente, "DATA")

        #Limpiar memoria   
        arcpy.management.Delete(raster_pendiente)
        
        
        # Paso 2: Ejecucion Potencial de Regeneracion Vegetal (R)
                # Declaracion de variables
        ClaseSuelo = "in_memory\\ClaseSuelo" 
        categCapacidadRege = "in_memory\\categCapacidadRege"
        inSuelos = inGDB + "\\T_14_SUELOS\\Suelo"
        output = self.output
        
        # Ejecucion P
        arcpy.FeatureToRaster_conversion(inSuelos, "CLASE", ClaseSuelo, "12.5")
        arcpy.gp.Reclassify_sa(ClaseSuelo, "VALUE", "10401 3;10402 3;10403 3;10404 2;10405 1;10406 1;10407 1;10408 1", categCapacidadRege, "DATA")


        #Limpiar memoria   
        arcpy.management.Delete(ClaseSuelo)

        # Paso 3: Ejecucion Estabilidad del suelo (E)
        GradoAmenMovMasa = "in_memory\\GradoAmenMovMasa" 
        categEstabilidad = "in_memory\\categEstabilidad" 
        inMovMasa = "in_memory\\inMovMasa" 
        AmenazaOtras = inGDB + "\\T_26_GESTION_RIESGO\\AmenazaOtras"
        #Ejecucion
        # Process: select amenaza por movimiento en masa
        arcpy.Select_analysis(AmenazaOtras, inMovMasa, "TIPO_EVEN = 4") 

        # Process: Feature to Raster
        arcpy.FeatureToRaster_conversion(inMovMasa, "GRAD_AME", GradoAmenMovMasa, "12.5")

        # Process: Reclassify
        arcpy.gp.Reclassify_sa(GradoAmenMovMasa, "VALUE", "1 3;2 3;3 3;4 2;5 1;6 1", categEstabilidad, "DATA")        

        #Limpiar memoria   
        arcpy.management.Delete(GradoAmenMovMasa)

        # Paso 4: Ejecucion Contraste Suelo Vegetación (V), Diversidad Estructural de la Vegetacion (D)
        coberturasNivDos = "in_memory\\coberturasNivDos" 
        categContrastSV = "in_memory\\categContrastSV"
        categDiverEstCobert = "in_memory\\categDiverEstCobert" 
        categContrastSR = "in_memory\\categContrastSR"
        inCoberturaTierra = inGDB + "\\T_20_BIOTICO_CONTI_COSTE\\CoberturaTierra"

        #Ejecucion Criterio Contraste Suelo Vegetación (V)
        # Process: Feature to Raster
        arcpy.FeatureToRaster_conversion(inCoberturaTierra, "N2_COBERT", coberturasNivDos, "12.5")

        # Process: Reclassify
        arcpy.gp.Reclassify_sa(coberturasNivDos, "VALUE", "11 3;12 1;13 1;14 1;21 1;22 3;23 1;24 2;31 3;32 3;33 1;41 2;42 2;51 1;52 1", categContrastSV, "DATA")        

        #Ejecucion Criterio Diversidad Estructural de la Vegetacion (D)
        # Process: Reclassify
        arcpy.gp.Reclassify_sa(coberturasNivDos, "VALUE", "11 1;12 1;13 1;14 1;21 2;22 2;23 1;24 2;31 3;32 2;33 1;41 2;42 1;51 1;52 1", categDiverEstCobert, "DATA")        

        #Ejecucion Criterio Contraste Suelo Roca 
        arcpy.gp.Reclassify_sa(coberturasNivDos, "VALUE", "11 2;12 2;13 2;14 3;21 3;22 3;23 3;24 3;31 3;32 3;33 1;41 2;42 1;51 1;52 1", categContrastSR, "DATA")

        #Limpiar memoria   
        arcpy.management.Delete(coberturasNivDos)

        # Paso 5: suma ponderada y catecorización de la Fragilidad visual del paisaje 
        arcpy.gp.RasterCalculator_sa("\"categPendiente\"*(\"categCapacidadRege\"+\"categEstabilidad\"+\"categDiverEstCobert\"+\"categContrastSV\"+\"categContrastSR\")", cav)
        if cav:
            arcpy.gp.RasterCalculator_sa(
                "Con(\"{s}\"  <= 18.33 ,3,Con((\"{s}\"  >  18.33) & (\"{s}\"  <= 31.67) ,2, Con(\"{s}\"> 31.67,1)))".format(s=cav), fvpMetYeomans)
        
        return fvpMetYeomans 
      
    def metHibrido (self): 
        """
            Realiza la valoración del paisaje conforme con el metodo híbrido Yeomans&Escribano et al.
        """
        # Definicion de variables
        calcMetHib = "in_memory\\calcMetHib"
        fvpMetHibrido = "in_memory\\fvpMetHibrido"
        inDem = self.inDem
        inVias = self.inVias
        inDistancia = self.inDistancia
         
        
        # Paso 1: Ejecutar criterios biofísicos
        try:
            arcpy.AddMessage("Calculando criterios biofisicos...")  
            fraViBiofi = self.metYeomans()
            
        except Exception:
            arcpy.AddError(
                "No fue posible ejecutar la evaluacion, verifique el insumo GDB modelo ANLA.")
  
        # Paso 2: ejecucion visibilidad (vi)
        try:
            arcpy.AddMessage("Calculando criterio de visibilidad ...") 
            PObservacion = "in_memory\\PObservacion" 
            FocalSt_LowF = "in_memory\\FocalSt_LowF"
            frecObserv = "in_memory\\frecObserv"
            viewshed = "in_memory\\visibilidad"  
            categVisibilidad = "in_memory\\categVisibilidad"

            # Proceso
            # generacion observadores a lo largo de vias
            arcpy.GeneratePointsAlongLines_management(inVias, PObservacion, "DISTANCE", inDistancia, "", "")

            # Suavisado filtro de paso bajo dem
            arcpy.gp.FocalStatistics_sa(inDem, FocalSt_LowF, "Rectangle 4 4 CELL", "MEAN", "DATA", "90")

            # Analisis de visibilidad
            arcpy.gp.Viewshed2_sa(FocalSt_LowF, PObservacion, frecObserv,"", "FREQUENCY", "0 Meters", "", "0.13", "0 Meters", "", "1 Meters", "", "GROUND", "", "GROUND", "0", "360", "90", "-90", "PERIMETER_SIGHTLINES")
            
            # inlcusion de celdas no visibles por ningún observador
            arcpy.gp.RasterCalculator_sa(
                "Con(IsNull(\"{s}\"),0,\"{s}\")".format(s=frecObserv), viewshed)

            # Categorizacion de la visibilidad
            arcpy.Slice_3d(viewshed, categVisibilidad, "3", "NATURAL_BREAKS", "1")

            #Limpiar memoria   
            arcpy.management.Delete( FocalSt_LowF)
            arcpy.management.Delete( frecObserv)        
            arcpy.management.Delete(viewshed)
            arcpy.management.Delete(PObservacion)        
        except Exception:
            arcpy.AddError(
                "No fue posible ejecutar la evaluacion, verifique los insumos MDE y vias.")
              
        # Paso 3: ejecucion distancia visual (DV)
        try:
            arcpy.AddMessage("Calculando criterio de distancia visual...") 
            distVisu = "in_memory\\distVisu" 
            CategDistVisu = "in_memory\\CategDistVisu"

            # Calculo de distancia viusal desde las vias
            arcpy.gp.EucDistance_sa(inVias, distVisu, "", "12.5", "", "PLANAR", "", "")      

            # Categorizacion de la distancia visual
            arcpy.gp.RasterCalculator_sa(
                "Con(\"distVisu\" < 300,3,Con((\"{s}\"   >=   300)&(\"{s}\" < 1000),2,Con(\"{s}\"  >= 1000,1)))".format(s=distVisu), CategDistVisu)
            arcpy.management.Delete(distVisu)
        except Exception:
            arcpy.AddError(
                "No fue posible ejecutar la evaluacion, verifique el insumo vias.")


        # Paso 4 calculo y categorización de la fragilidad visual del paisaje
        arcpy.gp.RasterCalculator_sa(
            "(\"{}\"+\"{}\"+\"{}\")".format(fraViBiofi,CategDistVisu,categVisibilidad), calcMetHib)
        
        arcpy.gp.RasterCalculator_sa(
            "Con(\"{s}\"  <= 5 ,1,Con((\"{s}\"  >  5) & (\"{s}\"  <= 7) ,2, Con(\"{s}\"> 7,3)))".format(s =calcMetHib),fvpMetHibrido)                 
        
        # Paso 5 Limpieza de memoria
        arcpy.management.Delete(calcMetHib)

        return fvpMetHibrido
  
    def isLicensed(self):
        #Set whether tool is licensed to execute.
        """
        arcpy.AddMessage("Comprobacion del estado de la extension Spatial Analyst...")
        try:
            if arcpy.CheckExtension("Spatial") != "Available":
                raise Exception
            else:
                arcpy.AddMessage("La extension Spatial Analyst esta disponible.")
                if arcpy.CheckOutExtension("Spatial") == "CheckedOut":
                    arcpy.AddMessage("La extension Spatial Analyst esta lista para su uso.")
                elif arcpy.CheckOutExtension("Spatial") == "NotInitialized":
                    arcpy.CheckOutExtension("Spatial")
                    arcpy.AddMessage("La extension Spatial Analyst ha sido retirada.")
                else:
                    arcpy.AddMessage("La extension Spatial Analyst no esta disponible para su uso..")
        except Exception:
            arcpy.AddMessage(
                "La extension Spatial Analyst no esta disponible para su uso. Compruebe sus licencias para asegurarse de que tiene"
                "acceso a esta extension.")
            return False
        """
        return True  # The tool can be run


    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""  

        # deficicion de variables                
        inMetodo = parameters[0]
        inDem = parameters[1]
        inVias = parameters[2]
        inGDB = parameters[3]
        inDistancia = parameters[4]
        output = parameters[5]
        
        # Valor por defecto para el parámetro distancia entre puntos de observación
        if not inDistancia.altered:
            inDistancia.value = "175 Meters"
        

        # valor por defecto del parámetro método
        if not inMetodo.altered:
            inMetodo.value = inMetodo.filter.list[1]

        # Valor por defecto del parametro ubicación de salida
        if inGDB.value:
            workspace = os.path.dirname(inGDB.value.value)
            if not output.altered:
                output.value = workspace  

        # activa o desactiva los campos dem y vias en función del valor en el campo metodo
        if not inMetodo.hasBeenValidated: 
            if inMetodo.value == inMetodo.filter.list[1]:
                inDem.enabled = True 
                inVias.enabled = True 
                inVias.value = ""
                inDem.value = ""
            else:
                inVias.enabled = False
                inVias.value = r".\\"
                inDem.enabled = False
                inDem.value = r".\\"
        

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        arcpy.env.addOutputsToMap = False
        # deficicion de variables        
        inVias = parameters[2].valueAsText
        inGDB = parameters[3].valueAsText
        inDem = parameters[1].valueAsText   

        #Verificacion de vias, el input debe ser de tipo polilinea 
        try:
            if inVias:
                desc = arcpy.Describe(inVias)
                if desc.datasettype in ['FeatureClass', 'FeatureLayer']:
                    if desc.shapetype != 'Polyline':
                        parameters[2].setErrorMessage("ERROR: El valor en vias de acceso no tiene geometria tipo polilinea")
        except:
            parameters[2].setErrorMessage("ERROR: El valor en vias de acceso no tiene geometria tipo polilinea")

        #Verificacion de GDB, los featureclass requeridos para el analisis no deben estar vacíos, la GDB debe cumplir con el modelo de almacenamiento ANLA        
        try:
            AmenazaOtras = r"{}\\T_26_GESTION_RIESGO\\AmenazaOtras".format(inGDB)
            movMasa = arcpy.Select_analysis(AmenazaOtras, "in_memory\movMasa", "TIPO_EVEN = 4")
            emptyFC = []
            inputs = {
                "CoberturaTierra": r"{}\\T_20_BIOTICO_CONTI_COSTE\\CoberturaTierra".format(inGDB),
                "Pendiente": r"{}\\T_12_GEOMORFOLOGIA\\Pendiente".format(inGDB),
                "Suelo": r"{}\\T_14_SUELOS\\Suelo".format(inGDB),
                "AmenazaOtras: movimientos en masa": movMasa
            }

            if inputs:
                for param in inputs:
                    value = inputs[param]
                    count = arcpy.GetCount_management(value)
                    if str(count) == '0':
                        emptyFC.append(param)
                if emptyFC:
                    parameters[3].setErrorMessage("ERROR: Los siguientes FeatureClass son requeridos: {}".format(emptyFC))
        except:
            parameters[3].setErrorMessage("ERROR: La base de datos no esta conforme con el modelo de almacenamiento ANLA")

        return
        

    def execute(self, parameters, messages):
        """The source code of the tool."""
        #Comprobacion de licencia 
        self.isLicensed()

        # definicion de parametros
        self.inMetodo = parameters[0].filter.list
        self.inDem = parameters[1].valueAsText
        self.inVias = parameters[2].valueAsText
        self.inGDB = parameters[3].valueAsText
        self.inDistancia = parameters[4].valueAsText
        self.output = parameters[5].valueAsText
        descWorkspace = arcpy.Describe(self.output)  

        # ambiente de geoprocesamiento
        arcpy.env.workspace = r"in_memory"
        arcpy.env.scratchWorkspace = r"in_memory"
        arcpy.env.overwriteOutput = True 
        arcpy.env.parallelProcessingFactor = "0"
        arcpy.env.cellSize = "12.5" 
        
        arcpy.AddMessage(
            "Parametros aceptados, calculando la fragilidad visual del paisaje...")

        # mensaje de comprobacion de la extension Spatial Analyst
        estado = arcpy.CheckInExtension("Spatial")
        
        arcpy.AddMessage("La extension Spatial Analyst esta en %s status." % estado)
    
        # ejecucion del metodo de evaluacion segun eleccion del usuario

        try: 
            if parameters[0].value == self.inMetodo[1]:
                fvpMetHibrido = self.metHibrido()
                if descWorkspace.WorkspaceType in ["LocalDatabase"]:
                    arcpy.CopyRaster_management(fvpMetHibrido, "{}\\fvpMetHibrido".format(self.output))
                else:
                    arcpy.CopyRaster_management(fvpMetHibrido, "{}\\fvpMetHibrido.tif".format(self.output))
            else:
                parameters[0].value == self.inMetodo[0]
                fvpMetYeomans = self.metYeomans()
                
                if descWorkspace.WorkspaceType in ["LocalDatabase"]:
                    arcpy.CopyRaster_management(fvpMetYeomans, "{}\\fvpMetYeomans".format(self.output))
                else:
                    arcpy.CopyRaster_management(fvpMetYeomans, "{}\\fvpMetYeomans.tif".format(self.output))
                
            # limpieza de memoria
            arcpy.management.Delete("in_memory") 
            # Mensaje de proceso completado
            arcpy.AddMessage("Evaluacion exitosa.")   

        except Exception:
            arcpy.AddError(
                "No fue posible ejecutar la evaluacion, verifique los insumos utilizados.")
            arcpy.management.Delete("in_memory")

        return 

