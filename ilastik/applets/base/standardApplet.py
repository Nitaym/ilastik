from ilastik.utility import MultiLaneOperatorABC, OpAutoMultiLane
from ilastik.applets.base.applet import Applet
from ilastik.applets.base.singleToMultiGuiAdapter import SingleToMultiGuiAdapter

class StandardApplet( Applet ):
    """
    In most cases, it is easiest to use StandardApplet as a base class for your custom applet.
    StandardApplet provides default implementations for the methods required by the Applet base
    class, provided that the StandardApplet subclass overrides a couple (simple) methods.
    
    StandardApplet subclasses may expose their top-level operator in one of two ways:
    
    1) (Advanced) Override the :py:attr:`Applet.topLevelOperator<ilastik.applets.base.applet.Applet.topLevelOperator>` property directly.
    2) (Simple) Override BOTH :py:attr:`singleLaneOperatorClass` and :py:attr:`broadcastingSlots`, in which case a default implementation of :py:attr:`topLevelOperator` is provided for you.
    
    StandardApplet subclasses may expose their GUI in one of three ways:
    
    1) (Advanced) Override :py:meth:`Applet.getMultiLaneGui()<ilastik.applets.base.applet.Applet.getMultiLaneGui>` directly.
    2) (Simpler) Override :py:meth:`createSingleLaneGui`, in which case a default implementation of :py:meth:`getMultiLaneGui` is provided for you.
    3) (Simplest) Override :py:attr:`singleLaneGuiClass`, in which case default implementations of :py:meth:`createSingleLaneGui` and :py:meth:`getMultiLaneGui` are provided for you.  
    """

    def __init__(self, name, workflow=None):
        """
        Constructor.
        :param name: The applet's name as it will appear in the GUI (e.g. the Applet Drawer title).
        :param workflow: The workflow this applet belongs to (not required if the subclass provides its own topLevelOperator).
        """
        super(StandardApplet, self).__init__(name)
        self._gui = None
        self.__topLevelOperator = None
        self.__workflow = workflow

    #
    # Top-Level Operator
    #
    # Subclasses have 2 Choices:
    #   - Override topLevelOperator (advanced)
    #   - Override singleLaneOpeartorClass AND broadcastingSlots (easier; uses default topLevelOperator implementation)
    
    @property
    def singleLaneOperatorClass(self):
        """
        Return the operator class which handles a single image.
        Single-lane applets should override this property.
        (Multi-lane applets must override ``topLevelOperator`` directly.)
        """
        return NotImplemented

    @property
    def broadcastingSlots(self):
        """
        Slots that should be connected to all image lanes are referred to as "broadcasting" slots.
        Single-lane applets should override this property to return a list of the broadcasting slots' names.
        (Multi-lane applets must override ``topLevelOperator`` directly.)
        """
        return NotImplemented

    @property
    def topLevelOperator(self):
        """
        Get the top-level (multi-image-lane) operator for the applet.
        This default implementation uses ``singleLaneOperatorClass`` 
        and ``broadcastingSlots`` to generate the top-level operator.
        Applets that must be multi-image-lane-aware must override this property.
        Note that the top-level operator must adhere to the ``MultiLaneOperatorABC`` interface.
        """
        if self.__topLevelOperator is None:
            self.__createTopLevelOperator()
        return self.__topLevelOperator

    #
    # GUI
    #
    # Subclasses have 3 choices:
    # - Override getMultiLaneGui (advanced)
    # - Override createSingleLaneGui (easier: uses default getMultiLaneGui implementation)
    # - Override singleLaneGuiClass (easiest: uses default createSingleLaneGui and getMultiLaneGui implementations)

    @property
    def singleLaneGuiClass(self):
        """
        Return the class that will be instantiated for each image lane the applet needs.
        The class constructure should accept a single parameter: a single-lane of the top-level operator.
        """
        return NotImplemented

    def createSingleLaneGui(self, imageLaneIndex):
        """
        This function is called to create new instances of single-lane applet GUIs.
        If your applet's single-lane GUI requires special constructor arguments, then override this method.
        Otherwise, this default implementation generates instances of your ``singleLaneGuiClass``.
        """
        if self.singleLaneGuiClass is NotImplemented:
            message  = "Cannot create GUI.\n"
            message += "StandardApplet subclasses must implement ONE of the following:\n" 
            message += "singleLaneGuiClass, createSingleLaneGui, or getMultiLaneGui"
            raise NotImplementedError(message)
        singleLaneOperator = self.topLevelOperator.getLane( imageLaneIndex )
        return self.singleLaneGuiClass( singleLaneOperator )

    def getMultiLaneGui(self):
        """
        Overridden from ``Applet.getMultiLaneGui``.  This default implementation adapts 
        multiple GUIs instantiated with ``createSingleLaneGui`` into one mult-image gui, 
        which is what the Applet interface expects.
        """
        if self._gui is None:
            assert isinstance(self.topLevelOperator, MultiLaneOperatorABC), "If your applet's top-level operator doesn't satisfy MultiLaneOperatorABC, you must implement getMultiLaneGui yourself."
            self._gui = SingleToMultiGuiAdapter( self.createSingleLaneGui, self.topLevelOperator )
        return self._gui

    #
    # Private
    #

    def __createTopLevelOperator(self):
        """
        Called by the default implementation of ``topLevelOperator`` to create a multi-image operator by wrapping single-image operators.
        """
        assert self.__topLevelOperator is None
        operatorClass = self.singleLaneOperatorClass
        broadcastingSlots = self.broadcastingSlots
        if operatorClass is NotImplemented or broadcastingSlots is NotImplemented:
            message = "Could not create top-level operator for {}\n".format( self.__class__ )
            message += "StandardApplet subclasses must implement the singleLaneOperatorClass and broadcastingSlots"
            message += " members OR override topLevelOperator themselves."
            raise NotImplementedError(message)

        if self.__workflow is None:
            message = "Could not create top-level operator for {}\n".format( self.__class__ )
            message += "Please initialize StandardApplet base class with a workflow object."
            raise NotImplementedError(message)
        
        self.__topLevelOperator = OpAutoMultiLane(self.singleLaneOperatorClass,
                                                  parent=self.__workflow,
                                                  broadcastingSlotNames=self.broadcastingSlots)

