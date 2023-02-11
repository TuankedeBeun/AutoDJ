import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.pyplot import cm

class Plotter_axis():
    def __init__(self, xtitle, ytitle):
        self.xdatasets = []
        self.ydatasets = []
        self.plottypes = []
        self.labels = []
        self.xtitle = xtitle
        self.ytitle = ytitle
        self.Nplots = 0
        self.commands = 'pass'
        self.linecounter = 0
        
    def add_plot(self, xdata, ydata, plottype, label):
        self.Nplots += 1
        self.xdatasets.append(xdata)
        self.ydatasets.append(ydata)
        self.plottypes.append(plottype)
        self.labels.append(label)
            
    def draw_plots(self, axis):
        # plotting
        axis.clear()
        for plottype, x, y, label in zip(self.plottypes, self.xdatasets, self.ydatasets, self.labels):
            if plottype == 'plot':
                axis.plot(x, y, label=label)
            elif plottype == 'histogram':
                axis.hist(x, bins=y.size, weights=y, histtype='step', label=label)
            elif plottype == 'tones':
                lw = 2.5 if (label == 'summed') else 1
                axis.hist(range(12), bins=range(13), weights=y, histtype='step', label=label, lw=lw)
                axis.set_xlim((0, 12))
                x_ticks = list(range(12))
                for i in range(12): x_ticks[i] += 0.5
                axis.set_xticks(x_ticks)
                axis.set_xticklabels(x)
            elif plottype == 'hline':
                color = cm.hsv(self.linecounter*0.618 % 1)
                self.linecounter += 1
                axis.axhline(y=y, xmin=x[0], xmax=x[1], label=label, ls='--', c=color, alpha=0.5)
            elif plottype == 'vline':
                color = cm.hsv(self.linecounter*0.618 % 1)
                self.linecounter += 1
                axis.axvline(x=x, ymin=y[0], ymax=y[1], label=label, ls='--', c=color, alpha=0.5)
        
        # layout
        axis.set_xlabel(self.xtitle, fontsize=12, color='w')
        axis.set_ylabel(self.ytitle, fontsize=12, color='w')
        axis.set_facecolor('#111111')
        axis.tick_params(axis='both', colors='w', labelsize=10)
        for spine in axis.spines: axis.spines[spine].set_color('w')
        if self.Nplots > 1: 
            legend = axis.legend(loc='upper right', fontsize=7, facecolor='#222222')
            for text in legend.get_texts(): text.set_color('w')
        
class Plotter():
    def __init__(self, title, figsize=(12,8), sharex=True):
        self.Naxes = 0
        self.sharex = sharex
        self.axis_objects = []
        self.fig = plt.figure(title,
                              figsize=figsize, 
                              facecolor='#333333',
                              clear=True)
        self.fig.set_visible(False)
        #self.fig.suptitle(title, fontsize=30)
        
    def add_axis(self, xtitle, ytitle):
        new_axis = Plotter_axis(xtitle, ytitle)
        self.axis_objects.append(new_axis)
        self.Naxes += 1
        return new_axis
        
    def draw_axes(self):
        # create axes
        self.fig.clear()
        axes = self.fig.subplots(nrows=self.Naxes, ncols=1, sharex=self.sharex)
        self.fig.set_visible(True)
        
        # draw plots
        for axis, axis_object in zip(axes, self.axis_objects):
            axis_object.draw_plots(axis)
        plt.show()

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
