"""
------------------------------------------
cgm_Meta: cgm.core
Author: Josh Burton
email: jjburton@cgmonks.com

Website : http://www.cgmonks.com
------------------------------------------

This is the Core of the MetaNode implementation of the systems.
It is uses Mark Jackson (Red 9)'s as a base.
================================================================
"""
import maya.cmds as mc
import maya.mel as mel
import copy
import time
import inspect
import sys

# From Red9 =============================================================

# From cgm ==============================================================
from cgm.lib import search
# Shared Defaults ========================================================

#=========================================================================
import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
#=========================================================================

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>   
# cgmMeta - MetaClass factory for figuring out what to do with what's passed to it
#========================================================================= 
class cgmFuncCls(object):  
    """
    Examples:
    
    self._l_ARGS_KWS_DEFAULTS = [{'kw':'objToAttach',"default":None},
				 {'kw':'targetSurface',"default":None},
				 {'kw':"createControlLoc","default":True},
				 {'kw':"createUpLoc","default":False},
				 {'kw':"parentToFollowGroup","default":False},	                  
				 {'kw':'f_offset',"default":1.0},
				 {'kw':'orientation',"default":'zyx'}]
    """
    def __init__(self,*args, **kws):
        self._str_funcClass = None
	self._str_funcCombined = None
        self._str_funcName = None
        self._str_funcDebug = None
	self._b_WIP = False
	self._l_ARGS_KWS_DEFAULTS = []
	self.d_kwsDefined  = {}
	self.l_funcSteps = []
	self.d_return = {}
	self._str_modPath = None
	self._str_mod = None	
	self._d_stepTimes = {}
	#This is our mask so that the fail report ignores them
	self._l_reportMask = ['_str_modPath','_go','l_funcSteps','d_return','_str_funcDebug','_str_funcKWs','_l_reportMask','_l_errorMask',
	                     '_str_funcClass','_str_funcName','d_kwsDefined','_str_funcCombined','_l_kwMask','_l_funcArgs','_b_WIP','_d_stepTimes','_l_ARGS_KWS_DEFAULTS',
	                     '_str_mod','_str_funcArgs','_d_funcKWs','_str_reportStart']  
	self._l_errorMask = ['_str_modPath','_go','l_funcSteps','d_return','_str_funcDebug','_str_funcKWs','_l_reportMask',
	                    '_str_funcClass','_str_funcName','d_kwsDefined','_str_funcCombined','_l_kwMask','_l_funcArgs','_l_ARGS_KWS_DEFAULTS',
	                    '_str_mod','_str_funcArgs','_d_funcKWs','_str_reportStart']
	#List of kws to ignore when a function wants to use kws for special purposes in the function call -- like attr:value
	self._l_kwMask = ['reportTimes','reportShow']
	     
    def __dataBind__(self,*args,**kws):
	try:self._l_funcArgs = args
	except:self._l_funcArgs = []
	try:self._d_funcKWs = kws
	except:self._d_funcKWs = {}	
	try:self._str_funcArgs = str(args)
	except:self._str_funcArgs = None
	try:self._str_funcKWs = str(kws)
	except:self._str_funcKWs = None
        try:
            mod = inspect.getmodule(self)
	    self._str_modPath = inspect.getmodule(self)
            self._str_mod = '%s' % mod.__name__.split('.')[-1]
	    self._str_funcCombined = "%s.%s"%(self._str_mod,self._str_funcName)
        except:self._str_funcCombined = self._str_funcName
	self._str_reportStart = " %s >> "%(self._str_funcName)
	
	if self._l_ARGS_KWS_DEFAULTS:
	    for i,d_buffer in enumerate(self._l_ARGS_KWS_DEFAULTS):
		try:self.d_kwsDefined[d_buffer['kw']] = args[ i ]#First we try the arg index
		except:
		    try:self.d_kwsDefined[d_buffer['kw']] = kws[d_buffer['kw']]#Then we try a kw call
		    except:self.d_kwsDefined[d_buffer['kw']] = d_buffer.get("default")#Lastly, we use the default value	
	l_storedKeys = self.d_kwsDefined.keys()
	for kw in kws:
	    try:
		if kw not in l_storedKeys:self.d_kwsDefined[kw] = kws[kw]
	    except Exception,error:raise StandardError,"%s failed to store kw: %s | value: %s | error: %s"%(self._str_reportStart,kw,kws[kw],error)
	if self._b_WIP or self.d_kwsDefined.get('reportShow'):
	    self.report()
	    
    def __func__(self,*args,**kws):
	raise StandardError,"%s No function set"%self._str_reportStart
        
    def go(self,goTo = '',**kws):
	"""
	"""	
	t_start = time.clock()
	try:
	    if not self.l_funcSteps: self.l_funcSteps = [{'call':self.__func__}]
	    int_keys = range(0,len(self.l_funcSteps)-1)
	    int_max = len(self.l_funcSteps)-1
	except Exception,error:
	    raise StandardError, ">"*3 + " %s >!FAILURE!> go start | Error: %s"%(self._str_funcCombined,error)
	
	for i,d_step in enumerate(self.l_funcSteps):
	    t1 = time.clock()	    
	    try:	
		_str_step = d_step.get('step') or self._str_funcName
		res = d_step['call']()
		if res is not None:
		    self.d_return[_str_step] = res
		"""
		if goTo.lower() == str_name:
		    log.debug("%s.doBuild >> Stopped at step : %s"%(self._strShortName,str_name))
		    break"""
	    except Exception,error:
		log.error(">"*3 + " %s "%self._str_funcCombined + "="*75)
		log.error(">"*3 + " Module: %s "%self._str_modPath)	    		    
		if self._str_funcArgs:log.error(">"*3 + " Args: %s "%self._str_funcArgs)
		if self._str_funcKWs:log.error(">"*3 + " KWs: %s "%self._str_funcKWs)	 
		if self.d_kwsDefined:
		    for k in self.d_kwsDefined.keys():
			log.error(">"*3 + " '%s' : %s "%(k,self.d_kwsDefined[k]))		
		_str_fail = ">"*3 + " %s >!FAILURE!> Step: '%s' | Error: %s"%(self._str_funcCombined,_str_step,error)
		log.error(_str_fail)
		
		log.error(">"*3 + " Self Stored " + "-"*75)
		l_keys = self.__dict__.keys()
		l_keys.sort()
		for k in l_keys:
		    if k not in self._l_errorMask:
			buffer = self.__dict__[k]
			if type(buffer) is dict:
			    log.error(">"*6 + " Nested Dict: %s "%k + "-"*75)
			    l_bufferKeys = buffer.keys()
			    l_bufferKeys.sort()
			    for k2 in buffer.keys():
				log.error(">"*6 + " '%s' : %s "%(k2,buffer[k2]))			
			else:
			    log.error(">"*3 + " '%s' : %s "%(k,self.__dict__[k]))
		if self._b_WIP:
		    log.error(">"*40 + " WIP CODE " + "<"*40)	
		log.error("%s >> Fail Time >> = %0.3f seconds " % (self._str_funcCombined,(time.clock()-t1)))
		#self.d_return[_str_step] = None	
		raise StandardError, _str_fail
	    t2 = time.clock()
	    _str_time = "%0.3f seconds"%(t2-t1)
	    self._d_stepTimes[_str_step] = _str_time
	    if int_max != 0 and self.d_kwsDefined.get('reportTimes'): log.info("%s | '%s' >> Time >> = %0.3f seconds " % (self._str_funcCombined,_str_step,(t2-t1)))		
	
	if self.d_kwsDefined.get('reportTimes'):
	    log.info("%s >> Complete Time >> = %0.3f seconds " % (self._str_funcCombined,(time.clock()-t_start)))		
	if int_max == 0:#If it's a one step, return, return the single return
	    try:return self.d_return[self.d_return.keys()[0]]
	    except:pass
	for k in self.d_return.keys():#Otherise we return the first one with actual data
	    buffer = self.d_return.get(k)
	    if buffer:
		return buffer
	return self.d_return
    
    def report(self):
	log.info(">"*3 + " %s "%self._str_funcCombined + "="*75)
	log.info(">"*3 + " Module: %s "%self._str_modPath)	
	if self.l_funcSteps:log.info(">"*3 + " l_funcSteps: %s "%self.l_funcSteps)	
	self.reportArgsKwsDefaults()	
	#if self._str_funcArgs:log.info(">"*3 + " Args: %s "%self._str_funcArgs)
	#if self._str_funcKWs:log.info(">"*3 + " KWs: %s "%self._str_funcKWs)	  
	if self.d_kwsDefined:
	    log.info(">"*3 + " KWs Defined " + "-"*75)	
	    l_keys = self.d_kwsDefined.keys()
	    l_keys.sort()	    
	    for k in l_keys:
		log.info(">"*3 + " '%s' : %s "%(k,self.d_kwsDefined[k]))
	log.info(">"*3 + " Self Stored " + "-"*75)	
	l_keys = self.__dict__.keys()
	l_keys.sort()
	for k in l_keys:
	    if k not in self._l_reportMask:
		buffer = self.__dict__[k]
		if type(buffer) is dict:
		    log.info(">"*6 + " Nested Dict: %s "%k + "-"*75)
		    l_bufferKeys = buffer.keys()
		    l_bufferKeys.sort()
		    for k2 in buffer.keys():
			log.info(">"*6 + " '%s' : %s "%(k2,buffer[k2]))			
		else:
		    log.info(">"*3 + " '%s' : %s "%(k,self.__dict__[k]))
	if self.l_funcSteps:
	    log.info(">"*3 + " Steps " + "-"*75)	  	    
	    for i,d in enumerate(self.l_funcSteps):
		try:log.info(">"*3 + " '%s' : %s "%(i,d.get('step')))
		except:pass
			
	if self._b_WIP:
	    log.info(">"*40 + " WIP Function " + "<"*40)	  	    
	log.info("#" + "-" *100)
	
    def reportArgsKwsDefaults(self):
	if self._l_ARGS_KWS_DEFAULTS:
	    log.info(">"*3 + " Args/KWs/Defaults " + "-"*75)	  	    	    
	    for i,d_buffer in enumerate(self._l_ARGS_KWS_DEFAULTS):
		l_tmp = [['Arg',i,]]
		try:l_tmp.append(['kw',"'%s'"%d_buffer.get('kw')])
		except:pass
		try:l_tmp.append(['default',d_buffer.get('default')])
		except:pass		
		l_build = ["%s : %s"%(s[0],s[1]) for s in l_tmp]
		log.info(" | ".join(l_build))
		
