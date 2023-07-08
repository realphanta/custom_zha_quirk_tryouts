import logging
from typing import Any, List, Optional, Union

import zigpy.types as t
from zigpy.profiles import zha
from zigpy.zcl import foundation
from zigpy.zcl.foundation import ZCLHeader
from zigpy.zcl.clusters.general import Basic, Identify, MultistateValue 
from zigpy.zcl.clusters.smartenergy import Metering
from zigpy.quirks import CustomCluster, CustomDevice

from zhaquirks import Bus, LocalDataCluster
from zhaquirks.const import (
    DEVICE_TYPE,
    ENDPOINTS,
    INPUT_CLUSTERS,
    MODELS_INFO,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
)

_LOGGER = logging.getLogger(__name__)

class PtvoUartCluster(CustomCluster):
    """Analog input cluster, only used to relay power consumption information to ElectricalMeasurementCluster."""

    cluster_id = 0x0014

    def __init__(self, *args, **kwargs):
        """Init."""
        _LOGGER.info("XXX - PtvoUartCluster - init")

        self._current_state = {}
        super().__init__(*args, **kwargs)


class PtvoMeteringCluster(LocalDataCluster, Metering):
    """Metering cluster to receive reports that are sent to the MultistateValue cluster."""

    cluster_id = Metering.cluster_id
    
    CURRENT_SUMM_DELIVERED_ID = 0x0000
    _CONSTANT_ATTRIBUTES = {
        0x0300: 0,  # unit_of_measure: kWh
        0x0301: 1,  # multiplier
        0x0302: 1000,  # divisor
        0x0303: 0b0_0100_011,  # summation_formatting (read from plug)
        0x0306: 0,  # metering_device_type: electric
    }

    def __init__(self, *args, **kwargs):
        """Init."""
        _LOGGER.info("XXX - PtvoUartCluster - init")

        super().__init__(*args, **kwargs)
        self.endpoint.device.consumption_bus.add_listener(self)

        # put a default value so the sensor is created
        if self.CURRENT_SUMM_DELIVERED_ID not in self._attr_cache:
            self._update_attribute(self.CURRENT_SUMM_DELIVERED_ID, 0)

    def consumption_reported(self, value):
        """Consumption reported."""
        _LOGGER.info("XXX - PtvoMeteringCluster - consumption_reported")


        self._update_attribute(self.CURRENT_SUMM_DELIVERED_ID, round(value * 1000))

    def handle_cluster_request(
        self,
        hdr: foundation.ZCLHeader,
        args: List[Any],
        *,
        dst_addressing: Optional[t.AddrMode] = None,
    ):
        """Handle incoming data."""
        _LOGGER.info("XXX - PtvoMeteringCluster - handle_cluster_request: header: %s - args: [%s]",
            hdr,
            args,
        )

    def handle_cluster_general_request(
        self,
        hdr: ZCLHeader,
        args: List[Any],
        *,
        dst_addressing: Optional[Union[t.Addressing.Group, t.Addressing.IEEE, t.Addressing.NWK]
        ] = None,
    ):
        """Handle general cluster command."""
        _LOGGER.info("XXX - PtvoMeteringCluster - handle_cluster_general_request: header: %s - args: [%s]",
            hdr,
            args,
        )
    


class PtvoUartDevice(CustomDevice):

    def __init__(self, *args, **kwargs):
        """Init."""
        _LOGGER.info("XXX - PtvoUartDevice - init")
        super().__init__(*args, **kwargs)


    signature = {
        MODELS_INFO: [("ptvo.info", "ptvo.switch")],
        ENDPOINTS: {
            #  <SimpleDescriptor endpoint=1 profile=260 device_type=65534
            #  device_version=0
            #  input_clusters=[0, 20]
            #  output_clusters=[0]>
            1: {
                PROFILE_ID: 0x0104,
                DEVICE_TYPE: 0xfffe,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    PtvoUartCluster.cluster_id,
                ],
                OUTPUT_CLUSTERS: [
                    Basic.cluster_id,
                ]
            },
        },
    }
    replacement = {
        ENDPOINTS: {
            1: {
                DEVICE_TYPE: zha.DeviceType.SMART_PLUG,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Identify.cluster_id,
                    PtvoMeteringCluster,
                    PtvoUartCluster.cluster_id,
                ],
                OUTPUT_CLUSTERS: [],
            },
        },
    }
