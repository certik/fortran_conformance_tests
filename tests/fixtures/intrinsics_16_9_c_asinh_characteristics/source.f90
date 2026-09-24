program i169c_asinh_characteristics
  implicit none
  real :: x(3) = [-2.0, 0.25, 3.0]
  real :: y(3)
  y = asinh(x)
  associate(result => asinh(x))
    if (rank(result) /= rank(x)) error stop
    if (size(result) /= size(x)) error stop
  end associate
  if (kind(y) /= kind(x)) error stop
  if (rank(y) /= rank(x)) error stop
  if (any(shape(y) /= shape(x))) error stop
  write(*,'(a)') 'INTRINSICS 16.9.C ASINH CHARACTERISTICS OK'
end program i169c_asinh_characteristics
