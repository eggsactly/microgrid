#!/usr/bin/python3

# Copyright (C) 2023 Garrett Weaver
# City of Tucson Commission on Climate, Energy, and Sustainability 

# This program models the air conditioning utilization of a building with 
# insulated walls and roof during a day with fluctuations in temperatures. And
# estimates energy consumption in response.
#
# Assumptions:
# 1. Convective heat is insignificant
#    - This is valid as long as there is not air movement through the building
#      from outside. 
# 2. Radiative heat is insignificant
#    - This may not be a valid assumption, but it would be a factor on outdoor
#      temperature to add. 
# 3. Latent heat is insignificant
#    - This is valid because southern AZ has very low humidity 
# 4. Thermal mass of the building structure is insignificant 
#    - This may not be a valid assumption, but for the uses of comparison 
#      between options this is acceptable as it will be a linear factor. This 
#      can be mitigated by modeling an arbitrary thermal mass in the building. 

# For trig functions
import math 

# For solar panel model
from numpy import array
from solarpy import solar_panel
from datetime import datetime

# HeatFlowRate Calculates heat flow rate between an insulated barrier using a
# formula based on the "CRC Handbook of Thermal Engineering" edited by 
# Raj P. Chhabra section on R-Value and U-Factor
#
# @param tempDiff floating point value measured in Kelvin of the difference
#  between inside and outside temperature 
# @param Area floating point value measured in meters squared
# @param rVal floating point value representing the R value in m^2*K*W^(-1)
# @return the heat flow rate in watts 
def HeatFlowRate(tempDiff, area, rVal): 
    return tempDiff * area / rVal

# FahrenheitToKelvin converts temperature in Fahrenheit to Kelvin
# @param fahrenheit temperature in Fahrenheit
# @return temperature in Kelvin 
def FahrenheitToKelvin(fahrenheit):
    return ((fahrenheit - 32.0) * 5.0/9.0) + 273.15

# KelvinToFahrenhit converts temperature in Kelvin to Fahrenheit
# @param kelvin temperature in Kelvin
# @return temperature in Fahrenheit 
def KelvinToFahrenhit(kelvin):
    return ((kelvin - 273.15) * 9.0/5.0) + 32.0

# simulate_building_ac executes the simulation of a building being exposed to
#  temperature fluctuations throughout time and outputs a list of times when
#  the thermostat turned on AC, and how long it was turned on for. 
# @param buildingFaces list of faces with area and an RSI insulation value
# @param volume total volume of air (in m^3) in the building
# @param temps list of times and outside temperatures (in K) throughout the day
# @param timeStep time step size, in seconds as an integer.
# @param duration length of the simulation in seconds as an integer
# @param airHeatCapacity heat capacity of air measured in J * Kg^(-1) * K^(-1)
# @param airDensity in Kg * m^(-1)
# @param acCapacity, amount of energy AC takes out of the system measured in W
# @param thermostat setting in Fahrenheit 
# @param thermostateDifferential the amount of temperature in Fahrenheit over 
#        the thermostat setting when the AC turns on and the amount below
#        the thermostat value when the AC turns off. 
# @return list of AC turn on times and their duration 
def simulate_building_ac(buildingFaces, volume, temps, timeStep, duration, 
        airHeatCapacity, airDensity, acCapacity, thermostat, 
        thermostateDifferential):
    
    # Initialize time keeping
    nextTempIndex = 0
    lastTemp = FahrenheitToKelvin(temps[nextTempIndex]["T"])
    lastTempTime = 0.0
    nextTempTime = 60*(60*temps[nextTempIndex]["h"] + temps[nextTempIndex]["m"])
    nextTemp = FahrenheitToKelvin(temps[nextTempIndex]["T"])
    nextTempIndex = nextTempIndex + 1
    m = 0
    currentIndoorTemp = FahrenheitToKelvin(thermostat)
    
    # Calculate the mass of air in the room in Kg
    massOfAir = volume * airDensity
    
    acOn = False
    timeTurnOn = 0

    acTurnOnList = list()

    # Step through time by the time step, doing linear interpolation of the 
    # temperature between points 
    for t in range(0, duration, timeStep):
        # When the current time has surpassed the next point in time, retrieve 
        # the next point 
        if float(t) > nextTempTime:
            # If there are no more points, use the last temp until we've hit
            # our duration. 
            if nextTempIndex >= len(temps):
                nextTempTime = float(duration)
                lastTemp = FahrenheitToKelvin(temps[nextTempIndex-1]["T"])
                nextTemp = FahrenheitToKelvin(temps[nextTempIndex-1]["T"])
                m = 0
            # If there are more points, get the next point
            else:
                lastTemp = nextTemp
                lastTempTime = nextTempTime
                nextTemp =  FahrenheitToKelvin(temps[nextTempIndex]["T"])
                nextTempTime = (60*((60*temps[nextTempIndex]["h"]) 
                    + temps[nextTempIndex]["m"]))
                m = (nextTemp - lastTemp) / (nextTempTime - lastTempTime)
            nextTempIndex = nextTempIndex + 1

        # Calculate the interpolated temperature between the last point and the
        # next
        currentOutdoorTemp = (m * (t - lastTempTime)) + lastTemp 
        
        tempDiff = currentOutdoorTemp - currentIndoorTemp

        # Heat Flow into building, positive number means heat comes into the 
        # building, measured in watts (W)
        heatFlow = 0
        # For each of the walls, calculate the heat flow into the building
        # TODO: Optimization opportunity, walls on the house wont change
        # minute to minute, calculate this before hand 
        for face in buildingFaces:
            heatFlow = heatFlow + HeatFlowRate(tempDiff, face["area"], 
                face["RSI"])
        
        # Calculate the temperature rise in the building based on the heat flow
        # over the period of time

        # Find the amount of energy that has come in during the time step
        energy = heatFlow * timeStep
        # If the AC is on, modify the energy flow
        if acOn:
            energy = energy - (acCapacity * timeStep)

        # Find the temperature change from the energy input 
        tempChange = energy / (massOfAir * airHeatCapacity)
        
        # Calculate the new temperature 
        currentIndoorTemp = currentIndoorTemp + tempChange

        # Determine if the AC should be on based on the thermostat 
        if acOn:
            if currentIndoorTemp < FahrenheitToKelvin(thermostat - thermostateDifferential):
                acOn = False
                acTurnOnList.append({"T": timeTurnOn, "duration": t-timeTurnOn})
        else:
            if currentIndoorTemp > FahrenheitToKelvin(thermostat + thermostateDifferential):
                acOn = True
                timeTurnOn = t

    return acTurnOnList

