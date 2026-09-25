program explicit_r816_lower_bound
  implicit none
  integer :: a(-2:1)
  if (any(lbound(a) /= [-2])) error stop 'R816 lower bound'
  write(*,'(a)') 'ARRAY SHAPES R816 OK'
end program explicit_r816_lower_bound
