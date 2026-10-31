import unittest

from universal_touch.memory import parse_linux_status, process_memory


class MemoryTests(unittest.TestCase):
    def test_reads_process_peak_and_current_rss_instead_of_ancestor_history(self):
        result = parse_linux_status('Name:\tpython\nVmHWM:\t102400 kB\nVmRSS:\t81920 kB\n')
        self.assertEqual(result, {'peak_rss_mib':100.,'rss_mib':80.,'memory_source':'proc-self-status'})

    def test_absent_process_counters_have_no_invented_measurement(self):
        self.assertIsNone(parse_linux_status('Name:\tpython\n'))

    def test_real_process_memory_is_positive(self):
        result = process_memory()
        self.assertGreater(result['peak_rss_mib'],0)
        self.assertGreater(result['rss_mib'],0)
