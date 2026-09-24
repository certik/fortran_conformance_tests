module p4_intrinsic_attr_m
  implicit none
  intrinsic :: abs
contains
  integer function via_attribute()
    via_attribute = abs(-7)
  end function via_attribute
end module p4_intrinsic_attr_m
program p4_intrinsic_attr_probe
  use p4_intrinsic_attr_m
  implicit none
  if (via_attribute() /= 7) error stop
  print '(a)', 'MODULE INTRINSIC ATTRIBUTE OK'
end program p4_intrinsic_attr_probe
! external-abs-anchor
