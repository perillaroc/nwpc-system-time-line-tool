# coding=utf-8
import pathlib

import click
import yaml

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from nwpc_log_model.rdbms_model.models import Model
from nwpc_log_model.util.repo_util import RepoUtil

from nwpc_log_collector.smslog_local_collector import collect_log_from_local_file_by_range, load_config as load_collector_config


def load_config(config_file_path):
    f = open(config_file_path, 'r')
    config = yaml.load(f)
    f.close()
    return config


@click.group()
def cli():
    pass


@cli.command()
@click.option('-c', '--config', help='config file path')
@click.option('-o', '--owner', help='owner name')
@click.option('-r', '--repo', help='repo name')
def setup(config, owner, repo):
    config = load_config(config)
    engine = create_engine(config['system_time_line']['rdbms']['database_uri'])
    Session = sessionmaker(bind=engine)
    session = Session()
    Model.metadata.create_all(engine)

    RepoUtil.create_owner(owner, session)
    RepoUtil.create_sms_repo(owner, repo, session)
    RepoUtil.create_record_table(owner, repo, session)


@cli.command()
@click.option('-c', '--config', help='config file path')
@click.option('-o', '--owner', help='owner name')
@click.option('-r', '--repo', help='repo name')
def teardown(config, owner, repo):
    config = load_config(config)
    engine = create_engine(config['system_time_line']['rdbms']['database_uri'])
    Session = sessionmaker(bind=engine)
    session = Session()
    Model.metadata.drop_all(engine)


@cli.command()
@click.option('-c', '--config', help='config file path')
@click.option('-o', '--owner', help='owner name')
@click.option('-r', '--repo', help='repo name')
@click.option('-l', '--log-file', help='log file path')
@click.option('--begin-date', help='begin date, [start_date, end_date), YYYY-MM-dd')
@click.option('--end-date', help='end date, [start_date, end_date), YYYY-MM-dd')
def load(config, owner, repo, log_file, begin_date, end_date):
    config_object = load_config(config)
    config_file_path = config_object['system_time_line']['smslog_local_collector']['config']
    if config_file_path.startswith('.'):
        config_file_path = pathlib.Path(pathlib.Path(config).parent, config_file_path)
    collector_config = load_collector_config(str(config_file_path))
    collect_log_from_local_file_by_range(collector_config, owner, repo, log_file, begin_date, end_date)


@cli.command()
@click.option('-c', '--config', help='config file path')
@click.option('-o', '--owner', help='owner name')
@click.option('-r', '--repo', help='repo name')
@click.option('--begin-date', help='begin date, [start_date, end_date), YYYY-MM-dd')
@click.option('--end-date', help='end date, [start_date, end_date), YYYY-MM-dd')
def process(config, owner, repo, begin_date, end_date):
    pass


if __name__ == "__main__":
    cli()
