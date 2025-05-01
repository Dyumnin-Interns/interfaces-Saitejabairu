import cocotb
from cocotb.triggers import Timer, RisingEdge, ReadOnly, NextTimeStep, FallingEdge
from cocotb_bus.drivers import BusDriver
from cocotb_coverage.coverage import CoverCross, CoverPoint, coverage_db
from cocotb_bus.monitors import BusMonitor
import os
import random
from cocotb.clock import Clock

class TB:
    def __init__(self, dut):
        self.dut = dut
        self.log = dut._log
        
        # Create drivers and monitors
        self.write_drv = InputDriver(dut, 'write', dut.CLK)
        self.read_drv = OutputDriver(dut, 'read', dut.CLK, self.sb_callback)
        self.input_mon = InputMonitor(dut, 'write', dut.CLK, self.a_cover)
        
        # Scoreboard storage
        self.expected_values = {}
        
    async def reset(self, duration=10):
        self.log.info("Asserting reset")
        self.dut.RST_N.value = 0
        await Timer(duration, units='ns')
        await RisingEdge(self.dut.CLK)
        self.dut.RST_N.value = 1
        self.log.info("Reset released")
        await Timer(duration, units='ns')  # Wait after reset
        
    def sb_callback(self, actual_value):
        """Scoreboard callback for read operations"""
        self.log.info(f"Read value: {actual_value}")
        # Add your scoreboard checks here
        
    def a_cover(self, state):
        """Coverage callback"""
        self.log.info(f"State transition: {state}")
        # Your coverage collection

async def run_test_case(dut, case):
    tb = TB(dut)
    
    # Start clock
    cocotb.start_soon(Clock(dut.CLK, 10, units='ns').start())
    
    # Reset sequence
    await tb.reset(20)  # Longer reset duration
    
    # Basic operational test
    if case == 0:
        dut._log.info("Running basic operational test")
        for i in range(10):
            addr = random.randint(0, 5)
            data = random.randint(0, 1)
            await tb.write_drv.write(addr, data)
            await tb.read_drv.read(addr)
            await FallingEdge(dut.CLK)
    
    # Test case 1: Input without enable
    elif case == 1:
        dut._log.info("Running case 1: Input without enable")
        # Test logic here
    
    # Add other test cases...
    
    # Final checks
    await Timer(100, 'ns')
    dut._log.info("Test completed")

@cocotb.test()
async def ifc_test(dut):
    """Main testbench entry point"""
    case = int(os.getenv('TEST_CASE', '0'))
    dut._log.info(f"Starting test case {case}")
    
    try:
        await run_test_case(dut, case)
    except Exception as e:
        dut._log.error(f"Test failed: {str(e)}")
        raise
        
    # Coverage reporting
    coverage_db.report_coverage(dut._log.info, bins=True)
    coverage_file = os.path.join(os.getenv('RESULT_PATH', "./"), 'coverage.xml')
    coverage_db.export_to_xml(filename=coverage_file)

class InputDriver(BusDriver):
    _signals = ['address', 'data', 'en', 'rdy']

    def __init__(self, dut, prefix, clk):
        super().__init__(dut, prefix, clk)
        self.bus.en.value = 0
        self.clk = clk

    async def write(self, address, data):
        """Convenience method for write operations"""
        await self._driver_send([address, data])

    async def _driver_send(self, value, sync=True):
        await RisingEdge(self.clk)
        self.bus.en.value = 1
        self.bus.address.value = value[0]
        self.bus.data.value = value[1]
        
        await ReadOnly()
        if self.bus.rdy.value != 1:
            await RisingEdge(self.bus.rdy)
            
        await RisingEdge(self.clk)
        self.bus.en.value = 0

class OutputDriver(BusDriver):
    _signals = ['address', 'data', 'en', 'rdy']

    def __init__(self, dut, prefix, clk, callback):
        super().__init__(dut, prefix, clk)
        self.bus.en.value = 0
        self.clk = clk
        self.callback = callback

    async def read(self, address):
        """Convenience method for read operations"""
        return await self._driver_send(address)

    async def _driver_send(self, value, sync=True):
        await RisingEdge(self.clk)
        self.bus.en.value = 1
        self.bus.address.value = value
        
        await ReadOnly()
        if self.bus.rdy.value != 1:
            await RisingEdge(self.bus.rdy)
            
        data = self.bus.data.value
        self.callback(data)
        
        await RisingEdge(self.clk)
        self.bus.en.value = 0
        return data

class InputMonitor(BusMonitor):
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
