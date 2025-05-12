# SDN - MPLS TE disjoint path routing

## Project Overview

This project implements a multipath IP/MPLS network using SDN technologies. The network is emulated in **Mininet**, with an SDN controller developed using **Ryu**. The goal is to establish **K disjoint shortest paths** between source and destination, assign **MPLS labels**, and ensure **traffic forwarding**.

## Objectives

- Discover network topology dynamically.
- Compute the first **K disjoint shortest paths** (node/link disjoint).
- Set up **Label Switched Paths (LSPs)** using **MPLS**.
- Forward IP packets using labels.
- Measure and analyze network performance (delay, throughput,jitter).


## 🛠️ Technologies Used

- [Mininet](http://mininet.org/)
- [Ryu SDN Framework](https://osrg.github.io/ryu/)
- Python 3
- D-ITG / iPerf (for traffic generation)
- GitLab (version control and delivery)

## Installations

- Install iperf:
sudo apt install iperf3
- Install dash:
pip3 install dash
- Install D-ITG:
sudo apt update
sudo apt install g++ make libpcap-dev libpthread-stubs0-dev git
git clone https://github.com/trafficgenerator/D-ITG.git
cd D-ITG/src
make clean
make


## How to start the simulation

1. **Start Ryu controller**
ryu-manager flowmanager/flowmanager.py MPLS.py --observe-links

2. **Start Mininet Topology**
sudo mn --custom mininet-topologies/topology_1.py --mac --pre mininet-topologies/config_1 --topo mytopo --controller=remote,ip=127.0.0.1,port=6633 --switch ovs,protocols=OpenFlow13

## Iperf 

1. **Run the dash application**
python3 dash_live_traffic.py

2. **Open the browser on http://127.0.0.1:8050/**

3. **In Mininet, start host 2 in server mode and report statistics every 1 second in the iperf_h2.txt file**
h2 stdbuf -oL iperf3 -s -i 1 > iperf_h2.txt &

4. **In Mininet, start host 1 in client mode, use UDP protocol for 100 seconds and report statistics every 1 second in the iperf_h1.txt file**
h1 stdbuf -oL iperf3 -t 100 -c h2 -u -i 1 > iperf_h1.txt

## D-ITG

1. **Start h2 in server mode**
h2 ITGRecv &

2. **Start h1 in client mode, send 10000 UDP packets per second to 195.0.0.2 for 10 seconds and generate send_log and recv_log to store statistics**
h1 ITGSend -a 195.0.0.2 -T UDP -C 10000 -c 1000 -t 10000 -l send_log -x recv_log

3. **Open recv_log**
h2 ITGDec recv_log

4. **Open send_log**
h1 ITGDec send_log
