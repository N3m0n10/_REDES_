from socket import *
import os
import time

# TCP à partir de UDP

S = socket(AF_INET, SOCK_DGRAM)
porta = 7777  # SERVER PORT
IP = gethostbyname('localhost')
wait_resp = 10
CONNECTED = False
SIZE = 993 # 1kb -> 1024 (contagens levam 0)
CABSIZE = 31
BUFFER = 4

def frame(msg="", seq=0, tipo="", checksum="",tamanho=""):
    if tamanho == "":
        tamanho = len(msg)

    return (
        tipo +
        format(tamanho, "010b") +
        format(seq, "03b") +
        checksum +
        msg
    )

# 3 way handshake
def connect_to_server(sock,server_ip, server_port):
    # pedir conexão ao server | pede_req
    pd_req = (frame(tipo="01"))
    if pd_req is None:
        print("Erro ao criar frame de pedido de conexão")
        return False
    sock.sendto(pd_req.encode(), (server_ip, server_port))
    # esperar resposta 
    S.settimeout(wait_resp)
    try:
        # processar resposta | ack ou nack
        #raise timeout("Simulando timeout para teste")  # Simulação de timeout
        resposta, _ = sock.recvfrom(1024)
        if resposta.decode()[0:2] == "11":
            print("Conexão estabelecida com o servidor")
        elif resposta.decode()[0:2] == "10":
            print("Servidor recusou a conexão")
            return False
        else:
            print("Resposta inválida do servidor")
    except timeout as e:
        print("Tempo esgotado ao receber resposta:", e)
        return False
    except OSError as e:
        print("Erro de socket ao receber resposta:", e)
        return False

    resp_ack = (frame(tipo="11"))
    # iniciar conexão ou esperar e tentar novamente | print()
    if resp_ack is not None:
        sock.sendto(resp_ack.encode(), (server_ip, server_port))
        print("Enviando confirmação!")
        # envia ack se receber ack do server | ack
        return True
    return False # básico

def bit_a_bit_sum(a, b):
    s = int(a, 2) + int(b, 2)

    # carry de complemento de 1
    while s > 0xFFFF:
        s = (s & 0xFFFF) + (s >> 16)

    return format(s, "016b")

def bit_a_bit_sum_pythonic(a, b):
    return bin(int(a, 2) + int(b, 2))[2:]

# só envio
def check_sum(msg, rec=False):
    # divide msg em partes de 16 bits + pad 0
    chunks = []
    n_chunks = len(msg) // 16
    n_pad = len(msg) % 16
    padding = 16 - n_pad if n_pad != 0 else 0
    for i in range(n_chunks):
        chunks.append(msg[i*16:(i+1)*16])
    if n_pad != 0:
        chunks.append(msg[n_chunks*16:] + "0" * padding)
    n_c = "0000000000000000"
    # soma com complemento de 1
    for chunk in chunks:
        n_c = bit_a_bit_sum(n_c, chunk)
    if rec:
        return n_c
    # inverte bits e retorna
    n_c_list = list(n_c) # tranforma em lista para poder alterar os bits
    for k in range(len(n_c)):
        if n_c_list[k] == "0":
            n_c_list[k] = "1"
        else:
            n_c_list[k] = "0"
    return ''.join(n_c_list) #junta a lista num string

