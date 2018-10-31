# coding: utf-8
from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, Time, Text


class EcflowRecord(object):
    repo_id = Column(Integer, primary_key=True)
    version_id = Column(Integer, primary_key=True)
    line_no = Column(Integer, primary_key=True)
    log_type = Column(String(10))
    date = Column(Date())
    time = Column(Time())
    command_type = Column(String(10))
    command = Column(String(100))
    node_path = Column(String(200))
    additional_information = Column(Text())
    log_record = Column(Text())

    @classmethod
    def parse(cls, line):
        record = EcflowRecord()
        record.log_record = line

        start_pos = 0
        end_pos = line.find(':')
        record.log_type = line[start_pos:end_pos]

        start_pos = end_pos + 2
        end_pos = line.find(']', start_pos)
        if end_pos == -1:
            print("can't find date and time => ", line)
            return
        record_time_string = line[start_pos:end_pos]
        date_time = datetime.strptime(record_time_string, '%H:%M:%S %d.%m.%Y')
        record.date = date_time.date()
        record.time = date_time.time()

        start_pos = end_pos + 2
        if line[start_pos: start_pos+1] == " ":
            record.command_type = "status"
            start_pos += 1
            record.parse_status_record(line[start_pos:])
        elif line[start_pos: start_pos+2] == "--":
            record.command_type = "client"
            start_pos += 2
            record.parse_client_record(line[start_pos:])
        elif line[start_pos: start_pos+4] == "chd:":
            # child
            record.command_type = "child"
            start_pos += 4
            record.parse_child_record(line[start_pos:])
        elif line[start_pos: start_pos+4] == "svr:":
            # server
            # print("[server command]", line)
            record.command_type = "server"
        else:
            # not supported
            print("[not supported]", line)

        return record

    def parse_status_record(self, status_line):
        """
        active: /swfdp/00/deterministic/base/024/SWFDP_CA/CIN_SWFDP_CA_sep_024
        """
        start_pos = 0
        end_pos = status_line.find(":", start_pos)
        if end_pos == -1:
            print("[ERROR] status record: command not found =>", self.log_record)
            return
        command = status_line[start_pos:end_pos]

        if command in ('submitted', 'active', 'queued', 'complete', 'aborted'):
            self.command = command
            start_pos = end_pos + 2
            end_pos = status_line.find(' ', start_pos)
            if end_pos == -1:
                # LOG:[23:12:00 9.10.2018] queued: /grapes_meso_3km_post/18/tograph/1h/prep_1h_10mw
                self.node_path = status_line[start_pos:].strip()
            else:
                # LOG:[11:09:31 20.9.2018]  aborted: /grapes_meso_3km_post/06/tograph/3h/prep_3h_10mw/plot_hour_030 try-no: 1 reason: trap
                self.node_path = status_line[start_pos:end_pos]
                self.additional_information = status_line[end_pos+1:]
        else:
            if command in ('unknown', ):
                # just ignore
                pass
            elif ' ' in command:
                print("[ERROR] status record: is not a valid command =>", self.log_record)
            else:
                self.command = command
                print("[ERROR] status record: command not supported =>", self.log_record)

    def parse_child_record(self, child_line):
        start_pos = 0
        end_pos = child_line.find(" ", start_pos)
        if end_pos == -1:
            print("[ERROR] child record: command not found =>", self.log_record)
            return
        command = child_line[start_pos:end_pos]

        if command in ('init', 'complete', 'abort'):
            self.command = command
            start_pos = end_pos + 2
            end_pos = child_line.find(' ', start_pos)
            if end_pos == -1:
                # MSG:[08:17:04 29.6.2018] chd:complete /gmf_grapes_025L60_v2.2_post/18/typhoon/post/tc_post
                self.node_path = child_line[start_pos:].strip()
            else:
                # MSG:[12:22:53 19.10.2018] chd:abort /3km_post/06/3km_togrib2/grib2WORK/030/after_data2grib2_030  trap
                self.node_path = child_line[start_pos:end_pos]
                self.additional_information = child_line[end_pos + 1:]
        elif command in ('meter', 'label', 'event'):
            self.command = command
            # MSG:[09:24:06 29.6.2018] chd:event transmissiondone /gmf_grapes_025L60_v2.2_post/00/tograph/base/015/AN_AEA/QFLXDIV_P700_AN_AEA_sep_015
            self.command = command
            start_pos = end_pos + 1
            line = child_line[start_pos:]
            node_path_start_pos = line.rfind(' ')
            if node_path_start_pos != -1:
                self.node_path = line[node_path_start_pos+1:]
                self.additional_information = line[:node_path_start_pos]
            else:
                print("[ERROR] child record: parse error =>", self.log_record)
        else:
            self.command = command
            print("[ERROR] child record: command not supported =>", self.log_record)

    def parse_client_record(self, child_line):
        start_pos = 0
        end_pos = child_line.find(" ", start_pos)
        if end_pos == -1:
            print("[ERROR] client record: command not found =>", self.log_record)
            return
        command = child_line[start_pos:end_pos]

        if command == 'requeue':
            self.command = command
            start_pos = end_pos + 1
            tokens = child_line[start_pos:].split()
            if len(tokens) == 3:
                requeue_option = tokens[0]
                node_path = tokens[1]
                user = tokens[2]
                self.node_path = node_path
                self.additional_information = requeue_option + ' ' + user
            else:
                print("[ERROR] client record: requeue parse error =>", self.log_record)
                return
        elif command in ('alter', 'free-dep', 'kill', 'delete', 'suspend', 'resume', 'run', 'status'):
            self.command = command
            start_pos = end_pos + 1
            tokens = child_line[start_pos:].split()
            user = tokens[-1]
            node_path = tokens[-2]
            self.node_path = node_path
            self.additional_information = ' '.join(tokens[:-2]) + ' ' + user
        elif command.startswith('force='):
            self.command = 'force'
            start_pos = end_pos + 1
            tokens = child_line[start_pos:].split()
            node_path = tokens[-2]
            user = tokens[-1]
            self.node_path = node_path
            self.additional_information = ' '.join(tokens[-2:]) + ' ' + user
        elif command.startswith('file='):
            self.command = 'file'
            node_path = command[5:]
            self.node_path = node_path
            start_pos = end_pos + 1
            self.additional_information = child_line[start_pos:]
        elif command.startswith('load='):
            self.command = 'load'
            node_path = command[5:]
            self.node_path = node_path
            start_pos = end_pos + 1
            self.additional_information = child_line[start_pos:]
        elif command.startswith('begin='):
            self.command = 'begin'
            node_path = command[6:]
            self.node_path = node_path
            start_pos = end_pos + 1
            self.additional_information = child_line[start_pos:]
        elif command.startswith('replace='):
            self.command = 'replace'
            node_path = command[5:]
            self.node_path = node_path
            start_pos = end_pos + 1
            self.additional_information = child_line[start_pos:]
        elif command.startswith('order='):
            self.command = 'order'
            node_path = command[6:]
            self.node_path = node_path
            start_pos = end_pos + 1
            self.additional_information = child_line[start_pos:]
        elif command in ('restart', 'suites', 'stats', 'edit_history',
                         'zombie_get', 'server_version', 'ping', 'check_pt'):
            self.command = command
        elif command.startswith('sync_full=') or \
                command.startswith('news=') or \
                command.startswith('sync=') or \
                command.startswith('edit_script=') or \
                command.startswith('zombie_fail=') or \
                command.startswith('zombie_kill=') or \
                command.startswith('zombie_fob=') or \
                command.startswith('zombie_adopt=') or \
                command.startswith('zombie_remove=') or \
                command.startswith('log=') or \
                command.startswith('halt=') or \
                command.startswith('terminate=') or \
                command.startswith('order=') or \
                command.startswith('ch_register=') or \
                command.startswith('ch_drop='):
            self.command = command[:command.find('=')]
        else:
            self.command = command
            print("[ERROR] client record: command not supported =>", self.log_record)