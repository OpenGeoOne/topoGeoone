# -*- coding: utf-8 -*-
__author__ = 'profCazaroli'
__date__ = '2024-06-20'
__copyright__ = '(C) 2024 by profCazaroli'
__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterVectorLayer)
import processing

class divideLoteBufferAlgorithm(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('lotes', 'Lotes', types=[QgsProcessing.TypeVectorPolygon],
                                                            defaultValue='Lotes'))
        self.addParameter(
            QgsProcessingParameterVectorLayer('rio', 'Rio', types=[QgsProcessing.TypeVectorLine],
                                              defaultValue='Rio'))
        self.addParameter(QgsProcessingParameterFeatureSink('lotesD', 'Lotes Divididos'))

    def processAlgorithm(self, parameters, context, model_feedback):
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}
    
        parameters['lotesD'].destinationName = 'Lotes_Divididos'  

        alg_params = { # Buffer
            'DISSOLVE': False,
            'DISTANCE': 1.5,
            'END_CAP_STYLE': 0,  # Arredondado
            'INPUT': parameters['rio'],
            'JOIN_STYLE': 0,  # Arredondado
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback,
                                            is_child_algorithm=True)
        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'INPUT': parameters['lotes'],
            'LINES': outputs['Buffer']['OUTPUT'],
            'OUTPUT': parameters['lotesD']
        }
        outputs['LinhasComQuebra'] = processing.run('native:splitwithlines', alg_params, context=context,
                                                    feedback=feedback, is_child_algorithm=True)
        results['LotesDivididos'] = outputs['LinhasComQuebra']['OUTPUT']
    
        return results

    def name(self):
        return 'Divide Lote(s) Buffer'

    def displayName(self):
        return 'Divide Lote(s) Buffer'

    def group(self):
        return 'Lotes'

    def groupId(self):
        return 'Lotes'

    def tr(self, texto):
        return QCoreApplication.translate('Processing', texto)

    def createInstance(self):
        return divideLoteBufferAlgorithm()
