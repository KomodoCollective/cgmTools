#=================================================================================================================================================
#=================================================================================================================================================
#	cgm.setTools - a part of cgmTools
#=================================================================================================================================================
#=================================================================================================================================================
#
# DESCRIPTION:
#   Tool for making locators and other stuffs
#
# ARGUMENTS:
#   Maya
#   distance
#
# AUTHOR:
# 	Josh Burton (under the supervision of python guru (and good friend) David Bokser) - jjburton@gmail.com
#	http://www.cgmonks.com
# 	Copyright 2011 CG Monks - All Rights Reserved.
#
#=================================================================================================================================================
__version__ = '0.1.06042012'

from cgm.lib.zoo.zooPyMaya.baseMelUI import *
from cgm.lib.classes.OptionVarFactory import *
from cgm.lib.classes.SetFactory import *

import maya.mel as mel
import maya.cmds as mc

from cgm.tools.lib import (setToolsLib)
from cgm.lib import (search,guiFactory)

from cgm.lib import guiFactory

reload(setToolsLib)
reload(guiFactory)


def run():
	cgmSetToolsWin = setToolsClass()
	#cgmSetToolsWin(edit = True, resizeToFitChildren = True)

class setToolsClass(BaseMelWindow):
	from  cgm.lib import guiFactory
	guiFactory.initializeTemplates()
	USE_Template = 'cgmUITemplate'
	
	WINDOW_NAME = 'cgmSetToolsWindow'
	WINDOW_TITLE = 'cgm.setTools'
	DEFAULT_SIZE = 265, 200
	DEFAULT_MENU = None
	RETAIN = True
	MIN_BUTTON = True
	MAX_BUTTON = False
	FORCE_DEFAULT_SIZE = False  #always resets the size of the window when its re-created

	def __init__( self):		
		self.toolName = 'cgm.setTools'
		self.description = 'This is a series of tools for working with cgm Sets'
		self.author = 'Josh Burton'
		self.owner = 'CG Monks'
		self.website = 'www.cgmonks.com'
		self.version =  __version__ 
		self.optionVars = []
		
		self.activeObjectSetsOptionVar = OptionVarFactory('cgmVar_activeObjectSets','string')
		#guiFactory.appendOptionVarList(self,'cgmVar_activeObjectSets')		

		self.showHelp = False
		self.helpBlurbs = []
		self.oldGenBlurbs = []
		
		self.objectSets = []
		setToolsLib.updateObjectSets(self)

		#Menu
		self.setupVariables
		self.UI_OptionsMenu = MelMenu( l='Options', pmc=self.buildOptionsMenu)
		self.UI_HelpMenu = MelMenu( l='Help', pmc=self.buildHelpMenu)
		
		self.ShowHelpOption = mc.optionVar( q='cgmVar_AnimToolsShowHelp' )
		
		#GUI
		
		self.Main_buildLayout(self)
		
		
		self.show()

	def setupVariables():
		if not mc.optionVar( ex='cgmVar_ForceBoundingBoxState' ):
			mc.optionVar( iv=('cgmVar_ForceBoundingBoxState', 0) )
		if not mc.optionVar( ex='cgmVar_ForceEveryFrame' ):
			mc.optionVar( iv=('cgmVar_ForceEveryFrame', 0) )
		if not mc.optionVar( ex='cgmVar_setToolsShowHelp' ):
			mc.optionVar( iv=('cgmVar_setToolsShowHelp', 0) )
		if not mc.optionVar( ex='cgmVar_CurrentFrameOnly' ):
			mc.optionVar( iv=('cgmVar_CurrentFrameOnly', 0) )
		if not mc.optionVar( ex='cgmVar_setToolsShowHelp' ):
			mc.optionVar( iv=('cgmVar_setToolsShowHelp', 0) )
		
		
		guiFactory.appendOptionVarList(self,'cgmVar_setToolsShowHelp')
		
	#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
	# Menus
	#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
	def buildOptionsMenu( self, *a ):
		self.UI_OptionsMenu.clear()

		# Placement Menu
		PlacementMenu = MelMenuItem( self.UI_OptionsMenu, l='Placement', subMenu=True)
		PlacementMenuCollection = MelRadioMenuCollection()

		if mc.optionVar( q='cgmVar_ForceBoundingBoxState' ) == 0:
			cgmOption = False
			pivotOption = True
		else:
			cgmOption = True
			pivotOption = False

		PlacementMenuCollection.createButton(PlacementMenu,l='Bounding Box Center',
				                             c=lambda *a: mc.optionVar( iv=('cgmVar_ForceBoundingBoxState', 1)),
				                             rb=cgmOption )
		PlacementMenuCollection.createButton(PlacementMenu,l='Pivot',
				                             c=lambda *a: mc.optionVar( iv=('cgmVar_ForceBoundingBoxState', 0)),
				                             rb=pivotOption )
		
		# Tagging options
		AutoloadMenu = MelMenuItem( self.UI_OptionsMenu, l='Tagging', subMenu=True)
		if not mc.optionVar( ex='cgmVar_TaggingUpdateRO' ):
			mc.optionVar( iv=('cgmVar_TaggingUpdateRO', 1) )
		guiFactory.appendOptionVarList(self,'cgmVar_TaggingUpdateRO')	
	  
		RenameOnUpdateState = mc.optionVar( q='cgmVar_TaggingUpdateRO' )
		MelMenuItem( AutoloadMenu, l="Update Rotation Order",
	                 cb= mc.optionVar( q='cgmVar_TaggingUpdateRO' ),
	                 c= lambda *a: guiFactory.doToggleIntOptionVariable('cgmVar_TaggingUpdateRO'))
		

		MelMenuItemDiv( self.UI_OptionsMenu )
		MelMenuItem( self.UI_OptionsMenu, l="Reset Active",
			         c=lambda *a: self.reset(True))		
		MelMenuItem( self.UI_OptionsMenu, l="Reset",
			         c=lambda *a: self.reset())
		
	def reset(self,resetActive = False):
		if resetActive:
			guiFactory.purgeOptionVars(['cgmVar_activeObjectSets'])
		Callback(guiFactory.resetGuiInstanceOptionVars(self.optionVars,run))

	def buildHelpMenu( self, *a ):
		self.UI_HelpMenu.clear()
		MelMenuItem( self.UI_HelpMenu, l="Show Help",
				     cb=self.ShowHelpOption,
				     c= lambda *a: self.do_showHelpToggle())
		
		MelMenuItem( self.UI_HelpMenu, l="Print Set Report",
				     c=lambda *a: self.printReport() )
		MelMenuItem( self.UI_HelpMenu, l="Print Tools Help",
				     c=lambda *a: self.printHelp() )

		MelMenuItemDiv( self.UI_HelpMenu )
		MelMenuItem( self.UI_HelpMenu, l="About",
				     c=lambda *a: self.showAbout() )

	def do_showHelpToggle( self):
		guiFactory.toggleMenuShowState(self.ShowHelpOption,self.helpBlurbs)
		mc.optionVar( iv=('cgmVar_setToolsShowHelp', not self.ShowHelpOption))
		self.ShowHelpOption = mc.optionVar( q='cgmVar_setToolsShowHelp' )


	def showAbout(self):
		window = mc.window( title="About", iconName='About', ut = 'cgmUITemplate',resizeToFitChildren=True )
		mc.columnLayout( adjustableColumn=True )
		guiFactory.header(self.toolName,overrideUpper = True)
		mc.text(label='>>>A Part of the cgmTools Collection<<<', ut = 'cgmUIInstructionsTemplate')
		guiFactory.headerBreak()
		guiFactory.lineBreak()
		descriptionBlock = guiFactory.textBlock(self.description)

		guiFactory.lineBreak()
		mc.text(label=('%s%s' %('Written by: ',self.author)))
		mc.text(label=('%s%s%s' %('Copyright ',self.owner,', 2011')))
		guiFactory.lineBreak()
		mc.text(label='Version: %s' % self.version)
		mc.text(label='')
		guiFactory.doButton('Visit Tool Webpage', 'import webbrowser;webbrowser.open(" http://www.cgmonks.com/tools/maya-tools/setTools/")')
		guiFactory.doButton('Close', 'import maya.cmds as mc;mc.deleteUI(\"' + window + '\", window=True)')
		mc.setParent( '..' )
		mc.showWindow( window )

	def printHelp(self):
		import setToolsLib
		help(setToolsLib)
		
	def printReport(self):
		setToolsLib.printReport(self)


	#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
	# Layouts
	#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
	def buildPlaceHolder(self,parent):
		self.containerName = MelColumnLayout(parent,ut='cgmUISubTemplate')
		return self.containerName
	
	
	def Main_buildLayout(self,parent):
		MainForm = MelFormLayout(parent)

		#>>>  Snap Section
		SetHeader = guiFactory.header('Sets')
		HelpInfo = MelLabel(MainForm,
		                    l = " Set buffer options: Set active, select, change name,add,remove,key,purge",
		                    ut = 'cgmUIInstructionsTemplate',
		                    al = 'center',
		                    ww = True,vis = self.ShowHelpOption)
		self.helpBlurbs.extend([HelpInfo])
		
		
		#>>>  All Sets menu
		AllSetsRow = MelFormLayout(MainForm,height = 20)
		activeState = True
		i = 1
		for b in self.objectSets:
			if b not in self.activeObjectSetsOptionVar.value:
				activeState = False
			
		tmpActive = MelCheckBox(AllSetsRow,
	                            annotation = 'Sets all sets active',
	                            value = activeState,
	                            onCommand =  Callback(setToolsLib.setAllSetsAsActive,self),
	                            offCommand = Callback(setToolsLib.setAllSetsAsInactive,self))
		
		tmpSel = guiFactory.doButton2(AllSetsRow,
		                              ' select ',
		                              Callback(setToolsLib.selectAll,self),
		                              'Select the set objects')
						
		
		tmpName = MelLabel(AllSetsRow, w = 100, l = '<<< All Sets >>>')
		

		tmpKey = guiFactory.doButton2(AllSetsRow,
	                                  ' k ',
	                                  Callback(setToolsLib.keyAll,self),			                              
	                                  'Key All Sets')
		tmpPurge = guiFactory.doButton2(AllSetsRow,
	                                    ' d ',
	                                    Callback(setToolsLib.deleteAllCurrentKeys,self),			                              			                                
	                                    'Delete All Set Keys')	
		
		mc.formLayout(AllSetsRow, edit = True,
	                  af = [(tmpActive, "left", 10),
	                        (tmpPurge,"right",10)],
	                  ac = [(tmpSel,"left",0,tmpActive),
	                        (tmpName,"left",2,tmpSel),
	                        (tmpName,"right",2,tmpKey),
	                        (tmpKey,"right",2,tmpPurge)])
		
		
		
		
		#>>> Sets building section
		SetListScroll = MelScrollLayout(MainForm,cr = 1, ut = 'cgmUISubTemplate')
		SetMasterForm = MelFormLayout(SetListScroll)
		SetListColumn = MelColumnLayout(SetMasterForm, adj = True, rowSpacing = 3)
		
		self.objectSetsDict = {}
		self.activeSetsCBDict = {}
		
		for i,b in enumerate(self.objectSets):
			#Store the info to a dict
			self.objectSetsDict[i] = b
			
			tmpSetRow = MelFormLayout(SetListColumn,height = 20)
			
			#Get check box state
			activeState = False
			if b in self.activeObjectSetsOptionVar.value:
				activeState = True
			tmpActive = MelCheckBox(tmpSetRow,
		                            annotation = 'make set as active',
		                            value = activeState,
		                            onCommand =  Callback(setToolsLib.setSetAsActive,self,'cgmVar_activeObjectSets',i),
		                            offCommand = Callback(setToolsLib.setSetAsInactive,self,'cgmVar_activeObjectSets',i))
			self.activeSetsCBDict[i] = tmpActive
			
			tmpSel = guiFactory.doButton2(tmpSetRow,
		                                  ' s ',
			                              Callback(setToolsLib.selectSetObjects,self,i),
		                                  'Select the set objects')
				

			tmpName = MelTextField(tmpSetRow, w = 100,ut = 'cgmUIReservedTemplate', text = b)
			
			tmpName(edit = True,
			        ec = Callback(setToolsLib.updateSetName,self,tmpName,i)	)
			

			tmpAdd = guiFactory.doButton2(tmpSetRow,
			                               '+',
			                               Callback(setToolsLib.addSelected,self,i),
			                               'Add selected  to the set')
			tmpRem= guiFactory.doButton2(tmpSetRow,
			                             '-',
			                             Callback(setToolsLib.removeSelected,self,i),
			                             'Remove selected  to the set')
			tmpKey = guiFactory.doButton2(tmpSetRow,
			                              'k',
			                              Callback(setToolsLib.keySet,self,i),			                              
			                              'Key set')
			tmpPurge = guiFactory.doButton2(tmpSetRow,
			                                'd',
			                                Callback(setToolsLib.deleteCurrentSetKey,self,i),			                              			                                
			                                'delete set key')	
			mc.formLayout(tmpSetRow, edit = True,
			              af = [(tmpActive, "left", 4),
			                    (tmpPurge,"right",2)],
			              ac = [(tmpSel,"left",0,tmpActive),
			                    (tmpName,"left",2,tmpSel),
			                    (tmpName,"right",4,tmpAdd),
			                    (tmpAdd,"right",2,tmpRem),
			                    (tmpRem,"right",2,tmpKey),
			                    (tmpKey,"right",2,tmpPurge)])
			
			MelSpacer(tmpSetRow, w = 2)
			
			#Build pop up for text field
			popUpMenu = MelPopupMenu(tmpName,button = 3)
			qssMenu = MelMenuItem(popUpMenu,
			                    label = "<<<%s>>>"%b,
			                    enable = False)
			
			qssState = False
			Set = SetFactory(b)
			qssState = Set.qssState
			qssMenu = MelMenuItem(popUpMenu,
			                      label = 'Qss',
			                      cb = qssState,
			                      c = Callback(setToolsLib.toggleQssState,self,i))
			
			categoryMenu = MelMenuItem(popUpMenu,
			                           label = 'Type:',
			                           sm = True)
			
			for n in 'none','modeling','anim':
				MelMenuItem(categoryMenu,
				            label = n)	
				
			MelMenuItem(popUpMenu ,
		                label = 'Copy Set',
		                c = Callback(setToolsLib.copySet,self,i))
			
			MelMenuItem(popUpMenu ,
		                label = 'Purge',
		                c = Callback(setToolsLib.purgeSet,self,i))
			
			MelMenuItemDiv(popUpMenu)
			MelMenuItem(popUpMenu ,
		                label = 'Delete',
		                c = Callback(setToolsLib.deleteSet,self,i))	
		
		
		
			
		
		NewSetRow = guiFactory.doButton2(MainForm,
		                                    'Create Set',
		                                    lambda *a:setToolsLib.createSet(self),
		                                    'Create new buffer from selected buffer')	
			
		SetMasterForm(edit = True,
		                 af = [(SetListColumn,"top",0),
		                       (SetListColumn,"left",0),
		                       (SetListColumn,"right",0),
		                       (SetListColumn,"bottom",0)])
		                 
		MainForm(edit = True,
		         af = [(SetHeader,"top",0),
		               (SetHeader,"left",0),
		               (SetHeader,"right",0),
		               (HelpInfo,"left",0),
		               (HelpInfo,"right",0),
		               (AllSetsRow,"left",0),
		               (AllSetsRow,"right",0),
		               (SetListScroll,"left",0),
		               (SetListScroll,"right",0),
		               (NewSetRow,"left",4),
		               (NewSetRow,"right",4),
		               (NewSetRow,"bottom",4)],
		         ac = [(HelpInfo,"top",0,SetHeader),
		               (AllSetsRow,"top",2,HelpInfo),
		               (SetListScroll,"top",2,AllSetsRow),
		               (SetListScroll,"bottom",0,NewSetRow)],
		         attachNone = [(NewSetRow,"top")])	
		




