#!/usr/bin/env python
#
# Copyright 2014 Microsoft Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import tempfile
import os
import LogUtil as lu


class TestLogUtil(unittest.TestCase):    
    def test_tail(self):
        # Create a temporary file that works on both Windows and Unix
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, encoding="utf-8") as F:
            temp_path = F.name
            # Write unicode string directly (no encoding needed for text mode)
            F.write("abcdefghijklmnopqrstu\u6211vwxyz")
        
        try:
            tail = lu.tail(temp_path, 2)
            self.assertEqual("yz", tail)

            tail = lu.tail(temp_path)
            self.assertEqual("abcdefghijklmnopqrstuvwxyz", tail)
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

if __name__ == '__main__':
    unittest.main()
