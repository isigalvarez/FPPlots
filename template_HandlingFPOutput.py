# !usr/bin/env python3
# ===========================================================
# Created on 07/05/2019
# Examples on how to use FLEXPARTOutput class to manage
# results from a FLEXPART simulation.
# ===========================================================

from FLEXPARTOutput import FLEXPARTOutput

# == Parameters =============================================
# Directory where simulations are stored
simDir = 'D:/Datos/0 - Trabajo/FLEXPART/Mistral_RunsIsi/'
# Define two simulations to check
sim1 = 'CAFE_F13_splitted/Flight13_20170831_95500/'
sim2 = 'CAFE_F13_splitted_CDS/Flight13_20170831_95500/'

# == Initialize FPOutput ====================================
# Call FLEXPARTOutput
FP1 = FLEXPARTOutput(simDir+sim1)
FP2 = FLEXPARTOutput(simDir+sim2)

# == Plotting ===============================================
# Trajectories for sim 1
FP1_traj_figData = FP1.plotMap_traj()
FP1_traj_figData[1].set_title(
    'Flight 13 trajectories\n0955 to 1055 (2018-08-31)\nCDS OFF')
FP1_traj_figData[0].savefig('F13_traj_CDS-OFF')

# Trajectories for sim 2
FP2_traj_figData = FP2.plotMap_traj()
FP2_traj_figData[1].set_title(
    'Flight 13 trajectories\n0955 to 1055 (2018-08-31)\nCDS ON')
FP2_traj_figData[0].savefig('F13_traj_CDS-ON')

# Folium trajectories for sim 1
FP1_traj_folium = FP1.plotFoliumMap_traj()
FP1_traj_folium.save('F13_trajFolium_CDS-OFF.html')

# Folium trajectories for sim 2
FP2_traj_folium = FP2.plotFoliumMap_traj()
FP2_traj_folium.save('F13_trajFolium_CDS-ON.html')

# Single Plume for sim 1
FP1_plume_figData = FP1.plotMap_plume('2017-08-28 08:00', plumeLims=(0.001, None),
                                      extent=[-40, -15, 0, 20])
title = FP1_plume_figData[1].get_title()
FP1_plume_figData[1].set_title(f'Flight 13 Plumes\n{title}\nCDS OFF')
FP1_plume_figData[0].savefig('F13_plume_CDS-OFF')

# Single plume for sim 2
FP2_plume_figData = FP2.plotMap_plume('2017-08-28 08:00', plumeLims=(0.1, None),
                                      extent=[-40, -15, 0, 20])
title = FP2_plume_figData[1].get_title()
FP2_plume_figData[1].set_title(f'Flight 13 Plumes\n{title}\nCDS ON')
FP2_plume_figData[0].savefig('F13_plume_CDS-ON')

# Complete
FP1_plume_figData = FP1.plotPdfMap_plume()
FP2_plume_figData = FP2.plotPdfMap_plume()

## Reduce the low limit for plume
# Sim1
FP1_plume_figData = FP1.plotMap_plume('2017-08-28 08:00',
                                      plumeLims=(0.001, None),
                                      extent=[-40, 30, -5, 25])
title = FP1_plume_figData[1].get_title()
FP1_plume_figData[1].set_title(f'Flight 13 Plumes\n{title}\nCDS OFF')
FP1_plume_figData[0].savefig('F13_plume_CDS-OFF_LowLims')
# Sim2
FP2_plume_figData = FP1.plotMap_plume('2017-08-28 08:00',
                                      plumeLims=(0.001, None),
                                      extent=[-40, 30, -5, 25])
title = FP2_plume_figData[1].get_title()
FP2_plume_figData[1].set_title(f'Flight 13 Plumes\n{title}\nCDS OFF')
FP2_plume_figData[0].savefig('F13_plume_CDS-ON_LowLims')

# == Flight 13 Complete plume plot ==========================
# Define run directory
runDir = 'testData/output_07_MultipleTrajectories/'
# Initiate the class
FPOut = FLEXPARTOutput(runDir)
# Plot every data in the plume
FPOut_plume_figData = FPOut.plotPdfMap_plume(saveName='plumeMap_complete.pdf',
                                             freq='5T', extent=[-40, 20, -15, 45])
