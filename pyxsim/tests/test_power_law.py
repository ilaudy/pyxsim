from pyxsim import \
    PowerLawSourceModel, PhotonList, \
    WabsModel, ACIS_I
from pyxsim.tests.utils import \
    BetaModelSource
from yt.units.yt_array import YTQuantity
import numpy as np
from yt.testing import requires_module
import os
import shutil
import tempfile
from yt.utilities.physical_constants import mp
from sherpa.astro.ui import load_user_model, add_user_pars, \
    load_pha, ignore, fit, set_model, set_stat, set_method, \
    covar, get_covar_results, set_covar_opt
from numpy.random import RandomState

prng = RandomState(27)

def setup():
    from yt.config import ytcfg
    ytcfg["yt", "__withintesting"] = "True"

def mymodel(pars, x, xhi=None):
    dx = x[1]-x[0]
    wm = WabsModel(pars[0])
    wabs = wm.get_absorb(x)
    plaw = pars[1]*dx*(x*(1.0+pars[2]))**(-pars[3])
    return wabs*plaw

@requires_module("sherpa")
def test_power_law():
    plaw_fit(1.1)
    plaw_fit(0.8)
    plaw_fit(1.0)

def plaw_fit(alpha_sim):

    tmpdir = tempfile.mkdtemp()
    curdir = os.getcwd()
    os.chdir(tmpdir)

    bms = BetaModelSource()
    ds = bms.ds

    def _hard_emission(field, data):
        return YTQuantity(1.0e-18, "s**-1*keV**-1")*data["density"]*data["cell_volume"]/mp
    ds.add_field(("gas", "hard_emission"), function=_hard_emission, units="keV**-1*s**-1")

    nH_sim = 0.02
    abs_model = WabsModel(nH_sim)

    A = YTQuantity(2000., "cm**2")
    exp_time = YTQuantity(2.0e5, "s")
    redshift = 0.01

    sphere = ds.sphere("c", (100.,"kpc"))

    plaw_model = PowerLawSourceModel(1.0, 0.01, 11.0, "hard_emission", 
                                     alpha_sim, prng=prng)

    photons = PhotonList.from_data_source(sphere, redshift, A, exp_time,
                                          plaw_model)

    D_A = photons.parameters["FiducialAngularDiameterDistance"]
    dist_fac = 1.0/(4.*np.pi*D_A*D_A*(1.+redshift)**3).in_cgs()
    norm_sim = float((sphere["hard_emission"]).sum()*dist_fac.in_cgs())*(1.+redshift)

    events = photons.project_photons("z", absorb_model=abs_model,
                                     prng=bms.prng,
                                     no_shifting=True)
    events = ACIS_I(events, rebin=False, convolve_psf=False, prng=bms.prng)
    events.write_spectrum("plaw_model_evt.pi", clobber=True)

    os.system("cp %s ." % events.parameters["ARF"])
    os.system("cp %s ." % events.parameters["RMF"])

    load_user_model(mymodel, "wplaw")
    add_user_pars("wplaw", ["nH", "norm", "redshift", "alpha"],
                  [0.01, norm_sim*1.1, redshift, 0.9], 
                  parmins=[0.0, 0.0, 0.0, 0.1],
                  parmaxs=[10.0, 1.0e9, 10.0, 10.0],
                  parfrozen=[False, False, True, False])

    load_pha("plaw_model_evt.pi")
    set_stat("cstat")
    set_method("simplex")
    ignore(":0.6, 7.0:")
    set_model("wplaw")
    fit()
    set_covar_opt("sigma", 1.645)
    covar()
    res = get_covar_results()

    assert np.abs(res.parvals[0]-nH_sim) < res.parmaxes[0]
    assert np.abs(res.parvals[1]-norm_sim) < res.parmaxes[1]
    assert np.abs(res.parvals[2]-alpha_sim) < res.parmaxes[2]

    os.chdir(curdir)
    shutil.rmtree(tmpdir)

if __name__ == "__main__":
    test_power_law()