class cgmFunctionClass2(object):
    """Simple class for use with TimerSimple"""
    def __init__(self,*args, **kws):
        self._str_funcClass = 'Default cgmFunctionClass'	
        self._str_funcName = 'Default func'
        self._str_funcStep = 'Default sub'
        self._str_funcDebug = 'Default debug'
	try:self._str_funcArgs = "%s"%args
	except:self._str_funcArgs = None
	try:self._str_funcKWs = "%s"%kws
	except:self._str_funcKWs = None

"""
example subFunctionClass(object)
class sampleClass(cgmFunctionClass):
    def __init__(self,*args, **kws):
        super(sampleClass, self).__init__(*args, **kws)
"""
        
        
def funcClassWrap(funcClass):
    '''
    Simple timer decorator 
    -- Taken from red9 and modified. Orignal props to our pal Mark Jackson
    '''        
    def wrapper( *args, **kws):
	#Data Gather
        _str_funcName = 'No Func found'
        try:_str_funcName = args[0]._str_funcName
        except Exception,error:log.info(error)

        t1 = time.clock()
        try:res=funcClass(*args,**kws) 
        except Exception,error:
	    log.info(">"*3 + " %s "%_str_funcName + "="*75)	    
	    log.error(">"*3 + " Step: %s "%args[0]._str_funcStep)	    
	    log.error(">"*3 + " Args: %s "%args[0]._str_funcArgs)
	    log.error(">"*3 + " KWs: %s "%args[0]._str_funcKWs)	    
	    log.info("%s >> Time to Fail >> = %0.3f seconds " % (_str_funcName,(time.clock()-t1)) + "-"*75)			    
	    raise error            
        t2 = time.clock()
	
	#Initial print
	log.info(">"*3 + " %s "%_str_funcName + "="*75)
	log.info(">"*3 + " Args: %s "%args[0]._str_funcArgs)
	log.info(">"*3 + " KWs: %s "%args[0]._str_funcKWs)		
		    
	log.info("%s >> Time >> = %0.3f seconds " % (_str_funcName,(t2-t1)) + "-"*75)		
        return res
    return wrapper  

