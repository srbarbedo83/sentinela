# Migração futura para VPS (documentado, não implementado)

Este documento descreve o caminho para, no futuro, mudar o Sentinela de
"correr apenas quando o PC Windows está ligado" para "correr 24/7". Nada
aqui está implementado — é só o plano para quando decidires avançar.

## Porque não agora

O sistema foi montado com Docker, exatamente para que este passo seja uma
mudança de "onde corre o Docker", não uma reescrita. O `docker-compose.yml`,
o `user_data/` (estratégias, configuração, base de dados) e os scripts
usados no PC podem, em princípio, ser copiados para o VPS quase sem
alterações.

## Opção recomendada: Oracle Cloud (camada gratuita "Always Free")

- A Oracle Cloud oferece instâncias `Always Free` (ARM Ampere, até 4 vCPU /
  24 GB RAM no total, ou uma instância AMD pequena) sem limite de tempo,
  ao contrário de "free trials" de 12 meses de outros fornecedores.
- Passos futuros, em alto nível:
  1. Criar conta Oracle Cloud e ativar uma instância `Always Free` (Ubuntu).
  2. Instalar Docker e Docker Compose na instância.
  3. Copiar a pasta do projeto (`docker-compose.yml`, `user_data/`) para o
     VPS via `git clone` ou `scp`.
  4. Repor os segredos (chaves API, token Telegram, password do FreqUI) —
     nunca copiar o `config.json` real através do Git; transferir à parte
     (ex. `scp` direto ou copiar manualmente).
  5. Ajustar `docker-compose.yml`: alterar `listen_ip_address` do
     `api_server` e considerar um proxy reverso com HTTPS (ex. Caddy ou
     Nginx) e autenticação, já que o painel passa a estar acessível pela
     internet e não só na rede local.
  6. Configurar firewall da instância (Oracle Cloud + `ufw` no Ubuntu) para
     só abrir as portas estritamente necessárias.
  7. Configurar arranque automático do Docker Compose ao reiniciar o VPS
     (`restart: unless-stopped` já está definido no `docker-compose.yml`).

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
