import maya.cmds as mc
import maya.mel as mel
import pprint
from functools import partial
import os
import time
from shutil import copyfile
#import fnmatch
import cgm.lib.pyui as pyui
#import subprocess
import re
from cgm.core import cgm_Meta as cgmMeta
from cgm.core.lib import asset_utils as ASSET
from cgm.core.tools import Project as Project
from cgm.core.mrs.lib import batch_utils as BATCH
from cgm.core import cgm_General as cgmGEN

import cgm.core.classes.GuiFactory as cgmUI
mUI = cgmUI.mUI

import cgm.core.cgmPy.path_Utils as PATHS
import cgm.images as cgmImages

mImagesPath = PATHS.Path(cgmImages.__path__[0])

#>>>======================================================================
import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
#=========================================================================


#>>> Root settings =============================================================
__version__ = "1.04.07.2020"
__toolname__ ='MRSScene'

_subLineBGC = [.75,.75,.75]

class ui(cgmUI.cgmGUI):
	'''
Animation Importer UI class.

Loads the Animation Importer UI.

| outputs AnimationImporter

example:
.. python::

	import cgm.core.mrs.Scene as SCENE
	x = SCENE.SceneUI()

	# returns loaded directory
	print x.directory

	# prints the names of all of the loaded assets
	print x.assetList
	'''

	WINDOW_NAME = 'cgmScene'
	DEFAULT_SIZE = 700, 400

	TOOLNAME = 'cgmScene'
	WINDOW_TITLE = '%s - %s'%(TOOLNAME,__version__)    

	def insert_init(self,*args,**kws):
		self.categoryList                = ["Character", "Environment", "Props"]
		self.categoryIndex               = 0

		self.optionVarProjectStore       = cgmMeta.cgmOptionVar("cgmVar_projectCurrent", varType = "string")
		self.optionVarLastAssetStore     = cgmMeta.cgmOptionVar("cgmVar_sceneUI_last_asset", varType = "string")
		self.optionVarLastAnimStore      = cgmMeta.cgmOptionVar("cgmVar_sceneUI_last_animation", varType = "string")
		self.optionVarLastVariationStore = cgmMeta.cgmOptionVar("cgmVar_sceneUI_last_variation", varType = "string")
		self.optionVarLastVersionStore   = cgmMeta.cgmOptionVar("cgmVar_sceneUI_last_version", varType = "string")
		self.showBakedStore              = cgmMeta.cgmOptionVar("cgmVar_sceneUI_show_baked", defaultValue = 0)
		self.removeNamespaceStore        = cgmMeta.cgmOptionVar("cgmVar_sceneUI_remove_namespace", defaultValue = 0)
		self.useMayaPyStore              = cgmMeta.cgmOptionVar("cgmVar_sceneUI_use_mayaPy", defaultValue = 0)
		self.categoryStore               = cgmMeta.cgmOptionVar("cgmVar_sceneUI_category", defaultValue = 0)
		self.alwaysSendReferenceFiles    = cgmMeta.cgmOptionVar("cgmVar_sceneUI_last_version", defaultValue = 0)

		## sizes
		self.__itemHeight                = 35
		self.__cw1                       = 125

		# UI elements
		self.assetList                   = None #pyui.SearchableList()
		self.animationList               = None #pyui.SearchableList()
		self.variationList               = None #pyui.SearchableList()
		self.versionList                 = None #pyui.SearchableList()
		self.queueTSL                    = None #pyui.UIList()
		self.updateCB                    = None
		self.menuBarLayout               = None
		self.uiMenu_FileMenu             = None
		self.uiMenu_ToolsMenu            = None
		self.uiMenu_OptionsMenu          = None
		self.categoryText                = None
		self.openInExplorerMB            = None
		self.openRigMB                   = None
		self.referenceRigMB              = None
		self.exportQueueFrame            = None
		self.categoryMenu                = None
		self.categoryMenuItemList        = []
		self.sendToProjectMenuItemList   = []
		self.assetRigMenuItemList        = []
		self.assetReferenceRigMenuItemList  = []
		self.sendToProjectMenu           = None

		self.project                     = None

		self.exportCommand               = ""

		self.showBakedOption             = None
		self.removeNamespaceOption       = None
		self.useMayaPyOption = None

		self.showBaked                   = False
		self.removeNamespace             = False
		self.useMayaPy                   = self.useMayaPyStore.getValue()

		self.fileListMenuItems           = []
		self.batchExportItems            = []

		self.exportDirectory             = None

		self.v_bgc                       = [.6,.3,.3]


	def post_init(self,*args,**kws):
		if self.optionVarProjectStore.getValue():
			self.LoadProject(self.optionVarProjectStore.getValue())
		else:
			mPathList = cgmMeta.pathList('cgmProjectPaths')
			self.LoadProject(mPathList.mOptionVar.value[0])

	@property
	def directory(self):
		return self.directoryTF.getValue()

	@directory.setter
	def directory(self, directory):
		self.directoryTF.setValue( directory )

	@property
	def categoryDirectory(self):
		return os.path.normpath(os.path.join( self.directory, self.category ))

	@property
	def selectedAsset(self):
		return self.assetList['scrollList'].getSelectedItem()

	@property
	def assetDirectory(self):
		return os.path.normpath(os.path.join( self.categoryDirectory, self.assetList['scrollList'].getSelectedItem() )) if self.assetList['scrollList'].getSelectedItem() else None

	@property
	def selectedAnimation(self):
		return self.animationList['scrollList'].getSelectedItem()	

	@property
	def animationDirectory(self):
		return os.path.normpath(os.path.join( self.assetDirectory, 'animation', self.animationList['scrollList'].getSelectedItem() )) if self.animationList['scrollList'].getSelectedItem() else None

	@property
	def selectedVariation(self):
		return self.variationList['scrollList'].getSelectedItem()

	@property
	def variationDirectory(self):
		return os.path.normpath(os.path.join( self.animationDirectory, self.variationList['scrollList'].getSelectedItem() )) if self.variationList['scrollList'].getSelectedItem() else None

	@property
	def selectedVersion(self):
		return self.versionList['scrollList'].getSelectedItem()

	@property
	def versionFile(self):
		return os.path.normpath(os.path.join( self.variationDirectory, self.versionList['scrollList'].getSelectedItem() )) if self.versionList['scrollList'].getSelectedItem() else None

	@property
	def exportFileName(self):
		return '%s_%s_%s.fbx' % (self.assetList['scrollList'].getSelectedItem(), self.animationList['scrollList'].getSelectedItem(), self.variationList['scrollList'].getSelectedItem())

	@property
	def category(self):
		return self.categoryList[self.categoryIndex] if len(self.categoryList) > self.categoryIndex else self.categoryList[0]

	def LoadOptions(self, *args):
		self.showBaked     = bool(self.showBakedStore.getValue())
		self.categoryIndex = int(self.categoryStore.getValue())
		self.removeNamespace = bool(self.removeNamespaceStore.getValue())
		self.useMayaPy = bool(self.useMayaPyStore.getValue())

		if self.showBakedOption:
			self.showBakedOption(e=True, checkBox = self.showBaked)
		if self.removeNamespaceOption:
			self.removeNamespaceOption(e=True, checkBox = self.removeNamespace)

		self.SetCategory(self.categoryIndex)
		self.LoadPreviousSelection()
		
		self.setTitle('%s - %s' % (self.WINDOW_TITLE, self.project.d_project['name']))

	def SaveOptions(self, *args):
		print "Saving options"
		self.showBaked = self.showBakedOption( q=True, checkBox=True ) if self.showBakedOption else False
		self.removeNamespace = self.removeNamespaceOption( q=True, checkBox=True ) if self.removeNamespaceOption else False
		self.useMayaPy = self.useMayaPyOption( q=True, checkBox=True ) if self.useMayaPyOption else False

		self.showBakedStore.setValue(self.showBaked)
		self.removeNamespaceStore.setValue(self.removeNamespace)
		self.useMayaPyStore.setValue(self.useMayaPy)

		# self.optionVarExportDirStore.setValue( self.exportDirectory )
		self.categoryStore.setValue( self.categoryIndex )
		#mc.optionVar( stringValue = [self.exportCommandStore, self.exportCommand] )

	def TagAsset(self, *args):
		pass

	def UpdateToLatestRig(self, *args):
		for obj in mc.ls(sl=True):
			myAsset = ASSET.Asset(obj)
			myAsset.UpdateToLatest()

	def SetExportSets(self, *args):
		mc.window( width=150 )
		col = mc.columnLayout( adjustableColumn=True )
		#mc.button( label='Set Bake Set', command=self.SetBakeSet )
		cgmUI.add_Button(col,'Set Bake Set', lambda *a: self.SetBakeSet())

		#mc.button( label='Set Delete Set', command=self.SetDeleteSet )
		cgmUI.add_Button(col,'Set Delete Set', lambda *a: self.SetDeleteSet())

		# mc.button( label='Set Export Set', command=self.SetExportSet )
		cgmUI.add_Button(col,'Set Export Set', lambda *a: self.SetExportSet())

		mc.showWindow()

	def SetDeleteSet(self, *args):
		sel = mc.ls(sl=True)
		deleteSet = sel[0].split(':')[-1]
		print "Setting delete set to: %s" % deleteSet 
		cgmMeta.cgmOptionVar('cgm_delete_set', varType="string").setValue(deleteSet)

	def SetBakeSet(self, *args):
		sel = mc.ls(sl=True)
		bakeSet = sel[0].split(':')[-1]
		print "Setting bake set to: %s" % bakeSet 
		cgmMeta.cgmOptionVar('cgm_bake_set', varType="string").setValue(bakeSet)

	def SetExportSet(self, *args):
		sel = mc.ls(sl=True)
		exportSet = sel[0].split(':')[-1]
		print "Setting geo set to: %s" % exportSet 
		cgmMeta.cgmOptionVar('cgm_export_set', varType="string").setValue(exportSet)

	def build_layoutWrapper(self,parent):

		_MainForm = mUI.MelFormLayout(self,ut='cgmUITemplate')

		##############################
		# Top Column Layout 
		##############################

		_directoryColumn = mUI.MelColumnLayout(_MainForm,useTemplate = 'cgmUISubTemplate') #mc.columnLayout(adjustableColumn=True)

		_imageFailPath = os.path.join(mImagesPath.asFriendly(),'cgm_project.png')
		imageRow = mUI.MelHRowLayout(_directoryColumn,bgc=self.v_bgc)

		#mUI.MelSpacer(imageRow,w=10)
		self.uiImage_ProjectRow =imageRow
		self.uiImage_Project= mUI.MelImage(imageRow,w=350, h=50)
		self.uiImage_Project.setImage(_imageFailPath)
		#mUI.MelSpacer(imageRow,w=10)	
		imageRow.layout()    

		cgmUI.add_LineSubBreak()

		_uiRow_dir = mUI.MelHSingleStretchLayout(_directoryColumn, height = 27)

		mUI.MelLabel(_uiRow_dir,l='Directory', w=100)
		self.directoryTF = mUI.MelTextField(_uiRow_dir, editable = False, bgc=(.8,.8,.8))
		self.directoryTF.setValue( self.directory )

		mUI.MelSpacer(_uiRow_dir,w=5)

		_uiRow_dir.setStretchWidget(self.directoryTF)
		_uiRow_dir.layout()

		_uiRow_export = mUI.MelHSingleStretchLayout(_directoryColumn, height = 27)
		mUI.MelLabel(_uiRow_export,l='Export Dir', w=100)
		self.exportDirectoryTF = mUI.MelTextField(_uiRow_export, editable = False, bgc=(.8,.8,.8))
		self.exportDirectoryTF.setValue( self.exportDirectory )

		mUI.MelSpacer(_uiRow_export,w=5)                      

		_uiRow_export.setStretchWidget(self.exportDirectoryTF)

		_uiRow_export.layout()

		mc.setParent(_MainForm)

		_uiRow_export(e=True, vis=False)
		_uiRow_dir(e=True, vis=False)

		##############################
		# Main Asset Lists 
		##############################
		self._assetsForm = mUI.MelFormLayout(_MainForm,ut='cgmUISubTemplate', numberOfDivisions=100) #mc.columnLayout(adjustableColumn=True)

		# Category
		_catForm = mUI.MelFormLayout(self._assetsForm,ut='cgmUISubTemplate')
		self.categoryText = mUI.MelButton(_catForm,
		                                  label=self.category,ut='cgmUITemplate',
		                                  ann='Select the asset category')

		self.categoryMenu = mUI.MelPopupMenu(self.categoryText, button=1 )
		for i,category in enumerate(self.categoryList):
			self.categoryMenuItemList.append( mUI.MelMenuItem(self.categoryMenu, label=category, c=partial(self.SetCategory,i)) )
			if i == self.categoryIndex:
				self.categoryMenuItemList[i]( e=True, enable=False)

		self.assetList = self.build_searchable_list(_catForm, sc=self.LoadAnimationList)

		pum = mUI.MelPopupMenu(self.assetList['scrollList'], pmc=self.UpdateAssetTSLPopup)
		self.renameAssetMB = mUI.MelMenuItem(pum, label="Rename Asset", command=self.RenameAsset )


		self.openInExplorerMB = mUI.MelMenuItem(pum, label="Open In Explorer", command=self.OpenAssetDirectory )
		self.openMayaFileHereMB = mUI.MelMenuItem(pum, label="Open In Maya", command=lambda *a:self.uiPath_mayaOpen( os.path.join(self.categoryDirectory, self.selectedAsset) ))


		self.openRigMB = mUI.MelMenuItem(pum, label="Open Rig", subMenu=True )
		self.referenceRigMB = mUI.MelMenuItem(pum, label="Reference Rig", subMenu=True )
		self.refreshAssetListMB = mUI.MelMenuItem(pum, label="Refresh", command=self.LoadCategoryList )



		self.assetButton = mUI.MelButton(_catForm, ut='cgmUITemplate', label="New Asset", command=self.CreateAsset)

		_catForm( edit=True, 
		          attachForm=[
		              (self.categoryText, 'top', 0), 
		                      (self.categoryText, 'left', 0), 
		                    (self.categoryText, 'right', 0), 
		                        (self.assetList['formLayout'], 'left', 0),
		                        (self.assetList['formLayout'], 'right', 0),
		                        (self.assetButton, 'bottom', 0), 
		                        (self.assetButton, 'right', 0), 
		                        (self.assetButton, 'left', 0)], 
		          attachControl=[
		                      (self.assetList['formLayout'], 'top', 0, self.categoryText),
		                    (self.assetList['formLayout'], 'bottom', 0, self.assetButton)] )


		# Animation
		_animForm = mUI.MelFormLayout(self._assetsForm,ut='cgmUISubTemplate')
		_animBtn = mUI.MelButton(_animForm,
		                         label='Animation',ut='cgmUITemplate',
		                         ann='Select the asset type', en=False)

		self.animationList = self.build_searchable_list(_animForm, sc=self.LoadVariationList)

		pum = mUI.MelPopupMenu(self.animationList['scrollList'])
		mUI.MelMenuItem(pum, label="Open In Explorer", command=self.OpenAnimationDirectory )
		mUI.MelMenuItem( pum, label="Send Last To Queue", command=self.AddLastToExportQueue )

		self.animationButton = mUI.MelButton(_animForm, ut='cgmUITemplate', label="New Animation", command=self.CreateAnimation)

		_animForm( edit=True, 
		           attachForm=[
		               (_animBtn, 'top', 0), 
		                       (_animBtn, 'left', 0), 
		                    (_animBtn, 'right', 0), 
		                        (self.animationList['formLayout'], 'left', 0),
		                        (self.animationList['formLayout'], 'right', 0),
		                        (self.animationButton, 'bottom', 0), 
		                        (self.animationButton, 'right', 0), 
		                        (self.animationButton, 'left', 0)], 
		           attachControl=[
		                       (self.animationList['formLayout'], 'top', 0, _animBtn),
		                    (self.animationList['formLayout'], 'bottom', 0, self.animationButton)] )

		# Variation
		_variationForm = mUI.MelFormLayout(self._assetsForm,ut='cgmUISubTemplate')
		_variationBtn = mUI.MelButton(_variationForm,
		                              label='Variation',ut='cgmUITemplate',
		                              ann='Select the asset variation', en=False)

		self.variationList = self.build_searchable_list(_variationForm, sc=self.LoadVersionList)

		pum = mUI.MelPopupMenu(self.variationList['scrollList'])
		mUI.MelMenuItem(pum, label="Open In Explorer", command=self.OpenVariationDirectory )
		mUI.MelMenuItem( pum, label="Send Last To Queue", command=self.AddLastToExportQueue )

		self.variationButton = mUI.MelButton(_variationForm, ut='cgmUITemplate', label="New Variation", command=self.CreateVariation)

		_variationForm( edit=True, 
		                attachForm=[
		                    (_variationBtn, 'top', 0), 
		                            (_variationBtn, 'left', 0), 
		                    (_variationBtn, 'right', 0), 
		                        (self.variationList['formLayout'], 'left', 0),
		                        (self.variationList['formLayout'], 'right', 0),
		                        (self.variationButton, 'bottom', 0), 
		                        (self.variationButton, 'right', 0), 
		                        (self.variationButton, 'left', 0)], 
		                attachControl=[
		                            (self.variationList['formLayout'], 'top', 0, _variationBtn),
		                    (self.variationList['formLayout'], 'bottom', 0, self.variationButton)] )


		# Version
		_versionForm = mUI.MelFormLayout(self._assetsForm,ut='cgmUISubTemplate')
		_versionBtn = mUI.MelButton(_versionForm,
		                            label='Version',ut='cgmUITemplate',
		                            ann='Select the asset version', en=False)

		self.versionList = self.build_searchable_list(_versionForm, sc=self.StoreCurrentSelection)

		pum = mUI.MelPopupMenu(self.versionList['scrollList'], pmc=self.UpdateVersionTSLPopup)
		mUI.MelMenuItem(pum, label="Open In Explorer", command=self.OpenVersionDirectory )
		mUI.MelMenuItem(pum, label="Reference File", command=self.ReferenceFile )
		self.sendToProjectMenu = mUI.MelMenuItem(pum, label="Send To Project", subMenu=True )		
		mUI.MelMenuItem( pum, label="Send Last To Queue", command=self.AddLastToExportQueue )
		
		self.versionButton = mUI.MelButton(_versionForm, ut='cgmUITemplate', label="Save New Version", command=self.SaveVersion)

		_versionForm( edit=True, 
		              attachForm=[
		                  (_versionBtn, 'top', 0), 
		                          (_versionBtn, 'left', 0), 
		                    (_versionBtn, 'right', 0), 
		                        (self.versionList['formLayout'], 'left', 0),
		                        (self.versionList['formLayout'], 'right', 0),
		                        (self.versionButton, 'bottom', 0), 
		                        (self.versionButton, 'right', 0), 
		                        (self.versionButton, 'left', 0)], 
		              attachControl=[
		                          (self.versionList['formLayout'], 'top', 0, _versionBtn),
		                    (self.versionList['formLayout'], 'bottom', 0, self.versionButton)] )


		self._subForms = [_catForm,_animForm,_variationForm,_versionForm]

		self.buildAssetForm()


		##############################
		# Bottom 
		##############################
		_bottomColumn    = mUI.MelColumnLayout(_MainForm,useTemplate = 'cgmUISubTemplate', adjustableColumn=True)#mc.columnLayout(adjustableColumn = True)

		mc.setParent(_bottomColumn)
		cgmUI.add_LineSubBreak()

		_row = mUI.MelHSingleStretchLayout(_bottomColumn,ut='cgmUISubTemplate',padding = 5)

		mUI.MelSpacer(_row,w=5)
		self.exportButton = mUI.MelButton(_row, label="Export", ut = 'cgmUITemplate', c=partial(self.RunExportCommand,1), h=self.__itemHeight)
		mc.popupMenu()
		mc.menuItem( l="Bake Without Export", c=partial(self.RunExportCommand,0))
		mc.menuItem( l="Export Rig", c=partial(self.RunExportCommand,3))
		mc.menuItem( l="Force Export As Cutscene", c=partial(self.RunExportCommand,2))

		mUI.MelButton(_row, ut = 'cgmUITemplate', label="Bake Without Export", c=partial(self.RunExportCommand,0), h=self.__itemHeight)
		mUI.MelButton(_row, ut = 'cgmUITemplate', label="Export Rig", c=partial(self.RunExportCommand,3), h=self.__itemHeight)
		mUI.MelButton(_row, ut = 'cgmUITemplate', label="Export Cutscene", c=partial(self.RunExportCommand,2), h=self.__itemHeight)

		mUI.MelButton(_row, ut = 'cgmUITemplate', label="Add To Export Queue", w=200, c=partial(self.AddToExportQueue), h=self.__itemHeight)

		_row.setStretchWidget(self.exportButton)

		mUI.MelSpacer(_row,w=5)

		_row.layout()

		mc.setParent(_bottomColumn)
		cgmUI.add_LineSubBreak()

		_row = mUI.MelHSingleStretchLayout(_bottomColumn,ut='cgmUISubTemplate',padding = 5)

		mUI.MelSpacer(_row,w=5)

		_row.setStretchWidget( mUI.MelButton(_row, ut = 'cgmUITemplate', label="Load Animation", c=self.LoadAnimation, h=self.__itemHeight))

		mUI.MelSpacer(_row,w=5)

		_row.layout()

		mc.setParent(_bottomColumn)
		cgmUI.add_LineSubBreak()

		self.exportQueueFrame = mUI.MelFrameLayout(_bottomColumn, label="Export Queue", collapsable=True, collapse=True)
		_rcl = mUI.MelFormLayout(self.exportQueueFrame,ut='cgmUITemplate')

		self.queueTSL = cgmUI.cgmScrollList(_rcl)
		self.queueTSL.allowMultiSelect(True)

		_col = mUI.MelColumnLayout(_rcl,width=200,adjustableColumn=True,useTemplate = 'cgmUISubTemplate')#mc.columnLayout(width=200,adjustableColumn=True)

		cgmUI.add_LineSubBreak()
		mUI.MelButton(_col, label="Add", ut = 'cgmUITemplate', command=partial(self.AddToExportQueue))
		cgmUI.add_LineSubBreak()
		mUI.MelButton(_col, label="Remove", ut = 'cgmUITemplate', command=partial(self.RemoveFromQueue, 0))
		cgmUI.add_LineSubBreak()
		mUI.MelButton(_col, label="Remove All", ut = 'cgmUITemplate', command=partial(self.RemoveFromQueue, 1))
		cgmUI.add_LineSubBreak()
		mUI.MelButton(_col, label="Batch Export", ut = 'cgmUITemplate', command=partial(self.BatchExport))
		cgmUI.add_LineSubBreak()

		_options_fl = mUI.MelFrameLayout(_col, label="Options", collapsable=True)

		_c2 = mUI.MelColumnLayout(_options_fl, adjustableColumn=True)
		self.updateCB = mUI.MelCheckBox(_c2, label="Update and Save Increment", v=False)

		_rcl( edit=True, 
		      attachForm=[
		          (self.queueTSL, 'top', 0), 
		                  (self.queueTSL, 'left', 0), 
		                    (self.queueTSL, 'bottom', 0), 
		                        (_col, 'bottom', 0), 
		                        (_col, 'top', 0), 
		                        (_col, 'right', 0)], 
		      attachControl=[
		                  (self.queueTSL, 'right', 0, _col)] )

		##############################
		# Layout form
		##############################

		_footer = cgmUI.add_cgmFooter(_MainForm)            

		_MainForm( edit=True, 
		           attachForm=[
		               (_directoryColumn, 'top', 0), 
		                       (_directoryColumn, 'left', 0), 
		                    (_directoryColumn, 'right', 0), 
		                        (_bottomColumn, 'right', 0), 
		                        (_bottomColumn, 'left', 0),
		                        (self._assetsForm, 'left', 0),
		                        (self._assetsForm, 'right', 0),
		                        (_footer, 'left', 0),
		                        (_footer, 'right', 0),
		                        (_footer, 'bottom', 0)], 
		           attachControl=[
		                       (_bottomColumn, 'bottom', 0, _footer),
		                    (self._assetsForm, 'top', 0, _directoryColumn),
		                    (self._assetsForm, 'bottom', 0, _bottomColumn)] )


	def show( self ):		
		self.setVisibility( True )


	#=========================================================================
	# Menu Building
	#=========================================================================
	def buildAssetForm(self):
		attachForm = []
		attachControl = []
		attachPosition = []

		attachedForms = []

		for form in self._subForms:
			vis = mc.formLayout(form, q=True, visible=True)
			if vis:
				attachedForms.append(form)

		for i,form in enumerate(attachedForms):
			if i == 0:
				attachForm.append( (form, 'left', 5) )
			else:
				attachControl.append( (form, 'left', 5, attachedForms[i-1]) )

			attachForm.append((form, 'top', 5))
			attachForm.append((form, 'bottom', 5))

			if i == len(attachedForms)-1:
				attachForm.append( (form, 'right', 5) )
			else:
				attachPosition.append( (form, 'right', 5, (100 / len(attachedForms)) * (i+1)) )

		self._assetsForm( edit=True, attachForm = attachForm, attachControl = attachControl, attachPosition = attachPosition)

	def build_menus(self):
		_str_func = 'build_menus[{0}]'.format(self.__class__.TOOLNAME)            
		log.info("|{0}| >>...".format(_str_func))   

		self.uiMenu_FileMenu = mUI.MelMenu( l='Projects', pmc=self.buildMenu_file)		        
		self.uiMenu_OptionsMenu = mUI.MelMenu( l='Options', pmc=self.buildMenu_options)
		self.uiMenu_ToolsMenu = mUI.MelMenu( l='Tools', pmc=self.buildMenu_tools)  
		self.uiMenu_HelpMenu = mUI.MelMenu( l='Help', pmc=self.buildMenu_help)   

	def buildMenu_help( self, *args):
		self.uiMenu_HelpMenu.clear()

		_log = mUI.MelMenuItem( self.uiMenu_HelpMenu, l="Logs:",subMenu=True)


		mUI.MelMenuItem( _log, l="Dat",
		                 c=lambda *a: self.project.log_self())

		mc.menuItem(parent=self.uiMenu_HelpMenu,
		            l = 'Get Help',
		            c='import webbrowser;webbrowser.open("https://http://docs.cgmonks.com/mrs.html");',                        
		                    rp = 'N')    
		mUI.MelMenuItem( self.uiMenu_HelpMenu, l="Log Self",
		                 c=lambda *a: cgmUI.log_selfReport(self) )

	def buildMenu_file( self, *args):
		self.uiMenu_FileMenu.clear()
		#>>> Reset Options			

		mPathList = cgmMeta.pathList('cgmProjectPaths')

		project_names = []
		for i,p in enumerate(mPathList.mOptionVar.value):
			proj = Project.data(filepath=p)
			name = proj.d_project['name']
			project_names.append(name)
			en = os.path.exists(proj.userPaths_get()['content'])
			mUI.MelMenuItem( self.uiMenu_FileMenu, en=en, l=name if project_names.count(name) == 1 else '%s {%i}' % (name,project_names.count(name)-1),
			                 c = partial(self.LoadProject,p))

		mUI.MelMenuItemDiv( self.uiMenu_FileMenu )

		mUI.MelMenuItem( self.uiMenu_FileMenu, l="MRSProject",
		                 c = lambda *a:mc.evalDeferred(Project.ui,lp=True))                         

	def buildMenu_options( self, *args):
		self.uiMenu_OptionsMenu.clear()
		#>>> Reset Options		

		self.showBakedOption = mUI.MelMenuItem( self.uiMenu_OptionsMenu, l="Show baked versions",
		                                        checkBox=self.showBaked,
		                                        c = lambda *a:mc.evalDeferred(self.SaveOptions,lp=True))
		self.removeNamespaceOption = mUI.MelMenuItem( self.uiMenu_OptionsMenu, l="Remove namespace upon export",
		                                              checkBox=self.removeNamespace,
		                                              c = lambda *a:mc.evalDeferred(self.SaveOptions,lp=True))
		self.useMayaPyOption =  mUI.MelMenuItem( self.uiMenu_OptionsMenu, l="Use MayaPy",
		                                         checkBox=self.useMayaPy,
		                                         c = lambda *a:mc.evalDeferred(self.SaveOptions,lp=True))

	def buildMenu_tools( self, *args):
		self.uiMenu_ToolsMenu.clear()
		#>>> Reset Options		

		mUI.MelMenuItem( self.uiMenu_ToolsMenu, l="Tag As Current Asset",
		                 c = lambda *a:mc.evalDeferred(self.TagAsset,lp=True))

		mUI.MelMenuItem( self.uiMenu_ToolsMenu, l="Set Export Sets",
		                 c = lambda *a:mc.evalDeferred(self.SetExportSets,lp=True))

		mUI.MelMenuItem( self.uiMenu_ToolsMenu, l="Update Selected Rigs",
		                 c = lambda *a:mc.evalDeferred(self.UpdateToLatestRig,lp=True))

		mUI.MelMenuItem( self.uiMenu_ToolsMenu, l="Remap Unlinked Textures",
		                 c = lambda *a:mc.evalDeferred(self.RemapTextures,lp=True))

	def RemapTextures(self, *args):
		import cgm.tools.findTextures as findTextures

		findTextures.FindAndRemapTextures()

	def buildMenu_category(self, *args):
		self.categoryMenu.clear()
		self.categoryMenuItemList = []

		for i,category in enumerate(self.categoryList):
			self.categoryMenuItemList.append( mUI.MelMenuItem(self.categoryMenu, label=category, c=partial(self.SetCategory,i)) )
			if i == self.categoryIndex:
				self.categoryMenuItemList[i]( e=True, enable=False)


	#####
	## Searchable Lists
	#####
	def build_searchable_list(self, parent = None, sc=None):
		_margin = 0

		if not parent:
			parent = self

		form = mUI.MelFormLayout(parent,ut='cgmUITemplate')

		rcl = mc.rowColumnLayout(numberOfColumns=2, adjustableColumn=1)

		tx = mUI.MelTextField(rcl)
		b = mUI.MelButton(rcl, label='clear', ut='cgmUISubTemplate')

		tsl = cgmUI.cgmScrollList(form)
		tsl.allowMultiSelect(False)

		if sc != None:
			tsl(edit = True, sc=sc)

		form( edit=True, attachForm=[(rcl, 'top', _margin), (rcl, 'left', _margin), (rcl, 'right', _margin), (tsl, 'bottom', _margin), (tsl, 'right', _margin), (tsl, 'left', _margin)], attachControl=[(tsl, 'top', _margin, rcl)] )

		searchableList = {'formLayout':form, 'scrollList':tsl, 'searchField':tx, 'searchButton':b, 'items':[], 'selectCommand':sc}

		tx(edit=True, tcc=partial(self.process_search_filter, searchableList))
		b(edit=True, command=partial(self.clear_search_filter, searchableList))

		return searchableList

	def process_search_filter(self, searchableList, *args):
		#print "processing search for %s with search term %s" % (searchableList['scrollList'], searchableList['searchField'].getValue())
		if not searchableList['searchField'].getValue():
			searchableList['scrollList'].setItems(searchableList['items'])
		else:
			searchTerms = searchableList['searchField'].getValue().lower().strip().split(' ')  #set(searchableList['searchField'].getValue().replace(' ', '').lower())
			listItems = []
			for item in searchableList['items']:
				hasAllTerms = True
				for term in searchTerms:
					if not term in item.lower():
						hasAllTerms = False
				if hasAllTerms:
					listItems.append(item)
			searchableList['scrollList'].setItems(listItems)

		searchableList['selectCommand']

	def clear_search_filter(self, searchableList, *args):
		print "Clearing search filter for %s with search term %s" % (searchableList['scrollList'], searchableList['searchField'].getValue())
		searchableList['searchField'].setValue("")
		selected = searchableList['scrollList'].getSelectedItem()
		searchableList['scrollList'].setItems(searchableList['items'])
		searchableList['scrollList'].selectByValue(selected)

	def SetCategory(self, index, *args):
		self.categoryIndex = index

		mc.button( self.categoryText, e=True, label=self.category )
		for i,category in enumerate(self.categoryMenuItemList):
			if i == self.categoryIndex:
				self.categoryMenuItemList[i]( e=True, enable=False)
			else:
				self.categoryMenuItemList[i]( e=True, enable=True)

		self.LoadCategoryList(self.directory)

		self.categoryStore.setValue(self.categoryIndex)
		#self.SaveOptions()

	def LoadCategoryList(self, directory="", *args):
		# p = self.GetPreviousDirectories()
		# if len(p) >= 10:
		# 	for i in range(len(p) - 9):
		# 		self.optionVarDirStore.removeIndex(0)

		# if directory not in p:
		# 	self.optionVarDirStore.append(directory)

		if directory:		
			self.directory = directory

		#self.buildMenu_file()

		# populate animation info list
		#fileExtensions = ['mb', 'ma']

		charList = []

		categoryDirectory = os.path.join(self.directory, self.category)
		if os.path.exists(categoryDirectory):
			for d in os.listdir(categoryDirectory):
				#for ext in fileExtensions:
				#	if os.path.splitext(f)[-1].lower() == ".%s" % ext :
				if d[0] == '_' or d[0] == '.':
					continue

				charDir = os.path.normpath(os.path.join(categoryDirectory, d))
				if os.path.isdir(charDir):
					charList.append(d)

		charList = sorted(charList, key=lambda v: v.upper())

		self.UpdateAssetList(charList)

		self.animationList['items'] = []
		self.animationList['scrollList'].clear()

		self.variationList['items'] = []
		self.variationList['scrollList'].clear()

		self.versionList['items'] = []
		self.versionList['scrollList'].clear()

		self.StoreCurrentSelection()

	def LoadAnimationList(self, *args):
		animList = []

		if self.categoryDirectory and self.assetList['scrollList'].getSelectedItem():
			charDir = os.path.normpath(os.path.join( self.categoryDirectory, self.assetList['scrollList'].getSelectedItem(), 'animation' ))

			if os.path.exists(charDir):
				for d in os.listdir(charDir):
					#for ext in fileExtensions:
					#	if os.path.splitext(f)[-1].lower() == ".%s" % ext :
					if d[0] == '_' or d[0] == '.':
						continue

					animDir = os.path.normpath(os.path.join(charDir, d))
					if os.path.isdir(animDir):
						animList.append(d)

		self.animationList['items'] = animList
		self.animationList['scrollList'].setItems(animList)

		self.variationList['items'] = []
		self.variationList['scrollList'].clear()

		self.versionList['items'] = []
		self.versionList['scrollList'].clear()

		self.StoreCurrentSelection()

	def LoadVariationList(self, *args):
		variationList = []

		selectedVariation = self.variationList['scrollList'].getSelectedItem()

		self.variationList['items'] = []
		self.variationList['scrollList'].clear()

		if self.categoryDirectory and self.assetList['scrollList'].getSelectedItem() and self.animationList['scrollList'].getSelectedItem():
			animationDir = self.animationDirectory

			if os.path.exists(animationDir):
				for d in os.listdir(animationDir):
					#for ext in fileExtensions:
					#	if os.path.splitext(f)[-1].lower() == ".%s" % ext :
					if d[0] == '_' or d[0] == '.':
						continue

					animDir = os.path.normpath(os.path.join(animationDir, d))
					if os.path.isdir(animDir):
						variationList.append(d)

		self.variationList['items'] = variationList
		self.variationList['scrollList'].setItems(variationList)

		self.variationList['scrollList'].selectByValue(selectedVariation)

		self.versionList['items'] = []
		self.versionList['scrollList'].clear()

		self.LoadVersionList()

		if len(self.versionList['items']) > 0:
			self.versionList['scrollList'].selectByIdx( len(self.versionList['items'])-1 )

		self.StoreCurrentSelection()

	def LoadVersionList(self, *args):
		if not self.assetList['scrollList'].getSelectedItem() or not self.animationList['scrollList'].getSelectedItem():
			return

		versionList = []
		anims = []

		# populate animation info list
		fileExtensions = ['mb', 'ma']

		if self.categoryDirectory and self.assetList['scrollList'].getSelectedItem() and self.animationList['scrollList'].getSelectedItem() and self.variationList['scrollList'].getSelectedItem():
			animDir = self.variationDirectory

			if os.path.exists(animDir):
				for d in os.listdir(animDir):
					if d[0] == '_' or d[0] == '.':
						continue

					for ext in fileExtensions:
						if os.path.splitext(d)[-1].lower() == ".%s" % ext :
							if not "_baked" in d or self.showBaked:
								anims.append(d)

		self.versionList['items'] = anims
		self.versionList['scrollList'].setItems(anims)

		self.StoreCurrentSelection()

	def LoadAnimation(self, *args):
		if not self.assetList['scrollList'].getSelectedItem():
			print "No asset selected"
			return
		if not self.animationList['scrollList'].getSelectedItem():
			print "No animation selected"
			return
		if not self.versionList['scrollList'].getSelectedItem():
			print "No version selected"
			return

		mc.file(self.versionFile, o=True, f=True, ignoreVersion=True)

	def SetAnimationDirectory(self, *args):
		basicFilter = "*"
		x = mc.fileDialog2(fileFilter=basicFilter, dialogStyle=2, fm=3)
		if x:
			self.LoadCategoryList(x[0])

	def GetPreviousDirectories(self, *args):
		if type(self.optionVarDirStore.getValue()) is list:
			return self.optionVarDirStore.getValue()
		else:
			return []

	def UpdateAssetList(self, charList):
		self.assetList['items'] = charList
		self.assetList['scrollList'].setItems(charList)

	# def GetPreviousDirectory(self, *args):
	# 	if self.optionVarLastDirStore.getValue():
	# 		return self.optionVarLastDirStore.getValue()
	# 	else:
	# 		return None

	def StoreCurrentSelection(self, *args):
		if self.assetList['scrollList'].getSelectedItem():
			self.optionVarLastAssetStore.setValue(self.assetList['scrollList'].getSelectedItem())
		#else:
		#	mc.optionVar(rm=self.optionVarLastAssetStore)

		if self.animationList['scrollList'].getSelectedItem():
			self.optionVarLastAnimStore.setValue(self.animationList['scrollList'].getSelectedItem())
		#else:
		#	mc.optionVar(rm=self.optionVarLastAnimStore)

		if self.variationList['scrollList'].getSelectedItem():
			self.optionVarLastVariationStore.setValue(self.variationList['scrollList'].getSelectedItem())
		#else:
		#	mc.optionVar(rm=self.optionVarLastVariationStore)

		if self.versionList['scrollList'].getSelectedItem():
			self.optionVarLastVersionStore.setValue( self.versionList['scrollList'].getSelectedItem() )
		#else:
		#	mc.optionVar(rm=self.optionVarLastVersionStore)

	def LoadPreviousSelection(self, *args):
		if self.optionVarLastAssetStore.getValue():
			self.assetList['scrollList'].selectByValue( self.optionVarLastAssetStore.getValue() )

		self.LoadAnimationList()

		if self.optionVarLastAnimStore.getValue():
			self.animationList['scrollList'].selectByValue( self.optionVarLastAnimStore.getValue() )

		self.LoadVariationList()

		if self.optionVarLastVariationStore.getValue():
			self.variationList['scrollList'].selectByValue( self.optionVarLastVariationStore.getValue() )

		self.LoadVersionList()

		if self.optionVarLastVersionStore.getValue():
			self.versionList['scrollList'].selectByValue( self.optionVarLastVersionStore.getValue() )


	def ClearPreviousDirectories(self, *args):		
		self.optionVarDirStore.clear()
		self.buildMenu_file()

	def CreateAsset(self, *args):
		result = mc.promptDialog(
		    title='New Asset',
		    message='Asset Name:',
		            button=['OK', 'Cancel'],
		                        defaultButton='OK',
		                        cancelButton='Cancel',
		                        dismissString='Cancel')

		if result == 'OK':
			charName = mc.promptDialog(query=True, text=True)
			charPath = os.path.normpath(os.path.join(self.categoryDirectory, charName))
			if not os.path.exists(charPath):
				os.mkdir(charPath)
				os.mkdir(os.path.normpath(os.path.join(charPath, 'animation')))

			self.LoadCategoryList(self.directory)

			self.assetList['scrollList'].selectByValue(charName)

	def CreateAnimation(self, *args):
		result = mc.promptDialog(
		    title='New Animation',
		    message='Animation Name:',
		            button=['OK', 'Cancel'],
		                        defaultButton='OK',
		                        cancelButton='Cancel',
		                        dismissString='Cancel')

		if result == 'OK':
			animName = mc.promptDialog(query=True, text=True)
			animationDir = os.path.normpath(os.path.join(self.assetDirectory, 'animation'))
			if not os.path.exists(animationDir):
				os.mkdir(animationDir)

			animPath = os.path.normpath(os.path.join(animationDir, animName))
			if not os.path.exists(animPath):
				os.mkdir(animPath)

			variationPath = os.path.normpath(os.path.join(animPath, '01'))
			if not os.path.exists(variationPath):
				os.mkdir(variationPath)

			self.LoadAnimationList()

			self.animationList['scrollList'].selectByValue( animName)
			#self.LoadAnimationList()
			self.LoadVariationList()
			#self.LoadVariationList()

			self.variationList['scrollList'].selectByValue( '01')
			#self.LoadVersionList()
			self.LoadVersionList()

			createPrompt = mc.confirmDialog(
			    title='Create?',
			    message='Create starting file?',
			                button=['Yes', 'No'],
			                    defaultButton='No',
			                    cancelButton='No',
			                    dismissString='No')

			if createPrompt == "Yes":
				self.OpenRig()
				self.SaveVersion()

	def CreateVariation(self, *args):
		lastVariation = 0
		for x in os.listdir(self.animationDirectory):
			if int(x) > lastVariation:
				lastVariation = int(x)

		newVariation = lastVariation + 1

		os.mkdir(os.path.normpath(os.path.join(self.animationDirectory, '%02d' % newVariation)))

		self.LoadVariationList()
		self.variationList['scrollList'].selectByValue('%02d' % newVariation)

		self.LoadVersionList()

	def SaveVersion(self, *args):
		animationFiles = self.versionList['items']

		animationName = self.animationList['scrollList'].getSelectedItem()
		wantedName = "%s_%s" % (self.assetList['scrollList'].getSelectedItem(), self.animationList['scrollList'].getSelectedItem())

		if len(animationFiles) == 0:
			wantedName = "%s_%02d.mb" % (wantedName, 1)
		else:
			currentFile = mc.file(q=True, loc=True)
			if not os.path.exists(currentFile):
				currentFile = "%s_%02d.mb" % (wantedName, 1)

			baseFile = os.path.split(currentFile)[-1]
			baseName, ext = baseFile.split('.')

			wantedBasename = "%s_%s" % (self.assetList['scrollList'].getSelectedItem(), self.animationList['scrollList'].getSelectedItem())
			if not wantedBasename in baseName:
				baseName = "%s_%02d" % (wantedBasename, 1)

			noVersionName = '_'.join(baseName.split('_')[:-1])
			version = int(baseName.split('_')[-1])

			versionFiles = []
			versions = []
			for item in self.versionList['items']:
				matchString = "^(%s_)[0-9]+\.m." % noVersionName
				pattern = re.compile(matchString)
				if pattern.match(item):
					versionFiles.append(item)
					versions.append( int(item.split('.')[0].split('_')[-1]) )

			versions.sort()

			if len(versions) > 0:
				newVersion = versions[-1]+1
			else:
				newVersion = 1

			wantedName = "%s_%02d.%s" % (noVersionName, newVersion, ext)

		saveFile = os.path.normpath(os.path.join(self.variationDirectory, wantedName) )
		print "Saving file: %s" % saveFile
		mc.file( rename=saveFile )
		mc.file( save=True )

		self.LoadVersionList()

	def OpenDirectory(self, path):
		os.startfile(path)

	def LoadProject(self, path, *args):
		if not os.path.exists(path):
			mel.eval('warning "No Project Set"')

		self.project = Project.data(filepath=path)
		_bgColor = self.v_bgc
		try:
			_bgColor = self.project.d_colors['project']
		except Exception,err:
			log.warning("No project color stored | {0}".format(err))

		try:self.uiImage_ProjectRow(edit=True, bgc = _bgColor)
		except Exception,err:
			log.warning("Failed to set bgc: {0} | {1}".format(_bgColor,err))

		d_userPaths = self.project.userPaths_get()

		if os.path.exists(d_userPaths['content']):
			self.optionVarProjectStore.setValue( path )

			self.LoadCategoryList(d_userPaths['content'])

			self.exportDirectory = d_userPaths['export']

			self.exportDirectoryTF.setValue( self.exportDirectory )
			# self.optionVarExportDirStore.setValue( self.exportDirectory )

			self.categoryList = self.project.d_structure['assetTypes']


			if os.path.exists(d_userPaths['image']):
				self.uiImage_Project.setImage(d_userPaths['image'])
			else:
				_imageFailPath = os.path.join(mImagesPath.asFriendly(),'cgm_project.png')
				self.uiImage_Project.setImage(_imageFailPath)

			self.buildMenu_category()

			mc.workspace( d_userPaths['content'], openWorkspace=True )

			self.LoadOptions()

		else:
			mel.eval('error "Project path does not exist"')

	def RenameAsset(self, *args):
		result = mc.promptDialog(
		    title='Rename Object',
		    message='Enter Name:',
		            button=['OK', 'Cancel'],
		                        defaultButton='OK',
		                        cancelButton='Cancel',
		                        dismissString='Cancel')

		if result == 'OK':
			newName = mc.promptDialog(query=True, text=True)
			print 'Renaming %s to %s' % (self.selectedAsset, newName)

			originalAssetName = self.selectedAsset

			# rename animations
			for animation in os.listdir(os.path.join(self.assetDirectory, 'animation')):
				for variation in os.listdir(os.path.join(self.assetDirectory, 'animation', animation)):
					for version in os.listdir(os.path.join(self.assetDirectory, 'animation', animation, variation)):
						if originalAssetName in version:
							originalPath = os.path.join(self.assetDirectory, 'animation', animation, variation, version)
							newPath = os.path.join(self.assetDirectory, 'animation', animation, variation, version.replace(originalAssetName, newName))
							os.rename(originalPath, newPath)

			# rename rigs
			for baseFile in os.listdir(self.assetDirectory):
				if os.path.isfile(os.path.join(self.assetDirectory, baseFile)):
					if originalAssetName in baseFile:
						originalPath = os.path.join(self.assetDirectory, baseFile)
						newPath = os.path.join(self.assetDirectory, baseFile.replace(originalAssetName, newName))
						os.rename(originalPath, newPath)

			# rename folder
			os.rename(self.assetDirectory, self.assetDirectory.replace(originalAssetName, newName))

			self.LoadCategoryList(self.directory)
			self.assetList['scrollList'].selectByValue( newName )

			self.LoadAnimationList()

			if self.optionVarLastAnimStore.getValue():
				self.animationList['scrollList'].selectByValue( self.optionVarLastAnimStore.getValue() )

			self.LoadVariationList()

			if self.optionVarLastVariationStore.getValue():
				self.variationList['scrollList'].selectByValue( self.optionVarLastVariationStore.getValue() )

			self.LoadVersionList()

			if self.optionVarLastVersionStore.getValue():
				self.versionList['scrollList'].selectByValue( self.optionVarLastVersionStore.getValue() )



	def OpenAssetDirectory(self, *args):
		if self.selectedAsset:
			self.OpenDirectory( os.path.join(self.categoryDirectory, self.selectedAsset) )
		else:
			self.OpenDirectory( self.categoryDirectory )

	def uiPath_mayaOpen(self,path=None):
		_res = mc.fileDialog2(fileMode=1, dir=path)
		if _res:
			log.warning("Opening: {0}".format(_res[0]))
			mc.file(_res[0], o=True, f=True, pr=True)

	def OpenAnimationDirectory(self, *args):
		self.OpenDirectory( os.path.normpath(os.path.join(self.assetDirectory, 'animation') ))

	def OpenVariationDirectory(self, *args):
		self.OpenDirectory(self.animationDirectory)

	def OpenVersionDirectory(self, *args):
		self.OpenDirectory(self.variationDirectory)

	def ReferenceFile(self, *args):
		if not self.assetList['scrollList'].getSelectedItem():
			print "No asset selected"
			return
		if not self.animationList['scrollList'].getSelectedItem():
			print "No animation selected"
			return
		if not self.versionList['scrollList'].getSelectedItem():
			print "No version selected"
			return

		filePath = self.versionFile
		mc.file(filePath, r=True, ignoreVersion=True, namespace=self.versionList['scrollList'].getSelectedItem())

	def UpdateAssetTSLPopup(self, *args):

		for item in self.assetRigMenuItemList:
			mc.deleteUI(item, menuItem=True)
		for item in self.assetReferenceRigMenuItemList:
			mc.deleteUI(item, menuItem=True)

		self.assetRigMenuItemList = []
		self.assetReferenceRigMenuItemList = []

		if self.assetDirectory:
			assetList = ASSET.AssetDirectory(self.assetDirectory)
			directoryList = assetList.GetFullPaths()

			#rigPath = #os.path.normpath(os.path.join(self.assetDirectory, "%s_rig.mb" % self.assetList['scrollList'].getSelectedItem() ))
			if len(assetList.versions) > 0:
				mc.menuItem( self.openRigMB, e=True, enable=True )
				mc.menuItem( self.referenceRigMB, e=True, enable=True )
			else:
				mc.menuItem( self.openRigMB, e=True, enable=False )
				mc.menuItem( self.referenceRigMB, e=True, enable=False )

			for i,rig in enumerate(assetList.versions):
				item = mUI.MelMenuItem( self.openRigMB, l=rig,
				                        c = partial(self.OpenRig,directoryList[i]))
				self.assetRigMenuItemList.append(item)

				item = mUI.MelMenuItem( self.referenceRigMB, l=rig,
				                        c = partial(self.ReferenceRig,directoryList[i]))
				self.assetReferenceRigMenuItemList.append(item)


	def UpdateVersionTSLPopup(self, *args):	
		for item in self.sendToProjectMenuItemList:
			mc.deleteUI(item, menuItem=True)

		self.sendToProjectMenuItemList = []

		asset = self.versionFile

		mPathList = cgmMeta.pathList('cgmProjectPaths')

		project_names = []
		for i,p in enumerate(mPathList.mOptionVar.value):
			proj = Project.data(filepath=p)
			name = proj.d_project['name']
			project_names.append(name)

			if self.project.userPaths_get()['content'] == proj.userPaths_get()['content']:
				continue

			item = mUI.MelMenuItem( self.sendToProjectMenu, l=name if project_names.count(name) == 1 else '%s {%i}' % (name,project_names.count(name)-1),
			                        c = partial(self.SendVersionFileToProject,{'filename':asset,'project':p}))
			self.sendToProjectMenuItemList.append(item)

	def SendVersionFileToProject(self, infoDict, *args):
		newProject = Project.data(filepath=infoDict['project'])

		newFilename = os.path.normpath(infoDict['filename']).replace(os.path.normpath(self.project.userPaths_get()['content']), os.path.normpath(newProject.userPaths_get()['content']))

		if os.path.exists(newFilename):
			result = mc.confirmDialog(
			    title='Destination file exists!',
			    message='The destination file already exists. Would you like to overwrite it?',
			                button=['Yes', 'Cancel'],
			                            defaultButton='Yes',
			                            cancelButton='Cancel',
			                            dismissString='Cancel')

			if result != 'Yes':
				return False

		if not os.path.exists(os.path.dirname(newFilename)):
			os.makedirs(os.path.dirname(newFilename))

		copyfile(infoDict['filename'], newFilename)

		if os.path.exists(newFilename) and os.path.normpath(mc.file(q=True, loc=True)) == os.path.normpath(infoDict['filename']):
			result = 'Cancel'
			if not self.alwaysSendReferenceFiles.getValue():
				result = mc.confirmDialog(
				    title='Send Missing References?',
				    message='Copy missing references as well?',
				                    button=['Yes', 'Yes and Stop Asking', 'Cancel'],
				                                defaultButton='Yes',
				                                cancelButton='No',
				                                dismissString='No')

			if result == 'Yes and Stop Asking':
				self.alwaysSendReferenceFiles.setValue(1)

			if result == 'Yes' or self.alwaysSendReferenceFiles.getValue():
				for refFile in mc.file(query=True, reference=True):
					newRefFilename = os.path.normpath(refFile).replace(os.path.normpath(self.project.userPaths_get()['content']), os.path.normpath(newProject.userPaths_get()['content']))
					if not os.path.exists(newRefFilename):
						if not os.path.exists(os.path.dirname(newRefFilename)):
							os.makedirs(os.path.dirname(newRefFilename))
						copyfile(refFile, newRefFilename)

			result = mc.confirmDialog(
			    title='Change Project?',
			    message='Change to the new project?',
			                button=['Yes', 'No'],
			                            defaultButton='Yes',
			                            cancelButton='No',
			                            dismissString='No')

			if result == 'Yes':
				self.LoadProject(infoDict['project'])
				self.LoadOptions()

	def SendLatestRigToProject():
		pass

	def OpenRig(self, filename, *args):
		rigPath = filename #os.path.normpath(os.path.join(self.assetDirectory, "%s_rig.mb" % self.assetList['scrollList'].getSelectedItem() ))
		if os.path.exists(rigPath):
			mc.file(rigPath, o=True, f=True, ignoreVersion=True)

	def ReferenceRig(self, filename, *args):
		rigPath = filename #os.path.normpath(os.path.join(self.assetDirectory, "%s_rig.mb" % self.assetList['scrollList'].getSelectedItem() ))
		if os.path.exists(rigPath):
			assetName = os.path.basename(os.path.dirname(rigPath))
			mc.file(rigPath, r=True, ignoreVersion=True, gl=True, mergeNamespacesOnClash=False, namespace=assetName)

	def AddLastToExportQueue(self, *args):
		if self.variationList != None:
			self.batchExportItems.append( {"category":self.category,"asset":self.assetList['scrollList'].getSelectedItem(),"animation":self.animationList['scrollList'].getSelectedItem(),"variation":self.variationList['scrollList'].getSelectedItem(),"version":self.versionList['scrollList'].getItems()[-1]} )

		self.RefreshQueueList()

	def AddToExportQueue(self, *args):
		if self.versionList['scrollList'].getSelectedItem() != None:
			self.batchExportItems.append( {"category":self.category,"asset":self.assetList['scrollList'].getSelectedItem(),"animation":self.animationList['scrollList'].getSelectedItem(),"variation":self.variationList['scrollList'].getSelectedItem(),"version":self.versionList['scrollList'].getSelectedItem()} )
		elif self.variationList != None:
			self.batchExportItems.append( {"category":self.category,"asset":self.assetList['scrollList'].getSelectedItem(),"animation":self.animationList['scrollList'].getSelectedItem(),"variation":self.variationList['scrollList'].getSelectedItem(),"version":self.versionList['scrollList'].getItems()[-1]} )

		self.RefreshQueueList()

	def RemoveFromQueue(self, *args):
		if args[0] == 0:
			idxes = self.queueTSL.getSelectedIdxs()
			idxes.reverse()

			for idx in idxes:
				del self.batchExportItems[idx-1]
		elif args[0] == 1:
			self.batchExportItems = []

		self.RefreshQueueList()

	def BatchExport(self, *args):
		if self.useMayaPy:
			#reload(BATCH)
			log.info('Maya Py!')

			bakeSetName = None
			deleteSetName = None
			exportSetName = None

			if(mc.optionVar(exists='cgm_bake_set')):
				bakeSetName = mc.optionVar(q='cgm_bake_set')    
			if(mc.optionVar(exists='cgm_delete_set')):
				deleteSetName = mc.optionVar(q='cgm_delete_set')
			if(mc.optionVar(exists='cgm_export_set')):
				exportSetName = mc.optionVar(q='cgm_export_set')                

			l_dat = []
			d_base = {'removeNamespace' : self.removeNamespace,
			          'bakeSetName':bakeSetName,
			          'exportSetName':exportSetName,
			          'deleteSetName':deleteSetName}

			for animDict in self.batchExportItems:
				# self.assetList['scrollList'].selectByValue( animDict["asset"] )
				# self.LoadAnimationList()
				# self.animationList['scrollList'].selectByValue( animDict["animation"])
				# self.LoadVariationList()
				# self.variationList['scrollList'].selectByValue( animDict["variation"])
				# self.LoadVersionList()
				# self.versionList['scrollList'].selectByValue( animDict["version"])

				#mc.file(self.versionFile, o=True, f=True, ignoreVersion=True)

				# masterNode = None
				# for item in mc.ls("*:master", r=True):
				# 	if len(item.split(":")) == 2:
				# 		masterNode = item

				# 	if mc.checkBox(self.updateCB, q=True, v=True):
				# 		rig = ASSET.Asset(item)
				# 		if rig.UpdateToLatest():
				# 			self.SaveVersion()

				# if masterNode is None:
				# 	objs = []
				# else:
				# 	objs = [masterNode]
				categoryDirectory = os.path.normpath(os.path.join( self.directory, animDict["category"] ))
				assetDirectory = os.path.normpath(os.path.join( categoryDirectory, animDict["asset"] ))
				animationDirectory = os.path.normpath(os.path.join( assetDirectory, 'animation', animDict["animation"] ))
				variationDirectory = os.path.normpath(os.path.join( animationDirectory, animDict["variation"] ))
				versionFile = os.path.normpath(os.path.join( variationDirectory, animDict["version"] ))
				
				categoryExportPath = os.path.normpath(os.path.join( self.exportDirectory, animDict["category"]))
				exportAssetPath = os.path.normpath(os.path.join( categoryExportPath, animDict["asset"]))
				exportAnimPath = os.path.normpath(os.path.join(exportAssetPath, 'animation'))                

				exportFileName = '%s_%s_%s.fbx' % (animDict["asset"], animDict["animation"], animDict["variation"])

				d = {
					'file':PATHS.Path(versionFile).asString(),
					#'objs':objs,
					'mode':-1, #Probably needs to be able to specify this
					'exportName':exportFileName,
					'animationName':animDict["animation"],
					'exportAssetPath' : PATHS.Path(exportAssetPath).split(),
					'categoryExportPath' : PATHS.Path(categoryExportPath).split(),
					'exportAnimPath' : PATHS.Path(exportAnimPath).split(),
					'updateAndIncrement' : int(mc.checkBox(self.updateCB, q=True, v=True))
				}                

				d.update(d_base)

				l_dat.append(d)



			pprint.pprint(l_dat)

			BATCH.create_Scene_batchFile(l_dat)
			return





		for animDict in self.batchExportItems:
			self.assetList['scrollList'].selectByValue( animDict["asset"] )
			self.LoadAnimationList()
			self.animationList['scrollList'].selectByValue( animDict["animation"])
			self.LoadVariationList()
			self.variationList['scrollList'].selectByValue( animDict["variation"])
			self.LoadVersionList()
			self.versionList['scrollList'].selectByValue( animDict["version"])

			mc.file(self.versionFile, o=True, f=True, ignoreVersion=True)

			masterNode = None
			for item in mc.ls("*:master", r=True):
				if len(item.split(":")) == 2:
					masterNode = item

				if mc.checkBox(self.updateCB, q=True, v=True):
					rig = ASSET.Asset(item)
					if rig.UpdateToLatest():
						self.SaveVersion()

			mc.select(masterNode)

			#mc.confirmDialog(message="exporting %s from %s" % (masterNode, mc.file(q=True, loc=True)))
			self.RunExportCommand(1)


	def RefreshQueueList(self, *args):
		self.queueTSL.clear()
		for item in self.batchExportItems:
			self.queueTSL.append( "%s - %s - %s - %s - %s" % (item["category"], item["asset"],item["animation"],item["variation"],item["version"]))

		if len(self.batchExportItems) > 0:
			mc.frameLayout(self.exportQueueFrame, e=True, collapse=False)
		else:
			mc.frameLayout(self.exportQueueFrame, e=True, collapse=True)

	# args[0]:
	# 0 is bake and prep, don't export
	# 1 is export as a regular asset
	#   - export the asset into the asset/animation directory
	# 2 is export as a cutscene 
	#   - cutscene means it adds the namespace to the 
	#   - asset and exports all of the assets into the
	#   - same directory
	# 3 is export as a rig
	#   - export into the base asset directory with
	#   - just the asset name
	def RunExportCommand(self, *args):
		categoryExportPath = os.path.normpath(os.path.join( self.exportDirectory, self.category))
		exportAssetPath = os.path.normpath(os.path.join( categoryExportPath, self.assetList['scrollList'].getSelectedItem()))
		exportAnimPath = os.path.normpath(os.path.join(exportAssetPath, 'animation'))

		d_userPaths = self.project.userPaths_get()

		if self.useMayaPy:
			#reload(BATCH)
			log.info('Maya Py!')

			bakeSetName = None
			deleteSetName = None
			exportSetName = None

			if(mc.optionVar(exists='cgm_bake_set')):
				bakeSetName = mc.optionVar(q='cgm_bake_set')    
			if(mc.optionVar(exists='cgm_delete_set')):
				deleteSetName = mc.optionVar(q='cgm_delete_set')
			if(mc.optionVar(exists='cgm_export_set')):
				exportSetName = mc.optionVar(q='cgm_export_set')                

			d = {
			'file':mc.file(q=True, sn=True),
			'objs':mc.ls(sl=1),
			'mode':args[0],
			'exportName':self.exportFileName,
			'exportAssetPath' : PATHS.Path(exportAssetPath).split(),
			'categoryExportPath' : PATHS.Path(categoryExportPath).split(),
			'exportAnimPath' : PATHS.Path(exportAnimPath).split(),
			'removeNamespace' : self.removeNamespace,
			'bakeSetName':bakeSetName,
			'exportSetName':exportSetName,
			'deleteSetName':deleteSetName,
            'animationName':self.selectedAnimation,
            'workspace':d_userPaths['content']
			}

			#pprint.pprint(d)

			BATCH.create_Scene_batchFile([d])
			return


		ExportScene(mode = args[0],
		            exportObjs = None,
		            exportName = self.exportFileName,
		            exportAssetPath = exportAssetPath,
		            categoryExportPath = categoryExportPath,
		            exportAnimPath = exportAnimPath,
		            removeNamespace = self.removeNamespace,
                    animationName = self.selectedAnimation,
                    workspace=d_userPaths['content']
		            )        

		return True





