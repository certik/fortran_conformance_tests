module expr_c1006_logical_false_spelling_control_mod
  implicit none
  interface operator(.falsity.)
    module procedure falsity_i
  end interface
contains
  pure integer function falsity_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    falsity_i = 10*lhs + rhs
  end function falsity_i
end module expr_c1006_logical_false_spelling_control_mod
program expr_c1006_logical_false_spelling_control
  use expr_c1006_logical_false_spelling_control_mod
  implicit none
  integer :: x
  x = 1 .falsity. 2
  if (x /= 12) error stop 'C1006:logical-false-spelling-rejected'
  write(*,'(a)') 'EXPRESSIONS C1006 FALSE CONTROL OK'
end program expr_c1006_logical_false_spelling_control
