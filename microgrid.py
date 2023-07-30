#!/usr/bin/python

# Copyright (C) 2023 Garrett Weaver
# City of Tucson Commission on Climate, Energy, and Sustainability 

# From engineering toolbox lists ohms/1000m of wire. 
# This dictionary associates wire gauge with resistance per 1000m of wire
copperWireResistance = {
     "1" : 0.41
    ,"2" : 0.51
    ,"3" : 0.65
    ,"4" : 0.81
    ,"6" : 1.3
    ,"8" : 2.1
    ,"10": 3.3
    ,"12": 5.2
    ,"14": 8.2
    ,"16": 13
}

conversionFactorMtoFt = 3.28084

# Ohms law
# Returns voltage given current measured in amps and resistance measured 
# in ohms
def OhmsLawV(I, R):
    return I * R
# Returns current given voltage measured in volts and resistance measured 
# in ohms
def OhmsLawI(V, R):
    return V / R

# Distance Conversion 
def metersToFeet(m):
    return m * mtoFConversionFactor
def feetToMeters(ft):
    return ft / conversionFactorMtoFt


# 100 ft of 8 gauge wire at 380 v DC
current = OhmsLawI(380, feetToMeters(100) * copperWireResistance["8"] / 1000)

print ("Current: " + str(current) + "A")


