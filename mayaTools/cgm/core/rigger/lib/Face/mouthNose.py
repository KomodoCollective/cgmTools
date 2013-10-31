"""
------------------------------------------
cgm.core.rigger: Face.mouthNose
Author: Josh Burton
email: jjburton@cgmonks.com

Website : http://www.cgmonks.com
------------------------------------------

mouthNose rig builder
================================================================
"""
__version__ = 0.10112013

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
from cgm.core import cgm_General as cgmGeneral
from cgm.core import cgm_Meta as cgmMeta
from cgm.core import cgm_RigMeta as cgmRigMeta
from cgm.core.rigger.lib import module_Utils as modUtils
from cgm.core.lib import meta_Utils as metaUtils

from cgm.core.classes import SnapFactory as Snap
from cgm.core.classes import NodeFactory as NodeF
from cgm.core.cgmPy import validateArgs as cgmValid
from cgm.core.rigger.lib import joint_Utils as jntUtils
reload(jntUtils)
from cgm.core.rigger import ModuleShapeCaster as mShapeCast
from cgm.core.rigger import ModuleControlFactory as mControlFactory
reload(mControlFactory)
from cgm.core.lib import nameTools
from cgm.core.lib import curve_Utils as crvUtils
from cgm.core.lib import rayCaster as rayCast
from cgm.core.lib import surface_Utils as surfUtils

from cgm.core.rigger.lib import rig_Utils as rUtils

from cgm.lib import (attributes,
                     joints,
                     cgmMath,
                     skinning,
                     lists,
                     dictionary,
                     distance,
                     modules,
                     search,
                     curves,
                     )

#>>> Skeleton
#=========================================================================================================
__l_jointAttrs__ = ['rigJoints','handleJoints']   

def __bindSkeletonSetup__(self):
    """
    TODO: Do I need to connect per joint overrides or will the final group setup get them?
    """
    log.info(">>> %s.__bindSkeletonSetup__ >> "%self._strShortName + "-"*75)            
    try:
	if not self._cgmClass == 'JointFactory.go':
	    log.error("Not a JointFactory.go instance: '%s'"%self)
	    raise StandardError
	
    except Exception,error:
	log.error("mouthNose.__bindSkeletonSetup__>>bad self!")
	raise StandardError,error
    
    #>>> Re parent joints
    #=============================================================  
    #ml_skinJoints = self.rig_getSkinJoints() or []
    if not self._i_module.isSkeletonized():
	raise StandardError, "%s is not skeletonized yet."%self._strShortName
    try:
	self._i_module.rig_getReport()#report	
    except Exception,error:
	log.error("build_mouthNose>>__bindSkeletonSetup__ fail!")
	raise StandardError,error   
    
