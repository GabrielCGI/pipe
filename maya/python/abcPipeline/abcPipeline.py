import abcPipelineExport as ppEx
reload(ppEx)
exportAnimGuiCls = ppEx.exportAnimGuiCls()
exportAnimGuiCls.show()
list =  ppEx.listCharRef()
exportAnimGuiCls.updateCharList(list)

#import abcPipelineImport as ppIm
#reload(ppIm)
#ppIm.importAnim()

import abcPipelineTools as ppTools
reload(ppTools)
ppTools.createNewAsset()