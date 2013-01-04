#=========================================================================      
#Pupper requirements- We force the update on the Red9 internal registry  
# Puppet - network node
# >>
#=========================================================================         
from Red9.core import Red9_Meta as r9Meta
#========================================================================
import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

import maya.cmds as mc

from cgm.lib.classes import NameFactory

from cgm.core import cgmMeta
reload(cgmMeta)

from cgm.lib import (modules,attributes,search)

import random
import re
import copy
import time

#Initial settings to setup
#=========================    
initLists = ['modules','rootModules','orderedModules','orderedParentModules','nodes']
initDicts = ['Module','moduleParents','moduleChildren','moduleStates']
initStores = []

########################################################################
class cgmPuppet(cgmMeta.cgmNode):
    """"""
    #----------------------------------------------------------------------
    def __init__(self, node = None, name = None, initializeOnly = False, *args,**kws):
        """Constructor"""
        #>>>Keyword args
        puppet = kws.pop('puppet',None)
        #puppet = kws.pop('puppet',None)
        #initializeOnly = kws.pop('initializeOnly',False)
        
        start = time.clock()
              
        #Need a simple return of
        puppets = simplePuppetReturn()
        
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Finding the network node and name info from the provided information
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>          
        ##If a node is provided, check if it's a cgmPuppet
        ##If a name is provided, see if there's a puppet with that name, 
        ##If nothing is provided, just make one
        if node is None and name is None and args:
            log.info("Checking '%s'"%args[0])
            node = args[0]
            
        if puppets:#If we have puppets, check em
            log.info("Found the following puppets: '%s'"%"','".join(puppets))            
            if name is not None or node is not None:    
                if node is not None and node in puppets:
                    puppet = node
                    name = attributes.doGetAttr(node,'cgmName')
                else:
                    for p in puppets:
                        if attributes.doGetAttr(p,'cgmName') in [node,name]:
                            log.info("Puppet tagged '%s' exists. Checking '%s'..."%(attributes.doGetAttr(p,'cgmName'),p))
                            puppet = p
                            name = attributes.doGetAttr(p,'cgmName')
                            break

                
        #if puppet == None:#If we still don't have a puppet
            #if args and args[0]:
                #log.info("Checking args")
                #if mc.objExists(args[0]):
                    ##If we're here, there's a node named our master null.
                    ##We need to get the network from that.
                    #log.info("Trying to find network from '%s'"%args[0])
                    #tmp = r9Meta.MetaClass(args[0])
                    #if attributes.doGetAttr(tmp.mNode,'mClass') == 'cgmPuppet':#If it's a puppet network
                        #puppet = args[0]
                    #else:
                        #puppet = tmp.puppet.mNode#If its a root
                    #name = tmp.cgmName
                #else:
                    #log.info("Not Puppet object found, creating '%s'"%args[0])
                    #puppet = None
                    #name = args[0]              
        
        if not name:
            log.warning("No puppet name found")
            name = search.returnRandomName()  
            
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Verify or Initialize
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>           
        log.info("Puppet is '%s'"%name)
        super(cgmPuppet, self).__init__(node = puppet, name = name) 

        self.addAttr('mClass', initialValue='cgmPuppet',lock=True)  
        self.doStore('cgmName',name,True)
        
        #>>> Puppet Network Initialization Procedure ==================       
        if self.isReferenced() or initializeOnly:
            log.info("'%s' Initializing only..."%name)
            if not self.initialize():
                #log.warning("'%s' failed to initialize. Please go back to the non referenced file to repair!"%name)
                raise StandardError,"'%s' failed to initialize. Please go back to the non referenced file to repair!"%name
        else:
            if not self.verify():
                #log.critical("'%s' failed to verify!"%name)
                raise StandardError,"'%s' failed to verify!"%name
            
        log.info("'%s' Checks out!"%name)
        log.info('Time taken =  %0.3f' % (time.clock()-start))
        
        
    def __bindData__(self):
        #Default to creation of a var as an int value of 0
        ### input check   
        log.info('>>'*5+ "cgmPuppet Bind data")     
        #self.addAttr('masterNull',type='messageSimple')        
        #self.addAttr('puppetGroup',type='messageSimple')
        #self.addAttr('modulesGroup',type='messageSimple')
        #self.addAttr('noTransformGroup',type='messageSimple')
        #self.addAttr('geoGroup',type='messageSimple')
        
    #====================================================================================
    def initialize(self):
        """ 
        Initializes the various components a masterNull for a character/asset.
        
        RETURNS:
        success(bool)
        """  
        #Puppet Network Node
        #==============
        if self.mClass != 'cgmPuppet':
            return False    
        
        #>>>Master null
        if self.masterNull:
            self.i_masterNull = self.masterNull#link it
            log.info("'%s' initialized as master null"%self.masterNull.mNode)
        else:
            log.error("MasterNull missing. Go back to unreferenced file")
            return False
        #>>>Info Nulls
        ## Initialize the info nodes
        for attr in 'settings','geo','parts':
            if attr in  self.__dict__.keys():
                try:
                    Attr = 'i_'+ attr
                    self.__dict__[Attr] = cgmMeta.cgmMetaFactory( self.__getattribute__(attr).mNode )
                    log.info("'%s' initialized as self.%s"%(self.__getattribute__(attr).mNode,Attr))                    
                except:
                    log.error("'%s' info node failed. Please verify puppet."%attr)                    
                    return False

        #>>>Groups 
        ## Initialize the info nodes
        for attr in 'partsGroup','noTransformGroup','geoGroup':
            if attr in self.i_masterNull.__dict__.keys():
                try:
                    Attr = 'i_'+ attr
                    self.__dict__[Attr] = cgmMeta.cgmMetaFactory( self.i_masterNull.__getattribute__(attr).mNode )
                    log.info("'%s' initialized as 'self.%s'"%(self.i_masterNull.__getattribute__(attr).mNode,Attr))                    
                except:
                    log.error("'%s' info node failed. Please verify puppet."%attr)                    
                    return False

                
        return True
    
    def verify(self):
        """"""
        """ 
        Verifies the various components a puppet network for a character/asset. If a piece is missing it replaces it.
        
        RETURNS:
        success(bool)
        """             
        #Puppet Network Node
        #==============    
        if attributes.doGetAttr(self.mNode,'mClass') != 'cgmPuppet':
            log.error("'%s' is not a puppet. It's mClass is '%s'"%(self.mNode, attributes.doGetAttr(self.mNode,'mClass')))
            return False
        self.doName() #See if it's named properly. Need to loop back after scene stuff is querying properly
        
        self.addAttr('cgmType','puppetNetwork')
        self.addAttr('version',initialValue = 1.0, lock=True)  
        self.addAttr('masterNull',attrType = 'messageSimple',lock=True)  
        self.addAttr('settings',attrType = 'messageSimple',lock=True)  
        self.addAttr('geo',attrType = 'messageSimple',lock=True)  
        self.addAttr('parts',attrType = 'messageSimple',lock=True)  

        self.doName()
        self.getAttrs()
        log.debug("Network good...")
        
        #MasterNull
        #==============   
        if not mc.objExists(attributes.returnMessageObject(self.mNode,'masterNull')):#If we don't have a masterNull, make one
            self.i_masterNull = cgmMasterNull(puppet = self)
            #self.connectChild(self.i_masterNull.mNode, 'masterNull','puppet')               
            log.info('Master created.')
        else:
            log.info('Master null exists. linking....')            
            self.i_masterNull = self.masterNull#Linking to instance for faster processing. Good idea?
            
        if self.i_masterNull.getShortName() != self.cgmName:
            self.i_masterNull.doName(False)
            if self.i_masterNull.getShortName() != self.cgmName:
                log.warning("Master Null name still doesn't match what it should be.")
                return False
        attributes.doSetLockHideKeyableAttr(self.masterNull.mNode,channels=['tx','ty','tz','rx','ry','rz','sx','sy','sz'])
        log.debug("Master Null good...")
        
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Info Nodes
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>             
        
        #Settings
        #==============
        if not mc.objExists( attributes.returnMessageObject(self.mNode,'settings') ):
            log.info('Creating settings')                                    
            self.i_settings = cgmInfoNode(puppet = self, infoType = 'settings')#Create and initialize
        else:
            log.info('settings infoNode exists. linking....')                        
            self.i_settings = self.settings #Linking to instance for faster processing. Good idea?
        
        defaultFont = modules.returnSettingsData('defaultTextFont')
        
        self.i_settings.addAttr('font',attrType = 'string',initialValue=defaultFont,lock=True)   
        self.i_settings.addAttr('puppetType',attrType = 'int',initialValue=0,lock=True)
        self.i_settings.addAttr('axisAim',enumName = 'x+:y+:z+:x-:y-:z-',attrType = 'enum',initialValue=2) 
        self.i_settings.addAttr('axisUp',enumName = 'x+:y+:z+:x-:y-:z-', attrType = 'enum',initialValue=1) 
        self.i_settings.addAttr('axisOut',enumName = 'x+:y+:z+:x-:y-:z-',attrType = 'enum',initialValue=0) 
        
        #Geo
        #==============
        if mc.objExists( attributes.returnMessageObject(self.mNode,'geo') ):
            log.info('geo infoNode exists. linking....')                        
            self.i_geo  = self.geo #Linking to instance for faster processing. Good idea?         
        else:
            log.info('Creating geo')                                    
            self.i_geo = cgmInfoNode(puppet = self, infoType = 'geo')#Create and initialize
            
        #Parts
        #==============
        if mc.objExists( attributes.returnMessageObject(self.mNode,'parts') ):
            log.info('parts infoNode exists. linking....')                        
            self.i_parts  = self.parts #Linking to instance for faster processing. Good idea?          
        else:
            log.info('Creating parts')                                    
            self.i_parts = cgmInfoNode(puppet = self, infoType = 'parts')#Create and initialize
            
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Groups
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>    
        for attr in 'noTransform','geo','parts':
            grp = attributes.returnMessageObject(self.i_masterNull.mNode,attr+'Group')# Find the group
            Attr = 'i_' + attr+'Group'#Get a better attribute store string           
            if mc.objExists( grp ):
                #If exists, initialize it
                log.info(self.i_masterNull.__dict__[attr+'Group'])
                #self.__dict__[Attr]  = self.i_masterNull.__dict__[attr+'Group']#link it, can't link it
                self.__dict__[Attr]  = r9Meta.MetaClass(grp)#initialize
                log.info("'%s' initialized as 'self.%s'"%(grp,Attr))
                log.info(self.__dict__[Attr].mNode)
                #except:
                    #log.error("'%s' group failed. Please verify puppet."%attr)                    
                    #return False   
                
            else:#Make it
                log.info('Creating %s'%attr)                                    
                self.__dict__[Attr]= cgmMeta.cgmObject(name=attr)#Create and initialize
                self.__dict__[Attr].doName()
                self.i_masterNull.connectChild(self.__dict__[Attr].mNode, attr+'Group','puppet') #Connect the child to the holder
                log.info("Initialized as 'self.%s'"%(Attr))                    
                
            # Few Case things
            #==============            
            if attr == 'geo':
                self.__dict__[Attr].doParent(self.i_noTransformGroup)
            else:    
                self.__dict__[Attr].doParent(self.i_masterNull)
        
            attributes.doSetLockHideKeyableAttr( self.__dict__[Attr].mNode )
        
        return True
    
    def changeName(self,name = ''):
        if name == self.cgmName:
            log.error("Puppet already named '%s'"%self.cgmName)
            return
        if name != '' and type(name) is str:
            log.warn("Changing name from '%s' to '%s'"%(self.cgmName,name))
            self.cgmName = name
            self.verify()
            
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Puppet Utilities
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>             
    def tracePuppet(self):
        pass #Do this later.Trace a puppet to be able to fully delete everything.
        #self.nodes_list.append()
        raise NotImplementedError
            
    def delete(self):
        """
        Delete the Puppet
        """
        mc.delete(self.i_masterNull.mNode)
        mc.delete(self.i_geo.mNode)
        mc.delete(self.i_parts.mNode)
        mc.delete(self.i_settings.mNode)
        del(self)
   
    
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Special objects
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>           
class cgmMasterNull(cgmMeta.cgmObject):
    """"""
    #----------------------------------------------------------------------
    def __init__(self,node = None, name = 'master',*args,**kws):
        """Constructor"""
        #>>>Keyword args
        puppet = kws.pop('puppet',False)
        
        super(cgmMasterNull, self).__init__(node=node, name = name)
        
        if puppet:
            log.info("Puppet provided!")
            log.info(puppet.cgmName)
            log.info(puppet.mNode)
            self.doStore('cgmName',puppet.mNode+'.cgmName')
            self.connectParent(puppet, 'masterNull','puppet')               
            
        self.verify()
        
    def verify(self):
        """"""
        """ 
        Verifies the various components a puppet network for a character/asset. If a piece is missing it replaces it.
        
        RETURNS:
        success(bool)
        """ 
        self.addAttr('mClass',value = 'cgmMasterNull',lock=True)
        self.addAttr('cgmName',initialValue = '',lock=True)
        self.addAttr('cgmType',initialValue = 'ignore',lock=True)
        self.addAttr('cgmModuleType',value = 'master',lock=True)   
        self.addAttr('partsGroup',attrType = 'messageSimple',lock=True)   
        self.addAttr('noTransformGroup',attrType = 'messageSimple',lock=True)   
        self.addAttr('geoGroup',attrType = 'messageSimple',lock=True)   
        
        #See if it's named properly. Need to loop back after scene stuff is querying properly
        self.doName()
        
    def __bindData__(self):
        pass
    
