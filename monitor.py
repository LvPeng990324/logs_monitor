import utils
import sys


def main():
    """
    监控器方法
    """

    # 判断参数列表长度，看是否提供了配置文件目录
    argv_list = sys.argv
    if len(argv_list) != 2:
        # 如果参数列表长度不是2，表明给的参数不止一个或没给参数，报错提示并退出
        raise '参数长度不正确，请给出仅一个配置文件路径参数，如果路径含有空格请使用单/双引号包裹'
    # 读取配置文件
    conf = utils.read_conf(argv_list[1])
    
    # 遍历配置中要管理的目录
    # 将需要进行备份的日志文件进行备份操作
    # 并且将它们的路径记录到列表中，以备进行邮件提醒
    backuped_logs_list = []
    for path in conf['logs_path']:
        # 获取当前path下日志文件路径及大小关系映射字典
        logs_path_size_dict = utils.get_logs_path_size(path, conf['logs_suffix'])
        # 获取要进行备份的日志路径们
        # （先进行配置文件中阈值数值单位转换）
        backup_size_byte = utils.covert_unit_of_filesize(conf['backup_size'], conf['unit'], 'B')
        to_backup_logs_list = utils.get_to_backup_logs(logs_path_size_dict, backup_size_byte)
        # 遍历需要备份的日志文件，进行备份
        for to_backup_log in to_backup_logs_list:
            utils.backup_conf(to_backup_log)
            # 记录到backuped_logs_list里
            backuped_logs_list.append(to_backup_log)

    # 判断是否需要email提醒
    # 本次没有进行备份操作的话也不发送email
    if conf['need_email'] and backuped_logs_list:
        # 创建邮件内容
        message = '''
        你的{}服务器内，以下日志文件大小超过设置阈值，已进行备份：
        {}
        '''.format(conf['server_name'], backuped_logs_list)
        # 发送电子邮件
        utils.send_email(
            from_email=conf['from_email'], 
            email_password=conf['email_password'], 
            to_email=conf['to_email'], 
            message=message,
        )


if __name__ == "__main__":
    main()
