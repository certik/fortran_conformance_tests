module expr_r1004_digit_in_name
  implicit none
  interface operator(.u1.)
    module procedure u
  end interface
contains
  integer function u(x)
    integer, intent(in) :: x
    u = x
  end function u
end module expr_r1004_digit_in_name
