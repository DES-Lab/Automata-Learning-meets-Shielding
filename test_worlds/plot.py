#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np
import csv
import copy


settings=["shielded", "penalty", "no"]
color_dict={"shielded": 0x00ff00, "no": 0x110000, "penalty": 0xff0000}
#filename = "penalty_summary.csv"
epochs = [1000,2000,3000,4000,5000,6000,7000,8000,9000,10000]
subplotrows=3
subplotcols=2
fig, axs = plt.subplots(subplotrows, subplotcols)
subplotrow=0
subplotcol=0
for setting in settings:
    data = []
    filename = setting + "_summary.csv"
    print(f"Plotting {setting}:")
    with open(filename,'r') as csvfile:
        plots = csv.reader(csvfile, delimiter = ';')

        for row in plots:
            data.append(row)
    for i, row in enumerate(data[1::2]):
        row = np.array(list(filter(None, row))).astype(float)
        color=copy.deepcopy(color_dict[setting])
        color+=0x0000aa * i
        color_string=str('0x{0:0{1}x}'.format(color,6)).replace("0x","#")
        print(f"{i}th {setting}: {color_string}")
        #color=str(hex(color)).replace("0x", "#")
        #print(color)
        axs[subplotrow%subplotrows, subplotcol%subplotcols].plot(epochs, row, color=color_string)
        subplotcol=subplotcol+1
        if subplotcol == subplotcols:
            subplotrow=subplotrow+1
            subplotcol = 0

    subplotrow=0
    subplotcol=0
    for i, row in enumerate(data[0::2]):
        delim=row[0].find('.')
        axs[subplotrow%subplotrows, subplotcol%subplotcols].set_title(row[0][0:delim])
        subplotcol=subplotcol+1
        if subplotcol == subplotcols:
            subplotrow=subplotrow+1
            subplotcol = 0
for ax in axs.flat:
    ax.set(xlabel='epochs', ylabel='reward')
    ax.set_yticks(np.arange(-120, 100, step=10))  # Set label locations.
#plt.legend()
#plt.xlabel('Epochs')
#plt.ylabel('Avg. Reward')
#plt.title('dummy')
plt.show()
