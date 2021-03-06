#!/usr/bin/python
#
#
# rkwee, Sept 2015

import os, math, time, ROOT, sys
from ROOT import *
from optparse import OptionParser
from array import array as ar
from helpers import mylabel, mean,gitpath, stddev
from MDAnalysis_dict import vDictTCTs, vDictTCPs
## -----------------------------------------------------------------------------------
parser = OptionParser()
parser.add_option("-f", "--file", dest="filename", type="string",
                  help="Input file with TIMBER data")


(options, args) = parser.parse_args()
## -----------------------------------------------------------------------------------
debug  = 0

def stringDateToTimeStamp(sDateTime):

    # 2015-06-07 17:10:45.604
    pattern = "%Y-%m-%d %H:%M:%S"
    sStruct = time.strptime(sDateTime, pattern)

    ts = time.mktime(sStruct)
    return ts

## -----------------------------------------------------------------------------------
def dictionizeData(fname):

    #  collect data in list (actually in tDict)
    tDict = {}


    print "Creating dictionary from file", fname
    with open(fname) as myfile:
        for i,line in enumerate(myfile):

            if line.count('VARIABLE'):

                key = line.split()[-1]

                # intialise
                if key not in tDict:
                    tDict[key] = []
                    if debug: 
                        print len(tDict)
                        print 'adding' , key

            elif line.count("Value") or line.startswith('#'):
                continue

            elif len(line.split()) == 2:

                # UTC date time, human readable
                dt = line.split(',')[0].split('.')[0]

                # UTC timestamp in seconds, add shift to convert to local cern time
                ts = stringDateToTimeStamp(dt) 

                # value
                val = float(line.split(',')[-1])

                # save into list
                tDict[key] += [[ts, dt, val]]

    keys = tDict.keys() 
    if debug: print 'have data from ',len(keys),' detectors'
    return tDict
## -----------------------------------------------------------------------------------

def getkname(k):
    if k.count('.'):
        kname = k.replace('.', '_')
    else:
        kname = k

    if kname.count(":"):
        kname = kname.replace(':', '_')
    else:
        kname = k

    if kname.endswith('.csv'): kname = kname.split('.')[0]
    return kname

def legendName(k):
    legname = k.split("_")[1]

    #if k.count("BLM"): legname = "BLM_"
    if k.count("TC"): legname += ".TC" + k.split("TC")[-1].split("_LOSS")[0]
    return legname.replace("_", ".")    

## -----------------------------------------------------------------------------------

def doGraphTimeAxis(vDict, k, xarray, yarray):
  
    kname = getkname(k) 
    gr = TGraph( len(xarray), ar('d',xarray), ar('d',yarray) )
    gr.SetName('gr_' + kname )

    gr.GetXaxis().SetTimeDisplay(1)
    gr.GetXaxis().GetTimeFormatOnly() 
    gr.GetXaxis().SetTimeFormat("%H:%M:%S")
    gr.GetXaxis().SetLabelSize(0.04)
    gr.GetXaxis().SetTitle("local time")
    if k.count("BLM"): gr.GetYaxis().SetTitle("Gy/s")
    gr.GetYaxis().SetTitleOffset(0.9)
    gr.SetMarkerColor(vDict[k][0])
    gr.SetMarkerStyle(vDict[k][1])
    gr.SetMarkerSize(1.2)
  
    return gr
## -----------------------------------------------------------------------------------

def doGraphErrors( scnt, k, xarray, yarray,xErrarray, yErrarray, doShowInfo):
  
    kname = getkname(k) + str(scnt)
    gr = TGraphErrors( len(xarray), ar('d',xarray), ar('d',yarray), ar('d',xErrarray), ar('d',yErrarray) )
    gr.SetName('gr_' + kname )
    #gr.GetXaxis().SetLabelSize(0.04)
    gr.GetYaxis().SetTitleOffset(0.8)
    datalines = []

    if doShowInfo: 
        for i,x in enumerate(xarray):

            print "collsetting:", x, ", TCT signal: (", yarray[i], "+-", yErrarray[i], "), fraction:", yErrarray[i]/yarray[i]
            datalines += [ str(x) + " " + str(yarray[i]) + " " + str(yErrarray[i]) + "\n" ]

    return gr, datalines
            
