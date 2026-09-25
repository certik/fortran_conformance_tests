module expr_c1006_logical_true_spelling_mod
  implicit none
  interface operator(.true.)
    module procedure truth_i
  end interface
contains
  pure integer function truth_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    truth_i = 10*lhs + rhs
  end function truth_i
end module expr_c1006_logical_true_spelling_mod
program expr_c1006_logical_true_spelling
  use expr_c1006_logical_true_spelling_mod
  implicit none
  integer :: x
  x = 1 .true. 2
  print *, x
end program expr_c1006_logical_true_spelling
