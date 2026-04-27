local rdt_proto = Proto("rdt_tp1", "TP1 Redes Protocol")
print("CARGANDO PLUGIN RDT")
-- Mapeo del header
local h_opcode  = ProtoField.uint8("rdt.opcode", "Opcode", base.DEC, {
    [1] = "START_UPLOAD",
    [2] = "START_DOWNLOAD",
    [3] = "DATA",
    [4] = "ACK",
    [5] = "END",
    [6] = "ERROR"
})
local h_padding = ProtoField.bytes("rdt.padding", "Padding", base.SPACE)
local h_seq     = ProtoField.uint32("rdt.seq", "Sequence Number", base.DEC)
local h_win     = ProtoField.uint32("rdt.window", "Window Size", base.DEC)
local h_chk     = ProtoField.uint16("rdt.checksum", "Checksum", base.HEX)
local h_len     = ProtoField.uint16("rdt.len", "Payload Length", base.DEC)

rdt_proto.fields = {h_opcode, h_padding, h_seq, h_win, h_chk, h_len}

function rdt_proto.dissector(buffer, pinfo, tree)
    if buffer:len() < 16 then return end

    pinfo.cols.protocol = "RFTP"
    
    -- Crear el tree en la interface de Wireshark
    local t = tree:add(rdt_proto, buffer(), "RDT Protocol Header")
    
    -- Mapeo por offset
    t:add(h_opcode,  buffer(0,1))
    t:add(h_padding, buffer(1,3))  -- 3 bytes padding
    t:add(h_seq,     buffer(4,4))  -- 4 bytes seqnum
    t:add(h_win,     buffer(8,4))  -- 4 bytes wsize
    t:add(h_chk,     buffer(12,2)) -- 2 bytes chksum
    t:add(h_len,     buffer(14,2)) -- 2 bytes plen
    
    -- lo que haya después de los 16 bytes es el payload
    if buffer:len() > 16 then
        t:add(buffer(16), "Payload Data (" .. buffer:len() - 16 .. " bytes)")
    end
end

-- Puerto para el Protocolo
local udp_port = DissectorTable.get("udp.port")
udp_port:add(65535, rdt_proto)