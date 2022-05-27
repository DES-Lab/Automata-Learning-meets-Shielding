#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np
import csv
import copy

import tikzplotlib

settings=["shielded"]#, "penalty"]#, "no"]
color_dict={"shielded": 0x00ff00}#,"penalty": 0xff0000}#, "no": 0x110000, }

model_sizes = [5*9-6,8*9-12,8*14-20,11*14-30,11*18-39,14*18-52,14*22-64,17*22-80]

epochs = [1000,2000,3000,4000,5000,6000,7000,8000,9000,10000,11000,12000,13000,14000,15000,16000,17000,18000,19000,20000,21000,22000,23000,24000,25000,26000,27000,28000,29000,30000]
def constant_function(x):
    return np.full(len(epochs), x)

subplotrows=4
subplotcols=2
fig, axs = plt.subplots(subplotrows, subplotcols)
for setting in settings:
    subplotrow=0
    subplotcol=0
    data = []
    filename = "automata_sizes.csv"
    #print(f"Plotting {setting}:")
    with open(filename,'r') as csvfile:
        plots = csv.reader(csvfile, delimiter = ';')

        for i, row in enumerate(plots):
            data.append(row)
    for i, row in enumerate(data[1::4]):

        row = np.array(list(filter(None, row))).astype(float)
        color=copy.deepcopy(color_dict[setting])
        #color+=0x00001f * i
        color_string=str('0x{0:0{1}x}'.format(color,6)).replace("0x","#")
        #print(f"{i}th {setting}: {color_string}")
        axs[subplotrow%subplotrows, subplotcol%subplotcols].plot(epochs, row, color=color_string, label=row[0])
        axs[subplotrow%subplotrows, subplotcol%subplotcols].plot(epochs, constant_function(model_sizes[i]), color='#000000')
        #axs[subplotrow%subplotrows, subplotcol%subplotcols].legend()
        subplotcol=subplotcol+1
        if subplotcol == subplotcols:
            subplotrow=subplotrow+1
            subplotcol = 0
    mins = []
    maxs = []
    for i, row in enumerate(data[2::4]):
        row = np.array(list(filter(None, row))).astype(float)
        mins.append(row)
    for i, row in enumerate(data[3::4]):
        row = np.array(list(filter(None, row))).astype(float)
        maxs.append(row)
    subplotrow=0
    subplotcol=0
    for i, row in enumerate(mins):
        color=copy.deepcopy(color_dict[setting])
        #color+=0x00001f * i
        color_string=str('0x{0:0{1}x}'.format(color,6)).replace("0x","#")
        #print(f"{i}th {setting}: {color_string}")
        axs[subplotrow%subplotrows, subplotcol%subplotcols].fill_between(epochs, mins[i], maxs[i], color=color_string, alpha=0.1)
        #axs[subplotrow%subplotrows, subplotcol%subplotcols].legend()
        subplotcol=subplotcol+1
        if subplotcol == subplotcols:
            subplotrow=subplotrow+1
            subplotcol = 0

    subplotrow=0
    subplotcol=0
    for i, row in enumerate(data[0::4]):
        delim=row[0].find('.')
        axs[subplotrow%subplotrows, subplotcol%subplotcols].set_title(row[0][0:delim])
        subplotcol=subplotcol+1
        if subplotcol == subplotcols:
            subplotrow=subplotrow+1
            subplotcol = 0
for ax in axs.flat:
    ax.set(xlabel='epochs', ylabel='reward')
    ax.set_yticks(np.arange(0, 300, step=50))  # Set label locations.
#plt.xlabel('Epochs')
#plt.ylabel('Avg. Reward')
#plt.title('dummy')
plt.show()

#tikzplotlib.save("result_unsafe1.tex")
