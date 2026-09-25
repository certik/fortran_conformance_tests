! rule: C1106
! covers: end-associate-name-mismatch-rejected
program ab_c1106_mismatch
  implicit none
  integer :: x
  x=5
  outer: associate (a => x)
    a=55
  end associate inner
end program ab_c1106_mismatch
