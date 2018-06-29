#!/bin/bash

cd /user_dev/src

case $D3MTYPE in
    single_client)
        echo "Running as single run client"
        ./client.py -p $D3MPORT -o $D3MHOST
        ;;
    loop_client)
        echo "Running as loop client"
        ./client.py -o $D3MHOST -p $D3MPORT --loop
        ;;
    default_scheduler)
        echo "Running as scheduler for default parameters settings"
        ./scheduler.py --resume --default $D3MOUTPUTDIR --max-connections $D3MNUMCLIENTS
        ;;
    scheduler)
        echo "Running as scheduler for all parameter settings"
        ./scheduler.py --resume $D3MOUTPUTDIR
        ;;
    *)
        echo "don't know what to do with: $D3MTYPE"
        ;;
esac
