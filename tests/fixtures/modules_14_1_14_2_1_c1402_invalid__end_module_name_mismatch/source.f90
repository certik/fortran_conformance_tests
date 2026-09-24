module c1402_name_m
  implicit none
  integer, parameter :: answer = 42
end module c1402_other_m
program c1402_name_probe
  use c1402_name_m
  implicit none
  if (answer /= 42) error stop
  print '(a)', 'C1402 CONTROL OK'
end program c1402_name_probe
