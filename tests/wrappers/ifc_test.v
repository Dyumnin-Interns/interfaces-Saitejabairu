module ifc_test(
    input wire CLK,
    input wire RST_N,
    input wire [2:0] write_address,
    input wire write_data,
    input wire write_en,
    output reg write_rdy,
    input wire [2:0] read_address,
    input wire read_en,
    output reg read_data,
    output reg read_rdy,
    input wire a,
    input wire b
);

    assign y=a|b;

endmodule

// Testbench for ifc_test
module tb_ifc_test;

    // Testbench signals
    reg CLK;
    reg RST_N;
    reg [2:0] write_address;
    reg write_data;
    reg write_en;
    wire write_rdy;
    reg [2:0] read_address;
    reg read_en;
    wire read_data;
    wire read_rdy;

    // Instantiate the DUT
    ifc_test dut (
        .CLK(CLK),
        .RST_N(RST_N),
        .write_address(write_address),
        .write_data(write_data),
        .write_en(write_en),
        .write_rdy(write_rdy),
        .read_address(read_address),
        .read_en(read_en),
        .read_data(read_data),
        .read_rdy(read_rdy)
    );

    // Clock generation
    initial begin
        CLK = 0;
        forever #5 CLK = ~CLK;  // Toggle clock every 5 time units
    end

    // Initial block for stimulus
    initial begin
        RST_N = 0;                // Assert reset
        #10 RST_N = 1;           // Deassert reset

        // Drive inputs for testing
        write_address = 3'b000;
        write_data = 1'b1;
        write_en = 1'b1;
        // Add additional test cases as needed
        // Example wait for write ready signal
        #10; // Wait some time
        // Assert write ready signal based on your logic

        // Further stimulus and checks for read operations

        // Finish simulation
        #100; // Adjust time as needed
        $finish;
    end

    initial begin
        $dumpfile("ifc.vcd");
        $dumpvars(0, tb_ifc_test); // Dump all variables
    end

endmodule
