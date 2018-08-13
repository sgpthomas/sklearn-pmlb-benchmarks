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
 
# Program Architecture
# Executing a Datarun
