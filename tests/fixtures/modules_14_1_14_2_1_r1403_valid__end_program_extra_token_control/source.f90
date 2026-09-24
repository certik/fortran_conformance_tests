program r1403_named_end_control
  implicit none
  integer :: observed
  observed = -777
  if (observed /= -777) error stop
  observed = 43
  if (observed /= 43) error stop
  print '(a)', 'END PROGRAM CONTROL OK'
end program r1403_named_end_control
