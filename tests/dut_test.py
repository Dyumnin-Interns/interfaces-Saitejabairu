import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_coverage.coverage import coverage_db, CoverCross, CoverPoint
import random

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

# Functional coverage points
covered_values = set()

@CoverPoint("top.write_addr", xf=lambda a, b: a, bins=list(range(2)), at_least=1)
@CoverPoint("top.write_data", xf=lambda a, b: b, bins=[0, 1], at_least=1)
@CoverCross("top.cross_write", items=["top.write_addr", "top.write_data"])
def sample_coverage(write_addr, write_data):
    covered_values.add((write_addr, write_data))


@cocotb.test()
async def interface_or_test(dut):
    """CRV + Functional Coverage test of OR gate using register-based interface"""
    cocotb.start_soon(Clock(dut.CLK, 10, units="ns").start())

    dut.RST_N.value = 0
    dut.write_en.value = 0
    dut.read_en.value = 0
    await RisingEdge(dut.CLK)
    dut.RST_N.value = 1
    await RisingEdge(dut.CLK)

    write_if = RegisterWriteInterface(dut)
    read_if = RegisterReadInterface(dut)

    # Constrained random test (keep testing until full coverage)
    max_tests = 50
    for _ in range(max_tests):
        write_addr = random.randint(0, 1)  # Assume 0 = A, 1 = B
        write_data = random.randint(0, 1)  # 1-bit input

        sample_coverage(write_addr, write_data)
        await write_if.write(write_addr, write_data)

        # Optional: Read output when both A and B are written
        if (0, 0) in covered_values and (0, 1) in covered_values and \
           (1, 0) in covered_values and (1, 1) in covered_values:
            result = await read_if.read(0)  # Assume read from OR result
            print(f"Read OR result: {result}")

        if coverage_db["top.cross_write"].coverage == 100:
            break

    assert coverage_db["top.cross_write"].coverage == 100, "Functional coverage not met!"

    coverage_db.export_to_xml(filename="coverage.xml")
