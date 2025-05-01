import cocotb
from cocotb.triggers import RisingEdge
from cocotb.clock import Clock
import random
from cocotb_coverage.coverage import CoverPoint, coverage_db

class TestFIFO:
    def __init__(self, dut):
        self.dut = dut
        
        # Coverage points
        @CoverPoint(
            "top.write_address",
            xf=lambda x: x.write_address,
            bins=list(range(8))  # 8 address bins (0-7)
        )
        @CoverPoint(
            "top.write_data",
            xf=lambda x: x.write_data,
            bins=list(range(256))  # 256 possible 8-bit values
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
        write_en = random.randint(0, 1)
        write_address = random.randint(0, 7)
        write_data = random.randint(0, 255)
        
        dut.write_en.value = write_en
        dut.write_address.value = write_address
        dut.write_data.value = write_data
        
        test.sample_write(write_address, write_data)
        await RisingEdge(dut.CLK)

    # Specific test sequence
    dut.write_en.value = 1
    dut.write_data.value = 1
    dut.write_address.value = 4
    await RisingEdge(dut.CLK)

    dut.write_en.value = 1
    dut.write_data.value = 1
    dut.write_address.value = 5
    await RisingEdge(dut.CLK)

    dut.write_en.value = 0
    await RisingEdge(dut.CLK)

    # Read operations
    dut.read_en.value = 1
    dut.read_address.value = 3
    await RisingEdge(dut.CLK)
    output = dut.read_data.value.integer
    dut._log.info(f"Read data from y_ff (address 3): {output}")
    dut.read_en.value = 0

    for addr in range(8):
        dut.read_address.value = addr
        await RisingEdge(dut.CLK)
        val = dut.read_data.value.integer
        dut._log.info(f"Read data from address {addr}: {val}")

    assert output in [0, 1], "Read data from y_ff must be 0 or 1"
    
    # Coverage report
    coverage_db.report_coverage(dut._log.info, bins=True)
    coverage_db.export_to_xml(filename="coverage.xml")
