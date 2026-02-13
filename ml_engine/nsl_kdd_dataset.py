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
        # Create SSL context that doesn't verify (for corporate networks)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        print(f"Downloading {url}...")
        urllib.request.urlretrieve(url, filepath)
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


def _generate_synthetic_kdd(n_samples: int = 5000, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic data matching NSL-KDD feature distributions.
    Used as fallback when download fails.
    """
    np.random.seed(seed)
    
    categories = {
        'normal': {'ratio': 0.53, 'duration': (50, 200), 'src_bytes': (200, 1000), 
                   'dst_bytes': (200, 800), 'count': (5, 30), 'srv_count': (5, 25),
                   'serror_rate': (0.0, 0.1), 'dst_host_count': (50, 255)},
        'DoS':    {'ratio': 0.28, 'duration': (0, 5), 'src_bytes': (0, 100),
                   'dst_bytes': (0, 50), 'count': (100, 511), 'srv_count': (100, 511),
                   'serror_rate': (0.8, 1.0), 'dst_host_count': (200, 255)},
        'Probe':  {'ratio': 0.09, 'duration': (0, 10), 'src_bytes': (0, 300),
                   'dst_bytes': (0, 200), 'count': (1, 50), 'srv_count': (1, 20),
                   'serror_rate': (0.0, 0.5), 'dst_host_count': (1, 100)},
        'R2L':    {'ratio': 0.07, 'duration': (100, 5000), 'src_bytes': (100, 5000),
                   'dst_bytes': (100, 3000), 'count': (1, 10), 'srv_count': (1, 5),
                   'serror_rate': (0.0, 0.2), 'dst_host_count': (1, 50)},
        'U2R':    {'ratio': 0.03, 'duration': (10, 500), 'src_bytes': (50, 2000),
                   'dst_bytes': (0, 500), 'count': (1, 5), 'srv_count': (1, 3),
                   'serror_rate': (0.0, 0.1), 'dst_host_count': (1, 30)},
    }
    
    rows = []
    for cat, params in categories.items():
        n = int(n_samples * params['ratio'])
        for _ in range(n):
            row = {}
            row['duration'] = np.random.uniform(*params['duration'])
            row['src_bytes'] = np.random.uniform(*params['src_bytes'])
            row['dst_bytes'] = np.random.uniform(*params['dst_bytes'])
            row['land'] = 1 if cat == 'DoS' and np.random.random() < 0.02 else 0
            row['wrong_fragment'] = np.random.randint(0, 3) if cat != 'normal' else 0
            row['urgent'] = 0
            row['hot'] = np.random.randint(0, 5) if cat in ['R2L', 'U2R'] else 0
            row['num_failed_logins'] = np.random.randint(0, 5) if cat == 'R2L' else 0
            row['logged_in'] = 1 if cat in ['normal', 'U2R'] else np.random.choice([0, 1])
            row['num_compromised'] = np.random.randint(0, 10) if cat == 'U2R' else 0
            row['root_shell'] = 1 if cat == 'U2R' and np.random.random() < 0.3 else 0
            row['su_attempted'] = 1 if cat == 'U2R' and np.random.random() < 0.2 else 0
            row['num_root'] = np.random.randint(0, 10) if cat == 'U2R' else 0
            row['num_file_creations'] = np.random.randint(0, 5) if cat in ['U2R', 'R2L'] else 0
            row['num_shells'] = np.random.randint(0, 2) if cat == 'U2R' else 0
            row['num_access_files'] = np.random.randint(0, 3) if cat in ['U2R', 'R2L'] else 0
            row['num_outbound_cmds'] = 0
            row['is_host_login'] = 0
            row['is_guest_login'] = 1 if cat == 'R2L' and np.random.random() < 0.1 else 0
            row['count'] = np.random.uniform(*params['count'])
            row['srv_count'] = np.random.uniform(*params['srv_count'])
            row['serror_rate'] = np.random.uniform(*params['serror_rate'])
            row['srv_serror_rate'] = row['serror_rate'] * np.random.uniform(0.8, 1.0)
            row['rerror_rate'] = np.random.uniform(0, 0.3) if cat == 'Probe' else np.random.uniform(0, 0.05)
            row['srv_rerror_rate'] = row['rerror_rate'] * np.random.uniform(0.8, 1.0)
            row['same_srv_rate'] = np.random.uniform(0.8, 1.0) if cat in ['normal', 'DoS'] else np.random.uniform(0.0, 0.5)
            row['diff_srv_rate'] = 1.0 - row['same_srv_rate'] + np.random.uniform(-0.05, 0.05)
            row['srv_diff_host_rate'] = np.random.uniform(0, 0.3)
            row['dst_host_count'] = np.random.uniform(*params['dst_host_count'])
            row['dst_host_srv_count'] = np.random.uniform(1, row['dst_host_count'] + 1)
            row['dst_host_same_srv_rate'] = np.random.uniform(0.5, 1.0)
            row['dst_host_diff_srv_rate'] = 1.0 - row['dst_host_same_srv_rate']
            row['dst_host_same_src_port_rate'] = np.random.uniform(0, 0.5)
            row['dst_host_srv_diff_host_rate'] = np.random.uniform(0, 0.3)
            row['dst_host_serror_rate'] = row['serror_rate'] * np.random.uniform(0.8, 1.2)
            row['dst_host_srv_serror_rate'] = row['dst_host_serror_rate']
            row['dst_host_rerror_rate'] = row['rerror_rate']
            row['dst_host_srv_rerror_rate'] = row['rerror_rate']
            
            row['label'] = cat if cat == 'normal' else np.random.choice({
                'DoS': ['neptune', 'smurf', 'back', 'teardrop', 'pod'],
                'Probe': ['satan', 'ipsweep', 'portsweep', 'nmap'],
                'R2L': ['warezclient', 'guess_passwd', 'ftp_write'],
                'U2R': ['buffer_overflow', 'rootkit', 'perl']
            }[cat])
            row['difficulty'] = np.random.randint(1, 21)
            row['attack_category'] = cat
            row['is_attack'] = 0 if cat == 'normal' else 1
            
            # Protocol and service (categorical)
            row['protocol_type'] = np.random.choice(['tcp', 'udp', 'icmp'], p=[0.7, 0.2, 0.1])
            row['service'] = np.random.choice(['http', 'smtp', 'ftp', 'ssh', 'dns', 'telnet', 'other'])
            row['flag'] = np.random.choice(['SF', 'S0', 'REJ', 'RSTR', 'SH', 'RSTO'])
            
            rows.append(row)
    
    df = pd.DataFrame(rows)
    # Shuffle
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    return df


# Cached data
_train_data = None
_test_data = None
_data_source = None


def load_nsl_kdd_train(force_reload: bool = False) -> pd.DataFrame:
    """
    Load NSL-KDD training data.
    Tries to download real data first, falls back to synthetic.
    """
    global _train_data, _data_source
    
    if _train_data is not None and not force_reload:
        return _train_data
    
    train_path = os.path.join(DATA_DIR, "KDDTrain+.txt")
    
    # Try loading from disk first
    if os.path.exists(train_path):
        try:
            _train_data = _load_kdd_file(train_path)
            _data_source = "NSL-KDD (downloaded)"
            print(f"Loaded {len(_train_data)} training records from disk")
            return _train_data
        except Exception as e:
            print(f"Error loading cached file: {e}")
    
    # Try downloading
    if _download_file(TRAIN_URL, train_path):
        try:
            _train_data = _load_kdd_file(train_path)
            _data_source = "NSL-KDD (downloaded)"
            print(f"Downloaded and loaded {len(_train_data)} training records")
            return _train_data
        except Exception as e:
            print(f"Error parsing downloaded file: {e}")
    
    # Fallback to synthetic data
    print("Using synthetic NSL-KDD-like data (download unavailable)")
    _train_data = _generate_synthetic_kdd(n_samples=10000, seed=42)
    _data_source = "Synthetic (NSL-KDD distributions)"
    return _train_data


def load_nsl_kdd_test(force_reload: bool = False) -> pd.DataFrame:
    """
    Load NSL-KDD test data.
    Tries to download real data first, falls back to synthetic.
    """
    global _test_data
    
    if _test_data is not None and not force_reload:
        return _test_data
    
    test_path = os.path.join(DATA_DIR, "KDDTest+.txt")
    
    if os.path.exists(test_path):
        try:
            _test_data = _load_kdd_file(test_path)
            print(f"Loaded {len(_test_data)} test records from disk")
            return _test_data
        except Exception as e:
            print(f"Error loading cached file: {e}")
    
    if _download_file(TEST_URL, test_path):
        try:
            _test_data = _load_kdd_file(test_path)
            print(f"Downloaded and loaded {len(_test_data)} test records")
            return _test_data
        except Exception as e:
            print(f"Error parsing downloaded file: {e}")
    
    # Fallback to synthetic
    _test_data = _generate_synthetic_kdd(n_samples=2000, seed=99)
    return _test_data


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
