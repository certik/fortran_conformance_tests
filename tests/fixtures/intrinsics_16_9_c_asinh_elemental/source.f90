program i169c_asinh_elemental
  implicit none
  real :: x(3) = [-2.0, 0.25, 3.0]
  associate(result => asinh(x))
    if (rank(result) /= 1) error stop
    if (size(result) /= 3) error stop
  end associate
  write(*,'(a)') 'INTRINSICS 16.9.C ASINH ELEMENTAL OK'
end program i169c_asinh_elemental