def Timer(func):
    '''
    Simple timer decorator 
    -- Taken from red9 and modified. Orignal props to our pal Mark Jackson
    '''

    def wrapper( *args, **kws):
        t1 = time.time()
        res=func(*args,**kws) 
        t2 = time.time()

        functionTrace=''
        str_arg = False
        try:
            #module if found
            mod = inspect.getmodule(args[0])
            #log.debug("mod: %s"%mod)            
            functionTrace+='%s >> ' % mod.__name__.split('.')[-1]
        except:
            log.debug('function module inspect failure')
        try:
            #class function is part of, if found
            cls = args[0].__class__
            #log.debug("cls: %s"%cls)
            #log.debug("arg[0]: %s"%args[0])
            if type(args[0]) in [str,unicode]:
                str_first = args[0]
            else:
                str_first = args[0].__class__.__name__  
                
            try:
                log.debug("args]0] : %s"%args[0])                
                str_arg = args[0].p_nameShort
            except:
                log.debug("arg[0] failed to call: %s"%args[0])
            functionTrace+='%s.' % str_first
        except StandardError,error:
            log.debug('function class inspect failure: %s'%error)
        functionTrace+=func.__name__ 
        if str_arg:functionTrace+='(%s)'%str_arg      
        log.info('>'*3 + ' TIMER : %s: %0.4f sec ' % (functionTrace,(t2-t1))+ '<'*3)
        #log.debug('%s: took %0.3f ms' % (func.func_name, (t2-t1)*1000.0))
        return res
    return wrapper  

