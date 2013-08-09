"""
cgmLimb
Josh Burton (under the supervision of David Bokser:)
www.cgmonks.com
1/12/2011

Key:
1) Class - Limb
    Creates our rig objects
2)  


"""
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

# From cgm ==============================================================
from cgm.core import cgm_Meta as cgmMeta
from cgm.core import cgm_General as cgmGeneral
from cgm.core.classes import SnapFactory as Snap

from cgm.lib import (distance,
                     attributes,
                     curves,
                     deformers,
                     lists,
                     rigging,
                     skinning,
                     dictionary,
                     search,
                     nodes,
                     joints,
                     cgmMath)
reload(distance)

#>>> Utilities
#===================================================================
def metaFreezeJointOrientation(targetJoints):
    """
    Copies joint orietnations from one joint to others
    """
    if type(targetJoints) not in [list,tuple]:targetJoints=[targetJoints]

    ml_targetJoints = cgmMeta.validateObjListArg(targetJoints,cgmMeta.cgmObject)
    for i_jnt in ml_targetJoints:
	if i_jnt.getConstraintsTo():
            log.warning("freezeJointOrientation>> target joint has constraints. Can't change orientation. Culling from targets: '%s'"%i_jnt.getShortName())
	    return False
	if i_jnt.getMayaType() != 'joint':
            log.warning("freezeJointOrientation>> target joint is not a joint. Can't change orientation. Culling from targets: '%s'"%i_jnt.getShortName())
	    return False
	
    #buffer parents and children of 
    d_children = {}
    d_parent = {}
    for i_jnt in ml_targetJoints:
        d_children[i_jnt] = cgmMeta.validateObjListArg( mc.listRelatives(i_jnt.mNode, path=True, c=True),cgmMeta.cgmObject,True) or []
	d_parent[i_jnt] = i_jnt.parent
    for i_jnt in ml_targetJoints:
	for i,i_c in enumerate(d_children[i_jnt]):
	    log.info(i_c.getShortName())
	    log.info("freezeJointOrientation>> parented '%s' to world to orient parent"%i_c.mNode)
	    i_c.parent = False
	
    #Orient
    for i,i_jnt in enumerate(ml_targetJoints):
	"""
	So....jointOrient is always in xyz rotate order
	dup,rotate order
	Unparent, add rotate & joint rotate, push value, zero rotate, parent back, done
	"""
	i_jnt.parent = d_parent.get(i_jnt)#parent back first before duping
	buffer = mc.duplicate(i_jnt.mNode,po=True,ic=False)[0]#Duplicate the joint
	i_dup = cgmMeta.cgmObject(buffer)
	i_dup.rotateOrder = 0
        mc.delete(mc.orientConstraint(i_jnt.mNode, i_dup.mNode, w=1, maintainOffset = False))
	
	#i_dup.parent = False
	
	l_rValue = i_dup.rotate
	l_joValue = i_dup.jointOrient
	l_added = cgmMath.list_add(l_rValue,l_joValue)	
	
	i_dup.jointOrientX = l_added[0]
	i_dup.jointOrientY = l_added[1]
	i_dup.jointOrientZ = l_added[2]	
	i_dup.rotate = [0,0,0]
	
	i_dup.parent = i_jnt.parent
	
	i_jnt.rotate = [0,0,0]
	i_jnt.jointOrient = i_dup.jointOrient	
	
        i_dup.delete()
	
    #reparent
    for i_jnt in ml_targetJoints:
        for i_c in d_children[i_jnt]:
            log.info("freezeJointOrientation>> parented '%s' back"%i_c.getShortName())
            i_c.parent = i_jnt.mNode 
	    cgmMeta.cgmAttr(i_c,"inverseScale").doConnectIn("%s.scale"%i_jnt.mNode )
	    
    return True


