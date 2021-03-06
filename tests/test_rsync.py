import context  # noqa: F401, isort:skip

import os
import shutil
import unittest

from dups import const, rsync

import utils as test_utils


class Test_Path(unittest.TestCase):
    def test_local(self):
        p = rsync.Path(context.TEST_DIR)
        self.assertTrue(p.is_local)

        p = rsync.Path(context.TEST_DIR)
        self.assertTrue(p.is_local)

    def test_remote(self):
        p = rsync.Path(context.TEST_DIR, context.SSH_HOST)
        self.assertTrue(not p.is_local)


class Test_Status(unittest.TestCase):
    def test_valid(self):
        status = rsync.Status(0)
        self.assertEqual(status.exit_code, 0)

    def test_invalid(self):
        self.assertRaises(ValueError, rsync.Status, -999)

    def test_complete(self):
        status = rsync.Status(0)
        self.assertTrue(status.is_complete)

        status = rsync.Status(20)
        self.assertTrue(not status.is_complete)


class Test_rsync(unittest.TestCase):
    @property
    def data_dir_struct(self):
        return test_utils.get_dir_struct(context.DATA_DIR.encode())

    @property
    def real_target(self):
        return os.path.join(context.TMP_DIR, context.DATA_DIR.lstrip('/'))

    def setUp(self):
        if os.path.isdir(context.TMP_DIR):
            shutil.rmtree(context.TMP_DIR)

        if os.path.isfile(context.TMP_FILE):
            os.remove(context.TMP_FILE)

    def tearDown(self):
        self.setUp()

    def test_singleton(self):
        sync1 = rsync.rsync.get()
        sync2 = rsync.rsync.get()

        self.assertEqual(sync1, sync2)

        del sync2
        sync2 = None

        sync2 = rsync.rsync.get()
        self.assertEqual(sync1, sync2)

    def test_success(self):
        sync = rsync.rsync()
        sync.dry_run = False

        target = rsync.Path(context.TMP_DIR)
        status = sync.sync(target, [context.TEST_DIR])
        self.assertEqual(status.exit_code, 0)

    def test_local_simple(self):
        sync = rsync.rsync()
        sync.dry_run = False

        # Define the structure we expect after synchronizing
        expected_data = self.data_dir_struct
        del expected_data[b'test.dir'][b'dir2']
        del expected_data[context.SPECIAL_NAME]

        # Send the files
        target = rsync.Path(context.TMP_DIR)
        sync.sync(target, [context.TEST_DIR, context.TEST_FILE],
                  excludes=['**/dir2/.gitkeep'])

        # Get and compare the structure of our sync target
        synced_data = test_utils.get_dir_struct(self.real_target.encode())
        self.assertEqual(expected_data, synced_data)

    def test_remote_simple(self):
        sync = rsync.rsync()
        sync.dry_run = False

        # Define the structure we expect after synchronizing
        expected_data = self.data_dir_struct
        del expected_data[b'test.dir'][b'dir2']
        del expected_data[context.SPECIAL_NAME]

        # Send the files
        target = rsync.Path(context.TMP_DIR, context.SSH_HOST)
        sync.sync(target, [context.TEST_DIR, context.TEST_FILE],
                  excludes=['**/dir2/.gitkeep'])

        # Get and compare the structure of our sync target
        synced_data = test_utils.get_dir_struct(self.real_target.encode())
        self.assertEqual(expected_data, synced_data)

    def test_local_special_char(self):
        sync = rsync.rsync()
        sync.dry_run = False

        # Define the structure we expect after synchronizing
        expected_data = self.data_dir_struct
        del expected_data[b'test.dir']
        del expected_data[b'test.file']

        # Send the files
        target = rsync.Path(context.TMP_DIR)
        sync.sync(target, [context.SPECIAL_FILE.decode()])

        # Get and compare the structure of our sync target
        synced_data = test_utils.get_dir_struct(self.real_target.encode())
        self.assertEqual(expected_data, synced_data)

    def test_remote_special_char(self):
        sync = rsync.rsync()
        sync.dry_run = False

        # Define the structure we expect after synchronizing
        expected_data = self.data_dir_struct
        del expected_data[b'test.dir']
        del expected_data[b'test.file']

        # Send the files
        target = rsync.Path(context.TMP_DIR, context.SSH_HOST)
        sync.sync(target, [context.SPECIAL_FILE.decode()])

        # Get and compare the structure of our sync target
        synced_data = test_utils.get_dir_struct(self.real_target.encode())
        self.assertEqual(expected_data, synced_data)

    def test_options(self):
        sync = rsync.rsync()
        sync.dry_run = False
        sync.prune_empty_dirs = False

        # Define the structure we expect after synchronizing
        expected_data = self.data_dir_struct
        del expected_data[b'test.dir'][b'dir2'][b'.gitkeep']
        del expected_data[context.SPECIAL_NAME]

        # Send the files
        target = rsync.Path(context.TMP_DIR)
        sync.sync(target, [context.TEST_DIR, context.TEST_FILE],
                  excludes=['**/dir2/.gitkeep'])

        # Get and compare the structure of our sync target
        synced_data = test_utils.get_dir_struct(self.real_target.encode())
        self.assertEqual(expected_data, synced_data)

    def test_ssh_wrapper(self):
        sync = rsync.rsync()
        sync.ssh_bin = '{} root {}'.format(const.SSH_WRAPPER_SCRIPT,
                                           sync.ssh_bin)
        sync.dry_run = False

        # Send the files
        target = rsync.Path(context.TMP_DIR, context.SSH_HOST)
        status = sync.sync(target, [context.DATA_DIR])

        self.assertEqual(status.exit_code, 0)


if __name__ == '__main__':
    unittest.main(exit=False)
