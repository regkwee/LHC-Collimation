#!/usr/bin/python
#
#
#
# R Kwee, 2016
# 
# ---------------------------------------------------------------------------------
import ROOT, sys, glob, os, math, helpers
from ROOT import *
# get function to read the data if 14 columns are present 
from cv32 import getdata14c
import cv65
from helpers import makeTGraph, mylabel, wwwpath
# --------------------------------------------------------------------------------
# calc total interaction probability

def calc_pint_tot(energy, rho_C, rho_H, rho_O):
    # 3.5 TeV inel cross-sections proton-atom from paper
    sigma_O = 316.e-31
    sigma_C = 258.e-31
    sigma_H =  37.e-31
    sigma_tot = sigma_O + sigma_H + sigma_C

    Trev = 1./11245.
    sigma_N = 286.e-31

    # weighted mean
    #meanrho = [ (math.sqrt(rho_H[i])*sigma_H/sigma_tot + math.sqrt(rho_O[i])*sigma_O/sigma_tot + math.sqrt(rho_C[i])*sigma_C/sigma_tot)**2 for i in range(1,len(rho_O))]
    pint_tot = [ (rho_H[i]*sigma_H/Trev+rho_O[i]*sigma_O/Trev+rho_C[i]*sigma_C/Trev) for i in range(1,len(rho_O))]
    
    #pint_tot = [rho*sigma_N/Trev for rho in meanrho]
    return pint_tot

