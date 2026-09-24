program i169c_atan_same_as_atan2
  implicit none
  real :: x(3) = [1.0, 0.0, 1.0]
  real :: y(3) = [0.0, 1.0, 1.0]
  real :: observed(3), reference(3)
  observed = atan(y, x)
  reference = atan2(y, x)
  if (any(observed /= reference)) error stop
  write(*,'(a)') 'INTRINSICS 16.9.C ATAN SAME AS ATAN2 OK'
end program i169c_atan_same_as_atan2
