# From Python =============================================================
import copy
import re

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# From Maya =============================================================
import maya.cmds as mc

# From Red9 =============================================================
from Red9.core import Red9_Meta as r9Meta
from Red9.core import Red9_General as r9General

# From cgm ==============================================================
from cgm.core import cgm_Meta as cgmMeta
from cgm.core import cgm_PuppetMeta as cgmPM
from cgm.core.classes import SnapFactory as Snap
from cgm.core.lib import rayCaster as RayCast
from cgm.core.rigger import ModuleControlFactory as mControlFactory
from cgm.core.lib import nameTools
reload(mControlFactory)
from cgm.lib import (cgmMath,
                     attributes,
                     locators,
                     constraints,
                     modules,
                     nodes,
                     distance,
                     dictionary,
                     joints,
                     rigging,
                     search,
                     curves,
                     lists,
                     )

#from cgm.lib.classes import NameFactory

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Modules
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
class go(object):
    @r9General.Timer
    def __init__(self,moduleInstance,forceNew = True,**kws): 
        """
        To do:
        Add rotation order settting
        Add module parent check to make sure parent is templated to be able to move forward, or to constrain
        Add any other piece meal data necessary
        Add a cleaner to force a rebuild
        """
        # Get our base info
        #==============	        
        #>>> module null data
        if not issubclass(type(moduleInstance),cgmPM.cgmModule):
            log.error("Not a cgmModule: '%s'"%moduleInstance)
            return 
        
        assert moduleInstance.mClass in ['cgmModule','cgmLimb'],"Not a module"
        assert moduleInstance.isTemplated(),"Module is not templated: '%s'"%moduleInstance.getShortName()        
        assert moduleInstance.isSkeletonized(),"Module is not skeletonized: '%s'"%moduleInstance.getShortName()
        
        log.info(">>> ModuleControlFactory.go.__init__")
        self.m = moduleInstance# Link for shortness
        """
        if moduleInstance.hasControls():
            if forceNew:
                deleteControls(moduleInstance)
            else:
                log.warning("'%s' has already been skeletonized"%moduleInstance.getShortName())
                return        
        """
        #>>> Gather info
        #=========================================================
        self.l_moduleColors = self.m.getModuleColors()
        self.l_coreNames = self.m.coreNames.value
        self.i_templateNull = self.m.templateNull
        self.bodyGeo = self.m.modulePuppet.getGeo() or ['Morphy_Body_GEO'] #>>>>>>>>>>>>>>>>>this needs better logic   
        #Joints
        self.l_skinJoints = self.m.rigNull.getMessage('skinJoints')
        self.l_iSkinJoints = self.m.rigNull.skinJoints
        
        #>>> part name 
        self.partName = self.m.getPartNameBase()
        self.partType = self.m.moduleType or False
        
        self.direction = None
        if self.m.hasAttr('cgmDirection'):
            self.direction = self.m.cgmDirection or None
               
        #>>> Instances and joint stuff
        self.jointOrientation = modules.returnSettingsData('jointOrientation')        
        
        #>>> We need to figure out which control to make
        self.l_controlsToMakeArg = []
        if not self.m.getMessage('moduleParent'):
            self.l_controlsToMakeArg.append('cog')
        if self.m.rigNull.ik:
            self.l_controlsToMakeArg.extend(['vectorHandles'])
            if self.partType == 'torso':#Maybe move to a dict?
                self.l_controlsToMakeArg.append('spineIKHandle')            
        if self.m.rigNull.fk:
            self.l_controlsToMakeArg.extend(['segmentControls'])
            if self.partType == 'torso':#Maybe move to a dict?
                self.l_controlsToMakeArg.append('hips')
        log.info("l_controlsToMakeArg: %s"%self.l_controlsToMakeArg)
        
        #self.d_controls = mControlFactory.limbControlMaker(self.m,self.l_controlsToMakeArg)
        
        #Make our stuff
        if self.partType in d_moduleRigFunctions.keys():
            log.info("mode: cgmLimb control building")
            d_moduleRigFunctions[self.partType](self)
            #if not limbControlMaker(self,self.l_controlsToMakeArg):
                #raise StandardError,"limbControlMaker failed!"
        else:
            raise NotImplementedError,"haven't implemented '%s' rigging yet"%self.m.mClass
    
