# -*- coding: utf-8 -*-
__author__ = 'profCazaroli'
__date__ = '2024-06-20'
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

class AngulosInternosAlgorithm(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):
        self.addParameter(
        QgsProcessingParameterNumber('distancia', 
                                     'Distância',
                                     type=QgsProcessingParameterNumber.Double, 
                                     minValue=0.1, 
                                     defaultValue=3))
        
        self.addParameter(
        QgsProcessingParameterVectorLayer('poligono', 'Polígono', types=[QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterVectorLayer('vertices', 'Vértices', types=[QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterFeatureSink('angInt', 'Ângulos Internos'))

    def processAlgorithm(self, parameters, context, model_feedback):
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        outputs = {}

        parameters['angInt'].destinationName = 'Ângulos Internos'

        # Buffer nos Vértices
        alg_params = {
            'INPUT': parameters['vertices'],
            'DISSOLVE': False,
            'DISTANCE': parameters['distancia'],
            'END_CAP_STYLE': 0,  # Arredondado
            'JOIN_STYLE': 0,     # Arredondado
            'MITER_LIMIT': 2,
            'SEGMENTS': 9,
            'SEPARATE_DISJOINT': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback,
                                           is_child_algorithm=True)
        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Polígonos para linhas (a linha que define o ângulo)
        alg_params = {
            'INPUT': outputs['Buffer']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['linhaAng'] = processing.run('native:polygonstolines', alg_params, context=context,
                                                       feedback=feedback, is_child_algorithm=True)
        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

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
        
        return {'angInt': self.SAIDA}
    
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
        return 'Ângulos Internos'

    def displayName(self):
        return 'Ângulos Internos'

    def group(self):
        return 'Ângulos'

    def groupId(self):
        return 'Ângulos'
        
    def tr(self, string):
        return QCoreApplication.translate('Processing2', string)

    def createInstance(self):
        return AngulosInternosAlgorithm()
    
    def displayName(self):
        return self.tr('Calcular Ângulos Internos de Polígono')
    
    def tags(self):
        return self.tr('angle,angulos,medida,abertura,outer,inner,polygon,measure,topography,azimuth,\
                       extract,vertices,extrair,vértices').split(',')
    
    def icon(self):
        return QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'images/topoGeoone.png'))
    
    texto = 'Este algoritmo calcula os ângulos internos dos vértices de uma camada de polígonos.'
    figura = 'images/vect_polygon_angles.jpg'

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