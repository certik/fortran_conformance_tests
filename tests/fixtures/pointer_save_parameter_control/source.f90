program save_parameter_control
  implicit none
  integer :: k = 3
  save :: k
  if (k /= 3) error stop
  print '(a)', 'SAVE PARAMETER CONTROL OK'
end program save_parameter_control
