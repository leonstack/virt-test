import logging, re
from autotest.client.shared import error
from virttest import utils_misc

@error.context_aware
def run_format_disk(test, params, env):
    """
    Format guest disk:
    1) Boot guest with second disk
    2) Login to the guest
    3) Get disk list in guest
    4) Create partition on disk
    5) Format the disk
    6) Mount the disk
    7) Read in the file to see whether content has changed

    @param test: QEMU test object
    @param params: Dictionary with the test parameters
    @param env: Dictionary with test environment.
    """
    vm = env.get_vm(params["main_vm"])
    vm.verify_alive()

    error.context("Login to the guest", logging.info)
    session = vm.wait_for_login(timeout=int(params.get("login_timeout", 360)))
    cmd_timeout = int(params.get("cmd_timeout", 360))

    # Create a partition on disk
    create_partition_cmd = params.get("create_partition_cmd")
    if create_partition_cmd:
        has_dispart = re.findall("diskpart", create_partition_cmd, re.I)
        if (params.get("os_type") == 'windows' and has_dispart):
            error.context("Get disk list in guest")
            list_disk_cmd = params.get("list_disk_cmd")
            s, o = session.cmd_status_output(list_disk_cmd,
                                                     timeout=cmd_timeout)
            for i in re.findall("Disk*.(\d+)\s+Offline",o):
                error.context("Set disk '%s' to online status" % i,
                              logging.info)
                set_online_cmd = params.get("set_online_cmd") % i
                s, o = session.cmd_status_output(set_online_cmd,
                                                     timeout=cmd_timeout)
                if s !=0:
                    raise error.TestFail("Can not set disk online %s" % o)

        error.context("Create partition on disk", logging.info)
        s, o = session.cmd_status_output(create_partition_cmd,
                                                 timeout=cmd_timeout)
        if s != 0:
            raise error.TestFail("Failed to create partition with error: %s" % o)
        logging.info("Output of command of create partition on disk: %s" % o)

    format_cmd = params.get("format_cmd")
    if format_cmd:
        error.context("Format the disk with cmd '%s'" % format_cmd,
                      logging.info)
        s, o = session.cmd_status_output(format_cmd,
                                                 timeout=cmd_timeout)
        if s != 0:
            raise error.TestFail("Failed to format with error: %s" % o)
        logging.info("Output of format disk command: %s" % o)

    mount_cmd = params.get("mount_cmd")
    if mount_cmd:
        error.context("Mount the disk with cmd '%s'" % mount_cmd, logging.info)
        s, o = session.cmd_status_output(mount_cmd, timeout=cmd_timeout)
        if s != 0:
            raise error.TestFail("Failed to mount with error: %s" % o)
        logging.info("Output of mount disk command: %s" % o)

    error.context("Write some random string to test file", logging.info)
    testfile_name = params.get("testfile_name")
    ranstr = utils_misc.generate_random_string(100)

    writefile_cmd = params.get("writefile_cmd")
    wfilecmd = writefile_cmd + " " + ranstr + " >" + testfile_name
    s, o = session.cmd_status_output(wfilecmd, timeout=cmd_timeout)
    if s != 0:
        raise error.TestFail("Write to file error: %s" % o)

    error.context("Read in the file to see whether content has changed",
                  logging.info)
    readfile_cmd = params.get("readfile_cmd")
    rfilecmd = readfile_cmd + " " + testfile_name
    s, o = session.cmd_status_output(rfilecmd, timeout=cmd_timeout)
    if s != 0:
        raise error.TestFail("Read file error: %s" % o)
    if o.strip() != ranstr:
        raise error.TestFail("The content writen to file has changed")
    session.close()
