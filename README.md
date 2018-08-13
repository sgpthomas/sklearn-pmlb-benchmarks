# Sklearn PMLB Benchmark

This repository holds the code used run benchmark of the Sklearn classifiers on the [PMLB Dataset](https://github.com/EpistasisLab/penn-ml-benchmarks).
Results for this datarun can be found here: [completed-w-holes-7-26-2018.pkl](https://drive.google.com/open?id=1FFY_hlvYbcmBvi2UzLk4N8CdDF9A4Ptq).
A lot of this code was derived from the code used to run the original PMLB experiments which is housed here:
[sklearn-benchmarks](https://github.com/rhiever/sklearn-benchmarks).

Here is a link to the original paper by Randal S. Olson, William La Cava, Patryk Orzechowski, Ryan J. Urbanowicz, and Jason H. Moore (2017).
[PMLB: a large benchmark suite for machine learning evaluation and comparison](https://biodatamining.biomedcentral.com/articles/10.1186/s13040-017-0154-4).

## Why?
The reason that we reran this experiment was so that we could gather data on generalization error.
Specificaly, in the original paper, they only recorded the average `accuracy`, `macrof1`, and `balanced accuracy` on the test data
after 10 fold cross validation.
We used the same metrics but recorded both test and train averages after 10 fold cross validiation.
On top of this, we also record fit and score times.
For a full list of every metric we save, look below.

 
# Program Architecture
This section outlines the architecture of the program.

## Overview
This program uses a client-server architecture with a variable number of clients and a single scheduler.
The clients and the scheduler communicate using a custom protocol over TCP.
All the data is passed in JSON. 
There were 2 main considerations that guided the development of this program:
 1) The datarun should be robust to the failures of clients.
 2) The datrun should be easily resumable.
A side effect of 1 is that is makes the program more scalable.
All progress is saved on the scheduler which allows the clients to be ephermeral and allows a datarun to be
stopped and started. 

## Scheduler
The scheduler has 3 duties: to keep track of trials to be completed, to commit the result of a trial to a file, and to hand out trials to clients.
The scheduler first discovers all tasks by enumerating every method with all given hyperparameter settings (specified in the method files).
It then looks into the results directory and removes any tasks that have already been committed.
Once this is complete, the scheduler starts listening for clients.
As soon as a client connects to the scheduler, the scheduler starts a handler process that deals with all the communication with the client.
Because all the communication is client driven, the scheduler simply has to respond to each type of message it receives.

Below is a list of all types of messages and how the scheduler responds to each.

### Message Types
| Client's Request | Server's Response |
-------------------------------------------------
| `verify`                              | `success`                                                        |
| `trial request`                       | get item from the top of the todo queue and send `trial details` |
| `trial done` (payload= trial results) | commit payload and confirm with `success`                        |
| `trial cancel` (payload= id#)         | commit file for id# with reason for failure                      |
| `terminate`                           | stop handler for this client                                     |

## Client


# Executing a Datarun

# Data Metadata
## Columns in the table
 - dataset
 - classifier
 - parameters
 - avg\_fit\_time
 - avg\_score\_time
 - avg\_test\_accuracy
 - avg\_test\_bal\_accuracy
 - avg\_test\_f1\_macro
 - avg\_train\_accuracy
 - avg\_train\_bal\_accuracy
 - avg\_train\_f1\_macro
 - std\_fit\_time
 - std\_score\_time
 - std\_test\_accuracy
 - std\_test\_bal\_accuracy
 - std\_test\_f1\_macro
 - std\_train\_accuracy
 - std\_train\_bal\_accuracy
 - std\_train\_f1\_macro
 - acc\_generror
 - bal\_acc\_generror
 - f1\_generror
 - bal\_acc\_weighted\_generror
 
## Datasets
 - GAMETES_Epistasis_2-Way_1000atts_0.4H_EDM-1_EDM-1_1
 - GAMETES_Epistasis_2-Way_20atts_0.1H_EDM-1_1
 - GAMETES_Epistasis_2-Way_20atts_0.4H_EDM-1_1
 - GAMETES_Epistasis_3-Way_20atts_0.2H_EDM-1_1
 - GAMETES_Heterogeneity_20atts_1600_Het_0.4_0.2_50_EDM-2_001
 - GAMETES_Heterogeneity_20atts_1600_Het_0.4_0.2_75_EDM-2_001
 - Hill_Valley_with_noise
 - Hill_Valley_without_noise
 - adult
 - agaricus-lepiota
 - allbp
 - allhyper
 - allhypo
 - allrep
 - analcatdata_aids
 - analcatdata_asbestos
 - analcatdata_authorship
 - analcatdata_bankruptcy
 - analcatdata_boxing1
 - analcatdata_boxing2
 - analcatdata_creditscore
 - analcatdata_cyyoung8092
 - analcatdata_cyyoung9302
 - analcatdata_dmft
 - analcatdata_fraud
 - analcatdata_germangss
 - analcatdata_happiness
 - analcatdata_japansolvent
 - analcatdata_lawsuit
 - ann-thyroid
 - appendicitis
 - australian
 - auto
 - backache
 - balance-scale
 - banana
 - biomed
 - breast
 - breast-cancer
 - breast-cancer-wisconsin
 - breast-w
 - buggyCrx
 - bupa
 - calendarDOW
 - car
 - car-evaluation
 - cars
 - cars1
 - chess
 - churn
 - clean1
 - clean2
 - cleve
 - cleveland
 - cleveland-nominal
 - cloud
 - cmc
 - coil2000
 - colic
 - collins
 - confidence
 - connect-4
 - contraceptive
 - corral
 - credit-a
 - credit-g
 - crx
 - dermatology
 - diabetes
 - dis
 - dna
 - ecoli
 - fars
 - flags
 - flare
 - german
 - glass
 - glass2
 - haberman
 - hayes-roth
 - heart-c
 - heart-h
 - heart-statlog
 - hepatitis
 - horse-colic
 - house-votes-84
 - hungarian
 - hypothyroid
 - ionosphere
 - iris
 - irish
 - kddcup
 - kr-vs-kp
 - krkopt
 - labor
 - led24
 - led7
 - letter
 - liver-disorder
 - lupus
 - lymphography
 - magic
 - mfeat-factors
 - mfeat-fourier
 - mfeat-karhunen
 - mfeat-morphological
 - mfeat-pixel
 - mfeat-zernike
 - mnist
 - mofn-3-7-10
 - molecular-biology_promoters
 - monk1
 - monk2
 - monk3
 - movement_libras
 - mushroom
 - mux6
 - new-thyroid
 - nursery
 - optdigits
 - page-blocks
 - parity5
 - parity5+5
 - pendigits
 - phoneme
 - pima
 - poker
 - postoperative-patient-data
 - prnn_crabs
 - prnn_fglass
 - prnn_synth
 - profb
 - promoters
 - ring
 - saheart
 - satimage
 - schizo
 - segmentation
 - shuttle
 - sleep
 - solar-flare_1
 - solar-flare_2
 - sonar
 - soybean
 - spambase
 - spect
 - spectf
 - splice
 - tae
 - texture
 - threeOf9
 - tic-tac-toe
 - titanic
 - tokyo1
 - twonorm
 - vehicle
 - vote
 - vowel
 - waveform-21
 - waveform-40
 - wdbc
 - wine-quality-red
 - wine-quality-white
 - wine-recognition
 - xd6
 - yeast

