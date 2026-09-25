module expr_r1018_defined_equiv_mod
  implicit none
  type :: token
    integer :: value
  end type token
  interface operator(.eqv.)
    module procedure join_eqv
  end interface
contains
  pure function join_eqv(lhs, rhs) result(out)
    type(token), intent(in) :: lhs, rhs
    type(token) :: out
    out%value = 10*lhs%value + rhs%value
  end function join_eqv
end module expr_r1018_defined_equiv_mod

program expr_r1018_defined_equiv_grouping
  use expr_r1018_defined_equiv_mod
  implicit none
  type(token) :: a, b, c, r
  a = token(1); b = token(2); c = token(3)
  r = a .eqv. b .eqv. c
  if (r%value /= 123) error stop 'R1018:left-recursive-equiv'
  write(*,'(a)') 'EXPRESSIONS R1018 DEFINED EQUIV GROUPING OK'
end program expr_r1018_defined_equiv_grouping
