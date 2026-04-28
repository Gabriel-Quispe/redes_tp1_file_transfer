local rftp_proto = Proto("RFTP", "Protocolo de Transferencia Confiable")

local opcode_names = {
    [1] = "START_UPLOAD",
    [2] = "START_DOWNLOAD",
    [3] = "DATA",
    [4] = "ACK",
    [5] = "END",
    [6] = "ERROR"
}

local rdt_names = {
    [1] = "Stop n Wait",
    [2] = "Selective Repeat"
}

local f_opcode   = ProtoField.uint8("rftp.opcode", "OpCode", base.HEX, opcode_names)
local f_rdt_type = ProtoField.uint8("rftp.rdt_type", "RDT Protocol", base.DEC, rdt_names)
local f_seq      = ProtoField.uint32("rftp.seq", "Sequence Number", base.DEC)
local f_wsize    = ProtoField.uint32("rftp.wsize", "Window Size", base.DEC)
local f_chk      = ProtoField.uint16("rftp.chk", "Checksum", base.HEX)
local f_plen     = ProtoField.uint16("rftp.plen", "Payload Length", base.DEC)

rftp_proto.fields = { f_opcode, f_seq, f_wsize, f_chk, f_plen, f_rdt_type }


function rftp_proto.dissector(buffer, pinfo, tree)
    --(Header tiene 16 bytes)
    if buffer:len() < 16 then return false end

    local opcode = buffer(0,1):uint()
-- filtro de protocolo    
    if opcode < 1 or opcode > 6 then return false end
    if buffer(1,3):uint() ~= 0 then return false end
-- al pasar el filtro, doy nombre
    pinfo.cols.protocol = "RFTP"
    
    local op_name = opcode_names[opcode] or "UNKNOWN"

    pinfo.cols.info:set("(" .. op_name .. ") SeqNumber: " .. buffer(4,4):uint())

    local t = tree:add(rftp_proto, buffer(), "RFTP Header")

    t:add(f_opcode, buffer(0,1))
    t:add(f_seq,    buffer(4,4))
    t:add(f_wsize,  buffer(8,4))
    t:add(f_chk,    buffer(12,2))
    t:add(f_plen,   buffer(14,2))

    local plen = buffer(14,2):uint()
    
    -- Manejo del payload
    if plen > 0 and buffer:len() >= (16 + plen) then
        local payload_tree = t:add(buffer(16, plen), "Payload Data (" .. plen .. " bytes)")
        
        -- Si es un inicio de conexión, vemos el tipo de RDT del payload
        if opcode == 1 or opcode == 2 then
            payload_tree:add(f_rdt_type, buffer(16,1))
        end
    end

    return true
end

rftp_proto:register_heuristic("udp", rftp_proto.dissector)
