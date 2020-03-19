import typing
import datetime

from loguru import logger
import pandas as pd

from nwpc_workflow_log_model.log_record.ecflow import StatusLogRecord
from nwpc_workflow_log_model.log_record.ecflow.status_record import StatusChangeEntry

from nwpc_workflow_log_tool.util import generate_in_date_range
from .situation_record import SituationRecord


class SituationCalculator(object):
    def __init__(
            self,
            dfa_engine,
            stop_states: typing.Tuple,
            dfa_kwargs: dict = None,
    ):
        self._dfa_engine = dfa_engine
        self._stop_states = stop_states
        self._dfa_kwargs = dfa_kwargs
        if self._dfa_kwargs is None:
            self._dfa_kwargs = dict()

    def get_situations(
            self,
            records: typing.List,
            node_path: str,
            start_date: datetime.datetime,
            end_date: datetime.datetime,
    ) -> typing.List[SituationRecord]:
        logger.info("Finding StatusLogRecord for {}", node_path)
        record_list = []
        for record in records:
            if record.node_path == node_path and isinstance(record, StatusLogRecord):
                record_list.append(record)

        logger.info("Calculating node status change using DFA...")
        situations = []
        for current_date in pd.date_range(start=start_date, end=end_date, closed="left"):
            filter_function = generate_in_date_range(current_date, current_date + pd.Timedelta(days=1))
            current_records = list(filter(lambda x: filter_function(x), record_list))

            status_changes = [StatusChangeEntry(r) for r in current_records]

            dfa = self._dfa_engine(
                name=current_date,
                **self._dfa_kwargs,
            )

            for s in status_changes:
                dfa.trigger(
                    s.status.value,
                    node_data=s,
                )
                if dfa.state in self._stop_states:
                    break

            situations.append(SituationRecord(
                date=current_date,
                state=dfa.state,
                node_situation=dfa.node_situation,
                records=current_records,
            ))

        logger.info("Calculating node status change using DFA...Done")
        return situations
