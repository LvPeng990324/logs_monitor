import os
from configparser import ConfigParser
from datetime import datetime
import smtplib
from email.mime.text import MIMEText


def read_conf(conf_file_path='./conf.ini'):
    """
    读取配置文件方法
    
    ## 参数 ##
    conf_file_path: 配置文件路径

    ## 返回值 ##
    以字典记录的配置文件内容
    """

    # 实例化解析器并读取配置文件
    cfg = ConfigParser()
    cfg.read(conf_file_path)
    # 读取配置中的备份目录们，存入一个列表
    logs_path_list = []
    for items in cfg.items('logs_path'):
        logs_path_list.append(items[1])
    # 存储记录的字典
    conf_dict = {
        'backup_size': cfg.getfloat('settings', 'backup_size'), 
        'unit': cfg.get('settings', 'unit'), 
        'logs_suffix': cfg.get('settings', 'logs_suffix'), 
        'need_email': cfg.getboolean('email', 'need_email'), 
        'from_email': cfg.get('email', 'from_email'), 
        'email_password': cfg.get('email', 'email_password'), 
        'to_email': cfg.get('email', 'to_email'), 
        'server_name': cfg.get('email', 'server_name'),
        'logs_path': logs_path_list,
    }
    # 返回数据
    return conf_dict


def covert_unit_of_filesize(filesize, old_unit, new_unit):
    """
    文件大小单位转换方法

    ## 参数 ##
    filesize: 文件原单位下的大小数值
    old_unit: 原来的单位，可取值为：'B'、'K'、'M'、'G'，应该不会再大了吧，对应字节、千字节、兆字节、吉字节
    new_unit: 要转换的单位，可取值为：'B'、'K'、'M'、'G'，应该不会再大了吧，对应字节、千字节、兆字节、吉字节

    ## 返回值 ##
    返回对应转换后的数值
    """

    # 定义对应单位的数量级映射关系
    unit_size_dict = {
        'B': 1, 
        'K': 1e3, 
        'M': 1e6, 
        'G': 1e9,
    }
    # 计算old_unit与new_unit相差的数量级
    gap_size = unit_size_dict[old_unit] / unit_size_dict[new_unit]
    # 将给定的filesize乘以这个gap_size即可得到转换后的大小数值
    return filesize * gap_size


def is_log_file(file_name, logs_suffix):
    """
    判断是否是日志文件方法
    通过给定的后缀判断给定的文件名是不是日志文件

    ## 参数 ##
    file_name: 日志文件名
    logs_suffix: 日志后缀

    ## 返回值 ##
    如果是日志文件返回True，否则返回False
    """

    # 首先判断logs_suffix是不是None
    if logs_suffix == 'None':
        # 日志文件没有后缀，那就判断给定文件名里有没有后缀符号点.
        # 有就判定它不是日志文件
        # 没有就判定它是日志文件
        # （哪有这么脑瘫的日志命名...但是为了兼容，这个判断还是加上吧）
        if '.' in file_name:
            return False
        else:
            return True
    else:
        # 有后缀，判断给定文件名最后几位跟给定后缀是否相同，
        # 相同就判定它是日志文件
        # 不同就不是日志文件
        if file_name[-len(logs_suffix):] == logs_suffix:
            return True
        else:
            return False


def get_logs_path_size(logs_path, logs_suffix):
    """
    获取日志路径: 大小映射关系方法

    ## 参数 ##
    logs_path: 要监控日志的目录路径，最好是绝对路径
    logs_suffix: 日志文件的后缀

    ## 返回值 ##
    返回字典，存储路径下文件的路径和字节单位的文件大小的映射关系
    """

    # 获取此目录下所有文件/文件夹名称
    files_name = os.listdir(logs_path)
    filepath_filesize_dict = {}  # 文件名: 文件大小字典
    # 遍历获取到的文件/文件夹
    for file_name in files_name:
        # 根据给定后缀仅筛选日志文件名
        if not is_log_file(file_name, logs_suffix):
            continue
        # 拼接出可访问路径
        file_path = os.path.join(logs_path, file_name)
        # 判断是否是文件夹，是的话就continue
        if os.path.isdir(file_path):
            continue
        # 获取这个文件的大小
        file_size = os.path.getsize(file_path)
        # 将文件路径及大小信息记录
        filepath_filesize_dict[file_path] = file_size
    return(filepath_filesize_dict)


def get_to_backup_logs(logs_path_size, backup_size):
    """
    获取需要进行备份的日志的方法

    ## 参数 ##
    logs_path_size: 日志路径: 大小映射关系
    backup_size: 字节单位的日志大小阈值，超过这个大小的日志将被判定为要备份的

    ## 返回值 ##
    返回记录着需要进行备份的日志文件的路径
    """

    # 遍历logs_path_size
    # 将需要进行备份的日志路径记录到列表中
    to_backup_logs_list = []
    for path_size in logs_path_size.items():
        if path_size[1] > backup_size:
            # 需要进行备份
            to_backup_logs_list.append(path_size[0])
    # 返回这个记录
    return to_backup_logs_list


def backup_conf(file_path):
    """
    备份指定日志文件方法
    将把指定文件文件名后加.backup_年_月_日_时_分，存储在相同目录下

    ## 参数 ##
    file_path: 要备份的日志文件的路径

    ## 返回值 ##
    无返回值
    """
    
    # 获取要添加在文件名后边的字符
    suffix ='.backup_{}'.format(datetime.now().strftime(r'%Y_%m_%d_%H_%M'))
    # 生成新文件路径名
    new_file_path = file_path + suffix
    # 重命名文件
    os.rename(file_path, new_file_path)


def send_email(from_email, email_password, to_email, message):
    """
    发送email方法
    此方法默认使用163邮箱的smtp服务
    请确认已开启
    如需其它邮箱，请自行修改

    ## 参数 ##
    from_email: 发送邮件用的email地址
    email_password: 发送邮件用的email登陆密码
    to_email: 接收提醒的email地址
    message: 要发送的内容

    ## 返回值 ##
    无返回值
    """
    
    #设置服务器所需信息
    #163邮箱服务器地址
    mail_host = 'smtp.163.com'  
    #163用户名
    mail_user = from_email
    #密码(部分邮箱为授权码) 
    email_password = email_password
    #邮件接受方邮箱地址
    receivers = [to_email]  

    #设置email信息
    #邮件内容设置
    message = MIMEText(message, 'plain', 'utf-8')
    #邮件主题       
    message['Subject'] = '日志文件已备份提醒' 
    #发送方信息
    message['From'] = from_email 
    #接受方信息     
    message['To'] = receivers[0]  

    #登录并发送邮件
    smtpObj = smtplib.SMTP() 
    #连接到服务器
    smtpObj.connect(mail_host,25)
    #登录到服务器
    smtpObj.login(mail_user, email_password) 
    #发送
    smtpObj.sendmail(
        from_email ,receivers, message.as_string()) 
    #退出
    smtpObj.quit() 


def main():
    # print(get_filepath_filesize('./logs'))
    # print(read_conf())
    # backup_conf('./logs/第三次大作业.zip')
    # print(is_log_file('alsdjflasjdf.log', '.log'))
    # print(get_logs_path_size('./logs', '.pdf'))
    # print(covert_unit_of_filesize(116116, 'B', 'B'))
    send_email(
        from_email='lvpeng990324@163.com', 
        email_password='lp990324', 
        to_email='lvpeng990324@qq.com', 
        message='测试信息'
    )


if __name__ == "__main__":
    main()
