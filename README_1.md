# Radar 2º Turno 2026

Pesquisas nacionais de 2º turno Lula x Flávio Bolsonaro: média ponderada, histórico por instituto e agenda de divulgações.

Site: https://fredvilaronga-star.github.io/pesquisa2turno/

- `index.html`: a página. Lê os CSVs da raiz do repositório a cada acesso.
- `pesquisas.csv`: histórico, uma linha por rodada, com link da reportagem.
- `agenda.csv`: pesquisas registradas no TSE com divulgação prevista.
- `quaest.csv`, `primeiro_turno.csv`: recortes da Quaest de 14/10 e resultado do 1º turno (TSE).
- `datafolha.csv`: detalhe de cada rodada do Datafolha no 2º turno (estimulada, rejeição, certeza e recortes por grupo), atualizado pelo workflow.
- `.github/workflows/atualizar.yml`: busca pesquisas novas às 7h45, 14h45 e 20h45 (Brasília) e publica.

Só entra número com fonte pública verificável e registro no TSE.