def build_rigSkeleton(*args, **kws):
    class fncWrap(modUtils.rigStep):
	def __init__(self,*args, **kws):
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName = 'build_rigSkeleton(%s)'%self.d_kws['goInstance']._strShortName	
	    self.__dataBind__()
	    self.l_funcSteps = [{'step':'Gather Info','call':self.gatherInfo},
	                        #{'step':'Rig Joints','call':self.build_rigJoints},
	                        {'step':'Handle Joints','call':self.build_handleJoints},
	                        #{'step':'Connections','call':self.build_connections}
	                        ]	
	    #=================================================================
	
	def gatherInfo(self):
	    mi_go = self._go#Rig Go instance link
	    self.mi_skullPlate = mi_go._mi_skullPlate
	    
	    self.mi_helper = cgmMeta.validateObjArg(mi_go._i_module.getMessage('helper'),noneValid=True)
	    if not self.mi_helper:raise StandardError,"No suitable helper found"
	    
	    for attr in self.mi_helper.getAttrs(userDefined = True):#Get allof our Helpers
		if "Helper" in attr:
		    try:self.__dict__["mi_%s"%attr.replace('Helper','Crv')] = cgmMeta.validateObjArg(self.mi_helper.getMessage(attr),noneValid=False)
		    except Exception,error:raise StandardError, " Failed to find '%s' | %s"%(attr,error)
		
		
	    #>> Find our joint lists ===================================================================
	    self.md_jointList = {}
	    #list of tags we're gonna check to build our joint lists indexed to the k
	    d_jointListBuldTags = {"smileLeft":'left_smileLineJoint',
	                           "smileRight":'right_smileLineJoint',
	                           "uprCheekLeft":'left_uprCheekJoint',
	                           "uprCheekRight":'right_uprCheekJoint',
	                           "cheekLeft":'left_cheekJoint',
	                           "cheekRight":'right_cheekJoint',
	                           "uprLipLeft":'left_lipUprJoint',
	                           "uprLipRight":'right_lipUprJoint',	    
	                           "lwrLipLeft":'left_lipLwrJoint',
	                           "lwrLipRight":'right_lipLwrJoint',	    
	                           "uprLipCenter": 'center_lipUprJoint',
	                           "lwrLipCenter":'center_lipLwrJoint',	                         
	                           "cornerLipLeft":'left_lipCornerJoint',
	                           "cornerLipRight":'right_lipCornerJoint',
	                           "noseBase":'noseBaseJoint',
	                           "jaw":'jawJoint',
	                           "centerJaw":'center_jawLineJoint',	                         
	                           "noseTop":'noseTopJoint',
	                           "noseTip":'noseTipJoint',
	                           "noseUnder":'noseUnderJoint',	                         
	                           "nostrilLeft":'left_nostrilJoint',
	                           "nostrilRight":'right_nostrilJoint',	                         
	                           "tongue":'tongueJoint'}
	    
	    for k in d_jointListBuldTags.iterkeys():
		try:self.md_jointList[k] = cgmMeta.validateObjListArg(mi_go._i_rigNull.msgList_get(d_jointListBuldTags[k]),noneValid = False)
		except Exception,error:raise StandardError,"Failed to find key:'%s'|msgList attr:'%s'|%s"%(k,d_jointListBuldTags[k],error)
	    #Build our handle build info stuff...
	    #TODO make this a contditional build for when we don't use all the joints
	    self.md_handleBuildInfo = {"smile":{"left":{'crv':self.mi_smileLeftCrv,'skinKey':'smileLeft',
	                                                'mi_closeTarget':self.md_jointList['cornerLipLeft'][0]},
	                                        "right":{'crv':self.mi_smileRightCrv,'skinKey':'smileRight',
	                                                 'mi_closeTarget':self.md_jointList['cornerLipRight'][0]},
	                                        "tags":['sneer','smile','smileBase'],'mode':'midSmileLinePoint'},
	                               "uprCheek":{"left":{'crv':self.mi_leftUprCheekCrv,'skinKey':'uprCheekLeft'},
	                                           "right":{'crv':self.mi_rightUprCheekCrv,'skinKey':'uprCheekRight'},
	                                           'mode':'startEnd'},
	                               "centerJaw":{"center":{'skinKey':'centerJaw'},"tags":['chin'],'mode':'zeroDuplicate'},
	                               "lwrLipCenter":{"center":{'skinKey':'lwrLipCenter'},'mode':'simpleDuplicate'},	                               
	                               "uprLipCenter":{"center":{'skinKey':'uprLipCenter'},'mode':'simpleDuplicate'},
	                               "cornerLipLeft":{"center":{'skinKey':'cornerLipLeft'},'mode':'simpleDuplicate'},	
	                               "cornerLipRight":{"center":{'skinKey':'cornerLipRight'},'mode':'simpleDuplicate'},
	                               "nose":{"center":{'skinKey':'noseBase'},'mode':'simpleDuplicate'},	                               	                               
	                               "noseTip":{"center":{'skinKey':'noseTip'},'mode':'simpleDuplicate'},
	                               "noseUnder":{"center":{'skinKey':'noseUnder'},'mode':'simpleDuplicate'},
	                               "nostril":{"left":{'crv':self.mi_noseBaseCastCrv,'skinKey':'nostrilLeft',
	                                                  'minU':.05,'maxU':.4, 'reverse':False},
	                                          "right":{'crv':self.mi_noseBaseCastCrv,'skinKey':'nostrilRight',
	                                                   'minU':.05,'maxU':.4, 'reverse':True},
	                                          'mode':'midSimpleAim',
	                                          'mi_aim':self.md_jointList['noseBase'][0],'v_aim':mi_go._vectorAimNegative,
	                                          'mi_up':self.md_jointList['noseTop'][0],'v_up':mi_go._vectorUp},
	                               "uprLip":{"left":{'crv':self.mi_lipUprCrv,'skinKey':'uprLipLeft',
	                                                 'mi_aimIn':self.md_jointList['uprLipCenter'][0],'v_aimIn':mi_go._vectorOutNegative,
	                                                 'mi_aimOut':self.md_jointList['cornerLipLeft'][0],'v_aimOut':mi_go._vectorOut,	                                                 
	                                                 'minU':0,'maxU':.5, 'reverse':False},
	                                          "right":{'crv':self.mi_lipUprCrv,'skinKey':'uprLipRight',
	                                                   'mi_aimIn':self.md_jointList['uprLipCenter'][0],'v_aimIn':mi_go._vectorOut,
	                                                   'mi_aimOut':self.md_jointList['cornerLipRight'][0],'v_aimOut':mi_go._vectorOutNegative,		                                                   
	                                                   'minU':0,'maxU':.5, 'reverse':True},
	                                          'mode':'midAimBlend',
	                                          'mi_up':self.md_jointList['noseUnder'][0],'v_up':mi_go._vectorUp},
	                               "lwrLip":{"left":{'crv':self.mi_lipLwrCrv,'skinKey':'lwrLipLeft',
	                                                 'mi_aimIn':self.md_jointList['lwrLipCenter'][0],'v_aimIn':mi_go._vectorOutNegative,
	                                                 'mi_aimOut':self.md_jointList['cornerLipLeft'][0],'v_aimOut':mi_go._vectorOut,	                                                 
	                                                 'minU':0,'maxU':.5, 'reverse':False},
	                                          "right":{'crv':self.mi_lipLwrCrv,'skinKey':'lwrLipRight',
	                                                   'mi_aimIn':self.md_jointList['lwrLipCenter'][0],'v_aimIn':mi_go._vectorOut,
	                                                   'mi_aimOut':self.md_jointList['cornerLipRight'][0],'v_aimOut':mi_go._vectorOutNegative,		                                                   
	                                                   'minU':0,'maxU':.5, 'reverse':True},
	                                          'mode':'midAimBlend',
	                                          'mi_up':self.md_jointList['noseUnder'][0],'v_up':mi_go._vectorUp},
	                               "tongue":{"center":{'skinKey':'tongue'},'mode':'startEnd'},
	                               "jaw":{"center":{'skinKey':'jaw'},'mode':'simpleDuplicate'}}	
	
	    	    
	def build_rigJoints(self):
	    #We'll have a rig joint for every joint
	    mi_go = self._go#Rig Go instance link
	    ml_rigJoints = mi_go.build_rigChain()
	    for mJoint in ml_rigJoints:
		if mJoint.parent == mi_go._ml_skinJoints[0].parent:
		    mJoint.parent = False
		mJoint.doName()
		
	    ml_rightRigJoints = metaUtils.get_matchedListFromAttrDict(ml_rigJoints , cgmDirection = 'right')
	    for mJoint in ml_rightRigJoints:
		mJoint.__setattr__("r%s"%mi_go._jointOrientation[1],180)
		jntUtils.freezeJointOrientation(mJoint)
	    self.ml_rigJoints = ml_rigJoints#pass to wrapper
	    
	def build_handleJoints(self):
	    mi_go = self._go#Rig Go instance link	    
	    ml_moduleHandleJoints = []
	    for k_name in self.md_handleBuildInfo.keys():#For each name...
		d_nameBuffer = self.md_handleBuildInfo[k_name]
		for k_direction in ['left','right','center']:#for each direction....
		    try:
			d_buffer = d_nameBuffer.get(k_direction)
			l_tags = d_nameBuffer.get('tags') or False
			str_mode = d_nameBuffer.get('mode') or 'regularMid'
			#if not d_buffer:raise StandardError,"%s %s fail"%(k_name,k_direction)
			if d_buffer:
			    log.info("Building '%s' | '%s' handle joints | mode: %s"%(k_name,k_direction,str_mode))
			    ml_skinJoints = self.md_jointList[d_buffer['skinKey']]
			    ml_handleJoints = []
			    self.l_build = []
			    #Build our copy list -------------------------------------------
			    if str_mode in ['regularMid','midSmileLinePoint']:
				self.l_build = [ml_skinJoints[0],'mid',ml_skinJoints[-1]]		    
			    elif str_mode == 'startEnd':
				self.l_build = [ml_skinJoints[0],ml_skinJoints[-1]]
			    elif str_mode == 'zeroDuplicate':
				self.l_build = [ml_skinJoints[0]]		    
			    else:
				self.l_build = ml_skinJoints
			    #Build ----------------------------------------------------------
			    if str_mode in ['simpleDulplicate','zeroDuplicate']:
				mi_jnt = cgmMeta.cgmObject( mc.duplicate(self.l_build[0].mNode,po=True,ic=True,rc=True)[0],setClass=True )
				mi_jnt.parent = False#Parent to world	
				if l_tags:
				    mi_jnt.addAttr('cgmName',l_tags[0],attrType='string',lock=True)				    				    			    
				mi_jnt.addAttr('cgmTypeModifier','handle',attrType='string',lock=True)
				mi_jnt.doName()
				ml_handleJoints.append(mi_jnt)
			    elif str_mode in ['midSimpleAim','midAimBlend']:
				try:#Get our data...
				    minU = d_buffer['minU']
				    maxU = d_buffer['maxU']
				    b_reverse = d_buffer['reverse']
				    mi_crv = d_buffer['crv']
				    mi_up = d_nameBuffer['mi_up']	
				    v_up = d_nameBuffer['v_up']					
				except Exception,error:raise StandardError,"Failed to get data for simple aim: %s"%error
				try:#Create
				    pos = crvUtils.returnSplitCurveList(mi_crv.mNode, 1, minU = minU, maxU = maxU, reverseCurve = b_reverse, rebuildForSplit=True)[0]				
				    mc.select(cl=True)
				    mi_jnt = cgmMeta.cgmObject( mc.joint(p = pos),setClass=True )
				    mi_jnt.parent = False
				    mi_jnt.addAttr('cgmName',k_name,lock=True)										
				    mi_jnt.addAttr('cgmDirection',k_direction,lock=True)
				    mi_jnt.addAttr('cgmTypeModifier','handle',attrType='string',lock=True)				    
				    mi_jnt.doName()
				    ml_handleJoints.append(mi_jnt)				
				except Exception,error:raise StandardError,"Simple aim build fail: %s"%error
				try:#Orient
				    if str_mode == 'midSimpleAim':
					try:
					    mi_aim = d_nameBuffer['mi_aim']
					    v_aim = d_nameBuffer['v_aim']			
					    mc.delete( mc.aimConstraint(mi_aim.mNode, mi_jnt.mNode,
						                        weight = 1, aimVector = v_aim, upVector = v_up,
						                        worldUpObject = mi_up.mNode, worldUpType = 'object' ) )
					except Exception,error:raise StandardError,"Simple aim fail: %s"%error
				    elif str_mode == 'midAimBlend':
					try:
					    mi_aimIn = d_buffer['mi_aimIn']
					    v_aimIn = d_buffer['v_aimIn']
					    mi_locIn = mi_jnt.doLoc()
					    mi_aimOut = d_buffer['mi_aimOut']
					    v_aimOut = d_buffer['v_aimOut']	
					    mi_locOut = mi_jnt.doLoc()
					    mc.delete( mc.aimConstraint(mi_aimIn.mNode, mi_locIn.mNode,
						                        weight = 1, aimVector = v_aimIn, upVector = v_up,
						                        worldUpObject = mi_up.mNode, worldUpType = 'object' ) )	
					    mc.delete( mc.aimConstraint(mi_aimOut.mNode, mi_locOut.mNode,
						                        weight = 1, aimVector = v_aimOut, upVector = v_up,
						                        worldUpObject = mi_up.mNode, worldUpType = 'object' ) )
					    mc.delete( mc.orientConstraint([mi_locIn.mNode,mi_locOut.mNode], mi_jnt.mNode,
						                           weight = 1) )
					    mc.delete([mi_locIn.mNode,mi_locOut.mNode])
					except Exception,error:raise StandardError,"midAimBlend aim fail: %s"%error
					
				    jntUtils.metaFreezeJointOrientation(mi_jnt)				
				except Exception,error:raise StandardError,"mid fail: %s"%error
			    else:
				for i,mJnt in enumerate(self.l_build):
				    if mJnt == 'mid':
					mi_crv = d_buffer.get('crv')
					if not mi_crv:
					    raise StandardError,"Step: '%s' '%s' | failed to find use curve"%(k_name,k_direction)
					if str_mode == 'midSmileLinePoint':
					    try:
						mi_target = d_buffer['mi_closeTarget']
						#Get initial point to get distance, offset a loc, get new pos
						pos_initial = distance.returnClosestUPosition(mi_target.mNode,mi_crv.mNode)
						f_dist = distance.returnDistanceBetweenPoints(mi_target.getPosition(),pos_initial)
						mi_loc = mi_target.doLoc()
						mi_loc.parent = mi_target
						if k_direction == 'left':
						    mi_loc.__setattr__("t%s"%mi_go._jointOrientation[2],f_dist)
						else:
						    mi_loc.__setattr__("t%s"%mi_go._jointOrientation[2],-f_dist)						
						pos = distance.returnClosestUPosition(mi_loc.mNode,mi_crv.mNode)
						mi_loc.delete()
					    except Exception,error:raise StandardError,"midClosestCurvePoint failed: %s"%error    
					else:
					    pos = crvUtils.getMidPoint(mi_crv)
					mc.select(cl=True)
					mi_jnt = cgmMeta.cgmObject( mc.joint(p = pos),setClass=True )
					mi_jnt.parent = False
					mi_jnt.addAttr('cgmDirection',k_direction,lock=True)
					if l_tags:
					    mi_jnt.addAttr('cgmName',l_tags[1],attrType='string',lock=True)				    				    
					else:
					    mi_jnt.addAttr('cgmName',k_name,lock=True)						
					    mi_jnt.addAttr('cgmNameModifier','mid',attrType='string',lock=True)				    
					mi_jnt.addAttr('cgmTypeModifier','handle',attrType='string',lock=True)				    
					mi_jnt.doName()
					ml_handleJoints.append(mi_jnt)
					
					#Orient
					v_aimVector = mi_go._vectorAim				
					v_upVector = mi_go._vectorUp
					#if k_direction == 'right':
					    #v_upVector = mi_go._vectorUpNegative			
					mc.delete( mc.normalConstraint(self.mi_skullPlate.mNode,mi_jnt.mNode,
					                               weight = 1, aimVector = v_aimVector, upVector = v_upVector, 
					                               ))				
					jntUtils.freezeJointOrientation(mi_jnt)
				    else:
					i_j = cgmMeta.cgmObject( mc.duplicate(mJnt.mNode,po=True,ic=True,rc=True)[0],setClass=True )
					i_j.parent = False#Parent to world				
					i_j.addAttr('cgmTypeModifier','handle',attrType='string',lock=True)
					if len(self.l_build)>1:
					    if l_tags:
						i_j.addAttr('cgmName',l_tags[i],attrType='string',lock=True)					    
					    else:
						if i == 0:
						    i_j.addAttr('cgmNameModifier','start',attrType='string',lock=True)
						else:
						    i_j.addAttr('cgmNameModifier','end',attrType='string',lock=True)
					    
					try:i_j.doRemove('cgmIterator')#Purge the iterator
					except:pass
					i_j.doName()
					ml_handleJoints.append(i_j)			
			    
			    d_buffer['handle'] = ml_handleJoints
			    ml_moduleHandleJoints.extend(ml_handleJoints)
			    
			    ml_rightHandles = metaUtils.get_matchedListFromAttrDict(ml_handleJoints , cgmDirection = 'right')
			    for mJoint in ml_rightHandles:
				log.info("%s flipping"% mJoint.p_nameShort)
				mJoint.__setattr__("r%s"% mi_go._jointOrientation[1],180)
				jntUtils.freezeJointOrientation(mJoint)			
		    except Exception,error:raise StandardError,"%s | %s failed: %s"%(k_name,k_direction,error)    
				
	    mi_go._i_rigNull.msgList_connect(ml_moduleHandleJoints,'handleJoints',"rigNull")
	    self.ml_moduleHandleJoints = ml_moduleHandleJoints
		    
	def build_connections(self):    
	    ml_jointsToConnect = []
	    ml_jointsToConnect.extend(self.ml_rigJoints)    
	    #ml_jointsToConnect.extend(self.ml_moduleHandleJoints)
	    #self._go.connect_toRigGutsVis(ml_jointsToConnect,vis = True)#connect to guts vis switches
	    """
	    for i_jnt in ml_jointsToConnect:
		i_jnt.overrideEnabled = 1		
		cgmMeta.cgmAttr(self._go._i_rigNull.mNode,'gutsVis',lock=False).doConnectOut("%s.%s"%(i_jnt.mNode,'overrideVisibility'))
		cgmMeta.cgmAttr(self._go._i_rigNull.mNode,'gutsLock',lock=False).doConnectOut("%s.%s"%(i_jnt.mNode,'overrideDisplayType'))    
		"""
    return fncWrap(*args, **kws).go()
	
