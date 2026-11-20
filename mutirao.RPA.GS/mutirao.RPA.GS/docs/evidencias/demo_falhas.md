# Demonstração de falhas tratadas

Gerado automaticamente por `python main.py falhas` em 19/11/2026 13:02.

| Cenário | Falha simulada | Esperado | Obtido | Passou? |
| :- | :- | :- | :- | :-: |
| API de clima fora do ar | URL da API apontando para um host inexistente | robô segue sem o critério de clima e explica isso na justificativa | 22 de 22 pedidos de lavoura com 'previsão indisponível'; disjuntor aberto após 2 falhas | sim |
| Sistema de ATER fora do ar | sistema desligado | nada se perde: tudo vai para a fila de pendentes | 0 registradas, 27 na fila de pendentes | sim |
| Arquivo corrompido | JSON cortado no meio (exportacao_interrompida.json) | arquivo vai para quarentena com o motivo e os outros 5 são lidos | 1 em quarentena (JSONDecodeError), 37 registros dos outros arquivos lidos | sim |
| Dados inválidos | data no futuro, texto 'oi', município inexistente e linha duplicada | rejeita com motivo e mensagem ao agricultor; duplicata ignorada | 3 rejeitadas, cada uma com motivo (BAL-0002, BAL-0007, COOP-0099), 1 duplicata ignorada | sim |
| Linha quebrada na fila do Fala, Lavoura! | última linha do JSONL cortada no meio | pula só a linha ruim e lê as outras fichas do mesmo arquivo | 6 fichas lidas do JSONL; a linha cortada foi registrada no log e pulada | sim |
| Sistema de ATER instável (erro 503) | sistema responde 503 a cada 4 cadastros | retry com espera recupera e a fila de pendentes zera | 27/27 registradas, 8 novas tentativas automáticas, fila de pendentes = 0 | sim |
| Execução repetida | rodar o robô de novo com os mesmos arquivos | nada é cadastrado em dobro no sistema de ATER | 37 já processadas ignoradas; o sistema continuou com 27 registros | sim |
| Senha do sistema errada | PORTAL_SENHA inválida no .env | não insiste no login, guarda na fila e registra quando a senha é corrigida | 1ª execução: 2 pendentes (CredenciaisInvalidas); após corrigir: 2 registradas | sim |
| Reenvio de pedido rejeitado | agricultor reenvia o BAL-0007 ('oi') com a descrição completa | o reenvio corrigido é processado; o original sem mudança continua ignorado | reenvio reconhecido e registrado (ATER-2026-000030); arquivo original sem mudança: 0 rejeições repetidas | sim |
| Arquivo ausente | caminho de arquivo que não existe | registra no log e termina a execução normalmente | status do arquivo: ausente; relatório gerado normalmente | sim |
