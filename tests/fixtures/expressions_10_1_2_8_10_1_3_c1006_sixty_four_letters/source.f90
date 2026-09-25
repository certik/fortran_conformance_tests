module expr_c1006_sixty_four_letters_mod
  implicit none
  interface operator(.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.)
    module procedure long_i
  end interface
contains
  pure integer function long_i(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    long_i = 10*lhs + rhs
  end function long_i
end module expr_c1006_sixty_four_letters_mod
program expr_c1006_sixty_four_letters
  use expr_c1006_sixty_four_letters_mod
  implicit none
  integer :: x
  x = 1 .aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa. 2
  print *, x
end program expr_c1006_sixty_four_letters
