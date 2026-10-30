#!/usr/bin/env python3
"""Exercise installed capabilities; native Snowflake remains a separate acceptance gate."""

import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import uuid

from contracts import ROOT, schema_for, validate


def contract(version):
    return {'apiVersion': 'v' + version, 'kind': 'DataContract', 'id': 'datacon-toolchain',
            'version': '1.0.0', 'status': 'active', 'name': 'Datacon toolchain fixture',
            'schema': [{'name': 'sample', 'logicalType': 'object', 'physicalType': 'table',
                        'properties': [{'name': 'id', 'logicalType': 'integer', 'physicalType': 'INTEGER',
                                        'required': True, 'unique': True},
                                       {'name': 'amount', 'logicalType': 'integer', 'physicalType': 'INTEGER'}]}]}


def offline_checks():
    import great_expectations as gx
    import yaml
    from sqlalchemy import create_engine, literal, select

    results = {}
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        for version in ('3.1.0', '3.2.0'):
            document = contract(version)
            assert validate(document)['valid']
            for suffix, data in (('json', json.dumps(document)), ('yaml', yaml.safe_dump(document))):
                path = directory / ('contract.' + suffix)
                path.write_text(data)
                result = subprocess.run([sys.executable, str(Path(__file__).with_name('contracts.py')), str(path)],
                                        capture_output=True, text=True, timeout=30)
                assert result.returncode == 0, 'Valid offline contract rejected'
                results[version + '-' + suffix] = True
            invalid = dict(document, kind='deliberately-invalid')
            assert not validate(invalid)['valid'], 'Invalid contract was accepted'
        path = directory / 'export.odcs.yaml'
        path.write_text(yaml.safe_dump(contract('3.1.0')))
        outputs = []
        for _ in range(2):
            result = subprocess.run(['datacontract', 'export', 'great-expectations', str(path), '--schema-name', 'sample'],
                                    capture_output=True, text=True, timeout=60)
            assert result.returncode == 0, 'Data Contract CLI export failed'
            outputs.append(json.loads(result.stdout))
        assert outputs[0] == outputs[1], 'GX export is not deterministic'
        suite = gx.ExpectationSuite(**outputs[0])
        assert suite.expectations, 'GX could not load exported expectations'
        results['gx_export_expectations'] = len(suite.expectations)
        # A corrupted vendored schema must fail before any validation occurs.
        schema_root = directory / 'tampered'
        (schema_root / 'platform/schemas').mkdir(parents=True)
        (schema_root / 'platform/schemas.json').write_bytes((ROOT / 'platform/schemas.json').read_bytes())
        (schema_root / 'platform/schemas/odcs-3.1.0.json').write_text('{}')
        try:
            schema_for('v3.1.0', schema_root)
        except ValueError as error:
            assert str(error) == 'ODCS schema integrity mismatch'
        else:
            raise AssertionError('Tampered schema was accepted')
        results['tampered_schema_rejected'] = True
        try:
            validate(dict(contract('3.1.0'), apiVersion='v99.0.0'))
        except ValueError:
            results['unsupported_version_rejected'] = True
        else:
            raise AssertionError('Unsupported schema version was accepted')
    # Loads the real connector and dialect, without opening a cloud connection.
    import snowflake.connector
    engine = create_engine('snowflake://user@account/database/schema?warehouse=qualification')
    assert 'SELECT' in str(select(literal(1)).compile(dialect=engine.dialect))
    engine.dispose()
    results['snowflake_connector_and_dialect'] = 'loaded; SQL compiled; native execution NOT_EXECUTED'
    return results


def database_checks():
    import great_expectations as gx
    import great_expectations.expectations as gxe
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import URL

    password = Path('/run/secrets/developer_password').read_text().strip()
    url = URL.create('postgresql+psycopg2', username=os.environ['PGUSER'], password=password,
                     host=os.environ['PGHOST'], port=int(os.environ['PGPORT']), database=os.environ['PGDATABASE'],
                     query={'connect_timeout': '10', 'options': '-c statement_timeout=30000'})
    engine = create_engine(url)
    table = 'toolchain_' + uuid.uuid4().hex
    qualified = 'workspace.' + table
    try:
        with engine.begin() as connection:
            assert not connection.execute(text('SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname=current_user')).scalar_one()
            connection.execute(text(f'CREATE TABLE {qualified} (id integer, amount integer)'))
            connection.execute(text(f'INSERT INTO {qualified} VALUES (1, 5), (2, 7)'))
        context = gx.get_context(mode='ephemeral')
        source = context.data_sources.add_postgres(name='qualification', connection_string=url.render_as_string(hide_password=False))
        asset = source.add_table_asset(name='sample', table_name=qualified)
        definition = asset.add_batch_definition_whole_table('all-rows')
        expectation = gxe.ExpectColumnValuesToBeBetween(column='amount', min_value=0, max_value=10)
        good = definition.get_batch().validate(expectation)
        assert good.success, 'GX rejected the valid SQL fixture'
        with engine.connect() as connection:
            transaction = connection.begin()
            connection.execute(text(f'INSERT INTO {qualified} VALUES (3, 9)'))
            transaction.rollback()
            assert connection.execute(text(f'SELECT count(*) FROM {qualified}')).scalar_one() == 2
        with engine.begin() as connection:
            connection.execute(text(f'INSERT INTO {qualified} VALUES (3, -1)'))
        bad = definition.get_batch().validate(expectation)
        assert not bad.success, 'GX accepted the deliberately invalid SQL fixture'
        return {'postgresql_sqlalchemy': True, 'rollback': True, 'gx_pass': True, 'gx_expected_failure': True}
    finally:
        with engine.begin() as connection:
            connection.execute(text(f'DROP TABLE IF EXISTS {qualified}'))
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    report = {'passed': False, 'timestamp': datetime.now(timezone.utc).isoformat(timespec='seconds'),
              'python': platform.python_version(), 'architecture': platform.machine(), 'uid': os.getuid(),
              'packages': {name: importlib.metadata.version(name) for name in (
                  'great-expectations', 'SQLAlchemy', 'psycopg2-binary', 'snowflake-connector-python',
                  'snowflake-sqlalchemy', 'datacontract-cli', 'PyYAML')}}
    try:
        assert report['python'] == '3.14.8' and report['uid'] != 0
        report['offline'] = offline_checks()
        if not args.offline:
            report['database'] = database_checks()
        report['passed'] = True
    except Exception as error:
        # SQL/GX exceptions may include URLs: never print raw exception messages.
        report['error_type'] = type(error).__name__
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
