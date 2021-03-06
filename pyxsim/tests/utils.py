import numpy as np
from yt.utilities.physical_ratios import \
    K_per_keV, mass_hydrogen_grams, cm_per_mpc
from yt.frontends.stream.api import \
    load_uniform_grid, load_particles
from numpy.random import RandomState

# Gas parameters
R = 1.0 # Mpc
r_c = 0.05 # Mpc
rho_c = 0.04*mass_hydrogen_grams # g/cm**3
beta = 2./3.
kT = 6.0 # keV
v_shift = 4.0e7 # cm/s
v_width = 4.0e7 # cm/s
Z = 0.3

# Dark matter parameters
r_s = 0.350 # Mpc
rho_s = 9.0e-26 # g/cm**3

class BetaModelSource(object):
    def __init__(self):

        self.prng = RandomState(32)
        self.kT = kT
        self.Z = Z

        nx = 128
        ddims = (nx,nx,nx)

        x, y, z = np.mgrid[-R:R:nx*1j,
                           -R:R:nx*1j,
                           -R:R:nx*1j]

        r = np.sqrt(x**2+y**2+z**2)

        dens = np.zeros(ddims)
        dens[r <= R] = rho_c*(1.+(r[r <= R]/r_c)**2)**(-1.5*beta)
        dens[r > R] = 0.0
        pden = np.zeros(ddims)
        x = r[r <= R]/r_s
        pden[r <= R] = rho_s/(x*(1.+x)**2)
        pden[r > R] = 0.0
        temp = self.kT*K_per_keV*np.ones(ddims)
        bbox = np.array([[-0.5,0.5],[-0.5,0.5],[-0.5,0.5]])
        velz = self.prng.normal(loc=v_shift,scale=v_width,size=ddims)
        dm_disp = 1000.*np.ones(ddims) # km/s

        data = {}
        data["density"] = (dens, "g/cm**3")
        data["dark_matter_density"] = (pden, "g/cm**3")
        data["dark_matter_dispersion"] = (dm_disp, "km/s")
        data["temperature"] = (temp, "K")
        data["velocity_x"] = (np.zeros(ddims), "cm/s")
        data["velocity_y"] = (np.zeros(ddims), "cm/s")
        data["velocity_z"] = (velz, "cm/s")

        self.ds = load_uniform_grid(data, ddims, length_unit=(2*R, "Mpc"),
                                    nprocs=64, bbox=bbox)

class ParticleBetaModelSource(object):
    def __init__(self):

        self.prng = RandomState(24)
        self.kT = kT
        self.Z = Z

        num_particles = 1000000

        rr = np.linspace(0.0, R, 10000)
        # This formula assumes beta = 2/3
        M_r = 4*np.pi*rho_c*r_c*r_c*(rr-r_c*np.arctan(rr/r_c))
        M_r *= cm_per_mpc**3

        pmass = M_r[-1]*np.ones(num_particles)/num_particles
        M_r /= M_r[-1]
        u = self.prng.uniform(size=num_particles)

        radius = np.interp(u, M_r, rr, left=0.0, right=1.0)
        dens = rho_c*(1.+(radius/r_c)**2)**(-1.5*beta)
        radius /= (2.*R)
        theta = np.arccos(self.prng.uniform(low=-1.,high=1.,size=num_particles))
        phi = 2.*np.pi*self.prng.uniform(size=num_particles)

        temp = self.kT*K_per_keV*np.ones(num_particles)
        velz = self.prng.normal(loc=v_shift,scale=v_width,size=num_particles)

        bbox = np.array([[-0.5,0.5],[-0.5,0.5],[-0.5,0.5]])

        data = {}
        data["io", "density"] = (dens, "g/cm**3")
        data["io", "temperature"] = (temp, "K")
        data["io", "particle_position_x"] = (radius*np.sin(theta)*np.cos(phi), "code_length")
        data["io", "particle_position_y"] = (radius*np.sin(theta)*np.sin(phi), "code_length")
        data["io", "particle_position_z"] = (radius*np.cos(theta), "code_length")
        data["io", "particle_velocity_x"] = (np.zeros(num_particles), "cm/s")
        data["io", "particle_velocity_y"] = (np.zeros(num_particles), "cm/s")
        data["io", "particle_velocity_z"] = (velz, "cm/s")
        data["io", "particle_mass"] = (pmass, "g")
        data["io", "smoothing_length"] = (0.02/(2.*R)*np.ones(num_particles), "code_length")

        self.ds = load_particles(data, length_unit=(2*R, "Mpc"), bbox=bbox)

def create_dummy_wcs():
    from yt.utilities.on_demand_imports import _astropy
    wcs = _astropy.pywcs.WCS(naxis=2)
    wcs.wcs.crpix = [512.5, 512.5]
    wcs.wcs.crval = [30.0, 45.0]
    wcs.wcs.cdelt = [-0.001, 0.001]
    wcs.wcs.ctype = ["RA---TAN","DEC--TAN"]
    wcs.wcs.cunit = ["deg"]*2
    return wcs
