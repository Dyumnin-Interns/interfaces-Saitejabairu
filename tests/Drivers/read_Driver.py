
from cocotb_bus.drivers import BusDriver

class read_Driver(BusDriver):

    _signals=["CLK", "RST_N", "write_address", "write_data", "write_en", "write_rdy", "read_address", "read_en", "readd_rdy", "read_data"]
    def __init__(self, name, entity):
        self.name = name
        self.entity= entity
        self.CLK = entity.CLK

    async def _driver_send(self, transaction, sync= True):
        await RisingEdge(self.CLK)
        if (self.entity.read_rdy.value.integer != 1):
            await RisingEdge(self.entity.read_rdy)
        self.entity.read_en.value = 1
        self.entity.read_address.value = transaction.get('addr')
        await RisingEdge(self.CLK)
        self.entity.read_en.value = 0
