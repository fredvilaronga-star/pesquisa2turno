# Radar 2º Turno 2026

Pesquisas nacionais de 2º turno Lula x Flávio Bolsonaro: média ponderada, histórico por instituto e agenda de divulgações.

Site: https://fredvilaronga-star.github.io/pesquisa2turno/

- `index.html`: a página. Lê os CSVs da pasta `data/` a cada acesso.
- `data/pesquisas.csv`: histórico, uma linha por rodada, com link da reportagem.
- `data/agenda.csv`: pesquisas registradas no TSE com divulgação prevista.
- `data/quaest.csv`, `data/primeiro_turno.csv`: recortes da Quaest de 14/10 e resultado do 1º turno (TSE).
- `.github/workflows/atualizar.yml`: busca pesquisas novas às 7h45, 14h45 e 20h45 (Brasília) e publica.

Só entra número com fonte pública verificável e registro no TSE.
