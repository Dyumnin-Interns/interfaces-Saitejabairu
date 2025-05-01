import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from interfaces.read_interface import ReadInterface
from interfaces.write_interface import WriteInterface
from constraints.input_generator import ConstrainedRandomInput
from coverage.coverage import sample_coverage, coverage_db

A_STATUS_ADDR = 0
B_STATUS_ADDR = 1
Y_STATUS_ADDR = 2
Y_OUTPUT_ADDR = 3
A_DATA_ADDR   = 4
B_DATA_ADDR   = 5


@cocotb.test()
async def or_gate_test(dut):
    cocotb.start_soon(Clock(dut.CLK, 10, units="ns").start())
    dut.RST_N.value = 0
    dut.read_en.value = 0
    dut.write_en.value = 0
    await RisingEdge(dut.CLK)
    dut.RST_N.value = 1

    writer = WriteInterface(dut)
    reader = ReadInterface(dut)
    cr_gen = ConstrainedRandomInput()

    input_queue = []  # store input pairs

    # Generate and write input
    for _ in range(20):
        in_data = cr_gen.get_sample()
        a_val = in_data['a']
        b_val = in_data['b']

        a_ready = await reader.read(A_STATUS_ADDR)
        b_ready = await reader.read(B_STATUS_ADDR)

        if a_ready and b_ready:
            await writer.write(A_DATA_ADDR, a_val)
            await writer.write(B_DATA_ADDR, b_val)
            input_queue.append((a_val, b_val))

        await Timer(10, units="ns")  # optional spacing

    # Read and check output
    for a_val, b_val in input_queue:
        for _ in range(100):
            y_valid = await reader.read(Y_STATUS_ADDR)
            if y_valid:
                y_val = await reader.read(Y_OUTPUT_ADDR)
                expected = a_val | b_val
                assert y_val == expected, f"FAIL: {a_val} | {b_val} = {expected}, got {y_val}"
                sample_coverage(a_val, b_val)
                break
            await Timer(10, units="ns")
        else:
            assert False, f"Timeout waiting for Y output for inputs a={a_val}, b={b_val}"

    coverage_db.export_to_xml(filename="coverage.xml")