def cv66():
# --------------------------------------------------------------------------------
# density profile is given in the following format:
# densities per molecule as function of s-coordinate
# x,y,z, cx, cy, cz as function of (different s-coordinate)
# merge densities with coordinates
# note, that the source routine needs fluka units, ie *cm*!
# --------------------------------------------------------------------------------

    do4TeV = 0 # means 3.5 is off
    if do4TeV:
        energy = '4 TeV' 
        bgfile    = '/afs/cern.ch/work/r/rkwee/HL-LHC/beam-gas-sixtrack/pressure_profiles_2012/LSS1_B1_Fill2736_Final.csv'
        bgfile    = '/Users/rkwee/Documents/RHUL/work/data/4TeV/LSS1_B1_Fill2736_Final.csv'
        beamintensity = 2e14
    else:
        energy = " 3.5 TeV "
        bgfile = "/Users/rkwee/Documents/RHUL/work/HL-LHC/runs/TCT/LSS1_B1_fill_2028-sync_rad_and_ecloud.csv"
        beamintensity = 1.66e14

    print "Using", bgfile
    
    debug = 0

    data = getdata14c(bgfile)
    print 'data keys are',data.keys()
    nb_s = len(data['s'])
    print 'number of s values', nb_s

    s, rho_C, rho_H, rho_O = cv65.getAtomicRho(data)
    # --
    # calculate the scaled number

    # unscaled inf
    hname, nbins, xmin, xmax = 'muons', 2*262, 22.6, 546.6
    binw = (xmax-xmin)/nbins
    hist = TH1F(hname, hname, nbins, xmin, xmax)
    hist.Sumw2()
    hist.GetXaxis().SetTitle('s [m]')
    datafile = '/afs/cern.ch/project/lhc_mib/valBG4TeV/ir1_BG_bs_4TeV_20MeV_b1_nprim5925000_67'
    datafile = '/Users/rkwee/Documents/RHUL/work/HL-LHC/runs/TCT/ir1_BG_bs_4TeV_20MeV_b1_nprim5925000_67'
    if not do4TeV: datafile = "/Users/rkwee/Documents/RHUL/work/HL-LHC/runs/TCT/beam_gas_3.5TeV_IR1_to_arc_20MeV_100M_nprim7660649_66"

    bbgFile = datafile + ".root"

    print "Using", bbgFile
    rfile = TFile.Open(bbgFile, "READ")

    hists = []
    cnt = 0

    mt  = rfile.Get('particle')

    particleTypes = [10, 11]

    hname = 'muons_flatpressure'
    hist_flat = hist.Clone(hname)
    hist_pint = hist.Clone("pint")
    hist_pint_re = hist.Clone("pint_re")
    var = "z_interact*0.01"
    cuts = "(particle == 10 || particle == 11) && energy_ke > 0.02"
    print "INFO: applying", cuts, "to", var, "in", hname
    mt.Project(hname, var, cuts)

    # divide by binwith
    for i in range(nbins+1):
        cont = hist_flat.GetBinContent(i)
        hist_flat.SetBinContent(i,cont/binw)
        err = hist_flat.GetBinError(i)
        hist_flat.SetBinError(i,err/binw)

    Trev = 1./11245.0
    
    #    pint_tot_re = [sigma_N/Trev * rho for rho in rho_A]
    # create histogram with same axis for pint 
    pint_tot = calc_pint_tot(energy,rho_C, rho_H, rho_O)
    pint_incomingbeam = {}

    for i,spoS in enumerate(s):
        spos = float(spoS)
        if spos < 0.: 
            z = -spos
            pint_incomingbeam[z] = pint_tot[i]
            zbin = hist_pint.FindBin(z)
            hist_pint.SetBinContent(zbin, pint_incomingbeam[z])
            #       hist_pint_re.SetBinContent(zbin, pint_tot_re[i])

    # first value is for arc
    arcvalue = pint_tot[1]

    startarc = 260.
    startarcBin = hist_pint.FindBin(startarc)
    for i in range(startarcBin, nbins-1): hist_pint.SetBinContent(i,arcvalue)

    #print "Integral", hist_pint.Integral()
    #print "Integral re", hist_pint_re.Integral()
    #print "ratio hist_pint_re.Integral()/hist_pint.Integral()", hist_pint_re.Integral()/hist_pint.Integral()
    #for bin in range(1,10):
    #   ratio = hist_pint_re.GetBinContent(bin)/hist_pint.GetBinContent(bin)
    #   print "pint_re/pint", ratio
    
    nprim = float(bbgFile.split('nprim')[-1].split('_')[0]) 
    Mk = nprim/nbins
    # compute normalisation fct for each bin
    for i in range(1,nbins+1):
        m = hist_flat.GetBinContent(i)
        scale = 1e2*beamintensity * hist_pint.GetBinContent(i) * binw / Mk
        hist.SetBinContent(i,scale * m)
        if i>5 and i<10 and debug:
            pass
            print "s, m, scale, binw,beamintensity, hist_pint.GetBinContent(i), Mk", hist_pint.GetBinLowEdge(i), m, scale, binw,beamintensity, hist_pint.GetBinContent(i), Mk
            print "scale * m", hist.GetBinContent(i)
            
    cv = TCanvas( 'cv', 'cv', 1600, 900)
    cv.SetGridy(1)
    x1, y1, x2, y2 = 0.57, 0.65, 0.9, 0.88
    mlegend = TLegend( x1, y1, x2, y2)
    mlegend.SetFillColor(0)
    mlegend.SetFillStyle(0)
    mlegend.SetLineColor(0)
    mlegend.SetTextSize(0.035)
    mlegend.SetShadowColor(0)
    mlegend.SetBorderSize(0)

    ytitle = "arbitrary units"
    YurMin, YurMax = 9, 9e6
    #hist.GetYaxis().SetRangeUser(YurMin,YurMax)
    hist.SetMarkerColor(kRed)
    hist.SetLineColor(kRed)
    #hist.GetYaxis().SetTitle(ytitle)
    XurMin,XurMax = 22.6,546.
    hist.GetXaxis().SetRangeUser(XurMin,XurMax)
    hist.GetYaxis().SetRangeUser(YurMin,YurMax)
    hist.Draw("hist")
    hist_flat.Scale(1e7/nprim)
    hist_flat.Draw("histsame")

    hist_pint.SetLineColor(kGreen-3)
    hist_pint.Draw("hist")
    #hist_pint_re.Draw("histsame")
    if debug:
        ztest = 28.
        print "at ",ztest,": have pint = ",hist_pint.GetBinContent(hist_pint.FindBin(ztest)),
        print "at ",ztest,": have flat = ",hist_flat.GetBinContent(hist_flat.FindBin(ztest)),
        print "at ",ztest,": have norm = ",hist.GetBinContent(hist.FindBin(ztest)),
        #hist_pint.GetYaxis().SetTitle("interaction probability [1/m/s]")

        hist_pint.Scale(1e16)
    hist_pint.Draw("histsame")

    lg, lm = "interaction probability x10^{16} [1/s/m]", 'l'
    mlegend.AddEntry(hist_pint, lg, lm)

    lg, lm = "#mu^{#pm} [1/s/m] ", 'l'
    mlegend.AddEntry(hist, lg, lm)

    lg, lm = "#mu^{#pm} 10^{7}/m/BG int. flat pressure", 'l'
    mlegend.AddEntry(hist_flat, lg, lm)

    gPad.SetLogy(1)
    gPad.RedrawAxis()

    lab = mylabel(42)
    lab.DrawLatex(0.45, 0.9, energy)

    mlegend.Draw()

    pname = wwwpath + 'TCT/beamgas/pressure_profiles_2012/flatvsprofile.pdf'
    pname = "/Users/rkwee/Documents/RHUL/work/HL-LHC/LHC-Collimation/Documentation/ATS/HLHaloBackgroundNote/figures/4TeV/reweighted/muonsrates.pdf"
    if not do4TeV: pname = "/Users/rkwee/Documents/RHUL/work/HL-LHC/LHC-Collimation/Documentation/ATS/HLHaloBackgroundNote/figures/4TeV/reweighted/xcheck2011/pint2011.pdf"
    print('Saving file as ' + pname ) 
    cv.Print(pname)

