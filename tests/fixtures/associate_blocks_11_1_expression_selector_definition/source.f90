! rule: C1101
! covers: expression-selector-definition-rejected
program ab_c1101_expr
  implicit none
  integer :: seed
  seed=3
  associate (a => seed + 1)
    a=5
  end associate
end program ab_c1101_expr
