module r1407_contains_m
  implicit none
contains
  integer function answer()
    answer = 42
  end function answer
end module r1407_contains_m
program r1407_contains_probe
  use r1407_contains_m
  implicit none
  if (answer() /= 42) error stop
  print '(a)', 'CONTAINS SUBPROGRAM OK'
end program r1407_contains_probe
