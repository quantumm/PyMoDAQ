from qtpy import QtWidgets
from qtpy.QtCore import QObject, Slot, Signal
import sys
from multipledispatch import dispatch
from pymodaq.daq_utils.messenger import deprecation_msg
import pymodaq.daq_utils.daq_utils as utils
from pymodaq.daq_utils.plotting.data_viewers.viewer0D_GUI import Ui_Form
from pymodaq.daq_utils.plotting.data_viewers.viewerbase import ViewerError
from pymodaq.daq_utils.plotting.plot_utils import Data0DWithHistory
from pymodaq.daq_utils.plotting.plot_utils import label_formatter
import numpy as np
from collections import OrderedDict
import datetime

logger = utils.set_logger(utils.get_module_name(__file__))


class Viewer0D(QtWidgets.QWidget, QObject):
    data_to_export_signal = Signal(OrderedDict)  # edict(name=self.DAQ_type,data0D=None,data1D=None,data2D=None)

    def __init__(self, parent=None, dock=None):
        """

        """
        
        super(Viewer0D, self).__init__()
        if parent is None:
            parent = QtWidgets.QWidget()
        self.parent = parent
        self.title = 'viewer0D'  # is changed when used from DAQ_Viewer
        self.ui = Ui_Form()
        self.ui.setupUi(parent)

        self.ui.xaxis_item = self.ui.Graph1D.plotItem.getAxis('bottom')

        self._labels = []
        self.viewer_type = 'Data0D'
        self.wait_time = 1000

        self.plot_channels = []
        self.plot_colors = utils.plot_colors

        self.Nsamples = self.ui.Nhistory_sb.value()
        self.data_history = Data0DWithHistory(self.Nsamples)

        self.legend = self.ui.Graph1D.plotItem.addLegend()
        self.data_to_export = None
        self.list_items = None

        # #Connecting buttons:
        self.ui.clear_pb.clicked.connect(self.clear_data)
        self.ui.Nhistory_sb.valueChanged.connect(self.data_history.update_history_length)
        self.ui.show_datalist_pb.clicked.connect(self.show_data_list)

        self.show_data_list(False)

    def clear_data(self):
        self.data_history.clear_data()
        for plot in self.plot_channels:
            plot.setData(x=np.array([]), y=np.array([]))

    @dispatch(utils.DataFromPlugins)
    def show_data(self, datas: utils.DataFromPlugins):
        self._show_data(datas['data'])
        if datas['labels'] != [] and datas['labels'] != self.labels:
            self.labels = datas['labels']

    @dispatch(list)
    def show_data(self, datas: list):
        deprecation_msg(f'Show_data method from Viewer0D accept as argument a DataFromPlugins object', stacklevel=3)
        if not isinstance(datas[0], np.ndarray):
            data_as_ndarray = []
            for dat in datas:
                if isinstance(dat, list):
                    data_as_ndarray.append(np.array(dat))
                else:
                    data_as_ndarray.append(np.array([dat]))
        dat = utils.DataFromPlugins(dim='Data0D', data=data_as_ndarray)
        self.show_data(dat)

    def init_channels(self, datas):
        self.update_channels()
        Ndatas = len(datas)
        if self.labels == [] or len(self.labels) != Ndatas:
            self._labels = [label_formatter(ind) for ind in range(Ndatas)]

        self.plot_channels = []
        self.ui.values_list.clear()
        self.ui.values_list.addItems(['{:.06e}'.format(data[0]) for data in datas])
        self.list_items = [self.ui.values_list.item(ind) for ind in range(self.ui.values_list.count())]
        for ind in range(len(datas)):
            channel = self.ui.Graph1D.plot(y=np.array([]))
            channel.setPen(self.plot_colors[ind])
            self.plot_channels.append(channel)
        self.update_labels(self._labels)

    @Slot(list)
    def _show_data(self, datas: list):
        """

        Parameters
        ----------
        datas: list of list of one float

        """
        try:
            self.data_to_export = OrderedDict(name=self.title, data0D=OrderedDict(), data1D=None, data2D=None)
            if self.plot_channels is None or len(self.plot_channels) != len(datas):
                self.init_channels(datas)
            self.data_history.add_datas(dict(zip(self.labels, datas)))

            self.update_list_items(datas)
            self.update_plots()
        except Exception as e:
            logger.exception(str(e))

    def update_list_items(self, datas):
        for ind, data in enumerate(datas):
            self.list_items[ind].setText('{:.06e}'.format(data[0]))

    def show_data_list(self, state=None):
        if state is None:
            state = self.ui.show_datalist_pb.isChecked()
        self.ui.values_list.setVisible(state)

    @Slot(list)
    def show_data_temp(self, datas):
        """
        to plot temporary data, for instance when all pixels are not yet populated...
        """
        pass

    def update_plots(self):

        for ind_data, plot in enumerate(self.plot_channels):
            plot.setData(x=self.data_history.xaxis, y=self.data_history.datas[self.labels[ind_data]])

        self.data_to_export['acq_time_s'] = datetime.datetime.now().timestamp()
        self.data_to_export_signal.emit(self.data_to_export)

    def update_channels(self):
        if self.plot_channels is not None:
            for ind, item in enumerate(self.plot_channels):
                self.legend.removeItem(item.name())
                self.ui.Graph1D.removeItem(item)
            self.plot_channels = None

    def update_labels(self, labels):
        try:
            items = [item[1].text for item in self.legend.items]
            for item in items:
                self.legend.removeItem(item)

            if len(labels) == len(self.plot_channels):
                for ind, channel in enumerate(self.plot_channels):
                    self.legend.addItem(channel, self._labels[ind])
        except Exception as e:
            logger.warning(str(e) + 'plot channels not yet declared')

    def update_status(self, txt, wait_time=0):
        logger.info(txt)

    def update_x_axis(self, Nhistory):
        self.Nsamples = Nhistory
        self.x_axis = np.linspace(0, self.Nsamples - 1, self.Nsamples)

    @property
    def labels(self):
        return self._labels

    @labels.setter
    def labels(self, labels):
        if len(labels) != len(self.plot_channels):
            raise ViewerError(f'The new labels {labels} are not consistent with the number of data curves')
        self._labels = labels
        self.update_labels(labels)


if __name__ == '__main__':  # pragma: no cover
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    prog = Viewer0D(Form)
    from pymodaq.daq_utils.daq_utils import gauss1D

    x = np.linspace(0, 200, 201)
    y1 = gauss1D(x, 75, 25)
    y2 = gauss1D(x, 120, 50, 2)
    Form.show()
    for ind, data in enumerate(y1):
        prog.show_data([np.array([data]), np.array([y2[ind]])])
        QtWidgets.QApplication.processEvents()

    sys.exit(app.exec_())
