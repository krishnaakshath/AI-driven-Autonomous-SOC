"""
NSL-KDD Dataset Loader for SOC ML Engine
==========================================
Loads the NSL-KDD intrusion detection dataset for training and evaluating
the Isolation Forest and Fuzzy C-Means models.

The NSL-KDD dataset is an industry-standard benchmark with ~125K training
records and ~22K test records, containing 41 features + attack labels.

Attack categories:
- normal: Legitimate traffic
- DoS: Denial of Service (neptune, smurf, back, teardrop, pod, land)
- Probe: Scanning/reconnaissance (satan, ipsweep, portsweep, nmap)
- R2L: Remote to Local (warezclient, guess_passwd, ftp_write, imap)
- U2R: User to Root (buffer_overflow, rootkit, perl, loadmodule)

Dataset source: https://www.unb.ca/cic/datasets/nsl.html
"""

import os
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Optional
import urllib.request
import ssl
import pickle

# Dataset URLs (GitHub mirrors for reliability)
TRAIN_URL = "https://raw.githubusercontent.com/jmnwong/NSL-KDD-Dataset/master/KDDTrain+.txt"
TEST_URL = "https://raw.githubusercontent.com/jmnwong/NSL-KDD-Dataset/master/KDDTest+.txt"

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# NSL-KDD column names (41 features + label + difficulty)
COLUMN_NAMES = [
    'duration', 'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes',
    'land', 'wrong_fragment', 'urgent', 'hot', 'num_failed_logins', 'logged_in',
    'num_compromised', 'root_shell', 'su_attempted', 'num_root', 'num_file_creations',
    'num_shells', 'num_access_files', 'num_outbound_cmds', 'is_host_login',
    'is_guest_login', 'count', 'srv_count', 'serror_rate', 'srv_serror_rate',
    'rerror_rate', 'srv_rerror_rate', 'same_srv_rate', 'diff_srv_rate',
    'srv_diff_host_rate', 'dst_host_count', 'dst_host_srv_count',
    'dst_host_same_srv_rate', 'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
    'dst_host_srv_diff_host_rate', 'dst_host_serror_rate', 'dst_host_srv_serror_rate',
    'dst_host_rerror_rate', 'dst_host_srv_rerror_rate',
    'label', 'difficulty'
]

# Map specific attack names to attack categories
ATTACK_CATEGORY_MAP = {
    'normal': 'normal',
    # DoS attacks
    'back': 'DoS', 'land': 'DoS', 'neptune': 'DoS', 'pod': 'DoS',
    'smurf': 'DoS', 'teardrop': 'DoS', 'mailbomb': 'DoS', 'apache2': 'DoS',
    'processtable': 'DoS', 'udpstorm': 'DoS',
    # Probe attacks
    'ipsweep': 'Probe', 'nmap': 'Probe', 'portsweep': 'Probe', 'satan': 'Probe',
    'mscan': 'Probe', 'saint': 'Probe',
    # R2L attacks
    'ftp_write': 'R2L', 'guess_passwd': 'R2L', 'imap': 'R2L', 'multihop': 'R2L',
    'phf': 'R2L', 'spy': 'R2L', 'warezclient': 'R2L', 'warezmaster': 'R2L',
    'sendmail': 'R2L', 'named': 'R2L', 'snmpgetattack': 'R2L', 'snmpguess': 'R2L',
    'xlock': 'R2L', 'xsnoop': 'R2L', 'worm': 'R2L',
    # U2R attacks
    'buffer_overflow': 'U2R', 'loadmodule': 'U2R', 'perl': 'U2R', 'rootkit': 'U2R',
    'httptunnel': 'U2R', 'ps': 'U2R', 'sqlattack': 'U2R', 'xterm': 'U2R',
}

# Numeric features to use for ML (exclude categorical)
NUMERIC_FEATURES = [
    'duration', 'src_bytes', 'dst_bytes', 'land', 'wrong_fragment', 'urgent',
    'hot', 'num_failed_logins', 'logged_in', 'num_compromised', 'root_shell',
    'su_attempted', 'num_root', 'num_file_creations', 'num_shells',
    'num_access_files', 'num_outbound_cmds', 'is_host_login', 'is_guest_login',
    'count', 'srv_count', 'serror_rate', 'srv_serror_rate', 'rerror_rate',
    'srv_rerror_rate', 'same_srv_rate', 'diff_srv_rate', 'srv_diff_host_rate',
    'dst_host_count', 'dst_host_srv_count', 'dst_host_same_srv_rate',
    'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
    'dst_host_srv_diff_host_rate', 'dst_host_serror_rate',
    'dst_host_srv_serror_rate', 'dst_host_rerror_rate', 'dst_host_srv_rerror_rate'
]


