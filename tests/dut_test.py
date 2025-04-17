import cocotb
from cocotb.regression import Test
from cocotb.triggers import RisingEdge, Timer
from cocotb_bus.drivers import BusDriver  
from cocotb_bus.monitors import BusMonitor 
from cocotb_coverage.coverage import CoverCross, CoverPoint, coverage_db 

class WriteBus(BusDriver):
    _signals = ["address", "data", "rdy", "en"]

    def __init__(self, dut, name, clock):
        BusDriver.__init__(self, dut, name, clock)

        self.bus.en.value = 0
        self.bus.address.value = 0
        self.bus.data.value = 0

    async def write(self, address, data):
        self.bus.address.value = address
        self.bus.data.value = data

        if self.bus.rdy.value != 1:
            await RisingEdge(self.bus.rdy)

        self.bus.en.value = 1
        await RisingEdge(self.clock)
        self.bus.en.value = 0

class ReadBus(BusDriver):
    _signals = ["address", "data", "rdy", "en"]

    def __init__(self, dut, name, clock):
        BusDriver.__init__(self, dut, name, clock)

        self.bus.en.value = 0

    async def read(self, address):
        self.bus.address.value = address
        self.bus.en.value = 1
        await RisingEdge(self.clock)

        if self.bus.rdy.value != 1:
            await RisingEdge(self.bus.rdy)

        data = self.bus.data.value
        self.bus.en.value = 0
        return data

@Test()
async def dut_test(dut):
    a_values = (0, 0, 1, 1)
    b_values = (0, 1, 0, 1)
    expected_outputs = (0, 1, 1, 1)

    for i in range(4):
        dut.a.value = a_values[i]
        dut.b.value = b_values[i]

        await Timer(1, 'ns')
        assert dut.y.value == expected_outputs[i], f'Error at iteration {i}: Expected {expected_outputs[i]}, got {dut.y.value}'
