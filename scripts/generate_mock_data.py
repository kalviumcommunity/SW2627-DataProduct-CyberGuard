import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def generate_mock_logs(output_path, num_records=1000):
    """
    Generate realistic mock authentication logs with normal behavior and security threat anomalies.
    
    Threats simulated:
    1. Brute force attacks (many failed logins from the same IP/username).
    2. Impossible travel anomaly (same user logging in from different countries within 1 hour).
    3. Suspicious off-hours activity.
    """
    np.random.seed(42)
    
    # List of normal users and some special/sensitive targets
    users = [f"user_{i}" for i in range(1, 21)] + ["admin", "root", "db_backup"]
    countries = ["US", "US", "CA", "GB", "DE", "FR", "IN", "JP", "AU"]
    suspicious_countries = ["RU", "CN", "KP", "IR"]
    devices = ["Workstation-Windows", "Laptop-macOS", "Mobile-iOS", "Mobile-Android", "Server-Linux"]
    
    base_time = datetime.now() - timedelta(days=7)
    
    logs = []
    
    # Helper to generate a random IP
    def random_ip():
        return f"{np.random.randint(1, 255)}.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}"
    
    user_ips = {user: random_ip() for user in users}
    user_countries = {user: np.random.choice(countries) for user in users}
    
    # 1. Normal traffic (90% of logs)
    for i in range(int(num_records * 0.9)):
        user = np.random.choice(users)
        ip = user_ips[user]
        country = user_countries[user]
        device = np.random.choice(devices)
        
        # Random status (mostly Success for normal users)
        status = "Success" if np.random.random() > 0.08 else "Failed"
        
        # Distribute logs over the 7 days, mostly during standard hours (8 AM - 8 PM)
        day_offset = int(np.random.randint(0, 7))
        hour = int(np.random.choice(
            list(range(8, 20)) * 4 + list(range(0, 8)) + list(range(20, 24))
        ))
        minute = int(np.random.randint(0, 60))
        second = int(np.random.randint(0, 60))
        
        timestamp = base_time + timedelta(days=day_offset, hours=hour, minutes=minute, seconds=second)
        
        logs.append({
            "timestamp": timestamp.isoformat(),
            "username": user,
            "ip_address": ip,
            "country": country,
            "status": status,
            "device_type": device
        })
        
    # 2. Anomaly: Brute Force Attack
    # Attacker tries to guess the admin password from a single IP
    attacker_ip = "198.51.100.42"
    attack_time = base_time + timedelta(days=3, hours=14, minutes=10)
    for i in range(40):
        # 39 failed attempts, then 1 success (compromise)
        status = "Failed" if i < 39 else "Success"
        logs.append({
            "timestamp": (attack_time + timedelta(seconds=i * 5)).isoformat(),
            "username": "admin",
            "ip_address": attacker_ip,
            "country": "RU",
            "status": status,
            "device_type": "Workstation-Windows"
        })
        
    # 3. Anomaly: Impossible Travel
    # User_5 logs in from US, then 15 minutes later logs in from CN
    travel_time_1 = base_time + timedelta(days=4, hours=9, minutes=0)
    logs.append({
        "timestamp": travel_time_1.isoformat(),
        "username": "user_5",
        "ip_address": "192.0.2.1",
        "country": "US",
        "status": "Success",
        "device_type": "Laptop-macOS"
    })
    logs.append({
        "timestamp": (travel_time_1 + timedelta(minutes=15)).isoformat(),
        "username": "user_5",
        "ip_address": "203.0.113.88",
        "country": "CN",
        "status": "Success",
        "device_type": "Mobile-Android"
    })
    
    # 4. Anomaly: Off-hours sensitive account access
    # db_backup accessed at 3:15 AM
    off_hours_time = base_time + timedelta(days=2, hours=3, minutes=15)
    logs.append({
        "timestamp": off_hours_time.isoformat(),
        "username": "db_backup",
        "ip_address": "198.51.100.99",
        "country": "KP",
        "status": "Failed",
        "device_type": "Server-Linux"
    })
    logs.append({
        "timestamp": (off_hours_time + timedelta(minutes=1)).isoformat(),
        "username": "db_backup",
        "ip_address": "198.51.100.99",
        "country": "KP",
        "status": "Success",
        "device_type": "Server-Linux"
    })

    df = pd.DataFrame(logs)
    # Sort by timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by="timestamp").reset_index(drop=True)
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} logs at {output_path}")

if __name__ == "__main__":
    generate_mock_logs("data/raw/auth_logs.csv")
