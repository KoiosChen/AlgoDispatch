import psycopg2
import sys

try:

    con = psycopg2.connect(host=r'shatljq-pgsql03.tljq.cnsh.algospace.org',
                           user='hmd',
                           password='ihUG9a79jaR3Xs3!!zAV',
                           dbname='job_stats')

    cur = con.cursor()
    cur.execute("select * from hmd.job where job_status='Completed' and trading_day::DATE = current_date")

    version = cur.fetchall()
    for v in version:
        print(v)

except psycopg2.DatabaseError as e:

    print(f'Error {e}')
    sys.exit(1)

finally:
    if con:
        con.close()