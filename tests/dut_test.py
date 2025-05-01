import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from interfaces.read_interface import ReadInterface
from interfaces.write_interface import WriteInterface
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
    cocotb.start_soon(Clock(dut.CLK, 10, units="ns").start())
    dut.RST_N.value = 0
    dut.read_en.value = 0
    dut.write_en.value = 0
    await RisingEdge(dut.CLK)
    dut.RST_N.value = 1

    writer = WriteInterface(dut)
    reader = ReadInterface(dut)
    cr_gen = ConstrainedRandomInput()

    input_queue = deque()

    # Feed inputs
    for _ in range(20):
        a_ready = await reader.read(A_STATUS_ADDR)
        b_ready = await reader.read(B_STATUS_ADDR)
        if a_ready and b_ready:
            sample = cr_gen.get_sample()
            a_val = sample['a']
            b_val = sample['b']
            await writer.write(A_DATA_ADDR, a_val)
            await writer.write(B_DATA_ADDR, b_val)
            input_queue.append((a_val, b_val))
        await Timer(10, units="ns")

    # Wait for and verify all outputs
    timeout_cycles = 0
    max_timeout = 1000
    while input_queue:
        y_ready = await reader.read(Y_STATUS_ADDR)
        if y_ready:
            a_val, b_val = input_queue.popleft()
            y_val = await reader.read(Y_OUTPUT_ADDR)
            expected = a_val | b_val
            assert y_val == expected, f"FAIL: {a_val} | {b_val} = {expected}, got {y_val}"
            sample_coverage(a_val, b_val)
        else:
            timeout_cycles += 1
            if timeout_cycles > max_timeout:
                assert False, f"Timeout waiting for Y output for inputs still in queue: {list(input_queue)}"
            await Timer(10, units="ns")

    coverage_db.export_to_xml(filename="coverage.xml")

