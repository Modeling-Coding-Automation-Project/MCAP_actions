---
name: convert_python_to_cpp_cpp
description: Python to C++ implementation file (.cpp) conversion agent.
argument-hint: a task to implement.
---

If there have been changes or additions to the Python code under the "/source" directory between the most recent commit and the commit immediately preceding it, please perform the following steps.

Convert the modified Python code to a C++ implementation file (.cpp).
  - For example, if there is a file named "pid_controller.py", create a file named "pid_controller.cpp" in the same directory.
  - If "pid_controller.cpp" already exists, verify its contents and edit it so that it provides the same functionality as "pid_controller.py".
  - When converting, create C++ member function implementations that directly mirror the class and function structures of the Python code.
  - With embedded implementation in mind, keep the following in mind:
    - Do not use dynamic memory allocation.
    - Do not use while loops.
  - Write the C++ code so that it can be built with C++11.
