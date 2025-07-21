from ciclopscontroller.controllers.timecontroller import TimeController
from PySide6.QtCore import QObject

import skyfield.api as sf
from skyfield.framelib import itrs
import numpy as np
import astropy.units as u
import astropy.coordinates as coord
from astropy.time import Time as astropy_time
from enum import Enum

class PositionFrame(Enum):
    ITRS = 'itrs'
    TOPO = 'topo'
    ALTAZ = 'altaz'

class SatController(QObject):
    def __init__(self, time_controller: TimeController):
        super().__init__()
        self.time_controller = time_controller
        self.satellite = None
        self.cached_positions = None
        self.cached_topo_positions = None
        self.cached_topo_angles = None
        self.cached_dts = None

        eph = sf.load('de421.bsp')
        self.earth_eph = eph['earth']
        self.sun_eph = eph['sun']

        latitude = 51.4953
        longitude = 0.1790
        self.observer = sf.wgs84.latlon(latitude, longitude)
        
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
        self.cached_positions = np.array(self.satellite.at(times).frame_xyz(itrs).km).T  # Convert to km

        difference = self.satellite - self.observer
        topocentric = difference.at(times)
        alt, az, distance = topocentric.altaz()
        self.cached_topo_angles = np.array([alt.radians, az.radians]).T

        alt = np.array(alt.radians)
        az = np.array(az.radians)
        distance = np.array(distance.km)

        self.cached_topo_positions = np.array([
            distance * np.cos(alt) * np.sin(az),
            distance * np.cos(alt) * np.cos(az),
            distance * np.sin(alt)
        ]).T

    def get_sat_position(self, frame: PositionFrame):
        return self.get_sat_positions([self.time_controller.get_time_since_epoch()], frame)

    def get_sat_positions(self, times, frame: PositionFrame):
        if self.cached_dts is None:
            raise ValueError("No satellite time data cached. Call load_tle_data() first.")
        if frame == PositionFrame.ITRS:
            if self.cached_positions is None:
                raise ValueError("Satellite ITRS positions not cached, check load_tle_data() method.")
            cache = self.cached_positions
        elif frame == PositionFrame.TOPO:
            if self.cached_topo_positions is None:
                raise ValueError("Satellite TOPO positions not cached, check load_tle_data() method.")
            cache = self.cached_topo_positions
        elif frame == PositionFrame.ALTAZ:
            if self.cached_topo_angles is None:
                raise ValueError("Satellite ALTAZ angles not cached, check load_tle_data() method.")
            cache = self.cached_topo_angles

        times = np.atleast_1d(times)
        if self.cached_positions is None or self.cached_topo_positions is None or self.cached_dts is None:
            raise ValueError("Satellite positions not cached, check load_tle_data() method.")
        
        if np.any(times < self.cached_dts[0]) or np.any(times > self.cached_dts[-1]):
            times = np.clip(times, self.cached_dts[0], self.cached_dts[-1])
            
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
            weights_lower[:, None] * cache[lower_idx] +
            weights_upper[:, None] * cache[upper_idx]
        )

    def get_trail_positions(self, start_time, end_time, n_points, frame: PositionFrame):        
        # Generate positions for the trail
        times = np.linspace(start_time, end_time, n_points) + self.time_controller.get_time_since_epoch()
        return self.get_sat_positions(times, frame)

    def get_observer_position(self):
        t = sf.load.timescale().now()
        return self.observer.at(t).frame_xyz(itrs).km

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
