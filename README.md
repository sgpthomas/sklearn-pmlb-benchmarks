# Docker Image, Data For D3M Kubernetes Example

Perform the following actions to create a gitlab project to build a container for your project and run the container onthe D3M K8s cluster. These instructions will also allow your container to run on the Texas Advanced Computing Center (TACC) HPC system.

## Create a Gitlab project on the D3M gitlab
Go to https://gitlab.datadrivendiscovery.org/dashboard/projects and click on new project.  Follow the provide instructions to create your gitlab project

### .gitlab-ci.yml
Copy the .gitlab-ci-yml file from this project into your own project and alter lines 12 and 13
```
- docker build -t "$CI_REGISTRY_IMAGE:D3M_Your_Team_Image_Name" -f Dockerfile .
- docker push "$CI_REGISTRY_IMAGE:D3M_Your_Team_Image_Name"
```
"D3M_Your_Team_Image_Name" should be replace with the container image tag for your team. You can choose any tag name for your container(s) except for the container that your team wants to evaluation team to use.  That container needs to be tag with the "live" tag. 

This file will configure the gitlab to build a docker container and push the container image to the gitlab registry. 

#### Important (D3M_Your_Team_Image_Name)
D3M_Your_Team_Image_Name should be change to "live" for the container(s) that will be used by the evaluation team.


### Dockerfile
The Dockerfile in the project is an example that will build a container image to run your code on the D3M K8s cluster
```
FROM ubuntu:16.04
RUN apt-get update && apt-get install -y python
RUN mkdir -p /user_dev
RUN mkdir -p /output
RUN mkdir -p /input
RUN mkdir -p /work

COPY d3mStart.sh /user_dev
RUN chmod a+x /user_dev/d3mStart.sh

COPY example.py /user_dev

ENTRYPOINT ["/user_dev/d3mStart.sh"]
``` 
1. FROM ubuntu:16.04
  * This will use the latest ubuntu 16.04 as a base container image.  You can start with any container image as as long as it is base off of ubuntu:16.04 or nvidia/cuda:8.0-cudnn6-devel-ubuntu16.04(if you are building for GPU)
2. RUN apt-get update && apt-get install -y python
  * Updates the packages list and installs the python binary/libraries needed by this container.  This is a good location to add(add to end of line, separated by space) other packages/libraries needed for your code. 
3. Run mkdir ... (lines 3-6) must be included in your project's Dockerfile
  * Creates a set of directories in the containers that the example code will need. The /input and /output directories work in concert with the definitions in example.yaml for mounting your seed data and output directories. However you will be using the enviromental variables D3MINPUTDIR and D3MOUTPUTDIR to determine your input and output directories. This is to support running in both  D3M K8s and TACC systems. 
4. d3mStart.sh (line 8-9) must be included in your project's Dockerfile
  * d3mStart.sh will execute your projects python code. 
5. COPY example.py /user_dev 
  * example for copying your project python code to the container
6. ENTRYPOINT ["/user_dev/d3mStart.sh"]
  * Configures the docker container to execute the copied over python code upon startup
7. It is recommended that all project code and extras be place under the /user_dev directory or subdirectories(created by your project). TACC system might override other directories such as /home (and all its subdirectories).  /user_dev has been tested to be safe against modification bu the TACC system.


#### d3mStart.sh[case - search test ts2ta3}
There is a case structure in the script for you edit to execute your project's code for the different D3M scenarios .
The enviromental variable D3MRUN is set in the yaml file that creates your Pod/Service/Deployment.
This is where you would pass parameters into your code or call different code base on the value D3MRUN is set to.  You can have your python code determine what D3MRUN is set to and trigger off of that(in which case you can delete line 7 to 24 and just execute your python code). Lines 7-23 is just one way to handle the different configurations. 

### example.py
This python code is provided as example on how to determine and access the data directory and and write to an output directory. The data and output directories are configure in example.yaml for the D3M K8s system and preconfigure for the TACC system.  

This python example also goes into an infinite sleep loop.  This was done to keep the container alive(in case a user wanted to access the container) when it was done executing/process its tasks.  This SHOULD NOT be done for your real analytic container unless you are debugging.


