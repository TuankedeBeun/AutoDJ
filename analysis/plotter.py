import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

class Plotter():
    def __init__(self, figsize=(18,9)):
        self.Naxes = 0
        self.tdatasets = []
        self.ydatasets = []
        self.ytitles = []
        self.fig = plt.figure(figsize=figsize, 
                              facecolor='#333333',
                              clear=True)
        
    def add_plot(self, time, data, description):
        self.fig.clear()
        self.Naxes += 1
        if(self.Naxes == 1):
            self.axes = [self.fig.subplots(nrows=1, ncols=1, sharex=True)]
        else:
            self.axes = self.fig.subplots(nrows=self.Naxes, ncols=1, sharex=True)
        
        self.tdatasets.append(time)
        self.ydatasets.append(data)
        self.ytitles.append(description)
        
    def draw_plots(self, t_range=None):
        for axis, tdata, ydata, ytitle in zip(self.axes, self.tdatasets, self.ydatasets, self.ytitles):
            axis.clear()
            axis.set_ylabel(ytitle, fontsize=20, color='w')
            axis.set_facecolor('#111111')
            axis.tick_params(axis='both', colors='w', labelsize=15)
            for spine in axis.spines: axis.spines[spine].set_color('w')
            
            if t_range:
                index_left = int(np.argwhere(tdata > t_range[0])[0])
                index_right = int(np.argwhere(tdata > t_range[1])[0])
                axis.plot(tdata[index_left: index_right],
                          ydata[index_left: index_right],
                          linewidth=2)
            else:
                axis.plot(tdata, ydata)
            
        axis.set_xlabel('time (s)', fontsize=20, color='w')
        self.fig.show()

class Animation_plotter():
    def __init__(self, time, xdata, ydata, xlabel, ylabel):
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(1,1,1)
        self.time = time
        self.xdata = xdata
        self.ydata = ydata
        self.single_plot(0)
        self.ax.set(xlabel=xlabel, ylabel=ylabel)
        self.textcoords = (0.9*self.xdata.max(), 0.9*self.ydata.max())
        
    def play(self):
        animation.FuncAnimation(self.fig, self.single_plot, interval=15)
        plt.show()
    
    def single_plot(self, i):
        self.ax.clear()
        self.ax.text(self.textcoords[0], self.textcoords[1], 'time: %.1f s' % self.time[i])
        self.ax.plot(self.xdata[i], self.ydata[i])
        self.ax.set_ylim(0,6e6)