## -----------------------------------------------------------------------------------
def doHistoLabels(scnt, k, xLabels, yarray):
    print "Filling histogram with yarray", yarray

    kname = 'hist_' + getkname(k) + "_" + str(scnt)
    xmin, xmax = -0.5, 5.5
    hist = TH1F(kname, kname, len(xLabels), xmin, xmax)

    if debug: print "Creating histogram", kname
    cnt = 1
    for y in yarray:

        # if y < 1e-12:
        #     cnt += 1
        #     if debug: print "want to skip", y
        #     continue
        hist.SetBinContent(cnt,y)
        cnt += 1

    # cnt = 1
    # for y in yarray:
    #     print "bin content is then", hist.GetBinContent(cnt)
    #     cnt += 1

    cnt = 1
    for xl in xLabels:
        hist.GetXaxis().SetBinLabel(cnt,xl)
        cnt += 1
        
    hist.GetXaxis().SetLabelSize(0.07)
    hist.SetMarkerSize(1.4)
    return hist
## -----------------------------------------------------------------------------------
def getPedestral(tDict, vDict, timetupel):
    #
    # returns dict with timber var as keys and corresponding 
    # averaged pedestral for time period
    # 
    #

    (dtStart, dtEnd, labText) = timetupel

    tsStart = stringDateToTimeStamp(dtStart)
    tsEnd   = stringDateToTimeStamp(dtEnd)

    pedList = []

    if debug: 
        print "Starting time", dtStart
        print "Ending time", dtEnd
    vars = vDict.keys()

    for det in vDict.keys():

        xarray, yarray = [], []
        if debug: print "timber var ", det
        detData = tDict[det]        

        for ts, dt, val in detData:
            if ts > tsEnd or ts <= tsStart: 
                continue
            yarray += [val]

        meanPedestral = mean(yarray)
        stddevPed = stddev(yarray)
        pedList  +=  [(det, [meanPedestral, stddevPed])]

    pedDict  = dict(pedList)
    if debug: print "pedDict", pedDict
    return pedDict
## -----------------------------------------------------------------------------------
def getPeaks(tDict, vDict, timetupel):
    #
    # return dict with timber var as keys and 
    # corresponding maximum value and time stamps (ts, dt, max)
    # within given time interval
    #
    #
    (dtStart, dtEnd, labText) = timetupel

    tsStart = stringDateToTimeStamp(dtStart)
    tsEnd   = stringDateToTimeStamp(dtEnd)

    peakList, peakListAll = [],[]

    if debug: 
        print "Starting time", dtStart
        print "Ending time", dtEnd
    vars = vDict.keys()

    for det in vDict.keys():

        x_ts, x_dt, yarray = [],[],[]
        if debug: print "in getPeaks:timber var ", det
        detData = tDict[det]        

        for ts, dt, val in detData:
            if ts > tsEnd or ts <= tsStart: 
                continue
            yarray += [val]
            x_ts += [ts]
            x_dt += [dt]

        if not yarray: print "No data within", dtStart," and ", dtEnd, "in ", det
        maxval = max(yarray)
        indexmax = yarray.index(maxval)
        peakList +=  [(  det,[x_ts[indexmax], x_dt[indexmax], maxval]  )]

    peakDict = dict(peakList)
    if debug: print "peakDict", peakDict

    return peakDict

## -----------------------------------------------------------------------------------
def getPeak(pDict):

    peaksList = [(det,pDict[det][2]) for det in pDict.keys()]
    if debug: print peaksList

    peaks = [pDict[det][2] for det in pDict.keys()]
    peak = max( peaks )
    for det, ts_dt_peak in pDict.iteritems():
        if debug: print "searching for peak", peak, "in ", det
        if peak in ts_dt_peak:
            return det, ts_dt_peak

