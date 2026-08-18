from market_monitor_bot.prematch_fetcher import PrematchFetcher
f = PrematchFetcher()
print('Buscando jogos do dia...')
matches = f.analyze_todays_matches(max_matches=5)
for m in matches:
    print(m['home'], 'vs', m['away'], '|', m['league'], '| Score:', m['score'], '| Prob HT:', m['prob_ht'], '|', m['recomendacao'])
print('Total:', len(matches))
