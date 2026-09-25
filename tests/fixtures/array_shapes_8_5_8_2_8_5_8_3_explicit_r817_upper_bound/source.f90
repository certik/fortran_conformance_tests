program explicit_r817_upper_bound
  implicit none
  integer :: positive(3)
  integer :: zero(0:0)
  integer :: negative(-3:-1)
  if (any(ubound(positive) /= [3])) error stop 'R817 positive upper'
  if (any(ubound(zero) /= [0])) error stop 'R817 zero upper'
  if (any(ubound(negative) /= [-1])) error stop 'R817 negative upper'
  write(*,'(a)') 'ARRAY SHAPES R817 OK'
end program explicit_r817_upper_bound
