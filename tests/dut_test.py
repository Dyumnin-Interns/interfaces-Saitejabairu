import asyncio
import os
import sys
from pathlib import Path
import cocotb
from cocotb import runner
from cocotb.runner import get_runner
from cocotb.triggers import Timer, ClockCycles, RisingEdge, Event, ReadOnly
from cocotb.clock import Clock
from cocotb.log import logging, SimLog
from cocotb_coverage.coverage import coverage_db
import random as rnd
import constraint

# Local module imports
from coverage import sample_fnc, fl_cv
from write_Driver import write_Driver
from read_Driver import read_Driver

class TB:
    def __init__(self, name, entity, log):
        self.log = log
        self.name = name
        self.entity = entity
        self.CLK = self.entity.CLK
        self.a_ls = []
        self.b_ls = []
        self.y_ls = []
        self.stats = []
        self.writer_event = Event()
        self.reader_event = Event()
        self.ref_address = {'A_status': 0, 'B_status': 1, 'Y_status': 2, 'Y_output': 3, 'A_data': 4, 'B_data': 5}
        self.writer = write_Driver("Write fifo", entity)
        self.reader = read_Driver("Read fifo", entity)

    async def reset_dut(self):
        await RisingEdge(self.CLK)
        self.entity.write_address.value = 0
        self.entity.write_data.value = 0
        self.entity.write_en.value = 0
        self.entity.read_en.value = 0
        self.entity.read_data.value = 0
        self.entity.read_address.value = 0
        self.entity.RST_N.value = 1
        await ClockCycles(self.CLK, 4)
        self.entity.RST_N.value = 0
        await ClockCycles(self.CLK, 4)
        self.entity.RST_N.value = 1
        await RisingEdge(self.CLK)
        print("\t\t reset done")

    def stat_dec(self, addr, val):
        if addr == 3:
            self.stats.append({'name': 'yr', 'val': val})
        elif addr == 4:
            self.stats.append({'name': 'aw', 'val': val})
        elif addr == 5:
            self.stats.append({'name': 'bw', 'val': val})
        elif addr == 0:
            self.stats.append({'name': 'as', 'val': ('full' if val == 0 else 'empty')})
        elif addr == 1:
            self.stats.append({'name': 'bs', 'val': ('full' if val == 0 else 'empty')})
        elif addr == 2:
            self.stats.append({'name': 'ys', 'val': ('full' if val == 1 else 'empty')})

    def cvr(self):
        self.p = constraint.Problem()
        self.p.addVariable('write_en', [0, 1])
        self.p.addVariable('read_en', [0, 1])
        self.p.addVariable('write_address', [4, 5])
        self.p.addVariable('read_address', [0, 1, 2, 3])
        self.p.addVariable('write_data', [0, 1])
        self.p.addVariable('write_rdy', [1])
        self.p.addVariable('read_rdy', [1])
        self.p.addConstraint(lambda rd_en, wd_en, rd_rdy: rd_en == 1 if wd_en == 0 and rd_rdy == 1 else rd_en == 0,
                             ['read_en', 'write_en', 'read_rdy'])
        self.p.addConstraint(lambda rd_en, wd_en, wd_rdy: wd_en == 1 if rd_en == 0 and wd_rdy == 1 else wd_en == 0,
                             ['read_en', 'write_en', 'write_rdy'])

    def solve(self):
        self.cvr()
        self.sols = self.p.getSolutions()

    def get_sols(self):
        return rnd.choice(self.sols) if self.sols else None


@cocotb.test()
async def dut_test(dut):
    cocotb.start_soon(Clock(dut.CLK, 2, "ns").start())
    log = SimLog("interface_test")
    logging.getLogger().setLevel(logging.INFO)

    tbh = TB(name="tb inst", entity=dut, log=log)
    await tbh.reset_dut()

    await tbh.writer._driver_send(transaction={'addr': 4, 'val': 0})
    await tbh.writer._driver_send(transaction={'addr': 5, 'val': 0})
    sample_fnc(0, 0)
    await tbh.reader._driver_send({'addr': 3, 'val': 0})
    log.debug(f"[functional] a:0 b:0 y:{dut.read_data.value.integer}")

    await tbh.writer._driver_send(transaction={'addr': 4, 'val': 0})
    await tbh.writer._driver_send(transaction={'addr': 5, 'val': 1})
    sample_fnc(0, 1)
    await tbh.reader._driver_send({'addr': 3, 'val': 0})
    log.debug(f"[functional] a:0 b:1 y:{dut.read_data.value.integer}")

    await tbh.writer._driver_send(transaction={'addr': 4, 'val': 1})
    await tbh.writer._driver_send(transaction={'addr': 5, 'val': 0})
    sample_fnc(1, 0)
    await tbh.reader._driver_send({'addr': 3, 'val': 0})
    log.debug(f"[functional] a:1 b:0 y:{dut.read_data.value.integer}")

    await tbh.writer._driver_send(transaction={'addr': 4, 'val': 1})
    await tbh.writer._driver_send(transaction={'addr': 5, 'val': 1})
    sample_fnc(1, 1)
    await tbh.reader._driver_send({'addr': 3, 'val': 0})
    log.debug(f"[functional] a:1 b:1 y:{dut.read_data.value.integer}")

    tbh.solve()
    for i in range(32):
        x = tbh.get_sols()
        fl_cv(x.get("write_address"), x.get("write_en"), x.get("write_data"), x.get("read_en"), x.get("read_address"))
        if x.get('read_en') == 1:
            await tbh.reader._driver_send(transaction={'addr': x.get('read_address'), 'val': 0})
            log.debug(f"[{i}][read  operation] address: {x.get('read_address')} got data: {dut.read_data.value.integer}")
            tbh.stat_dec(x.get('read_address'), dut.read_data.value.integer)
        elif x.get('write_en') == 1:
            await tbh.writer._driver_send(transaction={'addr': x.get('write_address'), 'val': x.get('write_data')})
            log.debug(f"[{i}][write operation] address: {x.get('write_address')} put data: {x.get('write_data')}")
            tbh.stat_dec(x.get('write_address'), x.get('write_data'))
        await RisingEdge(dut.CLK)

    for i in tbh.stats:
        log.debug(f"{i}")

    coverage_db.report_coverage(log.info, bins=True)
    log.info(f"Functional Coverage: {coverage_db['top.cross.ab'].cover_percentage:.2f} %")
    log.info(f"Write Coverage: {coverage_db['top.cross.w'].cover_percentage:.2f} %")
    log.info(f"Read Coverage: {coverage_db['top.cross.r'].cover_percentage:.2f} %")


def start_build():
    sim = os.getenv("SIM", "verilator")
    dut_dir = Path(__file__).resolve().parent.parent
    dut_dir = f"{dut_dir}/hdl"
    hdl_toplevel = "dut"
    verilog_sources = [f"{dut_dir}/{hdl_toplevel}.v", f"{dut_dir}/FIFO1.v", f"{dut_dir}/FIFO2.v"]
    build_args = ["--trace", "--trace-fst"]

    runner = get_runner(sim)
    runner.build(
        hdl_toplevel=hdl_toplevel,
        verilog_sources=verilog_sources,
        build_args=build_args,
        waves=True,
        always=True
    )

    runner.test(
        test_module="dut_test",
        hdl_toplevel=hdl_toplevel,
        waves=True
    )

if __name__ == "__main__":
    start_build()
