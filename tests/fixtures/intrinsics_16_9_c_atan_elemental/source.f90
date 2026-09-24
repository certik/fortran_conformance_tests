program i169c_atan_elemental
  implicit none
  real :: x(3) = [-1.4, 0.0, 1.4]
  associate(result => atan(x))
    if (rank(result) /= 1) error stop
    if (size(result) /= 3) error stop
  end associate
  write(*,'(a)') 'INTRINSICS 16.9.C ATAN ELEMENTAL OK'
end program i169c_atan_elemental
