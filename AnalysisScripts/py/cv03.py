#!/usr/bin/python
#
# May 2013, rkwee
## -------------------------------------------------------------------------------
import ROOT, sys, glob, os
from ROOT import *
import helpers
from helpers import *
## -------------------------------------------------------------------------------
def cv03():

    print 'run cv03 : losses on collmator Danieles script'

    debug = False

    path  = workpath + 'HL-LHC-Collimation/AnalysisScripts/C/danielesExample/forRegina/'

    f1    = path + 'LPI_BLP_out.s_total.dat'
    f2    = path + 'coll_summary_cleaned.dat'
    f3    = path + 'CollPositions.V6503.cry.dat'
    f4    = path + 'FirstImpacts.dat_total.dat'

    path  = '/afs/cern.ch/work/r/rkwee/public/sixtrack_example/clean_input/' 
    f1    = path + 'LPI_BLP_out.s'
    f2    = path + 'coll_summary.dat'
    f3    = path + 'CollPositions.b1.dat'
    f4    = path + 'FirstImpacts.dat'

    path  = '/afs/cern.ch/work/r/rkwee/HL-LHC/runs/exampleRuns/'
    f1    = path + 'LPI_BLP_out_merged.s'
    f2    = path + 'coll_summary_merged.dat'
    f3    = source_dir + 'CollPositions.b1.dat'
    f4    = path + 'FirstImpacts_merged.dat'


    check_npart(path,'_merged')
    #return

    rel = '_example_batch'

    # loss positions
    losses = []
   
    with open(f1) as myfile:
        
        for line in myfile:
            
            line  = line.rstrip()
            
            losses += [float(line.split()[2])]


    names_sum, nabs, length = [],[],[]
    
    with open(f2) as myfile:
        for line in myfile:
            
            line = line.rstrip()
            
            if line.count("nabs"):
                continue

            names_sum  += [ line.split()[1] ]
            nabs   += [ float(line.split()[3]) ]
            length += [ float(line.split()[6]) ]


    names_pos, coll_pos = [],[]
    
    with open(f3) as myfile:

        for line in myfile:

            line = line.rstrip()

            if line.count("Pos"):
                continue

            names_pos  += [ line.split()[1] ]
            coll_pos   += [ float(line.split()[2]) ]


    # -- plot 
    cv = TCanvas( 'cv_ap', 'cv_ap', 1200, 700)
    #cv.SetRightMargin(0.12)

    pad_l = TPad("pad_l","",0,0,1,1)
    pad_l.Draw()
    pad_l.cd()

    YurMin, YurMax = 1.2e-6, 3.

    # -- the number of lines in FirstImpact-1 (for header) is the total number of particles hitting a collimator
    maxval = file_len(f4)-1

    length_LHC = 26659
    nbins, xmin, xmax = 10*length_LHC,0., length_LHC

    coll_loss = TH1F("coll_loss","coll_loss",nbins, xmin, xmax)
    cold_loss = coll_loss.Clone("cold_loss")
    warm_loss = coll_loss.Clone("warm_loss")

    xtitle = 's [m]'
    ytitle = "losses"

    coll_loss.SetLineWidth(2)
    coll_loss.SetLineColor(kBlack)
    warm_loss.SetLineColor(kOrange)
    cold_loss.SetLineColor(kBlue)

    meter  = range(10)
    n_warm = len(warm)
    k_warm = [2*k for k in range(n_warm/2)]

    f1_nlines = len(losses)
    f2_nlines = len(names_sum)
    f3_nlines = len(names_pos)

    # -- cold and warm losses for 10th of 1 meter
    for j in range(10):                                                                                                              
        for i in range(f1_nlines):
            for k in k_warm:
                
                if losses[i] >= warm[k] and losses[i] <= warm[k+1]:
                    warm_loss.Fill(losses[i])                                                                   
                if k<n_warm-1 and losses[i] >= warm[k+1] and losses[i] <= warm[k+2]:
                    cold_loss.Fill(losses[i])                                                 

    # -- losses on collimator
    # f2_nlines = 0 
    for i in range(f2_nlines):

        for j in range(f3_nlines):

            if names_sum[i] == names_pos[j]:

                kval = int(nabs[i]/length[i])
                
                for k in range(kval):
                    
                    coll_loss.Fill(coll_pos[j])                


    pad_l.SetLogy(1)
    coll_loss.GetXaxis().SetTitleOffset(.9)
    coll_loss.GetYaxis().SetTitleOffset(1.06)
    coll_loss.GetXaxis().SetTitle(xtitle)
    coll_loss.GetYaxis().SetTitle(ytitle)
    coll_loss.Scale(1.0/maxval)
    cold_loss.Scale(1.0/maxval)
    warm_loss.Scale(1.0/maxval)
    coll_loss.GetYaxis().SetRangeUser(YurMin, YurMax)

    coll_loss.Draw('hist')
    cold_loss.Draw('same')
    warm_loss.Draw('same')

    lx, ly = TLine(),TLine()
    lx.SetLineWidth(2)
    lx.SetLineStyle(3)
    lx.DrawLine(0,1,26985,1)

    # x1, y1, x2, y2a
    thelegend = TLegend(0.2, 0.7, 0.24, 0.8) 
    thelegend.SetFillColor(0)
    thelegend.SetLineColor(0)
    thelegend.SetTextSize(0.035)
    thelegend.SetShadowColor(10)
    thelegend.AddEntry(coll_loss,'losses on collimators', "L")
    thelegend.AddEntry(cold_loss,'cold losses', "L")
    thelegend.AddEntry(warm_loss,'warm losses', "L")
    thelegend.Draw()

    pname  = wwwpath
    pname += 'losses'+rel+'.png'
    cv.Print(pname)

def check_npart(thispath,appendix):

    index = 1
    
    # l = sum_npart(fname,index)
    #    print("npart of " + fname + " is " + str(l))    

    # ----

    # fname = thispath + "tracks2.dat"
    index = 0
    
    #l = count_npart(fname,index)
    #print("npart of " + fname + " is " + str(l))    

    # ----
    fname = thispath + "survival"+appendix+".dat"
    index = 1
    
    l = count_npart(fname,index)
   
    print("npart of " + fname + " is " + str(l))    

    # ----
    fname = thispath + "LPI_BLP_out"+appendix+".s"
    index = 1
    
    l = count_npart(fname,index)
   
    print("npart of " + fname + " is " + str(l))    
    # ----

    fname = thispath + "FirstImpacts"+appendix+".dat"
    index = 0
    
    ll = count_npart(fname,index)
    print("npart of " + fname + " is " + str(ll))

    # ----
