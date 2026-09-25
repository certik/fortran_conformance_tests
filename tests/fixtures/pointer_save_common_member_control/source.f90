program save_common_member_control
  implicit none
  integer :: x
  common /shared/ x
  save /shared/
  x = 13
  if (x /= 13) error stop
  print '(a)', 'SAVE COMMON MEMBER CONTROL OK'
end program save_common_member_control
