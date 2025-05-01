import cocotb
from cocotb.triggers import RisingEdge

class WriteInterface:
    def __init__(self, dut):
        self.dut = dut

    async def write(self, addr, data):
        self.dut.write_address.value = addr
        self.dut.write_data.value = data
        self.dut.write_en.value = 1
        await RisingEdge(self.dut.CLK)
        self.dut.write_en.value = 0
        await RisingEdge(self.dut.CLK)