def get_orientChild(targetJoint):
    mi_targetJoint = cgmMeta.validateObjArg(targetJoint,cgmMeta.cgmObject,mayaType='joint')
    ml_childrenJoints = cgmMeta.validateObjListArg(mi_targetJoint.getChildren(),cgmMeta.cgmObject,mayaType='joint')
    if not ml_childrenJoints:
	log.warning("%s.get_orientChild >> failed to find children joints to check"%(mi_targetJoint.p_nameShort))
	return False
    
    for i_j in ml_childrenJoints:
	"""
	Measure dist
	"""
	pass
	
    
#>>> Helper joints
#===================================================================
__l_helperTypes__ = 'halfHold','childRootHold','halfPush'

@cgmGeneral.Timer
def add_defHelpJoint(targetJoint,childJoint = None, helperType = 'halfPush',
                       orientation = 'zyx',doSetup = True, forceNew = False):
    """
    Add helper joints to other joints
    
    @KWS
    targetJoint(string/inst)
    helperType(str) --
         'halfHold' -- like a regular bend joint that needs a holder at it's root, like a finger
	 'childRootHold' -- holds form on a hard rotate, like a finger root
    jointUp(str) --
    orientation(str)
    forceNew(bool) -- delete if exists
    
    """
    mi_posLoc = False
    if orientation != 'zyx':
	raise NotImplementedError, "add_defHelpJoints >> only currently can do orienation of 'zyx'"
    #Validate base info
    mi_targetJoint = cgmMeta.validateObjArg(targetJoint,cgmMeta.cgmObject,mayaType='joint')
    log.info(">>> %s.add_defHelpJoint >> "%mi_targetJoint.p_nameShort + "="*75)            
    
    #>>Child joint
    #TODO -- implement child guessing
    mi_childJoint = cgmMeta.validateObjArg(childJoint,cgmMeta.cgmObject,mayaType='joint',noneValid=True)
    log.info("%s.add_defHelpJoints >> Child joint : '%s'"%(mi_targetJoint.p_nameShort,mi_childJoint))
        
    str_plugHook = 'defHelp_joints'
    
    #Validate some data
    d_typeChecks = {'halfHold':[mi_childJoint],'childRootHold':[mi_childJoint],'halfPush':[mi_childJoint]}
    if helperType in d_typeChecks.keys():
	for k in d_typeChecks[helperType]:
	    if not k:
		log.warning("%s.add_defHelpJoints >> must have valid %s for helperType: '%s'"%(mi_targetJoint.p_nameShort,k,helperType))	    
		return False    
    
    #>Register
    #----------------------------------------------------------------
    #First see if we have one
    ml_dynDefHelpJoints = cgmMeta.validateObjListArg(mi_targetJoint.getMessage(str_plugHook),cgmMeta.cgmObject,noneValid=True)
    i_matchJnt = False
    for i_jnt in ml_dynDefHelpJoints:
	log.info(i_jnt.p_nameShort)
	if i_jnt.getAttr('defHelpType') == helperType and i_jnt.getMessage('defHelp_target') == [mi_targetJoint.p_nameLong]:
	    i_matchJnt = i_jnt
	    log.info("%s.add_defHelpJoints >> Found match: '%s'"%(mi_targetJoint.p_nameShort,i_matchJnt.p_nameShort))	    	    
	    break
	
    if i_matchJnt:#if we have a match
	if forceNew:
	    log.info("%s.add_defHelpJoints >> helper exists, no force new : '%s'"%(mi_targetJoint.p_nameShort,i_matchJnt.p_nameShort))	    	    
	    ml_dynDefHelpJoints.remove(i_matchJnt)	    
	    mc.delete(i_matchJnt.mNode)
	    
	else:
	    log.info("%s.add_defHelpJoints >> helper exists, no force new : '%s'"%(mi_targetJoint.p_nameShort,i_matchJnt.p_nameShort))	    
	    
    if not i_matchJnt:
	i_dupJnt = mi_targetJoint.doDuplicate(incomingConnections = False,breakMessagePlugsOut=True)#Duplicate
	i_dupJnt.addAttr('cgmTypeModifier',helperType)#Tag
	i_dupJnt.addAttr('defHelpType',helperType,lock=True)#Tag    
	i_dupJnt.doName()#Rename
	i_dupJnt.parent = mi_targetJoint#Parent
	ml_dynDefHelpJoints.append(i_dupJnt)#append to help joint list
	
	i_dupJnt.connectChildNode(mi_childJoint,"defHelp_childTarget")#Connect Child target
	mi_targetJoint.connectChildrenNodes(ml_dynDefHelpJoints,str_plugHook,'defHelp_target')#Connect
    else:
	i_dupJnt = i_matchJnt
    #------------------------------------------------------------
    log.info("%s.add_defHelpJoints >> Created helper joint : '%s'"%(mi_targetJoint.p_nameShort,i_dupJnt.p_nameShort))
    
    if doSetup:
	try:setup_defHelpJoint(i_dupJnt,orientation)
	except StandardError,error:
	    log.warning("%s.add_defHelpJoints >> Failed to setup | %s"%(i_dupJnt.p_nameShort,error))	    
	        
    return i_dupJnt

