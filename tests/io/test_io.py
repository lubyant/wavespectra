import os
import shutil
import pytest
from tempfile import mkdtemp
import xarray as xr

from wavespectra.core.attributes import attrs
from wavespectra import (
    read_swan,
    read_netcdf,
    read_ww3,
    read_ww3_msl,
    read_octopus,
    read_ncswan,
    read_triaxys,
    read_wwm,
    read_dataset,
)

FILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../sample_files")


class TestIO(object):
    """Test reading and writing of different file formats.
    
    Extend IO tests by adding tuple to parametrize, e.g.:
        ('filename', read_{filetype}, 'to_{filetype}')
    Use None for 'to_{filetype} if there is no output method defined'.

    """

    @classmethod
    def setup_class(self):
        """Setup class."""
        self.tmp_dir = mkdtemp()

    @classmethod
    def teardown_class(self):
        shutil.rmtree(self.tmp_dir)

    @pytest.mark.parametrize(
        "filename, read_func, write_method_name",
        [
            ("swanfile.spec", read_swan, "to_swan"),
            ("ww3file.nc", read_ww3, None),
            ("ww3mslfile.nc", read_ww3_msl, None),
            ("swanfile.nc", read_ncswan, None),
            ("triaxys.DIRSPEC", read_triaxys, None),
            ("triaxys.NONDIRSPEC", read_triaxys, None),
        ],
    )
    def test_io(self, filename, read_func, write_method_name):
        self.filename = filename
        self.read_func = read_func
        self.write_method_name = write_method_name
        # Execute io tests in order
        self._read()
        if self.write_method_name is not None:
            self._write()
            self._check()
        else:
            print(
                "No output method defined for {}, "
                "skipping output tests".format(filename)
            )

    @pytest.mark.parametrize(
        "read_func, filename",
        [
            (read_ww3, "ww3file.nc"),
            (read_wwm, "wwmfile.nc"),
            (read_ncswan, "swanfile.nc"),
        ],
    )
    def test_read_dataset(self, read_func, filename):
        readers = {read_ww3: "ww3file.nc", read_wwm: "wwmfile.nc", read_ncswan: "swanfile.nc"}
        for reader, filename in readers.items():
            filepath = os.path.join(FILES_DIR, filename)
            dset1 = reader(filepath)
            dset2 = read_dataset(xr.open_dataset(filepath))
            assert dset1.equals(dset2)

    def _read(self):
        self.infile = os.path.join(FILES_DIR, self.filename)
        self.ds = self.read_func(self.infile)

    def _write(self):
        self.write_method = getattr(self.ds.spec, self.write_method_name, None)
        self.outfile = os.path.join(self.tmp_dir, self.filename)
        self.write_method(self.outfile)

    def _check(self):
        self.ds2 = self.read_func(self.outfile)
        assert self.ds2.equals(self.ds[attrs.SPECNAME].to_dataset())
