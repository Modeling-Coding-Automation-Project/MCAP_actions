---
name: convert-python-matrix-to-cpp
description: When you convert Python code which uses NumPy to C++, you must follow this instruction. You can define efficient algorithm with matrix calculation.
---

# Coding C++ algorithms with Matrix

## Basic strategy

- The algorithms are assumed to be implemented to micro controllers.
  - Don't use dynamic memory allocation command.
  - Consider saving memory usage.
  - Don't use "while" because the calculation time will not be deterministic.
- One file, one class.
  - Write one C++ class in one file. Don't write more than two classes in on file.
  - Write namespace to avoid name conflict. The namespace name should be the same as file name.
  - Write header and source file to define the class.
- Class constructor.
  - Constructor with no arguments is always needed.
  - For example, if you want to write "SampleMatrix" class which needs one argument in constructor, write as below.

``` cpp
class SampleMatrix {

public:
  SampleMatrix();

  SampleMatrix(double value);

  ~SampleMatrix();
}
```

## use "python_numpy.hpp"

If you want to write matrix such as Python NumPy, Use "python_numpy.hpp".

``` cpp
#include "python_numpy.hpp"
```

Write the include code in header files.

## Define Matrix

You can use DenseMatrix, DiagMatrix, SparseMatrix.

Matrix definition of "python_numpy.hpp" is mathematical.

"number of columns" is the number of vertical elements. "number of rows" is the number of horizontal elements.

### DenseMatrix

Python NumPy can define dense matrix like below.

``` python
A = np.array([[1., 2., 3.], [5., 4., 6.], [9., 8., 7.]])
```

You can define dense matrix with "python_numpy.hpp" as below.

``` cpp
auto A = PythonNumpy::make_DenseMatrix<3, 3>(1.0, 2.0, 3.0, 5.0, 4.0, 6.0, 9.0, 8.0, 7.0);
```

The first template argument is the number of columns, the second is rows.

You can also define the type of the dense matrix as below.

``` cpp
using DenseMatrix_Type = PythonNumpy::DenseMatrix_Type<double, 3, 3>;
```

### DiagMatrix

Python NumPy can define diag matrix like below.

``` python
B = np.diag([1., 2., 3.])
```

You can define diag matrix with "python_numpy.hpp" as below.

``` cpp
auto B = PythonNumpy::make_DiagMatrix<3>(1.0, 2.0, 3.0);
```

The first template argument is the number of columns.

You can also define the type of the diag matrix as below.

``` cpp
using DiagMatrix_Type = PythonNumpy::DiagMatrix_Type<double, 3>;
```

### SparseMatrix

Python NumPy has no sparse matrix features. So we usually define sparse matrix like below.

``` python
C = np.array([[1., 0., 0.], [3., 0., 8.], [0., 2., 4.]])
```

It's not efficient, but anyway we can handle matrix calculation.

You can define sparse matrix with "python_numpy.hpp" as below.

``` cpp
using SparseAvailable_C = PythonNumpy::SparseAvailable<
  PythonNumpy::ColumnAvailable<true, false, false>,
  PythonNumpy::ColumnAvailable<true, false, true>,
  PythonNumpy::ColumnAvailable<false, true, true>>;

auto C = PythonNumpy::make_SparseMatrix<SparseAvailable_C>(1.0, 3.0, 8.0, 2.0, 4.0);
```

"SparseAvailable" defines which elements are valid or invalid.
You specify only the valid initial values in "make_SparseMatrix" arguments.

## Matrix calculations

You can use "+", "-", "*" to calculate matrix addition, subtraction, product.

Note that Python NumPy use "@" to calculate matrix product.