def TimerDebug(func):
    '''
    Variation,only outputs on debug
    -- Taken from red9 and modified. Orignal props to our pal Mark Jackson
    '''
    def wrapper( *args, **kws):
        t1 = time.time()
        res=func(*args,**kws) 
        t2 = time.time()
        
        functionTrace=''
        try:
            #module if found
            mod = inspect.getmodule(args[0])
            functionTrace+='%s >>' % mod.__name__.split('.')[-1]
        except:
            log.debug('function module inspect failure')
        try:
            #class function is part of, if found
            cls = args[0].__class__
            functionTrace+='%s.' % args[0].__class__.__name__
        except:
            log.debug('function class inspect failure')
        functionTrace+=func.__name__ 
        log.debug('DEBUG TIMER : %s: %0.4f sec' % (functionTrace,(t2-t1)))
        #log.debug('%s: took %0.3f ms' % (func.func_name, (t2-t1)*1000.0))
        return res
    return wrapper


def doStartMayaProgressBar(stepMaxValue = 100, statusMessage = 'Calculating....',interruptableState = True):
    """
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    DESCRIPTION:
    Tools to do a maya progress bar. This function and doEndMayaProgressBar are a part of a set. Example
    usage:

    mayaMainProgressBar = guiFactory.doStartMayaProgressBar(int(number))
    for n in range(int(number)):
    if mc.progressBar(mayaMainProgressBar, query=True, isCancelled=True ) :
    break
    mc.progressBar(mayaMainProgressBar, edit=True, status = (n), step=1)

    guiFactory.doEndMayaProgressBar(mayaMainProgressBar)

    ARGUMENTS:
    stepMaxValue(int) - max number of steps (defualt -  100)
    statusMessage(string) - starting status message
    interruptableState(bool) - is it interuptible or not (default - True)

    RETURNS:
    mayaMainProgressBar(string)
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    """
    mayaMainProgressBar = mel.eval('$tmp = $gMainProgressBar');
    mc.progressBar( mayaMainProgressBar,
                    edit=True,
                    beginProgress=True,
                    isInterruptable=interruptableState,
                    status=statusMessage,
                    minValue = 0,
                    maxValue= stepMaxValue )
    return mayaMainProgressBar

def doEndMayaProgressBar(mayaMainProgressBar):
    mc.progressBar(mayaMainProgressBar, edit=True, endProgress=True)