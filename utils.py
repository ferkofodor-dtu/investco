import yfinance as yf
import json

def read_ticker_list(file_path):
    """
    Reads a list of stock ticker symbols from a file.
    
    Args:
        file_path (str): The path to the file containing ticker symbols.
        
    Returns:
        list: A list of ticker symbols.
    """
    with open(file_path, 'r') as f:
        tickers = [line.strip().replace(',', '') for line in f if line.strip()]
    return tickers



def get_ticker_info(ticker, save_path=None):
    """
    Fetches stock information for a given ticker symbol using yfinance.
    
    Args:
        ticker (str): The stock ticker symbol.
        
    Returns:
        dict: A dictionary containing stock information.
    """
    stock = yf.Ticker(ticker)
    info = stock.info

    if save_path:
        with open(save_path, 'w') as f:
            json.dump(info, f, indent=4)

    return info


def load_ticker_info(file_path):
    """
    Loads stock information from a JSON file.
    
    Args:
        file_path (str): The path to the JSON file containing stock information.
        
    Returns:
        dict: A dictionary containing stock information.
    """
    with open(file_path, 'r') as f:
        info = json.load(f)
    return info