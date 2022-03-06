#!/bin/bash#
cd H03-2021
cat forecastdemand_nsw.csv.zip.partaa forecastdemand_nsw.csv.zip.partab > forecastdemand_nsw.csv.zip
unzip forecastdemand_nsw.csv.zip
unzip temperature_nsw.csv.zip
unzip totaldemand_nsw.csv.zip
cd ..
cd H06-2021
unzip a.zip
unzip b.zip
unzip c.zip
unzip d.zip