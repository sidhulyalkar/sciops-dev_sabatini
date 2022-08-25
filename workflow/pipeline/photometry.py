import datajoint as dj
import numpy as np
from .core import session
from workflow import db_prefix
from element_interface.utils import find_full_path
from workflow.utils.paths import get_raw_root_data_dir


logger = dj.logger
schema = dj.schema(db_prefix + "photometry")


@schema
class ExcitationWavelength(dj.Lookup):  # always constant?
    definition = """
    excitation_wavelength:      smallint 
    """

    contents = zip([405, 470])


@schema
class EmissionColor(dj.Lookup):
    definition = """
    emission_color:      varchar(10) 
    ---
    emission_wavelength: smallint
    """

    contents = [("green", 525)]


@schema
class FiberPhotometry(dj.Imported):
    definition = """
    -> session.Session
    fiber_id: int       # id of the implanted fibers
    ---
    sample_rate: float  # (in Hz) 
    notes='': varchar(1000)  
    """

    class Trace(dj.Part):
        definition = """ # preprocessed photometry traces
        -> master
        channel_id: int
        ---
        -> ExcitationWavelength
        -> EmissionColor
        timestamps: longblob  # (in seconds) photometry timestamps, already synced to the master clock
        trace: longblob
        """

    class TimeOffset(dj.Part):
        definition = """
        -> master
        ---
        time_offset: float  # (in second) time offset to synchronize the photometry traces to the master clock
        """

    def make(self, key):

        # Meta info hard-coded for now
        sample_rate = 50
        time_offset = 67.94
        excitation_wavelength = 405
        emission_color = "green"
        notes = ""

        session_dir = (session.SessionDirectory & key).fetch1("session_dir")
        photometry_dir = (
            find_full_path(get_raw_root_data_dir(), session_dir) / "photometry"
        )

        for fiber in photometry_dir.iterdir():

            fiber_id = fiber.stem

            # Populate FiberPhotometry
            self.insert1([*key.values(), fiber_id, sample_rate, notes])

            for channel in photometry_dir.rglob("*.csv"):

                channel_id = channel.stem[-1]
                trace = np.genfromtxt(channel, delimiter=",")
                timestamps = (
                    np.linspace(0, len(trace), len(trace)) / sample_rate
                ) + time_offset

                # Populate FiberPhotometry.Trace
                self.Trace.insert1(
                    [
                        *key.values(),
                        fiber_id,
                        channel_id,
                        excitation_wavelength,
                        emission_color,
                        timestamps,
                        trace,
                    ]
                )

        # Populate FiberPhotometry.TimeOffset
        self.TimeOffset.insert1([*key.values(), fiber_id, time_offset])
