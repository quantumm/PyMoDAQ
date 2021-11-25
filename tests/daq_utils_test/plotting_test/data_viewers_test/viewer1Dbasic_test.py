from qtpy import QtWidgets
from pytest import approx, mark, fixture, raises
import numpy as np

from pymodaq.daq_utils.plotting.data_viewers.viewer1Dbasic import Viewer1DBasic
from pymodaq.daq_utils.conftests import qtbotskip
from pymodaq.daq_utils import daq_utils as utils
from pymodaq.daq_utils.plotting.plot_utils import label_formatter

pytestmark = mark.skipif(qtbotskip, reason='qtbot issues but tested locally')


@fixture
def init_prog(qtbot):
    form = QtWidgets.QWidget()
    prog = Viewer1DBasic(form)
    qtbot.addWidget(form)
    yield prog, qtbot
    form.close()


def init_data():
    x = np.linspace(-10, 200, 201)
    y1 = utils.gauss1D(x, 75, 25)
    y2 = utils.gauss1D(x, 120, 50, 2)
    return x, y1, y2


class MainTest:
    def maintest(self, init_prog):
        prog, qtbot = init_prog
        x, y1, y2 = init_data()
        prog.show_data([y1, y2])

        assert np.any(prog.x_axis == approx(np.linspace(0, len(y1), len(y1), endpoint=False)))

        prog.x_axis = x
        assert np.any(prog.x_axis == approx(x))

        assert prog.labels == [label_formatter(ind) for ind in range(2)]

        NEW_LABEL = ['label1', 'label2']
        prog.labels = NEW_LABEL

        assert prog.labels == NEW_LABEL


class TestViewer1DBasic:
    def test_init(self, init_prog):
        prog, qtbot = init_prog
        assert isinstance(prog.parent, QtWidgets.QWidget)
        assert not prog.datas
        assert not prog._x_axis

    def test_noparent(self, qtbot):
        prog = Viewer1DBasic()
        assert isinstance(prog.parent, QtWidgets.QWidget)
        qtbot.addWidget(prog.parent)

    def test_show(self, init_prog):
        prog, qtbot = init_prog
        prog.parent.setVisible(False)
        assert not prog.parent.isVisible()
        prog.show()
        assert prog.parent.isVisible()
        prog.show(False)
        assert not prog.parent.isVisible()

    def show_data(self, init_prog):
        prog, qtbot = init_prog
        x, y1, y2 = init_data()
        prog.show_data([y1, y2])

        assert np.any(prog.x_axis == approx(np.linspace(0, len(y1), len(y1), endpoint=False)))
        prog.x_axis = x
        assert np.any(prog.x_axis == approx(x))
        assert prog.datas == [y1, y2]

    def test_update_labels(self, init_prog):
        prog, qtbot = init_prog
        x, y1, y2 = init_data()
        prog.show_data([y1, y2])
        assert prog.labels == [label_formatter(ind) for ind in range(2)]
        NEW_LABEL = ['label1', 'label2']
        prog.labels = NEW_LABEL
        assert prog.labels == NEW_LABEL

    def test_less_labels_than_plot(self, init_prog):
        prog, qtbot = init_prog
        x, y1, y2 = init_data()
        prog.show_data([y1, y2])

        NEW_LABEL = 'label1'
        prog.labels = [NEW_LABEL]

        assert prog.labels == [NEW_LABEL, label_formatter(1)]

    def test_more_labels_than_plot(self, init_prog):
        prog, qtbot = init_prog
        x, y1, y2 = init_data()
        prog.show_data([y1, y2])

        NEW_LABEL = 'label1'
        prog.labels = [NEW_LABEL, NEW_LABEL, NEW_LABEL]

        assert prog.labels == [NEW_LABEL, NEW_LABEL]

    def test_x_axis(self, init_prog):
        prog, qtbot = init_prog
        x, y1, y2 = init_data()
        prog.show_data([y1, y2])

        label = 'this is x axis'
        units = 'nm'

        x_axis = utils.Axis(data=x, label=label, units=units)
        prog.x_axis = x_axis

        assert np.any(prog.x_axis == approx(x))
        assert prog.get_axis_label('bottom') == label
        assert prog.get_axis_units('bottom') == units

    def test_x_axis_ndarray(self, init_prog):
        prog, qtbot = init_prog
        x, y1, y2 = init_data()
        prog.show_data([y1, y2])
        prog.x_axis = x

    def test_x_axis_error(self, init_prog):
        prog, qtbot = init_prog
        with raises(TypeError):
            prog.x_axis = 'not a valid axis'

    def test_update_region(self, init_prog):
        prog, qtbot = init_prog

        with qtbot.waitSignal(prog.roi_region_signal) as blocker:
            prog.roi_region.lineMoved(0)

        assert blocker.args[0] == prog.roi_region.getRegion()

    def test_update_line(self, init_prog):
        prog, qtbot = init_prog

        LINE_POS = 20

        with qtbot.waitSignal(prog.roi_line_signal) as blocker:
            prog.roi_line.setPos(LINE_POS)

        assert blocker.args[0] == prog.roi_line.getPos()[0]

    def test_remove_plots(self, init_prog):
        prog, qtbot = init_prog
        x, y1, y2 = init_data()
        prog.show_data([y1])
        assert [item[1].text for item in prog.legend.items] == [label_formatter(ind) for ind in range(1)]

        prog.show_data([y1, y2])
        assert [item[1].text for item in prog.legend.items] == [label_formatter(ind) for ind in range(2)]

        prog.show_data([y1])
        assert [item[1].text for item in prog.legend.items] == [label_formatter(ind) for ind in range(1)]
