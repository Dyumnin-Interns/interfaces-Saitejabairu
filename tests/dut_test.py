import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotb_coverage.coverage import coverage_db, CoverPoint, CoverCross
import random

# Interfaces
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

# Coverage Set
covered_values = set()

# Functional Coverage Points
@CoverPoint("top.input_a", xf=lambda a, b: a, bins=[0, 1], at_least=1)
@CoverPoint("top.input_b", xf=lambda a, b: b, bins=[0, 1], at_least=1)
@CoverCross("top.cross_inputs", items=["top.input_a", "top.input_b"], at_least=1)
def sample_coverage(a, b):
    covered_values.add((a, b))


@cocotb.test()
async def interface_or_test(dut):
    """CRV + Functional Coverage test of OR gate using register-based interface"""

    # Start Clock
    cocotb.start_soon(Clock(dut.CLK, 10, units="ns").start())

    # Reset
    dut.RST_N.value = 0
    dut.write_en.value = 0
    dut.read_en.value = 0
    await RisingEdge(dut.CLK)
    dut.RST_N.value = 1
    await RisingEdge(dut.CLK)

    # Instantiate interfaces
    write_if = RegisterWriteInterface(dut)
    read_if = RegisterReadInterface(dut)

    # Try random combinations until full coverage
    iterations = 0
    max_iterations = 50  # prevent infinite loops

    while coverage_db["top.cross_inputs"].coverage < 100 and iterations < max_iterations:
        a = random.randint(0, 1)
        b = random.randint(0, 1)

        # Assuming input A = address 4, B = address 5, output = address 3
        await write_if.write(4, a)
        await write_if.write(5, b)

        await RisingEdge(dut.CLK)  # Allow OR logic to update
        await RisingEdge(dut.CLK) 
        # Sample coverage after inputs are stable
        sample_coverage(a, b)

        # Optionally validate output
        result = await read_if.read(3)
        expected = a | b
        assert result == expected, f"OR output incorrect: {a} | {b} = {expected}, got {result}"

        print(f"Sampled a={a}, b={b} -> OR={result}, Coverage={coverage_db['top.cross_inputs'].coverage}%")

        iterations += 1
        await Timer(5, units="ns")

    # Final Coverage Check
    if coverage_db["top.cross_inputs"].coverage < 100:
        raise AssertionError("Functional coverage < 100%!")

    print("✅ All input combinations covered.")
    print(f"✅ Cross coverage %: {coverage_db['top.cross_inputs'].coverage}")

    # Export coverage to file
    coverage_db.export_to_xml(filename="coverage.xml")
