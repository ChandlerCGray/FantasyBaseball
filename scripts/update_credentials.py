#!/usr/bin/env python3
"""
Helper script to update ESPN credentials in .env file
"""
import os
import re

def update_env_file(swid, espn_s2):
    """Update the .env file with new ESPN credentials"""
    
    # Read current .env file
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            content = f.read()
    else:
        print("❌ .env file not found!")
        return False
    
    # Update SWID
    content = re.sub(r'SWID=.*', f'SWID={swid}', content)
    
    # Update ESPN_S2
    content = re.sub(r'ESPN_S2=.*', f'ESPN_S2={espn_s2}', content)
    
    # Write back to .env file
    with open('.env', 'w') as f:
        f.write(content)
    
    print("✅ .env file updated successfully!")
    return True

if __name__ == "__main__":
    print("ESPN Credentials Updater")
    print("=" * 40)
    print()
    print("To get fresh ESPN cookies:")
    print("1. Go to https://www.espn.com/fantasy/baseball/")
    print("2. Log into your account")
    print("3. Navigate to your league")
    print("4. Open Developer Tools (F12)")
    print("5. Go to Application → Cookies → espn.com")
    print("6. Copy the SWID and espn_s2 values")
    print()
    
    swid = input("Enter your SWID cookie value: ").strip()
    espn_s2 = input("Enter your espn_s2 cookie value: ").strip()
    
    if swid and espn_s2:
        if update_env_file(swid, espn_s2):
            print()
            print("🎉 Credentials updated! You can now:")
            print("1. Go to your Fantasy Baseball app")
            print("2. Click 'Update Data' in the sidebar")
            print("3. Your real league data should load!")
    else:
        print("❌ Please provide both SWID and espn_s2 values") 