def BatchExport(dataList = []):
	_str_func = 'BatchExport'
	#cgmGEN.log_start(_str_func)
	t1 = time.time()


	for fileDat in dataList:
		_d = {}

		_d['categoryExportPath'] = PATHS.NICE_SEPARATOR.join(fileDat.get('categoryExportPath'))
		_d['exportAnimPath'] = PATHS.NICE_SEPARATOR.join(fileDat.get('exportAnimPath'))
		_d['exportAssetPath'] = PATHS.NICE_SEPARATOR.join(fileDat.get('exportAssetPath'))
		_d['exportName'] = fileDat.get('exportName')
		mFile = PATHS.Path(fileDat.get('file'))
		_d['mode'] = int(fileDat.get('mode'))
		_d['exportObjs'] = fileDat.get('objs')
		_removeNamespace =  fileDat.get('removeNamespace')
		if _removeNamespace == "False":
			_d['removeNamespace'] = False
		else:
			_d['removeNamespace'] = True

		_d['deleteSetName'] = fileDat.get('deleteSetName')
		_d['exportSetName'] = fileDat.get('exportSetName')
		_d['bakeSetName'] = fileDat.get('bakeSetName')
		_d['animationName'] = fileDat.get('animationName')
		_d['workspace'] = fileDat.get('workspace')
		_d['updateAndIncrement'] = fileDat.get('updateAndIncrement')

		log.info(mFile)
		pprint.pprint(_d)


		_path = mFile.asString()
		if not mFile.exists():
			log.error("Invalid file: {0}".format(_path))
			continue

		mc.file(_path, open = 1, f = 1)

		# if not _d['exportObjs']:
		# 	log.info(cgmGEN.logString_sub(_str_func,"Trying to find masters..."))

		# 	l_masters = []
		# 	for item in mc.ls("*:master", r=True):
		# 		if len(item.split(":")) == 2:
		# 			masterNode = item
		# 			l_masters.append(item)

		# 		#if mc.checkBox(self.updateCB, q=True, v=True):
		# 			#rig = ASSET.Asset(item)
		# 			#if rig.UpdateToLatest():
		# 				#self.SaveVersion()

		# 	if l_masters:
		# 		log.info(cgmGEN.logString_msg(_str_func,"Found..."))
		# 		pprint.pprint(l_masters)

		# 		_d['exportObjs'] = l_masters


		#if _objs:
		#    mc.select(_objs)
		ExportScene(**_d)        

	t2 = time.time()
	log.info("|{0}| >> Total Time >> = {1} seconds".format(_str_func, "%0.4f"%( t2-t1 )))         

	return

	mFile = PATHS.Path(f)

	if not mFile.exists():
		raise ValueError,"Invalid file: {0}".format(f)

	_path = mFile.asFriendly()

	log.info("Good Path: {0}".format(_path))
	"""
    if 'template' in _path:
        _newPath = _path.replace('template','build')
    else:"""
	_name = mFile.name()
	_d = mFile.up().asFriendly()
	log.debug(cgmGEN.logString_msg(_str_func,_name))
	_newPath = os.path.join(_d,_name+'_BUILD.{0}'.format(mFile.getExtension()))        

	log.info("New Path: {0}".format(_newPath))

	#cgmGEN.logString_msg(_str_func,'File Open...')
	mc.file(_path, open = 1, f = 1)

	#cgmGEN.logString_msg(_str_func,'Process...')
	t1 = time.time()

	try:
		if not blocks:
			#cgmGEN.logString_sub(_str_func,'No blocks arg')

			ml_masters = r9Meta.getMetaNodes(mTypes = 'cgmRigBlock',
			                                 nTypes=['transform','network'],
			                                 mAttrs='blockType=master')

			for mMaster in ml_masters:
				#cgmGEN.logString_sub(_str_func,mMaster)

				RIGBLOCKS.contextual_rigBlock_method_call(mMaster, 'below', 'atUtils','changeState','rig',forceNew=False)

				ml_context = BLOCKGEN.get_rigBlock_heirarchy_context(mMaster,'below',True,False)
				l_fails = []

				for mSubBlock in ml_context:
					_state =  mSubBlock.getState(False)
					if _state != 4:
						l_fails.append(mSubBlock)

				if l_fails:
					log.info('The following failed...')
					pprint.pprint(l_fails)
					raise ValueError,"Modules failed to rig: {0}".format(l_fails)

				log.info("Begin Rig Prep cleanup...")
				'''

                Begin Rig Prep process

                '''
				mPuppet = mMaster.moduleTarget#...when mBlock is your masterBlock

				if postProcesses:
					log.info('mirror_verify...')
					mPuppet.atUtils('mirror_verify')
					log.info('collect worldSpace...')                        
					mPuppet.atUtils('collect_worldSpaceObjects')
					log.info('qss...')                        
					mPuppet.atUtils('qss_verify',puppetSet=1,bakeSet=1,deleteSet=1,exportSet=1)
					log.info('proxyMesh...')
					mPuppet.atUtils('proxyMesh_verify')
					log.info('ihi...')                        
					mPuppet.atUtils('rigNodes_setAttr','ihi',0)
					log.info('rig connect...')                        
					mPuppet.atUtils('rig_connectAll')
	except Exception,err:
		log.error(err)


	t2 = time.time()
	log.info("|{0}| >> Total Time >> = {1} seconds".format(_str_func, "%0.4f"%( t2-t1 ))) 


	#cgmGEN.logString_msg(_str_func,'File Save...')
	newFile = mc.file(rename = _newPath)
	mc.file(save = 1)            





