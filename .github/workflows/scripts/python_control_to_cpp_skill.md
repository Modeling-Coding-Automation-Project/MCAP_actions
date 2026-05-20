---
name: convert-python-control-to-cpp
description: When you convert Python code which uses python-control, or MCAP custom control libraries (LinearKalmanFilter, ExtendedKalmanFilter, UnscentedKalmanFilter, LeastSquares, RecursiveLeastSquares), to C++, you must follow this instruction. You can define efficient control and estimation algorithms for microcontrollers.
---

# Coding C++ control algorithms with python_control.hpp

## Basic strategy

- The algorithms are assumed to be implemented on micro controllers.
  - Don't use dynamic memory allocation commands.
  - Consider saving memory usage.
  - Don't use "while" because the calculation time will not be deterministic.
- One file, one class.
  - Write one C++ class in one file. Don't write more than two classes in one file.
  - Write namespace to avoid name conflict. The namespace name should be the same as file name.
  - Write header and source file to define the class.
- Class constructor.
  - Constructor with no arguments is always needed.

## use "python_control.hpp"

If you want to write control algorithms such as Python Control (python-control), use "python_control.hpp".

``` cpp
#include "python_control.hpp"
```

Write the include code in header files.

`python_control.hpp` includes the following headers internally:
- `python_control_kalman_filter.hpp` — Linear/Extended/Unscented Kalman Filters
- `python_control_least_squares.hpp` — Least Squares / Recursive Least Squares
- `python_control_lqr.hpp` — LQR / LQI controllers
- `python_control_pid_controller.hpp` — Discrete PID controller
- `python_control_state_space.hpp` — Discrete state-space model
- `python_control_transfer_function.hpp` — Discrete transfer function

Use the namespace at the top of the source file:

``` cpp
using namespace PythonControl;
```

When matrix operations are also needed (e.g. for Kalman filters or LQR), also include `python_numpy.hpp`:

``` cpp
#include "python_control.hpp"
#include "python_numpy.hpp"

using namespace PythonNumpy;
using namespace PythonControl;
```

---

## Discrete Transfer Function

### Python (python-control)

``` python
import control
sys_d = control.TransferFunction([0.5, 0.3, 0.1], [1.0, -1.8, 1.5, -0.7, 0.2], dt=0.2)
```

### C++

``` cpp
auto numerator = make_TransferFunctionNumerator<3>(0.5, 0.3, 0.1);
auto denominator = make_TransferFunctionDenominator<5>(1.0, -1.8, 1.5, -0.7, 0.2);
double dt = 0.2;
auto sys = make_DiscreteTransferFunction(numerator, denominator, dt);
```

The first template argument of `make_TransferFunctionNumerator<N>` is the number of coefficients.
The first template argument of `make_TransferFunctionDenominator<N>` is the number of coefficients.

### Simulation loop

``` cpp
for (std::size_t i = 0; i < 30; i++) {
  double u = 1.0;
  sys.update(u);
  std::cout << "y: " << sys.get_y() << std::endl;
}
```

### Derive steady-state input for a given output

``` cpp
double y_steady_state = 1.0;
double u_steady_state = sys.solve_steady_state_and_input(y_steady_state);
auto x_steady_state = sys.get_X();
```

---

## Discrete State Space

### Python (python-control / NumPy)

``` python
import control, numpy as np
A = np.array([[0.7, 0.2], [-0.3, 0.8]])
B = np.array([[0.1], [0.2]])
C = np.array([[2.0, 0.0]])
D = np.array([[0.0]])
dt = 0.01
sys = control.ss(A, B, C, D, dt)
```

### C++

Use `PythonNumpy` to define the matrices, then build the system with `make_DiscreteStateSpace`.

``` cpp
auto A = make_DenseMatrix<2, 2>(0.7, 0.2, -0.3, 0.8);
auto B = make_DenseMatrix<2, 1>(0.1, 0.2);
auto C = make_DenseMatrix<1, 2>(2.0, 0.0);
auto D = make_DenseMatrix<1, 1>(0.0);
double dt = 0.01;
auto sys = make_DiscreteStateSpace(A, B, C, D, dt);
```

For sparse state matrices, use `make_SparseMatrix`. For empty D matrices, use `make_SparseMatrixEmpty`.

