###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
from builtins import range
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from lazyflow.operators import OpMultiArraySlicer2
from volumina.api import LazyflowSource, AlphaModulatedLayer
from ilastik.utility import bind
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

class PredictionViewerGui( LayerViewerGui ):
    
    def __init__(self, *args, **kwargs):
        super(PredictionViewerGui, self).__init__(*args, **kwargs)
        self.topLevelOperatorView.PmapColors.notifyDirty( bind( self.updateAllLayers ) )
        self.topLevelOperatorView.LabelNames.notifyDirty( bind( self.updateAllLayers ) )
    
    def setupLayers(self):
        layers = []
        opLane = self.topLevelOperatorView

        exportedLayers = self._initPredictionLayers(opLane.PredictionProbabilities)
        layers += exportedLayers
        
        # If available, also show the raw data layer
        rawSlot = opLane.RawImage
        if rawSlot.ready():
            rawLayer = self.createStandardLayerFromSlot( rawSlot )
            rawLayer.name = "Raw Data"
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            layers.append( rawLayer )

        return layers 

    def _initPredictionLayers(self, predictionSlot):
        layers = []

        colors = []
        names = []

        opLane = self.topLevelOperatorView
        
        if opLane.PmapColors.ready():
            colors = opLane.PmapColors.value
        if opLane.LabelNames.ready():
            names = opLane.LabelNames.value

        # Use a slicer to provide a separate slot for each channel layer
        opSlicer = OpMultiArraySlicer2( parent=opLane.viewed_operator().parent )
        opSlicer.Input.connect( predictionSlot )
        opSlicer.AxisFlag.setValue('c')

        colors = [QColor(*c) for c in colors]
        for channel in range( len(colors), len(opSlicer.Slices) ):
            colors.append( PredictionViewerGui.DefaultColors[channel] )

        for channel in range( len(names), len(opSlicer.Slices) ):
            names.append( "Class {}".format(channel+1) )

        for channel, channelSlot in enumerate(opSlicer.Slices):
            if channelSlot.ready() and channel < len(colors) and channel < len(names):
                predictsrc = LazyflowSource(channelSlot)
                predictLayer = AlphaModulatedLayer( predictsrc,
                                                    tintColor=colors[channel],
                                                    range=(0.0, 1.0),
                                                    normalize=(0.0, 1.0) )
                predictLayer.opacity = 0.25
                predictLayer.visible = True
                predictLayer.name = names[channel]
                layers.append(predictLayer)

        return layers

    def _createDefault16ColorColorTable():
        colors = []

        # Transparent for the zero label
        colors.append(QColor(0,0,0,0))

        # ilastik v0.5 colors
        colors.append( QColor( Qt.red ) )
        colors.append( QColor( Qt.green ) )
        colors.append( QColor( Qt.yellow ) )
        colors.append( QColor( Qt.blue ) )
        colors.append( QColor( Qt.magenta ) )
        colors.append( QColor( Qt.darkYellow ) )
        colors.append( QColor( Qt.lightGray ) )

        # Additional colors
        colors.append( QColor(255, 105, 180) ) #hot pink
        colors.append( QColor(102, 205, 170) ) #dark aquamarine
        colors.append( QColor(165,  42,  42) ) #brown
        colors.append( QColor(0, 0, 128) )     #navy
        colors.append( QColor(255, 165, 0) )   #orange
        colors.append( QColor(173, 255,  47) ) #green-yellow
        colors.append( QColor(128,0, 128) )    #purple
        colors.append( QColor(240, 230, 140) ) #khaki

#        colors.append( QColor(192, 192, 192) ) #silver
#        colors.append( QColor(69, 69, 69) )    # dark grey
#        colors.append( QColor( Qt.cyan ) )

        assert len(colors) == 16

        #return [c.rgba() for c in colors]
        return colors

    DefaultColors = _createDefault16ColorColorTable()

