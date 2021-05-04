# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import pytest
import time

import dcgm_fields
from dcgm_stackdriver import DcgmStackdriver


DCGM_FIELDS = [
    dcgm_fields.DCGM_FI_DEV_POWER_USAGE,
    dcgm_fields.DCGM_FI_DEV_GPU_UTIL,
    dcgm_fields.DCGM_FI_DEV_MEM_COPY_UTIL,
    dcgm_fields.DCGM_FI_DEV_FB_TOTAL,
    dcgm_fields.DCGM_FI_DEV_FB_FREE,
    dcgm_fields.DCGM_FI_DEV_FB_USED,
    # DCGM Profile Fields
    dcgm_fields.DCGM_FI_PROF_DRAM_ACTIVE,
    dcgm_fields.DCGM_FI_PROF_GR_ENGINE_ACTIVE,
    dcgm_fields.DCGM_FI_PROF_SM_ACTIVE,
    dcgm_fields.DCGM_FI_PROF_SM_OCCUPANCY,
    dcgm_fields.DCGM_FI_PROF_PIPE_TENSOR_ACTIVE,
    dcgm_fields.DCGM_FI_PROF_PIPE_FP32_ACTIVE,
    dcgm_fields.DCGM_FI_PROF_PCIE_TX_BYTES,
    dcgm_fields.DCGM_FI_PROF_PCIE_RX_BYTES,
    dcgm_fields.DCGM_FI_PROF_NVLINK_TX_BYTES,
    dcgm_fields.DCGM_FI_PROF_NVLINK_RX_BYTES,
]

@pytest.fixture
def reader():
    update_frequency = 5 

    return DcgmStackdriver(
        update_frequency=update_frequency,
        field_ids=DCGM_FIELDS
    )


def test_dcgmstackdriver_process(reader):

    wait_interval = 5
    count = 500 

    print('starting monitoring')
    for i in range(count):
        reader.Process()
        time.sleep(wait_interval)
    print('stopped monitoring')

    assert True
