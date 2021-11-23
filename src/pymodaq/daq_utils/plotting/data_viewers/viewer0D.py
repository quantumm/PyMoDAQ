from qtpy import QtWidgets
from qtpy.QtCore import QObject, Slot, Signal
import sys
from multipledispatch import dispatch
from pymodaq.daq_utils.messenger import deprecation_msg
import pymodaq.daq_utils.daq_utils as utils
from pymodaq.daq_utils.plotting.data_viewers.viewer0D_GUI import Ui_Form
from pymodaq.daq_utils.plotting.data_viewers.viewerbase import ViewerError
import numpy as np
from collections import OrderedDict
import datetime

logger = utils.set_logger(utils.get_module_name(__file__))


def default_label_formatter(ind: int) -> str:
    return f'CH{ind:02.0f}'


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

        # self.ui.statusbar = QtWidgets.QStatusBar(parent)
        # self.ui.statusbar.setMaximumHeight(15)
        # self.ui.StatusBarLayout.addWidget(self.ui.statusbar)
        # self.ui.status_message = QtWidgets.QLabel()
        # self.ui.status_message.setMaximumHeight(15)
        # self.ui.statusbar.addWidget(self.ui.status_message)

        self.ui.xaxis_item = self.ui.Graph1D.plotItem.getAxis('bottom')

        self._labels = []
        self.viewer_type = 'Data0D'
        self.wait_time = 1000

        self.plot_channels = None
        self.plot_colors = utils.plot_colors

        self.Nsamples = self.ui.Nhistory_sb.value()

        self.x_axis = np.linspace(0, self.Nsamples - 1, self.Nsamples)
        self.datas = []  # datas on each channel. list of 1D arrays
        self.legend = self.ui.Graph1D.plotItem.addLegend()
        self.data_to_export = None
        self.list_items = None

        # #Connecting buttons:
        self.ui.clear_pb.clicked.connect(self.clear_data)
        self.ui.Nhistory_sb.valueChanged.connect(self.update_x_axis)
        self.ui.show_datalist_pb.clicked.connect(self.show_data_list)

        self.show_data_list(False)

    def clear_data(self):
        N = len(self.datas)
        self.datas = []
        for ind in range(N):
            self.datas.append(np.array([]))
        self.x_axis = np.array([])
        for ind_plot, data in enumerate(self.datas):
            self.plot_channels[ind_plot].setData(x=self.x_axis, y=data)

    @dispatch(utils.DataFromPlugins)
    def show_data(self, datas: utils.DataFromPlugins):
        self._show_data(datas['data'])
        if datas['labels'] != [] and datas['labels'] != self.labels:
            self.update_labels(datas['labels'])

    @dispatch(list)
    def show_data(self, datas: list):
        deprecation_msg(f'Show_data method from Viewer0D accept as argument a DataFromPlugins object', stacklevel=3)
        self._show_data(datas)

    def init_channels(self, datas):
        self.update_channels()
        Ndatas = len(datas)
        if self.labels == [] or len(self.labels) != Ndatas:
            self._labels = [default_label_formatter(ind) for ind in range(Ndatas)]

        self.plot_channels = []
        self.datas = []
        self.ui.values_list.clear()
        self.ui.values_list.addItems(['{:.06e}'.format(data[0]) for data in datas])
        self.list_items = [self.ui.values_list.item(ind) for ind in range(self.ui.values_list.count())]
        for ind in range(len(datas)):
            self.datas.append(np.array([]))
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

            self.update_list_items(datas)
            self.update_Graph1D(datas)
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

    def update_Graph1D(self, datas):
        try:
            data_tot = []
            L = len(self.datas[0]) + 1
            if L > self.Nsamples:
                self.x_axis += 1
            else:
                self.x_axis = np.linspace(0, L - 1, L)
            for ind_plot, data in enumerate(datas):
                data_tmp = self.datas[ind_plot]
                data_tmp = np.append(data_tmp, data)

                if len(data_tmp) > self.Nsamples:
                    data_tmp = data_tmp[L - self.Nsamples:]

                data_tot.append(data_tmp)

                self.plot_channels[ind_plot].setData(x=self.x_axis, y=data_tmp)
                self.data_to_export['data0D']['CH{:03d}'.format(ind_plot)] = utils.DataToExport(name=self.title,
                                                                                                data=data[0],
                                                                                                source='raw')
            self.datas = data_tot

            self.data_to_export['acq_time_s'] = datetime.datetime.now().timestamp()
            self.data_to_export_signal.emit(self.data_to_export)

        except Exception as e:
            logger.exception(str(e))

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
        prog.show_data([[data], [y2[ind]]])
        QtWidgets.QApplication.processEvents()

    sys.exit(app.exec_())
