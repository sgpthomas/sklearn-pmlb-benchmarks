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

With these in mind, I will present a high overview of the program.
There is a single centralized scheduler that keeps a queue of all trials.
When a client wants a trial, it asks the scheduler. The scheduler hands it a trial from the top of the queue.
When the client finishes executing the trial, it sends the scheduler the result.
The client is then free to ask for another trial.

The communication in this architecture is completely client driven. This removes the need for the scheduler to
have a list of the clients ahead of time and allows the clients ephermeral. You can start and stop clients without
having any effect on ths scheduler. This makes this program easily scalable to a large number of clients.

## Scheduler
The scheduler has 3 duties: to keep track of trials to be completed, to commit the result of a trial to a file, and to hand out trials to clients.
The scheduler first discovers all tasks by enumerating every method with all given hyperparameter settings (specified in the method files).
It then looks into the results directory and removes any tasks that have already been committed.
Once this is complete, the scheduler starts listening for clients.
As soon as a client connects to the scheduler, the scheduler starts a handler process that deals with all the communication with the client.
Putting the handler for each client in it's own process greatly increases the throughput of the scheduler.
Because all the communication is client driven, the scheduler simply has to respond to each type of message it receives.

Below is a list of all types of messages and how the scheduler responds to each.

### Message Types
 | Client's Request | Server's Response |
 |------------------|-------------------|
 | `verify`                              | `success`                                                        |
 | `trial request`                       | get item from the top of the todo queue and send `trial details` |
 | `trial done` (payload= trial results) | commit payload and confirm with `success`                        |
 | `trial cancel` (payload= id#)         | commit file for id# with reason for failure                      |
 | `terminate`                           | stop handler for this client                                     |

## Client
After the client connects to the scheduler. It simply runs a loop asking the scheduler for a trial, executing the trial, and then sending the results.
In order to allow the client to make use of multiple CPUs, there is parallelization on the client side. The client can start multiple processes.
Each process asks for a trial, executes the trial, commits the result, and then dies. The client is then free to start another process.

# Executing a Datarun
This section provides some guidelines for how to run this program on AWS.
I wrote a command line wrapper for `awscli`. This simplifies some common tasks. You can find that here: [aws-automation](https://github.com/sgpthomas/aws-automation).

## Overview
I will walk through creating an AMIs, security groups, configuring spot fleets, and automatically starting the program on instance launch.

### Creating an AMI
Once you get to the EC2 home screen, navigate to 'Instances' on the sidebar, and click 'Launch Instance'.

![Launch Instance](.aws-tutorial/launch-instance.png)

You then have to choose a base-OS for your AMI. I chose the Ubuntu 16.04 image because I'm very comfortable with Ubuntu.
Choose whatever are you comfortable with. This is will be a temporary machine so you can just choose the t2.micro instance type.
Then click 'Review and Launch'. Now we want to edit the security groups so click 'Edit security groups'. For now just make a
new security group and call it something you'll remember. Add a SSH connection wiht your IP address so that you can ssh into
this machine. Later we'll edit this security group to all communication between the clients and the server.

![Create security group](.aws-tutorial/create-security-groups.png)

With this done, we are ready to launch. After clicking launch, you'll see a window asking about a KeyPair. If you don't know what this is
or haven't done it before, select 'Create a new key pair' from the dropdown and give it a name. Download the .pem file somewhere you'll remember.
(A good place is `~/.ssh`). You will need this file to connect to the machine. If you already have a key pair, you can use that one instead.
Launch the machine and then view your instances. You should see a new entry here. Note the IP address in the 'IPv4 Public IP' column.
Open up a terminal, and type `ssh -i ~/.ssh/tiger.pem ubuntu@54.67.123.98`. (Replacing `~/.ssh/tiger.pem` with your key and the IP address with the one you just noted.
Keep the `ubuntu@` part). Type `yes` at the prompt and your in. (If this doesn't work immediately the machine might not have finished launching).

Now you want to clone your code repository and install the necessary dependencies. I'll provide the commands I used for this project. Change them to whatever you need.

Install some programs.
```bash
sudo apt update && sudo apt upgrade
sudo apt install python3-pip tmux htop
```

Install project dependencies. Make sure the dependencies can be accessed from root because the clients will have to run as root.
```bash
cd sklearn-pmlb-benchmarks
sudo -H pip3 install -r requirements
```

Once you are done with all of your dependency installing, you are ready to make the AMI.
Go back to the console, select the machine, click 'Actions > Image > Create Image'.
Give it a name and then click 'Create Image'. It'll take a few minutes to create the image, but after that you're done.
You can terminate the instance. If you need to update this image for some reason, you can repeat the process but instead of choosing the Ubuntu base image, choose your custom image.

### Editing our Security Group
We want to edit the security group we made earlier to allow TCP traffic between are instances. To do this find 'Security Groups' in the sidebar.
Then find the security group you made in the list. Take note of the Group ID. Select it, then click 'Actions > Edit inbound rules'. 
Add a rule that allows all TCP through on any port with a source of the Group ID you just noted. It should look something like:

![security group](.aws-tutorial/tcp-security-group.png)

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

