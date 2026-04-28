local rftp_proto = Proto("RFTP", "Protocolo de Transferencia Confiable")

-- Campos (igual que antes)
local f_opcode = ProtoField.uint8("rftp.opcode", "Opcode", base.HEX, {
    [1] = "UPLOAD_REQ", [2] = "DOWNLOAD_REQ", [3] = "DATA", [4] = "ACK", [5] = "ERROR"
})
local f_seq    = ProtoField.uint32("rftp.seq", "Sequence Number", base.DEC)
local f_wsize  = ProtoField.uint32("rftp.wsize", "Window Size", base.DEC)
local f_chk    = ProtoField.uint16("rftp.chk", "Checksum", base.HEX)
local f_plen   = ProtoField.uint16("rftp.plen", "Payload Length", base.DEC)

rftp_proto.fields = { f_opcode, f_seq, f_wsize, f_chk, f_plen }

function rftp_proto.dissector(buffer, pinfo, tree)
    -- 1. Validación heurística rápida:
    -- El paquete debe tener al menos el tamaño del header (16 bytes)
    if buffer:len() < 16 then return false end

    -- El opcode debe estar entre 1 y 5 (según tu lógica)
    local opcode = buffer(0,1):uint()
    if opcode < 1 or opcode > 5 then return false end

    -- El padding de 3 bytes (bytes 1, 2 y 3) deberían ser 0x00 en tu struct
    -- Esto ayuda a no confundirlo con otros protocolos UDP
    if buffer(1,3):uint() ~= 0 then return false end

    -- 2. Si pasó los filtros, es nuestro protocolo
    pinfo.cols.protocol = "RFTP"
    local t = tree:add(rftp_proto, buffer(), "RFTP Protocol Header")

    t:add(f_opcode, buffer(0,1))
    t:add(f_seq,    buffer(4,4))
    t:add(f_wsize,  buffer(8,4))
    t:add(f_chk,    buffer(12,2))
    t:add(f_plen,   buffer(14,2))

    local payload_len = buffer(14,2):uint()
    if buffer:len() > 16 then
        t:add(buffer(16, payload_len), "Payload Data")
    end

    return true -- IMPORTANTE: Avisamos que este paquete es nuestro
end

-- REGISTRO HEURÍSTICO
-- Esto hace que Wireshark lo intente con CUALQUIER paquete UDP
rftp_proto:register_heuristic("udp", rftp_proto.dissector)