@cgmGeneral.Timer
def setup_defHelpJoint(targetJoint,orientation = 'zyx'):
    """
    Setup a helper joint
    
    @KWS
    targetJoint(string/inst) -- must be helper joint
    orientation(str)
    forceNew(bool) -- delete if exists
    
    helperTypes --
     'halfHold' -- like a regular bend joint that needs a holder at it's root, like a finger
     'childRootHold' -- holds form on a hard rotate, like a finger root
     'halfPush' -- like a regular bend joint that needs a holder at it's root, like a finger
    """
    mi_posLoc = False
    if orientation != 'zyx':
	raise NotImplementedError, "add_defHelpJoints >> only currently can do orienation of 'zyx'"
    
    #Validate base info
    mi_helperJoint = cgmMeta.validateObjArg(targetJoint,cgmMeta.cgmObject,mayaType='joint')
    mi_targetJoint = cgmMeta.validateObjArg(mi_helperJoint.getMessage('defHelp_target'),cgmMeta.cgmObject,mayaType='joint')        
    mi_childJoint = cgmMeta.validateObjArg(mi_helperJoint.getMessage('defHelp_childTarget'),cgmMeta.cgmObject,mayaType='joint')    
    str_helperType = mi_helperJoint.getAttr('defHelpType')
    if not str_helperType in __l_helperTypes__:
	log.warning("%s.setup_defHelpJoint >> '%s' not a valid helperType: %s"%(mi_helperJoint.p_nameShort,str_helperType,__l_helperTypes__))	    
	return False
    
    log.info(">>> %s.setup_defHelpJoint >> "%mi_helperJoint.p_nameShort + "="*75)            
    #>Setup
    #---------------------------------------------------------------- 
    if str_helperType == 'halfHold':
	mi_helperJoint.tx = mi_childJoint.tx *.5
	mi_helperJoint.ty = mi_childJoint.ty *.5
	mi_helperJoint.tz = mi_childJoint.tz *.5
	
	mi_helperJoint.__setattr__("t%s"%orientation[1],(-mi_childJoint.tz *.2))
	
	#Setup sd
	'''
	""" set our keyframes on our curve"""
	for channel in :
	    mc.setKeyframe (attributeHolder,sqshStrchAttribute, time = cnt, value = 1)
	    """ making the frame cache nodes """
	    frameCacheNodes.append(nodes.createNamedNode(jointChain[jnt],'frameCache'))
	    cnt+=1
	""" connect it """
	for cacheNode  in frameCacheNodes:
	    mc.connectAttr((sqshStrchAttribute),(cacheNode+'.stream'))
	cnt=1
	""" set the vary time """
	for cacheNode in frameCacheNodes:
	    mc.setAttr((cacheNode+'.varyTime'),cnt)
	    cnt+=1	
	'''
	#With half hold, our driver is the child joint
	str_driverRot = "%s.r%s"%(mi_childJoint.mNode,orientation[2])
	str_drivenTransAim = "%s.t%s"%(mi_helperJoint.mNode,orientation[0])
	f_baseTransValue = mi_helperJoint.getAttr("t%s"%(orientation[0]))
	f_sdkTransValue = f_baseTransValue + (f_baseTransValue * .3)	
	mc.setDrivenKeyframe(str_drivenTransAim,
	                     currentDriver = str_driverRot,
	                     driverValue = 0,value = f_baseTransValue)
	mc.setDrivenKeyframe(str_drivenTransAim,
	                     currentDriver = str_driverRot,
	                     driverValue = 110,value = f_sdkTransValue)	
	
    elif str_helperType == 'halfPush':
	mi_helperJoint.tx = mi_childJoint.tx *.5
	mi_helperJoint.ty = mi_childJoint.ty *.5
	mi_helperJoint.tz = mi_childJoint.tz *.5
	
	mi_helperJoint.__setattr__("t%s"%orientation[1],-(mi_childJoint.tz *.2))
	
	#With half push, our driver is the target joint
	str_driverRot = "%s.r%s"%(mi_targetJoint.mNode,orientation[2])
	str_drivenTransAim = "%s.t%s"%(mi_helperJoint.mNode,orientation[0])
	f_baseTransValue = mi_helperJoint.getAttr("t%s"%(orientation[0]))
	f_sdkTransValue = f_baseTransValue + (f_baseTransValue * .3)	
	mc.setDrivenKeyframe(str_drivenTransAim,
                             currentDriver = str_driverRot,
                             driverValue = 0,value = f_baseTransValue)
	mc.setDrivenKeyframe(str_drivenTransAim,
                             currentDriver = str_driverRot,
                             driverValue = 110,value = f_sdkTransValue)	
	    
    elif str_helperType == 'childRootHold':
	mi_helperJoint.__setattr__("t%s"%orientation[1],(-mi_childJoint.tz *.2))
	mi_helperJoint.parent = mi_targetJoint.parent
	if not mi_posLoc:mi_posLoc = mi_helperJoint.doLoc()#Make sure we have a loc
	mi_posLoc.parent = mi_helperJoint.mNode#Parent loc to i_dup to make sure we're in same space
	
	f_baseUpTransValue = mi_helperJoint.getAttr("t%s"%(orientation[1]))
	f_sdkUpTransValue = mi_childJoint.getAttr("t%s"%(orientation[0])) * -.25
	
	f_baseAimTransValue = mi_helperJoint.getAttr("t%s"%(orientation[0]))
	f_sdkAimTransValue = mi_childJoint.getAttr("t%s"%(orientation[0])) * -.75	
	
	#Move the pos loc for our pose ----------------------------------
	mi_posLoc.__setattr__("t%s"%orientation[0],f_sdkAimTransValue)
	mi_posLoc.__setattr__("t%s"%orientation[1],f_sdkUpTransValue)
	mi_posLoc.parent = mi_helperJoint.parent
	
	#With childRootHold, our driver is the target joint --------------
	str_driverRot = "%s.r%s"%(mi_targetJoint.mNode,orientation[2])
	
	#Up ---------------------------------------------------------------
	str_drivenTransUp = "%s.t%s"%(mi_helperJoint.mNode,orientation[1])
	
	mc.setDrivenKeyframe(str_drivenTransUp,
	                     currentDriver = str_driverRot,
	                     driverValue = 0,value = f_baseUpTransValue)
	mc.setDrivenKeyframe(str_drivenTransUp,
	                     currentDriver = str_driverRot,
	                     driverValue = 150,value = mi_posLoc.getAttr("t%s"%orientation[1]))	

	#Aim ---------------------------------------------------------------
	str_drivenTransAim = "%s.t%s"%(mi_helperJoint.mNode,orientation[0])	
	
	mc.setDrivenKeyframe(str_drivenTransAim,
	                     currentDriver = str_driverRot,
	                     driverValue = 0,value = f_baseAimTransValue)
	mc.setDrivenKeyframe(str_drivenTransAim,
	                     currentDriver = str_driverRot,
	                     driverValue = 150,value = mi_posLoc.getAttr("t%s"%orientation[0]))	
			
	
    if mi_posLoc:mi_posLoc.delete()
    return
    