def _download_file(url: str, filepath: str) -> bool:
    """Download a file from URL to local path."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        # Create SSL context that doesn't verify (for corporate/local networks)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        print(f"Downloading {url}...")
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            data = response.read()
        with open(filepath, 'wb') as f:
            f.write(data)
        print(f"Saved to {filepath}")
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False


def _load_kdd_file(filepath: str) -> pd.DataFrame:
    """Load a KDD-format file into a DataFrame."""
    df = pd.read_csv(filepath, names=COLUMN_NAMES, header=None)
    # Map labels to categories
    df['attack_category'] = df['label'].map(
        lambda x: ATTACK_CATEGORY_MAP.get(x, 'Unknown')
    )
    # Binary label: 0 = normal, 1 = attack
    df['is_attack'] = (df['label'] != 'normal').astype(int)
    return df





# Cached data
_train_data = None
_test_data = None
_data_source = None


def load_nsl_kdd_train(force_reload: bool = False) -> pd.DataFrame:
    """
    Load NSL-KDD training data (125,973 records).
    Uses pickle cache for fast reload after first parse.
    """
    global _train_data, _data_source
    
    if _train_data is not None and not force_reload:
        return _train_data
    
    train_path = os.path.join(DATA_DIR, "KDDTrain+.txt")
    pickle_path = os.path.join(DATA_DIR, "KDDTrain+.pkl")
    
    # Try loading from pickle cache first (fastest)
    if os.path.exists(pickle_path) and not force_reload:
        try:
            _train_data = pd.read_pickle(pickle_path)
            _data_source = "NSL-KDD (cached)"
            return _train_data
        except Exception:
            pass
    
    # Try loading from CSV on disk
    if os.path.exists(train_path):
        try:
            _train_data = _load_kdd_file(train_path)
            _data_source = "NSL-KDD (downloaded)"
            # Save pickle cache for fast future loads
            try:
                _train_data.to_pickle(pickle_path)
            except Exception:
                pass
            return _train_data
        except Exception as e:
            print(f"Error loading cached file: {e}")
    
    # Try downloading
    if _download_file(TRAIN_URL, train_path):
        try:
            _train_data = _load_kdd_file(train_path)
            _data_source = "NSL-KDD (downloaded)"
            try:
                _train_data.to_pickle(pickle_path)
            except Exception:
                pass
            return _train_data
        except Exception as e:
            print(f"Error parsing downloaded file: {e}")
    
    raise RuntimeError(
        "NSL-KDD dataset not available. Please ensure data/KDDTrain+.txt exists "
        "or that you have internet access to download it."
    )


def load_nsl_kdd_test(force_reload: bool = False) -> pd.DataFrame:
    """
    Load NSL-KDD test data (22,544 records).
    Uses pickle cache for fast reload after first parse.
    """
    global _test_data
    
    if _test_data is not None and not force_reload:
        return _test_data
    
    test_path = os.path.join(DATA_DIR, "KDDTest+.txt")
    pickle_path = os.path.join(DATA_DIR, "KDDTest+.pkl")
    
    # Try loading from pickle cache first (fastest)
    if os.path.exists(pickle_path) and not force_reload:
        try:
            _test_data = pd.read_pickle(pickle_path)
            return _test_data
        except Exception:
            pass
    
    # Try loading from CSV on disk
    if os.path.exists(test_path):
        try:
            _test_data = _load_kdd_file(test_path)
            try:
                _test_data.to_pickle(pickle_path)
            except Exception:
                pass
            return _test_data
        except Exception as e:
            print(f"Error loading cached file: {e}")
    
    # Try downloading
    if _download_file(TEST_URL, test_path):
        try:
            _test_data = _load_kdd_file(test_path)
            try:
                _test_data.to_pickle(pickle_path)
            except Exception:
                pass
            return _test_data
        except Exception as e:
            print(f"Error parsing downloaded file: {e}")
    
    raise RuntimeError(
        "NSL-KDD test dataset not available. Please ensure data/KDDTest+.txt exists "
        "or that you have internet access to download it."
    )


def get_numeric_features(df: pd.DataFrame) -> np.ndarray:
    """Extract numeric features as numpy array for ML models."""
    available = [col for col in NUMERIC_FEATURES if col in df.columns]
    return df[available].values.astype(np.float64)


def get_binary_labels(df: pd.DataFrame) -> np.ndarray:
    """Get binary labels: 0 = normal, 1 = attack."""
    return df['is_attack'].values


def get_category_labels(df: pd.DataFrame) -> np.ndarray:
    """Get multi-class category labels."""
    return df['attack_category'].values


def get_data_source() -> str:
    """Return the source of the loaded data."""
    global _data_source
    return _data_source or "Not loaded"


def get_dataset_summary(df: pd.DataFrame) -> Dict:
    """Get summary statistics of the dataset."""
    total = len(df)
    normal = len(df[df['is_attack'] == 0])
    attack = len(df[df['is_attack'] == 1])
    
    categories = df['attack_category'].value_counts().to_dict()
    
    return {
        'total_records': total,
        'normal_count': normal,
        'attack_count': attack,
        'normal_pct': round(normal / total * 100, 1),
        'attack_pct': round(attack / total * 100, 1),
        'categories': categories,
        'num_features': len(NUMERIC_FEATURES),
        'data_source': get_data_source()
    }
