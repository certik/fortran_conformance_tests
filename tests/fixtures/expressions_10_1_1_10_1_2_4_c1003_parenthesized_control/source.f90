program expr_c1003_parenthesized_control
  implicit none
  integer :: checks, i
  checks=0
  i = 4
  if ((i+1) /= 5) error stop 'EC1003:ordinary'
  checks=checks+1
  if (checks /= 1) error stop 'EC1003:checks'
  write(*,'(a)') 'EXPRESSIONS C1003 PAREN CONTROL OK'
end program expr_c1003_parenthesized_control
