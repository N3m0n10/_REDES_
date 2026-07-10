from socket import *
import time
from CLIENT import check_sum, bit_a_bit_sum #provisorio

server_port = 7777
SERVER = socket(AF_INET, SOCK_DGRAM)
SERVER.bind(('', server_port))
SERVER.settimeout(120)
CONNECTIONS = []
connecting = False
con_wait = 50
con_wait_count = 0
CABSIZE = 31
MAXSIZE = 1024 - CABSIZE 
messages = {}
waiting = {}

def frame(msg="", tipo="", seq=0, tamanho=0, checksum="0"*16):
    return (
        tipo +
        format(tamanho, "010b") +
        format(seq, "03b") +
        checksum +
        msg
    )

def parse_frame(raw):
    raw = raw.decode()

    tipo = raw[0:2]
    tamanho = int(raw[2:12], 2)
    seq = int(raw[12:15], 2)
    checksum = raw[15:31]
    payload = raw[31:]

    return tipo, tamanho, seq, checksum, payload

# só recebimento
def r_check_sum(msg,checksum,test=False): # msg = data (pré separada), checksum da msg já separado
    # divide msg em partes de 16 bits + pad 0
    # soma com complemento de 1
    # soma com o campo checksum da msg
    # se 1111111111111111 -> msg correta -> retorna True
    if test:
        return False
    else:
        chk = check_sum(msg,rec=True)
        return bit_a_bit_sum(chk,checksum) == "1111111111111111"

while True:
    data, addr = SERVER.recvfrom(1024)
    tipo, tamanho, seq, check, payload = parse_frame(data)

    if addr in CONNECTIONS:
        print(data.decode())
        """" teste de msg direta
        print(f"Received message: {data.decode()} from {addr}")
        # pseudo ACK
        SERVER.sendto("Message received".encode(), addr)
        """
        match tipo:
            case "00": # fin -> monta a msg total 

                if not r_check_sum(payload,checksum=check):
                    SERVER.sendto(frame(tipo="10", seq=seq).encode(), addr) # nack
                    print("Checksum inválido para o frame recebido, enviando NACK")
                    continue
                
                """
                if not tamanho == len(payload):
                    SERVER.sendto(frame(tipo="10", seq=seq).encode(), addr) # nack
                    print("Tamanho não confere")
                    continue
                """

                if seq == 0: # fin e ultimo da seq
                    with open("message.bin", "wb") as resp:
                        resp.write(payload.encode())  # se enviar msg repetidas por engano de um só frame serão sobrescrevidas
                    messages.pop(addr,None)
                    SERVER.sendto(frame(tipo="11",seq=seq).encode(),addr) # ACK
                else:
                    if addr not in messages: # se a primeira recebida foi fin mas seq != 0 [meio bagunçado :/]
                        messages[addr] = [(seq,payload)]
                    now_seqs = [messages[addr][k][0] for k in range(len(messages[addr]))]
                    if seq in now_seqs:
                        print("Mensagem repetida!")
                        continue
                    SERVER.sendto(frame(tipo="11",seq=seq).encode(),addr) # ACK
                    print(f"Mensagem de sequencia {seq} com FIN recebida!")
                    # adicionar a última msg
                    messages[addr].append((seq,payload))
                    # tratar casos: é a ultima e tem todas | falta msgs
                    full_message = ""
                    psb_msg = [i for i in range(seq + 1)] #possíveis msgs até fin
                    ext_msg = [messages[addr][j][0] for j in range(len(messages[addr]))] #msgs existentes
                    need_msg = [i for i in psb_msg if i not in ext_msg] #msgs faltando
                    if need_msg == []:
                        sortmsgs = sorted(messages[addr], key=lambda x: x[0]) #ordena por seq
                        for m_num in range(seq + 1):
                            full_message += sortmsgs[m_num][1]
                        # montagem usa BYTE
                        mount = bytearray(
                            int(full_message[i:i+8], 2)
                            for i in range(0, len(full_message), 8)
                        )
                        with open("message.bin", "wb") as resp:
                            resp.write(mount)
                        messages.pop(addr,None)
                        del full_message, mount
                        print("Arquivo montado em binário!")
                    # checar se todos os frames chegaram e montar a msg total
                    else: 
                        if addr in waiting:
                            # espera msgs
                            for s_num in need_msg: 
                                waiting[addr].append(s_num)
                        else:
                            waiting[addr] = set(s_num for s_num in need_msg)

            case "11": # espera a proxima msg
                
                """
                print("PAYLOAD:", payload[:50])
                print("CHK RECEBIDO:", check)
                calc = check_sum(payload)
                print(len(calc))
                print("CHK CALCULADO:", calc)
                print("SERVER LEN:", len(payload))
                print("TAMANHO FRAME:", tamanho)
                raise Exception("testanto valores")
                """
                # checsksum
                if not r_check_sum(payload,checksum=check):
                    SERVER.sendto(frame(tipo="10", seq=seq).encode(), addr) # nack
                    print("Failed checksum - dados")
                    continue
                
                # ver se o addr tem msgs
                if addr in messages:
                    # teste de msg repetida
                    now_seqs = [messages[addr][k][0] for k in range(len(messages[addr]))]
                    if seq in now_seqs:
                        print("Mensagem repetida!")
                        continue
                    messages[addr].append((seq,payload))
                    print(f"Mensagem de sequencia {seq} recebida!")
                    if addr in waiting:
                        if seq in waiting[addr]: # se esperando
                            waiting[addr].remove(seq)
                        # se não há mais nada na espera
                        if waiting[addr] == []:
                            full_message = ""
                            waiting.pop(addr,None)
                            sortmsgs = sorted(messages[addr], key=lambda x: x[0])
                            for m_num in range(len(messages[addr])):
                                full_message += sortmsgs[m_num][1]
                            mount = bytearray(
                                int(full_message[i:i+8], 2)
                                for i in range(0, len(full_message), 8)
                                )
                            with open("message.bin","wb") as resp:
                                resp.write(mount)
                            messages.pop(addr,None)
                            del full_message, mount
                            print("Arquivo montado! FIN antecipado.")
                
                # senão, adicionar
                else:
                    messages[addr] = [(seq,payload)]
                
                # ack da sequencia 
                SERVER.sendto(frame(tipo="11", seq=seq).encode(),addr) # ACK

            case "10": # nack -> msg de texto pqn direta (teste) 
                """Mensagens não salvas!"""
                print(f"Received message: {payload} from {addr}")
                SERVER.sendto(frame(tipo="11",msg="Mensagem recebida").encode(), addr) # provisório
            case _ : # quando conectado só pode receber msg(nack), msg(ack) e fin | ignora o resto
                pass

    # Connection request
    if tipo == "01" and len(CONNECTIONS) < 3\
        and addr not in CONNECTIONS:  
        # se não lotado, tipo = pede_req e não conectado
        connecting = True
        con_addr = addr
        if connecting:
            SERVER.sendto(frame(tipo="11").encode(), addr) # ack zerado
            print(f"Sent ACK to {addr}")
            # count here
            data, addr = SERVER.recvfrom(1024)
            # fazer loop de espra
            if data[:2] == b"11" and len(CONNECTIONS) < 3 \
                and addr == con_addr and con_wait_count < con_wait:
                con_wait_count = 0
                CONNECTIONS.append(addr)
                print(f"Connection established with {addr}")
                connecting = False


# se conectado mas mandar pede_req? posivelmente reiniciou
# descosiderando ataque para disconectar ou erro de pedido
# ignorar e esperar timeout (se alarme falso haverá novas msgs)