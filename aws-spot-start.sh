#!/bin/bash
export D3MOUTPUTDIR=/home/ubuntu/output
export D3MTYPE=client
export D3MTIMEOUT=300
export D3MHOST=172.31.38.133
export D3MPORT=3000

tmux -v new -d -s session './sklearn-pmlb-benchmarks/d3mstart.sh'