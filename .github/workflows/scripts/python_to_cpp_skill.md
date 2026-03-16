---
name: convert_python_to_cpp
description: Python to C++ code conversion agent.
argument-hint: a task to implement.
---

If there have been changes or additions to the Python code under the "/source" directory between the most recent commit and the commit immediately preceding it, please perform the following steps.

Convert the modified Python code to C++.
  - For example, if there is a file named "pid_controller.py", create files named "pid_controller.cpp" and "pid_controller.hpp" in the same directory.
  - If "pid_controller.cpp" and "pid_controller.hpp" already exist, verify their contents and edit them so that they provide the same functionality as "pid_controller.py".
  - When converting, create C++ classes and functions that directly mirror the class and function structures of the Python code.
  - With embedded implementation in mind, keep the following in mind:
    - Do not use dynamic memory allocation.
    - Do not use while loops.
  - Write the C++ code so that it can be built with C++11.
  - Once "pid_controller.cpp" and "pid_controller.hpp" are complete, create "pid_controller_SIL.cpp" in the same directory. "pid_controller_SIL.cpp" is used for Software-In-the-Loop simulation with Pybind11.
    - "pid_controller_SIL.cpp" wraps ONLY the methods (member functions) that are explicitly defined in the Python class. Do NOT create additional convenience functions such as getters, setters, or reset functions that do not exist as methods in the Python source code. The SIL file should have an `initialize` function and one wrapper function per method defined in the Python class.
    - Refer to the "*_SIL.cpp" files in other directories for guidance on coding style.
    - If "pid_controller_SIL.cpp" already exists, review its contents and modify "pid_controller_SIL.cpp" so that it has the same interface as the class and content in "pid_controller.py". Remove any functions that do not correspond to methods in the Python class.

If you cannot find any other "*_SIL.cpp" files to use as a reference, use the following code as a guide.

```cpp
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

#include "sample_matrix.hpp"

namespace sample_matrix_SIL {

namespace py = pybind11;

SampleMatrix sm;

void initialize(void) { sm = SampleMatrix(); }

// Class: SampleMatrix
// Method: add
py::array_t<SampleMatrix::FLOAT> add(py::array_t<SampleMatrix::FLOAT> A_in,
                                     py::array_t<SampleMatrix::FLOAT> B_in) {

  py::buffer_info A_info = A_in.request();
  py::buffer_info B_info = B_in.request();

  /* check compatibility */
  if (SampleMatrix::MATRIX_SIZE != A_info.shape[0]) {
    throw std::runtime_error("ref must have " +
                             std::to_string(SampleMatrix::MATRIX_SIZE) +
                             " columns.");
  }

  if (SampleMatrix::MATRIX_SIZE != B_info.shape[0]) {
    throw std::runtime_error("ref must have " +
                             std::to_string(SampleMatrix::MATRIX_SIZE) +
                             " columns.");
  }

  /* substitute */
  SampleMatrix::DenseMatrix_Type A;
  SampleMatrix::DiagMatrix_Type B;

  SampleMatrix::FLOAT *A_data_ptr =
      static_cast<SampleMatrix::FLOAT *>(A_info.ptr);
  for (std::size_t i = 0; i < SampleMatrix::MATRIX_SIZE; i++) {
    for (std::size_t j = 0; j < SampleMatrix::MATRIX_SIZE; j++) {

      A(i, j) = A_data_ptr[i * SampleMatrix::MATRIX_SIZE + j];
    }
  }

  SampleMatrix::FLOAT *B_data_ptr =
      static_cast<SampleMatrix::FLOAT *>(B_info.ptr);
  for (std::size_t i = 0; i < SampleMatrix::MATRIX_SIZE; i++) {
    B(i) = B_data_ptr[i * SampleMatrix::MATRIX_SIZE + i];
  }

  /* call add method */
  auto result = sm.add(A, B);

  /* return numpy array */
  py::array_t<SampleMatrix::FLOAT> output;
  output.resize({static_cast<int>(SampleMatrix::MATRIX_SIZE),
                 static_cast<int>(SampleMatrix::MATRIX_SIZE)});

  for (std::size_t i = 0; i < SampleMatrix::MATRIX_SIZE; ++i) {
    for (std::size_t j = 0; j < SampleMatrix::MATRIX_SIZE; ++j) {
      output.mutable_at(i, j) = result(i, j);
    }
  }

  return output;
}

PYBIND11_MODULE(SampleMatrixSIL, m) {
  m.def("initialize", &initialize, "Initialize the module");
  m.def("add", &add, "add method");
}

} // namespace sample_matrix_SIL
```
