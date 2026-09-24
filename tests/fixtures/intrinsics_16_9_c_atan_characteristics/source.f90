program i169c_atan_characteristics
  implicit none
  real :: x(3) = [1.0, 0.0, 1.0]
  real :: y(3) = [0.0, 1.0, 1.0]
  real :: result(3)
  result = atan(y, x)
  associate(observed => atan(y, x))
    if (rank(observed) /= rank(x)) error stop
    if (size(observed) /= size(x)) error stop
  end associate
  if (kind(result) /= kind(x)) error stop
  if (rank(result) /= rank(x)) error stop
  if (any(shape(result) /= shape(x))) error stop
  write(*,'(a)') 'INTRINSICS 16.9.C ATAN CHARACTERISTICS OK'
end program i169c_atan_characteristics
