import pandas as pd, streamlit as st
import requests, json
import time, datetime

def get_swaps(api_key, real_swaps, address, start_date):

    start_timestamp = int(datetime.datetime.strptime(start_date, "%Y-%m-%d").timestamp())

    #Filter address
    address_real_swaps = real_swaps.loc[real_swaps.address == address]
    if len(address_real_swaps) > 0:
        mints_address_real_swaps = address_real_swaps.loc[address_real_swaps.timestamp.idxmin()]
        txn_sign = mints_address_real_swaps.signature
        txn_timestamp = mints_address_real_swaps.timestamp
    else:
        txn_sign = None
        txn_timestamp = start_timestamp

    #Params
    url = f"https://api.helius.xyz/v0/addresses/{address}/transactions"
    params = {
        "api-key": api_key,
        "type": "SWAP",  # This filters for swap transactions
        "before": txn_sign
    }

    swaps = []
    while txn_timestamp >= start_timestamp:

        #Get transactions
        response = requests.get(url, params=params)
        response.raise_for_status()
        transactions = response.json()

        while len(transactions) == 0:
            print('Retrying')
            time.sleep(30)
            response = requests.get(url, params=params)
            response.raise_for_status()
            transactions = response.json()

        #Update params
        txn_sign = transactions[-1]['signature']
        txn_timestamp = transactions[-1]['timestamp']
        print(pd.to_datetime(txn_timestamp, unit='s'))

        #Process transactions
        for transaction in transactions:
            swap = {
                "signature": transaction['signature'],
                "timestamp": transaction['timestamp'],
                "description": transaction['description'],
                "source": transaction['source'],
                "token_in": "",
                "token_in_amount": 0,
                "token_out": "",
                "token_out_amount": 0
            }
            
            for transfer in transaction['tokenTransfers']:
                if transfer['fromUserAccount'] == address:
                    swap['token_in'] = transfer['mint']
                    swap['token_in_amount'] = transfer['tokenAmount']
                else:
                    swap['token_out'] = transfer['mint']
                    swap['token_out_amount'] = transfer['tokenAmount']

            swaps.append(swap)
            params['before'] = txn_sign

    if len(swaps) > 0:
        # Create DataFrame
        swaps = pd.DataFrame(swaps)
        
        swaps['address'] = address
    else:
        swaps = pd.DataFrame()

    return pd.concat([real_swaps,swaps])

def simulate(real_swaps, address, start_date, start_sol, buy_perc, max_buy, txn_fee_buy, txn_fee_sell, slip_buy, slip_sell):

    start_timestamp = int(datetime.datetime.strptime(start_date, "%Y-%m-%d").timestamp())

    # real_swaps
    real_swaps = real_swaps[real_swaps.address == address]
    real_swaps = real_swaps[real_swaps.timestamp >= start_timestamp]

    # Sort the dataframe by timestamp to ensure chronological order
    real_swaps = real_swaps.sort_values('timestamp')
    real_swaps.dropna(subset=['token_in','token_out'],how='any',inplace=True)
    real_swaps = real_swaps[real_swaps.token_in != '']
    real_swaps = real_swaps[real_swaps.token_out != '']

    # Initialize portfolio
    real_portfolio = {'SOL': float('inf')}
    sim_portfolio = {'SOL': start_sol}
    sim_swaps = []

    for _, real_swap in real_swaps.iterrows():
        if real_swap['token_in'] == 'So11111111111111111111111111111111111111112':  # This is the SOL mint address
            
            token_out = real_swap['token_out']
            real_token_in_amount = float(real_swap['token_in_amount'])
            real_token_out_amount = float(real_swap['token_out_amount'])

            #Update real portfolio
            real_portfolio['SOL'] -= real_token_in_amount
            real_portfolio[token_out] = real_portfolio.get(token_out, 0) + real_token_out_amount

            # This is a buy transaction (swapping SOL for another token)
            sim_token_in_amount = min(real_token_in_amount * buy_perc, max_buy)
            bot_fee = sim_token_in_amount * 0.01            
            if sim_token_in_amount >= sim_portfolio['SOL']:
                print('Insufficient SOL for signature:', real_swap['signature'],' on:', pd.to_datetime(real_swap['timestamp'],unit='s'))
            else:
                sim_token_out_amount = real_token_out_amount * buy_perc * 1/(1+slip_buy)
                
                # Update portfolio
                sim_portfolio['SOL'] -= sim_token_in_amount
                sim_portfolio['SOL'] -= bot_fee
                sim_portfolio['SOL'] -= txn_fee_buy
                sim_portfolio[token_out] = sim_portfolio.get(token_out, 0) + float(sim_token_out_amount)
                
                # Record transaction
                sim_swaps.append({
                    'signature': real_swap['signature'],
                    'timestamp': real_swap['timestamp'],
                    'description': real_swap['description'],
                    'source': real_swap['source'],
                    'action': 'buy',
                    'token_in': 'So11111111111111111111111111111111111111112',
                    'token_in_amount': sim_token_in_amount,
                    'token_out': token_out,
                    'token_out_amount': sim_token_out_amount,
                    'bot_fee':bot_fee,
                    'txn_fee':txn_fee_buy
                })
        
        elif real_swap['token_out'] == 'So11111111111111111111111111111111111111112':
            # This is a sell transaction (swapping another token for SOL)
            # We don't need to do anything here as we're only simulating buys
            token_in = real_swap['token_in']
            real_token_in_amount = float(real_swap['token_in_amount'])
            real_token_out_amount = float(real_swap['token_out_amount'])

            sell_perc = real_token_in_amount / max(real_portfolio.get(token_in,0),real_token_in_amount)

            #Update real portfolio
            real_portfolio['SOL'] += real_token_out_amount
            real_portfolio[token_in] = max(real_portfolio.get(token_in, 0),real_token_in_amount) - real_token_in_amount

            if token_in in sim_portfolio and sim_portfolio[token_in] > 0:
                sim_token_in_amount = sim_portfolio[token_in] * sell_perc
                sim_token_out_amount = (sim_token_in_amount / real_token_in_amount) * real_token_out_amount * 1/(1+slip_sell)
                bot_fee = sim_token_out_amount * 0.01

                # Update portfolio
                sim_portfolio['SOL'] += sim_token_out_amount
                sim_portfolio['SOL'] -= bot_fee
                sim_portfolio['SOL'] -= txn_fee_sell
                sim_portfolio[token_in] = sim_portfolio.get(token_in, 0) - sim_token_in_amount

                # Record transaction
                sim_swaps.append({
                    'signature': real_swap['signature'],
                    'timestamp': real_swap['timestamp'],
                    'description': real_swap['description'],
                    'source': real_swap['source'],
                    'action': 'sell',
                    'token_in': token_in,
                    'token_in_amount': sim_token_in_amount,
                    'token_out': 'So11111111111111111111111111111111111111112',
                    'token_out_amount': sim_token_out_amount,
                    'bot_fee':bot_fee,
                    'txn_fee':txn_fee_sell
                })

    # Create a DataFrame from the transactions
    sim_swaps = pd.DataFrame(sim_swaps)
    
    return real_portfolio, sim_portfolio, sim_swaps    

