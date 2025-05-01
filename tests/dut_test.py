import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
from cocotb.regression import TestFactory
from cocotb.binary import BinaryValue
import random

# Constants for register addresses
A_FF_WRITE_ADDR = 4
B_FF_WRITE_ADDR = 5
Y_FF_READ_ADDR = 3
A_FF_FULL_ADDR = 0
B_FF_FULL_ADDR = 1
Y_FF_EMPTY_ADDR = 2

@cocotb.test()
async def or_gate_test(dut):
    """Test the OR gate DUT using register interface"""
    clock = Clock(dut.CLK, 10, units="ns")  # 100MHz clock
    cocotb.start_soon(clock.start())

    # Reset sequence
    dut.RST_N.value = 0
    await RisingEdge(dut.CLK)
    await RisingEdge(dut.CLK)
    dut.RST_N.value = 1
    await RisingEdge(dut.CLK)

    # Helper functions
    async def write_reg(addr, data):
        dut.write_address.value = addr
        dut.write_data.value = data
        dut.write_en.value = 1
        await RisingEdge(dut.CLK)
        dut.write_en.value = 0
        await RisingEdge(dut.CLK)

    async def read_reg(addr):
        dut.read_address.value = addr
        dut.read_en.value = 1
        await RisingEdge(dut.CLK)
        data = dut.read_data.value.integer
        dut.read_en.value = 0
        await RisingEdge(dut.CLK)
        return data

    # Functional coverage tracking
    coverage = {
        (0, 0): 0,
        (0, 1): 0,
        (1, 0): 0,
        (1, 1): 0
    }

    # Test all combinations of inputs
    for _ in range(10):  # 10 test iterations (you can increase this)
        a_val = random.randint(0, 1)
        b_val = random.randint(0, 1)

        # Write to a_ff
        await write_reg(A_FF_WRITE_ADDR, a_val)
        # Write to b_ff
        await write_reg(B_FF_WRITE_ADDR, b_val)

        # Wait for data to propagate through DUT
        await Timer(20, units='ns')

        # Read OR result from y_ff
        y_val = await read_reg(Y_FF_READ_ADDR)

        expected = a_val | b_val
        assert y_val == expected, f"FAIL: {a_val} | {b_val} = {expected}, got {y_val}"

        coverage[(a_val, b_val)] += 1
        dut._log.info(f"PASS: {a_val} | {b_val} = {y_val}")

    # Report coverage
    total_cases = len(coverage)
    hit_cases = sum(1 for hit in coverage.values() if hit > 0)
    assert hit_cases == total_cases, f"Functional coverage incomplete: {coverage}"
    dut._log.info(f"Functional coverage: {coverage}")
