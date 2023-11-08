# -*- coding: utf-8 -*-
"""
Created on Tue Sep 20 14:49:53 2022

@author: Jimenez Lab
"""

import numpy as np


CCDsensArr = np.array([[[18.3,16.3,16.0,15.9],[5.48,4.41,3.96,3.91]],[[3.34,3.37,np.nan,np.nan],[0.8,0.8,np.nan,np.nan]]]);
#CCDsens = CCDsensArr[Oamp,preamp,hssSpeed];

SingPixNoiseArr = np.array([[[210,131,73.1,23.7],[142,68.5,41.7,12.3]],[[6.48,6.87,np.nan,np.nan],[4.83,3.18,np.nan,np.nan]]]);
#SingPixNoise = SingPixNoiseArr[Oamp,preamp,hssSpeed];

PixWellDepth = 95400; #electrons/pix
GainPixWellDepth = 400000; #FWD of gain register is 730,000, but linear up to 400000
QE = 0.80; #460nm
darkRate = 6*0.00025; #electrons/pixel/sec (I observed that the dark rate was 6-7 times higher than the spec for 80C in one measurement)

#Check if pix well depth can be reached or is limited by ADC (65535 AD)
#pixel binning increases well depth linearly, but ADC still limits superpixel

t_array = np.append(np.arange(0.1,1.0,0.1),np.arange(1,11,1))
#t_array = np.append(t_array,np.arange(0.001,0.010,0.001))
#t_array = np.append(t_array,np.arange(10,210,10))
#t_array = np.append(t_array,np.arange(0.1,1.0,0.1))
#t_array = np.append(t_array,np.arange(1,10,1))
gainArr=np.zeros([3])

######### For a given photon rate (photRate) and bkgd rate (bkgdRate) spread over a number of pixels (pixels) and with a desired full well fraction (FWfrac) at this signal level,
######### this function spits out the best settings of the EMCCD 
######### output is BestSettings, SNR where
######### BestSettings is an array with [Output amplifier,Preamplifier,horizontal shift Speed,binning,integration time,gain,full well fraction]

def BestSettings(photRate=1,bkgdRate=40,pixels=20,FWfrac=0.01):
    SNR=0;
    PixWellDepth = 95400; #electrons/pix
    GainPixWellDepth = 400000;
    gainArr[1]=30
    gainArr[2]=300
    
    for Oamp in range(0,2): #loop through output amplifiers
        if Oamp==0: # for EM amplifier
            for preamp in range(0,2): #loop through pre amplifiers
                for hssSpeed in range(0,4): #loop through horizontal shift speeds
                    for binning in range(1,35):#np.logspace(0,3,4,base=2): #loop through binning conditions
                        for t in t_array:#range(1,61): #loop through integration times
                        
                            SuperPix = np.ceil(pixels/(binning)**2); #number of superpixels
                            photRatePix = photRate/SuperPix; #photons/superpixel
                            bkgdRatePix = bkgdRate/SuperPix;
                            SingPixNoise = SingPixNoiseArr[Oamp,preamp,hssSpeed]; #electrons/pix
                            gainArr[0] = 4*SingPixNoise/(photRatePix*QE) #gain should make signal 4-5 times larger than read noise (Andor suggestion)
                            for gain in gainArr:
                                if gain>300:
                                    gain=300; #don't use gain that could damage the detector at high signal levels
                                    
                                #set electronic noise factor    
                                if gain>30:
                                    ENF = 1.41;
                                else:
                                    ENF = 1;
                                
                                electRatePix = (photRatePix+bkgdRatePix)*QE;
                                CCDsens=CCDsensArr[Oamp,preamp,hssSpeed];
                                
                                PixWellDepthADU = PixWellDepth/CCDsens;
                                GainPixWellDepthADU = GainPixWellDepth/CCDsens;
                                if PixWellDepthADU>65535: #check if pixel well depth is limited by 16-bit digitization
                                    PixWellDepth = 65535*CCDsens
                                elif GainPixWellDepthADU>65535:
                                    GainPixWellDepth = 65535*CCDsens
                                    
                                electRatePixGain = electRatePix*gain;
                                
                                #make sure the pixel well depth is sufficient
                                if electRatePix*t>PixWellDepth:
                                    SNRnew=0;
                                elif electRatePixGain*t>FWfrac*GainPixWellDepth:
                                    SNRnew=0;
                                else:
                                    #calculate SNR
                                    SNRnew = photRatePix*QE*gain*SuperPix*t/(np.sqrt(SuperPix)*np.sqrt((SingPixNoise**2+(ENF*gain)**2*((photRate+bkgdRate)*QE*t+darkRate*t))+(SingPixNoise**2+(ENF*gain)**2*(bkgdRate*QE*t+darkRate*t))));
                                #if SNR is better than previous best settings, use this and save the settings    
                                if SNRnew>SNR:
                                    SNR=SNRnew
                                    BestSettings= [Oamp,preamp,hssSpeed,binning,t,gain,electRatePixGain*t/GainPixWellDepth]
        if Oamp==1: # for conventional amplifier
            for preamp in range(0,2):
                for hssSpeed in range(0,2):
                    for binning in range(1,35):#np.logspace(0,3,4,base=2):
                        for t in t_array:#range(1,61):
                        
                            SuperPix = np.ceil(pixels/(binning)**2);
                            photRatePix = photRate/SuperPix; #phot/pix
                            bkgdRatePix = bkgdRate/SuperPix;
                            SingPixNoise = SingPixNoiseArr[Oamp,preamp,hssSpeed]; #electrons/pix
        
                            
                            electRatePix = (photRatePix+bkgdRatePix)*QE;
                            CCDsens=CCDsensArr[Oamp,preamp,hssSpeed];
                            
                            PixWellDepthADU = PixWellDepth/CCDsens;
                            if PixWellDepthADU>65535:
                                PixWellDepth = 65535*CCDsens
                            if electRatePix*t>FWfrac*PixWellDepth:
                                SNRnew=0;
                            else:
                                SNRnew = photRatePix*QE*SuperPix*t/(np.sqrt(SuperPix)*np.sqrt((SingPixNoise**2+((photRate+bkgdRate)*QE*t+darkRate*t))+(SingPixNoise**2+(bkgdRate*QE*t+darkRate*t))));
                            if SNRnew>SNR:
                                SNR=SNRnew
                                BestSettings= [Oamp,preamp,hssSpeed,binning,t,1,electRatePix*t/PixWellDepth]
    return BestSettings,SNR;