``` cpp
auto D = make_SparseMatrixEmpty<double, OUTPUT_SIZE, INPUT_SIZE>();
```

### Input / State / Output vectors

``` cpp
auto u = make_StateSpaceInput<1>(1.0);
auto x = make_StateSpaceState<2>(0.0, 0.0);
auto y = make_StateSpaceOutput<1>(0.0);
```

### Simulation loop

``` cpp
for (std::size_t sim_step = 0; sim_step < 50; ++sim_step) {
  auto u = make_StateSpaceInput<1>(1.0);
  sys.update(u);
  std::cout << "X: " << sys.get_X()(0, 0) << ", " << sys.get_X()(1, 0) << std::endl;
  std::cout << "Y: " << sys.get_Y()(0, 0) << std::endl;
}
```

### Useful type aliases

``` cpp
constexpr std::size_t STATE_SIZE  = decltype(A)::ROWS;
constexpr std::size_t INPUT_SIZE  = decltype(B)::COLS;
constexpr std::size_t OUTPUT_SIZE = decltype(C)::ROWS;

using X_Type = StateSpaceState_Type<double, STATE_SIZE>;
using U_Type = StateSpaceInput_Type<double, INPUT_SIZE>;
using Y_Type = StateSpaceOutput_Type<double, OUTPUT_SIZE>;
```

---

## LQR (Linear Quadratic Regulator)

### Python (python-control / scipy)

``` python
import control, numpy as np
# continuous-time matrices
Ac = np.array([[0.0, 1.0], [0.0, -0.1]])
Bc = np.array([[0.0], [2.0]])
Q = np.diag([1.0, 0.0])
R = np.diag([1.0])
K, _, _ = control.lqr(Ac, Bc, Q, R)
```

### C++

Build the continuous-time matrices (sparse is preferred for efficiency) and call `make_LQR`.

``` cpp
using SparseAvailable_Ac = SparseAvailable<
    ColumnAvailable<false, true, false, false>,
    ColumnAvailable<false, true, true,  false>,
    ColumnAvailable<false, false, false, true>,
    ColumnAvailable<false, true, true,  false>>;
auto Ac = make_SparseMatrix<SparseAvailable_Ac>(1.0, -0.1, 3.0, 1.0, -0.5, 30.0);

using SparseAvailable_Bc = SparseAvailable<
    ColumnAvailable<false>,
    ColumnAvailable<true>,
    ColumnAvailable<false>,
    ColumnAvailable<true>>;
auto Bc = make_SparseMatrix<SparseAvailable_Bc>(2.0, 5.0);

auto Q = make_DiagMatrix<4>(1.0, 0.0, 1.0, 0.0);
auto R = make_DiagMatrix<1>(1.0);

auto lqr = make_LQR(Ac, Bc, Q, R);
auto K = lqr.solve();
K = lqr.get_K();
```

### Tracking simulation

``` cpp
auto X_ref = make_DenseMatrix<4, 1>(1.0, 0.0, 0.0, 0.0);
for (int i = 0; i < 100; i++) {
  auto X = plant.get_X();
  auto U = K * (X_ref - X);
  plant.update(U);
}
```

---

## LQI (Linear Quadratic Integral)

### Python (custom MCAP library)

``` python
from python_control.lqr_deploy import LQI_Deploy
deployed_file_names = LQI_Deploy.generate_LQI_cpp_code(Ac, Bc, Cc, Q_ex, R_ex)
```

### C++

The Q_ex matrix has size `(State_Num + Output_Num)` to include the integral states.

``` cpp
constexpr std::size_t Q_EX_SIZE = State_Num + Output_Num;
auto Q_ex = make_DiagMatrix<Q_EX_SIZE>(0.0, 2.0, 2.0);
auto R_ex = make_DiagMatrix<Input_Num>(1.0);

auto lqi = make_LQI(Ac, Bc, Cc, Q_ex, R_ex);

auto K = lqi.solve();
K = lqi.get_K();
```

Extract state-feedback and integral gains from the full gain matrix:

``` cpp
auto K_x = make_DenseMatrix<1, 2>(K.template get<0, 0>(), K.template get<0, 1>());
auto K_e = make_DenseMatrix<1, 1>(K.template get<0, 2>());
```

### Tracking loop

