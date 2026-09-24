program i169c_atan_arguments
  implicit none
  real :: x(3) = [1.0, 0.0, 1.0]
  real :: y(3) = [0.0, 1.0, 1.0]
  real :: boundary_x(2) = [1.0, 0.0]
  real :: boundary_y(2) = [0.0, 1.0]
  complex :: z = (2.0, 0.25)
  real :: pi
  real :: y_real_result(3), same_kind_result(3), boundary_result(2), one_arg(3)
  complex :: complex_arg
  pi = acos(-1.0)
  y_real_result = atan(y, x)
  if (any(y_real_result /= atan2(y, x))) error stop
  same_kind_result = atan(y, x)
  if (kind(same_kind_result) /= kind(x)) error stop
  if (any(same_kind_result /= atan2(y, x))) error stop
  boundary_result = atan(boundary_y, boundary_x)
  if (any(boundary_result /= atan2(boundary_y, boundary_x))) error stop
  one_arg = atan(x)
  complex_arg = atan(z)
  if (kind(one_arg) /= kind(x)) error stop
  if (kind(complex_arg) /= kind(z)) error stop
  if (real(complex_arg) < -pi / 2.0 .or. real(complex_arg) > pi / 2.0) error stop
  write(*,'(a)') 'INTRINSICS 16.9.C ATAN ARGUMENTS OK'
end program i169c_atan_arguments
