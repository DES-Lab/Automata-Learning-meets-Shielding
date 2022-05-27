# Automata Learning Meets Shielding

<p align="center">
  <img src="https://github.com/DES-Lab/Automata-Learning-meets-Shielding/blob/master/process.JPG" />
</p>
This repository contains source code and experiment data for paper "Automata Learning Meets Shielding".

# Install

Clone and install python dependencies.
```python
git clone git@github.com:DES-Lab/Automata-Learning-meets-Shielding.git
pip install -r requirements.txt
```

Install [TEMPEST](https://tempest-synthesis.org/)
```python
# To install STORM
sudo apt-get install build-essential git cmake libboost-all-dev libcln-dev libgmp-dev libginac-dev automake libglpk-dev libhwloc-dev libz3-dev libxerces-c-dev libeigen3-dev
# To install TEMPEST
git clone https://github.com/tempest-shields/tempest-shields
cd tempest-shields
mkdir build
cd build
cmake ..
# building the command line interface for tempest suffices:
make storm-main
# if you have at least 8GB of RAM and multiple cores available you can speed up the build step via
make storm-main -j${NUMBER_OF_CORES_TO_BE_USED}
```

# Run Experiments

Most of the code is based in the `q_learning.py` file. There you can find implementation 
of q-learning and shielded q-learning.

To reproduce experiments from the paper run:
```
./wrapper_q_learning.sh
```