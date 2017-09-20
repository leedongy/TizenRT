#!/usr/bin/env python

# Copyright JS Foundation and other contributors, http://js.foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#  This file converts ./js/*.js to a C-array in ./source/jerry-targetjs.h file

import argparse
import glob
import os
import re

from gen_c_source import LICENSE, format_code


HEADER = '''#ifndef JERRY_TARGETJS_H
#define JERRY_TARGETJS_H
'''

FOOTER = '''
#endif
'''

NATIVE_STRUCT = '''
struct js_source_all {
  const char* name;
  const char* source;
  const int length;
};

#define DECLARE_JS_CODES \\
struct js_source_all js_codes[] = \\
{ \\'''


def extract_name(path):
    special_chars = re.compile(r'[-\\?\'".]')
    return special_chars.sub('_', os.path.splitext(os.path.basename(path))[0])


def reduce_code(code):
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)  # remove all occurance streamed comments
    code = re.sub(r"//.*?\n", "", code)  # remove all occurance singleline comments
    code = re.sub('\n+', '\n', re.sub('\n +', '\n', code))  # remove white spaces
    return code


def js_to_native_code(path, name, build_type):
    with open(path, 'r') as js_source:
        code = js_source.read()

    if build_type != 'debug':
        code = reduce_code(code)

    data = format_code(code, 1, 2)

    native_code = """const static char {0}_n[] = "{0}";
const static char {0}_s[] =
{{
{1}
}};
const static int {0}_l = {2};
""".format(name, data, len(code))

    return native_code


def main():
    parser = argparse.ArgumentParser(description="js2c")
    parser.add_argument('--build-type', help='build type', default='release', choices=['release', 'debug'])
    parser.add_argument('--ignore', help='files to ignore', dest='ignore_files', default=[], action='append')
    parser.add_argument('--no-main',
                        help="don't require a 'main.js' file",
                        dest='main',
                        action='store_false',
                        default=True)
    parser.add_argument('--js-source',
                        dest='js_source_path',
                        default='./js',
                        help='Source directory of JavaScript files" (default: %(default)s)')
    parser.add_argument('--dest',
                        dest='output_path',
                        default='./source',
                        help="Destination directory of 'jerry-targetjs.h' (default: %(default)s)")

    script_args = parser.parse_args()

    gen_line = "/* This file is generated by %s. Please do not modify. */" % os.path.basename(__file__)

    gen_output = [LICENSE, "", gen_line, "", HEADER]
    gen_structs = [NATIVE_STRUCT]

    if script_args.main:
        gen_structs.append('  {{ {0}_n, {0}_s, {0}_l }}, \\'.format("main"))

    files = glob.glob(os.path.join(script_args.js_source_path, '*.js'))

    for path in files:
        if os.path.basename(path) not in script_args.ignore_files:
            name = extract_name(path)
            gen_output.append(js_to_native_code(path, name, script_args.build_type))
            if name != 'main':
                gen_structs.append('  {{ {0}_n, {0}_s, {0}_l }}, \\'.format(name))

    gen_structs.append('  { NULL, NULL, 0 } \\\n};')

    gen_output.append("\n".join(gen_structs))
    gen_output.append(FOOTER)

    with open(os.path.join(script_args.output_path, 'jerry-targetjs.h'), 'w') as gen_file:
        gen_file.write("\n".join(gen_output))


if __name__ == "__main__":
    main()