conversionFactorMtoFt = 3.28084

# Distance Conversion 
def metersToFeet(m):
    return m * mtoFConversionFactor
def feetToMeters(ft):
    return ft / conversionFactorMtoFt

# main is the first function called by this program, it's where initial '
# conditions are set up 
def main():
    # building dimensions in meters
    height = 8.0
    length = 32.0
    width = 32.0
    # Insulation R values (imperial units) of types of surfaces, based on 
    # building codes in our region from Owens Corning. 
    wallInsulationR = 2.2
    ceilingInsulationR = 13

    # R value is 5.8 times larger than RSI insulation value, so if you were to
    # use advertised R values from commercial insulation, it would need to be
    # divided by 5.8 to use with SI units that this program uses for simulation
    RtoRsiFactor = 1.0/5.8
    
    # Air heat capacity, the amount of energy needed to change the temperature
    # of air measured in units of J * Kg^(-1) * K^(-1)
    airHeatCapacity = 700.0
    # Density of air at standard temperature and pressure
    # measured in units of Kg m^(-3)
    airDensity = 1.293
    
    # WA14AZ18AJ1 AC unit heat capacity measured in watts 
    acTotalHeatCapacity = 5200
    # Thermostat setting in F
    thermostatSetting = 78.0
    # Thermostat differential is the range under which an AC will turn on and
    # off. If it goes this much over the thermostat setting it will turn on
    # when it goes this amount below the thermostat setting, it will turn off
    thermostateDifferential = 1.0 

    # Modeling details
    timeStep = 1

    # Model a building as a set of faces, each face has an R value. 
    # This is implemented as a list of dictionaries. 
    buildingFaces = list()
    # Front wall
    buildingFaces.append({"area": feetToMeters(length) * feetToMeters(height), 
        "RSI": wallInsulationR * RtoRsiFactor})
    # Side wall
    buildingFaces.append({"area": feetToMeters(width) * feetToMeters(height), 
        "RSI": wallInsulationR * RtoRsiFactor})
    # Back wall
    buildingFaces.append({"area": feetToMeters(length) * feetToMeters(height), 
        "RSI": wallInsulationR * RtoRsiFactor})
    # Side wall
    buildingFaces.append({"area": feetToMeters(width) * feetToMeters(height), 
        "RSI": wallInsulationR * RtoRsiFactor})
    # Roof
    buildingFaces.append({"area": feetToMeters(width) * feetToMeters(length), 
        "RSI": ceilingInsulationR})

    # Amount of time it takes for an AC unit to turn on, which is it's largest
    # period of power consumption
    acTurnOnTime = 1.0

    # 32 degrees is a typical solar angle in AZ 
    # use this cell 
    # https://www.gogreensolar.com/products/mission-solar-345w-mono-60-cell 

    # A 4 kWh system costs $8000
    # https://www.gogreensolar.com/products/4000w-diy-solar-panel-kit-grid-tie-inverter

    areaOfSolarPanel = (0.0254 * 68.82) * (0.0254 * 41.50) 
    areaOfSolarArray = 10 * areaOfSolarPanel
    solarAngle = math.radians(-32)
    panel = solar_panel(areaOfSolarArray, 0.187, id_name='Tucson')  # surface, efficiency and name
    panel.set_orientation(array([math.sin(solarAngle), 0, -1 * math.cos(solarAngle)]))  # upwards
    panel.set_position(32.2540, 110.9742, 0)  # Tucson latitude, longitude, altitude

    # July 27, 2023 temperatures in F from Weather Underground 
    temps = [
    {"h":0,"m":53,"T":84},
    {"h":1,"m":53,"T":83},
    {"h":2,"m":53,"T":81},
    {"h":3,"m":53,"T":82},
    {"h":4,"m":53,"T":80},
    {"h":5,"m":53,"T":81},
    {"h":6,"m":53,"T":79},
    {"h":7,"m":53,"T":86},
    {"h":8,"m":53,"T":91},
    {"h":9,"m":53,"T":94},
    {"h":10,"m":53,"T":98},
    {"h":11,"m":53,"T":100},
    {"h":12,"m":53,"T":102},
    {"h":13,"m":53,"T":105},
    {"h":14,"m":53,"T":106},
    {"h":15,"m":53,"T":106},
    {"h":16,"m":53,"T":107},
    {"h":17,"m":53,"T":106},
    {"h":18,"m":53,"T":105},
    {"h":19,"m":53,"T":103},
    {"h":20,"m":53,"T":99},
    {"h":20,"m":59,"T":98},
    {"h":21,"m":20,"T":93},
    {"h":21,"m":43,"T":93},
    {"h":21,"m":53,"T":93},
    {"h":22,"m":14,"T":91},
    {"h":22,"m":24,"T":89},
    {"h":22,"m":39,"T":89},
    {"h":22,"m":53,"T":89},
    {"h":23,"m":53,"T":92}]

    #WA14AZ18 AC data  
    ac_volts = 220.0
    compressorStartAmps=43.0
    compressorRunningAmps = 9.0
    fanStartAmps = 1.5
    fanRunningAmps = 0.8

    # simulate_building_ac will give a list of AC turn on durations throughout
    # the day 
    acOnDurations = simulate_building_ac(buildingFaces=buildingFaces, 
        volume = feetToMeters(length) * feetToMeters(height) 
            * feetToMeters(width),
        temps=temps, timeStep=timeStep, duration=60*60*24, 
        airHeatCapacity=airHeatCapacity, airDensity=airDensity, 
        acCapacity=acTotalHeatCapacity, thermostat=thermostatSetting, 
        thermostateDifferential=thermostateDifferential)

    # Calculate energy used in turning on AC, assume 1s to start
    turnOnPower = (fanStartAmps + compressorStartAmps) * ac_volts
    runningPower = (fanRunningAmps + compressorRunningAmps) * ac_volts

    secondsAcOn = 0
    print("Simulation of a 1000 sq ft., poorly insulated home (with no windows) "
"with a 1.5 Ton AC unit")
    print("Event log:")
    turnOnGridConsumption = 0.0
    operatingGridConsumption = 0.0
    # List times when AC turned on 
    for acTurnOn in acOnDurations:
        hour = int(acTurnOn["T"] / 3600)
        minute = int(acTurnOn["T"] / 60) % 60
        secondsAcOn = secondsAcOn + acTurnOn["duration"]
        pm = hour > 12
        if pm:
            daySide = "pm"
        else:
            daySide = "am"
        clockHour = ((hour-1) % 12)+1

        print (str(clockHour) + ":" + ("{:02d}".format(minute)) + " " + daySide 
            + " AC turned on for: " + str(acTurnOn["duration"]) + "s")

        # Model energy taken from the panel and subtract it from energy 
        # taken from the grid 
        panel.set_datetime(datetime(2023, 7, 23, hour, minute))  
        panelPower = panel.power()

        turnOnGridConsumption = (turnOnGridConsumption + 
            (max(turnOnPower - panelPower, 0.0) * acTurnOnTime))

        # Chop power consumption into 60 second blocks and recalculate solar production each minute
        numMinutes = int(acTurnOn["duration"]) // 60
        for i in range(0, numMinutes):
            operatingGridConsumption = operatingGridConsumption + (max(runningPower - panelPower, 0.0) * 60)
            minute = minute + 1
            if minute > 59:
                hour = hour + 1
                minute = 0
            if hour > 23:
                hour = 0
                minute = 0
            panel.set_datetime(datetime(2023, 7, 23, hour, minute))  
            panelPower = panel.power()

        # Calculate the last less than 60 second chunk 
        operatingGridConsumption = operatingGridConsumption + (max(runningPower - panelPower, 0.0) * (int(acTurnOn["duration"]) % 60))

    # Number of times to start
    timesToStart = len(acOnDurations)

    # Calculate energy consumption in joules
    runningEnergy = (runningPower * secondsAcOn)
    turnOnEnergy = turnOnPower * (1.0 * timesToStart)

    totalGridEnergy = turnOnGridConsumption + operatingGridConsumption

    totalEnergy = turnOnEnergy + runningEnergy

    print("\nAC Power from solar panels: " + "{:.3f}".format((totalEnergy - totalGridEnergy)/3.6e6) + " kWh")
    print("\nEnergy pulled from the grid: " 
        + "{:.3f}".format(totalGridEnergy/3.6e6) + " kWh")
    print("\nTotal energy used for the day: " 
        + "{:.3f}".format(totalEnergy/3.6e6) + " kWh")
   
if __name__ == "__main__":
    main()

