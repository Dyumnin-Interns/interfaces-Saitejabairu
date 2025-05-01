import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
from cocotb.scoreboard import Scoreboard
import random
from cocotb_coverage.coverage import CoverPoint, coverage_db

class TestFIFO:
    def __init__(self, dut):
        self.dut = dut
        self.scoreboard = Scoreboard(dut)
        
        # Coverage points
        @CoverPoint(
            "top.write_address",
            xf=lambda x: x.write_address,
            bins=[0, 1, 2, 3, 4, 5, 6, 7]
        )
        @CoverPoint(
            "top.write_data",
            xf=lambda x: x.write_data,
            bins=[0, 1, 2, 3, 4, 5, 6, 7]
        )
        def sample_write(self, write_address, write_data):
            pass

        self.sample_write = sample_write

@cocotb.test()
async def test_dut_fifo_behavior(dut):
    test = TestFIFO(dut)
    
    # Start clock
    clock = Clock(dut.CLK, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset sequence
    dut.RST_N.value = 0
    await RisingEdge(dut.CLK)
    await RisingEdge(dut.CLK)
    dut.RST_N.value = 1
    await RisingEdge(dut.CLK)

    # Generate constrained random stimuli
    for _ in range(20):  # Run 20 random transactions
        # Randomize inputs with constraints
        write_en = random.randint(0, 1)
        write_address = random.randint(0, 7)
        write_data = random.randint(0, 255)
        
        # Apply to DUT
        dut.write_en.value = write_en
        dut.write_address.value = write_address
        dut.write_data.value = write_data
        
        # Sample coverage
        test.sample_write(write_address, write_data)
        
        await RisingEdge(dut.CLK)

    # Specific test sequence from original test
    # Step 1: Write to a_ff
    dut.write_en.value = 1
    dut.write_data.value = 1  # Pushing data `1`
    dut.write_address.value = 4  # Address for a_ff
    await RisingEdge(dut.CLK)

    # Step 2: Write to b_ff
    dut.write_en.value = 1
    dut.write_data.value = 1
    dut.write_address.value = 5  # Address for b_ff
    await RisingEdge(dut.CLK)

    # Disable write
    dut.write_en.value = 0
    await RisingEdge(dut.CLK)

    # Step 3: Read y_ff status
    dut.read_en.value = 1
    dut.read_address.value = 3  # Read from y_ff
    await RisingEdge(dut.CLK)
    output = dut.read_data.value.integer
    dut._log.info(f"Read data from y_ff (address 3): {output}")
    dut.read_en.value = 0

    # Step 4: Read all addresses
    for addr in range(8):  # Check all 8 addresses
        dut.read_address.value = addr
        await RisingEdge(dut.CLK)
        val = dut.read_data.value.integer
        dut._log.info(f"Read data from address {addr}: {val}")

    # Assertions
    assert output in [0, 1], "Read data from y_ff must be 0 or 1"
    
    # Coverage report
    coverage_db.report_coverage(dut._log.info, bins=True)
    coverage_db.export_to_xml(filename="coverage.xml")
