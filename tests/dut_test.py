import cocotb
from cocotb.triggers import Timer
from cocotb.regression import TestFactory
from cocotbext.cocotb_bus.monitors import BusMonitor
from cocotbext.cocotb_bus.drivers import BusDriver
import random

# Coverage model
covered_inputs = set()
full_coverage = {(a, b) for a in range(2) for b in range(2)}

class RegisterWriteInterface(BusDriver):
    _signals = ["addr", "data", "wr_en"]

    def __init__(self, entity, name, clock, **kwargs):
        super().__init__(entity, name, clock, **kwargs)
        self.bus.wr_en.setimmediatevalue(0)

    async def write(self, addr, data):
        self.bus.addr.value = addr
        self.bus.data.value = data
        self.bus.wr_en.value = 1
        await Timer(10, units='ns')
        self.bus.wr_en.value = 0
        await Timer(10, units='ns')

class RegisterReadInterface(BusMonitor):
    _signals = ["addr", "data", "rd_en"]

    def __init__(self, entity, name, clock, **kwargs):
        super().__init__(entity, name, clock, **kwargs)
        self.entity = entity
        self.clock = clock
        self.bus.rd_en.setimmediatevalue(0)

    async def read(self, addr):
        self.bus.addr.value = addr
        self.bus.rd_en.value = 1
        await Timer(10, units='ns')
        data = self.bus.data.value.integer
        self.bus.rd_en.value = 0
        await Timer(10, units='ns')
        return data

@cocotb.test()
async def interface_or_test(dut):
    """
    CRV + Functional Coverage test of OR gate using register-based interface
    """
    write_if = RegisterWriteInterface(dut, "write_if", None)
    read_if = RegisterReadInterface(dut, "read_if", None)

    attempts = 0
    max_attempts = 20

    while covered_inputs != full_coverage and attempts < max_attempts:
        a = random.randint(0, 1)
        b = random.randint(0, 1)

        if (a, b) in covered_inputs:
            continue

        # Apply constrained-random stimulus
        await write_if.write(4, a)
        await write_if.write(5, b)

        # Wait for y_ready with extended timeout
        for _ in range(50):
            y_ready = await read_if.read(2)
            if y_ready == 1:
                break
            await Timer(10, units='ns')
        else:
            assert False, "Timeout waiting for output"

        # Read and check result
        y = await read_if.read(3)
        expected = a | b
        assert y == expected, f"Expected {expected}, got {y}"

        # Update coverage
        covered_inputs.add((a, b))
        attempts += 1

    assert covered_inputs == full_coverage, f"Functional coverage incomplete: {covered_inputs}"
