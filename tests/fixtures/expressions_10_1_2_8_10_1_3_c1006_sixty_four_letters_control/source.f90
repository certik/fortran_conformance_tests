module expr_c1006_sixty_four_letters_control_mod
  implicit none
  interface operator(.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.)
    module procedure long_i
  end interface
contains
  pure integer function long_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    long_i = 10*lhs + rhs
  end function long_i
end module expr_c1006_sixty_four_letters_control_mod
program expr_c1006_sixty_four_letters_control
  use expr_c1006_sixty_four_letters_control_mod
  implicit none
  integer :: x
  x = 1 .aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa. 2
  if (x /= 12) error stop 'C1006:sixty-four-control'
  write(*,'(a)') 'EXPRESSIONS C1006 SIXTY FOUR CONTROL OK'
end program expr_c1006_sixty_four_letters_control
