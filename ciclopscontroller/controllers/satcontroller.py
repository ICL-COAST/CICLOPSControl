from ciclopscontroller.controllers.timecontroller import TimeController
from PySide6.QtCore import QObject

import skyfield.api as sf
from skyfield.framelib import itrs
import numpy as np
import astropy.units as u
import astropy.coordinates as coord
from astropy.time import Time as astropy_time


class SatController(QObject):
    def __init__(self, time_controller: TimeController):
        super().__init__()
        self.time_controller = time_controller
        self.satellite = None
        self.cached_positions = None
        self.cached_dts = None

        eph = sf.load('de421.bsp')
        self.earth_eph = eph['earth']
        self.sun_eph = eph['sun']
        
        self.load_tle_data()

    def load_tle_data(self):
        satellites = sf.load.tle_file('tle.txt')
        self.satellite = satellites[0] if satellites else None
        if self.satellite is None:
            raise ValueError("No satellite loaded. Please load TLE data first.")
        epoch = self.time_controller.get_epoch()
        self.cached_dts = np.linspace(-720, 1320, 2000)
        ts = sf.load.timescale()
        times = ts.from_datetime(epoch) + self.cached_dts / 86400  # Convert seconds to days
        self.cached_positions = self.satellite.at(times).frame_xyz(itrs).km.T  # Convert to km and reshape

    def get_sat_position(self):
        return self.get_sat_positions([self.time_controller.get_time_since_epoch()])

    def get_sat_positions(self, times):
        times = np.atleast_1d(times)
        if self.satellite is None:
            raise ValueError("No satellite loaded. Please load TLE data first.")
        if self.cached_positions is None or self.cached_dts is None:
            raise ValueError("Satellite positions not cached, check load_tle_data() method.")
        
        if np.any(times < self.cached_dts[0]) or np.any(times > self.cached_dts[-1]):
            raise ValueError("Requested times are out of bounds.")
        # Get the two closest times in the cache
        upper_idx = np.searchsorted(self.cached_dts, times, side='left')
        exact_match = (upper_idx < len(self.cached_dts)) & (self.cached_dts[upper_idx] == times)
        upper_idx = np.clip(upper_idx, 1, len(self.cached_dts) - 1)
        lower_idx = upper_idx - 1

        ts_upper = self.cached_dts[upper_idx]
        ts_lower = self.cached_dts[lower_idx]

        # Avoid division by zero for exact matches    
        with np.errstate(divide='ignore', invalid='ignore'):
            weights_upper = (times - ts_lower) / (ts_upper - ts_lower)
            weights_upper[exact_match] = 0
        weights_lower = 1 - weights_upper
        weights_lower[exact_match] = 1

        return (
            weights_lower[:, None] * self.cached_positions[lower_idx] +
            weights_upper[:, None] * self.cached_positions[upper_idx]
        )

    def get_trail_positions(self, start_time, end_time, n_points):
        if self.satellite is None:
            raise ValueError("No satellite loaded. Please load TLE data first.")
        if self.cached_positions is None or self.cached_dts is None:
            raise ValueError("Satellite positions not cached, check load_tle_data() method.")
        
        # Generate positions for the trail
        times = np.linspace(start_time, end_time, n_points) + self.time_controller.get_time_since_epoch()
        return self.get_sat_positions(times)

    def get_observer_position(self):
        latitude = 51.4953
        longitude = 0.1790
        london = sf.wgs84.latlon(latitude, longitude)
        t = sf.load.timescale().now()
        return london.at(t).frame_xyz(itrs).km
    
    def get_sun_direction(self):
        t = sf.load.timescale().from_datetime(self.time_controller.get_datetime())
        obstime = astropy_time(self.time_controller.get_datetime())

        sun_icrs = (self.sun_eph - self.earth_eph).at(t).position.km
        sun_icrs = coord.SkyCoord(
            x=sun_icrs[0] * u.km,
            y=sun_icrs[1] * u.km,
            z=sun_icrs[2] * u.km,
            frame='icrs',
            representation_type='cartesian',
            obstime=obstime
        )
        sun_itr = sun_icrs.transform_to('itrs').cartesian.xyz.value
        sun_direction = sun_itr / np.linalg.norm(sun_itr)
        return sun_direction
