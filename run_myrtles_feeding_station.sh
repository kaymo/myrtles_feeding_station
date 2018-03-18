#!/bin/bash

# env PATH=${HOME}/myrtles_feeding_station/myrtles_feeding_stationenv/bin
cd ${HOME}/myrtles_feeding_station
exec uwsgi --ini run_myrtles_feeding_station.ini

# EOF