if __name__ == "__main__":
    run = True
    while run:
        while not CONNECTED:
            CONNECTED = connect_to_server(S, IP, porta)
        
        S.settimeout(wait_resp)
        estimated_rtt = wait_resp

        match input("pressione A p/ texto simples ou B p/ arquivo. \n X p/ encerrar \n").upper():
            case "A":
                msg = input('Digite a mensagem: ')
                msg_bits = ''.join(format(ord(c), '08b') for c in msg)
                enviado = False
                tentativas = 0
                max_tentativas = 3
                check = check_sum(msg_bits)
                
                while not enviado and tentativas < max_tentativas:
                    try:
                        tentativas += 1
                        print(f"Tentativa {tentativas}/{max_tentativas}...")
                        fr = frame(msg=msg,tipo="10",checksum=check)
                        
                        S.sendto(fr.encode(), (IP, porta))
                        resposta, _ = S.recvfrom(1024)

                        if resposta[:2] == b'11':
                            enviado = True # Enviado com sucesso!
                        elif resposta[:2] == b'10':
                            print("Servidor recusou a mensagem")
                        else:
                            print("Resposta inválida do servidor")

                        print('Resposta do servidor: ', resposta[31:].decode())
                        
                    except timeout:
                        print(f"Tempo esgotado na tentativa {tentativas}")
                        if tentativas >= max_tentativas:
                            print("Número máximo de tentativas atingido. Mensagem não enviada.")
                        else:
                            print("Reenviando mensagem em 1 segundo...")
                            time.sleep(1)  # Aguarda antes de reenviar

            case "B": # Sem BUFFER
                # É preciso dividir msgs grandes
                arch = "dummy_img390.png"
                with open(arch, 'rb') as f:
                    data = f.read()
                arch_bits = ''.join(format(byte, '08b') for byte in data)
                arc_pieces = []
                # dividir data com base no tamanho do arquivo
                if len(arch_bits) > SIZE:
                    for i in range(0, len(arch_bits), SIZE):
                        arc_pieces.append(arch_bits[i:i+SIZE])
                    if len(arc_pieces) > 8:
                        print("Arquivo excede limite de 8 frames!")
                        continue
                    # balanciar frame para não ter ultima parte muito maior que o cabeçalho
                    if len(arc_pieces[-1]) <= CABSIZE: # metade de tados para penúltimo e último frame
                        arc_pieces[-2] += arc_pieces[-1]
                        arc_pieces[-1] = arc_pieces[-2][SIZE//2:]
                        arc_pieces[-2] = arc_pieces[-2][:SIZE//2] 
                # enviar frame a frame e esperar ack do server
                else:
                    arc_pieces.append(arch_bits)
                for i, piece in enumerate(arc_pieces):
                    tipo = "00" if i == len(arc_pieces) - 1 else "11"
                    # Calcula checksum
                    chk = check_sum(piece)
                    a_msg = frame(msg=piece, tipo=tipo, seq=i,tamanho=(len(piece)),checksum=chk)
                    
                    enviado = False
                    tentativas = 0
                    max_tentativas = 3
                    
                    while not enviado and tentativas < max_tentativas:
                        try:
                            S.settimeout(estimated_rtt*2) # com sobra 
                            """
                            print("CLIENT LEN:", len(piece))
                            print("CLIENT CHK:", chk)
                            print("CLIENT PAYLOAD:", piece[:50])
                            print(len(chk))
                            print(chk)
                            """

                            tentativas += 1
                            # calculando o tempo de msg para RTT dinâmico
                            inicio = time.time()
                            S.sendto(a_msg.encode(), (IP, porta))
                            
                            # Espera resposta do servidor
                            resposta, _ = S.recvfrom(1024)
                            estimated_rtt = time.time() - inicio # tempo RTT
                            resp_dec = resposta.decode()
                            
                            if resp_dec[:2] == "11" and int(resp_dec[12:15],2) == i:
                                print(f"Parte {i+1}/{len(arc_pieces)} enviada ✓")
                                enviado = True
                            elif resp_dec[:2] == "10":
                                print(f"Servidor pediu reenvio da parte {i+1}")
                                # Continua no loop para reenviar
                            else:
                                print(f"Resposta inesperada: {resp_dec}")
                                enviado = True  # Sai para não travar
                                
                        except timeout:
                            print(f"Timeout na parte {i+1}, tentativa {tentativas}")
                            if tentativas < max_tentativas:
                                print(f"Reenviando em 1s...")
                                time.sleep(1)
                            else:
                                print(f"Falha ao enviar parte {i+1} após {max_tentativas} tentativas")
                                # Decide se continua ou aborta
                                # break  # Descomentar para abortar
                    
                    if not enviado:
                        print("Envio do arquivo abortado.")
                        break
                    else:
                        print("Arquivo enviado com sucesso!")
                pass
            case "X":
                run = False
            case _ : 
                print("Por favor, adicione um comando válido!")



# formato de msg: <tipo> <tamanho> <seq> <checksum> <dados>
# tipos: pede_req ack nack data=(fin?) --> 2 bits | 01 | 11 | 10 | 00
# tamanho: 10 bits (data até 1kb)
# seq: 3 bits (0-7) (limitar o cliente de mandar msg maior que seq max)
# checksum: 16 bits (usar crc16)
# em acks -> usar seq como ack num

# NOTE: updt -> em vez de data, msgs vão como ack. Com Fin para último frame

# TODO: em caso de muitas msgs sem ack -> suspeita de desconexão -> tentar reconectar