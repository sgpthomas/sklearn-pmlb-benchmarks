#!/bin/bash

cd `dirname $0`

case $D3MTYPE in
    client)
        echo "Running as client"
        ./src/client.py -p $D3MPORT -o $D3MHOST
        ;;
    default_scheduler)
        echo "Running as scheduler for default parameters settings"
        ./src/scheduler.py --resume --default $D3MOUTPUTDIR --max-connections $D3MNUMCLIENTS
        ;;
    scheduler)
        echo "Running as scheduler for all parameter settings"
        ./src/scheduler.py --resume $D3MOUTPUTDIR --max-connections $D3MNUMCLIENTS
        ;;
    *)
        echo "don't know what to do with: $D3MTYPE"
        ;;
esac
