! rule: C1106
! covers: unnamed-associate-end-name-rejected
program ab_c1106_unnamed
  implicit none
  integer :: x
  x=5
  associate (a => x)
    a=55
  end associate inner
end program ab_c1106_unnamed
