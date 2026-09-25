module expr_c1006_logical_false_spelling_mod
  implicit none
  interface operator(.false.)
    module procedure falsity_i
  end interface
contains
  pure integer function falsity_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    falsity_i = 10*lhs + rhs
  end function falsity_i
end module expr_c1006_logical_false_spelling_mod
program expr_c1006_logical_false_spelling
  use expr_c1006_logical_false_spelling_mod
  implicit none
  integer :: x
  x = 1 .false. 2
  print *, x
end program expr_c1006_logical_false_spelling
