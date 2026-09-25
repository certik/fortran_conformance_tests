module expr_c1006_logical_true_spelling_control_mod
  implicit none
  interface operator(.truth.)
    module procedure truth_i
  end interface
contains
  pure integer function truth_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    truth_i = 10*lhs + rhs
  end function truth_i
end module expr_c1006_logical_true_spelling_control_mod
program expr_c1006_logical_true_spelling_control
  use expr_c1006_logical_true_spelling_control_mod
  implicit none
  integer :: x
  x = 1 .truth. 2
  if (x /= 12) error stop 'C1006:logical-true-spelling-rejected'
  write(*,'(a)') 'EXPRESSIONS C1006 TRUE CONTROL OK'
end program expr_c1006_logical_true_spelling_control
