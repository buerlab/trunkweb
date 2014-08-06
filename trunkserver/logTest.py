from mylog import mylog,getLogText


def dbserviceLog(*arg):
    prefix = tuple(["DbServiceLog:"])
    arg = prefix + arg
    mylog.getlog().info(getLogText(arg))