#>>> Shapes
#===================================================================
__d_controlShapes__ = {'shape':['shape_handleCurves','shape_pinCurves']}
def build_shapes(*args, **kws):
    class fncWrap(modUtils.rigStep):
	def __init__(self,*args, **kws):
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName = 'build_shapes(%s)'%self.d_kws['goInstance']._strShortName	
	    self.__dataBind__()
	    self.l_funcSteps = [{'step':'Build Shapes','call':self.buildShapes},
	                        ]	
	    #=================================================================
	
	def buildShapes(self):
	    mi_go = self._go#Rig Go instance link
	    mShapeCast.go(mi_go._i_module,['mouthNose'], storageInstance=mi_go)#This will store controls to a dict called    
	    
    return fncWrap(*args, **kws).go()

#>>> Controls
#===================================================================
def build_controls(*args, **kws):
    class fncWrap(modUtils.rigStep):
	def __init__(self,*args, **kws):
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName = 'build_controls(%s)'%self.d_kws['goInstance']._strShortName	
	    self.__dataBind__()
	    self.l_funcSteps = [{'step':'Gather Info','call':self._gatherInfo_},
	                        {'step':'Settings','call':self._buildSettings_},	                        
	                        {'step':'Direct Controls','call':self._buildControls_},
	                        {'step':'Build Connections','call':self._buildConnections_}	                        
	                        ]	
	    #=================================================================
	
	def _gatherInfo_(self):
	    mi_go = self._go#Rig Go instance link
	    
	    self.mi_helper = cgmMeta.validateObjArg(mi_go._i_module.getMessage('helper'),noneValid=True)
	    if not self.mi_helper:raise StandardError,"No suitable helper found"
	    
	    #>> Find our joint lists ===================================================================
	    ''' We need left and right direction splits for mirror indexing at their color sorting '''
	    self.md_jointLists = {}	    
	    self.ml_handleJoints = mi_go._i_module.rigNull.msgList_get('handleJoints')
	    self.ml_rigJoints = mi_go._i_module.rigNull.msgList_get('rigJoints')
	    
	    l_missingCurves = []
	    for mJnt in self.ml_handleJoints + self.ml_rigJoints:
		if not mJnt.getMessage('controlShape'):l_missingCurves.append(mJnt.p_nameShort)

	    if l_missingCurves:
		log.error("Following joints missing curves: ")
		for obj in l_missingCurves:
		    log.error(">"*5 + " %s"%obj)
		raise StandardError,"Some joints missing controlShape curves"
	    
	    #>> Running lists ===========================================================================
	    self.md_directionControls = {"Left":[],"Right":[],"Centre":[]}
	    self.ml_directControls = []
	    self.ml_controlsAll = []
	    return True
	    	    
	def _buildSettings_(self):
	    mi_go = self._go#Rig Go instance link
	    mi_go.verify_faceSettings()
	    
	    #>>> Verify out vis controls	    
	    self.mPlug_result_moduleFaceSubDriver = mi_go.build_visSubFace()	
	    #self.mPlug_result_moduleFaceSubDriver = self._go.build_visSubFace()	

	def _buildControls_(self):
	    mi_go = self._go#Rig Go instance link
	    
	    ml_rigJoints = self.ml_rigJoints
	    ml_handleJoints = self.ml_handleJoints
		
	    l_strTypeModifiers = ['direct',None]
	    for ii,ml_list in enumerate( [ml_rigJoints,ml_handleJoints] ):
		for i,mObj in enumerate(ml_list):
		    str_mirrorSide = False
		    try:
			mObj.parent = mi_go._i_deformNull
			str_mirrorSide = mi_go.verify_mirrorSideArg(mObj.getAttr('cgmDirection'))#Get the mirror side
			#Register 
			try:
			    d_buffer = mControlFactory.registerControl(mObj, useShape = mObj.getMessage('controlShape'),addPushPull = "t%s"%mi_go._jointOrientation[0],
				                                       mirrorSide = str_mirrorSide, mirrorAxis="translateZ,rotateX,rotateY",		                                           
				                                       makeAimable=False, typeModifier=l_strTypeModifiers[ii]) 	    
			except Exception,error:
			    log.error("mObj: %s"%mObj.p_nameShort)
			    log.error("useShape: %s"%mObj.getMessage('controlShape'))
			    log.error("mirrorSide: %s"%str_mirrorSide)			
			    raise StandardError,"Register fail : %s"%error
			
			#Vis sub connect
			if ii == 0:
			    self.mPlug_result_moduleFaceSubDriver.doConnectOut("%s.visibility"%mObj.mNode)
			
			#
			mc.delete(mObj.getMessage('controlShape'))
			mObj.doRemove('controlShape')
			self.md_directionControls[str_mirrorSide].append(mObj)
			
			#i_obj.drawStyle = 6#Stick joint draw style
			cgmMeta.cgmAttr(mObj,'radius',value=.01, hidden=True)
			self.ml_directControls.append(mObj)
			
		    except Exception, error:
			raise StandardError,"Iterative fail item: %s | obj: %s | mirror side: %s | error: %s"%(i,mObj.p_nameShort,str_mirrorSide,error)
		    
	    self._go._i_rigNull.msgList_connect(self.ml_directControls ,'controlsDirect', 'rigNull')	    
	    self.ml_controlsAll.extend(self.ml_directControls)#append	
	    
	def _buildConnections_(self):
	    #Register our mirror indices ---------------------------------------------------------------------------------------
	    mi_go = self._go#Rig Go instance link	    
	    for str_direction in self.md_directionControls.keys():
		int_start = self._go._i_puppet.get_nextMirrorIndex( self._go._str_mirrorDirection )
		for i,mCtrl in enumerate(self.md_directionControls[str_direction]):
		    try:
			mCtrl.addAttr('mirrorIndex', value = (int_start + i))		
		    except Exception,error: raise StandardError,"Failed to register mirror index | mCtrl: %s | %s"%(mCtrl,error)

	    try:self._go._i_rigNull.msgList_connect(self.ml_controlsAll,'controlsAll')
	    except Exception,error: raise StandardError,"Controls all connect| %s"%error	    
	    try:self._go._i_rigNull.moduleSet.extend(self.ml_controlsAll)
	    except Exception,error: raise StandardError,"Failed to set module objectSet | %s"%error
	    
    return fncWrap(*args, **kws).go()
	    