``` cpp
auto e_y_integral = make_StateSpaceOutput<Output_Num>(0.0);
for (int i = 0; i < 100; i++) {
  auto x = plant.get_X();
  auto y = Cc * x;
  auto e_y = y_ref - y;
  e_y_integral = e_y_integral + e_y * dt;
  auto u = K_x * (x_ref - x) + K_e * e_y_integral;
  plant.update(u);
}
```

---

## Discrete PID Controller

### Python (python-control + MCAP custom library)

``` python
from external_libraries.MCAP_python_control.python_control.pid_controller import DiscretePID_Controller
pid = DiscretePID_Controller(delta_time=dt, Kp=Kp, Ki=Ki, Kd=Kd, N=(1.0/dt),
                             Kb=Ki, minimum_output=-0.2, maximum_output=0.2)
u = pid.update(error)
```

### C++

``` cpp
double dt = 0.2;
double Kp = 1.0;
double Ki = 0.1;
double Kd = 0.5;
double N  = 1.0 / dt;
double Kb = Ki;
double minimum_output = -0.2;
double maximum_output =  0.2;

auto pid = make_DiscretePID_Controller(dt, Kp, Ki, Kd, N, Kb, minimum_output, maximum_output);
```

### Simulation loop

``` cpp
double reference = 1.0;
double y = 0.0;
for (std::size_t i = 0; i < 100; i++) {
  double error = reference - y;
  double u = pid_controller.update(error);
  plant.update(u);
  y = plant.get_y();
}
```

---

## Linear Kalman Filter

The `LinearKalmanFilter` class used in Python comes from the MCAP custom library (`external_libraries/MCAP_python_control`), not from `python-control` directly.

### Python (MCAP custom library)

``` python
from external_libraries.MCAP_python_control.python_control.kalman_filter import LinearKalmanFilter
lkf = LinearKalmanFilter(A, B, C, Q, R, Number_of_Delay)
lkf.predict_and_update(u, y_measured)
x_estimate = lkf.get_x_hat_without_delay()
```

### C++

Build the discrete state-space model first, then create the filter.

``` cpp
auto sys = make_DiscreteStateSpace(A, B, C, D, dt);

auto Q = make_KalmanFilter_Q<STATE_SIZE>(1.0, 1.0, 1.0, 2.0);
auto R = make_KalmanFilter_R<OUTPUT_SIZE>(10.0, 10.0);

auto lkf = make_LinearKalmanFilter(sys, Q, R);
```

Set initial estimate:

``` cpp
lkf.set_x_hat(make_StateSpaceState<STATE_SIZE>(0.0, 0.0, 0.0, 0.0));
```

### Simulation loop

``` cpp
for (std::size_t i = 1; i < SIM_STEP_MAX; i++) {
  auto u = make_StateSpaceInput<INPUT_SIZE>(...);

  // true system
  x_true    = A * x_true + B * u;
  y_measured = C * x_true + D * u;

  // filter
  lkf.predict_and_update(u, y_measured);

  // get estimate
  auto x_hat = lkf.get_x_hat();
  // or without delay compensation:
  // auto x_hat = lkf.get_x_hat_without_delay();
}
```

`make_KalmanFilter_Q` and `make_KalmanFilter_R` produce diagonal matrices (`DiagMatrix_Type`).

---

## Extended Kalman Filter (EKF)

The `ExtendedKalmanFilter` class is from the MCAP custom library. In Python, the state and measurement equations are symbolically defined using SymPy and then deployed as callable functions.

### Python (MCAP custom library + SymPy)

``` python
from external_libraries.MCAP_python_control.python_control.kalman_filter import ExtendedKalmanFilter
ekf = ExtendedKalmanFilter(fxu, hx, fxu_jacobian, hx_jacobian,
                           Q, R, parameters, Number_of_Delay)
ekf.predict(u)
ekf.update(y_measured)
x_hat = ekf.get_x_hat_without_delay()
```

### C++

Define a parameter struct and four equation functions (state equation, state Jacobian, measurement equation, measurement Jacobian), then build the EKF.

