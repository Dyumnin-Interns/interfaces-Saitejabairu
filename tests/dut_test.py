import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
from cocotb.result import TestFailure

# CSR addresses (these must match DUT)
A_WRITE_ADDR = 0x00
B_WRITE_ADDR = 0x04
Y_READ_ADDR  = 0x08
A_EMPTY_ADDR = 0x0C
B_EMPTY_ADDR = 0x10
Y_EMPTY_ADDR = 0x14

@cocotb.test()
async def or_gate_test(dut):
    """ Test the OR gate DUT using register interface """

    # Start clock
    cocotb.start_soon(Clock(dut.CLK, 10, units="ns").start())

    # Reset
    dut.RST_N.value = 0
    await Timer(100, units="ns")
    dut.RST_N.value = 1
    await RisingEdge(dut.CLK)

    # Helper: Write to DUT register
    async def write_reg(addr, data):
        dut.wr_valid.value = 1
        dut.wr_addr.value = addr
        dut.wr_data.value = data
        await RisingEdge(dut.CLK)
        dut.wr_valid.value = 0
        await RisingEdge(dut.CLK)

    # Helper: Read from DUT register
    async def read_reg(addr):
        dut.rd_valid.value = 1
        dut.rd_addr.value = addr
        await RisingEdge(dut.CLK)
        data = dut.rd_data.value.integer
        dut.rd_valid.value = 0
        await RisingEdge(dut.CLK)
        return data

    # Helper: Wait until y_ff is not empty
    async def wait_until_output_ready(timeout_cycles=20):
        for _ in range(timeout_cycles):
            empty = await read_reg(Y_EMPTY_ADDR)
            if empty == 0:
                return
            await RisingEdge(dut.CLK)
        raise TestFailure("Timeout waiting for y_ff to be non-empty")

    # Run multiple test cases
    test_vectors = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for a_val, b_val in test_vectors:
        # Write inputs
        await write_reg(A_WRITE_ADDR, a_val)
        await write_reg(B_WRITE_ADDR, b_val)

        # Wait until output is ready
        await wait_until_output_ready()

        # Read and check output
        y_val = await read_reg(Y_READ_ADDR)
        expected = a_val | b_val
        dut._log.info(f"{a_val} | {b_val} = {expected}, got {y_val}")
        assert y_val == expected, f"FAIL: {a_val} | {b_val} = {expected}, got {y_val}"

    dut._log.info("All test cases passed.")
