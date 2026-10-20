#!/usr/bin/env python3
"""Grava em mercados.csv a probabilidade de vitória de Flávio e Lula na Polymarket e na Kalshi.

Roda no GitHub Actions (mercados.yml). Usa só as APIs públicas e a biblioteca padrão.
Na primeira execução, quando o arquivo ainda não tem histórico, preenche a série desde 01/09/2026.
Cada execução acrescenta uma leitura por plataforma; nunca apaga linhas.
"""
import csv, json, os, sys, time, urllib.request
from datetime import datetime, timezone

ARQ = 'mercados.csv'
CAMPOS = ['data_hora', 'plataforma', 'flavio', 'lula', 'volume', 'unidade_volume', 'origem', 'fonte']
INICIO = int(datetime(2026, 9, 1, tzinfo=timezone.utc).timestamp())

PM_EVENTO = 'https://gamma-api.polymarket.com/events?slug=brazil-presidential-election'
PM_HIST = 'https://clob.polymarket.com/prices-history?market={tok}&startTs={ini}&endTs={fim}&fidelity=360'
PM_HIST_MAX = 'https://clob.polymarket.com/prices-history?market={tok}&interval=max&fidelity=360'
PM_PAGINA ='https://polymarket.com/event/brazil-presidential-election'
KS_API = 'https://api.elections.kalshi.com/trade-api/v2'
KS_EVENTO = 'KXBRPRES-26'
KS_FLAVIO, KS_LULA = 'KXBRPRES-26-FBOL', 'KXBRPRES-26-LULA'
KS_PAGINA = 'https://kalshi.com/markets/kxbrpres/brazil-presidency/kxbrpres-26'


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'radar-2turno/1.0', 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def iso(ts):
    return datetime.fromtimestamp(int(ts), timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def pct(p):
    return round(float(p) * 100, 1)


def polymarket():
    ev = get(PM_EVENTO)
    ev = ev[0] if isinstance(ev, list) else ev
    def mercado(nome):
        for m in ev['markets']:
            if nome in m.get('groupItemTitle', ''):
                return m
        raise RuntimeError(f'Polymarket: mercado de {nome} não encontrado')
    f, l = mercado('Flávio'), mercado('Lula')
    preco = lambda m: json.loads(m['outcomePrices'])[0] if isinstance(m['outcomePrices'], str) else m['outcomePrices'][0]
    token = lambda m: (json.loads(m['clobTokenIds']) if isinstance(m['clobTokenIds'], str) else m['clobTokenIds'])[0]
    agora = {'plataforma': 'Polymarket', 'flavio': pct(preco(f)), 'lula': pct(preco(l)),
             'volume': round(float(ev.get('volume') or 0)), 'unidade_volume': 'US$', 'fonte': PM_PAGINA}
    return agora, token(f), token(l)


def polymarket_hist(tok_f, tok_l, fim):
    serie = {}
    for nome, tok in (('flavio', tok_f), ('lula', tok_l)):
        hist = get(PM_HIST.format(tok=tok, ini=INICIO, fim=fim)).get('history', [])
        if not hist:  # a API às vezes recusa janelas longas; tenta a série completa
            hist = [p for p in get(PM_HIST_MAX.format(tok=tok)).get('history', []) if int(p['t']) >= INICIO]
        for p in hist:
            serie.setdefault(int(p['t']) // 21600 * 21600, {})[nome] = pct(p['p'])
    return [{'data_hora': iso(t), 'plataforma': 'Polymarket', 'flavio': v['flavio'], 'lula': v['lula'], 'volume': '',
             'unidade_volume': '', 'origem': 'Histórico', 'fonte': PM_PAGINA}
            for t, v in sorted(serie.items()) if 'flavio' in v and 'lula' in v]


def kalshi():
    ms = {m['ticker']: m for m in get(f'{KS_API}/markets?event_ticker={KS_EVENTO}')['markets']}
    def prob(m):
        bid, ask = float(m.get('yes_bid_dollars') or 0), float(m.get('yes_ask_dollars') or 0)
        if 0 < bid <= ask < 1 and ask - bid <= 0.05:
            return pct((bid + ask) / 2)
        return pct(m.get('last_price_dollars') or 0)
    f, l = ms[KS_FLAVIO], ms[KS_LULA]
    vol = sum(float(m.get('volume_fp') or 0) for m in (f, l))
    return {'plataforma': 'Kalshi', 'flavio': prob(f), 'lula': prob(l), 'volume': round(vol),
            'unidade_volume': 'contratos', 'fonte': KS_PAGINA}


def kalshi_hist(fim):
    serie = {}
    for nome, tk in (('flavio', KS_FLAVIO), ('lula', KS_LULA)):
        url = f'{KS_API}/series/KXBRPRES/markets/{tk}/candlesticks?start_ts={INICIO}&end_ts={fim}&period_interval=60'
        for c in get(url).get('candlesticks', []):
            t = int(c['end_period_ts'])
            if t % 21600:  # uma leitura a cada 6 horas, como na Polymarket
                continue
            close = (c.get('price') or {}).get('close_dollars')
            if close is None:
                b, a = (c.get('yes_bid') or {}).get('close_dollars'), (c.get('yes_ask') or {}).get('close_dollars')
                close = (float(b) + float(a)) / 2 if b is not None and a is not None else None
            if close is not None:
                serie.setdefault(t, {})[nome] = pct(close)
    return [{'data_hora': iso(t), 'plataforma': 'Kalshi', 'flavio': v['flavio'], 'lula': v['lula'], 'volume': '',
             'unidade_volume': '', 'origem': 'Histórico', 'fonte': KS_PAGINA}
            for t, v in sorted(serie.items()) if 'flavio' in v and 'lula' in v]


def main():
    linhas = list(csv.DictReader(open(ARQ, encoding='utf-8'))) if os.path.exists(ARQ) else []
    agora_ts = int(time.time())
    carimbo = iso(agora_ts)
    novas, erros = [], []
    tem_hist = {p: any(r['plataforma'] == p and r['origem'] == 'Histórico' for r in linhas) for p in ('Polymarket', 'Kalshi')}

    try:
        pm, tf, tl = polymarket()
        if not tem_hist['Polymarket']:
            try: novas += polymarket_hist(tf, tl, agora_ts)
            except Exception as e: erros.append(f'Polymarket histórico: {e}')
        novas.append({**pm, 'data_hora': carimbo, 'origem': 'Leitura'})
    except Exception as e:
        erros.append(f'Polymarket: {e}')

    try:
        if not tem_hist['Kalshi']:
            try: novas += kalshi_hist(agora_ts)
            except Exception as e: erros.append(f'Kalshi histórico: {e}')
        novas.append({**kalshi(), 'data_hora': carimbo, 'origem': 'Leitura'})
    except Exception as e:
        erros.append(f'Kalshi: {e}')

    for e in erros:
        print('ERRO', e, file=sys.stderr)
    if not novas:
        sys.exit('Nenhuma plataforma respondeu.')
    with open(ARQ, 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        w.writeheader()
        todas = linhas + novas
        todas.sort(key=lambda r: (r['data_hora'], r['plataforma']))
        w.writerows(todas)
    for r in novas[-2:]:
        print(r['data_hora'], r['plataforma'], 'Flávio', r['flavio'], 'Lula', r['lula'], r['volume'], r['unidade_volume'])
    print(f'{len(novas)} linhas acrescentadas.')


if __name__ == '__main__':
    main()
