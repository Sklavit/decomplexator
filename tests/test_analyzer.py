import os
from datetime import datetime
import random

from decomplexator.analyzer import ComplexityAnalyzer, AnalyzerGroup

from tests import BaseTests


def _path(*elem):
    here = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(here, *elem))


class AnalyzerBaseTests(BaseTests):

    FILE_NAME = 'test1.py'
    DUMMY_PATH = os.path.join('/dummy', FILE_NAME)
    FILE_CONTENT = open(_path('data', FILE_NAME)).read()
    DT = datetime(2018, 8, 2, 12, 22, 15, 0)
    DT_FMT = DT.isoformat()
    COMPLEXITY = {
        DUMMY_PATH: {
            DT_FMT: {
                'fun1': (0, 1, 'fun1'),
                'fun2': (1, 2, 'fun2'),
            },
        },
    }
    MAX_COMPLEXITY = 10

    def _gen_complexity(cls, date, num_records=2, max_entries_per_record=2):
        ret = {}
        for i in range(num_records):
            filename = 'test%d.py' % i
            run_data = ret.setdefault(filename, {date: {}})
            num_entries = random.randint(0, max_entries_per_record)
            for n in range(num_entries):
                entry_name = 'fun%d' % n
                data = (random.randint(0, cls.MAX_COMPLEXITY), random.randint(0, cls.MAX_COMPLEXITY), entry_name)
                run_data[date][entry_name] = data
        return ret


class TestAnalyzer(AnalyzerBaseTests):

    def test_analyze(self, mocker):
        fake_dt = mocker.MagicMock()
        mocker.patch('decomplexator.analyzer.datetime', fake_dt)
        fake_dt.utcnow = mocker.MagicMock(return_value=self.DT)
        fake = mocker.mock_open(read_data=self.FILE_CONTENT)
        mocker.patch('builtins.open', fake)
        mocker.patch.dict('os.environ', self._environ())
        ca = ComplexityAnalyzer(self.DUMMY_PATH)
        ca.analyze()
        summary = ca.summary()
        run_data = summary[self.DUMMY_PATH][self.DT_FMT]
        for name in ['fun1', 'fun2']:
            assert run_data[name] == self.COMPLEXITY[self.DUMMY_PATH][self.DT_FMT][name]

    def test_analyze_with_fname(self, mocker):
        fake_dt = mocker.MagicMock()
        mocker.patch('decomplexator.analyzer.datetime', fake_dt)
        fake_dt.utcnow = mocker.MagicMock(return_value=self.DT)
        fake = mocker.mock_open(read_data=self.FILE_CONTENT)
        mocker.patch('builtins.open', fake)
        mocker.patch.dict('os.environ', self._environ())
        ca = ComplexityAnalyzer()
        ca.analyze(self.DUMMY_PATH)
        summary = ca.summary()
        run_data = summary[self.DUMMY_PATH][self.DT_FMT]
        for name in ['fun1', 'fun2']:
            assert run_data[name] == self.COMPLEXITY[self.DUMMY_PATH][self.DT_FMT][name]

    def test_has_data(self, mocker):
        fake_dt = mocker.MagicMock()
        mocker.patch('decomplexator.analyzer.datetime', fake_dt)
        fake_dt.utcnow = mocker.MagicMock(return_value=self.DT)
        fake = mocker.mock_open(read_data=self.FILE_CONTENT)
        mocker.patch('builtins.open', fake)
        mocker.patch.dict('os.environ', self._environ())
        ca = ComplexityAnalyzer()
        assert ca.has_data() is False
        ca.analyze(self.DUMMY_PATH)
        assert ca.has_data() is True

    def test_get_summary_data_generated(self, mocker):
        fake_dt = mocker.MagicMock()
        mocker.patch('decomplexator.analyzer.datetime', fake_dt)
        fake_dt.utcnow = mocker.MagicMock(return_value=self.DT)
        fake = mocker.mock_open(read_data=self.FILE_CONTENT)
        mocker.patch('builtins.open', fake)
        mocker.patch.dict('os.environ', self._environ())
        ca = ComplexityAnalyzer()
        ca.analyze(self.DUMMY_PATH)
        ca.summary()
        ca.summary()
        fake_dt.utcnow.assert_called_once()

    def test_persist(self, mocker):
        mock_save = mocker.MagicMock()
        mocker.patch('decomplexator.analyzer.save_scores', mock_save)
        mock_load = mocker.MagicMock(return_value={})
        mocker.patch('decomplexator.analyzer.load_previous_scores', mock_load)
        mock_open = mocker.mock_open(read_data=self.FILE_CONTENT)
        mocker.patch('builtins.open', mock_open)
        mocker.patch.dict('os.environ', self._environ())
        ca = ComplexityAnalyzer()
        ca.analyze(self.DUMMY_PATH)
        ca.persist()
        mock_save.assert_called_once()

    def test_persist_no_data(self, mocker):
        mock_save = mocker.MagicMock()
        mocker.patch('decomplexator.analyzer.save_scores', mock_save)
        mocker.patch.dict('os.environ', self._environ())
        ca = ComplexityAnalyzer()
        ca.persist()
        assert mock_save.call_count == 0


class TestAnalyzerGroup(AnalyzerBaseTests):

    FILE_NAMES = [
        'test1.py',
        'test2.py',
        'test3.py',
    ]

    def test_add_files(self, mocker):
        mocker.patch.dict('os.environ', self._environ())
        grp = AnalyzerGroup()
        grp.add_files(self.FILE_NAMES)
        assert len(grp.files) == len(self.FILE_NAMES)