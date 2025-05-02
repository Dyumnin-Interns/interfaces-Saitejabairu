from cocotb_bus.drivers import BusDriver
from cocotb.triggers import Timer, ClockCycles, RisingEdge, Event , ReadOnly
class write_Driver(BusDriver):
    _signals=["CLK", "RST_N", "write_address", "write_data", "write_en", "write_rdy", "read_address", "read_en", "read_rdy", "read_data"]
    def __init__(self, name, entity):
        self.name = name
        self.entity= entity
        self.CLK = entity.CLK

    async def _driver_send(self, transaction, sync = True):
        await RisingEdge(self.CLK)
        if (self.entity.write_rdy.value.integer != 1):
            await RisingEdge(self.entity.write_rdy)
        self.entity.write_en.value = 1
        self.entity.write_address.value = transaction.get('addr')
        self.entity.write_data.value = transaction.get('val')
        await RisingEdge(self.CLK)
        self.entity.write_en.value = 0
