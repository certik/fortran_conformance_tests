program i169c_asinh_arguments
  implicit none
  real :: real_x = 0.25
  complex :: complex_x = (2.0, 2.0)
  real :: pi
  real :: real_result
  complex :: complex_result
  pi = acos(-1.0)
  real_result = asinh(real_x)
  complex_result = asinh(complex_x)
  if (kind(real_result) /= kind(real_x)) error stop
  if (kind(complex_result) /= kind(complex_x)) error stop
  if (aimag(complex_result) < -pi / 2.0 .or. aimag(complex_result) > pi / 2.0) error stop
  write(*,'(a)') 'INTRINSICS 16.9.C ASINH ARGUMENTS OK'
end program i169c_asinh_arguments