# args[0]:
# -1 is unknown mode
# 0 is bake and prep, don't export
# 1 is export as a regular asset
#   - export the asset into the asset/animation directory
# 2 is export as a cutscene 
#   - cutscene means it adds the namespace to the 
#   - asset and exports all of the assets into the
#   - same directory
# 3 is export as a rig
#   - export into the base asset directory with
#   - just the asset name

def ExportScene(mode = -1,
                exportObjs = None,
                exportName = None,
                categoryExportPath = None,
                exportAssetPath = None,
                exportAnimPath = None,
                removeNamespace = False,
                bakeSetName = None,
                exportSetName = None,
                deleteSetName = None,
                animationName = None,
                workspace = None,
                updateAndIncrement = False
                ):

	if workspace:
		mc.workspace( workspace, openWorkspace=True )

	#exec(self.exportCommand)
	import cgm.core.tools.bakeAndPrep as bakeAndPrep
	#reload(bakeAndPrep)
	import cgm.core.mrs.Shots as SHOTS
	_str_func = 'ExportScene'

	if not exportObjs:
		exportObjs = mc.ls(sl=True)

	cameras = []
	exportCams = []

	for obj in exportObjs:
		log.info("Checking: {0}".format(obj))
		if mc.listRelatives(obj, shapes=True, type='camera'):
			cameras.append(obj)
			exportCams.append( bakeAndPrep.MakeExportCam(obj) )
			exportObjs.remove(obj)

	exportObjs += exportCams

	addNamespaceSuffix = False
	exportFBXFile = False
	exportAsRig = False
	exportAsCutscene = False


	log.info("mode check...")
	if mode == -1:
		log.info("unknown mode, attempting to auto detect")
		if not exportObjs:
			exportObjs = []
			wantedSets = []
			for set in mc.ls('*%s' % exportSetName, r=True):
				if len(set.split(':')) == 2:
					ns = set.split(':')[0]
					for p in mc.ls(mc.sets(set,q=True)[0], l=True)[0].split('|'):
						if mc.objExists(p) and ns in p:
							exportObjs.append(p)
							break
				if len(set.split(':')) == 1:
					objName = set.replace('_%s' % exportSetName, '')
					if mc.objExists(objName):
						exportObjs.append(objName)

		if len(exportObjs) > 1:
			log.info("More than one export obj found, setting cutscene mode: 2")
			mode = 2
		elif len(exportObjs) == 1:
			log.info("One export obj found, setting regular asset mode: 1")
			mode = 1
		else:
			log.info("Auto detection failed. Exiting.")
			return

	if mode > 0:
		exportFBXFile = True

	if len(exportObjs) > 1 and mode != 2:
		result = mc.confirmDialog(
		    title='Multiple Object Selected',
		    message='Will export in cutscene mode, is this what you intended? If not, hit Cancel, select one object and try again.',
		            button=['Yes', 'Cancel'],
		            defaultButton='Yes',
		            cancelButton='Cancel',
		            dismissString='Cancel')

		if result != 'Yes':
			return False

		addNamespaceSuffix = True
		exportAsCutscene = True

	if mode== 2:
		addNamespaceSuffix = True
		exportAsCutscene = True
	if mode == 3:
		exportAsRig = True

	# make the relevant directories if they dont exist
	#categoryExportPath = os.path.normpath(os.path.join( self.exportDirectory, self.category))

	log.info("category path...")
	if not os.path.exists(categoryExportPath):
		os.mkdir(categoryExportPath)
	#exportAssetPath = os.path.normpath(os.path.join( categoryExportPath, self.assetList['scrollList'].getSelectedItem()))

	log.info("asset path...")

	if not os.path.exists(exportAssetPath):
		os.mkdir(exportAssetPath)
	exportAnimPath = os.path.normpath(os.path.join(exportAssetPath, 'animation'))

	if not os.path.exists(exportAnimPath):
		log.info("making export anim path...")

		os.mkdir(exportAnimPath)
		# create empty file so folders are checked into source control
		f = open(os.path.join(exportAnimPath, "filler.txt"),"w")
		f.write("filler file")
		f.close()

	if exportAsCutscene:
		log.info("export as cutscene...")

		exportAnimPath = os.path.normpath(os.path.join(exportAnimPath, animationName))
		if not os.path.exists(exportAnimPath):
			os.mkdir(exportAnimPath)

	exportFiles = []

	log.info("bake start...")

	# rename for safety
	loc = mc.file(q=True, loc=True)
	base, ext = os.path.splitext(loc)
	bakedLoc = "%s_baked%s" % (base, ext)

	mc.file(rn=bakedLoc)

	if not bakeSetName:
		if(mc.optionVar(exists='cgm_bake_set')):
			bakeSetName = mc.optionVar(q='cgm_bake_set')    
	if not deleteSetName:
		if(mc.optionVar(exists='cgm_delete_set')):
			deleteSetName = mc.optionVar(q='cgm_delete_set')
	if not exportSetName:
		if(mc.optionVar(exists='cgm_export_set')):
			exportSetName = mc.optionVar(q='cgm_export_set')    

	animList = SHOTS.AnimList()
	#find our minMax
	l_min = []
	l_max = []

	for shot in animList.shotList:
		l_min.append(min(shot[1]))
		l_max.append(max(shot[1]))

	if l_min:
		_start = min(l_min)
	else:
		_start = None

	if l_max:
		_end = max(l_max)
	else:
		_end = None

	log.info( cgmGEN.logString_sub(_str_func,'Bake | start: {0} | end: {1}'.format(_start,_end)) )

	bakeAndPrep.Bake(exportObjs,bakeSetName,startFrame= _start, endFrame= _end)


	for obj in exportObjs:			
		log.info( cgmGEN.logString_sub(_str_func,'On: {0}'.format(obj)) )

		mc.select(obj)

		assetName = obj.split(':')[0].split('|')[-1]

		exportFile = os.path.normpath(os.path.join(exportAnimPath, exportName) )

		if( addNamespaceSuffix ):
			exportFile = exportFile.replace(".fbx", "_%s.fbx" % assetName )
		if( exportAsRig ):
			exportFile = os.path.normpath(os.path.join(exportAssetPath, '{}_rig.fbx'.format( assetName )))

		bakeAndPrep.Prep(removeNamespace, deleteSetName,exportSetName)

		exportTransforms = mc.ls(sl=True)

		mc.select(exportTransforms, hi=True)		

		log.info("Heirarchy...")

		for i,o in enumerate(mc.ls(sl=1)):
			log.info("{0} | {1}".format(i,o))

		if(exportFBXFile):
			mel.eval('FBXExportSplitAnimationIntoTakes -c')
			for shot in animList.shotList:
				log.info( cgmGEN.logString_msg(_str_func, "shot..."))
				log.info(shot)
				mel.eval('FBXExportSplitAnimationIntoTakes -v \"{}\" {} {}'.format(shot[0], shot[1][0], shot[1][1]))

			#mc.file(exportFile, force=True, options="v=0;", exportSelected=True, pr=True, type="FBX export")
			log.info('Export Command: FBXExport -f \"{}\" -s'.format(exportFile))
			mel.eval('FBXExport -f \"{}\" -s'.format(exportFile.replace('\\', '/')))
			#mc.FBXExport(f= exportFile)

			if len(exportObjs) > 1 and removeNamespace:
				# Deleting the exported transforms in case another file has duplicate export names
				mc.delete(obj)
				try:
					mc.delete(exportTransforms)
				except:
					pass

	return True



