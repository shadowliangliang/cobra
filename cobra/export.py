# -*- coding: utf-8 -*-

"""
    export
    ~~~~~~~~~~~~~~~~~~~

    Export scan result to files or console

    :author:    40huo <git@40huo.cn>
    :homepage:  https://github.com/wufeifei/cobra
    :license:   MIT, see LICENSE for more details.
    :copyright: Copyright (c) 2017 Feei. All rights reserved
"""
import json
import re
import os
import csv
from codecs import open
from prettytable import PrettyTable
from .log import logger
from .config import running_path
from jinja2 import Template

try:
    import cgi as html
except ImportError:
    import html

try:
    # Python 2
    _unicode = unicode
except NameError:
    # Python 3
    _unicode = str


def dict_to_xml(dict_obj, line_padding=""):
    """
    Convert scan result to XML string.
    :param dict_obj:a dict object
    :param line_padding:
    :return: XML String
    """
    result_list = []

    if isinstance(dict_obj, list):
        for list_id, sub_elem in enumerate(dict_obj):
            result_list.append(" " * 4 + "<vulnerability>")
            result_list.append(dict_to_xml(sub_elem, line_padding))
            result_list.append(" " * 4 + "</vulnerability>")

        return "\n".join(result_list)

    if isinstance(dict_obj, dict):
        for tag_name in dict_obj:
            sub_obj = dict_obj[tag_name]
            if isinstance(sub_obj, _unicode):
                sub_obj = html.escape(sub_obj)
            result_list.append("%s<%s>" % (line_padding, tag_name))
            result_list.append(dict_to_xml(sub_obj, " " * 4 + line_padding))
            result_list.append("%s</%s>" % (line_padding, tag_name))

        return "\n".join(result_list)

    return "%s%s" % (line_padding, dict_obj)


def dict_to_json(dict_obj):
    """
    Convert scan result to JSON string.
    :param dict_obj: a dict object
    :return: JSON String
    """
    return json.dumps(dict_obj, indent=4, sort_keys=True, ensure_ascii=False)


def dict_to_csv(vul_list, filename):
    """
    Write scan result to file.
    :param vul_list:a list which contains dicts
    :param filename:
    :return:
    """
    # 将 target 调整到第一列
    header = vul_list[0].keys()
    header.remove("target")
    header.insert(0, "target")

    if not os.path.exists(filename):
        with open(filename, "w", encoding='utf-8') as f:
            csv_writer = csv.DictWriter(f, header)
            csv_writer.writeheader()
            csv_writer.writerows(vul_list)
    else:
        with open(filename, "a", encoding='utf-8') as f:
            csv_writer = csv.DictWriter(f, header)
            csv_writer.writerows(vul_list)


def dict_to_pretty_table(vul_list):
    """
    Pretty print vul_list in console.
    :param vul_list:
    :return: Pretty Table Format String
    """
    row_list = PrettyTable()
    row_list.field_names = ["ID", "Vulnerability", "Target", "Discover Time", "Author"]
    for vul in vul_list:
        row_list.add_row(
            [vul.get("id"), vul.get("rule_name"), vul.get("file_path") + ": " + str(vul.get("line_number")),
             vul.get("commit_time"), vul.get("commit_author")]
        )
    return row_list


def write_to_file(target, sid, output_format="", filename=""):
    """
    Export scan result to file.
    :param sid: scan sid
    :param output_format: output format
    :param filename: filename to save
    :return:
    """
    data_file = os.path.join(running_path, '{sid}_data'.format(sid=sid))
    with open(data_file, 'r') as f:
        scan_data = json.load(f)

    scan_data['target'] = target

    if output_format == "":
        logger.info("Vulnerabilities\n" + str(dict_to_pretty_table(scan_data.get('vulnerabilities'))))

    elif output_format == "json" or output_format == "JSON":
        if not os.path.exists(filename):
            with open(filename, "w") as f:
                f.write("""{"results":[\n""")
                f.write(dict_to_json(scan_data))
                f.write("\n]}")
        else:
            # 在倒数第二行插入
            with open(filename, "r") as f:
                results = f.readlines()
                results.insert(len(results) - 1, ",\n" + dict_to_json(scan_data) + "\n")
            with open(filename, "w") as f:
                f.writelines(results)

    elif output_format == "xml" or output_format == "XML":
        xml_obj = {
            "result": scan_data,
        }
        if not os.path.exists(filename):
            with open(filename, "w", encoding='utf-8') as f:
                f.write("""<?xml version="1.0" encoding="UTF-8"?>\n""")
                f.write("""<results>\n""")
                f.write(dict_to_xml(xml_obj))
                f.write("""\n</results>\n""")
        else:
            # 在倒数第二行插入
            with open(filename, "r", encoding='utf-8') as f:
                results = f.readlines()
                results.insert(len(results) - 1, "\n" + dict_to_xml(xml_obj) + "\n")
            with open(filename, "w", encoding='utf-8') as f:
                f.writelines(results)

    elif output_format == "csv" or output_format == "CSV":
        for vul in scan_data.get('vulnerabilities'):
            vul["target"] = scan_data.get('target')
        dict_to_csv(scan_data.get('vulnerabilities'), filename)

    else:
        raise ValueError("Unknown output format!")