@r9General.Timer
def rigSpine(goInstance):
    """ 
    """ 
    if not issubclass(type(goInstance),go):
        log.error("Not a RigFactory.go instance: '%s'"%goInstance.getShortName())
        return False        
    self = goInstance#Link
    
    #>>> Figure out what's what
    #Add some checks like at least 3 handles
    
    #>>>Build our controls
    
    #>>>Set up structure
    
    #>>>Create joint chains
    #=============================================================
    #>>Surface chain
    l_surfaceJoints = mc.duplicate(self.l_skinJoints[:-1],po=True,ic=True,rc=True)
    l_iSurfaceJoints = []
    for i,j in enumerate(l_surfaceJoints):
        i_j = cgmMeta.cgmObject(j)
        i_j.addAttr('cgmType','surfaceJoint',attrType='string')
        i_j.doName()
        l_surfaceJoints[i] = i_j.mNode
        l_iSurfaceJoints.append(i_j)
        
    #Start
    i_startJnt = cgmMeta.cgmObject(mc.duplicate(self.l_skinJoints[0],po=True,ic=True,rc=True)[0])
    i_startJnt.addAttr('cgmType','deformationJoint',attrType='string',lock=True)
    i_startJnt.doName()
    
    #End
    l_endJoints = mc.duplicate(self.l_skinJoints[-2],ic=True,rc=True)
    i_endJnt = cgmMeta.cgmObject(l_endJoints[0])
    for j in l_endJoints:
        i_j = cgmMeta.cgmObject(j)
        i_j.addAttr('cgmType','deformationJoint',attrType='string',lock=True)
        i_j.doName()
    i_endJnt.parent = False
    
    #Influence chain for influencing the surface
    l_iInfluenceJoints = []
    for i_jnt in self.l_iSkinJoints:
        if i_jnt.hasAttr('cgmName') and i_jnt.cgmName in self.l_coreNames:
            i_new = cgmMeta.cgmObject(mc.duplicate(i_jnt.mNode,po=True,ic=True)[0])
            i_new.addAttr('cgmType','influenceJoint',attrType='string',lock=True)
            i_new.parent = False
            i_new.doName()
            l_iInfluenceJoints.append(i_new)
    
    
    createControlSurfaceSegment(l_surfaceJoints)
    return l_surfaceJoints
    