######### For a given photon rate (photRate) and bkgd rate (bkgdRate) spread over a number of pixels (pixels) under various 
######### EMCCD settings, this script outputs the SNR and full well fraction

def SNR(photRate=1,bkgdRate=40,pixels=20,Oamp=0,preamp=0,hssSpeed=0,binning=8,t=1,gain=10):
    PixWellDepth = 95400; #electrons/pix
    GainPixWellDepth = 400000;
    
    SuperPix = np.ceil(pixels/(binning)**2); #number of superpixels
    photRatePix = photRate/SuperPix; #photons/superpixel
    bkgdRatePix = bkgdRate/SuperPix;
    SingPixNoise = SingPixNoiseArr[Oamp,preamp,hssSpeed]; #electrons/pix
    
    CCDsens=CCDsensArr[Oamp,preamp,hssSpeed];
    
    electRatePix = (photRatePix+bkgdRatePix)*QE;
    CCDsens=CCDsensArr[Oamp,preamp,hssSpeed];
    
    PixWellDepthADU = PixWellDepth/CCDsens;
    GainPixWellDepthADU = GainPixWellDepth/CCDsens;
    if PixWellDepthADU>65535: #check if pixel well depth is limited by 16-bit digitization
        PixWellDepth = 65535*CCDsens
    elif GainPixWellDepthADU>65535:
        GainPixWellDepth = 65535*CCDsens
        
    electRatePixGain = electRatePix*gain;
    
    if Oamp==0:
        PixWellFrac = electRatePixGain*t/GainPixWellDepth
    else:
        PixWellFrac = electRatePix*t/PixWellDepth
    
    
    #set electronic noise factor    
    if gain>30:
        ENF = 1.41;
    else:
        ENF = 1;
        
    SNR = photRatePix*QE*gain*SuperPix*t/(np.sqrt(SuperPix)*np.sqrt((SingPixNoise**2+(ENF*gain)**2*((photRate+bkgdRate)*QE*t+darkRate*t))+(SingPixNoise**2+(ENF*gain)**2*(bkgdRate*QE*t+darkRate*t))));
    return SNR, PixWellFrac