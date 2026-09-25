program explicit_r815_scalar_forms
  implicit none
  integer :: checks
  integer :: upper_only(4)
  integer :: explicit_lower(-2:1)
  integer :: multi(2,0:2)
  checks=0
  if (any(lbound(upper_only) /= [1])) error stop 'R815 upper lower'
  checks=checks+1
  if (any(ubound(upper_only) /= [4])) error stop 'R815 upper upper'
  checks=checks+1
  if (any(lbound(explicit_lower) /= [-2])) error stop 'R815 explicit lower'
  checks=checks+1
  if (rank(multi) /= 2) error stop 'R815 multidimensional rank'
  checks=checks+1
  if (checks /= 4) error stop 'R815 check count'
  write(*,'(a)') 'ARRAY SHAPES R815 OK'
end program explicit_r815_scalar_forms
