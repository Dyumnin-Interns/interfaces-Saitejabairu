import cocotb
from cocotb.triggers import RisingEdge

class ReadInterface:
    def __init__(self, dut):
        self.dut = dut

    async def read(self, addr):
        self.dut.read_address.value = addr
        self.dut.read_en.value = 1
        await RisingEdge(self.dut.CLK)
        self.dut.read_en.value = 0
        await RisingEdge(self.dut.CLK)
        return self.dut.read_data.value.integer
