#!/usr/bin/env python
"""
These wrap a CameraFrameDisplay and possibly a ParamsDisplay in
a single object that Display interacts with.

Hazen 4/17.
"""

from PyQt5 import QtCore, QtWidgets

import storm_control.hal4000.display.cameraFrameViewer as cameraFrameViewer
import storm_control.hal4000.display.paramsViewer as paramsViewer
import storm_control.hal4000.feeds.feeds as feeds
import storm_control.hal4000.halLib.halDialog as halDialog
import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.hal4000.qtdesigner.camera_detached_ui as cameraDetachedUi
import storm_control.hal4000.qtdesigner.camera_params_detached_ui as cameraParamsDetachedUi
import storm_control.hal4000.qtdesigner.camera_params_ui as cameraParamsUi
import storm_control.hal4000.qtdesigner.feed_viewer_ui as feedViewerUi


class CameraParamsMixin(object):
    """
    This mixin provides all of the default functionality for a
    viewer, which is an awkward combination of a parameters viewer
    that might or might not exist and a frame viewer. Furthermore
    the UI of the parameter viewer and frame viewer might actually
    be located in the UI of HAL (in classic mode).
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.camera_name = ""
        self.params_viewer = None

    def configure1(self):
        pass

    def configure2(self):
        pass    
    
    def getParameters(self):
        return self.frame_viewer.getParameters()

    def getViewerName(self):
        return self.module_name

    def handleFeedChange(self, feed_name):
        self.guiMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = "get camera functionality",
                                                   data = {"camera" : feed_name,
                                                           "extra data" : self.module_name}))

    def handleGuiMessage(self, message):
        self.guiMessage.emit(message)

    def handleRecordButton(self, boolean):
        self.guiMessage.emit(self.frame_viewer.ui.recordButton.getHalMessage())

    def newParameters(self, parameters):
        self.frame_viewer.newParameters(parameters)

    def setCameraFunctionality(self, camera_functionality):
        self.frame_viewer.setCameraFunctionality(camera_functionality)
        if self.params_viewer is not None:
            self.params_viewer.setCameraFunctionality(camera_functionality)

    def setFeedNames(self, feed_names):
        self.frame_viewer.setFeedNames(feed_names)

    def showViewer(self, show_gui):
        self.handleFeedChange(self.frame_viewer.getFeedName())
        if show_gui:
            self.show()

    def startFilm(self, film_settings):
        self.frame_viewer.startFilm(film_settings)
        if self.params_viewer is not None:
            self.params_viewer.startFilm()

    def stopFilm(self):
        self.frame_viewer.stopFilm()
        if self.params_viewer is not None:
            self.params_viewer.stopFilm()

    def updatedParameters(self, parameters):
        self.frame_viewer.updatedParameters()

            
class ClassicViewer(QtCore.QObject, CameraParamsMixin):
    """
    This does not actually show anything, it creates and manages the
    camera and parameters UI elements but they are displayed in HAL.
    """
    guiMessage = QtCore.pyqtSignal(object)

    def __init__(self, module_name = "", camera_name = "camera1", default_colortable = None, **kwds):
        super().__init__(**kwds)
        self.module_name = module_name

        self.frame_viewer = cameraFrameViewer.CameraFrameViewer(display_name = self.module_name,
                                                                feed_name = camera_name,
                                                                default_colortable = default_colortable)
        self.params_viewer = paramsViewer.ParamsViewer(viewer_name = self.module_name,
                                                       viewer_ui = cameraParamsUi)

        self.frame_viewer.showRecord(True)

        self.frame_viewer.feedChange.connect(self.handleFeedChange)
        self.frame_viewer.guiMessage.connect(self.handleGuiMessage)
        self.frame_viewer.ui.recordButton.clicked.connect(self.handleRecordButton)

    def cleanUp(self, qt_settings):
        pass

    def configure1(self):
        """
        Send messages with the UI elements to HAL.
        """
        self.guiMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = "add to ui",
                                                   data = {"ui_parent" : "hal.cameraFrame",
                                                           "ui_widget" : self.frame_viewer}))

        self.guiMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = "add to ui",
                                                   data = {"ui_order" : 2,
                                                           "ui_parent" : "hal.containerWidget",
                                                           "ui_widget" : self.params_viewer}))

    def configure2(self):
        self.handleFeedChange(self.frame_viewer.getFeedName())

    def showViewer(self, show_gui):
        self.handleFeedChange(self.frame_viewer.getFeedName())

    
class FeedViewer(halDialog.HalDialog, CameraParamsMixin):
    """
    These are dialog boxes that show only the camera 
    image without the camera parameters.
    """
    guiMessage = QtCore.pyqtSignal(object)
    
    def __init__(self, camera_name = "camera1", default_colortable = None, **kwds):
        super().__init__(**kwds)

        self.frame_viewer = cameraFrameViewer.CameraFrameViewer(display_name = self.module_name,
                                                                feed_name = camera_name,
                                                                default_colortable = default_colortable)

        self.ui = feedViewerUi.Ui_Dialog()
        self.ui.setupUi(self)
        layout = QtWidgets.QGridLayout(self.ui.cameraFrame)
        layout.setContentsMargins(2,2,2,2)
        layout.addWidget(self.frame_viewer)

        self.frame_viewer.feedChange.connect(self.handleFeedChange)
        self.frame_viewer.guiMessage.connect(self.handleGuiMessage)


class DetachedViewer(halDialog.HalDialog, CameraParamsMixin):
    """
    These are the dialog boxes that show the camera image in combination with a
    parameters view. In detached mode there is at least one of these.
    """
    guiMessage = QtCore.pyqtSignal(object)

    def __init__(self, camera_name = "camera1", default_colortable = None, **kwds):
        super().__init__(**kwds)

        self.frame_viewer = cameraFrameViewer.CameraFrameViewer(display_name = self.module_name,
                                                                feed_name = camera_name,
                                                                default_colortable = default_colortable)
        self.params_viewer = paramsViewer.ParamsViewer(viewer_name = self.module_name,
                                                       viewer_ui = cameraParamsDetachedUi)

        self.ui = cameraDetachedUi.Ui_Dialog()
        self.ui.setupUi(self)

        layout = QtWidgets.QGridLayout(self.ui.cameraFrame)
        layout.setContentsMargins(2,2,2,2)
        layout.addWidget(self.frame_viewer)

        layout = QtWidgets.QGridLayout(self.ui.cameraParamsFrame)
        layout.setContentsMargins(2,2,2,2)
        layout.addWidget(self.params_viewer)

        self.frame_viewer.feedChange.connect(self.handleFeedChange)
        self.frame_viewer.guiMessage.connect(self.handleGuiMessage)
        self.frame_viewer.ui.recordButton.clicked.connect(self.handleRecordButton)

    def configure2(self):
        self.handleFeedChange(self.frame_viewer.getFeedName())






#    def handleShutterButton(self, boolean):
#        self.guiMessage.emit(halMessage.HalMessage(source = self,
#                                                   m_type = "shutter clicked",
#                                                   data = {"display_name" : self.module_name,
#                                                           "camera" : self.camera_name}))
        

#        if self.params_viewer is not None:
#            self.params_viewer.newParameters(parameters.get(self.camera_name))

#    def getFeedName(self):
#        return self.frame_viewer.getFeedName()
        
#    def getViewerName(self):
#        return self.module_name

#    def enableStageDrag(self, enabled):
#        self.frame_viewer.enableStageDrag(enabled)

#    def getDefaultParameters(self):
#        return self.frame_viewer.getDefaultParameters()
        


#    def messageCameraEMCCDGain(self, camera_name, emccd_gain):
#        if (camera_name == self.camera_name):
#            if self.params_viewer is not None:
#                self.params_viewer.setEMCCDGain(emccd_gain)

#    def messageCameraShutter(self, camera_name, camera_shutter):
#        if (camera_name == self.camera_name):
#            self.frame_viewer.setShutter(camera_shutter)

#    def messageCameraTemperature(self, camera_name, state, temperature):
#        if (camera_name == self.camera_name):
#            if self.params_viewer is not None:
#                self.params_viewer.setTemperature(state, temperature)

                
#    def messageGetFeedInformation(self, feed_info):
#        self.frame_viewer.setFeedInformation(feed_info)

#    def messageFeedsInformation(self, feeds_info):
#        self.frame_viewer.setFeeds(feeds_info)

#    def messageNewFrame(self, frame):
#        self.frame_viewer.newFrame(frame)