## -----------------------------------------------------------------------------------
def subPedestral(tDict, vDict, pDict):

    # 
    # return dictionary with same structure as tDict but with pedestral substracted data
    # det: [ts, dt, val-ped]
    #
    # should only be applied to vDictTCTs and vDictTCPs
    tpList = []
    for det in vDict.keys():
        
        if debug: print "timber var ", det
        detData = tDict[det]        

        # pedestral substracted data
        pedSubData = []
        for ts, dt, val in detData:

            noise = pDict[det][0]
            stddev = pDict[det][1]
            noisestddev = noise-stddev
            if noisestddev > val:
                if debug: print "No signal in",det, ". Found larger noise", noise-stddev,"than value", val, "at", dt
                noise = val
            # substract pedestral, leave maximal stddev of noise.
            pedSubData += [ [ts, dt, val-(noisestddev)] ]

        if debug: print "adding data of ", det

        tpList += [[det, pedSubData]]

    return dict(tpList)
## -----------------------------------------------------------------------------------    
def doLossesVsTime(tDict, vDict, pDict, timetupel, pname, YurMin, YurMax):

    tpDict = subPedestral(tDict, vDict, pDict)

    hists = []
    graphs, graphsPed = [],[]

    ml = mylabel(42)
    ml.SetTextSize(0.06)
    X1, Y1 = 0.12, 0.88

    (dtStart, dtEnd, labText) = timetupel

    tsStart = stringDateToTimeStamp(dtStart)
    tsEnd   = stringDateToTimeStamp(dtEnd)

    if debug: 
        print "Starting time", dtStart
        print "Ending time", dtEnd

    # ............................................................ 
    # first graph : no noise substraction

    vars = vDict.keys()

    for det in vars:
        xarray, yarray, yarrayPed = [],[],[]
        if debug: print "timber var ", det
        detData = tDict[det]        

        for ts, dt, val in detData:

            if ts > tsEnd or ts <= tsStart: 
                continue

            if debug: print "at", dt, "have", val

            yarray += [val]
            xarray += [ts]
        
        if debug: print "Counted", len(xarray), "time points"
        graphs   += [doGraphTimeAxis(vDict, det, xarray, yarray)]

    # ............................................................ 
    # second graph : with noise substraction

    for det in vars:
        xarray, yarrayPed = [],[]

        # use noise substracted data
        detData = tpDict[det]        
        
        for ts, dt, val in detData:

            if ts > tsEnd or ts <= tsStart: 
                continue

            yarrayPed += [val]
            xarray += [ts]
        
        if debug: print "Counted", len(xarray), "time points"
        graphsPed+= [doGraphTimeAxis(vDict, det, xarray, yarrayPed)]
    # ............................................................ 
    # actual plots

    a,b,doLogy = 1,2,1
    cv = TCanvas( 'cv', 'cv' , 10, 10, a*1200, b*500 )

    # great root needs some Timeoffset
    da = TDatime(2002,01,01,02,00,00)
    cv.Divide(a,b)

    thelegend = TLegend(0.865,0.53,0.94,0.95)
    thelegend.SetFillColor(ROOT.kWhite)
    thelegend.SetShadowColor(ROOT.kWhite)
    thelegend.SetLineColor(ROOT.kWhite)
    thelegend.SetLineStyle(0)
    thelegend.SetTextSize(0.03)

    mg    = TMultiGraph(pname, pname)
    mgPed = TMultiGraph(pname+"Ped", pname+"Ped")
    for gr in graphs:

        kname = gr.GetName()
        lText = legendName(kname)
        thelegend.AddEntry(gr,lText, 'p')
        mg.Add(gr)

    for gr in graphsPed:
        mgPed.Add(gr)

    cv.cd(1)
    gStyle.SetTimeOffset(da.Convert())
    gPad.SetLogy(doLogy)
    gPad.SetLeftMargin(-0.09)
    gPad.SetRightMargin(0.14)
    gPad.SetGridx(1)

    mg.Draw('ap')
    mg.GetXaxis().SetTimeDisplay(1)
    mg.GetXaxis().SetTimeFormat("%H:%M:%S")
    mg.GetXaxis().SetLabelSize(0.04)
    mg.GetXaxis().SetTitle("local time")
    mg.GetYaxis().SetRangeUser(YurMin, YurMax)
    mg.GetYaxis().SetTitle("Gy/s")
    mg.GetYaxis().SetTitleOffset(0.98)
    ml.DrawLatex(X1, Y1, "with pedestral")
    ml.DrawLatex(X1, Y1+0.075, labText)
    thelegend.Draw()

    cv.cd(2)
    gStyle.SetTimeOffset(da.Convert())
    gPad.SetLogy(doLogy)
    gPad.SetLeftMargin(-0.09)
    gPad.SetRightMargin(0.14)
    gPad.SetGridx(1)

    mgPed.Draw('ap')
    mgPed.GetXaxis().SetTimeDisplay(1)
    mgPed.GetXaxis().SetTimeFormat("%H:%M:%S")
    mgPed.GetXaxis().SetLabelSize(0.04)
    mgPed.GetXaxis().SetTitle("local time")
    mgPed.GetYaxis().SetRangeUser(YurMin, YurMax)
    mgPed.GetYaxis().SetTitle("Gy/s")
    mgPed.GetYaxis().SetTitleOffset(0.8)

    thelegend.Draw()

    ml.DrawLatex(X1, Y1, "noise substracted")
    ml.DrawLatex(X1, Y1+0.075, labText)

    TCTsett = labText.split()[2].split("#")[0]
    TCLAsett = labText.split()[5].split("#")[0]
    rfSett = labText.split()[6].split("-mom")[0]
    pname += "_TCT" + TCTsett.replace(".","") + "_TCLA" + TCLAsett + "_" + rfSett
    print "Saving", pname
    cv.Print(pname + ".pdf" )
