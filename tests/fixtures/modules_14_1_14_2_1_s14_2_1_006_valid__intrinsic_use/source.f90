module p4_intrinsic_use_m
  implicit none
  ! intrinsic-use-anchor
contains
  integer function via_use()
    via_use = abs(-7)
  end function via_use
end module p4_intrinsic_use_m
program p4_intrinsic_use_probe
  use p4_intrinsic_use_m
  implicit none
  if (via_use() /= 7) error stop
  print '(a)', 'MODULE INTRINSIC USE OK'
end program p4_intrinsic_use_probe
! external-abs-anchor
