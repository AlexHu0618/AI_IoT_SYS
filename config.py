# @Contact : jthu4alex@163.com
# @FileName: config.py
# @Software: PyCharm
# @Blog    : http://www.gzrobot.net/aboutme
# @version : 0.1.0

import os
from ruamel import yaml
import ruamel
import warnings


class ConfigYaml(object):
    def __init__(self, file):
        """
        get target file
        :param file:
        """
        self.file = os.path.join(os.path.dirname(os.path.realpath(__file__)), file)

    def read_yaml_file(self, key=None):
        """
        to read yaml data
        :return:
        """
        warnings.simplefilter('ignore', ruamel.yaml.error.UnsafeLoaderWarning)
        with open(self.file, 'r', encoding='utf-8') as f:
            rsl = yaml.load_all(f.read())
            for i in rsl:
                if key is not None and key in i.keys():
                    return i[key]
                else:
                    return i
            # print()
            # print('*****************************')
            # print(i)
            # if isinstance(i, dict):
            #     print(json.dumps(i,
            #                      ensure_ascii=False,
            #                      sort_keys=True,
            #                      indent=4,
            #                      separators=(',', ':')))
            # else:
            #     print(i)

    def write_yaml_file(self, *data):
        """
        to write yaml data
        :param data:
        :return:
        """
        try:
            with open(self.file, 'w', encoding='utf-8') as f:
                yaml.dump_all(data,
                              f,
                              Dumper=yaml.RoundTripDumper)
                print("successful for writing!")
        except Exception as e:
            print(f"raise error{e}")
        finally:
            f.close()


config_parser = ConfigYaml('config.yml')