``` cpp
// --- Parameter struct ---
template <typename T>
class MyParameter {
public:
  MyParameter() {}
  MyParameter(const T &delta_time, ...) : delta_time(delta_time), ... {}
  T delta_time;
  // other parameters ...
};

// --- Equation function signatures (defined below main) ---
template <typename T>
auto my_state_equation(
    const StateSpaceState_Type<T, STATE_SIZE> &X,
    const StateSpaceInput_Type<T, INPUT_SIZE> &U,
    const MyParameter<T> &params) -> StateSpaceState_Type<T, STATE_SIZE>;

template <typename T, typename A_Type>
auto my_state_equation_jacobian(
    const StateSpaceState_Type<T, STATE_SIZE> &X,
    const StateSpaceInput_Type<T, INPUT_SIZE> &U,
    const MyParameter<T> &params) -> A_Type;

template <typename T>
auto my_measurement_equation(
    const StateSpaceState_Type<T, STATE_SIZE> &X,
    const MyParameter<T> &params) -> StateSpaceOutput_Type<T, OUTPUT_SIZE>;

template <typename T, typename C_Type>
auto my_measurement_equation_jacobian(
    const StateSpaceState_Type<T, STATE_SIZE> &X,
    const MyParameter<T> &params) -> C_Type;
```

Declare matrix types for the Jacobians using `SparseMatrix_Type`:

``` cpp
using SparseAvailable_A = SparseAvailable<
    ColumnAvailable<true, false, true>,
    ColumnAvailable<false, true, true>,
    ColumnAvailable<false, false, true>>;
using A_Type = SparseMatrix_Type<double, SparseAvailable_A>;

using SparseAvailable_C = SparseAvailable<
    ColumnAvailable<true, true, false>,
    ColumnAvailable<true, true, true>,
    ColumnAvailable<true, true, false>,
    ColumnAvailable<true, true, true>>;
using C_Type = SparseMatrix_Type<double, SparseAvailable_C>;
```

Build the EKF:

``` cpp
auto Q = make_KalmanFilter_Q<STATE_SIZE>(1.0, 1.0, 1.0);
using Q_Type = decltype(Q);
auto R = make_KalmanFilter_R<OUTPUT_SIZE>(10.0, 10.0, 10.0, 10.0);
using R_Type = decltype(R);

using Parameter_Type = MyParameter<double>;
Parameter_Type parameters(0.1, 0.5, ...);

StateEquation_Object<X_Type, U_Type, Parameter_Type>
    state_equation = my_state_equation<double>;
StateEquationJacobian_Object<A_Type, X_Type, U_Type, Parameter_Type>
    state_equation_jacobian = my_state_equation_jacobian<double, A_Type>;
MeasurementEquation_Object<Y_Type, X_Type, Parameter_Type>
    measurement_equation = my_measurement_equation<double>;
MeasurementEquationJacobian_Object<C_Type, X_Type, Parameter_Type>
    measurement_equation_jacobian = my_measurement_equation_jacobian<double, C_Type>;

ExtendedKalmanFilter<A_Type, C_Type, U_Type, Q_Type, R_Type,
                     Parameter_Type, NUMBER_OF_DELAY>
    ekf(Q, R, state_equation, state_equation_jacobian,
        measurement_equation, measurement_equation_jacobian, parameters);
```

Set initial state:

``` cpp
ekf.X_hat.template set<0, 0>(0.0);
ekf.X_hat.template set<1, 0>(0.0);
ekf.X_hat.template set<2, 0>(0.0);
```

### Simulation loop with delay

``` cpp
std::array<Y_Type, NUMBER_OF_DELAY + 1> y_store;
std::size_t delay_index = 0;

for (std::size_t i = 0; i < SIM_STEP_MAX; i++) {
  x_true = my_state_equation<double>(x_true, u, parameters);
  y_store[delay_index] = my_measurement_equation<double>(x_true, parameters);

  delay_index++;
  if (delay_index > NUMBER_OF_DELAY) {
    delay_index = 0;
  }

  ekf.predict(u);
  ekf.update(y_store[delay_index]);

  auto x_hat = ekf.get_x_hat_without_delay();
}
```

---

## Unscented Kalman Filter (UKF)

The `UnscentedKalmanFilter` class is from the MCAP custom library. It has the same interface as EKF but does **not** require Jacobian functions.

### Python (MCAP custom library + SymPy)

