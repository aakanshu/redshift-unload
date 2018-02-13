'''
Created on May 11, 2017

@author: Devin
'''

import json
import os
import argparse
import psycopg2


def _simple_sanitize(s):
    return s.split(';')[0]


def run(config, tablename, file_path, schema_name=None, sql_file=None, range_col=None, range_start=None, range_end=None):
    if not file_path:
        file_path = tablename
    conn = psycopg2.connect(**config['db'])
    unload_options = '\n'.join(config.get('unload_options', []))
    cursor = conn.cursor()

    schema_clause = ''
    if schema_name:
        schema_clause = "AND table_schema = '{}'".format(schema_name)

    query = """SELECT column_name, data_type \
        FROM information_schema.columns \
        WHERE table_name = '{}' {} \
        ORDER BY ordinal_position \
    """.format(tablename, schema_clause)

    cursor.execute(query)
    res = cursor.fetchall()

    cast_columns = []
    columns = [x[0] for x in res]
    for col in res:
        # Boolean is a special case; cannot be casted to text so it needs to be handled differently
        if 'boolean' in col[1]:
            cast_columns.append(
                r"CASE {} WHEN 1 THEN \'true\' ELSE \'false\'::text END".format(col[0])
            )
        else:
            cast_columns.append("{}::text".format(col[0]))

    header_str = ''
    for i in columns:
        header_str += "\\\'" + i + "\\\' as " + i.split(':')[0] + ', '
    header_str = header_str.rstrip().rstrip(',')
    column_str = ", ".join(columns)
    cast_columns_str = ", ".join(cast_columns)

    cursor = conn.cursor()
    where_clause = ""
    if range_col and range_start and range_end:
        where_clause = cursor.mogrify(r"WHERE {} BETWEEN \'{}\' AND \'{}\'".format(range_col, range_start, range_end,))
    elif sql_file:
        where_clause = sql_file
    query_tmpl = """
    UNLOAD ('SELECT {0} FROM (
        SELECT 1 as rn, {1}
        UNION ALL
        (
            SELECT 2 as rn, {2}
            FROM {3}{4} {5}
        )
    ) ORDER BY rn')
    TO '{8}'
    CREDENTIALS 'aws_access_key_id={6};aws_secret_access_key={7}'
    {9}
    """

    query = query_tmpl.format(
        column_str,
        header_str,
        cast_columns_str,
        '{}.'.format(schema_name) if schema_name else '',
        tablename,
        where_clause,
        config['aws_access_key_id'],
        config['aws_secret_access_key'],
        file_path,
        unload_options
    )
    print "The following UNLOAD query is being run: \n" + query
    cursor.execute(query)
    print 'Completed write to {}'.format(file_path)


def update_config_from_env(config, env):
    for key in config.get('db'):
        env_val = os.environ.get('DB_{}'.format(key.upper()))
        if env_val is not None:
            config['db'][key] = env_val

    for key in ('aws_access_key_id', 'aws_secret_access_key'):
        env_val = os.environ.get(key)
        if env_val is not None:
            config[key] = env_val

    return config


def main():
    config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')
    with open(config_path, 'r') as f:
        config = json.loads(f.read())

    config = update_config_from_env(config, os.environ)

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', help='Table name', dest='tablename')
    parser.add_argument('-c', help='Schema name', dest='schema_name', default=None)
    parser.add_argument('-f', help='Desired S3 file path', dest='file_path')
    parser.add_argument('-s', help='SQL WHERE clause', dest='sql_file', default=None)
    parser.add_argument('-r', help='Range column', dest='range_col', default=None)
    parser.add_argument('-r1', help='Range start', dest='range_start', default=None)
    parser.add_argument('-r2', help='Range end', dest='range_end', default=None)
    raw_args = parser.parse_args()
    if 's' in vars(raw_args) and raw_args.s:
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), raw_args.s), 'r') as f:
            raw_args.s = f.read()
    args = {}
    for k, v in vars(raw_args).items():
        if v:
            args[k] = _simple_sanitize(v)
        else:
            args[k] = None
    run(config, **args)


if __name__ == '__main__':
    main()