### example.yaml
This yaml file tells K8s the container to run and which directories to mount etc.
```
apiVersion: v1
kind: Pod
metadata:
  name: d3m-example-pod
spec:
  restartPolicy: Never
  containers:
  - name: d3m-example
    image: registry.datadrivendiscovery.org/d3m/d3m-summer2018-run-example:D3M_Your_Team_Image_Name
    env:
    - name: D3MRUN
      value: "search"
    - name: D3MINPUTDIR
      value: "/input"
    - name: D3MOUTPUTDIR
      value: "/output"
    volumeMounts:
      - name: input-data
        mountPath: /input
        readOnly: true
      - name: output-data
        mountPath: /output
        readOnly: false
    resources:
      requests:
        memory: 512Mi
        cpu: 1
  imagePullSecrets:
  - name: regcred
  volumes:
  - name: input-data
    hostPath:
      path: /opt/datasets/seed_datasets_current/185_baseball
      type: Directory
  - name: output-data
    persistentVolumeClaim:
      claimName: eval-output-pv-claim
```
Things to be aware of:
1. Lines 4 (name: d3mexample-pod) and 8 (- name: d3m-example)
  * The Pod and container name for your project. You should name them appropriately for your team and project
2. Line 9 (image: registry.datadrivendiscovery.org/wlau/d3m-summer2018-run-example:D3M_Your_Team_Image_Name)
  * The container image you want to run.  Go to your registry page on your gitlab project to get the url for your project's container image
3. Lines 26 to 33 - 
  * The persistent volumes that contains the data your code should operate on and the output volume. During sequestered evaluation, the hostpath will be replaced with those containing sequestered data.
  * Lines 17 - 23 - This mounts the hostpath and pv-claim to local directories in the container
    * Lines 21-23 and 35-37 are the mounts and claims for the output directories.
      * The input mount should always be mounted readonly (line 20)
    * Lines 14-16 and 27-30 are the mounts and hostpath for the input
      * Only one container can mount this as writabe (readOnly: false)
