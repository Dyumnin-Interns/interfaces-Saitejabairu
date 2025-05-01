import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
from cocotb.regression import TestFactory
from cocotb_coverage.coverage import coverage_db, CoverPoint
import random

# Track coverage
covered = []

@CoverPoint("top.a", xf=lambda a, b: a, bins=[0, 1], at_least=1)
@CoverPoint("top.b", xf=lambda a, b: b, bins=[0, 1], at_least=1)
@CoverPoint("top.y", xf=lambda a, b: a | b, bins=[0, 1], at_least=1)
def sample_coverage(a, b):
    covered.append((a, b))

# Write helper
async def write(dut, addr, data):
    dut.write_address.value = addr
    dut.write_data.value = data
    dut.write_en.value = 1
    await RisingEdge(dut.CLK)
    dut.write_en.value = 0
    await RisingEdge(dut.CLK)

# Read helper
async def read(dut, addr):
    dut.read_address.value = addr
    dut.read_en.value = 1
    await RisingEdge(dut.CLK)
    await RisingEdge(dut.CLK)  # Allow for 1-cycle latency
    val = dut.read_data.value.integer
    dut.read_en.value = 0
    return val

@cocotb.test()
async def interface_or_test(dut):
    """Test OR gate using register-based interface with CRV and coverage"""
    
    # Clock generation
    cocotb.start_soon(Clock(dut.CLK, 10, units="ns").start())
    dut.RST_N.value = 0
    dut.write_en.value = 0
    dut.read_en.value = 0

    await Timer(20, units="ns")
    dut.RST_N.value = 1
    await RisingEdge(dut.CLK)

    tries = 0
    while len(covered) < 4 and tries < 20:
        a = random.randint(0, 1)
        b = random.randint(0, 1)

        # Write A and B values
        await write(dut, 4, a)  # A_Data
        await write(dut, 5, b)  # B_Data

        # Wait for computation to complete
        await Timer(20, units="ns")

        # Check Y_Status
        y_ready = await read(dut, 2)
        if y_ready == 1:
            y_val = await read(dut, 3)
            expected = a | b
            assert y_val == expected, f"Output mismatch: a={a}, b={b}, got={y_val}, expected={expected}"
            sample_coverage(a, b)

        tries += 1

    coverage_db.export_to_yaml("coverage_results.yml")
