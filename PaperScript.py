#!/usr/bin/env python


from optparse import OptionParser	# Command-line parsing

import glob			# for filename globbing
import os
import numpy
import scipy.stats as ss	# for sem() and other stat funcs
import scipy.stats.stats as sss	# for nanmean() and other nan-friendly funcs
import pylab			# for plotting

from filtertraining import *	# for MakeBins(), Hist2d()

from scipy import optimize
#from arff import arffread

def ZRModel(coefs, reflects) :
    return(((10.0 **(reflects/10.0))/coefs[0]) ** (1/coefs[1]))

def ZRBest(trainData) :
    def errFun(coefs) :
        return(numpy.sqrt(numpy.mean((ZRModel(coefs, trainData[:, 0]) - trainData[:, 1])**2.0)))

    return(optimize.fmin(errFun, [300, 1.4], maxiter=2000, disp=0))


############################## Plotting #########################################
def PlotCorr(obs, estimated, **kwargs) :
    pylab.scatter(obs.flatten(), estimated.flatten(), s=1, **kwargs)
    pylab.plot([0.0, obs.max()], [0.0, obs.max()], color='c', hold=True)
    pylab.xlabel('Observed Rainfall Rate [mm/hr]')
    pylab.ylabel('Estimated Rainfall Rate [mm/hr]')
    pylab.xlim((0.0, obs.max()))
    pylab.ylim((0.0, obs.max()))

def PlotZR(reflects, obs, estimated, **kwargs) :
    pylab.scatter(reflects.flatten(), obs.flatten(), color='r', s = 1)
    pylab.scatter(reflects.flatten(), estimated.flatten(), color='b', s = 1, hold = True, **kwargs)
    pylab.xlabel('Reflectivity [dBZ]')
    pylab.ylabel('Rainfall Rate [mm/hr]')
    pylab.xlim((reflects.min(), reflects.max()))
    pylab.ylim((obs.min(), obs.max()))

####################################################################################

def ObtainModelInfo(dirLoc, subProj) :
    modelList = glob.glob(os.sep.join([dirLoc, subProj, 'model_*.txt']))
    modelCoefs = [ProcessModelInfo(filename) for filename in modelList]

    coefNames = modelCoefs[0].keys()
    coefNames.sort()

    vals = []
    for weight in modelCoefs :
        vals.append([weight[coef] for coef in coefNames])

    return((coefNames, numpy.array(vals)))



#    print len(tempy), type(tempy[0])



def ProcessModelInfo(filename) :
    weights = {}
    nodeName = None

    for line in open(filename) :
        line = line.strip()
        if (line.startswith('Linear Node') or line.startswith('Sigmoid Node')) :
	    nodeName = line.split(' ')[-1].strip()
        elif  (line.startswith('Threshold') 
		 or line.startswith('Node')
		 or line.startswith('Attrib')) :
            weights["%s-%s" % (nodeName, line.split()[-2])] = float(line.split()[-1])

    return(weights)


def ObtainARFFData(filename, columnIndxs, linesToSkip) :
    return(numpy.loadtxt(filename, delimiter=',', skiprows=linesToSkip)[:, columnIndxs])
    

def ObtainResultInfo(dirLoc, subProj) :
    resultsList = glob.glob(os.sep.join([dirLoc, subProj, 'results_*.csv']))
    resultsList.sort()

    skipMap = {'FullSet': 13,
	       'SansWind': 11,
	       'JustWind': 10,
	       'Reflect': 8,
	       'ZRBest': 0,
	       'Shuffled': 13,
	       'NWSZR': 0}


    tempy = [ObtainARFFData(filename, numpy.array([-1, -2, -3]), skipMap[subProj]) for filename in resultsList]
    return({'modelPredicts': numpy.array([aRow[:, 0] for aRow in tempy]),
            'testObs': numpy.array([aRow[:, 1] for aRow in tempy]),
            'reflectObs': numpy.array([aRow[:, 2] for aRow in tempy])})


def SaveSubprojectModel(dirLoc, subProj) :
    resultsList = glob.glob(os.sep.join([dirLoc, subProj, 'results_*.csv']))
    resultsList.sort()

    summaryInfo = {'rmse': [],
		   'mae': [],
		   'corr': [],
		   'sse': [],
		   'sae': []}
    skipMap = {'FullSet': 13,
	       'SansWind': 11,
	       'JustWind': 10,
	       'Reflect': 8,
	       'ZRBest': 0,
	       'Shuffled': 13,
	       'NWSZR': 0}


    resultInfo = ObtainResultInfo(dirLoc, subProj)
    PlotCorr(resultInfo['testObs'], resultInfo['modelPredicts'])
    pylab.title('Model/Obs Correlation Plot - Model: ' + subProj)
    pylab.savefig(os.sep.join([dirLoc, "CorrPlot_" + subProj + ".eps"]))
    pylab.clf()
    print "   Saved Correlation Plot..."

    PlotZR(resultInfo['reflectObs'], resultInfo['testObs'], resultInfo['modelPredicts'])
    pylab.title('Model Comparison - Z-R Plane - ' + subProj)
    pylab.savefig(os.sep.join([dirLoc, "ZRPlot_" + subProj + ".png"]))
    pylab.clf()
    print "   Save ZR Plot..."

#    summaryInfo = DoSummaryInfo(resultInfo['testObs'], resultInfo['modelPredicts'])
#    statNames = summaryInfo.keys()
#    for statname in statNames :
#        numpy.savetxt(os.sep.join([dirLoc, "summary_%s_%s.txt" % (statname, subProj)]), summaryInfo[statname])
#        print "        Saved summary data for", statname



# Run this code if this script is executed like a program
# instead of being loaded like a library file.
if __name__ == '__main__':
   projectName = 'ModelProject_Retry6/'

   resultInfo = {'FullSet': None, 'ZRBest': None}

   resultInfo['FullSet'] = ObtainResultInfo(projectName, 'FullSet')
   resultInfo['ZRBest'] = ObtainResultInfo(projectName, 'ZRBest')

   pylab.figure(figsize = (12.0, 6.0))
   pylab.subplot(121)

   PlotCorr(resultInfo['ZRBest']['testObs'], resultInfo['ZRBest']['modelPredicts'])
   pylab.title('Model/Obs Correlation Plot - Model: ZRBest', fontsize = 14)

   pylab.subplot(122)
   PlotCorr(resultInfo['FullSet']['testObs'], resultInfo['FullSet']['modelPredicts'])
   pylab.title('Model/Obs Correlation Plot - Model: FullSet', fontsize = 14)

   pylab.savefig(projectName + os.sep + "CorrModels.eps")
   pylab.savefig(projectName + os.sep + "CorrModels.png", dpi = 300)
   pylab.clf()

   pylab.figure(figsize = (12.0, 6.0))
   pylab.subplot(121)

   PlotZR(resultInfo['ZRBest']['reflectObs'], resultInfo['ZRBest']['testObs'], resultInfo['ZRBest']['modelPredicts'])
   pylab.title('Model Comparison - Z-R Plane - Model: ZRBest', fontsize = 14)

   pylab.subplot(122)
   PlotZR(resultInfo['FullSet']['reflectObs'], resultInfo['FullSet']['testObs'], resultInfo['FullSet']['modelPredicts'])
   pylab.title('Model Comparison - Z-R Plane - Model: FullSet', fontsize = 14)

   pylab.savefig(projectName + os.sep + "ZRPlot_Models.eps")
   pylab.savefig(projectName + os.sep + "ZRPlot_Models.png", dpi = 300)

    

