# -*- coding: utf-8 -*-
__author__ = 'profCazaroli'
__date__ = '2024-07-02'
__copyright__ = '(C) 2024 by profCazaroli'
__revision__ = '$Format:%H$'

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingUtils
from qgis.core import QgsTextFormat, QgsTextBufferSettings
from qgis.core import QgsPalLayerSettings, QgsVectorLayerSimpleLabeling
from qgis.PyQt.QtGui import QColor, QFont, QIcon
from qgis.core import QgsLineSymbol, QgsCategorizedSymbolRenderer, QgsRendererCategory
from qgis.PyQt.QtCore import QCoreApplication
import processing
import os
import numpy as np
from qgis.PyQt.QtCore import QgsProject, QgsVectorLayer, QgsPoint, QgsField, QVariant
from qgis.PyQt.QtCore import QgsFeature, QgsGeometry, QgsPointXY, QgsWkbTypes

# Dados Air 2S (5472 × 3648)

class PlanoVooAlgorithm(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterNumber('h','Altura de Voo',
                                                       type=QgsProcessingParameterNumber.Double,
                                                       minValue=50,defaultValue=100))
        self.addParameter(QgsProcessingParameterNumber('dc','Tamanho do Sensor Horizontal (m)',
                                                       type=QgsProcessingParameterNumber.Double,
                                                       minValue=0,defaultValue=13.2e-3))
        self.addParameter(QgsProcessingParameterNumber('dl','Tamanho do Sensor Vertical (m)',
                                                       type=QgsProcessingParameterNumber.Double,
                                                       minValue=0,defaultValue=8.8e-3))
        self.addParameter(QgsProcessingParameterNumber('f','Distância Focal (m)',
                                                       type=QgsProcessingParameterNumber.Double,
                                                       minValue=0,defaultValue=8.38e-3))
        self.addParameter(QgsProcessingParameterNumber('percL','Percentual de sobreposição Lateral (75% = 0.75)',
                                                       type=QgsProcessingParameterNumber.Double,
                                                       minValue=0.60,defaultValue=0.75))
        self.addParameter(QgsProcessingParameterNumber('percF','Percentual de sobreposição Frontal (85% = 0.85)',
                                                       type=QgsProcessingParameterNumber.Double,
                                                       minValue=0.60,defaultValue=0.85))
        
        self.addParameter(QgsProcessingParameterVectorLayer('terreno', 'Terreno do Voo', types=[QgsProcessing.TypeVectorPolygon]))
        
        self.addParameter(QgsProcessingParameterFeatureSink('linhasVoo', 'Linhas de Voo'))

    def processAlgorithm(self, parameters, context, model_feedback):
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        outputs = {}

        parameters['linhasVoo'].destinationName = 'Linhas de Voo'

        # ===========================================================
        # Parâmetros de entrada para variáveis
        camada = parameters['terreno']
        h = parameters['h']
        dc = parameters['dc']
        dl = parameters['dl']
        f = parameters['f']
        percL = parameters['percL']
        percF = parameters['percF']

        # Distância das linhas de voo paralelas - Espaçamento Lateral
        tg_alfa_2 = (dc/(2*f))
        alfa = np.degrees(2*np.arctan(tg_alfa_2))
        D = dc*h/f
        SD = percL*D
        h1 = SD/(2*tg_alfa_2)
        h2 = h - h1
        deltax = h2*SD/h1
        if deltax > 0: # valor negativo para ser do Norte para o Sul
            deltax = deltax * (-1)
        deltax = round(deltax,1) # Sobreposição Lateral

        # Espaçamento Frontal
        tg_alfa_2 = (dl/(2*f))
        alfa = np.degrees(2*np.arctan(tg_alfa_2))
        D = dl*h/f
        SD = percF*D
        h1 = SD/(2*tg_alfa_2)
        h2 = h - h1
        deltay = h2*SD/h1
        deltay = round(deltay,1) # Sobreposição Frontal

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # ===========================================================
        # Criar Linha do polígono mais ao Norte
        # Distância do ponto mais ao Norte do mais ao Sul
        pontoNorte = None
        pontoSul = None

        # Obter a primeira feature (único polígono)
        f = next(camada.getFeatures())

        # Obter a geometria do polígono
        geom = f.geometry()

        # Iterar sobre os vértices do polígono para encontrar 
        # a coordenada mais ao sul
        for ponto in geom.vertices():
            if pontoNorte is None or ponto.y() > pontoNorte.y():
                pontoNorte = ponto
            if pontoSul is None or ponto.y() < pontoSul.y():
                pontoSul = ponto

        p1 = pontoNorte.y()
        p2 = pontoSul.y()

        print(p1)
        print(p2)
        d = abs(p1-p2)

        print(d)

        # Criando a Camada Linha mais ao Norte
        maxNorte = float('-inf')
        limiteMaisNorte = None

        # Obter a primeira feature (único polígono)
        f = next(camada.getFeatures())

        # Obter a geometria do polígono
        geom = f.geometry()

        # obter o Lado do Terreno mais ao Norte
        pols = geom.asPolygon()
        for p in pols:
            for i in range(len(p) - 1):
                ponto1 = p[i]
                ponto2 = p[i + 1]
                pontoMedio = QgsPoint((ponto1.x() + ponto2.x()) / 2, (ponto1.y() + ponto2.y()) / 2)
                if pontoMedio.y() > maxNorte: # obter a maior Latitude
                    maxNorte = pontoMedio.y()
                    limiteMaisNorte = (ponto1, ponto2)

        ponto1, ponto2 = limiteMaisNorte
        x1, y1 = ponto1.x(),ponto1.y()
        x2, y2 = ponto2.x(),ponto2.y()

        print(x1, y1)
        print(x2, y2)

        crs = camada.crs().authid()
        camadaLinha = QgsVectorLayer(f"LineString?crs={crs}", "Lado Mais ao Norte", "memory")
        provider = camadaLinha.dataProvider()

        # Adicionar um campo de ID à nova camada
        provider.addAttributes([QgsField("ID", QVariant.Int)])
        camadaLinha.updateFields()

        # Criar uma nova feição com a aresta mais ao norte
        linha = QgsFeature()
        linha.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(x1, y1), QgsPointXY(x2, y2)]))
        linha.setAttributes([1])

        # Adicionar a feição à camada
        provider.addFeatures([linha])
        camadaLinha.updateExtents()

        # Adicionar a camada ao projeto
        #QgsProject.instance().addMapLayer(camadaLinha)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}
        
        # ===========================================================
        # Extender a Linha criada com os extremos W e E
        alg_params = {
            'INPUT': camadaLinha,
            'START_DISTANCE':100,
            'END_DISTANCE':100,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }

        outputs['linhaExtendida'] = processing.run('native:extendlines', alg_params, context=context,
                                                       feedback=feedback, is_child_algorithm=True)

        # Linhas paralelas a partir da Linha criada
        alg_params = {
            'INPUT': outputs['linhaExtendida']['OUTPUT'],
            'COUNT':10,
            'OFFSET':deltax,
            'SEGMENTS':8,
            'JOIN_STYLE':0,
            'MITER_LIMIT':2,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }

        outputs['linhas'] = processing.run('native:arrayoffsetlines', alg_params, context=context,
                                                       feedback=feedback, is_child_algorithm=True)
        
        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # ===========================================================
        # Interseção - Ângulo Interno
        alg_params = {
            'GRID_SIZE': None,
            'INPUT': outputs['linhaAng']['OUTPUT'],
            'INPUT_FIELDS': [''],
            'OVERLAY': parameters['poligono'],
            'OVERLAY_FIELDS': [''],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': parameters['angInt']
        }

        outputs['OUTPUT'] = processing.run('native:intersection', alg_params, context=context, feedback=feedback,
                                             is_child_algorithm=True)
        
        self.SAIDA = outputs['OUTPUT']

        return {'linhasVoo': self.SAIDA}
    
    def postProcessAlgorithm(self, context, feedback):
        camada = QgsProcessingUtils.mapLayerFromString(self.SAIDA['OUTPUT'], context)
        
        # Simbologia
        simbolo = QgsLineSymbol.createSimple({'color': 'red', 'width': '0.6'})
        renderer = QgsCategorizedSymbolRenderer("field_name", [QgsRendererCategory(None, simbolo, "Categoria")])
        camada.setRenderer(renderer)

        # Rótulo
        settings = QgsPalLayerSettings()  # Configurar as definições do rótulo
        settings.fieldName = 'format_number("ang_int_dec",2)'
        settings.isExpression = True
        settings.placement = QgsPalLayerSettings.Line  # Posicionamento do rótulo ao longo da linha
        settings.enabled = True

        textoF = QgsTextFormat()  # Configurar o formato do texto
        textoF.setFont(QFont("Arial", 13))
        textoF.setSize(12)

        bufferS = QgsTextBufferSettings()  # Configurar o contorno do texto
        bufferS.setEnabled(True)
        bufferS.setSize(1)
        bufferS.setColor(QColor("white"))

        textoF.setBuffer(bufferS)

        settings.setFormat(textoF)

        camada.setLabelsEnabled(True)
        camada.setLabeling(QgsVectorLayerSimpleLabeling(settings))
        
        camada.triggerRepaint() # Atualizar a interface do QGIS

        return {'angInt': self.SAIDA['OUTPUT']}
    
    def name(self):
        return 'Plano de Voo Drone'

    def displayName(self):
        return 'Plano de Voo Drone'

    def group(self):
        return 'Drones'

    def groupId(self):
        return 'Drones'
        
    def tr(self, string):
        return QCoreApplication.translate('Processing3', string)

    def createInstance(self):
        return PlanoVooAlgorithm()
    
    def displayName(self):
        return self.tr('Calcular sobreposição Lateral e Frontal de Voo de Drone')
    
    def tags(self):
        return self.tr('drone,side overlap,front overlay,flight,flight plan,topography').split(',')
    
    def icon(self):
        return QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'images/topoGeoone.png'))
    
    texto = 'Este algoritmo calcula a sobreposição lateral e frontal de Voo de Drone.'
    figura = 'images/voo_drone.jpg'

    def shortHelpString(self):
        corpo = '''<div align="center">
                      <img src="'''+ os.path.join(os.path.dirname(os.path.dirname(__file__)), self.figura) +'''">
                      </div>
                      <div align="right">
                      <p align="right">
                      <b>'Autor: Prof Cazaroli'</b>
                      </p>'Geoone'</div>
                    </div>'''
        return self.tr(self.texto) + corpo