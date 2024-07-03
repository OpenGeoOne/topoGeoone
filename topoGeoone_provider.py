# -*- coding: utf-8 -*-
__author__ = 'profCazaroli'
__date__ = '2024-06-20'
__copyright__ = '(C) 2024 by profCazaroli'
__revision__ = '$Format:%H$'

from qgis.core import QgsProcessingProvider
from .algoritmos.Divide_Lote_Buffer import divideLoteBufferAlgorithm
from .algoritmos.Angulos_Internos import AngulosInternosAlgorithm
from .algoritmos.Plano_de_Voo import PlanoVooAlgorithm
from qgis.PyQt.QtGui import QIcon
import os

class topoGeooneProvider(QgsProcessingProvider):
    def __init__(self):
        QgsProcessingProvider.__init__(self)

    def unload(self):
        pass

    def loadAlgorithms(self):
        self.addAlgorithm(divideLoteBufferAlgorithm())
        self.addAlgorithm(AngulosInternosAlgorithm())
        self.addAlgorithm(PlanoVooAlgorithm())

    def id(self):
        return 'topoGeoone'

    def name(self):
        return self.tr('topoGeoone')

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/images/topoGeoone.png')

    def longName(self):
        return self.name()