4. Line 24-27 are the resource declaration. These lines must be included. However, you can adjust the cpu and the memory value to match your needs. Also keep in mind that each namespace has a quota of 14 CPU and 100 GB RAM. Please see [Specifying resource declaration](https://datadrivendiscovery.org/wiki/display/gov/Specifying+Resources+Declaration) page for more. 
5. Lines 29 (- name: regcred)
  * This is the registry access token. You should not have to rename the label as long as regred is use in step #3 in "Usage on D3M K8s" [read more](https://datadrivendiscovery.org/wiki/display/gov/Pulling-From-Private-Repository).  
6. hostPath: This section configures your container to mount a data set for a run.  You can change path(line 26) to mount different datasets for different test runs. 
  * example - path: /opt/datasets/seed_datasets_current/185_baseball
  * currently available seed datasets
  ```
  1491_one_hundred_plants_margin  534_cps_85_wages
  1567_poker_hand                 56_sunspots
  185_baseball                    57_hypothyroid
  196_autoMpg                     59_umls
  22_handgeometry                 60_jester
  26_radon_seed                   66_chlorineConcentration
  27_wordLevels                   6_70_com_amazon
  299_libras_move                 6_86_com_DBLP
  30_personae                     DS01876
  313_spectrometer                LL1_net_nomination_seed
  31_urbansound                   LL1_penn_fudan_pedestrian
  32_wikiqa                       uu1_datasmash
  38_sick                         uu2_gp_hyperparameter_estimation
  4550_MiceProtein                uu3_world_development_indicators
  49_facebook                     uu4_SPECT
  ```
  * search_config.json and test_config.json are in each of the directories.
8. imagePullPolicy: Always - During development and testing, you may want to add this to your yaml file. This will tell K8s to always download the container image before deploying it.
   ```
   containers:
    - name: d3m-example
      image: registry.datadrivendiscovery.org/d3m/d3m-summer2018-run-example:D3M_Your_Team_Image_Name
      imagePullPolicy: Always 
   ```
9. D3MRUN (line 12) - During POD/Service creation, this env value should be change to search , test or ta2ta3 etc
10. Lines 13 to 15 should always be in your yaml file and therer values need to be "/input" and "/output" for D3MINPUTDIR and D3MOUTPUTDIR respectively


## Usage on D3M K8s
1. git clone this project
  * git clone https://gitlab.datadrivendiscovery.org/wlau/d3m-summer2018-run-example.git or the url for your git project
    * git clone is here to get a copy of your projects yaml file. You can just download your yaml file instead of git cloning your entire project  

2. install your kubernetes config file in .kube directory OR Use the Jump Server for the D3M project ( which is already configure to use K8s for your team)

3. Create a Gitlab registry access token with read_registry permission by following instruction from this page https://datadrivendiscovery.org/wiki/display/gov/Pulling-From-Private-Repository

4. Use kubectl to start the Pod/Service define in your yaml file
  * kubctl create -f example.yaml
    * The above command will start all the containers define in the example.yaml file

# Summer Eval Information
This information is here to help you setup and run your system on the D3M K8s system
1. These environmental variables are always available and they are set in your yaml file
  * D3MRUN
    * values[search,test,ta2ta3]
        * search - In standalone mode perform search
        * test   - In standalone mode perform test
        * ta2ta3 - You are running with a TA2 and TA3 are running in combination - TA should expect 
  * D3MTESTOPT - This environmental variable is expected to be used for when D3MRUN='test'. This is the full path and filename (as seem from your container) for the executable your container will be testing on. 
  * D3MINPUTDIR - The path to the data directory that the executable will use in your container
  * D3MOUTPUTDIR - The path to the output directory that the executable will use in your container
  * D3MCPU - How many CPUs are available to your container
  * D3MRAM - The amount of ram that is available to your container
  * D3MTIMEOUT - time in minutes how long the system will allow you to run for.  In standalone/test phase this is not enforce.  During eval., The orchestration system will shutdown your container when timeout is exceeded
2. config files:
  * search_config.json - A search_config.json file exist in each dataset directory.
  * test_config.json
    * A search and test config file exist in each dataset directory. In your container, these files will be at /${D3MINPUTDIR}/search_config.json and /${D3MINPUTDIR}/test_config.json
    
  
  Important Config Notes:
  ---
  1. In your yaml file(that is use to start your system/pod/service):
    * D3MCPU in the env section should match the cpu in the resources section:
    * D3MRAM in the env section should match the memory in the resources section:
      * The orchestration system will ensure that they match during eval
 

  
  Other Notes:
  ---
  1. The environmental variables are set in the yaml file that start your Pod in the K8s system. For this project, it is in the example.yaml
  2. This example has the d3mstart.sh as the ENTRYPOINT in its Dockerfile. d3mstart.sh uses the D3M projects environmental variables to determine what the container is being started for and executes the appropriate code with correct parameters.
    * Your system does not have to do this as long as it uses the environmental variables to decide what to do.
  3. You are expected to modify d3mstart.sh to call your project code correctly
  4. The hostPath which you can configure to determine which dataset to run on is specify in item #6 in the example.yaml section in this readme



## Delete Existing Pods/ Clean up
The prefined output volume can only be mounted on a single pod. So this example pod must be removed to remove the mount lock. To delete the pod created in this example run `kubectl delete pod d3m-example-pod`. See [Ways of removing existing pod](https://gitlab.datadrivendiscovery.org/d3m/d3m-summer2018-run-example/blob/master/README.md#ways-to-delete-existing-running-pods) for more.

### Ways to delete existing running Pods
1. kubectl delete pod {POD_name}
    * replace {POD_name} with the name of your Pod.

2. kubectl delete -f {filename}
    * {filename} the same file that you use to create the Pod.
    
3. kubectl delete pods --all
    * delete all the pods 

Link to use kubectl to delete your pod

## Helpful Notes:
1. Use the following command to access a container in your pod
  * kubectl exec -it {pod-name} -- /bin/bash
2. When the Pod containers multiple containers, to specify which containers
  * kubectl exec -it {pod-name} --container {container name} -- /bin/bash
3. To copy files to/from pods and containers 
  * From a pod to localhost: kubectl cp {file-spec-src} {file-spec-dest}
  * Pod in a specific container: kubectl cp {file-spec-src} {file-spec-dest} -c {specific-container}
  * Copy /tmp/foo local file to /tmp/bar in a remote pod in namespace: kubectl cp /tmp/foo {some-namespace}/{some-pod}:/tmp/bar
  * Copy /tmp/foo from a remote pod to /tmp/bar locally: kubectl cp {some-namespace}/{some-pod}:/tmp/foo /tmp/bar
4. Get detail status on your pod
  * kubectl describe pod {pod-name}
