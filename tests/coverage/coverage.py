CoverPoint("top.a",
            xf = lambda x,y:x,
            bins=[0,1])
@CoverPoint("top.b",
            xf = lambda x,y:y,
            bins=[0,1])
@CoverCross("top.cross.ab",
            items=['top.a','top.b'])
def sample_fnc(x,y):
    pass 

@CoverPoint("top.w.wd_addr",
            xf = lambda wd_addr,wd_en, wd_data, rd_en, rd_addr: wd_addr,
            bins=[4,5])
@CoverPoint("top.w.wd_data",
            xf = lambda wd_addr,wd_en, wd_data, rd_en, rd_addr: wd_data,
            bins=[0,1])
@CoverPoint("top.w.wd_en",
            xf = lambda wd_addr,wd_en, wd_data, rd_en, rd_addr: wd_en,
            bins=[0,1])
@CoverPoint("top.r.rd_addr",
            xf = lambda wd_addr,wd_en, wd_data, rd_en, rd_addr: rd_addr,
            bins=[0,1,2,3])
@CoverPoint("top.r.rd_en",
            xf = lambda wd_addr,wd_en, wd_data, rd_en, rd_addr: rd_en,
            bins=[0,1])
@CoverCross("top.cross.w",
            items=['top.w.wd_addr', 'top.w.wd_data', 'top.w.wd_en'] 
            )
@CoverCross("top.cross.r",
            items=["top.r.rd_en", "top.r.rd_addr"])
def fl_cv(wd_addr, wd_en, wd_data, rd_en, rd_addr):
    pass