``` python
from external_libraries.MCAP_python_control.python_control.kalman_filter import UnscentedKalmanFilter
ukf = UnscentedKalmanFilter(fxu, hx, Q, R, parameters, Number_of_Delay)
ukf.predict(u)
ukf.update(y_measured)
x_hat = ukf.get_x_hat_without_delay()
```

### C++

The UKF only needs state and measurement equations (no Jacobians):

``` cpp
StateEquation_Object<X_Type, U_Type, Parameter_Type>
    state_equation = my_state_equation<double>;
MeasurementEquation_Object<Y_Type, X_Type, Parameter_Type>
    measurement_equation = my_measurement_equation<double>;

UnscentedKalmanFilter<U_Type, Q_Type, R_Type, Parameter_Type, NUMBER_OF_DELAY>
    ukf(Q, R, state_equation, measurement_equation, parameters);
```

The simulation loop is the same pattern as EKF (predict/update with delay ring buffer).

---

## Least Squares

The `LeastSquares` class is from the MCAP custom library. It performs batch ordinary least squares.

### Python (MCAP custom library)

``` python
from external_libraries.MCAP_python_control.python_control.least_squares import LeastSquares
ls = LeastSquares(X)
ls.fit(X, y)
weights = ls.get_weights()
predictions = ls.predict(X)
```

### C++

The input matrix type `X_Type` is `DenseMatrix_Type<double, N_DATA, X_SIZE>`.

``` cpp
constexpr std::size_t N_DATA = 20;
constexpr std::size_t X_SIZE = 2;
constexpr std::size_t Y_SIZE = 1;

using X_Type = DenseMatrix_Type<double, N_DATA, X_SIZE>;
auto ls = make_LeastSquares<X_Type>();
```

Fill data and call fit:

``` cpp
DenseMatrix_Type<double, N_DATA, X_SIZE> X;
for (std::size_t i = 0; i < N_DATA; i++) {
  for (std::size_t j = 0; j < X_SIZE; j++) {
    X(i, j) = /* data */;
  }
}

DenseMatrix_Type<double, N_DATA, Y_SIZE> Y;
for (std::size_t i = 0; i < N_DATA; i++) {
  Y(i, 0) = /* data */;
}

ls.fit(X, Y);
auto weights = ls.get_weights();
// weights has X_SIZE + 1 rows (features + bias/offset)
```

---

## Recursive Least Squares (RLS)

The `RecursiveLeastSquares` class is from the MCAP custom library. It performs online weight estimation.

### Python (MCAP custom library)

``` python
from external_libraries.MCAP_python_control.python_control.least_squares import RecursiveLeastSquares
rls = RecursiveLeastSquares(feature_size=X.shape[1], lambda_factor=0.9)
rls.update(x, y_true)
weights = rls.get_weights()
```

### C++

The feature vector type `X_Type` is `StateSpaceState_Type<double, X_SIZE>`.

``` cpp
constexpr std::size_t X_SIZE = 2;
constexpr std::size_t Y_SIZE = 1;

using X_Type = StateSpaceState_Type<double, X_SIZE>;
auto rls = make_RecursiveLeastSquares<X_Type>();
rls.set_lambda(0.9);
```

Online update loop:

``` cpp
for (std::size_t i = 0; i < N_DATA; i++) {
  X_Type x_row;
  for (std::size_t j = 0; j < X_SIZE; j++) {
    x_row(j, 0) = /* data[i][j] */;
  }
  double y_val = /* target[i] */;
  rls.update(x_row, y_val);

  auto weights = rls.get_weights();
  // weights has X_SIZE + 1 rows (features + bias/offset)
}
```

---

## Helper: DiagMatrix identity

When discretizing a continuous-time model manually (Euler method), use `make_DiagMatrixIdentity`:

``` cpp
auto Ad = make_DiagMatrixIdentity<double, State_Num>() + Ac * dt;
auto Bd = Bc * dt;
```

---

## Notes on matrix types

- Matrix operations (`+`, `-`, `*`) follow the same rules as `python_numpy.hpp`.
- `SparseMatrix_Type<T, SparseAvailable_...>` is used for Jacobian type aliases.
- When defining Jacobian return types for EKF, use `SparseMatrix_Type` (not `auto`) because the exact type must be declared for the function object.
- Access individual elements with `.template get<ROW, COL>()` for compile-time indices, or `(row, col)` for runtime indices.
