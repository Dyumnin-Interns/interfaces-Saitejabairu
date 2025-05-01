import cocotb
from cocotb.triggers import Timer, RisingEdge, ReadOnly, NextTimeStep, FallingEdge
from cocotb_bus.drivers import BusDriver
from cocotb_coverage.coverage import CoverCross, CoverPoint, coverage_db
from cocotb_bus.monitors import BusMonitor
import os
import random
from cocotb.clock import Clock
from cocotb.result import TestFailure

class TB:
    def __init__(self, dut):
        self.dut = dut
        self.log = dut._log
        self.memory_model = {}  # Scoreboard storage
        
        # Create drivers and monitors
        self.write_drv = WriteDriver(dut, 'write', dut.CLK)
        self.read_drv = ReadDriver(dut, 'read', dut.CLK, self.scoreboard_check)
        self.write_mon = WriteMonitor(dut, 'write', dut.CLK, self.write_callback)
        
    async def reset(self, duration=20):
        self.log.info("Asserting reset")
        self.dut.RST_N.value = 0
        await Timer(duration, units='ns')
        await RisingEdge(self.dut.CLK)
        self.dut.RST_N.value = 1
        self.log.info("Reset released")
        await Timer(duration, units='ns')

    def write_callback(self, transaction):
        """Track all writes in memory model"""
        addr = transaction['address']
        data = transaction['data']
        self.memory_model[addr] = data
        self.log.info(f"Write captured: addr={addr}, data={data}")

    def scoreboard_check(self, addr, data):
        """Verify read values against expected"""
        expected = self.memory_model.get(addr, 0)
        if data != expected:
            raise TestFailure(f"Read mismatch! Addr={addr}: Expected {expected}, Got {data}")
        self.log.info(f"Read verified: addr={addr}, data={data} (correct)")

@cocotb.test()
async def basic_test(dut):
    """Main testbench entry point"""
    tb = TB(dut)
    
    # Start clock
    clock = Clock(dut.CLK, 10, units='ns')
    cocotb.start_soon(clock.start())
    
    # Reset sequence
    await tb.reset()
    
    # Test case 1: Basic write/read
    tb.log.info("Test 1: Basic write/read")
    await tb.write_drv.write(0, 1)
    await tb.read_drv.read(0)
    
    # Test case 2: Multiple operations
    tb.log.info("Test 2: Multiple operations")
    test_data = [(1,0), (2,1), (3,0), (4,1)]
    for addr, data in test_data:
        await tb.write_drv.write(addr, data)
        await tb.read_drv.read(addr)
    
    # Test case 3: Random operations
    tb.log.info("Test 3: Random operations")
    for _ in range(20):
        addr = random.randint(0, 5)
        data = random.randint(0, 1)
        await tb.write_drv.write(addr, data)
        await tb.read_drv.read(addr)
        await Timer(random.randint(1, 5), units='ns')
    
    # Final checks
    await Timer(100, 'ns')
    report_coverage()

def report_coverage():
    """Handle coverage reporting safely"""
    if coverage_db.coverages:
        coverage_db.report_coverage(cocotb.log.info, bins=True)
        coverage_file = os.path.join(os.getenv('RESULT_PATH', "./"), 'coverage.xml')
        coverage_db.export_to_xml(filename=coverage_file)
    else:
        cocotb.log.warning("No coverage data collected")

class WriteDriver(BusDriver):
    _signals = ['address', 'data', 'en', 'rdy']

    def __init__(self, dut, prefix, clk):
        super().__init__(dut, prefix, clk)
        self.bus.en.value = 0
        self.clk = clk

    async def write(self, address, data):
        """Write transaction"""
        await RisingEdge(self.clk)
        self.bus.en.value = 1
        self.bus.address.value = address & 0x7  # Ensure 3-bit address
        self.bus.data.value = data & 0x1       # Ensure 1-bit data
        
        if self.bus.rdy.value != 1:
            await RisingEdge(self.bus.rdy)
        
        await ReadOnly()
        await RisingEdge(self.clk)
        self.bus.en.value = 0

class ReadDriver(BusDriver):
    _signals = ['address', 'data', 'en', 'rdy']

    def __init__(self, dut, prefix, clk, callback):
        super().__init__(dut, prefix, clk)
        self.bus.en.value = 0
        self.clk = clk
        self.callback = callback

    async def read(self, address):
        """Read transaction with verification"""
        await RisingEdge(self.clk)
        self.bus.en.value = 1
        self.bus.address.value = address & 0x7  # Ensure 3-bit address
        
        if self.bus.rdy.value != 1:
            await RisingEdge(self.bus.rdy)
        
        await ReadOnly()
        data = self.bus.data.value
        self.callback(address, data)  # Verify with scoreboard
        
        await RisingEdge(self.clk)
        self.bus.en.value = 0
        return data

class WriteMonitor(BusMonitor):
    _signals = ['address', 'data', 'en', 'rdy']

    def __init__(self, dut, prefix, clk, callback):
        super().__init__(dut, prefix, clk)
        self.callback = callback

    async def _monitor_recv(self):
        while True:
            await RisingEdge(self.clock)
            await ReadOnly()
            
            if self.bus.en.value and self.bus.rdy.value:
                transaction = {
                    'address': self.bus.address.value,
                    'data': self.bus.data.value,
                    'time': cocotb.utils.get_sim_time(units='ns')
                }
                self._recv(transaction)
                self.callback(transaction)

# Coverage Definitions
@CoverPoint("top.write", 
            xf=lambda x: x['address'],
            bins=list(range(8)),  # All 8 possible addresses
            )
@CoverPoint("top.data",
            xf=lambda x: x['data'],
            bins=[0, 1],
            )
def write_callback(transaction):
    pass
