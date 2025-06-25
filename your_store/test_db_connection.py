import pyodbc

try:
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=tcp:sql2k2201.discountasp.net;'
        'DATABASE=SQL2022_96222_tba;'
        'UID=SQL2022_96222_tba_user;'
        'PWD=Alfred47114711$;'
        'TrustServerCertificate=yes;'
    )
    cursor = conn.cursor()
    cursor.execute('SELECT TOP 1 * FROM dbo.addresses')
    row = cursor.fetchone()
    if row:
        print("✅ Connection succeeded! Sample row:")
        print(row)
    else:
        print("✅ Connected, but no rows found in dbo.addresses.")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
