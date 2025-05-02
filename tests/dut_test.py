import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from interfaces.csr_read_interface import ReadInterface
from interfaces.csr_write_interface import WriteInterface
from constraints.input_generator import ConstrainedRandomInput
from coverage.coverage import sample_coverage, coverage_db
from collections import deque

A_STATUS_ADDR = 0
B_STATUS_ADDR = 1
Y_STATUS_ADDR = 2
Y_OUTPUT_ADDR = 3
A_DATA_ADDR   = 4
B_DATA_ADDR   = 5

@cocotb.test()
async def dut_test(dut):

    read_if = ReadInterface(dut)
    write_if = WriteInterface(dut)  
    # Create clock
    cocotb.start_soon(Clock(dut.CLK, 10, units="ns").start())

    # Reset sequence
    dut.RST_N.value = 0
    await Timer(20, units="ns")
    dut.RST_N.value = 1
    await Timer(20, units="ns")

    # Wait a bit to let sim run
    await Timer(100, units="ns")
    # Test
    a, b = 1, 0
    await write_if.write(A_DATA, a)
    await write_if.write(B_DATA, b)

    for _ in range(10):
        await RisingEdge(dut.CLK)

    y_status = await read_if.read(Y_STATUS)
    y_output = await read_if.read(Y_OUTPUT)

    assert y_status == 1, "Y FIFO should not be empty"
    assert y_output == (a | b), f"Expected {a | b}, got {y_output}"