def convert2sol(sim_portfolio, api_key, price_per_sol):

    url = f"https://mainnet.helius-rpc.com/?api-key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }

    sol_sim_portfolio, usdc_sim_portfolio = {}, {}
    for token, amount in sim_portfolio.items():

        if amount == 0:
            continue

        elif token == 'SOL':
            sol_sim_portfolio[token] = amount 
            usdc_sim_portfolio[token] = price_per_sol
        
        else:

            payload = {
                "jsonrpc": "2.0",
                "id": "my-id",
                "method": "getAsset",
                "params": {
                    "id": token
                }
            }
            
            response = requests.post(url, headers=headers, data=json.dumps(payload))

            response.raise_for_status()

            data = response.json()
            price_per_token = data['result']['token_info'].get('price_info',{}).get('price_per_token',0)
            sol_sim_portfolio[token] = (amount * price_per_token)/price_per_sol if price_per_token > 0 else 0
            usdc_sim_portfolio[token] = price_per_token

    return sol_sim_portfolio, usdc_sim_portfolio

st.title('Copy Trader')
api_key = st.secrets['helius_key']

# Usage
col1, col2, col3, col4, col5 = st.columns(5)
address = col1.text_input('Address:')
start_date = col2.date_input('Start Date:')
end_date = col2.date_input('End Date:')
start_sol = col1.number_input('Start Sol:')
buy_perc = col3.number_input('Buy Percentage:')
max_buy = col3.number_input('Buy Max:')
txn_fee_buy = col4.number_input('Buy Txn Fee:')
txn_fee_sell = col4.number_input('Sell Txn Fee:')
slip_buy = col5.number_input('Buy Slippage:')
slip_sell = col5.number_input('Sell Slippage:')

if st.button('Load:'):

    #Get swaps
    # real_swaps = pd.read_csv('real_swaps.csv')
    real_swaps = pd.DataFrame()
    real_swaps = get_swaps(api_key, real_swaps, address, start_date)
    # real_swaps.to_csv('real_swaps.csv', index=False)

    #Simulate copy trading
    real_portfolio, sim_portfolio, sim_swaps = simulate(real_swaps=real_swaps, address=address, start_date=start_date, start_sol=start_sol, buy_perc=buy_perc, max_buy=max_buy, txn_fee_buy=txn_fee_buy, txn_fee_sell=txn_fee_sell, slip_buy=slip_buy, slip_sell=slip_sell)
    # pd.DataFrame(real_portfolio,index=[0]).to_csv('real_portfolio.csv',index=False)
    # pd.DataFrame(sim_portfolio,index=[0]).to_csv('sim_portfolio.csv',index=False)
    # sim_swaps.to_csv('sim_swaps.csv',index=False)

    #Convert to SOL
    sol_sim_portfolio, usdc_sim_portfolio = convert2sol(sim_portfolio, api_key, 245)
    # pd.DataFrame(sol_sim_portfolio,index=[0]).to_csv('sol_sim_portfolio.csv',index=False)
    # pd.DataFrame(usdc_sim_portfolio,index=[0]).to_csv('usdc_sim_portfolio.csv',index=False)