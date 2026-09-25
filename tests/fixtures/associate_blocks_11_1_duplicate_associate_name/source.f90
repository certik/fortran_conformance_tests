! rule: C1102
! covers: duplicate-associate-name-rejected
program ab_c1102_duplicate
  implicit none
  integer :: x, y
  x=4; y=8
  associate (item => x, item => y)
    x=item
  end associate
end program ab_c1102_duplicate