## -----------------------------------------------------------------------------------    

def createKey(l):

    #l = "TCTs at 8.3#sigma, TCLAs at 14#sigma, on-momentum, B2V "
    if debug: print l.split()
    TCTsett = l.split()[2].split("#")[0]
    TCLAsett = l.split()[5].split("#")[0]
    rfSett = l.split()[6].split("-mom")[0]
    try: 
        beamplane = "_" + l.split()[7]
    except:
        beamplane = ""

    k = TCTsett + "_" + TCLAsett + "_" + rfSett + beamplane
    return k
## -----------------------------------------------------------------------------------    
def getPedDicts(tDict, doTCPs):

    # return by default pDict for TCTs

    from MDAnalysis_dict import timeNoise 
    pedDictTCTs = []
    pedDictTCPs = []

    for timetupel in timeNoise:
        pedDictTCTs += [ getPedestral(tDict, vDictTCTs, timetupel ) ]
        if doTCPs: pedDictTCPs += [ getPedestral(tDict, vDictTCPs, timetupel ) ]


    if doTCPs:
        return pedDictTCTs, pedDictTCPs
    else:
        return pedDictTCTs
## -----------------------------------------------------------------------------------    
def plotLossesForTimeRange(tDict):
    # ............................................................ 
    #     
    # 
    #
    # ............................................................

    from MDAnalysis_dict import timeSignal 

    pedDictTCTs, pedDictTCPs = getPedDicts(tDict,1)
    if len(pedDictTCTs) != len(timeSignal): 
        print "Error!!! ", len(pedDictTCTs), len(timeSignal)
        sys.exit()

    for i,timetupel in enumerate(timeSignal):

        pDictTCTs = pedDictTCTs[i]
        pDictTCPs = pedDictTCPs[i]
        
        doLossesVsTime(tDict, vDictTCTs, pDictTCTs, timetupel, "BLM_TCTs", 5e-9,1e-4)
        doLossesVsTime(tDict, vDictTCPs, pDictTCPs, timetupel, "BLM_TCPs", 5e-9,3e-3)

