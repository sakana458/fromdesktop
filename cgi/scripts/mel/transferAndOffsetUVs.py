# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
## Copyright
"""
Copyright (C) 2000-2013 Digital Frontier Inc. All rights reserved.
All source code, statements, computer programs and related files
(hereafter known as “program data”) are property of Digital Frontier Inc.
(hereafter known as “DF”). Unauthorized duplication and distribution,
regardless of purpose or format, is forbidden by Japanese and international
law. DF is prepared to pursue legal action against anyone found
to be committing such acts.
"""

## Description
"""
polygonメッシュのUVをTransferし、書くUVシェルの大きさ毎にオフセットします。
下記のコマンドをscriptEditorのpythonタブに入力して実行するとGUIが起動します。
import transferAndOffsetUVs as uv
a = uv.Main()
"""
#------------------------------------------------------------------------------

__author__ = 'nozawa2'
__date__ = '04 April 2015'
__modified__ = '16 April 2015'
__ver__ = '1.4'
from maya import cmds, OpenMaya
import pymel.core as pm
from functools import partial
import random



class CalcUVShell:
    def __init__(self):
        pass


    def getMinMax(self):

        selList   = OpenMaya.MSelectionList()
        OpenMaya.MGlobal.getActiveSelectionList( selList )
        dagPath   = OpenMaya.MDagPath()
        cmpnt     = OpenMaya.MObject()
        selList.getDagPath(0, dagPath, cmpnt)
        iter      = OpenMaya.MItSelectionList( selList )
        uvShellIds = OpenMaya.MIntArray()

        umin = 10000.0
        umax = -10000.0
        vmin = 10000.0
        vmax = -10000.0

        while not iter.isDone():
            iter.getDagPath(dagPath, cmpnt)
            meshFn    = OpenMaya.MFnMesh(dagPath)
            if dagPath.hasFn(OpenMaya.MFn.kMesh):

                index = OpenMaya.MFnSingleIndexedComponent(cmpnt)

                indexArray = OpenMaya.MIntArray()
                index.getElements( indexArray )

                u = 0.0
                v = 0.0
                uUtil = OpenMaya.MScriptUtil()
                vUtil = OpenMaya.MScriptUtil()
                uPtr = uUtil.asFloatPtr()
                vPtr = vUtil.asFloatPtr()

                sutil = OpenMaya.MScriptUtil()
                sutil.createFromInt(0)
                uint = sutil.asUintPtr()
                meshFn.getUvShellsIds(uvShellIds, uint)

                posArray = []
                centArray = []
                posDict = {}
                for i in indexArray:
                    meshFn.getUV(i, uPtr, vPtr)
                    u = OpenMaya.MScriptUtil.getFloat(uPtr)
                    v = OpenMaya.MScriptUtil.getFloat(vPtr)
                    if u < umin : umin = u
                    if u > umax : umax = u
                    if v < vmin : vmin = v
                    if v > vmax : vmax = v

            iter.next()
        return (umin, umax, vmin, vmax)


calc = CalcUVShell()

