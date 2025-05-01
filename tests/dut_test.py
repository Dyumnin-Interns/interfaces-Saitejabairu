import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotb_coverage.coverage import coverage_db, CoverCross, CoverPoint
import random

# Register write interface
class RegisterWriteInterface:
    def __init__(self, dut):
        self.dut = dut

    async def write(self, address, data):
        self.dut.write_address.value = address
        self.dut.write_data.value = data
        self.dut.write_en.value = 1
        await RisingEdge(self.dut.CLK)
        self.dut.write_en.value = 0
        await RisingEdge(self.dut.CLK)
        while self.dut.write_rdy.value == 0:
            await RisingEdge(self.dut.CLK)


# Register read interface
class RegisterReadInterface:
    def __init__(self, dut):
        self.dut = dut

    async def read(self, address):
        self.dut.read_address.value = address
        self.dut.read_en.value = 1
        await RisingEdge(self.dut.CLK)
        self.dut.read_en.value = 0
        await RisingEdge(self.dut.CLK)
        while self.dut.read_rdy.value == 0:
            await RisingEdge(self.dut.CLK)
        return int(self.dut.read_data.value)


# Global coverage tracker
covered_values = set()

# Functional coverage declarations
@CoverPoint("top.input_a", xf=lambda a, b: a, bins=[0, 1], at_least=1)
@CoverPoint("top.input_b", xf=lambda a, b: b, bins=[0, 1], at_least=1)
@CoverCross("top.cross_inputs", items=["top.input_a", "top.input_b"], at_least=1)
def sample_coverage(a, b):
    covered_values.add((a, b))


@cocotb.test()
async def interface_or_test(dut):
    """CRV + Functional Coverage test of OR gate using register-based interface"""
    cocotb.start_soon(Clock(dut.CLK, 10, units="ns").start())

    # Reset
    dut.RST_N.value = 0
    dut.write_en.value = 0
    dut.read_en.value = 0
    await RisingEdge(dut.CLK)
    dut.RST_N.value = 1
    await RisingEdge(dut.CLK)

    write_if = RegisterWriteInterface(dut)
    read_if = RegisterReadInterface(dut)

    max_iterations = 100
    iterations = 0

    while len(covered_values) < 4 and iterations < max_iterations:
        a = random.randint(0, 1)
        b = random.randint(0, 1)

        # Stimulate input A at address 4 and B at address 5
        await write_if.write(4, a)
        await write_if.write(5, b)
        sample_coverage(a, b)

        iterations += 1
        await Timer(5, units="ns")

    # Read OR result from address 3
    result = await read_if.read(3)
    print(f"Read OR result: {result}")

    print(f"Covered combinations: {covered_values}")
    coverage_percent = coverage_db["top.cross_inputs"].coverage
    print(f"Cross coverage %: {coverage_percent}")

    if coverage_percent < 100:
        raise AssertionError("Functional coverage < 100%!")

    # Export coverage
    coverage_db.export_to_xml("coverage.xml")