## -----------------------------------------------------------------------------------    
def getTCTlosses(ts_dt_peak, tDict, pDict):
    # returns a list of this type: npList
    # npList += [ [det,normVal] ]

    (ts_peak, dt, peak) = ts_dt_peak
    print "Searching for ts ", ts_peak, dt
    tpDict = subPedestral(tDict, vDictTCTs, pDict)

    delta = 60.
    npList = []
    debug = 0
    YurMin, YurMax = -1, -1
    for det in vDictTCTs.keys():
        
        detData = tpDict[det]

        if debug: print "Checking data of ", det

        for ts, dt, val in detData:

            normVal = val
            if debug: print det,"loss =", val, dt
            if peak: normVal /= peak
            if debug: print det,"loss normed =", normVal, dt
            if ts == ts_peak:
                npList += [ [det,normVal] ]
                if debug: print "Found exact same timestamp of peak and tct loss", normVal
                break
            elif (ts <= ts_peak+delta) and ts > ts_peak:
                npList += [ [det,normVal] ]
                if debug: print "Look for ts ", delta,"sec. after peak happened. Found", dt, normVal
                break

        debug = 0

    if len(vDictTCTs.keys()) != len(npList):
        print "Expected ", len(vDictTCTs.keys()), " entries and have", len(npList)
        print "Exiting.. not yet."
        #sys.exit()

    if debug: print npList
    return npList

## -----------------------------------------------------------------------------------    
def prepYarray(loss_at_thisTCT, xLabels):

    yarray = [ 1e-16 for i in range(len(xLabels)) ]
    for settID, loss in loss_at_thisTCT:
        
        for xl in xLabels:
            tctSett = settID.split("_")[0]
            if settID.count(xl): 
                t = xLabels.index(tctSett)
                break

        yarray[t] = loss
            
    return yarray

## -----------------------------------------------------------------------------------    
def getNoisePerSett(peddetDict, det, keys_per_scan):

    noise = []

    for sett_blm_key in peddetDict.keys():
        if not sett_blm_key.count(det): continue

        for tk in keys_per_scan:
            sett  = sett_blm_key.split(det)[0]

            tkShort =  "_".join(tk.split("_")[:3])
            if sett == tkShort:
                # sett, [meanNoise, stddev]
                noise += [[ sett, peddetDict[sett_blm_key] ]]

    return noise
