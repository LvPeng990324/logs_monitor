import utils


# TODO 待增加系统命令参数功能
def main():
    """
    监控器方法
    """

    # 读取配置文件
    # TODO 参数待补充
    conf = utils.read_conf()
    
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
    if conf['need_email']:
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