class cgmInfoNode(cgmMeta.cgmNode):
    """"""
    def __init__(self,node = None, name = None,*args,**kws):
        """Constructor"""
        puppet = kws.pop('puppet',False)#to pass a puppet instance in 
        infoType = kws.pop('infoType','')
        
        #>>>Keyword args
        super(cgmInfoNode, self).__init__(node=node, name = name,*args,**kws)
        log.info("puppet :%s"%puppet)
        if puppet:
            self.doStore('cgmName',puppet.mNode+'.cgmName')
            self.connectParent(puppet, infoType, 'puppet')               
             
        self.addAttr('cgmName', attrType = 'string', initialValue = '',lock=True)
        if infoType == '':
            if self.hasAttr('cgmTypeModifier'):
                infoType = self.cgmTypeModifier
            else:
                infoType = 'settings'
                
        self.addAttr('cgmTypeModifier',infoType,lock=True)
        self.addAttr('cgmType','info',lock=True)
        
        self.verify()
        
    def verify(self):
        """"""
        """ 
        Verifies the various components a puppet network for a character/asset. If a piece is missing it replaces it.
        
        RETURNS:
        success(bool)
        """ 
        log.info(">"*10 + " cgmInfoNode.verify.... " + "<"*10)
        #See if it's named properly. Need to loop back after scene stuff is querying properly
        self.doName()  
        
    def __bindData__(self):
        pass
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# MODULE Base class
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  
InfoNullsNames = ['settings',
                  'setupOptions',
                  'templatePosObjects',
                  'visibilityOptions',
                  'templateControlObjects',
                  'coreNames',
                  'templateStarterData',
                  'templateControlObjectsData',
                  'skinJoints',
                  'rotateOrders']

