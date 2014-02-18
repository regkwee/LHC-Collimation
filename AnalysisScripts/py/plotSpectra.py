#!/usr/bin/python
#
# R Kwee-Hinzmann, 2013
# ---------------------------------------------------------------------------------
import ROOT, sys, glob, os, math, helpers
from ROOT import *
from helpers import *
from array import array
import fillTTree
from fillTTree_dict import generate_sDict
from createTTree import treeName
from plotSpectra_dict import hDict_BH_4TeV,hDict_HL_BGac, hDict_HL_BH, hDict_HL_comp,hDict_BG_4TeV,hDict_BH_3p5TeV
# ---------------------------------------------------------------------------------
zmin, zmax = 2260., 14960.
# to disable the zcut have zOn > zmax
zOn = 2e4
# ---------------------------------------------------------------------------------
def plotSpectra(bbgFile, tag):

    print "Using ...", bbgFile
    norm = float(bbgFile.split('nprim')[-1].split('_')[0])
    tBBG = TFile.Open(bbgFile).Get(treeName)
    yrel = '/TCT hit'
    sDict = generate_sDict(tag, norm, tBBG, yrel)

    rfname = fillTTree.resultFile(bbgFile)

    if rfname.count('B1') or rfname.count('b1'): Beam, beam = 'B1', 'b1'
    elif rfname.count('B2') or rfname.count('b2'): Beam, beam = 'B2','b2'
    else: Beam, beam = '', ''

    if rfname.count('20MeV'): EnCutOff = '20MeV'
    elif rfname.count('20GeV'): EnCutOff = '20GeV'
    else: print 'no energycutoff?!'

    debug = 1

    if rfname.count("BH") and not rfname.count('4TeV') and not rfname.count('3p5TeV'): 
        hDict = hDict_HL_BH
        subfolder= 'TCT/HL/nominalSettings/beamhalo/'

        if debug: print "Using HL BG format", '.'*10

    elif rfname.count("BGac"): 
        hDict = hDict_HL_BGac
        subfolder= 'TCT/HL/nominalSettings/beamgas/'
        if debug: print "Using HL BH format", '.'*10

    elif rfname.count("comp"): 
        hDict = hDict_HL_comp
        subfolder= 'TCT/HL/nominalSettings/comp/'
        if debug: print "Using HL comp format", '.'*10

    elif rfname.count('4TeV'): 
        hDict = hDict_BH_4TeV
        subfolder= 'TCT/4TeV/'+Beam+'/' + EnCutOff + '/'
        if debug: print "Using 4 TeV format", '.'*10

    elif rfname.count('BG_4TeV'): 
        hDict = hDict_BG_4TeV
        subfolder= 'TCT/4TeV/'
        if debug: print "Using 4 TeV format", '.'*10

    elif rfname.count('BG_3p5TeV'): 
        hDict = hDict_BG_3p5TeV
        subfolder= 'TCT/3p5TeV/'
        if debug: print "Using 4 TeV format", '.'*10

    elif rfname.count('beam-halo_3.5TeV-R1_D1'): 
        hDict = hDict_BH_3p5TeV
        subfolder= 'TCT/3p5TeV/'
        if debug: print "Using 4 TeV format", '.'*10


    if not os.path.exists(wwwpath + subfolder):
        print 'making dir', wwwpath + subfolder
        os.mkdir(wwwpath + subfolder)
    else: "Writing plot to ", wwwpath + subfolder

    # ---------------------------------------------------------------------------------
    print 'Opening ','.'*20, rfname
    rfile = TFile.Open(rfname)

    for hkey in hDict.keys():
      
      print "Plotting ...", hkey
      hists = []
      cv = TCanvas( 'cv'+hkey, 'cv'+hkey, 1200, 900)

      gStyle.SetPalette(1)
      gPad.SetRightMargin(1.4)
      # gPad.SetLeftMargin(-0.2)

      hList = hDict[hkey][0] 
      x1, y1, x2, y2 = hDict[hkey][1],hDict[hkey][2],hDict[hkey][3],hDict[hkey][4]
      doLogx, doLogy = hDict[hkey][5], hDict[hkey][6]
      pname = wwwpath + subfolder + hkey 
      XurMin, XurMax = hDict[hkey][7],hDict[hkey][8]
      YurMin, YurMax = hDict[hkey][9],hDict[hkey][10]
      ZurMin, ZurMax = hDict[hkey][15],hDict[hkey][16]
      doFill = hDict[hkey][11]
      lText  = hDict[hkey][12] + ' ' + Beam
      lx, ly = hDict[hkey][13],hDict[hkey][14]

      mlegend = TLegend( x1, y1, x2, y2)
      mlegend.SetFillColor(0)
      mlegend.SetFillStyle(0)
      mlegend.SetLineColor(0)
      mlegend.SetTextSize(0.035)
      mlegend.SetShadowColor(0)
      mlegend.SetBorderSize(0)
      
      for i,hname in enumerate(hList):
           hname += tag
           hists += [rfile.Get(hname)]

           if not hists[-1]:
               print "WARNING: histogram", hname," not found","!"*10
               continue

           print "INFO: ", hists[-1].GetName(), ' has ', hists[-1].GetEntries(), ' entries.'
           
           hcolor = sDict[hname][7]
           hists[-1].SetLineColor(hcolor)
           hists[-1].SetLineWidth(2)
           # if doFill:  hists[-1].SetFillColor(hcolor)
           
           norm   = sDict[hname][1]
           if norm != 1.: print 'normalising by ', norm
           #hists[-1].Scale(1./norm)

           if not i: 
               if   type(hists[-1]) == TH1F: hists[-1].Draw("HIST")
               elif type(hists[-1]) == TH2F: hists[-1].Draw("COLZ")
           else:
               if   type(hists[-1]) == TH1F: hists[-1].Draw("HISTSAME")

           prettyName = sDict[hname][6]
           mlegend.AddEntry(hists[-1],prettyName, "l")
           
           xtitle = sDict[hname][9]
           ytitle = sDict[hname][10]
        
      # ....................................
      if not hists[-1] or not hists[0]:
          continue

      if XurMin is not -1 and not type(hists[0]) == TH2F:
          hists[0].GetXaxis().SetRangeUser(XurMin, XurMax)

      if YurMin is not -1 and not type(hists[0]) == TH2F:
          hists[0].GetYaxis().SetRangeUser(YurMin, YurMax)

      if ZurMin is not -1 and type(hists[0]) == TH2F: 
          hists[0].GetZaxis().SetRangeUser(ZurMin, ZurMax)
        
      hists[0].GetYaxis().SetTitleSize(0.04)
      hists[0].GetYaxis().SetLabelSize(0.035)
      hists[0].GetXaxis().SetTitleSize(0.04)
      hists[0].GetXaxis().SetLabelSize(0.035)
      if type(hists[0]) == TH2F: 
          hists[0].GetZaxis().SetLabelSize(0.035)

      hists[0].GetXaxis().SetTitle(xtitle)
      hists[0].GetYaxis().SetTitle(ytitle)

      mlegend.Draw()
      lab = mylabel(62)
      lab.DrawLatex(lx,ly,lText)

      gPad.RedrawAxis()
      if type(hists[0]) == TH2F: 
          gPad.SetLogz(doLogx)
      else:
          gPad.SetLogx(doLogx)
          gPad.SetLogy(doLogy)
      
      print('Saving file as' + pname ) 
      cv.Print(pname + '.pdf')
      #cv.Print(pname + '.png')

# ---------------------------------------------------------------------------------
