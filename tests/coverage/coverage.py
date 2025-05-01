from cocotb_coverage.coverage import coverage_db, CoverCross, CoverPoint

@CoverPoint("top.a", xf=lambda a, b: a, bins=[0, 1])
@CoverPoint("top.b", xf=lambda a, b: b, bins=[0, 1])
@CoverCross("top.cross", items=["top.a", "top.b"])
def sample_coverage(a, b):
    pass
