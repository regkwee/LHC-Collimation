#!/usr/bin/python
#
# reweights by pressure profile 6.5 TeV
# write rootfile with 2d histos flat and reweighted
# from 4 TeV version cv70

# Oct 16
#
# R Kwee, 2016
# 
# ---------------------------------------------------------------------------------
import ROOT, sys, glob, os, math, helpers
from ROOT import *
from array import array
from fillTTree import *
from fillTTree_dict import generate_sDict
from helpers import makeTGraph, mylabel, wwwpath, thispath
import cv79
from cv79 import pData
# --------------------------------------------------------------------------------
def resultFileBG(k,rel):
    n = os.path.join(os.path.dirname(k),"results_pressure2015_"+rel+k.split('/')[-1])
    return  n
# --------------------------------------------------------------------------------
def cv86():
    datafile = '/Users/rkwee/Documents/RHUL/work/HL-LHC/runs/TCT/hilumi_ir1_hybrid_b2_exp_20MeV_nprim5315000_30'
    tag  = '_BH_HL_tct5inrdB2_20MeV'

    datafile = thispath + 'hilumi_ir1_hybrid_b2_exp_20MeV_nprim5001000_30'
    tag =  '_BH_HL_tct5otrdB2_20MeV'

    bbgFile = datafile + ".root"
    print "Opening", bbgFile

    nprim = float(bbgFile.split('nprim')[-1].split('_')[0])
    rfile = TFile.Open(bbgFile, "READ")
    tBBG = rfile.Get("particle")
    yrel = ''
    print tBBG
    sDict = generate_sDict(tag, nprim, tBBG, yrel)

    # -- small version of fillTTree
    sk = []
    for skey in sDict.keys():

        if skey.count("Sel"): continue
        elif skey.count("Neg"): continue
        elif skey.count("Pos"): continue
        elif skey.count("Z"): continue
        elif skey.count("Neu_"): continue
        elif skey.count("Char"): continue
        elif skey.count("Plus") or skey.count("Minus"): continue
        elif skey.split(tag)[0].endswith("0") or skey.count("XY"): continue
        elif skey.count("Pio") or skey.count("Kao"): continue

        # for testing!!
        if not skey.startswith("EkinAll"): continue

        sk += [skey]
        
        print "histogram ", len(sk)+1, "."*33, skey

    for j,skey in enumerate(sk):
        print "Now on #",j,">"*5, skey


        # -- x axis, value
        particleTypes = sDict[skey][0]
        hname         = skey
        xnbins        = sDict[skey][2]
        xmin          = sDict[skey][3]
        xmax          = sDict[skey][4]
        mt            = tBBG
        print xnbins, xmin, xmax, "xnbins, xmin, xmax"
        var = ''
        energyweight = ''
        enCut = ' energy_ke > 0.02 '
        if skey.startswith("Ekin"):
            xaxis = getXLogAxis(xnbins, xmin, xmax)
            var = "energy_ke"
            
        elif hname.startswith("Rad"):
            binwidth = xmax/xnbins
            xaxis = [i*binwidth for i in range(xnbins+1)]
            var = '(TMath::Sqrt(x*x + y*y))'
            if skey.count("En"): energyweight = "energy_ke * "

        elif hname.startswith("Phi"):
            binwidth = (xmax-xmin)/xnbins
            xaxis = [xmin+i*binwidth for i in range(xnbins+1)]
            var = '(TMath::ATan2(y,x))'
            if skey.count("En"): energyweight = "energy_ke * "

        if not particleTypes[0].count('ll'):
            pcuts = [ 'particle ==' + p for p in particleTypes  ]
            pcut  = '||'.join(pcuts)
            cuts += ['('+ pcut + ')']

        # -- y axis, weigths
        nbins, xmin, xmax =  250, 0., 250e2
        #hist = TH1F(skey, skey, nbins, xmin, xmax)
        hname4 = skey + "tct4"
        hist4 = TH1F(hname4, hname4, xnbins, array('d', xaxis))
        hname5 = skey + "tct5"
        hist5 = TH1F(hname5, hname5, xnbins, array('d', xaxis))


        tct5Cut = "(z_interact > 211.79e2 && z_interact <= 212.79e2) ||  (z_interact <= 214.79e2 && z_interact > 213.79e2)"
        tct4Cut = "(z_interact > 132.6e2 && z_interact <= 133.6e2) ||  (z_interact > 130.97e2 && z_interact <= 131.97e2)"
        tct4a = 130.97e2
        tct4b = tct4a +1e2
        tct4c = 132.6e2
        tct4d = tct4c + 1e2
        tct5a = 211.79e2
        tct5b = tct5a+1e2
        tct5c = 213.79e2
        tct5d = tct5c+1e2


        tct4Cut = "((z_interact >= "+str(tct4a)+" && z_interact <= "+str(tct4b)+" ) || (z_interact > "+str(tct4c)+" && z_interact <= "+str(tct4d)+"))"
        tct5Cut = "((z_interact >= "+str(tct5a)+" && z_interact <= "+str(tct5b)+" ) || (z_interact > "+str(tct5c)+" && z_interact <= "+str(tct5d)+"))"
        
        cuts = [ enCut, tct4Cut ]        
        cuts = "weight * "+energyweight+"("+" && ".join(cuts) + ") "
        print "INFO: applying", cuts, "to", var, "in", hname4
        mt.Project(hname4, var, cuts)
        entries4 =hist4.GetEntries()/nprim
        print "entries  ",entries4
        cuts = [ enCut, tct5Cut ]        
        cuts = "weight * "+energyweight+"("+" && ".join(cuts) + ") "
        print "INFO: applying", cuts, "to", var, "in", hname5
        mt.Project(hname5, var, cuts)
        entries5 = hist5.GetEntries()/nprim
        int5 = hist5.Integral()
        print "entries  ",entries5, int5

        # This loop changes the Get.Entries() value by number of bins!!
        for bin in range(1,nbins+1):
            content = hist4.GetBinContent(bin)
            width   = hist4.GetBinWidth(bin)
            bcenter = hist4.GetXaxis().GetBinCenterLog(bin)
            hist4.SetBinContent(bin,bcenter*content/width)
            content = hist5.GetBinContent(bin)
            width   = hist5.GetBinWidth(bin)
            bcenter = hist5.GetXaxis().GetBinCenterLog(bin)
            hist5.SetBinContent(bin,bcenter*content/width)


        # normalised to nprim
        hist4.Scale(1./nprim)
        hist5.Scale(1./nprim)
        # --

        cv = TCanvas(skey+ 'cv',skey+ 'cv', 1400, 900)
        cv.SetLogx(1)
        cv.SetLogy(1)
        # right corner
        x1, y1, x2, y2 = 0.6, 0.75, 0.9, 0.88
        mlegend = TLegend( x1, y1, x2, y2)
        mlegend.SetFillColor(0)
        mlegend.SetFillStyle(0)
        mlegend.SetLineColor(0)
        mlegend.SetTextSize(0.035)
        mlegend.SetShadowColor(0)
        mlegend.SetBorderSize(0)
        #XurMin, XurMax = 120.e2, 218e2
        #xtitle,ytitle = "z [cm]", "entries"
        xtitle,ytitle = "E [GeV]", "dN/dlogE/TCT hit"
        hist4.GetXaxis().SetTitle(xtitle)
        hist4.GetYaxis().SetTitle(ytitle)
        #hist5.GetXaxis().SetRangeUser(XurMin, XurMax)

        hist4.SetLineColor(kTeal+3)
        hist5.SetLineColor(kRed+3)
        hist4.Draw("hist")
        hist5.Draw("histsame")

        mlegend.AddEntry(hist4, "with cut on TCT4, nentries:" + str(round(entries4,4)), "l")
        mlegend.AddEntry(hist5, "with cut on TCT5, nentries:" + str(round(entries5,4)), "l")
        mlegend.Draw()
        
        lab = mylabel(42)
        #lab.DrawLatex(0.2, 0.9, cuts)
        #lab.DrawLatex(0.2, 0.8, var)

        YurMin, YurMax = 0., 12000
        l = TLine()
        l.SetLineStyle(1)
        l.SetLineColor(kRed)
        if 0:        
            s = tct4a
            l.DrawLine(s,YurMin,s,YurMax)
            s = tct4b
            l.DrawLine(s,YurMin,s,YurMax)
            s = tct4c
            l.DrawLine(s,YurMin,s,YurMax)
            s = tct4d
            l.DrawLine(s,YurMin,s,YurMax)

            s = tct5a
            l.DrawLine(s,YurMin,s,YurMax)
            s = tct5b
            l.DrawLine(s,YurMin,s,YurMax)
            s = tct5c
            l.DrawLine(s,YurMin,s,YurMax)
            s = tct5d
            l.DrawLine(s,YurMin,s,YurMax)
        
        pname = "/Users/rkwee/Documents/RHUL/work/HL-LHC/LHC-Collimation/Documentation/ATS/HLHaloBackgroundNote/figures/HL/checkB2.pdf"
        cv.SaveAs(pname)