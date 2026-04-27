--Código	Significado
--FILE_NOT_FOUND	El archivo no existe en el servidor
--INVALID_FILENAME	Nombre vacío, con /, \ o ..
--FILESIZE_MISMATCH	Tamaño recibido ≠ tamaño declarado
--WRITE_ERROR	Error al escribir en disco
--USER_CANCELLED	El cliente canceló la transferencia


local rftp_proto = Proto("RFTP", "Protocolo de Transferencia Confiable")
local header_seq = ProtoField.uint8("rftp.seq", "Sequence Number", base.DEC)
local header_ack = ProtoField.uint8("rftp.ack", "ACK Number", base.DEC)
local header_chk = ProtoField.uint16("rftp.chk", "Checksum", base.HEX)

--   Campos de la applayer
local header_type = ProtoField.uint8("rftp.type", "Message Type", base.HEX, {
    [0x01] = "REQUEST", [0x02] = "RESPONSE", [0x03] = "DATA", [0x04] = "ERROR"
})
local header_err = ProtoField.uint8("rftp.err", "Error Code", base.HEX, {
    [0x01] = "FILE_NOT_FOUND", [0x02] = "INVALID_FILENAME"
})

rftp_proto.fields = { header_seq, header_ack, header_chk, header_type, header_err }

function rftp_proto.dissector(buffer, pinfo, tree)
    pinfo.cols.protocol = "RFTP"
    local t = tree:add(rftp_proto, buffer(), "RFTP Protocol")
    
    -- capa de rdt (4 bytes)
    t:add(header_seq, buffer(0,1))
    t:add(header_ack, buffer(1,1))
    t:add(header_chk, buffer(2,2))    
    -- applayer
    if buffer:len() > 4 then 
        local app_tree = t:add(buffer(4), "App Layer")
        app_tree:add(header_type, buffer(4,1))
        
        local type = buffer(4,1):uint()
        if type == 0x04 then -- error
            app_tree:add(header_err, buffer(5,1))
        end
    end
end
local udp_table = DissectorTable.get("udp.port")
udp_table:add(5000, rftp_proto)
