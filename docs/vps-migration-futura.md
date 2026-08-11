# Migração futura para VPS (documentado, não implementado)

Este documento descreve o caminho para, no futuro, mudar o Sentinela de
"correr apenas quando o PC Windows está ligado" para "correr 24/7". Nada
aqui está implementado — é só o plano para quando decidires avançar.

## Porque não agora

A instalação local (Fase 1) é nativa (Python + ambiente virtual, sem
Docker), por escolha deliberada, para evitar mexer em virtualização na
BIOS. Isso não impede a migração futura — só significa que, no VPS,
faz mais sentido correr o Freqtrade como um **serviço systemd** (Linux),
em vez de depender de uma janela aberta como no Windows. O `user_data/`
(estratégias, configuração, base de dados) pode ser copiado para o VPS
quase sem alterações; o que muda é só a forma como o processo arranca e
fica em segundo plano.

## Opção recomendada: Oracle Cloud (camada gratuita "Always Free")

- A Oracle Cloud oferece instâncias `Always Free` (ARM Ampere, até 4 vCPU /
  24 GB RAM no total, ou uma instância AMD pequena) sem limite de tempo,
  ao contrário de "free trials" de 12 meses de outros fornecedores.
- Passos futuros, em alto nível:
  1. Criar conta Oracle Cloud e ativar uma instância `Always Free` (Ubuntu).
  2. Instalar Python e criar um ambiente virtual na instância, tal como no
     PC Windows (ou, alternativamente, usar Docker no VPS mesmo que o PC
     local não use — no Linux é mais simples e sem a fricção da BIOS).
  3. Copiar a pasta do projeto (`user_data/`, `start.ps1` como referência)
     para o VPS via `git clone` ou `scp`.
  4. Repor os segredos (chaves API, token Telegram, password do FreqUI) —
     nunca copiar o `config.json` real através do Git; transferir à parte
     (ex. `scp` direto ou copiar manualmente).
  5. Criar um serviço `systemd` (ou usar Docker com
     `restart: unless-stopped`) para que o Freqtrade arranque sozinho e
     se mantenha em segundo plano, sobrevivendo a reinícios do VPS.
  6. Ajustar `api_server.listen_ip_address` no `config.json` e considerar
     um proxy reverso com HTTPS (ex. Caddy ou Nginx) e autenticação, já
     que o painel passa a estar acessível pela internet e não só na rede
     local.
  7. Configurar firewall da instância (Oracle Cloud + `ufw` no Ubuntu) para
     só abrir as portas estritamente necessárias.

## Alternativas mais simples (com custo)

- Um VPS barato (ex. Hetzner, DigitalOcean) por poucos euros/mês, se a
  camada gratuita da Oracle se tornar limitativa ou pouco fiável.

## Riscos adicionais a considerar nessa altura (não aplicáveis enquanto
correr localmente)

- Exposição do painel FreqUI à internet exige HTTPS + password forte
  (idealmente autenticação adicional/VPN) — nunca deixar a porta 8080
  exposta diretamente sem proteção.
- Backups automáticos da base de dados (`tradesv3.sqlite`) e da
  configuração, já que deixa de haver "o PC" como cópia única.
- Monitorização de que o processo continua vivo (ex. `healthcheck` no
  Docker Compose, ou um serviço externo tipo UptimeRobot a verificar a
  API do Freqtrade).
