program i169c_asinh_complex_range
  implicit none
  integer :: i
  real :: pi
  complex :: x(2), y(2)
  pi = acos(-1.0)
  x = [(cmplx(2.0, 1.4), i = 1, 2)]
  y = asinh(x)
  if (any(aimag(y) < -pi / 2.0 .or. aimag(y) > pi / 2.0)) error stop
  write(*,'(a)') 'INTRINSICS 16.9.C ASINH COMPLEX RANGE OK'
end program i169c_asinh_complex_range