class Main:

    def __init__(self):
        self.gui()
        pass

    """
        実行処理
    """
    def doit(self, *argvs):

        sels = cmds.ls(sl=1)
        alluvs = cmds.polyListComponentConversion(sels, tuv=1)
        if self.topoCheck(sels):
            self.transferUVs(sels)
            cmds.select(cmds.polyListComponentConversion(sels[0], tuv=1))
            umin, umax, vmin, vmax = calc.getMinMax()
            values = self.uvField.getValue()
            space = self.space.getValue()
            countU = values[0]
            countV = values[1]
            interval = space[0]

            select = self.mode.getSelect()
            direction = 'U'
            if select != 1:
                direction = 'V'

            select = self.dirc.getSelect()
            dirc = 1
            if select != 1:
                dirc = -1

            lengthU = umax - umin + interval
            lengthV = vmax - vmin + interval
            j = 0
            iCnt = 0
            maxShellCount = self.shellCount.getValue1()
            values = []
            ## get uv positions to move
            for i in range(len(sels)):
                cur = i+1

                uvalue = lengthU*iCnt
                vvalue = lengthV*iCnt

                if direction == 'U':
                    if j==0:
                        values.append((uvalue*dirc, -lengthV*j))
                    else:
                        values.append(((uvalue-lengthU)*dirc, -lengthV*j))
                    if cur % countU == 0 and i != 0:
                        j += 1
                        iCnt = 0
                else:
                    if j==0:
                        values.append((lengthU*j, -vvalue*dirc))
                    else:
                        values.append((lengthU*j, (-vvalue+lengthV)*dirc))
                    if cur % countV == 0 and i != 0:
                        j += 1
                        iCnt = 0

                iCnt += 1

            shuffled = []
            origin = values[0]
            if self.shuffleCB.getValue1() and not self.useOverlap.getValue1():
                random.shuffle(values)

            ## move uvs
            for i in range(len(sels)):
                v = i
                if self.useOverlap.getValue1():
                    v = i % maxShellCount
                    if self.shuffleCB.getValue1() and i>0:
                        v = random.randint(0, maxShellCount-1)

                if i == 0:
                    self.offsetUVs(sels[i], origin[0], origin[1])
                else:
                    self.offsetUVs(sels[i], values[v][0], values[v][1])

            cmds.select(alluvs)
            if self.fitCB.getValue1():
                cmds.polyMultiLayoutUV(lm=1, sc=2, rbf=0, fr=1, ps=0.2,
                                       l=0, psc=0, su=1, sv=1, ou=0, ov=0)

            if self.adjustCB.getValue1():
                cmds.polyMultiLayoutUV(lm=0, sc=1, rbf=0, fr=1, ps=0.05,
                                       l=0, psc=0, su=1, sv=1, ou=0, ov=0)

            cmds.select(sels)
        else:
            pm.warning('There are wrong topology object. please check selected objects')

    """
        guiを表示する
    """
    def gui(self):
        if pm.window('transferAndOffsetUVsGUI', exists=True):
            pm.deleteUI('transferAndOffsetUVsGUI', window=True)

        window = pm.window('transferAndOffsetUVsGUI',
                             title='transferAndOffsetUVs v%s' % __ver__,
                             widthHeight=(200, 55) )
        baseLayout = pm.autoLayout()
        with baseLayout:
            optLayout = pm.autoLayout(orientation='horizontal')
            with optLayout:
                self.uvField = pm.intFieldGrp(l='UV', nf=2, cw3=[20,25,25],
                                        v1=6, v2=6)

                self.space = pm.floatFieldGrp(l='space', cw2=(30,50), pre=3, v1=0.01)

                onc = partial(self.isOverlapEnabled, 1)
                ofc = partial(self.isOverlapEnabled, 0)
                self.useOverlap = pm.checkBoxGrp(l='overlap', v1=0, cw2=(40,50)
                                             , onCommand1=onc, offCommand1=ofc)
                self.shellCount = pm.intFieldGrp(l='max shell count', cw2=(80,35),
                                                 en=0, v1=4)

            modeLayout = pm.autoLayout(orientation='horizontal')
            with modeLayout:
                self.mode = pm.radioButtonGrp(la2=['U','V'], nrb=2,cw3=[30,25,25],
                                        l='mode',
                                        sl=1)

                self.dirc = pm.radioButtonGrp(la2=['+','-'], nrb=2,cw3=[45,25,25],
                                        l='direction',
                                        sl=1)
                self.adjustCB = pm.checkBoxGrp(l='Adjust', v1=0, cw2=(35,20))
                self.fitCB = pm.checkBoxGrp(l='Fit', v1=0, cw2=(20,20))
                self.shuffleCB = pm.checkBoxGrp(l='Shuffle', v1=0, cw2=(40,20))


            modeLayout.attachNone(self.adjustCB, 'right')
            modeLayout.attachNone(self.fitCB, 'right')
            modeLayout.attachNone(self.shuffleCB, 'right')

            with pm.autoLayout(orientation='horizontal'):

                cmd = partial(self.calc)
                pm.button('calc', c=cmd)
                cmd = partial(self.doit)
                pm.button('run', c=cmd)


        optLayout.attachNone(self.uvField, 'right')
        optLayout.attachNone(self.space, 'right')
        optLayout.attachNone(self.useOverlap, 'right')
        optLayout.attachNone(self.shellCount, 'right')
        baseLayout.attachNone(optLayout, 'bottom')
        baseLayout.attachNone(modeLayout, 'bottom')

        pm.showWindow( window )
        window.setWidthHeight([380, 100])


    def isOverlapEnabled(self, stat, value):
        self.shellCount.setEnable(value)


    def calc(self, value):
        selected = cmds.ls(sl=1)
        ls = cmds.polyListComponentConversion(selected[0], tuv=1)
        cmds.select(ls)

        space = self.space.getValue()
        interval = space[0]
        umin, umax, vmin, vmax = calc.getMinMax()
#         print umin, umax, vmin, vmax
        lengthU = umax - umin + interval
        lengthV = vmax - vmin + interval
        vlaues = [1 / lengthU, 1 / lengthV]

        self.uvField.setValue1(vlaues[0])
        self.uvField.setValue2(vlaues[1])
        cmds.select(selected)

    """
        uvをoffsetする
        @param[in] <str>obj オブジェクト名
        @param[in] <float>uValue U方向の移動量
        @param[in] <float>vValue V方向の移動量
        @param[in] <float>interval 隙間の広さ
        @retval None
    """
    def offsetUVs(self, obj, uValue, vValue, interval=0.0):
        cmds.select(cmds.polyListComponentConversion(obj, tuv=1))
        cmds.polyEditUVShell( relative=True,
                              uValue= uValue,
                              vValue= vValue)

    """
        uvをtransferする
        @param[in] <list>objects 対象のオブジェクトのグループ
        @retval None
    """
    def transferUVs(self, objects):
        for obj in objects:
            if obj != objects[0]:
                cmds.polyTransfer(obj, ao=objects[0], uv=1, ch=0)

    #==========================================================================#
    """
        選択したオブジェクトの頂点数を調べる。
        @param[in] <list>objects 対象のオブジェクトのグループ
        @retval True 頂点数が全て一致していた場合
        @retval False  一つでも頂点数が一致しない物が含まれている場合
    """
    def topoCheck(self, objects):
        checkedObjs = [cmds.polyEvaluate(o, v=1) for o in objects]
        if len(list(set(checkedObjs))) != 1:
            return False
        else:
            return True

    #==========================================================================#






#------------------------------------------------------------------------------
# EOF
#------------------------------------------------------------------------------
