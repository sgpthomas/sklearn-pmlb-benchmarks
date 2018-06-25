import os
import time

#get the directry where the input data is
inputDir = os.environ['D3MINPUTDIR']
#get the directory where to put the output data
outputDir = os.environ['D3MOUTPUTDIR']


count = 0
for root, dirs, files in os.walk(inputDir):
  for file in files:
    count += 1
    
outcount = 0
for root, dirs, files in os.walk(outputDir):
  for file in files:
    outcount += 1

outFilename = outputDir+'/example_'+str(outcount)+'.output'
with open(outFilename, 'a') as the_file:
    the_file.write('Hello world! There are '+str(count)+' in the input data directory')
    

#This is here so that the docker container will not shutdown    
while True:
  time.sleep(5)
    