moduleStates = ['define','template','deform','rig']

initLists = []
initDicts = ['infoNulls','parentTagDict']
initStores = ['ModuleNull','refState']
initNones = ['refPrefix','moduleClass']

defaultSettings = {'partType':'none'}

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Modules
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
moduleNulls_toMake = 'rig','template' #These will be created and connected to a module and parented under them    

rigNullAttrs_toMake = {'fk':'bool',#Attributes to be initialzed for any module
                       'ik':'bool',
                       'stretchy':'bool',
                       'bendy':'bool',
                       'handles':'int',
                       'skinJoints':'message'}
templateNullAttrs_toMake = {'rollJoints':'int',
                            'stiffIndex':'int',
                            'curveDegree':'int',
                            'templatePosObjects':'message',
                            'templateControlObjects':'message',
                            'templateStarterData':'string',
                            'templateControlObjectData':'string'}
                
class cgmModule(cgmMeta.cgmObject):
    def __init__(self,*args,**kws):
        """ 
        Intializes an module master class handler
        Args:
        node = existing module in scene
        name = treated as a base name
        
        Keyword arguments:
        moduleName(string) -- either base name or the name of an existing module in scene
        moduleParent(string) -- module parent to connect to. MUST exist if called. If the default False flag is passed, it looks for what's stored
        
        Naming and template tags. All Default to False
        position(string) -- position tag
        direction(string) -- direction
        directionModifier(string)
        nameModifier(string)
        forceNew(bool) --whether to force the creation of another if the object exists
        """
        start = time.clock()
        
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Figure out the node
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>          
        ##If a node is provided, use it
        ##If a name is provided, see if there's node for it
        ##If nothing is provided, just make one     


        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Verify or Initialize
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>           
        super(cgmModule, self).__init__(*args,**kws) 
        
        #Keywords - need to set after the super call
        #==============         
        self.kw_name= kws.pop('name',False)        
        self.kw_moduleParent = kws.pop('moduleParent',False)
        self.kw_position = kws.pop('position',False)
        self.kw_direction = kws.pop('direction',False)
        self.kw_directionModifier = kws.pop('directionModifier',False)
        self.kw_nameModifier = kws.pop('nameModifier',False)
        self.kw_forceNew = kws.pop('forceNew',False)
        self.kw_initializeOnly = kws.pop('initializeOnly',False)  
        self.kw_handles = kws.pop('handles',1) # can't have self handles  
        
        if self.kw_name:#If we have a name, store it
            self.doStore('cgmName',self.kw_name,True)
         
        self.kw_callNameTags = {'cgmPosition':self.kw_position, 
                                'cgmDirection':self.kw_direction, 
                                'cgmDirectionModifier':self.kw_directionModifier,
                                'cgmNameModifier':self.kw_nameModifier}
        
        #>>> Initialization Procedure ==================   
        if self.isReferenced() or self.kw_initializeOnly:
            log.info("'%s' Initializing only..."%self.kw_name)
            if not self.initialize():
                log.warning("'%s' failed to initialize. Please go back to the non referenced file to repair!"%self.kw_name)
                return          
        else:
            if not self.verify():
                log.critical("'%s' failed to verify!"%self.kw_name)
                return  
            
        log.info("'%s' Checks out!"%self.kw_name)
        log.info('Time taken =  %0.3f' % (time.clock()-start))
        

    def __bindData__(self,**kws):        
        #Variables
        #==============      
        self.addAttr('mClass', initialValue='cgmModule',lock=True) 
        self.addAttr('cgmType',value = 'module',lock=True)

        
    def initialize(self):
        """ 
        Initializes the various components a moduleNull for a character/asset.
        
        RETURNS:
        success(bool)
        """  
        #Puppet Network Node
        #==============
        if self.cgmType != 'module':
            log.warning("cgmType not '%s'"%self.cgmType)
            return False    
        
        for attr in moduleNulls_toMake:
            if attr + 'Null' in self.__dict__.keys():
                try:
                    Attr = 'i_' + attr+'Null'#Get a better attribute store string           
                    self.__dict__[Attr] = r9Meta.MetaClass( self.__getattribute__(attr+'Null').mNode  )
                    log.info("'%s' initialized as self.%s"%(self.__getattribute__(attr+'Null').mNode,Attr))  
                except:    
                    log.error("'%s' info node failed. Please verify puppet."%attr)                    
                    return False
                    
        return True
             
        
    def verify(self):
        """"""
        """ 
        Verifies the various components a puppet network for a character/asset. If a piece is missing it replaces it.
        
        RETURNS:
        success(bool)
        """
        #>>> Module Null ==================           
  
        if attributes.doGetAttr(self.mNode,'cgmType') != 'module':
            log.error("'%s' is not a module. It's mClass is '%s'"%(self.mNode, attributes.doGetAttr(self.mNode,'mClass')))
            return False
        
        #Store tags from init call
        #==============  
        for k in self.kw_callNameTags.keys():
            if self.kw_callNameTags.get(k):
                log.info(k + " : " + str(self.kw_callNameTags.get(k)))                
                self.addAttr(k,value = self.kw_callNameTags.get(k),lock = True)
                log.info(str(self.getNameDict()))
                log.info(self.__dict__[k])
            #elif k in self.parentTagDict.keys():
             #   self.store(k,'%s.%s'%(self.msgModuleParent.value,k))
        self.doName()        
        
        #Attributes
        #==============  
        self.addAttr('moduleType',value = 'segment',lock=True)
        
        self.addAttr('moduleParent',attrType='messageSimple')
        self.addAttr('modulePuppet',attrType='messageSimple')
        
        stateDict = {'templateState':0,'rigState':0,'skeletonState':0} #Initial dict
        self.addAttr('moduleStates',attrType = 'string', initialValue=stateDict, lock = True)
        
        self.addAttr('rigNull',attrType='messageSimple',lock=True)
        self.addAttr('templateNull',attrType='messageSimple',lock=True)

        log.debug("Module null good...")
        
        #>>> Rig/Template Nulls ==================   
        
        #Initialization
        #==============      
        for attr in moduleNulls_toMake:
            log.info(attr)
            grp = attributes.returnMessageObject(self.mNode,attr+'Null')# Find the group
            Attr = 'i_' + attr+'Null'#Get a better attribute store string           
            if mc.objExists( grp ):
                #If exists, initialize it
                try:     
                    self.__dict__[Attr]  = r9Meta.MetaClass(grp)#Initialize if exists  
                    log.info("'%s' initialized to 'self.%s'"%(grp,Attr))                    
                except:
                    log.error("'%s' group failed. Please verify puppet."%attr)                    
                    return False   
                
            else:#Make it
                log.info('Creating %s'%attr)                                    
                self.__dict__[Attr]= cgmMeta.cgmObject(name=attr)#Create and initialize
                self.connectChild(self.__dict__[Attr].mNode, attr+'Null','module') #Connect the child to the holder                
                self.__dict__[Attr].addAttr('cgmType',attr+'Null',lock=True)
                log.info("'%s' initialized to 'self.%s'"%(grp,Attr))                    
                
            self.__dict__[Attr].doParent(self.mNode)
            self.__dict__[Attr].doName()
        
            attributes.doSetLockHideKeyableAttr( self.__dict__[Attr].mNode )
                 
            
        #Attrbute checking
        #=================
        for attr in rigNullAttrs_toMake.keys():#See table just above cgmModule
            log.info("Checking '%s' on rig Null"%attr)
            if attr == 'handles':
                if self.kw_handles == 1:
                    self.i_rigNull.addAttr(attr,initialValue = self.kw_handles, attrType = rigNullAttrs_toMake[attr],lock = True )                
                else:
                    self.i_rigNull.addAttr(attr,value = self.kw_handles, attrType = rigNullAttrs_toMake[attr],lock = True )                
                    
                log.info('handles case, setting min')
                a = cgmMeta.cgmAttr(self.i_rigNull.mNode,'handles')
                log.info(self.kw_handles)                
                log.info(self.i_rigNull.handles)                
                a.doMin(1)#Make this check that the value is not below the min when set
                #a.set(self.kw_handles)
            else:
                self.i_rigNull.addAttr(attr,attrType = rigNullAttrs_toMake[attr],lock = True )
                                
        for attr in templateNullAttrs_toMake.keys():#See table just above cgmModule
            log.info("Checking '%s' on template Null"%attr)
            self.i_templateNull.addAttr(attr,attrType = templateNullAttrs_toMake[attr],lock = True )        
      
        return True        
    
    def doSetParentModule(self,moduleParent):
        assert mc.objExists(moduleParent),"'%s' doesn't exists! Can't be module parent of '%s'"%(moduleParent,self.ModuleNull.nameShort)
        if search.returnTagInfo(moduleParent,'cgmType') == 'module':
            if self.moduleParent != moduleParent:
                self.moduleParent = moduleParent
                self.connectParent(moduleParent, 'masterNull','puppet')                               
                log.repport("'%s' is not the module parent of '%s'"%(moduleParent,self.ModuleNull.nameShort))
            else:
                log.warning("'%s' already this module's parent. Moving on..."%moduleParent)
                return True
        else:
            log.warning("'%s' isn't tagged as a module."%moduleParent)
            return False
        
        

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Utilities
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>        
def simplePuppetReturn():
    catch = mc.ls(type='network')
    returnList = []
    if catch:
        for o in catch:
            if attributes.doGetAttr(o,'mClass') == 'cgmPuppet':
                returnList.append(o)
    return returnList



#=========================================================================      
# R9 Stuff - We force the update on the Red9 internal registry  
#=========================================================================      
r9Meta.registerMClassInheritanceMapping()   
print '============================================='  
r9Meta.printSubClassRegistry()  
print '============================================='
#=========================================================================
          