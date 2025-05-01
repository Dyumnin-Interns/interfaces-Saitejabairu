import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
from cocotb_coverage.coverage import coverage_db, CoverCross, CoverPoint
import random

# Functional coverage points
covered_values = set()

def sample_cover(a, b):
    covered_values.add((a, b))

@CoverPoint("top.a", xf=lambda a, b: a, bins=[0, 1], at_least=1)
@CoverPoint("top.b", xf=lambda a, b: b, bins=[0, 1], at_least=1)
@CoverCross("top.cross_ab", items=["top.a", "top.b"], at_least=1)
def ab_coverage(a, b):
    sample_cover(a, b)

# Interfaces
class WriteInterface:
    def __init__(self, dut):
        self.dut = dut

    async def write(self, address, data):
        self.dut.write_address.value = address
        self.dut.write_data.value = data
        self.dut.write_en.value = 1
        await RisingEdge(self.dut.CLK)
        self.dut.write_en.value = 0
        await RisingEdge(self.dut.CLK)

class ReadInterface:
    def __init__(self, dut):
        self.dut = dut

    async def read(self, address):
        self.dut.read_address.value = address
        self.dut.read_en.value = 1
        await RisingEdge(self.dut.CLK)
        self.dut.read_en.value = 0
        await RisingEdge(self.dut.CLK)
        return int(self.dut.read_data.value)

@cocotb.test()
async def interface_or_test(dut):
    """CRV + Functional Coverage test of OR gate using register-based interface"""

    cocotb.start_soon(Clock(dut.CLK, 10, units="ns").start())

    write_if = WriteInterface(dut)
    read_if = ReadInterface(dut)

    # Reset
    dut.RST_N.value = 0
    dut.write_en.value = 0
    dut.read_en.value = 0
    await Timer(20, units="ns")
    dut.RST_N.value = 1
    await Timer(20, units="ns")

    # Run constrained random tests until full coverage
    max_tests = 20  # safety limit
    test_count = 0

    while len(covered_values) < 4 and test_count < max_tests:
        test_count += 1

        a = random.randint(0, 1)
        b = random.randint(0, 1)

        ab_coverage(a, b)

        # Write inputs
        await write_if.write(4, a)
        await write_if.write(5, b)

        # Wait for output to be ready
        for _ in range(10):
            y_ready = await read_if.read(2)
            if y_ready == 1:
                break
            await Timer(10, units='ns')
        else:
            assert False, "Timeout waiting for output"

        # Read and check result
        y_val = await read_if.read(3)
        expected = a | b
        assert y_val == expected, f"Output mismatch: a={a}, b={b}, got={y_val}, expected={expected}"

    # Print coverage report
    coverage_db.report_coverage(cocotb.log.info)
    assert len(covered_values) == 4, f"Functional coverage incomplete: {covered_values}"
