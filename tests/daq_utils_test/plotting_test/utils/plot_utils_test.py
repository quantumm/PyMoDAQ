from pymodaq.daq_utils.plotting.plot_utils import Data0DWithHistory
from pytest import approx, fixture
import numpy as np


@fixture
def init_qt(qtbot):
    return qtbot


class TestData0DWithHistory:
    def test_add_datas_list(self, init_qt):
        Nsamplesinhisto = 2
        data_histo = Data0DWithHistory(Nsamplesinhisto)
        dat = [[1, 2], [np.array([1]), 2], [1, 2], [1, 2], [1, 2], [1, 2]]
        for ind, d in enumerate(dat):
            data_histo.add_datas(d)
            assert data_histo._data_length == ind+1
            assert np.any(data_histo.xaxis == approx(np.linspace(max(0, ind+1-Nsamplesinhisto), ind+1,
                                                                 min(Nsamplesinhisto, ind+1)
                                                                 , endpoint=False, dtype=float)))
            assert 'data_00' in data_histo.datas
            assert 'data_01' in data_histo.datas

    def test_add_datas(self, init_qt):
        data_histo = Data0DWithHistory()
        dat = [dict(CH0=1, CH1=2.), dict(CH0=np.array([1]), CH1=2.), dict(CH0=1, CH1=2.), dict(CH0=1, CH1=2.)]
        for ind, d in enumerate(dat):
            data_histo.add_datas(d)
            assert data_histo._data_length == ind+1
            assert np.any(data_histo.xaxis == approx(np.linspace(0, ind+1, ind+1, endpoint=False)))
            assert 'CH0' in data_histo.datas
            assert 'CH1' in data_histo.datas

    def test_add_datas_and_clear(self, init_qt):
        data_histo = Data0DWithHistory()
        dat = [dict(CH0=1, CH1=2.), dict(CH0=np.array([1]), CH1=2.), dict(CH0=1, CH1=2.), dict(CH0=1, CH1=2.)]
        for ind, d in enumerate(dat):
            data_histo.add_datas(d)
        data_histo.clear_data()

        assert data_histo.datas['CH0'].size == 0
        assert data_histo.datas['CH0'].size == 0
        assert data_histo.datas['CH0'].size == 0
        assert data_histo._data_length == 0

    def test_get_data(self, init_qt):
        data_histo = Data0DWithHistory()
        dat = [dict(CH0=1, CH1=2.), dict(CH0=np.array([1.1]), CH1=1.1), dict(CH0=1, CH1=2.), dict(CH0=4, CH1=3.)]
        for ind, d in enumerate(dat):
            data_histo.add_datas(d)

        for key in data_histo.datas:
            assert key in ['CH0', 'CH1']
        assert np.any(data_histo.datas['CH0'] == approx(np.array([1, 1.1, 1, 4])))
        assert np.any(data_histo.datas['CH1'] == approx(np.array([2, 1.1, 2, 3])))