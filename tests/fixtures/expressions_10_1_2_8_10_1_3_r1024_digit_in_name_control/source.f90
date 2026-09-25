module expr_r1024_digit_in_name_control_mod
  implicit none
  interface operator(.ba.)
    module procedure ba_i
  end interface
contains
  pure integer function ba_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    ba_i = 10*lhs + rhs
  end function ba_i
end module expr_r1024_digit_in_name_control_mod
program expr_r1024_digit_in_name_control
  use expr_r1024_digit_in_name_control_mod
  implicit none
  integer :: x
  x = 1 .ba. 2
  if (x /= 12) error stop 'R1024:digit-in-name-rejected'
  write(*,'(a)') 'EXPRESSIONS R1024 DIGIT-IN-NAME-REJECTED CONTROL OK'
end program expr_r1024_digit_in_name_control