#>>> Utilities
#===================================================================
@r9General.Timer
def createControlSurfaceSegment(jointList,orientation = 'zyx',name='test'):
    """
    """
    #Good way to verify an instance list?
    #validate orientation
    outChannel = orientation[2]
    upChannel = '%sup'%orientation[1]
    log.info("out: '%s'"%outChannel)
    log.info("up: '%s'"%upChannel)
    
    #Create surface
    l_surfaceReturn = joints.loftSurfaceFromJointList(jointList,outChannel)
    
    i_controlSurface = cgmMeta.cgmObject( l_surfaceReturn[0] )
    i_controlSurface.addAttr('cgmName',name,attrType='string',lock=True)    
    i_controlSurface.addAttr('cgmType','controlSurface',attrType='string',lock=True)
    i_controlSurface.doName()
    
    l_iJointList = [cgmMeta.cgmObject(j) for j in jointList]
    #Create folicles
    l_iFollicleTransforms = []
    l_iFollicleShapes = []
    
    #First thing we're going to do is create our follicles
    for i_jnt in l_iJointList:       
        l_closestInfo = distance.returnClosestPointOnSurfaceInfo(i_jnt.mNode,i_controlSurface.mNode)
        log.debug("%s : %s"%(i_jnt.mNode,l_closestInfo))
        #>>> Follicle =======================================================
        l_follicleInfo = nodes.createFollicleOnMesh(i_controlSurface.mNode)
        i_follicleTrans = cgmMeta.cgmObject(l_follicleInfo[1])
        i_follicleShape = cgmMeta.cgmNode(l_follicleInfo[0])
        #> Name
        i_follicleTrans.doStore('cgmName',i_jnt.mNode)
        i_follicleTrans.doName()
        #>Set follicle value
        i_follicleShape.parameterU = l_closestInfo['normalizedU']
        i_follicleShape.parameterV = l_closestInfo['normalizedV']
        
        l_iFollicleShapes.append(i_follicleShape)
        l_iFollicleTransforms.append(i_follicleTrans)
        #>> Surface Anchor ===================================================
        
        """
        i_grpPos = cgmMeta.cgmObject( rigging.groupMeObject(i_jnt.mNode,False) )
        i_grpPos.doStore('cgmName',i_jnt.mNode)        
        i_grpOrient = cgmMeta.cgmObject( mc.duplicate(i_grpPos.mNode,returnRootsOnly=True)[0] )
        i_grpPos.addAttr('cgmType','surfaceAnchor',attrType='string',lock=True)
        i_grpOrient.addAttr('cgmType','surfaceOrient',attrType='string',lock=True)
        i_grpPos.doName()
        i_grpOrient.doName()
        i_grpOrient.parent = i_grpPos.mNode
        
        constraint = mc.pointConstraint(i_transFollicle.mNode,i_grpPos.mNode, maintainOffset=False)
        constraint = mc.orientConstraint(i_transFollicle.mNode,i_grpPos.mNode, maintainOffset=False)
        """
        
        #>>>Connect via constraint - no worky
        #constraint = mc.pointConstraint(i_grpOrient.mNode,i_jnt.mNode, maintainOffset=True)
        #constraint = mc.orientConstraint(i_grpOrient.mNode,i_jnt.mNode, maintainOffset=True)
        
        #constraints.doConstraintObjectGroup(i_transFollicle.mNode,transform,['point','orient'])
        #>>> Connect the joint
        #attributes.doConnectAttr('%s.translate'%i_grpPos.mNode,'%s.translate'%i_jnt.mNode)
        
    #>>>Create distance nodes
    #>>>Create scale stuff
    #>>>Create IK effectors
    l_iIK_effectors = []
    l_iIK_handles = []  
    l_iDistanceObjects = []
    l_iDistanceShapes = []  
    for i,i_jnt in enumerate(l_iJointList[:-1]):
        ik_buffer = mc.ikHandle (startJoint=i_jnt.mNode,
                                 endEffector = l_iJointList[i+1].mNode,
                                 setupForRPsolver = True, solver = 'ikRPsolver',
                                 enableHandles=True )
        #Handle
        i_IK_Handle = cgmMeta.cgmObject(ik_buffer[0])
        i_IK_Handle.parent = l_iFollicleTransforms[i+1].mNode
        i_IK_Handle.doStore('cgmName',i_jnt.mNode)    
        i_IK_Handle.doName()
        
        #Effector
        i_IK_Effector = cgmMeta.cgmObject(ik_buffer[1])        
        #i_IK_Effector.doStore('cgmName',i_jnt.mNode)    
        i_IK_Effector.doName()
        
        l_iIK_handles.append(i_IK_Handle)
        l_iIK_effectors.append(i_IK_Effector)
        
        #>> create up loc
        i_loc = i_jnt.doLoc()
        mc.move(0, 10, 0, i_loc.mNode, r=True,os=True,wd=True)
        
        #>> Distance nodes
        i_distanceShape = cgmMeta.cgmNode( mc.createNode ('distanceDimShape') )        
        i_distanceObject = cgmMeta.cgmObject( i_distanceShape.getTransform() )
        i_distanceObject.doStore('cgmName',i_jnt.mNode)
        i_distanceObject.addAttr('cgmType','measureNode',lock=True)
        i_distanceObject.doName(nameShapes = True)
        
        #Connect things
        mc.connectAttr ((l_iFollicleTransforms[i].mNode+'.translate'),(i_distanceShape.mNode+'.startPoint'))
        mc.connectAttr ((l_iFollicleTransforms[i+1].mNode+'.translate'),(i_distanceShape.mNode+'.endPoint'))
        
        l_iDistanceObjects.append(i_distanceObject)
        l_iDistanceShapes.append(i_distanceShape)
        
        #Connect joint to follicle
        #constraint = mc.pointConstraint(l_iFollicleTransforms[i].mNode,i_jnt.mNode, maintainOffset=True)
    
    #Connect the first joint's position since an IK handle isn't controlling it    
    attributes.doConnectAttr('%s.translate'%l_iFollicleTransforms[0].mNode,'%s.translate'%l_iJointList[0].mNode)
    
        
    """
    # connect joints to surface#
    surfaceConnectReturn = joints.attachJointChainToSurface(surfaceJoints,controlSurface,jointOrientation,upChannel,'animCrv')
    print surfaceConnectReturn
    # surface influence joints skinning#
    surfaceSkinCluster = mc.skinCluster (influenceJoints,controlSurface,tsb=True, n=(controlSurface+'_skinCluster'),maximumInfluences = 3, normalizeWeights = 1,dropoffRate=1)
    #surfaceSkinCluster = mc.skinCluster (influenceJoints,controlSurface,tsb=True, n=(controlSurface+'_skinCluster'),maximumInfluences = 3, normalizeWeights = 1, dropoffRate=1,smoothWeights=.5,obeyMaxInfluences=True, weight = 1)
    controlSurfaceSkinCluster = surfaceSkinCluster[0]
    
    # smooth skin weights #
    skinning.simpleControlSurfaceSmoothWeights(controlSurface)    
    """
    
d_moduleRigFunctions = {'torso':rigSpine,
                        }
    
 