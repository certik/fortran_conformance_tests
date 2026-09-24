module r1406_named_end_m
  implicit none
  integer, parameter :: answer = 42
end module r1406_named_end_m
program r1406_named_end_probe
  use r1406_named_end_m
  implicit none
  if (answer /= 42) error stop
  print '(a)', 'END MODULE CONTROL OK'
end program r1406_named_end_probe