def PurgeData():

	optionVarProjectStore       = cgmMeta.cgmOptionVar("cgmVar_projectCurrent", varType = "string")
	optionVarProjectStore.purge()

	optionVarLastAssetStore     = cgmMeta.cgmOptionVar("cgmVar_sceneUI_last_asset", varType = "string")
	optionVarLastAssetStore.purge()

	optionVarLastAnimStore      = cgmMeta.cgmOptionVar("cgmVar_sceneUI_last_animation", varType = "string")
	optionVarLastAnimStore.purge()

	optionVarLastVariationStore = cgmMeta.cgmOptionVar("cgmVar_sceneUI_last_variation", varType = "string")
	optionVarLastVariationStore.purge()

	optionVarLastVersionStore   = cgmMeta.cgmOptionVar("cgmVar_sceneUI_last_version", varType = "string")
	optionVarLastVersionStore.purge()

	showBakedStore              = cgmMeta.cgmOptionVar("cgmVar_sceneUI_show_baked", defaultValue = 0)
	showBakedStore.purge()

	removeNamespaceStore        = cgmMeta.cgmOptionVar("cgmVar_sceneUI_remove_namespace", defaultValue = 0)
	removeNamespaceStore.purge()

	categoryStore               = cgmMeta.cgmOptionVar("cgmVar_sceneUI_category", defaultValue = 0)
	categoryStore.purge()

	alwaysSendReferenceFiles    = cgmMeta.cgmOptionVar("cgmVar_sceneUI_last_version", defaultValue = 0)
	alwaysSendReferenceFiles.purge()