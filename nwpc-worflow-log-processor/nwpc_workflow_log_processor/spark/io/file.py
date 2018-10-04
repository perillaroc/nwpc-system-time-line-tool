# coding: utf-8
import datetime

from nwpc_log_model import Record


def get_from_file(config, owner, repo, begin_date, end_date, log_file, spark):
    Record.prepare(owner, repo)

    log_data = spark.read.text(log_file).rdd

    # record line => record object
    def parse_sms_log(line):
        record = Record()
        record.parse(line.value)
        return record

    log_data = log_data.map(parse_sms_log)

    # record object => record object
    # 日期范围 [ begin_date - 1, end_date ]，这是日志条目收集的范围
    if begin_date is not None:
        start_date = begin_date - datetime.timedelta(days=1)

    def filter_node(record):
        if begin_date is not None:
            if record.record_date < start_date.date():
                return False

        if end_date is not None:
            if record.record_date >= end_date.date():
                return False

        return True

    record_rdd = log_data.filter(filter_node)

    Record.init()

    return record_rdd