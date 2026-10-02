# Falta o `sim_cfg.json`

O portão (`testa_sim.py`) precisa de `sim_cfg.json`: a configuração **congelada** de teste,
um recorte do Mad Max com 17 MODs. Ela não está aqui de propósito — é configuração sua, e
tudo que entra num repositório público vira legível por qualquer um.

Para rodar o portão, gere o arquivo a partir da sua biblioteca:

```python
import json
B = json.load(open('biblioteca.json'))
mm = next(j for j in B['jogos'] if j.get('nome') == 'Mad Max')
json.dump({'jogos': [mm], 'ordem': [0]},
          open('sim_cfg.json', 'w'), ensure_ascii=False, indent=1)
```

E coloque em `ferramentas/`, ao lado do `testa_sim.py`.

**Por que congelada e não a biblioteca viva:** se as expectativas do teste viessem dos seus
dados, elas mudariam junto e o teste viraria espelho. O MOD_11 tem de sair 150/50/150/50/
150/50/250 ms porque foi assim que o PLOT mediu no hardware, não porque é o que a
biblioteca diz hoje.

Se preferir manter o repositório privado, basta incluir o `sim_cfg.json` normalmente.
