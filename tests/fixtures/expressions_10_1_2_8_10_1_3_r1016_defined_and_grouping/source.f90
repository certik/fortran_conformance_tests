module expr_r1016_defined_and_mod
  implicit none
  type :: token
    integer :: value
  end type token
  interface operator(.and.)
    module procedure join_and
  end interface
contains
  pure function join_and(lhs, rhs) result(out)
    type(token), intent(in) :: lhs, rhs
    type(token) :: out
    out%value = 10*lhs%value + rhs%value
  end function join_and
end module expr_r1016_defined_and_mod

program expr_r1016_defined_and_grouping
  use expr_r1016_defined_and_mod
  implicit none
  type(token) :: a, b, c, r
  a = token(1); b = token(2); c = token(3)
  r = a .and. b .and. c
  if (r%value /= 123) error stop 'R1016:left-recursive-and'
  write(*,'(a)') 'EXPRESSIONS R1016 DEFINED AND GROUPING OK'
end program expr_r1016_defined_and_grouping