## -----------------------------------------------------------------------------------    
def plotPeaks(tDict):
    # ............................................................ 
    #     
    # plot losses vs BLM for a certain time
    #
    # ............................................................
    from MDAnalysis_dict import timeNoise 

    pedDictTCTs, pedDictTCPs = getPedDicts(tDict,1)
    pedTCTsKeys = [ createKey(tN[-1]) for tN in timeNoise ]
  
    # create flat dict
    ppListTCTs, ppListTCPs = [],[]
    for i,sett in enumerate(pedTCTsKeys):

        pDictTCTs = pedDictTCTs[i]
        pDictTCPs = pedDictTCPs[i]
        for det in pDictTCTs:
            pedSBLM = sett + det
            ppListTCTs += [[ pedSBLM, pDictTCTs[det] ]]

        for det in pDictTCPs:
            pedSBLM = sett + det
            ppListTCPs += [[ pedSBLM, pDictTCPs[det] ]]

    peddetDictTCTs = dict(ppListTCTs)
    peddetDictTCPs = dict(ppListTCPs)
    
    from MDAnalysis_dict import timeRanges
    tctLossList = []
    peaksTCPsList = []
    for i,sett in enumerate(timeRanges):

        for timetupel in sett:
            print "-" * 80
            detPeak, ts_dt_peak = getPeak( getPeaks(tDict, vDictTCPs, timetupel) )
            print "Found peak in ", detPeak, ts_dt_peak, timetupel
            peaksTCPsList += [ [detPeak, ts_dt_peak] ]
            (ts, dt, peak) = ts_dt_peak

            # create key from timeRange
            tR_key = createKey(timetupel[-1])

            # getTCTlosses returns a list with elements [det_tct, normedTCTLoss]
            tctLosses = getTCTlosses(ts_dt_peak, tDict, pedDictTCTs[i])
            tctLossList += [ (tR_key, [tctLosses, peak, detPeak] ) ]


    tctLossDict = dict(tctLossList)
    tkeys = tctLossDict.keys()
    tkeys.sort()
    if debug: print "Keys in tctLossDict", tkeys

    ## ...................................................................................
    
    # scan identifier
    scans = ["14_on", "10_on", "14_neg-off", "14_pos-off"]
    rlabs = ["TCLAs@14#sigma dp/p=0", "TCLAs@10#sigma dp/p=0", "TCLAs@14#sigma #deltap/p=-1.2e-4 ", "TCLAs@14#sigma #deltap/p=+1.2e-4"]
    smark = [20 , 34 , 23, 22]
    scols = [kCyan+2, kBlue, kPink-6, kRed ]
    fDataName = "MDtighterTCTs_measurementData.txt"
    dataOutFile = open(fDataName, 'w')

    dataline = 'TCT setting, noise substracted normalised TCT signal, uncertainty of TCT signal normalised, noise substracted tct signal, noise substracted highest loss \n'
    dataOutFile.write(dataline)

    print "writing ........ ", fDataName
    xLabels = ["7.8", "8.3", "8.8", "9.3", "9.8", "10.3"]
    for det in vDictTCTs.keys():
        print "Preparing plot for ", det
        dataline = det  + '\n'
        dataOutFile.write(dataline)

        hists = []
        graphs = []
        graphsNoise = []
        graphsPeaks = []

        mg = TMultiGraph()
        mgN = TMultiGraph()
        mgP = TMultiGraph()

        Beam = "B1"
        if det.count("B2"): Beam = "B2"

        Plane = "H"
        if det.count("TCTPV"): Plane = "V"

        IP = "IP1"
        if det.count("L5") or det.count("R5"): IP = "IP5"
        scan_14_on, scan_10_on = [], []
        colcnt = 0
        for s,scan in enumerate(scans):
            print "-"*10,">> In scan",  scan

            # get settings per scan
            keys_per_scan = []

            for tk in tkeys:
                if tk.count(scan) and tk.count(Beam+Plane): keys_per_scan += [tk]

            if debug:
                print "Found these keys identifying the settings per scan", keys_per_scan

            # collect losses on this tct per setting
            loss_at_thisTCT = []
            norm_at_thisTCT = []
            for tk in keys_per_scan:

                tctLosses = tctLossDict[tk][0]
                peak = tctLossDict[tk][1]
                detPeak = tctLossDict[tk][2]

                for tct,loss in tctLosses:
                    if tct == det: 
                        loss_at_thisTCT += [ [tk, loss] ]
                        norm_at_thisTCT += [ [tk, peak, detPeak] ]

                        # dont really need other losses...
                        break

            if debug: print "loss_at_thisTCT", loss_at_thisTCT

            lossTCTtupl = [(float(sett.split("_")[0]),loss) for sett,loss in loss_at_thisTCT]
            lossTCPtupl = [(float(sett.split("_")[0]),norm) for sett,norm,detPeak in norm_at_thisTCT]
            xErrarray   = [0. for i in lossTCTtupl]
            lossTCPs    = [loss for sett,loss in sorted(lossTCPtupl)]
            xarray      = [sett for sett,loss in sorted(lossTCTtupl)]
            lossTCTs    = [loss for sett,loss in sorted(lossTCTtupl)]    

            peddetDict = peddetDictTCTs
            noise = []
            for sett_blm_key in peddetDict.keys():
                if not sett_blm_key.count(det): continue

                for tk in keys_per_scan:
                    sett  = sett_blm_key.split(det)[0]

                    tkShort =  "_".join(tk.split("_")[:3])
                    if sett == tkShort:
                        # sett, [meanNoise, stddev]
                        noise += [[ sett, peddetDict[sett_blm_key] ]]
            noiseTCT = noise
            noiseTCP = noise

            yNoiseTCTtupl    = sorted( [(float(sett.split("_")[0]),tctnoise,noiseErr) for sett,(tctnoise,noiseErr) in noiseTCT] )
            yNoiseTCT        = [tctnoise for sett,tctnoise,noiseErr in yNoiseTCTtupl]
            yNoiseErrTCT     = [noiseErr for sett,tctnoise,noiseErr in yNoiseTCTtupl]

            yNoiseTCPtupl    = sorted( [(float(sett.split("_")[0]),0.,0.) for sett,(tcpnoise,noiseErr) in noiseTCP] )
            yNoiseTCP        = [tcpnoise for sett,tcpnoise,noiseErr in yNoiseTCPtupl]
            yNoiseErrTCP     = [noiseErr for sett,tcpnoise,noiseErr in yNoiseTCPtupl]

            yNoiseTCTnormed  = []
            yNoiseErrTCTnormed  = []
            for i in range(len(yNoiseTCT)):
                tctnoise   = yNoiseTCT[i]
                # scale error up by normalisation factor
                yNoiseTCTnormed += [tctnoise/lossTCPs[i]]
                yNoiseErrTCTnormed += [yNoiseErrTCT[i]/lossTCPs[i]]

            grs, datalines   = doGraphErrors(s, det, xarray, lossTCTs, xErrarray, yNoiseErrTCTnormed, 1)
            grsN, datalinesN = doGraphErrors(s, det, xarray, yNoiseTCTnormed, xErrarray, yNoiseErrTCTnormed, 1)
            grsP, datalinesP = doGraphErrors(s, det, xarray, lossTCPs, xErrarray, yNoiseTCP, 1)
            graphs      += [grs]
            graphsNoise += [grsN]
            graphsPeaks += [grsP]

            dataline = "--->> In scan : " + scan + "\n"
            dataOutFile.write(dataline)

            maxval, minval   = -1, 1 
            for i in range(len(datalines)):
                tct = float(datalines[i].split()[1])
                tctsignal = tct * float(datalinesP[i].split()[1])
                dataline = datalines[i].rstrip() + " " + str(tctsignal) + " " + datalinesP[i].split()[1] + " \n"
                dataOutFile.write(dataline)
                # ..............
                noise = float(datalinesN[i].split()[1])
                tctnoise = tct+noise
                collsett = datalines[i].split()[0]
                print "scan", scan, "collsetting",collsett,"tct normed", tct, ", noise", noise                    

                if tct > maxval: maxval = tct
                if tct < minval: minval = tct
                # ..............


                if scan.count("14_on"): scan_14_on += [(collsett,tct)]
                if scan.count("10_on"): scan_10_on += [(collsett,tct)]

            print det, scan, "increase max/min", maxval/minval
            for collsett_14, tct_14 in scan_14_on:

                for collsett_10, tct_10 in scan_10_on:

                    if collsett_14 == collsett_10:

                        print "collsett", collsett_10, "tct_10/14", 1-tct_10/tct_14

        # .......................................................................
        # result: signal

        cv = TCanvas( 'cv', 'cv' , 10, 10, 900, 600 )
        cv.SetLogy(1)
        pname = getkname(det)
        # YurMin, YurMax = 8e-6, 8e-2
        YurMin, YurMax = -1, -1

        thelegend = TLegend(0.56,0.755,0.88,0.91)
        thelegend.SetFillColor(ROOT.kWhite)
        thelegend.SetShadowColor(ROOT.kWhite)
        thelegend.SetLineColor(ROOT.kWhite)
        thelegend.SetLineStyle(0)

        for h, gr in enumerate(graphs):
            gr.SetLineColor(scols[h])
            gr.SetLineStyle(1+h)
            gr.SetMarkerColor(scols[h])
            gr.SetMarkerStyle(smark[h])
            gr.SetMarkerSize(1.5)
            lText = rlabs[h]
            thelegend.AddEntry(gr,lText, 'pl')
            mg.Add(gr)

        mg.Draw("aple")
        if det.count("BLMTI.04R5.B2I10_TCTPV.4R5.B2:LOSS_RS09"):
            YurMin, YurMax = 2e-5,3e-3

        if YurMin > 0.: mg.GetYaxis().SetRangeUser(YurMin, YurMax)
        mg.GetXaxis().SetTitle("[#sigma]")
        mg.GetYaxis().SetTitle("noise substracted normalised loss")

        thelegend.Draw()
        ml = mylabel(42)
        ml.SetTextSize(0.04)
        X1, Y1 = 0.23, 0.96
        ml.DrawLatex(X1, Y1, det)

        print "Saving", pname 
        cv.Print(pname + ".pdf" )
        # .......................................................................
        # noise on TCTs

        cv = TCanvas( 'cv', 'cv' , 10, 10, 900, 600 )
        cv.SetLogy(0)
        pname = getkname(det)
        YurMin, YurMax = 8e-6, 8e-2

        for h, gr in enumerate(graphsNoise):
            gr.SetLineColor(scols[h])
            gr.SetLineStyle(1+h)
            gr.SetMarkerColor(scols[h])
            gr.SetMarkerStyle(smark[h])
            gr.SetMarkerSize(1.5)
            mgN.Add(gr)

        mgN.Draw("aple")
        YurMin, YurMax = 5e-5, 1e-3
        mgN.GetYaxis().SetRangeUser(YurMin, YurMax)
        mgN.GetXaxis().SetTitle("[#sigma]")
        mgN.GetYaxis().SetTitle("noise Gy/s")

        thelegend.Draw()
        ml.DrawLatex(X1, Y1, det)

        print "Saving", pname 
        cv.Print("Noise"+pname + ".pdf" )
        # .......................................................................
        # peaks

        cv = TCanvas( 'cv', 'cv' , 10, 10, 900, 600 )
        cv.SetLogy(0)
        pname = getkname(det)
        YurMin, YurMax = 8e-6, 8e-2

        for h, gr in enumerate(graphsPeaks):
            gr.SetLineColor(scols[h])
            gr.SetLineStyle(1+h)
            gr.SetMarkerColor(scols[h])
            gr.SetMarkerStyle(smark[h])
            gr.SetMarkerSize(1.5)
            mgP.Add(gr)

        mgP.Draw("apl")
        YurMin, YurMax = 5e-5, 1e-3
        #mgP.GetYaxis().SetRangeUser(YurMin, YurMax)
        mgP.GetXaxis().SetTitle("[#sigma]")
        mgP.GetYaxis().SetTitle("peak signal Gy/s")

        thelegend.Draw()
        ml.DrawLatex(X1, Y1, det)

        print "Saving", pname 
        cv.Print("Peaks"+pname + ".pdf" )
    dataOutFile.close()
## -----------------------------------------------------------------------------------    
if __name__ == "__main__":

    gROOT.SetBatch()
    gROOT.Reset()
    gROOT.SetStyle("Plain")
    gStyle.SetOptStat(0)
    gStyle.SetPalette(1)
    gROOT.LoadMacro(gitpath + "AnalysisScripts/C/AtlasStyle.C")
    gROOT.LoadMacro(gitpath + "AnalysisScripts/C/AtlasUtils.C")
    SetAtlasStyle()

    #print "time.ctime(1) = ", time.ctime(1.) 
    fname = "TIMBER_DATA_BLMs_20152808_default_MDB.csv"
    fname = "/Users/rkwee/Documents/RHUL/work/MDs/MD_TCT_analysis/TIMBER_DATA_BLMs_20152808_default_MDB.csv"

    tDict = dictionizeData(fname)
    #plotLossesForTimeRange(tDict)
    plotPeaks(tDict)
    
