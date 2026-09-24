program i169c_atan_one_arg_range
  implicit none
  real :: pi
  real :: real_result
  complex :: complex_result
  pi = acos(-1.0)
  real_result = atan(1.4)
  complex_result = atan(cmplx(1.4, 0.25))
  if (real_result < -pi / 2.0 .or. real_result > pi / 2.0) error stop
  if (real(complex_result) < -pi / 2.0 .or. real(complex_result) > pi / 2.0) error stop
  write(*,'(a)') 'INTRINSICS 16.9.C ATAN ONE ARG RANGE OK'
end program i169c_atan_one_arg_range
