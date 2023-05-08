#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# checkmk_apc_rackpdu_sensor - Checkmk extension for APC RackPDU Sensors
#
# Copyright (C) 2021  Marius Rieder <marius.rieder@scs.ch>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# modified by Tim Heitkamp for use with AP9320

from .agent_based_api.v1 import (
    get_value_store,
    all_of,
    exists,
    register,
    Service,
    SNMPTree,
    startswith,
    State,
)
from .utils.temperature import (
    check_temperature,
)

APC_AP9320_SENSOR_LEVEL_STATES = {
    0: State.OK,    # Just a guess
    1: State.CRIT,  # not present
    2: State.CRIT,  # low critical,
    3: State.WARN,  # low warning,
    4: State.OK,    # normal,
    5: State.WARN,  # high warning,
    6: State.CRIT,  # high critical,
}


def parse_apc_ap9320_sensor_temp(string_table):
    parsed = {}
    for row in string_table:
        for name, temperature, highthresh, maxthresh, commstatus, alarmstatus in row:
            parsed[name] = [
                int(temperature),  # temperature
                int(highthresh),   # High temp threshold
                int(maxthresh),    # Max temp threshold
                int(alarmstatus),  # alarmstatus
                int(commstatus)    # commstatus
            ]
    return parsed

register.snmp_section(
    name='apc_ap9320_sensor_temp',
    detect=all_of(
        startswith('.1.3.6.1.2.1.1.1.0', 'APC Environmental Management System '),
        exists('.1.3.6.1.4.1.318.1.1.10.*')
    ),
    parse_function=parse_apc_ap9320_sensor_temp,
    fetch=[
        SNMPTree(
            base= '.1.3.6.1.4.1.318.1.1.10.3.13.1.1',
            oids=[
                '2',   # PowerNet-MIB::emsProbeStatusProbeName
                '3',   # PowerNet-MIB::emsProbeStatusProbeTemperature
                '4',   # PowerNet-MIB::emsProbeStatusProbeHighTempThresh
                '12',  # PowerNet-MIB::emsProbeStatusProbeMaxTempThresh
                '10',  # PowerNet-MIB::emsProbeStatusProbeCommStatus
                '11',  # PowerNet-MIB::emsProbeStatusProbeAlarmStatus
            ]),
    ],
)

def discovery_apc_ap9320_sensor_temp(section):
    for sensor in section.keys():
        if section[sensor][4] != 2:
            continue
        yield Service(item=sensor)


def check_apc_ap9320_sensor_temp(item, params, section):
    if item not in section:
        return

    temperature, highthresh, maxthresh, alarmstatus, commstatus = section[item]
    print(highthresh)

    yield from check_temperature(
        reading=temperature,
        params=params,
        unique_name='check_apc_ap9320_sensor_temp.%s' % item,
        value_store=get_value_store(),
        dev_levels=(highthresh, maxthresh),
        dev_status=APC_AP9320_SENSOR_LEVEL_STATES[alarmstatus],
        dev_status_name=item,
    )


register.check_plugin(
    name='apc_ap9320_sensor_temp',
    service_name='%s Temperature',
    discovery_function=discovery_apc_ap9320_sensor_temp,
    check_function=check_apc_ap9320_sensor_temp,
    check_default_parameters={},
    check_ruleset_name='temperature',
)