def build_rig(*args, **kws):
    class fncWrap(modUtils.rigStep):
	def __init__(self,*args, **kws):
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName = 'build_rig(%s)'%self.d_kws['goInstance']._strShortName	
	    self.__dataBind__()
	    self.l_funcSteps = [{'step':'Gather Info','call':self._gatherInfo_},
	                        {'step':'Special Locs','call':self._buildSpecialLocs_},	                        
	                        {'step':'Rig Brows','call':self._buildBrows_},
	                        {'step':'Rig Upr Cheek','call':self._buildUprCheek_},
	                        {'step':'Rig Temple','call':self._buildTemple_},
	                        {'step':'Attach Squash','call':self._attachSquash_},
	                        {'step':'Lock N hide','call':self._lockNHide_},
	                        
	                        ]	
	    #=================================================================
	
	def _gatherInfo_(self):
	    mi_go = self._go#Rig Go instance link
	    
	    self.mi_helper = cgmMeta.validateObjArg(mi_go._i_module.getMessage('helper'),noneValid=True)
	    if not self.mi_helper:raise StandardError,"No suitable helper found"
	    
	    self.mi_skullPlate = mi_go._mi_skullPlate
	    mi_go._i_rigNull.connectChildNode(self.mi_skullPlate,'skullPlate')#Connect it
	    self.str_skullPlate = self.mi_skullPlate.mNode
	    
	    self.mi_jawPlate = cgmMeta.validateObjArg(self.mi_helper.getMessage('jawPlate'),noneValid=True)
	    
	    #>> Get our lists ==========================================================================
	    '''
	    We need lists of handle and a rig joints for each segment - brow, upr cheek temple
	    md_joints = {'leftBrow:{'ml_handleJoints':[],'ml_rigJoints':[],'mi_crv'}}
	    '''
	    ml_handleJoints = mi_go._i_module.rigNull.msgList_get('handleJoints')
	    ml_rigJoints = mi_go._i_module.rigNull.msgList_get('rigJoints')
	    self.md_rigList = {"brow":{"left":{},"right":{},"center":{}},
	                       "uprCheek":{"left":{},"right":{}},
	                       "squash":{},
	                       "temple":{"left":{},"right":{}}}
	    
	    self.ml_rigJoints = ml_rigJoints
	    self.ml_handlesJoints = ml_handleJoints
	    #>> Brow --------------------------------------------------------------------------------------------------
	    self.md_rigList['brow']['left']['ml_handles'] = metaUtils.get_matchedListFromAttrDict(ml_handleJoints,
	                                                                                          cgmDirection = 'left',
	                                                                                          cgmName = 'brow')
	    self.md_rigList['brow']['right']['ml_handles'] = metaUtils.get_matchedListFromAttrDict(ml_handleJoints,
	                                                                                           cgmDirection = 'right',
	                                                                                           cgmName = 'brow') 
	    self.md_rigList['brow']['center']['ml_handles'] = metaUtils.get_matchedListFromAttrDict(ml_handleJoints,
	                                                                                           cgmDirection = 'center',
	                                                                                           cgmName = 'brow') 
	    self.md_rigList['brow']['left']['ml_rigJoints'] = metaUtils.get_matchedListFromAttrDict(ml_rigJoints,
	                                                                                            cgmDirection = 'left',
	                                                                                            cgmName = 'brow')
	    self.md_rigList['brow']['right']['ml_rigJoints'] = metaUtils.get_matchedListFromAttrDict(ml_rigJoints,
	                                                                                             cgmDirection = 'right',
	                                                                                             cgmName = 'brow') 
	    self.md_rigList['brow']['center']['ml_rigJoints'] = metaUtils.get_matchedListFromAttrDict(ml_rigJoints,
	                                                                                              cgmDirection = 'center',
	                                                                                              cgmName = 'brow') 	    
	    if not self.md_rigList['brow']['left'].get('ml_handles'):raise StandardError,"Failed to find left brow handle joints"
	    if not self.md_rigList['brow']['right'].get('ml_handles'):raise StandardError,"Failed to find right brow handle joints"
	    if not self.md_rigList['brow']['center'].get('ml_handles'):raise StandardError,"Failed to find center brow handle joints"
	    
	    #>> Cheek --------------------------------------------------------------------------------------------------
	    self.md_rigList['uprCheek']['left']['ml_handles'] = metaUtils.get_matchedListFromAttrDict(ml_handleJoints,
	                                                                                              cgmDirection = 'left',
	                                                                                              cgmName = 'uprCheek')
	    self.md_rigList['uprCheek']['right']['ml_handles'] = metaUtils.get_matchedListFromAttrDict(ml_handleJoints,
	                                                                                               cgmDirection = 'right',
	                                                                                               cgmName = 'uprCheek') 		    
	    self.md_rigList['uprCheek']['left']['ml_rigJoints'] = metaUtils.get_matchedListFromAttrDict(ml_rigJoints,
	                                                                                                cgmDirection = 'left',
	                                                                                                cgmName = 'uprCheek')
	    self.md_rigList['uprCheek']['right']['ml_rigJoints'] = metaUtils.get_matchedListFromAttrDict(ml_rigJoints,
	                                                                                                 cgmDirection = 'right',
	                                                                                                 cgmName = 'uprCheek') 	    
	    #>> Temple --------------------------------------------------------------------------------------------------
	    self.md_rigList['temple']['left']['ml_handles'] = metaUtils.get_matchedListFromAttrDict(ml_handleJoints,
	                                                                                              cgmDirection = 'left',
	                                                                                              cgmName = 'temple')
	    self.md_rigList['temple']['right']['ml_handles'] = metaUtils.get_matchedListFromAttrDict(ml_handleJoints,
	                                                                                               cgmDirection = 'right',
	                                                                                               cgmName = 'temple') 	
	    
	    self.md_rigList['temple']['left']['ml_rigJoints'] = metaUtils.get_matchedListFromAttrDict(ml_rigJoints,
	                                                                                                cgmDirection = 'left',
	                                                                                                cgmName = 'temple')
	    self.md_rigList['temple']['right']['ml_rigJoints'] = metaUtils.get_matchedListFromAttrDict(ml_rigJoints,
	                                                                                                 cgmDirection = 'right',
	                                                                                                 cgmName = 'temple') 	 	    
	    #>> Squash --------------------------------------------------------------------------------------------------
	    self.md_rigList['squash']['ml_rigJoints'] = metaUtils.get_matchedListFromAttrDict(ml_rigJoints,
	                                                                                      cgmNameModifier = 'squash')
	    
	    self.mi_squashCastHelper = cgmMeta.validateObjArg(self.mi_helper.getMessage('squashCastHelper'),noneValid=True)	    

	    #>> Calculate ==========================================================================
	    self.f_offsetOfUpLoc = distance.returnDistanceBetweenObjects(self.md_rigList['brow']['left']['ml_rigJoints'][0].mNode,
	                                                                 self.md_rigList['brow']['left']['ml_rigJoints'][-1].mNode)
	    
	    #>> Running lists ==========================================================================
	    self.ml_toVisConnect = []
	    self.ml_curves = []
	    self.md_attachReturns = {}
	    
	    return True
	
	def _buildSpecialLocs_(self):
	    #>> Need to build some up locs =======================================================================================
	    mi_go = self._go#Rig Go instance link
	    """
	    str_cast = mi_go._jointOrientation[1]+"+"
	    d_return = rayCast.findMeshIntersectionFromObjectAxis(self.mi_skullPlate.mNode,self.mi_squashCastHelper.mNode,str_cast)
	    log.info(d_return)
	    pos = d_return.get('hit')
	    if not pos:
		log.warning("rayCast.findMeshIntersectionFromObjectAxis(%s,%s,%s)"%(self.l_targetMesh[0],self.mi_squashCastHelper.mNode,str_cast))
		raise StandardError, "Failed to find hit." 
		"""
	    try:#Brow up loc
		str_skullPlate = self.str_skullPlate
		d_section = self.md_rigList['brow']		
		#Some measurements
		#From the outer brow to outer brow
		f_distBrowToBrow = distance.returnDistanceBetweenObjects(d_section['left']['ml_rigJoints'][-1].mNode,
		                                                         d_section['right']['ml_rigJoints'][-1].mNode)		
		mi_browUpLoc = self.mi_helper.doLoc()
		#mi_browUpLoc.parent = False
		str_grp = mi_browUpLoc.doGroup()
		mi_browUpLoc.__setattr__("t%s"%mi_go._jointOrientation[0],-f_distBrowToBrow/2)
		mi_browUpLoc.__setattr__("t%s"%mi_go._jointOrientation[1],f_distBrowToBrow/2)
		mi_browUpLoc.addAttr('cgmTypeModifier','moduleUp',lock = True)
		mi_browUpLoc.doName()
		
		#mi_browUpLoc.parent = mi_go._i_rigNull#parent to rigNull
		self.mi_browUpLoc = mi_browUpLoc #Link
		try:
		    d_return = surfUtils.attachObjToSurface(objToAttach = mi_browUpLoc.mNode,
			                                    targetSurface = str_skullPlate,
			                                    createControlLoc = False,
			                                    createUpLoc = False,	
		                                            parentToFollowGroup = True,		                                            
			                                    orientation = mi_go._jointOrientation)
		except Exception,error:raise StandardError,"Failed to attach. | error : %s"%(error)
		self.md_attachReturns[mi_browUpLoc] = d_return		
		mc.delete(str_grp)
		
	    except Exception,error:raise StandardError,"Brow up setup. | error : %s"%(error)

	def _buildBrows_(self):
	    try:#>> Attach brow rig joints =======================================================================================
		mi_go = self._go#Rig Go instance link
		str_skullPlate = self.str_skullPlate
		d_section = self.md_rigList['brow']
		ml_rigJoints = d_section['center']['ml_rigJoints'] + d_section['left']['ml_rigJoints'] + d_section['right']['ml_rigJoints']
		ml_handles = d_section['center']['ml_handles'] + d_section['left']['ml_handles'] + d_section['right']['ml_handles']
		str_centerBrowRigJoint = d_section['center']['ml_rigJoints'][0].mNode
		f_offsetOfUpLoc = distance.returnDistanceBetweenObjects(d_section['left']['ml_rigJoints'][0].mNode,
		                                                        d_section['left']['ml_rigJoints'][-1].mNode)
		for mObj in ml_rigJoints:
		    try:
			try:#>> Attach ------------------------------------------------------------------------------------------
			    d_return = surfUtils.attachObjToSurface(objToAttach = mObj.getMessage('masterGroup')[0],
				                                    targetSurface = str_skullPlate,
				                                    createControlLoc = True,
				                                    createUpLoc = True,
				                                    f_offset = f_offsetOfUpLoc,
				                                    orientation = mi_go._jointOrientation)
			except Exception,error:raise StandardError,"Failed to attach. | error : %s"%(error)
			try:#>> Setup curve locs ------------------------------------------------------------------------------------------
			    mi_controlLoc = d_return['controlLoc']
			    mi_crvLoc = mi_controlLoc.doDuplicate(parentOnly=False)
			    mi_crvLoc.addAttr('cgmTypeModifier','crvAttach',lock=True)
			    mi_crvLoc.doName()
			    mi_crvLoc.parent = mi_go._i_rigNull#parent to rigNull
			    d_return['crvLoc'] = mi_crvLoc #Add the curve loc
			except Exception,error:raise StandardError,"Loc setup. | error : %s"%(error)
    
			self.md_attachReturns[mObj] = d_return
		    except Exception,error:
			raise StandardError,"Attach rig joint loop. obj: %s | error : %s"%(mObj.p_nameShort,error)	    
		    
		for mObj in ml_handles:
		    try:
			try:#>> Attach ------------------------------------------------------------------------------------------
			    d_return = surfUtils.attachObjToSurface(objToAttach = mObj.getMessage('masterGroup')[0],
				                                    targetSurface = str_skullPlate,
				                                    createControlLoc = False,
				                                    createUpLoc = True,	
			                                            parentToFollowGroup = False,
				                                    orientation = mi_go._jointOrientation)
			except Exception,error:raise StandardError,"Failed to attach. | error : %s"%(error)
			self.md_attachReturns[mObj] = d_return
		    except Exception,error:
			raise StandardError,"Attach handle. obj: %s | error : %s"%(mObj.p_nameShort,error)	  
	    except Exception,error:
		raise StandardError,"Attach | %s"%(mObj.p_nameShort,error)
	    
	    try:#>> Center Brow =======================================================================================
		ml_handles = d_section['center']['ml_handles']
		ml_rigJoints = d_section['center']['ml_rigJoints'] 
		mi_centerHandle = ml_handles[0]
		mi_centerRigJoint = ml_rigJoints[0]
		
		try:#Connect the control loc to the center handle
		    mi_controlLoc = self.md_attachReturns[ml_rigJoints[0]]['controlLoc']
		    mc.pointConstraint(mi_centerHandle.mNode,mi_controlLoc.mNode)
		    #cgmMeta.cgmAttr(mi_controlLoc,"translate").doConnectIn("%s.translate"%mi_centerHandle.mNode)
		except Exception,error:raise StandardError,"Control loc connect | error: %s"%(error)			
		    
		try:#Setup the offset group which will take half the left/right handles
		    #Create offsetgroup for the mid
		    mi_offsetGroup = cgmMeta.cgmObject( mi_centerHandle.doGroup(True),setClass=True)	 
		    mi_offsetGroup.doStore('cgmName',mi_centerHandle.mNode)
		    mi_offsetGroup.addAttr('cgmTypeModifier','offset',lock=True)
		    mi_offsetGroup.doName()
		    mi_centerHandle.connectChildNode(mi_offsetGroup,'offsetGroup','groupChild')		    
		    
		    arg = "%s.ty = %s.ty >< %s.ty"%(mi_offsetGroup.p_nameShort,
		                                    self.md_rigList['brow']['left']['ml_handles'][0].p_nameShort,
		                                    self.md_rigList['brow']['right']['ml_handles'][0].p_nameShort,
		                                    )
		    NodeF.argsToNodes(arg).doBuild()
		except Exception,error:raise StandardError,"Offset group | error: %s"%(error)			
		try:#Create the brow up loc and parent it to the 
		    mi_browFrontUpLoc = mi_offsetGroup.doLoc()
		    mi_browFrontUpLoc.parent = mi_offsetGroup.parent
		    mi_browFrontUpLoc.tz = f_offsetOfUpLoc
		    self.mi_browFrontUpLoc = mi_browFrontUpLoc
		except Exception,error:raise StandardError,"Offset group | error: %s"%(error)			
		
	    except Exception,error:
		raise StandardError,"Center Brow | %s"%(error)
	    
	    #>> Left and Right =======================================================================================
	    for i,d_browSide in enumerate([self.md_rigList['brow']['left'],self.md_rigList['brow']['right']] ):
		ml_handles = d_browSide['ml_handles']
		ml_rigJoints = d_browSide['ml_rigJoints']
		"""
		log.info("%s Handles >>>>"%self._str_reportStart)
		for mObj in ml_handles:
		    log.info(">>> %s "%mObj.p_nameShort)
		log.info("%s Rig Joints >>>>"%self._str_reportStart)
		for mObj in ml_rigJoints:
		    log.info(">>> %s "%mObj.p_nameShort)
		    """
		if len(ml_handles) != 3:
		    raise StandardError,"Only know how to rig a 3 handle brow segment. step: %s"%(i) 	
		
		str_side = ml_rigJoints[0].cgmDirection
		v_up = mi_go._vectorAim
		if str_side == 'left':
		    v_aim = mi_go._vectorOut
		else:
		    v_aim = mi_go._vectorOutNegative
		    
		try:#Create our curves ------------------------------------------------------------------------------------
		    str_crv = mc.curve(d=1,ep=[mObj.getPosition() for mObj in ml_rigJoints],os =True)
		    mi_crv = cgmMeta.cgmObject(str_crv,setClass=True)
		    mi_crv.doCopyNameTagsFromObject(ml_rigJoints[0].mNode,ignore=['cgmIterator','cgmTypeModifier','cgmType'])
		    mi_crv.addAttr('cgmTypeModifier','driver',lock=True)
		    mi_crv.doName()
		    mi_crv.parent = mi_go._i_rigNull#parent to rigNull
		    self.ml_toVisConnect.append(mi_crv)	
		    d_browSide['mi_crv'] = mi_crv
		except Exception,error:raise StandardError,"Failed to build crv. step: %s | error : %s"%(i,error) 
		
		try:# Setup rig joints ------------------------------------------------------------------------------------
		    int_lastIndex = len(ml_rigJoints) - 1
		    for obj_idx,mObj in enumerate( ml_rigJoints ):
			d_current = self.md_attachReturns[mObj]
			try:
			    try:#>> Attach  loc to curve --------------------------------------------------------------------------------------
				mi_crvLoc = d_current['crvLoc']
				mi_controlLoc = d_current['controlLoc']
				crvUtils.attachObjToCurve(mi_crvLoc.mNode,mi_crv.mNode)
				mc.pointConstraint(mi_crvLoc.mNode,mi_controlLoc.mNode,maintainOffset = True)
				
			    except Exception,error:raise StandardError,"Failed to attach to crv. | error : %s"%(error)
			    try:#>> Aim the offset group  ------------------------------------------------------------------------------------------
				if obj_idx != int_lastIndex:
				    str_upLoc = d_current['upLoc'].mNode
				    str_offsetGroup = d_current['offsetGroup'].mNode				    
				    if obj_idx == 0:
					#If it's the interior brow, we need to aim forward and back on the chain
					#We need to make a couple of locs
					d_tomake = {'aimIn':{'target':str_centerBrowRigJoint,
					                     'aimVector':cgmMath.multiplyLists([v_aim,[-1,-1,-1]])},
					            'aimOut':{'target':ml_rigJoints[1].mNode,
					                      'aimVector':v_aim}}
					for d in d_tomake.keys():
					    d_sub = d_tomake[d]
					    str_target = d_sub['target']
					    mi_loc = mObj.doLoc()
					    mi_loc.addAttr('cgmTypeModifier',d,lock=True)
					    mi_loc.doName()
					    mi_loc.parent = d_current['zeroGroup']
					    d_sub['aimLoc'] = mi_loc
					    v_aimVector = d_sub['aimVector']
					    if str_side == 'right':
						v_aimVector = cgmMath.multiplyLists([v_aimVector,[-1,-1,-1]])
					    mc.aimConstraint(str_target,mi_loc.mNode,
					                     maintainOffset = True,
					                     weight = 1,
					                     aimVector = v_aimVector, upVector = v_up,
					                     worldUpVector = [0,1,0], worldUpObject = str_upLoc, worldUpType = 'object' )
					mc.orientConstraint([d_tomake['aimIn']['aimLoc'].mNode, d_tomake['aimOut']['aimLoc'].mNode],str_offsetGroup,maintainOffset = True)					
				    else:
					ml_targets = [ml_rigJoints[obj_idx+1]]	
					mc.aimConstraint([o.mNode for o in ml_targets],str_offsetGroup,
					                 maintainOffset = True, weight = 1, aimVector = v_aim, upVector = v_up, worldUpVector = [0,1,0], worldUpObject = str_upLoc, worldUpType = 'object' )				    
			    except Exception,error:raise StandardError,"Loc setup. | error : %s"%(error)
	
			    self.md_attachReturns[mObj] = d_current#push back
			except Exception,error:
			    raise StandardError,"Rig joint setup fail. obj: %s | error : %s"%(mObj.p_nameShort,error)	    
		except Exception,error:raise StandardError,"Rig joint setup fail. step: %s | error : %s"%(i,error) 
		
		try:#Skin -------------------------------------------------------------------------------------------------
		    mi_skinNode = cgmMeta.cgmNode(mc.skinCluster ([mObj.mNode for mObj in ml_handles],
		                                                  mi_crv.mNode,
		                                                  tsb=True,
		                                                  maximumInfluences = 3,
		                                                  normalizeWeights = 1,dropoffRate=2.5)[0])
		    mi_skinNode.doCopyNameTagsFromObject(mi_crv.mNode,ignore=['cgmType'])
		    mi_skinNode.doName()
		    d_browSide['mi_skinNode'] = mi_skinNode
		except Exception,error:raise StandardError,"Failed to skinCluster crv. step: %s | error : %s"%(i,error) 
		
		try:#Setup mid --------------------------------------------------------------------------------------------
		    d_firstRigJoint = self.md_attachReturns[ml_rigJoints[0]]
		    d_firstHandle = self.md_attachReturns[ml_handles[0]]		    
		    self.d_buffer = d_firstRigJoint	    
		    mi_midHandle = ml_handles[1]
		    str_upLoc = self.mi_browUpLoc .mNode
		    
		    #Create offsetgroup for the mid
		    mi_offsetGroup = cgmMeta.cgmObject( mi_midHandle.doGroup(True),setClass=True)	 
		    mi_offsetGroup.doStore('cgmName',mi_midHandle.mNode)
		    mi_offsetGroup.addAttr('cgmTypeModifier','offset',lock=True)
		    mi_offsetGroup.doName()
		    mi_midHandle.connectChildNode(mi_offsetGroup,'offsetGroup','groupChild')
		    mc.parentConstraint([ml_handles[0].mNode,ml_handles[-1].mNode], mi_offsetGroup.mNode,maintainOffset = True)
		    
		    #Create offsetgroup for the mid
		    mi_aimGroup = cgmMeta.cgmObject( mi_midHandle.doGroup(True),setClass=True)	 
		    mi_aimGroup.doStore('cgmName',mi_midHandle.mNode)
		    mi_aimGroup.addAttr('cgmTypeModifier','aim',lock=True)
		    mi_midHandle.connectChildNode(mi_aimGroup,'aimGroup','groupChild')		    
		    mi_aimGroup.doName()
		    
		    if str_side == 'left':
			v_aim = mi_go._vectorOutNegative
		    else:
			v_aim = mi_go._vectorOut
			
		    mc.aimConstraint(ml_handles[0].mNode, mi_aimGroup.mNode,
		                     maintainOffset = True, weight = 1, aimVector = v_aim, upVector = v_up, worldUpVector = [0,1,0], worldUpObject = str_upLoc, worldUpType = 'object' )
				     
		except Exception,error:raise StandardError,"Mid failed. step: %s | error : %s"%(i,error) 		
		    
	    return True
	
	def _buildUprCheek_(self):
	    try:#>> Attach uprCheek rig joints =======================================================================================
		mi_go = self._go#Rig Go instance link
		str_skullPlate = self.str_skullPlate
		d_section = self.md_rigList['uprCheek']
		ml_rigJoints = d_section['left']['ml_rigJoints'] + d_section['right']['ml_rigJoints']
		ml_handles = d_section['left']['ml_handles'] + d_section['right']['ml_handles']
		f_offsetOfUpLoc = self.f_offsetOfUpLoc
		
		for mObj in ml_rigJoints:
		    try:
			try:#>> Attach ------------------------------------------------------------------------------------------
			    d_return = surfUtils.attachObjToSurface(objToAttach = mObj.getMessage('masterGroup')[0],
				                                    targetSurface = str_skullPlate,
				                                    createControlLoc = True,
				                                    createUpLoc = True,
				                                    f_offset = f_offsetOfUpLoc,
				                                    orientation = mi_go._jointOrientation)
			except Exception,error:raise StandardError,"Failed to attach. | error : %s"%(error)
			try:#>> Setup curve locs ------------------------------------------------------------------------------------------
			    mi_controlLoc = d_return['controlLoc']
			    mi_crvLoc = mi_controlLoc.doDuplicate(parentOnly=False)
			    mi_crvLoc.addAttr('cgmTypeModifier','crvAttach',lock=True)
			    mi_crvLoc.doName()
			    mi_crvLoc.parent = mi_go._i_rigNull#parent to rigNull
			    d_return['crvLoc'] = mi_crvLoc #Add the curve loc
			except Exception,error:raise StandardError,"Loc setup. | error : %s"%(error)
    
			self.md_attachReturns[mObj] = d_return
		    except Exception,error:
			raise StandardError,"Attach rig joint loop. obj: %s | error : %s"%(mObj.p_nameShort,error)	    
		    
		for mObj in ml_handles:
		    try:
			try:#>> Attach ------------------------------------------------------------------------------------------
			    d_return = surfUtils.attachObjToSurface(objToAttach = mObj.getMessage('masterGroup')[0],
				                                    targetSurface = str_skullPlate,
				                                    createControlLoc = False,
				                                    createUpLoc = True,	
			                                            parentToFollowGroup = False,
				                                    orientation = mi_go._jointOrientation)
			except Exception,error:raise StandardError,"Failed to attach. | error : %s"%(error)
			self.md_attachReturns[mObj] = d_return
		    except Exception,error:
			raise StandardError,"Attach handle. obj: %s | error : %s"%(mObj.p_nameShort,error)	  
	    except Exception,error:
		raise StandardError,"Attach | %s"%(error)
	    	    
	    #>> Left and Right =======================================================================================
	    for i,d_uprCheekSide in enumerate([self.md_rigList['uprCheek']['left'],self.md_rigList['uprCheek']['right']] ):
		ml_handles = d_uprCheekSide['ml_handles']
		ml_rigJoints = d_uprCheekSide['ml_rigJoints']

		if len(ml_handles) != 2:
		    raise StandardError,"Only know how to rig a 2 handle uprCheek segment. step: %s"%(i) 	
		
		str_side = ml_rigJoints[0].cgmDirection
		v_up = mi_go._vectorAim
		if str_side == 'left':
		    v_aim = mi_go._vectorOut
		else:
		    v_aim = mi_go._vectorOutNegative
		    
		try:#Create our curves ------------------------------------------------------------------------------------
		    str_crv = mc.curve(d=1,ep=[mObj.getPosition() for mObj in ml_rigJoints],os =True)
		    mi_crv = cgmMeta.cgmObject(str_crv,setClass=True)
		    mi_crv.doCopyNameTagsFromObject(ml_rigJoints[0].mNode,ignore=['cgmIterator','cgmTypeModifier','cgmType'])
		    mi_crv.addAttr('cgmTypeModifier','driver',lock=True)
		    mi_crv.doName()
		    mi_crv.parent = mi_go._i_rigNull#parent to rigNull
		    self.ml_toVisConnect.append(mi_crv)	
		    d_uprCheekSide['mi_crv'] = mi_crv
		except Exception,error:raise StandardError,"Failed to build crv. step: %s | error : %s"%(i,error) 
		
		try:# Setup rig joints ------------------------------------------------------------------------------------
		    int_lastIndex = len(ml_rigJoints) - 1
		    for obj_idx,mObj in enumerate( ml_rigJoints ):
			d_current = self.md_attachReturns[mObj]
			try:
			    try:#>> Attach  loc to curve --------------------------------------------------------------------------------------
				mi_crvLoc = d_current['crvLoc']
				mi_controlLoc = d_current['controlLoc']
				crvUtils.attachObjToCurve(mi_crvLoc.mNode,mi_crv.mNode)
				mc.pointConstraint(mi_crvLoc.mNode,mi_controlLoc.mNode,maintainOffset = True)
				
			    except Exception,error:raise StandardError,"Failed to attach to crv. | error : %s"%(error)
			    try:#>> Aim the offset group  ------------------------------------------------------------------------------------------
				if obj_idx != int_lastIndex:
				    str_upLoc = d_current['upLoc'].mNode
				    str_offsetGroup = d_current['offsetGroup'].mNode				    
				    ml_targets = [ml_rigJoints[obj_idx+1]]	
				    mc.aimConstraint([o.mNode for o in ml_targets],str_offsetGroup,
				                     maintainOffset = True, weight = 1, aimVector = v_aim, upVector = v_up, worldUpVector = [0,1,0], worldUpObject = str_upLoc, worldUpType = 'object' )				    
			    except Exception,error:raise StandardError,"Loc setup. | error : %s"%(error)
	
			    self.md_attachReturns[mObj] = d_current#push back
			except Exception,error:
			    raise StandardError,"Rig joint setup fail. obj: %s | error : %s"%(mObj.p_nameShort,error)	    
		except Exception,error:raise StandardError,"Rig joint setup fail. step: %s | error : %s"%(i,error) 
		
		try:#Skin -------------------------------------------------------------------------------------------------
		    mi_skinNode = cgmMeta.cgmNode(mc.skinCluster ([mObj.mNode for mObj in ml_handles],
		                                                  mi_crv.mNode,
		                                                  tsb=True,
		                                                  maximumInfluences = 3,
		                                                  normalizeWeights = 1,dropoffRate=2.5)[0])
		    mi_skinNode.doCopyNameTagsFromObject(mi_crv.mNode,ignore=['cgmType'])
		    mi_skinNode.doName()
		    d_uprCheekSide['mi_skinNode'] = mi_skinNode
		except Exception,error:raise StandardError,"Failed to skinCluster crv. step: %s | error : %s"%(i,error) 
		    
	    return True
	    
	def _attachSquash_(self):
	    mi_go = self._go#Rig Go instance link
	    str_skullPlate = self.str_skullPlate
	    d_section = self.md_rigList['squash']
	    ml_rigJoints = d_section['ml_rigJoints']	
	    for mObj in ml_rigJoints:
		try:
		    try:#>> Attach ------------------------------------------------------------------------------------------
			d_return = surfUtils.attachObjToSurface(objToAttach = mObj.getMessage('masterGroup')[0],
		                                                targetSurface = str_skullPlate,
		                                                createControlLoc = False,
		                                                createUpLoc = False,
		                                                orientation = mi_go._jointOrientation)
		    except Exception,error:raise StandardError,"Failed to attach. | error : %s"%(error)
		    self.md_attachReturns[mObj] = d_return
		except Exception,error:
		    raise StandardError,"Attach rig joint loop. obj: %s | error : %s"%(mObj.p_nameShort,error)	
		
	    return True
		
	def _buildTemple_(self):
	    try:#>> Attach temple rig joints =======================================================================================
		mi_go = self._go#Rig Go instance link
		str_skullPlate = self.str_skullPlate
		d_section = self.md_rigList['temple']
		ml_rigJoints = d_section['left']['ml_rigJoints'] + d_section['right']['ml_rigJoints']
		ml_handles = d_section['left']['ml_handles'] + d_section['right']['ml_handles']
    
		for mObj in ml_rigJoints:
		    try:
			try:#>> Attach ------------------------------------------------------------------------------------------
			    d_return = surfUtils.attachObjToSurface(objToAttach = mObj.getMessage('masterGroup')[0],
				                                    targetSurface = str_skullPlate,
				                                    createControlLoc = True,
				                                    createUpLoc = True,
				                                    f_offset = self.f_offsetOfUpLoc,
				                                    orientation = mi_go._jointOrientation)
			except Exception,error:raise StandardError,"Failed to attach. | error : %s"%(error)
			self.md_attachReturns[mObj] = d_return
		    except Exception,error:
			raise StandardError,"Attach rig joint loop. obj: %s | error : %s"%(mObj.p_nameShort,error)	    
		    
		for mObj in ml_handles:
		    try:
			try:#>> Attach ------------------------------------------------------------------------------------------
			    d_return = surfUtils.attachObjToSurface(objToAttach = mObj.getMessage('masterGroup')[0],
				                                    targetSurface = str_skullPlate,
				                                    createControlLoc = False,
				                                    createUpLoc = True,	
				                                    parentToFollowGroup = False,
				                                    orientation = mi_go._jointOrientation)
			except Exception,error:raise StandardError,"Failed to attach. | error : %s"%(error)
			self.md_attachReturns[mObj] = d_return
		    except Exception,error:
			raise StandardError,"Attach handle. obj: %s | error : %s"%(mObj.p_nameShort,error)	  
	    except Exception,error:
		raise StandardError,"Attach | %s"%(error)		
	    
	    try:#>> Setup handle =======================================================================================
		for i,mObj in enumerate(ml_handles):
		    try:#Connect the control loc to the center handle
			mi_controlLoc = self.md_attachReturns[ml_rigJoints[i]]['controlLoc']
			mc.pointConstraint(mObj.mNode,mi_controlLoc.mNode,maintainOffset = True)
			#cgmMeta.cgmAttr(mi_controlLoc,"translate").doConnectIn("%s.translate"%mi_centerHandle.mNode)
		    except Exception,error:raise StandardError,"Control loc connect | error: %s"%(error)			
				
	    except Exception,error:
		raise StandardError,"Setup handle | %s"%(error)
	
	def _lockNHide_(self):
	    #Lock and hide all 
	    for mHandle in self.ml_handlesJoints:
		cgmMeta.cgmAttr(mHandle,'scale',lock = True, hidden = True)
		cgmMeta.cgmAttr(mHandle,'v',lock = True, hidden = True)		
		mHandle._setControlGroupLocks()	
		
	    for mJoint in self.ml_rigJoints:
		mJoint._setControlGroupLocks()	
		cgmMeta.cgmAttr(mJoint,'v',lock = True, hidden = True)		

	    mi_go = self._go#Rig Go instance link
	    try:#parent folicles to rignull
		for k in self.md_attachReturns.keys():# we wanna parent 
		    d_buffer = self.md_attachReturns[k]
		    try:d_buffer['follicleFollow'].parent = mi_go._i_rigNull
		    except:pass
		    try:d_buffer['follicleAttach'].parent = mi_go._i_rigNull
		    except:pass				
	    except Exception,error:raise StandardError,"Parent follicles. | error : %s"%(error)
	    
    return fncWrap(*args, **kws).go()
    
#----------------------------------------------------------------------------------------------
# Important info ==============================================================================
__d_buildOrder__ = {0:{'name':'skeleton','function':build_rigSkeleton},
                    1:{'name':'shapes','function':build_shapes},
                    2:{'name':'controls','function':build_controls},
                    3:{'name':'rig','function':build_rig},
                    } 
#===============================================================================================
#----------------------------------------------------------------------------------------------