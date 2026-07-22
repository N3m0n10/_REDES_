# Implementação de um protocolo semelhante ao TCP com base em UDP
Inicialmente elaborado para como projeto final da classe *DAS5314*

## Características Técnicas

### Implementação
- **Camada de Aplicação**: Cliente e Servidor
- **Camada de Transporte**: UDP com confiabilidade
- **Controle de Fluxo**: Janela deslizante (tamanho 4)
- **Controle de Erro**: Checksum e NACK/ACK
- **Recuperação**: Retransmissão por timeout

### Estados do Protocolo
1. **INICIALIZAÇÃO**: Handshake 3 vias
2. **TRANSMISSÃO**: Envio com janela deslizante
3. **RECUPERAÇÃO**: Retransmissão de frames perdidos
4. **FINALIZAÇÃO**: Envio de FIN

### Métricas de Confiabilidade
- ✅ Detecção de erros via checksum
- ✅ Confirmação positiva (ACK)
- ✅ Confirmação negativa (NACK)
- ✅ Timeout e retransmissão
- ✅ Reordenação de pacotes
- ✅ Controle de fluxo por janela

## Como Usar

1. **Inicializar conexão**: Cliente envia PEDE_REQ
2. **Handshake**: Aguarda ACK do servidor
3. **Transmissão**: Envia frames sequenciais
4. **Monitoramento**: Acompanha logs e status
5. **Recuperação**: Trata erros automaticamente
6. **Finalização**: Envia FIN para fechar conexão

## Simulação de Erros

O simulador permite testar diferentes cenários de falha:
- **Checksum inválido**: Simula corrupção de dados
- **Perda de pacote**: Simula perda na rede
- **Timeout**: Simula lentidão na rede
- **Fora de ordem**: Simula reordenação de pacotes

## Benefícios do Protocolo

🔒 **Confiabilidade**: Garante entrega de dados mesmo sobre UDP
🔄 **Recuperação**: Retransmissão automática de pacotes perdidos
📊 **Controle**: Janela deslizante para controle de fluxo
🛡️ **Integridade**: Checksum para detecção de erros
⚡ **Eficiência**: Mínimo de overhead com máximo de confiabilidade

---

*Simulador para demonstração de protocolos de comunicação confiáveis sobre UDP*
